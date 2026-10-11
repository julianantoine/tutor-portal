"""
Tutor Portal — Notes → Study Kit.

Turns a student's own notes (pasted text, .txt/.md, or an uploaded PDF) into
(1) a flashcard deck and (2) a graded practice exam on that subject.

Two engines, in this order:

* ``ai``     — the local Ollama tutor model is asked for strict JSON grounded
               ONLY in the student's notes. Richer phrasings, real exam style.
* ``rules``  — a fully offline extractive generator. No model, no network. It
               mines definition-shaped lines, markdown headings and cloze-able
               sentences out of the notes, then builds distractors for the
               multiple-choice exam out of the other terms in the same notes.

``auto`` tries the model with a hard time budget and silently falls back to
``rules``, so the feature always works — even with Ollama stopped.
"""

from __future__ import annotations

import json
import re
import random
import base64
import io
from typing import List, Dict, Optional, Tuple

# --------------------------------------------------------------------------- #
# text extraction
# --------------------------------------------------------------------------- #

def text_from_pdf_b64(b64: str) -> str:
    """Extract the text layer from an uploaded PDF (pypdf), or '' if we can't."""
    try:
        from pypdf import PdfReader
        raw = base64.b64decode(b64.split(",")[-1])
        reader = PdfReader(io.BytesIO(raw))
        out = []
        for page in reader.pages[:60]:
            try:
                out.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(out).strip()
    except Exception:
        return ""


def clean_text(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# deterministic ("rules") generator
# --------------------------------------------------------------------------- #

SEPARATORS = [" — ", " – ", " - ", ": ", " = ", "→", "=>"]
BULLET = re.compile(r"^\s*(?:[-*•·‣]|\d+[.)])\s*")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "has", "have", "had", "not", "but", "you", "your", "can", "will", "when",
    "which", "then", "than", "into", "over", "each", "also", "such", "only",
    "more", "most", "some", "these", "those", "there", "their", "they", "them",
    "about", "because", "between", "does", "doing", "done", "very", "just",
    "like", "make", "makes", "made", "used", "using", "use", "one", "two",
}


def _looks_like_junk(s: str) -> bool:
    if len(s) < 12:
        return True
    if "http://" in s or "https://" in s or "www." in s:
        return True
    if s.count("|") >= 2:              # tables come through mangled
        return True
    if len(re.findall(r"[A-Za-z]", s)) < 8:
        return True
    return False


def _split_definitions(text: str) -> List[Tuple[str, str]]:
    """Pull (term, definition) pairs out of definition-shaped lines and headings."""
    pairs: List[Tuple[str, str]] = []
    lines = text.split("\n")

    # 1. headings: "## Term" followed by prose
    for i, raw in enumerate(lines):
        h = HEADING.match(raw)
        if not h:
            continue
        term = h.group(2).strip().rstrip(":").strip()
        if len(term) < 2 or len(term) > 80:
            continue
        body = []
        for j in range(i + 1, min(i + 8, len(lines))):
            nxt = lines[j].strip()
            if not nxt:
                if body:
                    break
                continue
            if HEADING.match(lines[j]):
                break
            body.append(nxt)
        defn = " ".join(body).strip()
        if len(defn) >= 20 and not _looks_like_junk(defn):
            pairs.append((term, defn[:400]))

    # 2. inline "term <sep> definition"
    for raw in lines:
        line = BULLET.sub("", raw.strip()).strip()
        if len(line) < 20 or _looks_like_junk(line):
            continue
        for sep in SEPARATORS:
            idx = line.find(sep)
            if idx <= 0:
                continue
            term, defn = line[:idx].strip(), line[idx + len(sep):].strip()
            if not (2 <= len(term) <= 70) or len(defn) < 15:
                continue
            # a sentence that merely contains a dash is not a definition
            if term.endswith((",",)) or len(term.split()) > 9:
                continue
            if _looks_like_junk(defn):
                continue
            pairs.append((term, defn[:400]))
            break

    # de-duplicate on the term, keeping the longest definition (and the original casing)
    best: Dict[str, Tuple[str, str]] = {}
    for term, defn in pairs:
        key = term.lower().strip()
        if key not in best or len(defn) > len(best[key][1]):
            best[key] = (term.strip(), defn)
    return [(t, d) for t, d in best.values()]


def _sentences(text: str) -> List[str]:
    flat = re.sub(r"\n+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", flat)
    out = []
    for s in parts:
        s = s.strip()
        if 40 <= len(s) <= 320 and not _looks_like_junk(s) and s.lower().count("http") == 0:
            out.append(s)
    return out


def _key_token(sentence: str) -> Optional[str]:
    """Pick a memorable token to blank out: a long capitalised term or a number+unit."""
    words = re.findall(r"[A-Za-z][A-Za-z\-]{4,}|-?\d+(?:\.\d+)?\s?[A-Za-z%]{1,6}", sentence)
    cands = []
    for w in words:
        wl = w.strip()
        if wl.lower() in STOPWORDS:
            continue
        if wl[0].isupper() or any(c.isdigit() for c in wl):
            cands.append(wl)
    if not cands:
        return None
    cands.sort(key=len, reverse=True)
    return cands[0]


def rules_cards(text: str, limit: int = 40) -> List[Dict]:
    """Flashcards: definition pairs first, then cloze deletions from prose."""
    cards: List[Dict] = []
    defs = _split_definitions(text)
    taken = {t.lower() for t, _ in defs}

    for term, defn in defs:
        cards.append({"front": term, "back": defn, "source": "definition"})

    if len(cards) < limit:
        for s in _sentences(text):
            if len(cards) >= limit:
                break
            # don't re-ask what a definition card already asked, and strip
            # markdown/bullet furniture so the cloze reads like a question
            s = BULLET.sub("", re.sub(r"^\s*#{1,6}\s*", "", s)).strip()
            tok = _key_token(s)
            if not tok or tok not in s or tok.lower() in taken:
                continue
            cloze = s.replace(tok, "_____", 1)
            if len(cloze) < 30:
                continue
            cards.append({"front": cloze, "back": tok, "source": "cloze"})

    # de-dupe on the prompt text
    seen, out = set(), []
    for c in cards:
        k = c["front"].lower()[:90]
        if k in seen:
            continue
        seen.add(k)
        out.append(c)
    out = out[:limit]
    for i, c in enumerate(out):
        c["level"] = 1 if i < len(out) / 3 else (2 if i < 2 * len(out) / 3 else 3)
    return out


def rules_exam(text: str, cards: List[Dict], limit: int = 10) -> List[Dict]:
    """Multiple-choice questions built from the notes' own terms and distractor pool."""
    random.seed(7)
    defs = [(c["front"], c["back"]) for c in cards if c.get("source") == "definition"]
    questions: List[Dict] = []

    # A. "which best describes X?" using other definitions as distractors
    if len(defs) >= 4:
        for term, defn in defs[:limit]:
            others = [d for t, d in defs if d != defn]
            if len(others) < 3:
                break
            distractors = random.sample(others, 3)
            opts = [defn] + distractors
            random.shuffle(opts)
            questions.append({
                "q": f"Which of these best describes {term}?",
                "opts": [o[:200] for o in opts],
                "answer": opts.index(defn),
                "explain": f"{term} — {defn[:220]}",
            })

    # B. cloze multiple choice from the other cards
    if len(questions) < limit:
        cloze = [c for c in cards if c.get("source") == "cloze"]
        pool = [c["back"] for c in cloze]
        for c in cloze:
            if len(questions) >= limit:
                break
            others = [t for t in pool if t != c["back"]]
            if len(others) < 3:
                continue
            opts = random.sample(others, 3) + [c["back"]]
            random.shuffle(opts)
            questions.append({
                "q": f"Fill in the blank: {c['front']}",
                "opts": opts,
                "answer": opts.index(c["back"]),
                "explain": f"The missing term is {c['back']}.",
            })

    # C. last resort: true/false from prose, so an exam always exists
    if len(questions) < 3:
        for s in _sentences(text)[:limit]:
            if len(questions) >= limit:
                break
            questions.append({
                "q": f"True or false — your notes state: \u201c{s[:220]}\u201d",
                "opts": ["True", "False"],
                "answer": 0,
                "explain": "This statement is taken verbatim from the notes you uploaded.",
            })

    questions = questions[:limit]
    for i, q in enumerate(questions):
        q["level"] = 1 if i < len(questions) / 3 else (2 if i < 2 * len(questions) / 3 else 3)
    return questions


def rules_kit(text: str) -> Dict:
    cards = rules_cards(text)
    return {
        "cards": cards,
        "exam": rules_exam(text, cards),
        "engine": "rules",
        "summary": f"{len(cards)} flashcards and a {len(rules_exam(text, cards))}-question exam "
                   f"built offline from {len(text.split())} words of your notes.",
    }


# --------------------------------------------------------------------------- #
# local-AI generator
# --------------------------------------------------------------------------- #

AI_SYSTEM = """You turn a student's own lecture notes into study material.
Ground EVERY card and question ONLY in the notes supplied. Never invent facts,
formulas or definitions the notes do not contain. If the notes are thin, make
fewer items rather than padding.
Reply with STRICT JSON and nothing else, shaped exactly like:
{"flashcards":[{"front":"prompt","back":"answer","level":1}],
 "exam":[{"q":"question","opts":["a","b","c","d"],"answer":0,"explain":"why"}]}
Rules: 8-15 flashcards; 5-8 exam questions; every exam question has exactly 4
options with "answer" the 0-based index of the correct one; "explain" one sentence;
level is 1 (foundational), 2 (intermediate) or 3 (advanced/exam). Keep every string
short (under 220 characters)."""


def _balanced_objects(s: str, start: int = 0) -> List[str]:
    """Every complete, brace-balanced ``{...}`` object at any depth from ``start``."""
    out: List[str] = []
    i, n = start, len(s)
    while i < n:
        if s[i] != "{":
            i += 1
            continue
        depth, j, instr, esc = 0, i, False, False
        while j < n:
            ch = s[j]
            if instr:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    instr = False
            elif ch == '"':
                instr = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    out.append(s[i:j + 1])
                    i = j
                    break
            j += 1
        else:
            break                      # ran off the end mid-object: keep what we have
        i += 1
    return out


def _array_after(s: str, key: str) -> Optional[str]:
    """The text inside the ``[ ... ]`` that follows ``"key":``, if there is one."""
    m = re.search(r'"%s"\s*:\s*\[' % re.escape(key), s)
    if not m:
        return None
    i, n, depth, instr, esc = m.end(), len(s), 1, False, False
    start = i
    while i < n:
        ch = s[i]
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return s[start:i]
        i += 1
    return s[start:]                   # unterminated (truncated) — salvage anyway


def _salvage(s: str, key: str) -> List[dict]:
    """Pull as many well-formed objects as possible out of a key's array.

    Local models routinely truncate mid-array or repeat a key name; parsing the
    whole document as JSON then fails. Salvaging object-by-object keeps the good
    items instead of throwing the whole answer away.
    """
    seg = _array_after(s, key)
    if seg is None:
        seg = s
    items = []
    for chunk in _balanced_objects(seg):
        try:
            obj = json.loads(chunk)
        except Exception:
            continue
        if isinstance(obj, dict):
            items.append(obj)
    return items


def _extract_json(s: str) -> Optional[dict]:
    if not s:
        return None
    s = re.sub(r"```(?:json)?", "", s).strip()
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    a, b = s.find("{"), s.rfind("}")
    if a >= 0 and b > a:
        try:
            obj = json.loads(s[a:b + 1])
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    # last resort: rebuild a document from whatever complete objects exist
    cards = _salvage(s, "flashcards")
    exam = _salvage(s, "exam")
    if cards or exam:
        return {"flashcards": cards, "exam": exam}
    return None


def _valid_kit(obj: dict) -> Optional[Dict]:
    if not isinstance(obj, dict):
        return None
    cards, exam = [], []
    for c in obj.get("flashcards") or []:
        if isinstance(c, dict) and c.get("front") and c.get("back"):
            lvl = c.get("level")
            cards.append({
                "front": str(c["front"])[:300],
                "back": str(c["back"])[:600],
                "level": lvl if lvl in (1, 2, 3) else 2,
                "source": "ai",
            })
    for q in obj.get("exam") or []:
        if not isinstance(q, dict):
            continue
        opts = q.get("opts") or q.get("options") or []
        if not isinstance(opts, list) or len(opts) < 2:
            continue
        try:
            ans = int(q.get("answer", 0))
        except Exception:
            ans = 0
        if not 0 <= ans < len(opts):
            ans = 0
        lvl = q.get("level")
        exam.append({
            "q": str(q.get("q", ""))[:400],
            "opts": [str(o)[:280] for o in opts][:6],
            "answer": ans,
            "explain": str(q.get("explain", ""))[:400],
            "level": lvl if lvl in (1, 2, 3) else 2,
        })
    if len(cards) < 3 or len(exam) < 3:
        return None
    for i, c in enumerate(cards):
        c.setdefault("level", 1 if i < len(cards) / 3 else (2 if i < 2 * len(cards) / 3 else 3))
    return {"cards": cards, "exam": exam, "engine": "ai"}


def ai_kit(text: str, title: str, ollama_url: str, model: str,
           timeout: float = 90.0) -> Optional[Dict]:
    """Ask the local tutor model for a study kit. Returns None on any failure."""
    try:
        import httpx
        # keep the prompt inside a sane context window for small local models
        body = text[:12000]
        user = f"Notes title: {title}\n\nNOTES:\n{body}\n\nReturn the JSON now."
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": AI_SYSTEM},
                         {"role": "user", "content": user}],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2, "num_predict": 1600},
        }
        with httpx.Client(timeout=httpx.Timeout(timeout, connect=8.0)) as client:
            r = client.post(f"{ollama_url}/api/chat", json=payload)
            if r.status_code != 200:
                return None
            data = r.json()
            content = (data.get("message") or {}).get("content") or ""
            if not content and data.get("response"):
                content = data["response"]
        return _valid_kit(_extract_json(content) or {})
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# public entry point
# --------------------------------------------------------------------------- #

def build_kit(text: str, title: str = "Notes", engine: str = "auto",
              ollama_url: str = "http://localhost:11437",
              model: str = "hermes3:latest", timeout: float = 240.0) -> Dict:
    """Return {'cards', 'exam', 'engine', 'summary', 'fallback_reason'}."""
    text = clean_text(text)
    if len(text.split()) < 25:
        raise ValueError("That looks like too little text — paste at least a few lines of notes.")

    if engine in ("auto", "ai"):
        kit = ai_kit(text, title, ollama_url, model, timeout=timeout)
        if kit:
            kit["summary"] = (f"{len(kit['cards'])} flashcards and {len(kit['exam'])} exam "
                              f"questions written by your local tutor model.")
            kit["fallback_reason"] = None
            return kit
        if engine == "ai":
            raise ValueError(f"The local model at {ollama_url} did not return usable JSON — "
                             f"try the 'Instant (offline rules)' engine.")

    kit = rules_kit(text)
    kit["fallback_reason"] = None if engine == "rules" else \
        "Local model unavailable or too slow, so these were built offline by the rules engine."
    return kit
