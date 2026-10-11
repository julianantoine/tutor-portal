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

def pdf_pages_b64(b64: str) -> List[str]:
    """Text of each PDF page, kept separate per page.

    Per-page is the point: slide decks repeat a running footer on every page
    (copyright line, slide number, course code), and that boilerplate is only
    detectable by comparing pages with each other.
    """
    try:
        from pypdf import PdfReader
        raw = base64.b64decode(b64.split(",")[-1])
        reader = PdfReader(io.BytesIO(raw))
        pages = []
        for page in reader.pages[:80]:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        return pages
    except Exception:
        return []


# --- footnote / running-header filters ------------------------------------- #
PAGE_NO_RE = re.compile(r"^\s*(?:page\s*)?\d{1,4}(?:\s*(?:of|/)\s*\d{1,4})?\s*$", re.I)
SLIDE_RE = re.compile(r"^\s*(?:slide|fig(?:ure)?|table|chart|exhibit|appendix)\s*\.?\s*\d+\b.*$", re.I)
COPY_RE = re.compile(
    r"(©|\(c\)\s*\d{4}|\bcopyright\b|all rights reserved|do not (?:copy|distribute|reproduce|share)"
    r"|confidential|proprietary|used with permission|reprinted)", re.I)
URL_ONLY_RE = re.compile(r"^\s*(?:https?://|www\.)\S+\s*$", re.I)
# "Physics 202 – Lecture 4", "MTH-202", "Prof. Smith", "Fall 2026"
RUNNING_RE = re.compile(
    r"^\s*(?:[A-Z]{2,4}[-\s]?\d{3}[a-z]?|lecture\s*\d+|chapter\s*\d+|prof(?:essor)?\.?\s+\S+"
    r"|(?:spring|summer|fall|winter)\s*\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\s*$", re.I)


def _norm_boiler(s: str) -> str:
    """Normalise for cross-page comparison: digits and punctuation collapse, so
    'Slide 12' and 'Slide 13' compare equal."""
    s = re.sub(r"\d+", "#", (s or "").lower())
    s = re.sub(r"[^a-z#\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _too_small_to_matter(t: str) -> bool:
    """Very short lines that carry no learnable content. Deliberately narrow —
    formula fragments like 'C = Q/V' must survive."""
    return len(re.findall(r"[A-Za-z]", t)) < 3 and len(t) < 24


def is_footnote_line(line: str) -> bool:
    """A single line that is footnote/slide furniture rather than content."""
    t = (line or "").strip()
    if not t:
        return True
    if PAGE_NO_RE.match(t) or SLIDE_RE.match(t):
        return True
    if COPY_RE.search(t) and len(t) < 200:
        return True
    if URL_ONLY_RE.match(t):
        return True
    if RUNNING_RE.match(t):
        return True
    if _too_small_to_matter(t):
        return True
    return False


def strip_slide_boilerplate(pages: List[str], frac: float = 0.4, min_pages: int = 3) -> List[str]:
    """Drop running headers/footers from a deck, page by page.

    Two passes:
      1. line-level footnote filters (page numbers, ©, 'Slide N', course codes);
      2. anything short that repeats across a large fraction of pages, compared
         after digit-collapsing so 'Slide 12' matches 'Slide 13'.
    Long sentences are never removed by the repetition rule, so a genuinely
    repeated teaching line survives.
    """
    n = len(pages)
    boiler = set()
    if n >= min_pages:
        counts: Dict[str, int] = {}
        for p in pages:
            lines = [l.strip() for l in (p or "").split("\n") if l.strip()]
            if not lines:
                continue
            edge = lines[:2] + lines[-3:]
            for key in {_norm_boiler(x) for x in edge}:
                if key:
                    counts[key] = counts.get(key, 0) + 1
        thresh = max(min_pages, int(n * frac))
        boiler = {k for k, c in counts.items() if c >= thresh and len(k) <= 90}
        # a repeated SHORT line anywhere on the page is furniture too
        everywhere: Dict[str, int] = {}
        for p in pages:
            for key in {_norm_boiler(l) for l in (p or "").split("\n") if l.strip()}:
                if key:
                    everywhere[key] = everywhere.get(key, 0) + 1
        boiler |= {k for k, c in everywhere.items()
                   if c >= thresh and len(k) <= 60 and not k.endswith((".", "?", "!"))}

    out = []
    for p in pages:
        keep = []
        for raw in (p or "").split("\n"):
            t = raw.strip()
            if not t or is_footnote_line(t):
                continue
            if _norm_boiler(t) in boiler:
                continue
            keep.append(t)
        out.append("\n".join(keep))
    return out


def drop_footnote_lines(text: str) -> str:
    """Line-level filter for text that has no page structure (pasted notes)."""
    keep = [l for l in (text or "").split("\n") if not is_footnote_line(l)]
    return "\n".join(keep)


def merge_wrapped_lines(text: str) -> str:
    """Rejoin sentences that a PDF hard-wrapped across lines.

    Careful not to glue a slide title onto its body: a SHORT line with no
    terminal punctuation followed by a proper sentence is treated as a heading
    and left on its own line, everything else is joined.
    """
    lines = [l.strip() for l in (text or "").split("\n")]
    out: List[str] = []
    buf = ""
    for raw in lines:
        t = raw.strip()
        if not t:
            if buf:
                out.append(buf); buf = ""
            if out and out[-1] != "":
                out.append("")
            continue
        if not buf:
            buf = t
            continue
        prev_incomplete = not buf.endswith((".", "!", "?", ":", ";"))
        nxt_is_sentence = bool(re.match(r"[A-Z\"'(]", t)) and len(t) >= 40
        heading_like = len(buf) <= 65 and prev_incomplete and len(buf.split()) <= 10
        starts_item = bool(BULLET.match(t) or HEADING.match(t))
        if prev_incomplete and not starts_item and not (heading_like and nxt_is_sentence):
            buf = buf + " " + t
        else:
            out.append(buf)
            buf = t
    if buf:
        out.append(buf)
    return "\n".join(out)


def clean_text(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = drop_footnote_lines(text)
    text = merge_wrapped_lines(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def text_from_pdf_b64(b64: str) -> str:
    """Extract a PDF's text layer, minus slide footers/running headers."""
    pages = pdf_pages_b64(b64)
    if not pages:
        return ""
    pages = strip_slide_boilerplate(pages)
    return clean_text("\n\n".join(pages))


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

    # 1b. slide-style titles: a short, unpunctuated line followed by a sentence.
    #     Deck exports have no markdown, so "Capacitance" on its own line is the
    #     only signal that the next paragraph defines it.
    for i, raw in enumerate(lines):
        t = raw.strip()
        if not (2 <= len(t) <= 70) or len(t.split()) > 6:
            continue
        if t.endswith((".", "!", "?", ":", ";", ",")) or t.startswith(("(", "[")):
            continue
        if "," in t or ";" in t:
            continue
        if HEADING.match(raw) or BULLET.match(raw):
            continue
        nxt = ""
        for j in range(i + 1, min(i + 3, len(lines))):
            if lines[j].strip():
                nxt = lines[j].strip()
                break
        if len(nxt) < 40 or BULLET.match(nxt) or _looks_like_junk(nxt):
            continue
        pairs.append((t, nxt[:400]))

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
            # an equation or clause inside prose is not a definition: "…
            # potential difference, C = Q/V, measured in farads." must not become
            # the term "difference, C"
            if sep in (" = ", "=>", "→") and ("," in term or ";" in term or len(term.split()) > 5):
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
    # A heading has no terminal punctuation, so flattening newlines blindly glues
    # it to the sentence below — which produced garbled cloze cards such as
    # "_____ constant The dielectric constant is the factor …". Mark the boundary
    # at every heading line (markdown "## Title" or a bare slide title) first.
    lines = (text or "").split("\n")
    guarded: List[str] = []
    for i, raw in enumerate(lines):
        t = raw.strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        bare_title = (2 <= len(t) <= 70 and len(t.split()) <= 8
                      and not t.endswith((".", "!", "?", ":", ";"))
                      and len(nxt) >= 40 and not BULLET.match(nxt))
        if t and (HEADING.match(raw) or bare_title):
            guarded.append(t + " .")
        else:
            guarded.append(raw)
    flat = re.sub(r"\n+", " ", "\n".join(guarded))
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


def _too_similar(a: str, b: str) -> bool:
    """True when two options are effectively the same content.

    Without this a deck that has both 'Kirchhoff's Laws' and 'Kirchhoff's Voltage
    Law' gives a question whose distractor IS the answer in different words, which
    is unanswerable rather than difficult.
    """
    a, b = (a or "").lower().strip(), (b or "").lower().strip()
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    ta = set(re.findall(r"[a-z]{3,}", a))
    tb = set(re.findall(r"[a-z]{3,}", b))
    if not ta or not tb:
        return False
    return len(ta & tb) / max(1, len(ta | tb)) >= 0.55


def attach_quiz(cards: List[Dict], text: str = "") -> List[Dict]:
    """Give every card an auto-written prompt, radio options, the correct index
    and an explanation grounded in the student's own notes.

    The study view walks the deck one card at a time: prompt -> pick an option ->
    press Answer -> the correct option is highlighted with the reason why. Every
    string here is derived from the uploaded material, never from outside
    knowledge, so an explanation can always be traced back to the notes.
    """
    rnd = random.Random(11)
    defs = [(c["front"], c["back"]) for c in cards
            if c.get("source") != "cloze" and len(c.get("back", "")) >= 15]
    all_backs = [c["back"] for c in cards if c.get("back")]

    # term-like pool for fill-in-the-blank options: the answer there is a word,
    # so offering whole sentences as alternatives would be nonsense
    token_pool: List[str] = []
    for candidate in all_backs + [t for t, _d in defs]:
        if 3 <= len(candidate) <= 40 and len(candidate.split()) <= 3 \
                and candidate not in token_pool:
            token_pool.append(candidate)

    for c in cards:
        correct = c.get("back", "")
        if not correct:
            continue
        if c.get("source") == "cloze":
            prompt = c["front"] if "_____" in c.get("front", "") else f"Fill in the blank: {c['front']}"
            pool = [t for t in token_pool if t != correct]
            restored = c["front"].replace("_____", correct)
            why = (f"Reading the sentence in full: \u201c{restored}\u201d \u2014 so "
                   f"\u201c{correct}\u201d is the term your notes use there.")
        else:
            term = c["front"]
            prompt = f"Which of these best describes {term}?"
            pool = [d for _t, d in defs if d != correct]
            names = [t for t, d in defs if d != correct]
            why = f"Your notes define {term} as: \u201c{correct}\u201d"
            if len(names) >= 3:
                picks = rnd.sample(names, 3)
                why += (f" The other options describe {picks[0]}, {picks[1]} "
                        f"and {picks[2]}.")
            else:
                why += "."

        # keep only distractors that are clearly different from the answer and
        # from one another, then pad the question out to four where possible
        rnd.shuffle(pool)
        chosen: List[str] = []
        for o in pool:
            if not o or o == correct or o == c.get("front"):
                continue
            if _too_similar(o, correct) or any(_too_similar(o, x) for x in chosen):
                continue
            chosen.append(o)
            if len(chosen) == 3:
                break

        opts = [correct] + chosen
        if len(opts) < 2:
            continue                      # no fair question is possible; leave the card alone
        rnd.shuffle(opts)
        c["prompt"] = prompt[:400]
        c["opts"] = [o[:260] for o in opts]
        c["answer"] = opts.index(correct)
        c["why"] = why[:600]
    return cards


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
            kit["cards"] = attach_quiz(kit["cards"], text)
            kit["summary"] = (f"{len(kit['cards'])} flashcards and {len(kit['exam'])} exam "
                              f"questions written by your local tutor model.")
            kit["fallback_reason"] = None
            return kit
        if engine == "ai":
            raise ValueError(f"The local model at {ollama_url} did not return usable JSON — "
                             f"try the 'Instant (offline rules)' engine.")

    kit = rules_kit(text)
    kit["cards"] = attach_quiz(kit["cards"], text)
    kit["fallback_reason"] = None if engine == "rules" else \
        "Local model unavailable or too slow, so these were built offline by the rules engine."
    return kit
