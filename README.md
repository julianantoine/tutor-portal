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

- **Student portal** — course/unit browser, Learn tabs (concepts → formulas → worked examples → traps → practice), flip flashcards, multiple-choice quizzes graded at 70%, mastery rings.
- **Notes → Study Kit** — the student drops in their *own* notes (paste, `.txt`/`.md` upload, or a PDF) and the portal returns a flashcard deck plus a graded practice exam on exactly that material. Two engines: an offline extractive builder that answers in milliseconds, and the local AI tutor for richer, better-phrased cards. Every exam run is logged for the tutor dashboard.
- **Progressive difficulty** — every unit, quiz question, worked example and practice problem is tagged **Foundational → Intermediate → Advanced**. Each unit carries two worked examples (one that builds the idea, one exam-level), quizzes are ordered easy → hard, and the AI tutor escalates with you.
- **Semester / quarter planner** — register each term, list its courses, and add **any course you type**. You get a study plan that orders every subject easy → hard and interleaves subjects week by week.
- **AI tutor** — streaming chat grounded in the selected course/unit material, powered by a **local Ollama model** (default `hermes3:latest` on `:11437`). Free and offline.
- **Tutor/admin dashboard** — per-student mastery across all courses, quiz history, activity counts, weakest units to target, assignment authoring.
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
│   ├── notes.py       # Notes → Study Kit: PDF/text intake + the two generators
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
GET  /api/terms               POST /api/terms            DELETE /api/terms/{id}
POST /api/terms/{id}/activate GET  /api/terms/{id}/courses
POST /api/terms/{id}/courses  GET  /api/terms/{id}/study-plan
DELETE /api/term-courses/{id}
GET  /api/assignments         POST /api/assignments      POST /api/assignments/{id}/toggle
GET  /api/admin/students      GET  /api/admin/student/{uid}
GET  /api/notes               POST /api/notes           GET    /api/notes/{id}
POST /api/notes/{id}/generate POST /api/notes/{id}/exam DELETE /api/notes/{id}
GET  /api/health
```

### How the difficulty progression works

`backend/difficulty.py` is the single place that owns the ramp:

- `UNIT_LEVELS` — each unit's tier (1-3), authored **monotonic** per course so working units in
  syllabus order reads easy → hard.
- `QUIZ_LEVELS` — per-course list aligning to `QUIZ_BANK` order; questions are then **sorted** so
  every quiz runs foundational → advanced.
- `PRACTICE_TAGS` — tags the authored practice problems.
- `UNIT_EXTRA` — a **harder second worked example** plus extra practice for every unit, so the
  ladder is real content, not a label.

`content.py` merges all of it at import, and `content.LEVELS` is the one source of the
labels/colours used by the app, the hosted demo, and the study-plan generator.

### Terms, custom courses, and the study plan

A term belongs to a user and holds a course list. A course whose `code` matches the catalog
contributes its authored units; any other code is a **custom course** — its `topics` become unit
names and it gets a generated ramp from the `level` you pick. `/api/terms/{id}/study-plan` then
returns, per course, the ordered units plus a **weekly interleaved sequence** across all courses
(research on interleaving: a little of each subject each week beats blocking one at a time).

## Notes → Study Kit

`backend/notes.py` owns this. Upload path: paste text, or send a `.txt`/`.md`
body (read in the browser) or a base64 PDF (text layer extracted server-side with
`pypdf`). The note row is written immediately with `gen_status='running'` and the
build is handed to a 2-worker thread pool, so the request returns at once and the
client polls `GET /api/notes/{id}` until the status flips to `ready`.

Two generators, picked by the `engine` field:

- `rules` — fully offline and instant. Mines definition-shaped lines
  (`term — definition`, `term: definition`), markdown headings followed by prose,
  and bullet lists; then makes **cloze** cards by blanking the most memorable
  token in a sentence. The exam is built from those same pairs: *"which of these
  best describes X?"* with three distractors drawn from the other definitions in
  your notes, falling back to cloze multiple-choice and finally to true/false so
  an exam always exists.
- `ai` — the local tutor model is asked for strict JSON grounded **only** in the
  notes. Local models drift, repeat keys and truncate mid-array, so
  `_extract_json` falls back to brace-matching each complete object out of the
  array and keeping the good ones; anything that still fails validation drops to
  the `rules` kit rather than erroring out. `auto` tries the model first and
  quietly uses `rules` if the model is offline or too slow.

On this CPU-only box an 8B model needs minutes per generation, which is why the
UI defaults to `rules` and the AI engines are opt-in. Tune with
`NOTES_AI_TIMEOUT` (seconds) and `TUTOR_MODEL`.

## Importing study material

PDFs are read page by page so a deck's running footer can be recognised and
dropped. Removed on import: page numbers, `©`/copyright/'all rights reserved'
lines, `Slide N` / `Figure N` markers, bare URLs, course-code lines
(`PHY 202 — Lecture 4`, `Prof. …`, `Fall 2026`), and any short line that repeats
on 40% or more of the pages (compared with digits collapsed, so 'Slide 12' and
'Slide 13' count as the same line). Long sentences are never dropped by the
repetition rule, so a repeated teaching line survives. A 6-slide physics deck
imports as 213 words of content instead of 333 words of content plus furniture.

Two related guards worth knowing about:

* Sentences hard-wrapped by the PDF layout are rejoined — unless the line is a
  short title followed by a proper sentence, which is left alone so the title
  can be paired with the paragraph under it.
* `X = Y` inside a prose sentence is not treated as a definition, so '…potential
  difference, C = Q/V, measured in farads.' does not produce the flashcard
  `difference, C → Q/V`.

## Studying a deck

Each flashcard is studied as a question, built at generation time:

1. an automatic prompt — `Which of these best describes <term>?` for a
   definition card, or the sentence with the blank in it for a cloze card;
2. four radio options, one correct;
3. an **Answer** button that marks the pick green/red, locks the options and
   shows *why* — the definition the notes give for that term, plus which of the
   other options describe which other concepts, so a wrong guess is
   explainable rather than just wrong;
4. **Next** to move on, with a running `correct / answered` score.

Two guards keep the questions fair, both in `attach_quiz()`:

* a distractor that restates the answer in other words is dropped — a deck
  holding both `Kirchhoff's Laws` and `Kirchhoff's Voltage Law` otherwise
  produced a question whose distractor *was* the answer;
* a fill-in-the-blank card only ever offers term-length alternatives, never
  whole sentences.

Kits generated before this existed have no options and fall back to the plain
flip card, so old notes keep working.

## Deployment (Railway + custom domain)

Live at **https://app.collegegradelifter.com** — Railway project `gradeboost`,
service `tutor-portal`, built from the `Dockerfile`, with a volume mounted at
`/app/data` so the SQLite db survives redeploys.

Deploy with the CLI:

```bash
railway up --detach        # from this directory, linked to the project
railway logs               # uvicorn output / tracebacks
```

Environment: `OLLAMA_URL` / `TUTOR_MODEL` are unset in the cloud, so the AI
engines are offline there and `auto` falls back to the offline rules engine —
the Notes → Study Kit feature still works in full.

### Adding a custom domain — Railway needs TWO record types

`railway domain <name>` prints the required records. **Add both:**

| Type  | Host                                | Value                        |
|-------|-------------------------------------|------------------------------|
| CNAME | the subdomain (`app`, `www`, …)     | `<hash>.up.railway.app`      |
| TXT   | `_railway-verify.<subdomain>`       | `railway-verify=<hex token>` |

The TXT is not optional. With only the CNAME in place the record shows
`PROPAGATED` and the certificate sits at `VALIDATING_OWNERSHIP` forever, and
Railway answers `404` on the custom domain even though DNS resolves. The token
is masked in `railway domain status` output — read it via `railway api` with a
`customDomain(id, projectId) { status { verificationToken } }` query.

### Network Solutions DNS caveats

- **No CNAME at the apex, no ALIAS/ANAME support.** Railway requires
  CNAME-flattening or an ALIAS for a root domain, so a bare domain cannot be
  pointed at Railway while NS runs the DNS. Use a subdomain (`app.`) instead, or
  move DNS to a provider with CNAME flattening (Cloudflare) — the registration
  can stay at NS.
- **The hosting connection re-adds `A @` and `A www`.** Deleting them in the DNS
  panel appears to work, but they come back, and a CNAME plus an A at the same
  name is an invalid record set — resolvers then split between Railway and the
  NS "Web Page Under Construction" parking page. Pick a hostname NS does not
  manage (`app`) rather than fighting it.
- The DNS panel's **Add Advanced DNS Record** flow only offers `@`, `www` and
  **Other Host** — use Other Host for anything else, and note the dialog shows a
  specific validation error (e.g. the A/CNAME conflict) that names the problem.
- `railway domain status` flapping between `PROPAGATED` and `REQUIRES_UPDATE` is
  just their checker sampling resolvers with mismatched caches; the authoritative
  answer from `ns61.worldnic.com` is the one that matters.

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
