/* =========================================================================
   Tutor Portal — single-page app
   Same-origin API (the FastAPI server serves this file at "/"), so no CORS
   config is needed; every call is relative to window.location.origin.
   ========================================================================= */

const API = '';                       // same origin
const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

// An <img> cannot send an Authorization header, so the session token rides along
// as a query param; the server still checks the note belongs to this user.
const mediaUrl = (nid, name) =>
  `/api/notes/${nid}/media/${encodeURIComponent(name)}?t=${encodeURIComponent(state.token || '')}`;

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
let paidSession = null;        // filled in when the browser returns from Stripe
let planInfo = null;

function authMsg(text, isError) {
  const el = $('#authErr');
  el.textContent = text;
  el.hidden = !text;
  el.style.color = isError ? '' : 'var(--green)';
}

function setAuthMode(mode) {
  authMode = mode;
  $$('#authSeg .seg-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  const isDemo = mode === 'demo';
  const isSubscribe = mode === 'subscribe';
  const isFinish = mode === 'finish';          // came back from a paid checkout

  $('#passField').hidden = isSubscribe || isDemo;
  // a hidden input that is still `required` silently blocks the submit
  $('#authPass').required = !(isSubscribe || isDemo);
  $('#authPass').disabled = isSubscribe || isDemo;
  $('#demoCourseField').hidden = !isDemo;
  $('#demoCourse').required = isDemo;
  $('#userLabel').textContent = isDemo ? 'Your email' : 'Email';
  $('#passLabel').textContent = isFinish ? 'Choose a password' : 'Password';
  $('#authUser').disabled = isFinish;
  if (isFinish) $('#authUser').value = (paidSession && paidSession.email) || '';

  const price = (planInfo && planInfo.label) || '$29.99/month';
  const hours = (planInfo && planInfo.demo_hours) || 24;
  const notes = {
    subscribe: `Flat ${price}. Cancel anytime. You pay first, then set your password.`,
    finish: `Payment confirmed — set a password and your account is ready.`,
    demo: `One subject, full access for ${hours} hours. One demo per email address. No card needed.`,
    login: '',
  };
  const note = $('#planNote');
  note.textContent = notes[mode] || '';
  note.hidden = !note.textContent;
  $('#manageBtn').hidden = mode !== 'login';

  const labels = { login: 'Sign in', subscribe: 'Continue to payment →',
                   demo: 'Start my free demo', finish: 'Create my account' };
  $('#authSubmit').textContent = labels[mode] || 'Continue';
}

$('#authSeg').addEventListener('click', e => {
  const b = e.target.closest('.seg-btn');
  if (b) { authMsg(''); setAuthMode(b.dataset.mode); }
});

async function loadPlan() {
  try {
    planInfo = await api('/api/plan');
    const sel = $('#demoCourse');
    sel.innerHTML = (planInfo.courses || [])
      .map(c => `<option value="${esc(c.code)}">${esc(c.short)} — ${esc(c.title)}</option>`).join('');
    const price = planInfo.label || '$29.99/month';
    $('#authHint').innerHTML =
      `<strong>${esc(price)} — flat monthly, cancel anytime</strong>` +
      `<div>Subscribe to open an account. Or start a free demo on one subject.</div>`;
  } catch { /* keep the static hint */ }
}

$('#manageBtn').addEventListener('click', async () => {
  const email = ($('#authUser').value || '').trim() || prompt('The email you subscribed with:') || '';
  if (!email) return;
  authMsg('');
  try {
    const r = await api('/api/billing/portal', { method: 'POST', body: JSON.stringify({ email }) });
    location.href = r.url;
  } catch (ex) { authMsg(ex.message, true); }
});

$('#authForm').addEventListener('submit', async e => {
  e.preventDefault();
  authMsg('');
  const identifier = $('#authUser').value.trim();
  const password = $('#authPass').value;
  const btn = $('#authSubmit'); btn.disabled = true; btn.textContent = '…';
  try {
    if (authMode === 'subscribe') {
      const r = await api('/api/subscribe', { method: 'POST', body: JSON.stringify({ email: identifier }) });
      location.href = r.url;                       // to Stripe — pay first
      return;
    }
    if (authMode === 'demo') {
      const r = await api('/api/demo', { method: 'POST', body: JSON.stringify({
        email: identifier, course_code: $('#demoCourse').value }) });
      state.token = r.token;
      localStorage.setItem('tp_token', r.token);
      state.user = r.user;
      await enterApp();
      return;
    }
    if (authMode === 'finish') {
      const r = await api('/api/register', { method: 'POST', body: JSON.stringify({
        identifier, password, session_id: paidSession && paidSession.session_id }) });
      state.token = r.token;
      localStorage.setItem('tp_token', r.token);
      state.user = r.user;
      await enterApp();
      return;
    }
    const data = await api('/api/' + authMode, { method: 'POST', body: JSON.stringify({ identifier, password }) });
    state.token = data.token;
    localStorage.setItem('tp_token', data.token);
    state.user = data.user;
    await enterApp();
  } catch (ex) {
    authMsg(ex.message, true);
  } finally {
    btn.disabled = false; setAuthMode(authMode);
  }
});

/* the browser comes back from Stripe with ?checkout=cs_... — confirm the
   payment server-side, then let them pick a password */
async function handleCheckoutReturn() {
  const q = new URLSearchParams(location.search);
  if (q.get('canceled')) {
    authMsg('Payment cancelled — nothing was charged.');
    history.replaceState(null, '', '/');
  }
  const sid = q.get('checkout');
  if (!sid) return;
  history.replaceState(null, '', '/');
  try {
    const r = await api('/api/checkout/status', { method: 'POST', body: JSON.stringify({ session_id: sid }) });
    if (r.claimed) {
      authMsg('That payment already has an account — please sign in.');
      setAuthMode('login');
      return;
    }
    if (r.paid) {
      paidSession = { session_id: sid, email: r.email };
      setAuthMode('finish');
      return;
    }
    authMsg('That payment is not confirmed yet. If you were charged, reload in a moment.');
  } catch (ex) {
    authMsg(ex.message, true);
  }
}

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
  await loadPlan();
  if (!state.token) {
    $('#authView').hidden = false;
    await handleCheckoutReturn();
    return;
  }
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
    else if (v) active = state.view.name === v || (v === 'notes' && state.view.name === 'note');
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
  notes:      () => viewNotes(),
  note:       () => viewNote(),
  dashboard:  () => viewDashboard(),
};

async function navigate(name, opts = {}) {
  state.view = { name, code: opts.code ?? state.view.code, unit: opts.unit ?? null,
                 tab: opts.tab || 'learn',
                 note: opts.note ?? (name === 'note' ? state.view.note : null) };
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

/* ================================================ NOTES → STUDY KIT == */
async function readNotesFile(file) {
  const nm = file.name.toLowerCase();
  if (nm.endsWith('.pdf')) {
    const b64 = await new Promise((res, rej) => {
      const fr = new FileReader();
      fr.onload = () => res(String(fr.result).split(',')[1] || '');
      fr.onerror = rej;
      fr.readAsDataURL(file);
    });
    return { pdf_b64: b64, filename: file.name };
  }
  const text = await new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => res(String(fr.result));
    fr.onerror = rej;
    fr.readAsText(file);
  });
  return { text, filename: file.name };
}

const engineLabel = e => e === 'ai' ? 'AI tutor' : e === 'rules' ? 'offline rules' : 'auto';

async function viewNotes() {
  const d = await api('/api/notes');
  const notes = d.notes || [];
  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow">Your own material</div>
      <h1>Notes → Study Kit</h1>
      <p>Drop in your lecture notes — paste them, or upload a .txt, .md or PDF. The portal reads them and
         builds a flashcard deck plus a graded practice exam on exactly that material. Nothing you upload
         leaves this machine.</p>
    </div>

    <div class="card" style="margin-bottom:26px">
      <h3 style="font-size:17px;margin-bottom:14px">Add notes</h3>
      <form id="noteForm" class="grid grid-2">
        <label class="field"><span>Title</span>
          <input id="nTitle" placeholder="e.g. E&M lecture 4 — Gauss &amp; potential" /></label>
        <label class="field"><span>Course (optional)</span>
          <select id="nCourse" style="width:100%;padding:11px 14px;border:1px solid var(--border);border-radius:12px;font-family:var(--body)">
            <option value="">— none —</option>
            ${state.courses.map(c => `<option value="${esc(c.code)}">${esc(c.short)}</option>`).join('')}
          </select></label>
        <label class="field" style="grid-column:1/-1"><span>Notes</span>
          <textarea id="nText" rows="8" placeholder="Paste your notes here — headings, bullet lists and
'term — definition' lines all work well." style="width:100%;padding:12px 14px;border:1px solid var(--border);border-radius:12px;font-family:var(--body);resize:vertical"></textarea></label>
        <label class="field"><span>…or upload a file (.txt, .md, .pdf)</span>
          <input id="nFile" type="file" accept=".txt,.md,.markdown,.csv,.pdf" /></label>
        <label class="field"><span>Engine</span>
          <select id="nEngine" style="width:100%;padding:11px 14px;border:1px solid var(--border);border-radius:12px;font-family:var(--body)">
            <option value="rules">Instant — offline rules, ready in a second</option>
            <option value="auto">Auto — AI tutor when it's online, otherwise instant</option>
            <option value="ai">AI tutor only — richer cards, 1–5 min on this machine</option>
          </select></label>
        <div style="grid-column:1/-1;display:flex;align-items:center;gap:12px">
          <button class="btn btn-accent" type="submit" id="nSubmit">Build my study kit</button>
          <span class="muted" id="nHint" style="font-size:12.5px"></span>
        </div>
      </form>
    </div>

    <h2 style="font-size:20px;margin-bottom:14px">My note sets</h2>
    <div id="noteList"></div>
  `;

  const form = $('#noteForm');
  $('#nSubmit').addEventListener('click', () => {});
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = $('#nSubmit'), hint = $('#nHint');
    let payload = {
      title: $('#nTitle').value.trim() || null,
      course_code: $('#nCourse').value || null,
      engine: $('#nEngine').value,
      text: $('#nText').value,
    };
    const f = $('#nFile').files[0];
    if (f) {
      try {
        const extra = await readNotesFile(f);
        payload = { ...payload, ...extra, title: payload.title || f.name };
      } catch { hint.textContent = 'Could not read that file.'; return; }
    }
    if (!(payload.text || '').trim() && !payload.pdf_b64) {
      hint.textContent = 'Paste some notes or choose a file first.'; return;
    }
    btn.disabled = true; btn.textContent = 'Uploading…'; hint.textContent = '';
    try {
      const r = await api('/api/notes', { method: 'POST', body: JSON.stringify(payload) });
      navigate('note', { note: r.id });
    } catch (ex) {
      hint.textContent = ex.message;
      btn.disabled = false; btn.textContent = 'Build my study kit';
    }
  });

  $('#noteList').innerHTML = notes.length ? notes.map(n => {
    const running = n.gen_status === 'running';
    const failed = n.gen_status === 'error';
    const c = state.courses.find(x => x.code === n.course_code);
    return `<div class="unit-row" data-nid="${n.id}">
      <div class="u-main">
        <div class="u-title">${esc(n.title)}</div>
        <div class="u-sum">${c ? esc(c.short) + ' · ' : ''}${n.words} words ·
          ${n.cards || 0} flashcards · ${n.questions || 0} exam questions ·
          engine: ${esc(engineLabel(n.gen_engine || n.engine))}${n.gen_ms ? ' (' + (n.gen_ms / 1000).toFixed(1) + 's)' : ''}</div>
      </div>
      <div class="u-right">
        ${running ? '<span class="tag warn">building…</span>'
                  : failed ? `<span class="tag bad" title="${esc(n.gen_error || '')}">failed</span>`
                           : '<span class="tag ok">ready</span>'}
        <button class="btn btn-ghost btn-sm" data-open="${n.id}">Open</button>
        <button class="btn btn-ghost btn-sm" data-del="${n.id}" title="Delete these notes">✕</button>
      </div></div>`;
  }).join('') : `<div class="empty">No notes uploaded yet — add your first set above.</div>`;

  $$('#noteList [data-open]').forEach(b => b.addEventListener('click', () => navigate('note', { note: +b.dataset.open })));
  $$('#noteList .unit-row').forEach(row => row.addEventListener('click', e => {
    if (e.target.closest('button')) return;
    navigate('note', { note: +row.dataset.nid });
  }));
  $$('#noteList [data-del]').forEach(b => b.addEventListener('click', async e => {
    e.stopPropagation();
    if (!confirm('Delete these notes and the study kit built from them?')) return;
    await api('/api/notes/' + b.dataset.del, { method: 'DELETE' });
    viewNotes();
  }));

  if (notes.some(n => n.gen_status === 'running')) setTimeout(() => {
    if (state.view.name === 'notes') viewNotes();
  }, 4000);
}

async function viewNote() {
  const nid = state.view.note;
  const g = await api('/api/notes/' + nid);
  const n = g.note, kit = g.kit;

  if (n.gen_status === 'running') {
    $('#content').innerHTML = `
      <div class="page-head">
        <div class="eyebrow">Building study kit</div>
        <h1>${esc(n.title)}</h1>
        <p>Reading your notes and writing cards${n.engine === 'rules' ? '' : ' with the local tutor model — this can take a minute or two'}…</p>
      </div>
      <div class="card"><div class="loading">Working… ${n.words} words queued. Leave this page open.</div></div>`;
    setTimeout(() => { if (state.view.name === 'note' && state.view.note === nid) viewNote(); }, 3000);
    return;
  }
  if (n.gen_status === 'error') {
    $('#content').innerHTML = `
      <div class="page-head"><div class="eyebrow">Study kit</div><h1>${esc(n.title)}</h1></div>
      <div class="card"><div class="empty">Generation failed: ${esc(n.gen_error || 'unknown error')}</div>
      <div style="margin-top:14px;display:flex;gap:10px">
        <button class="btn btn-accent" id="retryRules">Build instantly (offline rules)</button>
        <button class="btn btn-ghost" id="retryAi">Try the AI tutor again</button>
        <button class="btn btn-ghost" id="backNotes">Back</button>
      </div></div>`;
    $('#retryRules').addEventListener('click', () => regenerateNote(nid, 'rules'));
    $('#retryAi').addEventListener('click', () => regenerateNote(nid, 'ai'));
    $('#backNotes').addEventListener('click', () => navigate('notes'));
    return;
  }

  const c = state.courses.find(x => x.code === n.course_code);
  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow">${c ? esc(c.short) + ' · ' : ''}${n.words} words${n.course_code ? ' · ' + esc(n.course_code) : ''}</div>
      <h1>${esc(n.title)}</h1>
      <p>${esc(engineLabel(n.gen_engine || n.engine))} built this in ${n.gen_ms ? (n.gen_ms / 1000).toFixed(1) + 's' : 'a moment'}.
         ${n.gen_error ? esc(n.gen_error) : 'Everything here comes from the notes you uploaded.'}</p>
    </div>
    <div class="toolbar">
      <div class="tabs" id="kitTabs">
        <button class="tab active" data-tab="cards">Flashcards (${kit ? kit.cards.length : 0})</button>
        <button class="tab" data-tab="exam">Practice exam (${kit ? kit.exam.length : 0})</button>
        <button class="tab" data-tab="ask">Ask about this material</button>
      </div>
      <div class="row" style="gap:8px">
        <button class="btn btn-ghost btn-sm" id="regenBtn">Rebuild</button>
        <button class="btn btn-ghost btn-sm" id="backBtn">All notes</button>
      </div>
    </div>
    <div id="kitHost"></div>`;
  $('#backBtn').addEventListener('click', () => navigate('notes'));
  $('#regenBtn').addEventListener('click', () => {
    const engine = prompt('Rebuild with which engine?\n  auto — AI if available\n  ai — AI only (slower, richer)\n  rules — instant offline', n.engine || 'auto');
    if (engine) regenerateNote(nid, engine.trim().toLowerCase());
  });

  const host = $('#kitHost');
  const show = tab => {
    $$('#kitTabs .tab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    if (tab === 'cards') renderDeck(host, (kit && kit.cards) || [], n.title, nid);
    else if (tab === 'ask') renderAsk(host, nid, n.title);
    else renderNoteExam(host, nid, (kit && kit.exam) || []);
  };
  $$('#kitTabs .tab').forEach(b => b.addEventListener('click', () => show(b.dataset.tab)));
  show('cards');
}

async function regenerateNote(nid, engine) {
  if (!['auto', 'ai', 'rules'].includes(engine)) engine = 'auto';
  await api(`/api/notes/${nid}/generate`, { method: 'POST', body: JSON.stringify({ engine }) });
  viewNote();
}

/* Shuffle the questions AND the options, remapping the correct index so grading
   still works. Returns copies — the stored kit is never mutated. */
function shuffleDeck(cards) {
  const out = cards.map(c => {
    const opts = Array.isArray(c.opts) ? c.opts : null;
    if (!opts || typeof c.answer !== 'number') return c;
    const order = opts.map((_, i) => i);
    for (let i = order.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [order[i], order[j]] = [order[j], order[i]];
    }
    return { ...c, opts: order.map(i => opts[i]), answer: order.indexOf(c.answer) };
  });
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function renderDeck(host, cards, title, nid) {
  if (!cards.length) { host.innerHTML = `<div class="empty">No flashcards in this set.</div>`; return; }
  // Kits stored before the quiz fields existed have no options: keep the plain
  // flip card rather than showing an unanswerable question.
  if (!cards.some(c => Array.isArray(c.opts) && c.opts.length > 1)) return renderFlipDeck(host, cards, title);

  // shuffled on every render, so the questions never come up in the same order
  // twice and the correct option is not always in the same position
  let deck = shuffleDeck(cards);
  let idx = 0, pick = null, revealed = false, answered = 0, correct = 0;

  const reshuffle = () => {
    deck = shuffleDeck(cards);
    idx = 0; pick = null; revealed = false; answered = 0; correct = 0;
    draw();
  };

  const draw = () => {
    const c = deck[idx];
    const opts = Array.isArray(c.opts) ? c.opts : [];
    const hasQ = opts.length > 1 && typeof c.answer === 'number';
    const pct = answered ? Math.round(100 * correct / answered) : 0;
    host.innerHTML = `
      <div class="deck-wrap">
        <div class="deck-head">
          <span class="fc-counter">Card ${idx + 1} / ${deck.length}${c.level ? ' · ' + lvlName(c.level) : ''}</span>
          <span class="muted">${answered ? `${correct}/${answered} correct · ${pct}%` : 'Choose an option, then press Answer'}</span>
        </div>
        <div class="quiz-q">
          ${c.image ? `<figure class="q-figure">
            <img src="${mediaUrl(nid, c.image)}" loading="lazy"
                 alt="Diagram accompanying this question${c.image_page ? ', from page ' + c.image_page : ''}" />
            <figcaption>${c.image_page ? 'Diagram from page ' + c.image_page + ' of your notes' : 'Diagram from your notes'}</figcaption>
          </figure>` : ''}
          <div class="qq-text">${esc(hasQ ? (c.prompt || c.front) : c.front)}</div>
          ${hasQ ? opts.map((o, j) => {
            const mark = revealed ? (j === c.answer ? ' opt-correct' : (j === pick ? ' opt-wrong' : '')) : '';
            return `<label class="opt${mark}">
              <input type="radio" name="fcOpt" value="${j}" ${pick === j ? 'checked' : ''} ${revealed ? 'disabled' : ''} />
              <span>${esc(o)}</span></label>`;
          }).join('') : `<div class="muted">No options for this card — press Answer to reveal it.</div>`}
        </div>
        <div class="deck-actions">
          <button class="btn btn-ghost btn-sm" id="fcPrev" ${idx === 0 ? 'disabled' : ''}>← Prev</button>
          <button class="btn btn-primary btn-sm" id="fcAnswer" ${revealed ? 'disabled' : ''}>Answer</button>
          <button class="btn btn-accent btn-sm" id="fcNext" ${idx === deck.length - 1 ? 'disabled' : ''}>Next →</button>
          <button class="btn btn-ghost btn-sm" id="fcShuffle" title="New random order">⤨ Shuffle</button>
        </div>
        ${revealed ? `
        <div class="why-box">
          <div class="why-head">${pick === null ? 'Answer' : (pick === c.answer ? '✓ Correct' : '✗ Not quite')}</div>
          ${hasQ ? `<div class="why-line"><strong>Correct answer:</strong> ${esc(opts[c.answer])}</div>` : ''}
          ${c.why ? `<div class="why-line"><strong>Why:</strong> ${esc(c.why)}</div>`
                  : `<div class="why-line">${esc(c.back)}</div>`}
        </div>` : ''}
      </div>`;

    $$('input[name=fcOpt]', host).forEach(r =>
      r.addEventListener('change', () => { pick = Number(r.value); }));

    const prev = $('#fcPrev', host), next = $('#fcNext', host), ans = $('#fcAnswer', host);
    const shuf = $('#fcShuffle', host);
    if (shuf) shuf.addEventListener('click', reshuffle);
    if (prev) prev.addEventListener('click', () => { if (idx > 0) { idx--; pick = null; revealed = false; draw(); } });
    if (next) next.addEventListener('click', () => { if (idx < deck.length - 1) { idx++; pick = null; revealed = false; draw(); } });
    if (ans) ans.addEventListener('click', () => {
      revealed = true;
      if (pick !== null) { answered++; if (pick === c.answer) correct++; }
      draw();
    });
  };
  draw();
}

function renderFlipDeck(host, cards, title) {
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
          <span class="fc-counter">${st.idx + 1} / ${st.deck.length} ${c.level ? '· ' + lvlName(c.level) : ''}</span>
        </div>
      </div>`;
    $('#fcEl', host).addEventListener('click', () => { st.flipped = !st.flipped; draw(); });
    $('#fcFlip', host).addEventListener('click', () => { st.flipped = !st.flipped; draw(); });
    const p = $('#fcPrev', host), nx = $('#fcNext', host);
    if (p) p.addEventListener('click', () => { st.idx--; st.flipped = false; draw(); });
    if (nx) nx.addEventListener('click', () => { st.idx++; st.flipped = false; draw(); });
  };
  draw();
}

function renderNoteExam(host, nid, exam) {
  if (!exam.length) { host.innerHTML = `<div class="empty">No exam questions in this set.</div>`; return; }
  host.innerHTML = `
    <div class="row-between" style="margin-bottom:16px">
      <div><strong>Practice exam</strong> <span class="muted">· ${exam.length} questions · generated from your notes · pass at 70%</span></div>
    </div>
    <form id="noteExamForm">
      ${exam.map((q, i) => `
        <div class="quiz-q" data-q="${i}">
          ${q.image ? `<figure class="q-figure">
            <img src="${mediaUrl(nid, q.image)}" loading="lazy"
                 alt="Diagram for question ${i + 1}${q.image_page ? ', from page ' + q.image_page : ''}" />
            <figcaption>${q.image_page ? 'Diagram from page ' + q.image_page + ' of your notes' : 'Diagram from your notes'}</figcaption>
          </figure>` : ''}
          <div class="qq-text">${lvlBadge(q.level || 2)} ${i + 1}. ${esc(q.q)}</div>
          ${q.opts.map((o, j) => `<label class="opt"><input type="radio" name="q${i}" value="${j}" /> <span>${esc(o)}</span></label>`).join('')}
        </div>`).join('')}
      <button type="submit" class="btn btn-accent" id="neSubmit">Submit answers</button>
    </form>`;
  $$('.opt input', host).forEach(r => r.addEventListener('change', () => {
    $$(`input[name="${r.name}"]`, host).forEach(x => x.closest('.opt').classList.toggle('sel', x.checked));
  }));
  $('#noteExamForm', host).addEventListener('submit', async e => {
    e.preventDefault();
    const answers = exam.map((_, i) => {
      const sel = $(`input[name="q${i}"]:checked`, host);
      return sel ? parseInt(sel.value, 10) : -1;
    });
    if (answers.includes(-1)) { alert('Answer every question before submitting.'); return; }
    const btn = $('#neSubmit', host); btn.disabled = true; btn.textContent = 'Grading…';
    const res = await api(`/api/notes/${nid}/exam`, { method: 'POST', body: JSON.stringify({ answers }) });
    host.innerHTML = `
      <div class="card stat-card" style="margin-bottom:20px">
        <div class="big">${res.pct}%</div>
        <div class="lbl">${res.score} of ${res.total} correct — ${res.passed ? 'passed' : 'keep going, pass is 70%'}</div>
      </div>
      ${exam.map((q, i) => {
        const r = res.results[i];
        return `<div class="quiz-q ${r.correct ? 'ok' : 'bad'}">
          <div class="qq-text">${lvlBadge(q.level || 2)} ${i + 1}. ${esc(q.q)}</div>
          ${q.opts.map((o, j) => `<div class="opt ${j === r.answer ? 'sel right' : (j === r.given && !r.correct ? 'sel wrong' : '')}">
            <span>${esc(o)}</span></div>`).join('')}
          <div class="qq-explain">${esc(r.explain || '')}</div>
        </div>`;
      }).join('')}
      <button class="btn btn-ghost" id="neAgain">Retake</button>`;
    $('#neAgain', host).addEventListener('click', () => renderNoteExam(host, nid, exam));
  });
}

/* ============================================== ASK ABOUT THE MATERIAL == */
function renderAsk(host, nid, title) {
  host.innerHTML = `
    <div class="ask-wrap">
      <div class="ask-note">Answers come only from <strong>${esc(title)}</strong> — nothing from
        outside it. Every reply shows the passages it came from.</div>
      <div class="ask-log" id="askLog"></div>
      <form class="ask-form" id="askForm">
        <input id="askInput" autocomplete="off"
               placeholder="e.g. what is the time constant?   /   show me the circuit diagram" />
        <button class="btn btn-primary btn-sm" type="submit" id="askSend">Ask</button>
      </form>
      <div class="ask-hint">Try “explain the charging curve”, “show me the diagram”,
        “what happens after five time constants?”</div>
    </div>`;

  const log = $('#askLog', host);
  const bubble = (role, html) => {
    const d = document.createElement('div');
    d.className = 'ask-msg ask-' + role;
    d.innerHTML = html;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
    return d;
  };
  bubble('bot', `<div class="ask-text">Ask me anything about <strong>${esc(title)}</strong>.</div>`);

  let answered = 0;
  $('#askForm', host).addEventListener('submit', async e => {
    e.preventDefault();
    const input = $('#askInput', host);
    const q = input.value.trim();
    if (!q) return;
    input.value = '';
    bubble('user', `<div class="ask-text">${esc(q)}</div>`);
    const pending = bubble('bot', `<div class="ask-text muted">reading your material…</div>`);
    try {
      const r = await api(`/api/notes/${nid}/ask`, { method: 'POST', body: JSON.stringify({ question: q }) });
      // the "which engine" note is worth saying once, not on every answer
      pending.innerHTML = askAnswerHtml(r, nid, answered === 0);
    } catch (ex) {
      pending.innerHTML = `<div class="ask-text">${esc(ex.message)}</div>`;
    }
    answered++;
    log.scrollTop = log.scrollHeight;
  });
}

function askAnswerHtml(r, nid, showEngine) {
  const parts = [`<div class="ask-text">${esc(r.answer || '')}</div>`];
  const withFig = (r.passages || []).filter(p => p.image);
  if ((r.passages || []).length) {
    parts.push('<div class="ask-src">' + r.passages.map(p => `
      <div class="ask-passage">
        ${p.image ? `<img class="ask-fig" loading="lazy" alt="Diagram from page ${p.page || ''}"
                        src="${mediaUrl(nid, p.image)}" />` : ''}
        <blockquote>${esc(p.text)}</blockquote>
        ${p.page ? `<div class="ask-page">page ${p.page}</div>` : ''}
      </div>`).join('') + '</div>');
  }
  // the material has figures but no matching sentence named one — show them anyway
  if ((r.figures || []).length && !withFig.length) {
    parts.push('<div class="ask-src">' + r.figures.map(f => `
      <div class="ask-passage">
        <img class="ask-fig" loading="lazy" alt="Figure on page ${f.page}"
             src="${mediaUrl(nid, f.image)}" />
        <div class="ask-page">figure on page ${f.page}</div>
      </div>`).join('') + '</div>');
  }
  if (showEngine && r.fallback_reason) parts.push(`<div class="ask-why">${esc(r.fallback_reason)}</div>`);
  return parts.join('');
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
