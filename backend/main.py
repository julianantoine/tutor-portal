"""
Tutor Portal — FastAPI backend.

Local-first tutoring SaaS for a sophomore engineering-technology course load.
- SQLite persistence (users, progress, quiz attempts, chat, assignments)
- Token auth (register/login)
- Curriculum + flashcards + quizzes from content.py
- AI tutor streaming from local Ollama (default :11437)
- Tutor/admin dashboard endpoints

Run:  python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8950
(also runnable as `python3 backend/main.py`)
"""

import json
import os
import sys
import sqlite3
import hashlib
import secrets
import time
from contextlib import contextmanager, asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

# Make `import content` work whether this is run as `python3 backend/main.py`
# or as `python3 -m uvicorn backend.main:app` (package context).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import httpx
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import content

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "tutor.db"

STATIC_DIR = BASE_DIR / "static"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11437")
TUTOR_MODEL = os.environ.get("TUTOR_MODEL", "hermes3:latest")
PORT = int(os.environ.get("PORT", "8950"))


@asynccontextmanager
async def lifespan(app):
    """Ensure the schema + seed accounts exist however the app is launched."""
    init_db()
    yield

app = FastAPI(title="Tutor Portal API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier TEXT UNIQUE NOT NULL,
    pass_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS progress (
    user_id INTEGER NOT NULL,
    unit_id TEXT NOT NULL,
    mastery REAL NOT NULL DEFAULT 0,
    quizzes_taken INTEGER NOT NULL DEFAULT 0,
    quizzes_passed INTEGER NOT NULL DEFAULT 0,
    problems_done INTEGER NOT NULL DEFAULT 0,
    last_seen TEXT,
    UNIQUE(user_id, unit_id)
);
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_code TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_code TEXT,
    unit_id TEXT,
    title TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_code TEXT,
    unit_id TEXT,
    title TEXT NOT NULL,
    notes TEXT,
    due TEXT,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'semester',
    start_date TEXT,
    end_date TEXT,
    active INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS term_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    units INTEGER NOT NULL DEFAULT 1,
    level INTEGER NOT NULL DEFAULT 1,
    topics TEXT,
    created_at TEXT NOT NULL
);
"""


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=8000")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    with db() as con:
        con.executescript(SCHEMA)
        # seed tutor + student accounts once
        row = con.execute("SELECT COUNT(*) c FROM users").fetchone()
        if row["c"] == 0:
            for ident, pw, name, role in [
                ("tutor", "tutor", "Julian (Tutor)", "tutor"),
                ("student", "student", "Student", "student"),
            ]:
                salt = secrets.token_hex(8)
                h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000).hex()
                con.execute(
                    "INSERT INTO users(identifier, pass_hash, salt, name, role, created_at) "
                    "VALUES(?,?,?,?,?,?)",
                    (ident, h, salt, name, role, now_iso()),
                )


def hash_pw(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000).hex()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class AuthIn(BaseModel):
    identifier: str
    password: str


class ChatIn(BaseModel):
    message: str
    course_code: Optional[str] = None
    unit_id: Optional[str] = None
    session_id: Optional[int] = None


class QuizIn(BaseModel):
    course_code: str
    unit_id: str
    answers: List[int]


class ProgressIn(BaseModel):
    course_code: str
    unit_id: str
    mastery: float


class AssignmentIn(BaseModel):
    user_id: int
    title: str
    course_code: Optional[str] = None
    unit_id: Optional[str] = None
    notes: Optional[str] = None
    due: Optional[str] = None


def current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1].strip()
    with db() as con:
        r = con.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?",
            (token,),
        ).fetchone()
    if not r:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return dict(r)


def require_tutor(user=Depends(current_user)):
    if user["role"] != "tutor":
        raise HTTPException(status_code=403, detail="Tutor access required")
    return user


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.post("/api/register")
def register(body: AuthIn):
    ident = body.identifier.strip().lower()
    if len(ident) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(body.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")
    salt = secrets.token_hex(8)
    h = hash_pw(body.password, salt)
    with db() as con:
        exists = con.execute("SELECT id FROM users WHERE identifier=?", (ident,)).fetchone()
        if exists:
            raise HTTPException(409, "That username is taken")
        cur = con.execute(
            "INSERT INTO users(identifier, pass_hash, salt, name, role, created_at) VALUES(?,?,?,?,?,?)",
            (ident, h, salt, body.identifier.strip(), "student", now_iso()),
        )
        uid = cur.lastrowid
        con.commit()  # release the write lock before issuing a session
        token = secrets.token_urlsafe(24)
        con.execute(
            "INSERT INTO sessions(token, user_id, created_at) VALUES(?,?,?)",
            (token, uid, now_iso()),
        )
        user = con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return {"token": token, "user": public_user(dict(user))}


@app.post("/api/login")
def login(body: AuthIn):
    ident = body.identifier.strip().lower()
    with db() as con:
        r = con.execute("SELECT * FROM users WHERE identifier=?", (ident,)).fetchone()
        if not r or hash_pw(body.password, r["salt"]) != r["pass_hash"]:
            raise HTTPException(401, "Wrong username or password")
        token = secrets.token_urlsafe(24)
        con.execute(
            "INSERT INTO sessions(token, user_id, created_at) VALUES(?,?,?)",
            (token, r["id"], now_iso()),
        )
    return {"token": token, "user": public_user(dict(r))}


@app.post("/api/logout")
def logout(user=Depends(current_user), authorization: Optional[str] = Header(None)):
    token = authorization.split(" ", 1)[1].strip()
    with db() as con:
        con.execute("DELETE FROM sessions WHERE token=?", (token,))
    return {"ok": True}


def public_user(u: dict) -> dict:
    return {"id": u["id"], "identifier": u["identifier"], "name": u["name"], "role": u["role"]}


@app.get("/api/me")
def me(user=Depends(current_user)):
    prog = get_progress(user["id"])
    return {"user": public_user(user), "progress": prog, "summary": progress_summary(prog)}


# ---------------------------------------------------------------------------
# Progress helpers
# ---------------------------------------------------------------------------

def get_progress(user_id: int) -> dict:
    with db() as con:
        rows = con.execute("SELECT * FROM progress WHERE user_id=?", (user_id,)).fetchall()
    out = {}
    for r in rows:
        out[r["unit_id"]] = {
            "mastery": r["mastery"],
            "quizzes_taken": r["quizzes_taken"],
            "quizzes_passed": r["quizzes_passed"],
            "problems_done": r["problems_done"],
            "last_seen": r["last_seen"],
        }
    return out


def progress_summary(prog: dict) -> dict:
    """Per-course average mastery + overall, for the rings on both dashboards."""
    courses = []
    total_units = 0
    total_mastery = 0.0
    for c in content.COURSES:
        m = 0.0
        for u in c["units"]:
            total_units += 1
            p = prog.get(u["id"])
            val = p["mastery"] if p else 0.0
            m += val
            total_mastery += val
        avg = m / len(c["units"]) if c["units"] else 0.0
        courses.append({"code": c["code"], "title": c["title"], "short": c["short"],
                        "accent": c["accent"], "mastery": round(avg, 1),
                        "units": len(c["units"])})
    overall = round(total_mastery / total_units, 1) if total_units else 0.0
    return {"courses": courses, "overall": overall, "units": total_units}


def upsert_progress(user_id, unit_id, mastery=None, quiz=False, passed=False, problems=0):
    with db() as con:
        r = con.execute(
            "SELECT * FROM progress WHERE user_id=? AND unit_id=?", (user_id, unit_id)
        ).fetchone()
        if not r:
            con.execute(
                "INSERT INTO progress(user_id, unit_id, mastery, quizzes_taken, quizzes_passed, problems_done, last_seen) "
                "VALUES(?,?,?,?,?,?,?)",
                (user_id, unit_id, mastery or 0.0, 1 if quiz else 0,
                 1 if passed else 0, problems, now_iso()),
            )
        else:
            new_m = r["mastery"]
            if mastery is not None:
                new_m = max(r["mastery"], mastery)
            con.execute(
                "UPDATE progress SET mastery=?, quizzes_taken=?, quizzes_passed=?, problems_done=?, last_seen=? "
                "WHERE user_id=? AND unit_id=?",
                (new_m,
                 r["quizzes_taken"] + (1 if quiz else 0),
                 r["quizzes_passed"] + (1 if (quiz and passed) else 0),
                 r["problems_done"] + problems,
                 now_iso(), user_id, unit_id),
            )


# ---------------------------------------------------------------------------
# Curriculum routes
# ---------------------------------------------------------------------------

@app.get("/api/courses")
def courses(user=Depends(current_user)):
    prog = get_progress(user["id"])
    out = []
    for c in content.COURSES:
        units = []
        for u in c["units"]:
            p = prog.get(u["id"], {})
            units.append({"id": u["id"], "title": u["title"], "summary": u["summary"],
                          "level": u.get("level", 2),
                          "mastery": p.get("mastery", 0), "quizzes_taken": p.get("quizzes_taken", 0)})
        out.append({"code": c["code"], "title": c["title"], "short": c["short"],
                    "credits": c["credits"], "accent": c["accent"], "blurb": c["blurb"],
                    "units": units})
    return {"courses": out, "levels": content.LEVELS}


@app.get("/api/course/{code}")
def course_detail(code: str, user=Depends(current_user)):
    c = content.course_by_code(code)
    if not c:
        raise HTTPException(404, "Course not found")
    prog = get_progress(user["id"])
    units = []
    for u in c["units"]:
        uu = dict(u)
        uu["mastery"] = prog.get(u["id"], {}).get("mastery", 0)
        units.append(uu)
    return {"code": c["code"], "title": c["title"], "short": c["short"], "accent": c["accent"],
            "blurb": c["blurb"], "credits": c["credits"], "units": units,
            "levels": content.LEVELS}


@app.get("/api/flashcards/{code}")
def flashcards(code: str, user=Depends(current_user)):
    cards = content.flashcards_for(code)
    if not cards:
        raise HTTPException(404, "No flashcards for that course")
    return {"cards": cards, "count": len(cards)}


@app.get("/api/quiz/{code}/{unit_id}")
def quiz(code: str, unit_id: str, user=Depends(current_user)):
    qs = content.quiz_for_unit(code, unit_id)
    if not qs:
        raise HTTPException(404, "No quiz for that unit")
    # strip the answers before sending to the client; questions are already
    # ordered easy -> hard by the difficulty layer.
    safe = [{"q": q["q"], "opts": q["opts"], "level": q.get("level", 2)} for q in qs]
    return {"course_code": code, "unit_id": unit_id, "questions": safe,
            "levels": content.LEVELS}


@app.post("/api/quiz/submit")
def quiz_submit(body: QuizIn, user=Depends(current_user)):
    bank = content.quiz_for_unit(body.course_code, body.unit_id)
    if not bank:
        raise HTTPException(404, "No quiz for that unit")
    results = []
    score = 0
    for i, q in enumerate(bank):
        given = body.answers[i] if i < len(body.answers) else -1
        ok = given == q["answer"]
        if ok:
            score += 1
        results.append({"correct": ok, "given": given, "answer": q["answer"],
                        "explain": q["explain"]})
    total = len(bank)
    pct = round(100 * score / total, 1)
    passed = pct >= 70
    with db() as con:
        con.execute(
            "INSERT INTO quiz_attempts(user_id, course_code, unit_id, score, total, detail, created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (user["id"], body.course_code, body.unit_id, score, total,
             json.dumps(results), now_iso()),
        )
    upsert_progress(user["id"], body.unit_id, mastery=pct, quiz=True, passed=passed)
    return {"score": score, "total": total, "pct": pct, "passed": passed, "results": results,
            "mastery": pct}


@app.get("/api/progress")
def progress(user=Depends(current_user)):
    prog = get_progress(user["id"])
    return {"progress": prog, "summary": progress_summary(prog)}


@app.post("/api/progress")
def set_progress(body: ProgressIn, user=Depends(current_user)):
    upsert_progress(user["id"], body.unit_id, mastery=max(0.0, min(100.0, body.mastery)))
    return {"ok": True, "progress": get_progress(user["id"])}


# ---------------------------------------------------------------------------
# AI tutor (local Ollama)
# ---------------------------------------------------------------------------

TUTOR_SYSTEM = """You are an expert, patient tutor on a student's personal engineering tutoring portal.
The student is a college sophomore in an engineering-technology program, working to raise his grades.

Your job:
- Teach clearly and Socratic-ly: explain the concept, then guide him to the answer rather than dumping it when he is practising.
- Keep it focused on the course/unit material below. Use its formulas and conventions EXACTLY.
- Show worked steps with numbers, units, and a final boxed-style answer when solving a problem.
- Calibrate to difficulty: units are tagged Foundational / Intermediate / Advanced. On a Foundational
  topic build intuition with simple numbers first; on an Advanced topic go multi-step and exam-level.
  When the student seems comfortable, escalate difficulty - that is the point of this portal.
- If he gets something wrong in practice, say exactly where the slip was - do not just re-solve it silently.
- Be encouraging but honest; he is behind and needs real progress, not flattery.
- Keep answers tight: 3-8 short paragraphs or a compact step list. No filler.

{context}
"""


def build_system_prompt(course_code, unit_id):
    ctx = content.course_context(course_code, unit_id) if course_code else ""
    if not ctx:
        # give the tutor the whole catalog outline so it can answer anything
        lines = ["AVAILABLE COURSES:"]
        for c in content.COURSES:
            lines.append(f"- {c['code']} {c['title']}: " + "; ".join(u["title"] for u in c["units"]))
        ctx = "\n".join(lines)
    return TUTOR_SYSTEM.format(context=ctx)


async def ollama_stream(messages):
    """Yield text deltas from the local Ollama /api/chat streaming endpoint.

    num_predict caps runaway generation on weaker local hardware. Some local
    models emit a reasoning trace instead of content; we prefer `content` and
    do not surface `thinking` (it is the model's scratchpad, not the answer).
    """
    payload = {"model": TUTOR_MODEL, "messages": messages, "stream": True,
               "options": {"num_predict": 700}}
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
        async with client.stream("POST", f"{OLLAMA_URL}/api/chat", json=payload) as r:
            if r.status_code != 200:
                body = (await r.aread()).decode(errors="replace")[:300]
                raise RuntimeError(f"Ollama {r.status_code}: {body}")
            async for line in r.aiter_lines():
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = obj.get("message") or {}
                delta = msg.get("content") or ""
                if delta:
                    yield delta
                if obj.get("done"):
                    break


@app.post("/api/tutor/chat")
async def tutor_chat(body: ChatIn, user=Depends(current_user)):
    """Stream the tutor reply as Server-Sent Events."""
    msg = body.message.strip()
    if not msg:
        raise HTTPException(400, "Empty message")

    # session handling (create on first message)
    session_id = body.session_id
    with db() as con:
        if not session_id:
            cur = con.execute(
                "INSERT INTO chat_sessions(user_id, course_code, unit_id, title, created_at) VALUES(?,?,?,?,?)",
                (user["id"], body.course_code, body.unit_id, msg[:60], now_iso()),
            )
            session_id = cur.lastrowid
        else:
            own = con.execute(
                "SELECT id FROM chat_sessions WHERE id=? AND user_id=?", (session_id, user["id"])
            ).fetchone()
            if not own:
                raise HTTPException(404, "Chat session not found")
        con.execute(
            "INSERT INTO chat_messages(session_id, role, content, created_at) VALUES(?,?,?,?)",
            (session_id, "user", msg, now_iso()),
        )
        con.commit()  # release write lock before the (slow) model call

    # build context: history (last 8) + system
    with db() as con:
        hist = con.execute(
            "SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY id DESC LIMIT 8",
            (session_id,),
        ).fetchall()
    history = [{"role": h["role"], "content": h["content"]} for h in reversed(hist)]
    messages = [{"role": "system", "content": build_system_prompt(body.course_code, body.unit_id)}] + history

    async def gen():
        yield f"data: {json.dumps({'session_id': session_id})}\n\n"
        acc = []
        try:
            async for delta in ollama_stream(messages):
                acc.append(delta)
                yield f"data: {json.dumps({'delta': delta})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        full = "".join(acc)
        if full:
            with db() as con:
                con.execute(
                    "INSERT INTO chat_messages(session_id, role, content, created_at) VALUES(?,?,?,?)",
                    (session_id, "assistant", full, now_iso()),
                )
        yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/chat/sessions")
def chat_sessions(user=Depends(current_user)):
    with db() as con:
        rows = con.execute(
            "SELECT id, course_code, unit_id, title, created_at FROM chat_sessions "
            "WHERE user_id=? ORDER BY id DESC", (user["id"],)
        ).fetchall()
    return {"sessions": [dict(r) for r in rows]}


@app.get("/api/chat/session/{sid}")
def chat_session(sid: int, user=Depends(current_user)):
    with db() as con:
        s = con.execute("SELECT * FROM chat_sessions WHERE id=? AND user_id=?", (sid, user["id"])).fetchone()
        if not s:
            raise HTTPException(404, "Session not found")
        msgs = con.execute(
            "SELECT role, content, created_at FROM chat_messages WHERE session_id=? ORDER BY id", (sid,)
        ).fetchall()
    return {"session": dict(s), "messages": [dict(m) for m in msgs]}


@app.get("/api/tutor/status")
def tutor_status(user=Depends(current_user)):
    """Report the tutor model and whether Ollama answers."""
    ok = False
    models = []
    try:
        with httpx.Client(timeout=4.0) as client:
            r = client.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                ok = True
                models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return {"ollama_url": OLLAMA_URL, "model": TUTOR_MODEL, "online": ok,
            "model_present": TUTOR_MODEL in models, "models": models[:40]}


# ---------------------------------------------------------------------------
# Terms / semesters — let the student register their load each term and add
# courses the catalog doesn't cover, with a generated progressive study plan.
# ---------------------------------------------------------------------------

class TermIn(BaseModel):
    name: str
    kind: Optional[str] = "semester"          # semester | quarter | term
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    make_active: Optional[bool] = True


class TermCourseIn(BaseModel):
    code: str
    title: str
    units: Optional[int] = 1
    level: Optional[int] = 1
    topics: Optional[List[str]] = None


def _term_courses(con, term_id):
    rows = con.execute(
        "SELECT id, code, title, units, level, topics FROM term_courses WHERE term_id=? ORDER BY level, id",
        (term_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/terms")
def list_terms(user=Depends(current_user)):
    with db() as con:
        rows = con.execute(
            "SELECT * FROM terms WHERE user_id=? ORDER BY active DESC, id DESC", (user["id"],)
        ).fetchall()
        out = []
        for r in rows:
            t = dict(r)
            t["courses"] = _term_courses(con, r["id"])
            out.append(t)
    return {"terms": out, "catalog_levels": content.LEVELS}


@app.post("/api/terms")
def create_term(body: TermIn, user=Depends(current_user)):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Term needs a name")
    kind = (body.kind or "semester").lower()
    if kind not in ("semester", "quarter", "term", "trimester"):
        kind = "semester"
    with db() as con:
        if body.make_active:
            con.execute("UPDATE terms SET active=0 WHERE user_id=?", (user["id"],))
        cur = con.execute(
            "INSERT INTO terms(user_id, name, kind, start_date, end_date, active, created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (user["id"], name, kind, body.start_date, body.end_date,
             1 if body.make_active else 0, now_iso()),
        )
        tid = cur.lastrowid
    return {"ok": True, "id": tid}


@app.post("/api/terms/{tid}/activate")
def activate_term(tid: int, user=Depends(current_user)):
    with db() as con:
        own = con.execute("SELECT id FROM terms WHERE id=? AND user_id=?", (tid, user["id"])).fetchone()
        if not own:
            raise HTTPException(404, "Term not found")
        con.execute("UPDATE terms SET active=0 WHERE user_id=?", (user["id"],))
        con.execute("UPDATE terms SET active=1 WHERE id=?", (tid,))
    return {"ok": True}


@app.delete("/api/terms/{tid}")
def delete_term(tid: int, user=Depends(current_user)):
    with db() as con:
        own = con.execute("SELECT id FROM terms WHERE id=? AND user_id=?", (tid, user["id"])).fetchone()
        if not own:
            raise HTTPException(404, "Term not found")
        con.execute("DELETE FROM term_courses WHERE term_id=?", (tid,))
        con.execute("DELETE FROM terms WHERE id=?", (tid,))
    return {"ok": True}


@app.get("/api/terms/{tid}/courses")
def term_courses(tid: int, user=Depends(current_user)):
    with db() as con:
        own = con.execute("SELECT * FROM terms WHERE id=? AND user_id=?", (tid, user["id"])).fetchone()
        if not own:
            raise HTTPException(404, "Term not found")
        courses = _term_courses(con, tid)
    return {"term": dict(own), "courses": courses}


@app.post("/api/terms/{tid}/courses")
def add_term_course(tid: int, body: TermCourseIn, user=Depends(current_user)):
    code = body.code.strip().upper()
    title = body.title.strip()
    if not code or not title:
        raise HTTPException(400, "Course needs a code and a title")
    topics = body.topics or []
    with db() as con:
        own = con.execute("SELECT id FROM terms WHERE id=? AND user_id=?", (tid, user["id"])).fetchone()
        if not own:
            raise HTTPException(404, "Term not found")
        cur = con.execute(
            "INSERT INTO term_courses(term_id, code, title, units, level, topics, created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (tid, code, title, max(1, body.units or 1), max(1, min(3, body.level or 1)),
             json.dumps(topics), now_iso()),
        )
        cid = cur.lastrowid
    return {"ok": True, "id": cid}


@app.delete("/api/term-courses/{cid}")
def delete_term_course(cid: int, user=Depends(current_user)):
    with db() as con:
        row = con.execute(
            "SELECT tc.id FROM term_courses tc JOIN terms t ON t.id = tc.term_id "
            "WHERE tc.id=? AND t.user_id=?", (cid, user["id"])
        ).fetchone()
        if not row:
            raise HTTPException(404, "Course not found")
        con.execute("DELETE FROM term_courses WHERE id=?", (cid,))
    return {"ok": True}


@app.get("/api/terms/{tid}/study-plan")
def term_study_plan(tid: int, user=Depends(current_user)):
    """A progressive study plan across every course in the term, easy -> hard.

    Catalog courses contribute their authored units (already level-tagged);
    custom courses contribute generated units drawn from the topics the student
    typed, so every course in the term is workable.
    """
    with db() as con:
        own = con.execute("SELECT * FROM terms WHERE id=? AND user_id=?", (tid, user["id"])).fetchone()
        if not own:
            raise HTTPException(404, "Term not found")
        courses = _term_courses(con, tid)

    plan = []
    for tc in courses:
        cat = content.course_by_code(tc["code"])
        if cat:
            units = [{"n": i + 1, "id": u["id"], "title": u["title"], "level": u.get("level", 2),
                      "summary": u["summary"], "custom": False}
                     for i, u in enumerate(cat["units"])]
            plan.append({"course": cat["title"], "code": cat["code"], "custom": False,
                         "level": max(u["level"] for u in units) if units else 1, "units": units})
        else:
            topics = []
            try:
                topics = json.loads(tc.get("topics") or "[]")
            except Exception:
                topics = []
            n = max(1, tc.get("units") or 1)
            base = tc.get("level") or 1
            topics = [t for t in topics if str(t).strip()]
            units = []
            for i in range(n):
                # ramp difficulty across the generated units, clamped to 1..3
                lvl = min(3, max(1, base + (1 if i >= n // 2 else 0)))
                title = topics[i] if i < len(topics) else f"{tc['title']} — Part {i + 1}"
                units.append({
                    "n": i + 1, "id": None, "title": title, "level": lvl, "custom": True,
                    "summary": "Custom unit you added for this term. Use the AI tutor to work it, "
                               "and add practice problems as you go.",
                })
            plan.append({"course": tc["title"], "code": tc["code"], "custom": True,
                         "level": base, "units": units})

    # order courses easy -> hard, and give one interleaved weekly sequence
    plan.sort(key=lambda c: c["level"])
    sequence = []
    week = 1
    # round-robin the courses so weeks interleave subjects (better for retention)
    max_units = max((len(c["units"]) for c in plan), default=0)
    for i in range(max_units):
        for c in plan:
            if i < len(c["units"]):
                u = c["units"][i]
                sequence.append({"week": week, "course": c["course"], "code": c["code"],
                                 "unit": u["title"], "level": u["level"], "custom": u["custom"]})
                week += 0  # same week groups the parallel units
        week += 1
    # renumber: give each course-row its own week index for clarity
    for idx, s in enumerate(sequence):
        s["step"] = idx + 1
    return {"term": dict(own), "plan": plan, "sequence": sequence,
            "levels": content.LEVELS}


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

@app.get("/api/assignments")
def assignments(user=Depends(current_user)):
    with db() as con:
        rows = con.execute(
            "SELECT * FROM assignments WHERE user_id=? ORDER BY done, "
            "CASE WHEN due IS NULL OR due='' THEN 1 ELSE 0 END, due",
            (user["id"],),
        ).fetchall()
    return {"assignments": [dict(r) for r in rows]}


@app.post("/api/assignments")
def make_assignment(body: AssignmentIn, tutor=Depends(require_tutor)):
    with db() as con:
        cur = con.execute(
            "INSERT INTO assignments(user_id, course_code, unit_id, title, notes, due, created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (body.user_id, body.course_code, body.unit_id, body.title, body.notes, body.due, now_iso()),
        )
        aid = cur.lastrowid
    return {"ok": True, "id": aid}


@app.post("/api/assignments/{aid}/toggle")
def toggle_assignment(aid: int, user=Depends(current_user)):
    with db() as con:
        r = con.execute("SELECT * FROM assignments WHERE id=?", (aid,)).fetchone()
        if not r:
            raise HTTPException(404, "Not found")
        if r["user_id"] != user["id"] and user["role"] != "tutor":
            raise HTTPException(403, "Not your assignment")
        con.execute("UPDATE assignments SET done=? WHERE id=?", (0 if r["done"] else 1, aid))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Tutor / admin dashboard
# ---------------------------------------------------------------------------

@app.get("/api/admin/students")
def admin_students(tutor=Depends(require_tutor)):
    with db() as con:
        rows = con.execute("SELECT * FROM users WHERE role='student' ORDER BY id").fetchall()
    out = []
    for r in rows:
        uid = r["id"]
        prog = get_progress(uid)
        summ = progress_summary(prog)
        with db() as con:
            n_quiz = con.execute("SELECT COUNT(*) c FROM quiz_attempts WHERE user_id=?", (uid,)).fetchone()["c"]
            last = con.execute(
                "SELECT created_at FROM quiz_attempts WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)
            ).fetchone()
            n_msg = con.execute(
                "SELECT COUNT(*) c FROM chat_messages m JOIN chat_sessions s ON s.id=m.session_id "
                "WHERE s.user_id=?", (uid,)
            ).fetchone()["c"]
        # weakest units (for the tutor to target)
        weak = []
        for c in content.COURSES:
            for u in c["units"]:
                m = prog.get(u["id"], {}).get("mastery", 0)
                weak.append({"unit_id": u["id"], "title": u["title"], "course": c["short"], "mastery": m})
        weak.sort(key=lambda x: x["mastery"])
        out.append({
            "user": public_user(dict(r)),
            "summary": summ,
            "quizzes": n_quiz,
            "messages": n_msg,
            "last_active": last["created_at"] if last else None,
            "weakest": weak[:4],
        })
    return {"students": out}


@app.get("/api/admin/student/{uid}")
def admin_student(uid: int, tutor=Depends(require_tutor)):
    with db() as con:
        r = con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        if not r:
            raise HTTPException(404, "Student not found")
        quizzes = con.execute(
            "SELECT course_code, unit_id, score, total, created_at FROM quiz_attempts "
            "WHERE user_id=? ORDER BY id DESC LIMIT 50", (uid,)
        ).fetchall()
        assigns = con.execute(
            "SELECT * FROM assignments WHERE user_id=? ORDER BY done, due", (uid,)
        ).fetchall()
        chats = con.execute(
            "SELECT id, title, course_code, unit_id, created_at FROM chat_sessions "
            "WHERE user_id=? ORDER BY id DESC LIMIT 20", (uid,)
        ).fetchall()
    prog = get_progress(uid)
    return {
        "user": public_user(dict(r)),
        "progress": prog,
        "summary": progress_summary(prog),
        "quiz_history": [dict(q) for q in quizzes],
        "assignments": [dict(a) for a in assigns],
        "chat_sessions": [dict(c) for c in chats],
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "time": now_iso(), "model": TUTOR_MODEL, "ollama": OLLAMA_URL}


# ---------------------------------------------------------------------------
# Static SPA — MUST be declared LAST (Starlette matches routes in order, so
# every /api/* route above keeps priority and "/" serves the app + assets).
# ---------------------------------------------------------------------------

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
