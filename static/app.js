/* =========================================================================
   Tutor Portal — single-page app
   Same-origin API (the FastAPI server serves this file at "/"), so no CORS
   config is needed; every call is relative to window.location.origin.
   ========================================================================= */

const API = '';                       // same origin
const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const state = {
  token: localStorage.getItem('tp_token') || null,
  user: null,
  courses: [],
  progress: {},
  summary: null,
  view: { name: 'overview', code: null, unit: null, tab: 'learn' },
  chat: { sessionId: null, course: null, unit: null, streaming: false },
  flashcards: { deck: [], idx: 0, flipped: false },
};

/* ------------------------------------------------------------ helpers --- */
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (state.token) headers.Authorization = 'Bearer ' + state.token;
  const res = await fetch(API + path, { ...opts, headers });
  if (res.status === 401) { logout(true); throw new Error('Session expired'); }
  const txt = await res.text();
  let data = null;
  try { data = txt ? JSON.parse(txt) : null; } catch { data = { raw: txt }; }
  if (!res.ok) throw new Error((data && (data.detail || data.error)) || `HTTP ${res.status}`);
  return data;
}
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pctColor = p => p >= 70 ? 'var(--green)' : p >= 40 ? 'var(--amber)' : 'var(--red)';

/* difficulty helpers (1 Foundational · 2 Intermediate · 3 Advanced) */
const LEVELS = {
  1: { name: 'Foundational', short: 'Easy',   cls: 'lvl-1' },
  2: { name: 'Intermediate', short: 'Medium', cls: 'lvl-2' },
  3: { name: 'Advanced',     short: 'Hard',   cls: 'lvl-3' },
};
const lvlName = n => (LEVELS[n] || LEVELS[2]).name;
function lvlBadge(n) {
  const L = LEVELS[n] || LEVELS[2];
  return `<span class="lvl ${L.cls}" title="${L.name}"><span class="lvl-dot">${
    [1,2,3].map(i => `<i class="${i <= n ? 'on l' + i : ''}"></i>`).join('')
  }</span>${L.short}</span>`;
}
const levelLegend = () => `<div class="level-legend">
  <span>${lvlBadge(1)} ${LEVELS[1].name} — start here</span>
  <span>${lvlBadge(2)} ${LEVELS[2].name} — apply the concept</span>
  <span>${lvlBadge(3)} ${LEVELS[3].name} — multi-step / exam level</span>
</div>`;

/* ================================================================ AUTH == */
let authMode = 'login';

function setAuthMode(mode) {
  authMode = mode;
  $$('#authSeg .seg-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  $('#authSubmit').textContent = mode === 'login' ? 'Sign in' : 'Create account';
}

$('#authSeg').addEventListener('click', e => {
  const b = e.target.closest('.seg-btn');
  if (b) setAuthMode(b.dataset.mode);
});

$('#authForm').addEventListener('submit', async e => {
  e.preventDefault();
  const err = $('#authErr'); err.hidden = true;
  const identifier = $('#authUser').value.trim();
  const password = $('#authPass').value;
  const btn = $('#authSubmit'); btn.disabled = true; btn.textContent = '…';
  try {
    const data = await api('/api/' + authMode, { method: 'POST', body: JSON.stringify({ identifier, password }) });
    state.token = data.token;
    localStorage.setItem('tp_token', data.token);
    state.user = data.user;
    await enterApp();
  } catch (ex) {
    err.textContent = ex.message; err.hidden = false;
  } finally {
    btn.disabled = false; setAuthMode(authMode);
  }
});

function logout(silent) {
  if (state.token && !silent) api('/api/logout', { method: 'POST' }).catch(() => {});
  state.token = null; state.user = null;
  localStorage.removeItem('tp_token');
  $('#appView').hidden = true; $('#authView').hidden = false;
  if (!silent) setAuthMode('login');
}
$('#logoutBtn').addEventListener('click', () => logout(false));

/* =============================================================== BOOT == */
async function boot() {
  renderAsideCourses();
  if (!state.token) { $('#authView').hidden = false; return; }
  try {
    const me = await api('/api/me');
    state.user = me.user;
    await enterApp();
  } catch { logout(true); }
}

function renderAsideCourses() {
  // static list on the auth screen — the catalog lives in the backend, but the
  // four course titles are fixed for this build, so list them without a call.
  const courses = [
    ['#52525b', 'Character, Career & Self Development', '2 cr · ethics, communication, career'],
    ['#71717a', 'Modeling and Design', '3 cr · design process, CAD, drawings'],
    ['#3f3f46', 'Static Modeling of Mechanical Systems', '3 cr · statics, trusses, friction'],
    ['#a1a1aa', 'Engineering Materials', '3 cr · bonding, phases, failure, selection'],
    ['#4b5563', 'Calculus II', '4 cr · integration, series, polar, ODEs'],
    ['#374151', 'Physics II (Electricity & Magnetism)', '4 cr · fields, circuits, magnetism'],
  ];
  $('#asideCourses').innerHTML = courses.map(([c, t, s]) =>
    `<li><span class="dot" style="background:${c}"></span><div><div>${esc(t)}</div><div class="a-sub">${esc(s)}</div></div></li>`
  ).join('');
}

async function enterApp() {
  $('#authView').hidden = true;
  $('#appView').hidden = false;
  $('#whoami').textContent = state.user.name || state.user.identifier;
  const rp = $('#rolePill');
  rp.textContent = state.user.role;
  rp.classList.toggle('tutor', state.user.role === 'tutor');
  $$('.tutor-only').forEach(el => el.hidden = state.user.role !== 'tutor');
  await refreshData();
  navigate('overview');
  pollTutorStatus();
}

async function refreshData() {
  const [c, p] = await Promise.all([api('/api/courses'), api('/api/progress')]);
  state.courses = c.courses;
  state.progress = p.progress;
  state.summary = p.summary;
  renderNav();
  renderRing();
  refreshAssignBadge();
}

function renderNav() {
  $('#navCourses').innerHTML =
    `<div class="nav-label">My courses</div>` +
    state.courses.map(c => {
      const avg = Math.round(state.summary.courses.find(x => x.code === c.code)?.mastery || 0);
      const active = state.view.name === 'course' && state.view.code === c.code ? ' active' : '';
      return `<a class="nav-item${active}" data-course="${esc(c.code)}">
        <span class="nav-dot" style="background:${c.accent}"></span>
        <span>${esc(c.short)}</span>
        <span class="m-pct">${avg}%</span></a>`;
    }).join('');
  $$('#navCourses .nav-item').forEach(a => a.addEventListener('click', () => navigate('course', { code: a.dataset.course })));
  markActiveNav();
}

function markActiveNav() {
  $$('.nav-item').forEach(a => {
    const v = a.dataset.view, c = a.dataset.course;
    let active = false;
    if (c) active = state.view.name === 'course' && state.view.code === c;
    else if (v) active = state.view.name === v;
    a.classList.toggle('active', active);
  });
}

function renderRing() {
  const pct = state.summary?.overall || 0;
  const circ = 2 * Math.PI * 52;          // r = 52
  const el = $('#overallRing');
  el.style.strokeDasharray = circ;
  el.style.strokeDashoffset = circ * (1 - pct / 100);
  $('#overallPct').textContent = Math.round(pct) + '%';
}

async function refreshAssignBadge() {
  try {
    const a = await api('/api/assignments');
    const open = a.assignments.filter(x => !x.done).length;
    const b = $('#assignBadge');
    b.hidden = open === 0; b.textContent = open;
  } catch {}
}

async function pollTutorStatus() {
  try {
    const s = await api('/api/tutor/status');
    const el = $('#tutorStatus');
    el.className = 'tutor-status ' + (s.online ? 'on' : 'off');
    el.title = s.online
      ? `Local AI tutor online — ${s.model} @ ${s.ollama_url}`
      : `Tutor offline — is Ollama running at ${s.ollama_url}?`;
  } catch {}
}

/* ============================================================ ROUTER == */
const navViews = {
  overview:   () => viewOverview(),
  course:     () => viewCourse(),
  unit:       () => viewUnit(),
  tutor:      () => viewTutor(),
  terms:      () => viewTerms(),
  assignments:() => viewAssignments(),
  dashboard:  () => viewDashboard(),
};

async function navigate(name, opts = {}) {
  state.view = { name, code: opts.code ?? state.view.code, unit: opts.unit ?? null, tab: opts.tab || 'learn' };
  if (name !== 'unit') state.view.unit = null;
  markActiveNav();
  $('#sidebar').classList.remove('open');
  window.scrollTo(0, 0);
  const el = $('#content');
  el.innerHTML = `<div class="loading">Loading…</div>`;
  try {
    await navViews[name]();
  } catch (ex) {
    el.innerHTML = `<div class="empty">Could not load: ${esc(ex.message)}</div>`;
  }
}

$('#menuBtn').addEventListener('click', () => $('#sidebar').classList.toggle('open'));

$$('.nav-item[data-view]').forEach(a => a.addEventListener('click', () => {
  if (a.dataset.view === 'tutor' && state.user.role !== 'tutor') return;
  navigate(a.dataset.view);
}));

/* ========================================================== OVERVIEW == */
function viewOverview() {
  const s = state.summary;
  const weakest = [];
  for (const c of state.courses) for (const u of c.units)
    weakest.push({ ...u, course: c, mastery: state.progress[u.id]?.mastery || 0 });
  weakest.sort((a, b) => a.mastery - b.mastery);

  const quizzesTaken = Object.values(state.progress).reduce((n, p) => n + p.quizzes_taken, 0);
  const passed = Object.values(state.progress).reduce((n, p) => n + p.quizzes_passed, 0);

  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow">Welcome back, ${esc((state.user.name || '').split(' ')[0] || state.user.identifier)}</div>
      <h1>Your grade-recovery plan</h1>
      <p>${s.units} units across ${state.courses.length} courses. Work a unit top to bottom — read the concepts, drill the flashcards, pass the quiz at 70%, then ask the AI tutor about anything that didn't click.</p>
    </div>

    <div class="grid grid-4" style="margin-bottom:26px">
      <div class="card stat-card"><div class="big">${Math.round(s.overall)}%</div><div class="lbl">Overall mastery</div></div>
      <div class="card stat-card"><div class="big">${passed}<span class="muted" style="font-size:19px">/${quizzesTaken}</span></div><div class="lbl">Quizzes passed</div></div>
      <div class="card stat-card"><div class="big">${s.units}</div><div class="lbl">Units to master</div></div>
      <div class="card stat-card"><div class="big">${state.courses.length}</div><div class="lbl">Courses</div></div>
    </div>

    <h2 style="font-size:22px;margin-bottom:16px">Courses</h2>
    <div class="grid-courses" style="margin-bottom:34px">
      ${state.courses.map(c => {
        const cm = s.courses.find(x => x.code === c.code)?.mastery || 0;
        const done = c.units.filter(u => (state.progress[u.id]?.mastery || 0) >= 70).length;
        return `<div class="card hoverable course-card" data-code="${esc(c.code)}">
          <div class="course-head">
            <span class="cc-dot" style="background:${c.accent}"></span>
            <div><div class="cc-code">${esc(c.code)} · ${c.credits} cr</div><h3>${esc(c.title)}</h3></div>
          </div>
          <p class="cc-blurb">${esc(c.blurb)}</p>
          <div class="meter-row"><span class="meter" style="flex:1"><i style="width:${cm}%;background:${c.accent}"></i></span><span>${Math.round(cm)}%</span></div>
          <div class="muted" style="font-size:12.5px">${done}/${c.units.length} units at 70%+</div>
        </div>`;
      }).join('')}
    </div>

    <h2 style="font-size:22px;margin-bottom:16px">What to study next</h2>
    <div class="grid grid-2">
      ${weakest.slice(0, 4).map(w => `
        <div class="card hoverable" data-unit="${esc(w.id)}" data-code="${esc(w.course.code)}">
          <div class="card-top"><span class="nav-dot" style="background:${w.course.accent}"></span>
            <span class="muted" style="font-size:12.5px">${esc(w.course.short)}</span></div>
          <h3 style="font-size:16.5px">${esc(w.title)}</h3>
          <div class="meter-row" style="margin-top:10px"><span class="meter"><i style="width:${w.mastery}%;background:${pctColor(w.mastery)}"></i></span><span>${Math.round(w.mastery)}%</span></div>
        </div>`).join('')}
    </div>
  `;
  $$('#content .course-card').forEach(el => el.addEventListener('click', () => navigate('course', { code: el.dataset.code })));
  $$('#content [data-unit]').forEach(el => el.addEventListener('click', () => navigate('unit', { code: el.dataset.code, unit: el.dataset.unit })));
}

/* ============================================================ COURSE == */
async function viewCourse() {
  const code = state.view.code;
  const c = await api('/api/course/' + encodeURIComponent(code));
  const cm = state.summary.courses.find(x => x.code === code)?.mastery || 0;
  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow" style="color:${c.accent}">${esc(c.code)} · ${c.credits} credits</div>
      <h1>${esc(c.title)}</h1>
      <p>${esc(c.blurb)}</p>
      <div class="ramp-note" style="margin-top:12px">Units are ordered from foundational to advanced — work them in order.</div>
      <div class="meter-row" style="max-width:420px;margin-top:16px">
        <span class="meter"><i style="width:${cm}%;background:${c.accent}"></i></span>
        <span><strong>${Math.round(cm)}%</strong> course mastery</span>
      </div>
    </div>
    ${levelLegend()}
    <div class="row-between" style="margin-bottom:14px">
      <h2 style="font-size:20px">Units</h2>
      <div class="row">
        <button class="btn btn-ghost btn-sm" id="courseCards">Flashcards <span class="muted">· all units</span></button>
        <button class="btn btn-accent btn-sm" id="courseTutor">Ask the AI tutor</button>
      </div>
    </div>
    <div id="unitList"></div>
  `;
  $('#unitList').innerHTML = c.units.map((u, i) => {
    const m = state.progress[u.id]?.mastery || 0;
    const passed = m >= 70;
    return `<div class="unit-row" data-unit="${esc(u.id)}">
      <span class="u-num">${i + 1}</span>
      <div class="u-main">
        <div class="u-title">${esc(u.title)} ${lvlBadge(u.level)}</div>
        <div class="u-sum">${esc(u.summary)}</div>
      </div>
      <div class="u-right">
        ${passed ? '<span class="tag ok">passed</span>' : (m > 0 ? '<span class="tag warn">in&nbsp;progress</span>' : '<span class="tag neutral">new</span>')}
        <span class="mini-bar"><i style="width:${m}%;background:${pctColor(m)}"></i></span>
        <span class="u-pct">${Math.round(m)}%</span>
      </div></div>`;
  }).join('');
  $$('#unitList .unit-row').forEach(el => el.addEventListener('click', () => navigate('unit', { code, unit: el.dataset.unit })));
  $('#courseTutor').addEventListener('click', () => { state.chat.course = code; state.chat.unit = null; state.chat.sessionId = null; navigate('tutor'); });
  $('#courseCards').addEventListener('click', () => startCourseFlashcards(code));
}

/* ============================================================== UNIT == */
async function viewUnit() {
  const code = state.view.code, uid = state.view.unit;
  const c = await api('/api/course/' + encodeURIComponent(code));
  const u = c.units.find(x => x.id === uid);
  if (!u) throw new Error('Unit not found');
  const m = state.progress[uid]?.mastery || 0;
  const idx = c.units.findIndex(x => x.id === uid) + 1;

  $('#content').innerHTML = `
    <div class="page-head">
      <a class="btn btn-ghost btn-sm" id="backCourse">← ${esc(c.short)}</a>
      <div class="eyebrow" style="color:${c.accent};margin-top:18px">${esc(c.code)} · Unit ${idx} of ${c.units.length}</div>
      <h1>${esc(u.title)}</h1>
      <p>${esc(u.summary)}</p>
      <div class="meter-row" style="max-width:420px;margin-top:16px">
        <span class="meter"><i style="width:${m}%;background:${pctColor(m)}"></i></span>
        <span><strong>${Math.round(m)}%</strong> mastery ${m >= 70 ? '· <span class="tag ok">passed</span>' : ''}</span>
      </div>
    </div>

    <div class="tabs">
      <button class="tab active" data-tab="learn">Learn</button>
      <button class="tab" data-tab="cards">Flashcards</button>
      <button class="tab" data-tab="quiz">Quiz</button>
      <button class="tab" data-tab="tutor">Ask AI Tutor</button>
    </div>

    <div class="tab-panel active" id="panel-learn"></div>
    <div class="tab-panel" id="panel-cards"></div>
    <div class="tab-panel" id="panel-quiz"></div>
    <div class="tab-panel" id="panel-tutor"></div>
  `;
  $('#backCourse').addEventListener('click', () => navigate('course', { code }));

  renderLearnPanel($('#panel-learn'), u);
  renderQuizPanel($('#panel-quiz'), code, uid);
  $('#panel-cards').innerHTML = `<div id="unitCardHost"></div>`;
  renderFlashcardHost($('#unitCardHost'), { course: code, unit: uid });
  renderUnitTutor($('#panel-tutor'), code, uid);

  $$('.tab').forEach(t => t.addEventListener('click', () => {
    $$('.tab').forEach(x => x.classList.toggle('active', x === t));
    $$('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + t.dataset.tab));
  }));
}

function renderLearnPanel(host, u) {
  const ex = u.example, exHard = u.example_hard;
  host.innerHTML = `
    <div class="learn-block">
      <h3>Key concepts</h3>
      ${u.concepts.map(c => `<div class="concept"><div class="c-t">${esc(c.t)}</div><div class="c-d">${esc(c.d)}</div></div>`).join('')}
    </div>
    <div class="learn-block">
      <h3>Formulas &amp; rules</h3>
      ${u.formulas.map(f => `<div class="formula"><span class="f-name">${esc(f.n)}</span><span class="f-eq">${esc(f.e)}</span><span class="f-note">${esc(f.note)}</span></div>`).join('')}
    </div>
    <div class="learn-block">
      <h3>Worked examples</h3>
      <p class="muted" style="font-size:13.5px;margin:0 0 14px">Work these in order — the first builds the idea, the second is exam-level.</p>
      <div class="tier">
        <div class="tier-head">${lvlBadge(Math.min(...(u.practice || [{level:1}]).map(p => p.level || 1), 2))}
          <h4>Worked example 1 — build the idea</h4></div>
        <div class="tier-body">
          <h4 style="font-size:15px;margin-bottom:12px">${esc(ex.problem)}</h4>
          <ol style="margin:0 0 14px;padding-left:20px">${ex.steps.map(s => `<li style="margin-bottom:6px;font-size:14px;color:var(--ink-2)">${esc(s)}</li>`).join('')}</ol>
          <div class="answer-box"><strong>Answer:</strong> ${esc(ex.answer)}</div>
        </div>
      </div>
      ${exHard ? `<div class="tier">
        <div class="tier-head">${lvlBadge(exHard.level || 3)}<h4>Worked example 2 — exam-level</h4></div>
        <div class="tier-body">
          <h4 style="font-size:15px;margin-bottom:12px">${esc(exHard.problem)}</h4>
          <ol style="margin:0 0 14px;padding-left:20px">${exHard.steps.map(s => `<li style="margin-bottom:6px;font-size:14px;color:var(--ink-2)">${esc(s)}</li>`).join('')}</ol>
          <div class="answer-box"><strong>Answer:</strong> ${esc(exHard.answer)}</div>
        </div>
      </div>` : ''}
    </div>
    <div class="grid grid-2">
      <div class="learn-block">
        <h3>Common traps</h3>
        ${u.traps.map(t => `<div class="trap">${esc(t)}</div>`).join('')}
      </div>
      <div class="learn-block">
        <h3>Practise these <span class="ramp-note">· easy → hard</span></h3>
        ${u.practice.map((p, i) => `
          <div class="practice-item">
            <div class="practice-q">${lvlBadge(p.level || 2)} <strong>Q${i + 1}.</strong> ${esc(p.q)}</div>
            <button class="btn btn-ghost btn-sm reveal-btn" data-a="${i}">Show answer</button>
            <div class="practice-a" id="ans-${i}" hidden>${esc(p.a)}</div>
          </div>`).join('')}
      </div>
    </div>
  `;
  $$('.reveal-btn', host).forEach(b => b.addEventListener('click', () => {
    const el = $('#ans-' + b.dataset.a, host);
    el.hidden = !el.hidden;
    b.textContent = el.hidden ? 'Show answer' : 'Hide answer';
    if (!el.hidden && !b.dataset.counted) {
      b.dataset.counted = '1';
    }
  }));
}

/* ------------------------------------------------------ flashcards ---- */
async function startCourseFlashcards(code) {
  openModal('Flashcards — all units of ' + (state.courses.find(c => c.code === code)?.short || code), '<div id="modalCardHost"></div>');
  renderFlashcardHost($('#modalCardHost'), { course: code, unit: null });
}

async function renderFlashcardHost(host, { course, unit }) {
  host.innerHTML = `<div class="loading">Dealing cards…</div>`;
  const data = await api('/api/flashcards/' + encodeURIComponent(course));
  let cards = data.cards;
  if (unit) cards = cards.filter(c => c.unit === unit);
  if (!cards.length) { host.innerHTML = `<div class="empty">No flashcards in this set.</div>`; return; }
  const st = { deck: cards, idx: 0, flipped: false };

  const draw = () => {
    const c = st.deck[st.idx];
    host.innerHTML = `
      <div class="fc-wrap">
        <div class="fc ${st.flipped ? 'flipped' : ''}" id="fcEl">
          <div class="fc-inner">
            <div class="fc-face fc-front"><div class="fc-kicker">Prompt</div><div class="fc-text">${esc(c.front)}</div></div>
            <div class="fc-face fc-back"><div class="fc-kicker">Answer</div><div class="fc-text small">${esc(c.back)}</div></div>
          </div>
        </div>
        <div class="fc-controls">
          <button class="btn btn-ghost btn-sm" id="fcPrev" ${st.idx === 0 ? 'disabled' : ''}>← Prev</button>
          <button class="btn btn-primary btn-sm" id="fcFlip">Flip</button>
          <button class="btn btn-ghost btn-sm" id="fcNext" ${st.idx === st.deck.length - 1 ? 'disabled' : ''}>Next →</button>
          <span class="fc-counter">${st.idx + 1} / ${st.deck.length}</span>
        </div>
      </div>`;
    $('#fcEl', host).addEventListener('click', () => { st.flipped = !st.flipped; draw(); });
    $('#fcFlip', host).addEventListener('click', () => { st.flipped = !st.flipped; draw(); });
    const prev = $('#fcPrev', host), next = $('#fcNext', host);
    if (prev) prev.addEventListener('click', () => { st.idx--; st.flipped = false; draw(); });
    if (next) next.addEventListener('click', () => { st.idx++; st.flipped = false; draw(); });
  };
  draw();
}

/* ------------------------------------------------------------- quiz --- */
async function renderQuizPanel(host, code, unit) {
  host.innerHTML = `<div class="loading">Loading quiz…</div>`;
  let quiz;
  try { quiz = await api(`/api/quiz/${encodeURIComponent(code)}/${encodeURIComponent(unit)}`); }
  catch { host.innerHTML = `<div class="empty">No quiz for this unit yet.</div>`; return; }

  let started = false;
  const start = () => {
    started = true;
    host.innerHTML = `
      <div class="row-between" style="margin-bottom:16px">
        <div><strong>Unit quiz</strong> <span class="muted">· ${quiz.questions.length} questions · ordered easy → hard · pass at 70%</span></div>
      </div>
      <form id="quizForm">
        ${quiz.questions.map((q, i) => `
          <div class="quiz-q" data-q="${i}">
            <div class="qq-text">${lvlBadge(q.level || 2)} ${i + 1}. ${esc(q.q)}</div>
            ${q.opts.map((o, j) => `
              <label class="opt"><input type="radio" name="q${i}" value="${j}" /> <span>${esc(o)}</span></label>
            `).join('')}
          </div>`).join('')}
        <button type="submit" class="btn btn-accent" id="quizSubmit">Submit answers</button>
      </form>`;
    $$('.opt input', host).forEach(r => r.addEventListener('change', () => {
      const group = r.name;
      $$(`input[name="${group}"]`, host).forEach(x => x.closest('.opt').classList.toggle('sel', x.checked));
    }));
    $('#quizForm', host).addEventListener('submit', async e => {
      e.preventDefault();
      const answers = quiz.questions.map((_, i) => {
        const sel = $(`input[name="q${i}"]:checked`, host);
        return sel ? parseInt(sel.value, 10) : -1;
      });
      if (answers.includes(-1)) { alert('Answer every question before submitting.'); return; }
      const btn = $('#quizSubmit', host); btn.disabled = true; btn.textContent = 'Grading…';
      try {
        const res = await api('/api/quiz/submit', { method: 'POST', body: JSON.stringify({ course_code: code, unit_id: unit, answers }) });
        renderQuizResult(host, quiz, res, code, unit, start);
        await refreshData();
      } catch (ex) { alert('Could not submit: ' + ex.message); btn.disabled = false; btn.textContent = 'Submit answers'; }
    });
  };

  host.innerHTML = `
    <div class="card" style="max-width:640px">
      <h3 style="font-size:19px;margin-bottom:8px">Unit quiz</h3>
      <p class="muted" style="margin:0 0 16px">${quiz.questions.length} multiple-choice questions. You need 70% to mark this unit passed. Your best score is kept as your mastery for the unit.</p>
      <button class="btn btn-accent" id="quizStart">Start quiz</button>
    </div>`;
  $('#quizStart', host).addEventListener('click', start);
}

function renderQuizResult(host, quiz, res, code, unit, restart) {
  host.innerHTML = `
    <div class="result-banner ${res.passed ? 'pass' : 'fail'}">
      <div class="rb-score">${res.pct}%</div>
      <div class="rb-txt">
        <strong>${res.passed ? 'Passed — unit marked complete' : 'Not passed yet (need 70%)'}</strong>
        <small>${res.score} of ${res.total} correct · mastery updated to ${Math.round(res.mastery)}%</small>
      </div>
      <div class="spacer"></div>
      <button class="btn btn-primary btn-sm" id="quizRetry">Retry</button>
    </div>
    ${quiz.questions.map((q, i) => {
      const r = res.results[i];
      return `<div class="quiz-q">
        <div class="qq-text">${i + 1}. ${esc(q.q)}</div>
        ${q.opts.map((o, j) => {
          let cls = 'opt';
          if (j === r.answer) cls += ' right';
          else if (j === r.given) cls += ' wrong';
          return `<div class="${cls}"><span>${esc(o)}</span>${j === r.answer ? '<span class="spacer"></span><span class="tag ok">correct</span>' : (j === r.given ? '<span class="spacer"></span><span class="tag bad">your pick</span>' : '')}</div>`;
        }).join('')}
        <div class="quiz-explain"><strong>Why:</strong> ${esc(r.explain)}</div>
      </div>`;
    }).join('')}
  `;
  $('#quizRetry', host).addEventListener('click', restart);
}

/* --------------------------------------------------------- unit tutor - */
function renderUnitTutor(host, code, unit) {
  host.innerHTML = `
    <div class="card" style="max-width:680px">
      <h3 style="font-size:19px;margin-bottom:8px">Ask the AI tutor about this unit</h3>
      <p class="muted" style="margin:0 0 16px">The tutor is grounded in this unit's concepts, formulas and conventions and runs on your own machine (Ollama). It will walk you through a problem step by step.</p>
      <button class="btn btn-accent" id="unitTutorGo">Open the tutor on this unit</button>
    </div>`;
  $('#unitTutorGo', host).addEventListener('click', () => {
    state.chat.course = code; state.chat.unit = unit; state.chat.sessionId = null;
    navigate('tutor');
  });
}

/* ============================================================= TUTOR == */
async function viewTutor() {
  let status = { online: false, model: '', ollama_url: '' };
  try { status = await api('/api/tutor/status'); } catch {}

  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow">AI tutor · local</div>
      <h1>Your tutor</h1>
      <p>Grounded in the course material and powered by ${esc(status.model || 'a local model')} on Ollama — free and offline. It teaches the concept, then guides you to the answer.</p>
    </div>
    <div class="chat-layout">
      <div class="chat-side">
        <button class="btn btn-primary btn-sm btn-block" id="newChat" style="margin-bottom:14px">+ New conversation</button>
        <h4>Recent</h4>
        <div id="chatSessions"></div>
      </div>
      <div class="chat-main">
        <div class="chat-context">
          <span>Context:</span>
          <select id="ctxCourse"></select>
          <select id="ctxUnit"></select>
          <span class="spacer"></span>
          <span class="muted" id="ctxStatus">${status.online ? '● online' : '● offline — start Ollama'}</span>
        </div>
        <div class="chat-stream" id="chatStream">
          <div class="empty" id="chatEmpty">
            Ask anything — a concept you didn't follow, a problem you're stuck on, or "quiz me on this unit".
          </div>
        </div>
        <div class="chat-input">
          <textarea id="chatText" rows="1" placeholder="Type your question…"></textarea>
          <button class="btn btn-accent" id="chatSend">Send</button>
        </div>
      </div>
    </div>
  `;

  // context selectors
  const cc = $('#ctxCourse'), cu = $('#ctxUnit');
  cc.innerHTML = `<option value="">All courses</option>` +
    state.courses.map(c => `<option value="${esc(c.code)}">${esc(c.short)}</option>`).join('');
  const fillUnits = () => {
    const c = state.courses.find(x => x.code === cc.value);
    cu.innerHTML = `<option value="">Whole course</option>` +
      (c ? c.units.map(u => `<option value="${esc(u.id)}">${esc(u.title)}</option>`).join('') : '');
  };
  cc.value = state.chat.course || '';
  fillUnits();
  cu.value = state.chat.unit || '';
  cc.addEventListener('change', () => { state.chat.course = cc.value || null; state.chat.unit = null; cu.value = ''; fillUnits(); });
  cu.addEventListener('change', () => { state.chat.unit = cu.value || null; });

  $('#newChat').addEventListener('click', () => {
    state.chat.sessionId = null;
    $('#chatStream').innerHTML = `<div class="empty">New conversation. Ask anything about the selected context.</div>`;
    loadChatSessions();
  });

  const ta = $('#chatText');
  ta.addEventListener('input', () => { ta.style.height = 'auto'; ta.style.height = Math.min(160, ta.scrollHeight) + 'px'; });
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } });
  $('#chatSend').addEventListener('click', sendChat);

  loadChatSessions();
  if (state.chat.sessionId) openChatSession(state.chat.sessionId);
}

async function loadChatSessions() {
  const host = $('#chatSessions'); if (!host) return;
  try {
    const d = await api('/api/chat/sessions');
    if (!d.sessions.length) { host.innerHTML = `<div class="muted" style="font-size:13px;padding:6px 11px">No conversations yet.</div>`; return; }
    host.innerHTML = d.sessions.map(s =>
      `<div class="chat-sess ${s.id === state.chat.sessionId ? 'active' : ''}" data-sid="${s.id}">${esc(s.title || 'Conversation ' + s.id)}</div>`
    ).join('');
    $$('#chatSessions .chat-sess').forEach(el => el.addEventListener('click', () => openChatSession(parseInt(el.dataset.sid, 10))));
  } catch {}
}

async function openChatSession(sid) {
  state.chat.sessionId = sid;
  try {
    const d = await api('/api/chat/session/' + sid);
    const stream = $('#chatStream'); if (!stream) return;
    stream.innerHTML = '';
    d.messages.forEach(m => appendMsg(m.role, m.content));
    if (d.session.course_code) {
      const cc = $('#ctxCourse'); if (cc) { cc.value = d.session.course_code; cc.dispatchEvent(new Event('change')); }
      if (d.session.unit_id) { const cu = $('#ctxUnit'); if (cu) cu.value = d.session.unit_id; }
      state.chat.course = d.session.course_code; state.chat.unit = d.session.unit_id || null;
    }
    loadChatSessions();
    stream.scrollTop = stream.scrollHeight;
  } catch {}
}

function appendMsg(role, text) {
  const stream = $('#chatStream'); if (!stream) return null;
  const empty = $('#chatEmpty'); if (empty) empty.remove();
  const div = document.createElement('div');
  div.className = 'msg ' + (role === 'user' ? 'user' : 'assistant');
  div.innerHTML = `<div class="role-tag">${role === 'user' ? 'You' : 'Tutor'}</div><div class="bubble"></div>`;
  div.querySelector('.bubble').textContent = text;
  stream.appendChild(div);
  stream.scrollTop = stream.scrollHeight;
  return div;
}

async function sendChat() {
  if (state.chat.streaming) return;
  const ta = $('#chatText'); const text = ta.value.trim(); if (!text) return;
  ta.value = ''; ta.style.height = 'auto';
  state.chat.streaming = true;
  $('#chatSend').disabled = true;

  appendMsg('user', text);
  const reply = appendMsg('assistant', '');
  const bubble = reply.querySelector('.bubble');
  bubble.innerHTML = `<span class="typing"></span>`;

  const body = {
    message: text,
    course_code: state.chat.course || null,
    unit_id: state.chat.unit || null,
    session_id: state.chat.sessionId || null,
  };

  try {
    const res = await fetch(API + '/api/tutor/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + state.token },
      body: JSON.stringify(body),
    });
    if (!res.ok || !res.body) throw new Error('HTTP ' + res.status);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '', acc = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split('\n\n');
      buf = parts.pop();
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith('data:')) continue;
        let evt;
        try { evt = JSON.parse(line.slice(5).trim()); } catch { continue; }
        if (evt.delta) { acc += evt.delta; bubble.textContent = acc; $('#chatStream').scrollTop = $('#chatStream').scrollHeight; }
        if (evt.session_id) state.chat.sessionId = evt.session_id;
        if (evt.error) { acc += `\n\n[tutor error: ${evt.error}]`; bubble.textContent = acc; }
      }
    }
    if (!acc) bubble.textContent = '(no reply — is the local model running?)';
  } catch (ex) {
    bubble.textContent = 'Could not reach the tutor: ' + ex.message;
  } finally {
    state.chat.streaming = false;
    $('#chatSend').disabled = false;
    loadChatSessions();
  }
}

/* ============================================================= TERMS == */
async function viewTerms() {
  const d = await api('/api/terms');
  const terms = d.terms || [];
  const active = terms.find(t => t.active);
  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow">Plan your load</div>
      <h1>Semesters &amp; quarters</h1>
      <p>Register each term, list the courses you're taking, and get a progressive study plan that
      runs every subject easy → hard. Add any course — one you type joins the plan alongside the built-in ones.</p>
    </div>

    <div class="card" style="margin-bottom:22px">
      <h3 style="font-size:18px;margin-bottom:14px">Start a new term</h3>
      <form id="termForm" class="grid grid-3">
        <label class="field" style="grid-column:span 2"><span>Term name</span>
          <input id="tName" placeholder="e.g. Spring 2027 · Fall Quarter 2027" required /></label>
        <label class="field"><span>Type</span>
          <select id="tKind">
            <option value="semester">Semester</option>
            <option value="quarter">Quarter</option>
            <option value="trimester">Trimester</option>
            <option value="term">Other term</option>
          </select></label>
        <label class="field"><span>Starts (optional)</span><input id="tStart" type="date" /></label>
        <label class="field"><span>Ends (optional)</span><input id="tEnd" type="date" /></label>
        <div style="display:flex;align-items:flex-end;padding-bottom:16px">
          <button class="btn btn-accent" type="submit">Create term</button></div>
      </form>
    </div>

    ${terms.length ? terms.map(t => `
      <div class="card term-card" style="margin-bottom:16px">
        <div class="row-between">
          <div class="term-head">
            <h3>${esc(t.name)}</h3>
            <span class="tag ${t.active ? 'term-active' : 'neutral'}">${t.active ? 'active' : esc(t.kind)}</span>
            <span class="muted" style="font-size:12.5px">${(t.courses || []).length} course${(t.courses || []).length === 1 ? '' : 's'}</span>
          </div>
          <div class="row">
            ${t.active ? '' : `<button class="btn btn-ghost btn-sm" data-activate="${t.id}">Make active</button>`}
            <button class="btn btn-ghost btn-sm" data-plan="${t.id}">Study plan</button>
            <button class="btn btn-ghost btn-sm" data-del="${t.id}">Delete</button>
          </div>
        </div>
        <div class="row" style="margin-top:4px">
          ${(t.courses || []).length ? (t.courses || []).map(c => `
            <span class="chip-x">${esc(c.code)} · ${esc(c.title)} ${lvlBadge(c.level)}
              <button data-delcourse="${c.id}" title="Remove">✕</button></span>`).join('') : '<span class="muted" style="font-size:13px">No courses yet — add one below.</span>'}
        </div>
        <form class="grid grid-4" data-addform="${t.id}" style="margin-top:6px">
          <label class="field" style="margin:0"><span>Code</span><input name="code" placeholder="MTH-203" required /></label>
          <label class="field" style="margin:0"><span>Course title</span><input name="title" placeholder="Calculus III" required /></label>
          <label class="field" style="margin:0"><span>Units / topics</span><input name="units" type="number" min="1" max="12" value="4" /></label>
          <label class="field" style="margin:0"><span>Start difficulty</span>
            <select name="level"><option value="1">Easy</option><option value="2">Medium</option><option value="3">Hard</option></select></label>
          <label class="field" style="grid-column:1/-1;margin:0"><span>Topics (optional, comma-separated — used as unit names)</span>
            <input name="topics" placeholder="Vectors, Partial derivatives, Multiple integrals, Vector fields" /></label>
          <div style="grid-column:1/-1"><button class="btn btn-primary btn-sm" type="submit">Add course to ${esc(t.name)}</button></div>
        </form>
      </div>`).join('') : `<div class="empty">No terms yet. Create one above to plan the semester.</div>`}
  `;

  $('#termForm').addEventListener('submit', async e => {
    e.preventDefault();
    const btn = e.target.querySelector('button'); btn.disabled = true;
    try {
      await api('/api/terms', { method: 'POST', body: JSON.stringify({
        name: $('#tName').value.trim(), kind: $('#tKind').value,
        start_date: $('#tStart').value || null, end_date: $('#tEnd').value || null, make_active: true }) });
      viewTerms();
    } catch (ex) { alert('Could not create term: ' + ex.message); btn.disabled = false; }
  });

  $$('#content [data-activate]').forEach(b => b.addEventListener('click', async () => {
    await api(`/api/terms/${b.dataset.activate}/activate`, { method: 'POST' }); viewTerms();
  }));
  $$('#content [data-del]').forEach(b => b.addEventListener('click', async () => {
    if (!confirm('Delete this term and its course list?')) return;
    await api(`/api/terms/${b.dataset.del}`, { method: 'DELETE' }); viewTerms();
  }));
  $$('#content [data-delcourse]').forEach(b => b.addEventListener('click', async () => {
    await api(`/api/term-courses/${b.dataset.delcourse}`, { method: 'DELETE' }); viewTerms();
  }));
  $$('#content [data-plan]').forEach(b => b.addEventListener('click', () => openStudyPlan(b.dataset.plan)));
  $$('#content [data-addform]').forEach(f => f.addEventListener('submit', async e => {
    e.preventDefault();
    const tid = f.dataset.addform;
    const fd = new FormData(f);
    const topics = (fd.get('topics') || '').split(',').map(s => s.trim()).filter(Boolean);
    try {
      await api(`/api/terms/${tid}/courses`, { method: 'POST', body: JSON.stringify({
        code: fd.get('code'), title: fd.get('title'),
        units: parseInt(fd.get('units') || '1', 10), level: parseInt(fd.get('level') || '1', 10),
        topics }) });
      viewTerms();
    } catch (ex) { alert('Could not add course: ' + ex.message); }
  }));
}

async function openStudyPlan(tid) {
  openModal('Study plan', `<div class="loading">Building your plan…</div>`);
  try {
    const d = await api(`/api/terms/${tid}/study-plan`);
    const courses = d.plan || [];
    $('#modalTitle').textContent = `Study plan — ${d.term.name}`;
    $('#modalBody').innerHTML = `
      <p class="muted" style="font-size:13.5px;margin:0 0 18px">
        Every course is ordered foundational → advanced, and the weekly sequence <strong>interleaves subjects</strong>
        (spending a bit of each subject every week beats one subject at a time).
      </p>
      ${courses.map(c => `
        <div class="tier" style="margin-bottom:12px">
          <div class="tier-head">
            <strong style="font-size:14.5px">${esc(c.course)}</strong>
            <span class="muted" style="font-size:12.5px">${esc(c.code)}</span>
            ${c.custom ? '<span class="tag neutral">custom</span>' : ''}
          </div>
          <div class="tier-body" style="padding:12px 16px">
            ${c.units.map(u => `<div class="week-row" style="padding:8px 0">
              <span class="week-num">Unit ${u.n}</span>
              <span style="flex:1">${esc(u.title)}</span>${lvlBadge(u.level)}
            </div>`).join('')}
          </div>
        </div>`).join('')}
      <h4 style="font-size:14px;margin:20px 0 10px">Weekly sequence</h4>
      <div style="border:1px solid var(--border);border-radius:12px;overflow:hidden;max-height:340px;overflow-y:auto">
        ${(d.sequence || []).map(s => `<div class="week-row">
          <span class="week-num">Wk ${s.week}</span>
          <span style="flex:1"><strong>${esc(s.code)}</strong> · ${esc(s.unit)}</span>${lvlBadge(s.level)}
        </div>`).join('')}
      </div>
      <div class="row" style="margin-top:18px">
        <a class="btn btn-primary btn-sm" href="https://github.com/julianantoine/tutor-portal" target="_blank" rel="noopener">How this works</a>
        <span class="muted" style="font-size:12.5px">Custom units are worked with the AI tutor — open it and pick the course.</span>
      </div>`;
  } catch (ex) {
    $('#modalBody').innerHTML = `<div class="empty">Could not build the plan: ${esc(ex.message)}</div>`;
  }
}

/* ======================================================= ASSIGNMENTS == */
async function viewAssignments() {
  const d = await api('/api/assignments');
  const isTutor = state.user.role === 'tutor';
  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow">Study plan</div>
      <h1>Assignments</h1>
      <p>${isTutor ? 'Set work for a student and track completion.' : 'Everything your tutor has set for you, plus anything you add yourself.'}</p>
    </div>
    ${isTutor ? `<div class="card" style="margin-bottom:22px">
      <h3 style="font-size:17px;margin-bottom:14px">New assignment</h3>
      <form id="assignForm" class="grid grid-2">
        <label class="field"><span>Student</span><select id="aStudent" style="width:100%;padding:11px 14px;border:1px solid var(--border);border-radius:12px;font-family:var(--body)"></select></label>
        <label class="field"><span>Title</span><input id="aTitle" placeholder="e.g. Rework truss practice set" required /></label>
        <label class="field"><span>Course</span><select id="aCourse" style="width:100%;padding:11px 14px;border:1px solid var(--border);border-radius:12px;font-family:var(--body)">
          <option value="">— none —</option>${state.courses.map(c => `<option value="${esc(c.code)}">${esc(c.short)}</option>`).join('')}</select></label>
        <label class="field"><span>Due (optional)</span><input id="aDue" type="date" /></label>
        <label class="field" style="grid-column:1/-1"><span>Notes</span><input id="aNotes" placeholder="What to focus on" /></label>
        <div style="grid-column:1/-1"><button class="btn btn-accent" type="submit">Assign</button></div>
      </form>
    </div>` : ''}
    <div id="assignList"></div>
  `;

  if (isTutor) {
    const students = await api('/api/admin/students');
    $('#aStudent').innerHTML = students.students.map(s => `<option value="${s.user.id}">${esc(s.user.name || s.user.identifier)}</option>`).join('') || `<option value="">No students</option>`;
    $('#assignForm').addEventListener('submit', async e => {
      e.preventDefault();
      const payload = {
        user_id: parseInt($('#aStudent').value, 10),
        title: $('#aTitle').value.trim(),
        course_code: $('#aCourse').value || null,
        due: $('#aDue').value || null,
        notes: $('#aNotes').value.trim() || null,
      };
      await api('/api/assignments', { method: 'POST', body: JSON.stringify(payload) });
      viewAssignments();
    });
  }

  const list = d.assignments;
  $('#assignList').innerHTML = list.length ? list.map(a => {
    const c = state.courses.find(x => x.code === a.course_code);
    const overdue = a.due && !a.done && new Date(a.due) < new Date(new Date().toDateString());
    return `<div class="unit-row" data-aid="${a.id}">
      <input type="checkbox" ${a.done ? 'checked' : ''} style="width:18px;height:18px;accent-color:var(--accent)" />
      <div class="u-main">
        <div class="u-title" style="${a.done ? 'text-decoration:line-through;color:var(--ink-3)' : ''}">${esc(a.title)}</div>
        <div class="u-sum">${c ? esc(c.short) + ' · ' : ''}${a.notes ? esc(a.notes) : ''}</div>
      </div>
      <div class="u-right">
        ${a.due ? `<span class="tag ${overdue ? 'bad' : 'neutral'}">due ${esc(a.due)}</span>` : ''}
        ${a.done ? '<span class="tag ok">done</span>' : ''}
      </div></div>`;
  }).join('') : `<div class="empty">Nothing assigned yet.</div>`;

  $$('#assignList .unit-row').forEach(el => {
    const cb = el.querySelector('input');
    el.addEventListener('click', async e => {
      if (e.target === cb) return;
      cb.checked = !cb.checked;
      await api(`/api/assignments/${el.dataset.aid}/toggle`, { method: 'POST' });
      viewAssignments(); refreshAssignBadge();
    });
    cb.addEventListener('change', async () => {
      await api(`/api/assignments/${el.dataset.aid}/toggle`, { method: 'POST' });
      viewAssignments(); refreshAssignBadge();
    });
  });
}

/* ======================================================== DASHBOARD == */
async function viewDashboard() {
  const d = await api('/api/admin/students');
  const totalQuiz = d.students.reduce((n, s) => n + s.quizzes, 0);
  const totalMsg = d.students.reduce((n, s) => n + s.messages, 0);
  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow">Tutor dashboard</div>
      <h1>Progress overview</h1>
      <p>Per-student mastery across the four courses, quiz activity, and the weakest units to target in the next session.</p>
    </div>
    <div class="grid grid-4" style="margin-bottom:26px">
      <div class="card stat-card"><div class="big">${d.students.length}</div><div class="lbl">Students</div></div>
      <div class="card stat-card"><div class="big">${Math.round(d.students.reduce((n, s) => n + s.summary.overall, 0) / (d.students.length || 1))}%</div><div class="lbl">Avg mastery</div></div>
      <div class="card stat-card"><div class="big">${totalQuiz}</div><div class="lbl">Quiz attempts</div></div>
      <div class="card stat-card"><div class="big">${totalMsg}</div><div class="lbl">Tutor messages</div></div>
    </div>
    <div id="studentList"></div>
  `;
  $('#studentList').innerHTML = d.students.length ? d.students.map(s => `
    <div class="card" style="margin-bottom:16px">
      <div class="row-between">
        <div class="row">
          <div class="logo" style="width:42px;height:42px;font-size:16px;border-radius:12px">${esc((s.user.name || s.user.identifier)[0].toUpperCase())}</div>
          <div><h3 style="font-size:17px">${esc(s.user.name || s.user.identifier)}</h3>
          <div class="muted" style="font-size:12.5px">@${esc(s.user.identifier)} · ${s.quizzes} quizzes · ${s.messages} messages${s.last_active ? ' · last active ' + esc(s.last_active.slice(0, 10)) : ''}</div></div>
        </div>
        <button class="btn btn-ghost btn-sm" data-uid="${s.user.id}">Open profile</button>
      </div>
      <div class="grid grid-4" style="margin:16px 0 14px">
        ${s.summary.courses.map(c => `
          <div><div class="muted" style="font-size:12px">${esc(c.short)}</div>
          <div class="meter-row" style="margin-top:6px"><span class="meter"><i style="width:${c.mastery}%;background:${c.accent}"></i></span><span>${Math.round(c.mastery)}%</span></div></div>`).join('')}
      </div>
      <div class="muted" style="font-size:12.5px;margin-bottom:8px">Weakest units</div>
      <div class="row">
        ${s.weakest.map(w => `<span class="tag ${w.mastery >= 70 ? 'ok' : w.mastery >= 40 ? 'warn' : 'bad'}">${esc(w.course)} · ${esc(w.title)} · ${Math.round(w.mastery)}%</span>`).join('')}
      </div>
    </div>`).join('') : `<div class="empty">No students registered yet.</div>`;

  $$('#studentList [data-uid]').forEach(b => b.addEventListener('click', () => openStudentProfile(parseInt(b.dataset.uid, 10))));
}

async function openStudentProfile(uid) {
  openModal('Student profile', `<div class="loading">Loading…</div>`);
  const d =await api('/api/admin/student/' + uid);
  $('#modalBody').innerHTML = `
    <h3 style="font-size:18px;margin-bottom:4px">${esc(d.user.name || d.user.identifier)}</h3>
    <div class="muted" style="font-size:13px;margin-bottom:18px">@${esc(d.user.identifier)} · ${Math.round(d.summary.overall)}% overall mastery</div>
    <div class="grid grid-2" style="margin-bottom:20px">
      ${d.summary.courses.map(c => `
        <div><div class="muted" style="font-size:12px">${esc(c.short)}</div>
        <div class="meter-row" style="margin-top:6px"><span class="meter"><i style="width:${c.mastery}%;background:${c.accent}"></i></span><span>${Math.round(c.mastery)}%</span></div></div>`).join('')}
    </div>
    <h4 style="font-size:14px;margin:0 0 10px">Quiz history</h4>
    ${d.quiz_history.length ? `<table class="table"><thead><tr><th>Course</th><th>Unit</th><th>Score</th><th>When</th></tr></thead><tbody>
      ${d.quiz_history.map(q => {
        const p = Math.round(100 * q.score / q.total);
        return `<tr><td>${esc(q.course_code)}</td><td class="muted">${esc(q.unit_id)}</td>
          <td><span class="tag ${p >= 70 ? 'ok' : p >= 40 ? 'warn' : 'bad'}">${q.score}/${q.total} · ${p}%</span></td>
          <td class="muted">${esc((q.created_at || '').slice(0, 16).replace('T', ' '))}</td></tr>`;
      }).join('')}</tbody></table>` : `<div class="muted" style="font-size:13px">No quizzes taken yet.</div>`}
    <h4 style="font-size:14px;margin:22px 0 10px">Assignments</h4>
    ${d.assignments.length ? d.assignments.map(a => `<div class="row" style="padding:8px 0;border-bottom:1px solid var(--border-soft)">
        <span class="tag ${a.done ? 'ok' : 'neutral'}">${a.done ? 'done' : 'open'}</span>
        <span>${esc(a.title)}</span>${a.due ? `<span class="spacer"></span><span class="muted" style="font-size:12.5px">due ${esc(a.due)}</span>` : ''}
      </div>`).join('') : `<div class="muted" style="font-size:13px">Nothing assigned.</div>`}
  `;
}

/* ============================================================ MODAL == */
function openModal(title, bodyHtml) {
  $('#modalTitle').textContent = title;
  $('#modalBody').innerHTML = bodyHtml;
  $('#modalOverlay').classList.add('open');
}
function closeModal() { $('#modalOverlay').classList.remove('open'); }
$('#modalClose').addEventListener('click', closeModal);
$('#modalOverlay').addEventListener('click', e => { if (e.target === $('#modalOverlay')) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

/* ============================================================= START == */
boot();
