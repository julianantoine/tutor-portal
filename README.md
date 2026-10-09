# Tutor Portal

A local-first **tutoring SaaS** for a sophomore engineering-technology course load.
Curriculum, worked examples, flashcards, graded quizzes and a **local AI tutor** —
in one browser app, running entirely on your own machine (no cloud, no API bill).

## The six courses

| Code | Course | Units | What it covers |
|------|--------|------:|----------------|
| **MTH-202** | Calculus II | 6 | Integration techniques, improper integrals & applications, sequences & series, power/Taylor series, parametric & polar curves, first-order ODEs |
| **PHY-202** | Physics II (Electricity & Magnetism) | 6 | Charge/force/field, Gauss's law, potential & capacitance, DC circuits, magnetism & induction, inductance/AC/EM waves |
| **CCD-101** | Character, Career and Self Development | 5 | Engineering ethics (NSPE), technical communication, teamwork, career readiness, growth mindset |
| **MD-102** | Modeling and Design | 5 | Design process, visualization/sketching, CAD & solid modeling, drawings & tolerances, DFM & prototyping |
| **SM-201** | Static Modeling of Mechanical Systems | 6 | Vectors & force systems, particle equilibrium, rigid bodies, trusses, frames/friction, centroids & moments of inertia |
| **EM-202** | Engineering Materials | 6 | Bonding, crystal structures & defects, mechanical properties & testing, phase diagrams & heat treatment, failure modes, materials selection |

**34 units · 55 quiz questions · 315 flashcards** — every unit has key concepts,
formulas with notes, a fully worked example, common traps, and practice problems.

## Features

- **Student portal** — course/unit browser, Learn tabs (concepts → formulas → worked example → traps → practice), flip flashcards, multiple-choice quizzes graded at 70%, mastery rings.
- **AI tutor** — streaming chat grounded in the selected course/unit material, powered by a **local Ollama model** (default `qwen3.5:27b` on `:11437`). Free and offline.
- **Tutor/admin dashboard** — per-student mastery across all four courses, quiz history, activity counts, weakest units to target, assignment authoring.
- **Assignments** — the tutor sets work; the student checks it off.
- **Auth** — username/password with PBKDF2 hashing, token sessions in SQLite.

## Run it

```bash
./start.sh            # starts the server on :8950 and opens the browser
```

Or manually:

```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8950
```

Then open <http://127.0.0.1:8950/> (or `http://<lan-ip>:8950/` from a phone/laptop on the same network).

### Demo / seed accounts

| Username | Password | Role |
|----------|----------|------|
| `antoine` | (your set password) | full tutor access |
| `student` | `student` | student view |
| `tutor` | `tutor` | tutor dashboard |

New students can self-register on the sign-in screen. The hosted GitHub Pages demo
(`docs/`) also has a register/login that stores accounts **in your browser only**.

### The AI tutor needs Ollama

The tutor calls an OpenAI-compatible Ollama server:

- `OLLAMA_URL` — default `http://localhost:11437`
- `TUTOR_MODEL` — default `hermes3:latest`

Start Ollama, then `ollama pull <model>` if the model isn't present. The status dot
in the top bar turns green when the tutor server answers. Change the model with:

```bash
TUTOR_MODEL=llama3.2 ./start.sh      # smaller / faster
```

Note: this box (Xeon + 4 GB Quadro) is CPU-bound for large models — a 27B model is
too slow to be usable interactively. Small-to-mid models (≈4–12B) respond in seconds.
Reasoning models (e.g. `gemma4`) stream their output into a separate `thinking` field
and may return empty `content`; prefer an instruct model like `hermes3` or `llama3.2`.

## Architecture

Two-process-free: **one FastAPI server serves both the API and the SPA** (the
`StaticFiles` mount is declared *last*, after every `/api/*` route, so the API keeps
priority and `/` serves `index.html` + assets). Same-origin fetches, so no CORS config.

```
tutor-portal/
├── backend/
│   ├── main.py        # FastAPI: auth, curriculum, quiz, tutor SSE, admin, assignments
│   └── content.py     # the curriculum: courses → units → concepts/formulas/examples/quizzes
├── static/
│   ├── index.html     # SPA shell + auth screen
│   ├── styles.css     # clean/restrained design system
│   └── app.js         # views, routing, streaming chat, quizzes
├── data/              # SQLite db + server.log (gitignored)
├── start.sh           # idempotent launcher
└── README.md
```

### API surface

```
POST /api/register            POST /api/login            POST /api/logout
GET  /api/me                  GET  /api/courses          GET  /api/course/{code}
GET  /api/flashcards/{code}   GET  /api/quiz/{code}/{unit}
POST /api/quiz/submit         GET  /api/progress         POST /api/progress
POST /api/tutor/chat          (SSE stream)               GET  /api/tutor/status
GET  /api/chat/sessions       GET  /api/chat/session/{id}
GET  /api/assignments         POST /api/assignments      POST /api/assignments/{id}/toggle
GET  /api/admin/students      GET  /api/admin/student/{uid}
GET  /api/health
```

## Editing the curriculum

Everything the student sees comes from **`backend/content.py`**. Unit topics follow the
standard catalog treatment of each course title — **swap in the actual syllabus topics
where they differ**; because the data model is plain dicts, an edit there flows to the
Learn tabs, the flashcards, and the AI tutor's grounding context at once.

A quiz question is graded server-side and the **best** score is kept as the unit's
mastery, so retakes can only help.

## Honest boundaries

- **Local-only by default.** It binds `0.0.0.0` so a phone on the same LAN can reach it,
  but there is no TLS and no rate-limiting — don't expose the port to the public internet
  as-is.
- **AI answers are model-generated**, grounded on the unit text but not infallible —
  the tutor is a study aid, not a substitute for the coursework.
- Curriculum content was authored for this build; verify it against the real syllabus
  before relying on it for graded work.
