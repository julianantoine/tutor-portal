/* =========================================================================
   Tutor Portal — HOSTED STATIC DEMO (GitHub Pages)
   Full curriculum + flashcards + client-side graded quizzes + a browser-local
   login/register and per-user score tracking. No backend.
   The real app (saved server-side progress + streaming AI tutor) runs locally:
   clone the repo and run ./start.sh
   ========================================================================= */

const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
const pctColor = p => p >= 70 ? 'var(--green)' : p >= 40 ? 'var(--amber)' : 'var(--red)';

let DATA = { courses: [], quiz: {} };
const state = { code: null, unit: null, user: null };

/* ----------------------------------------------------- auth (local) ---- */
const usersKey = 'tp_users';
const sessKey  = 'tp_session';
const loadUsers = () => { try { return JSON.parse(localStorage.getItem(usersKey)) || {}; } catch { return {}; } };
const saveUsers = u => localStorage.setItem(usersKey, JSON.stringify(u));
const progressKey = () => 'tp_progress_' + (state.user || 'anon');
const loadProgress = () => { try { return JSON.parse(localStorage.getItem(progressKey())) || {}; } catch { return {}; } };
const saveProgress = p => localStorage.setItem(progressKey(), JSON.stringify(p));
function setProgress(course, unit, pct) {
  const p = loadProgress();
  p[unit] = Math.max(p[unit] || 0, pct);
  saveProgress(p);
}
function courseMastery(code) {
  const p = loadProgress();
  const c = DATA.courses.find(x => x.code === code);
  if (!c) return 0;
  const sum = c.units.reduce((n, u) => n + (p[u.id] || 0), 0);
  return Math.round(sum / c.units.length);
}
function overallMastery() {
  const total = DATA.courses.reduce((n, c) => n + courseMastery(c.code), 0);
  return DATA.courses.length ? Math.round(total / DATA.courses.length) : 0;
}

let authMode = 'login';
$('#authSeg').addEventListener('click', e => {
  const b = e.target.closest('.seg-btn'); if (!b) return;
  authMode = b.dataset.mode;
  $$('#authSeg .seg-btn').forEach(x => x.classList.toggle('active', x === b));
  $('#authSubmit').textContent = authMode === 'login' ? 'Log in' : 'Create account';
  $('#nameField').hidden = authMode !== 'register';
});
$('#authForm').addEventListener('submit', e => {
  e.preventDefault();
  const err = $('#authErr'); err.hidden = true;
  const u = $('#authUser').value.trim(), p = $('#authPass').value, nm = $('#authName').value.trim();
  if (u.length < 3) { err.textContent = 'Username must be at least 3 characters.'; err.hidden = false; return; }
  if (p.length < 4) { err.textContent = 'Password must be at least 4 characters.'; err.hidden = false; return; }
  const users = loadUsers();
  if (authMode === 'register') {
    if (users[u.toLowerCase()]) { err.textContent = 'That username is taken.'; err.hidden = false; return; }
    users[u.toLowerCase()] = { password: p, name: nm || u };
    saveUsers(users);
    state.user = u.toLowerCase();
    localStorage.setItem(sessKey, state.user);
    enterApp();
  } else {
    const rec = users[u.toLowerCase()];
    if (!rec || rec.password !== p) { err.textContent = 'Wrong username or password. (New here? Register, or use demo / demo.)'; err.hidden = false; return; }
    state.user = u.toLowerCase();
    localStorage.setItem(sessKey, state.user);
    enterApp();
  }
});
$('#logoutBtn').addEventListener('click', () => {
  localStorage.removeItem(sessKey);
  state.user = null;
  $('#appView').hidden = true; $('#authView').hidden = false;
  authMode = 'login';
  $$('#authSeg .seg-btn').forEach(x => x.classList.toggle('active', x.dataset.mode === 'login'));
  $('#authSubmit').textContent = 'Log in';
  $('#nameField').hidden = true;
});

function seedDemoUser() {
  const users = loadUsers();
  if (!users['demo']) { users['demo'] = { password: 'demo', name: 'Demo Student' }; saveUsers(users); }
}

/* --------------------------------------------------------------- boot --- */
(async function boot() {
  seedDemoUser();
  renderAsideCourses();
  try {
    DATA = await (await fetch('curriculum.json')).json();
  } catch (e) {
    $('#content').innerHTML = `<div class="empty">Could not load curriculum.json — open this from the repo's docs/ folder or the Pages site.</div>`;
    return;
  }
  const sess = localStorage.getItem(sessKey);
  if (sess && loadUsers()[sess]) { state.user = sess; enterApp(); }
  else { $('#authView').hidden = false; }
})();

function renderAsideCourses() {
  const courses = [
    ['#4b5563', 'Calculus II', '4 cr · integration, series, polar, ODEs'],
    ['#374151', 'Physics II (Electricity & Magnetism)', '4 cr · fields, circuits, magnetism'],
    ['#52525b', 'Character, Career & Self Development', '2 cr · ethics, communication, career'],
    ['#71717a', 'Modeling and Design', '3 cr · design process, CAD, drawings'],
    ['#3f3f46', 'Static Modeling of Mechanical Systems', '3 cr · statics, trusses, friction'],
    ['#a1a1aa', 'Engineering Materials', '3 cr · bonding, phases, failure, selection'],
  ];
  $('#asideCourses').innerHTML = courses.map(([c, t, s]) =>
    `<li><span class="dot" style="background:${c}"></span><div><div>${esc(t)}</div><div class="a-sub">${esc(s)}</div></div></li>`
  ).join('');
}

function enterApp() {
  $('#authView').hidden = true;
  $('#appView').hidden = false;
  const rec = loadUsers()[state.user];
  $('#whoami').textContent = rec ? rec.name : state.user;
  renderNav();
  overview();
}
$('#menuBtn').addEventListener('click', () => $('#sidebar').classList.toggle('open'));

/* ------------------------------------------------------------- nav ----- */
function renderNav() {
  $('#navCourses').innerHTML = `<div class="nav-label">Courses</div>` + DATA.courses.map(c => {
    const m = courseMastery(c.code);
    return `<a class="nav-item" data-code="${esc(c.code)}">
      <span class="nav-dot" style="background:${c.accent}"></span>
      <span>${esc(c.short)}</span>
      <span class="m-pct">${m}%</span></a>`;
  }).join('');
  $$('#navCourses .nav-item').forEach(a => a.addEventListener('click', () => courseView(a.dataset.code)));
}
function markNav(code) {
  $$('#navCourses .nav-item').forEach(a => a.classList.toggle('active', a.dataset.code === code));
  $$('.nav-item[data-view]').forEach(a => a.classList.toggle('active', !code && a.dataset.view === 'overview'));
}

function flashcards(course, unit) {
  const cards = [];
  const c = DATA.courses.find(x => x.code === course);
  if (!c) return cards;
  for (const u of c.units) {
    if (unit && u.id !== unit) continue;
    (u.concepts || []).forEach(k => cards.push({ unit: u.id, front: k.t, back: k.d }));
    (u.formulas || []).forEach(k => cards.push({ unit: u.id, front: k.n, back: `${k.e} — ${k.note}` }));
  }
  return cards;
}

/* ------------------------------------------------------------ overview --- */
function overview() {
  state.code = null; state.unit = null; markNav(null);
  renderNav();
  const units = DATA.courses.reduce((n, c) => n + c.units.length, 0);
  const p = loadProgress();
  const passed = DATA.courses.reduce((n, c) => n + c.units.filter(u => (p[u.id] || 0) >= 70).length, 0);
  const first = (loadUsers()[state.user]?.name || state.user).split(' ')[0];

  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow">Welcome back, ${esc(first)}</div>
      <h1>Your grade-recovery plan</h1>
      <p>${units} units across ${DATA.courses.length} courses. Work a unit top to bottom — read the concepts,
      study the worked example, flip the flashcards, pass the quiz at 70%.</p>
    </div>
    <div class="grid grid-4" style="margin-bottom:26px">
      <div class="card stat-card"><div class="big">${overallMastery()}%</div><div class="lbl">Overall mastery</div></div>
      <div class="card stat-card"><div class="big">${passed}<span class="muted" style="font-size:19px">/${units}</span></div><div class="lbl">Units passed</div></div>
      <div class="card stat-card"><div class="big">${DATA.courses.length}</div><div class="lbl">Courses</div></div>
      <div class="card stat-card"><div class="big">${Object.values(DATA.quiz).reduce((n, v) => n + v.length, 0)}</div><div class="lbl">Quiz questions</div></div>
    </div>
    <h2 style="font-size:22px;margin-bottom:16px">Courses</h2>
    <div class="grid-courses" style="margin-bottom:34px">
      ${DATA.courses.map(c => {
        const m = courseMastery(c.code);
        const done = c.units.filter(u => (p[u.id] || 0) >= 70).length;
        return `<div class="card hoverable course-card" data-code="${esc(c.code)}">
          <div class="course-head">
            <span class="cc-dot" style="background:${c.accent}"></span>
            <div><div class="cc-code">${esc(c.code)} · ${c.credits} cr</div><h3>${esc(c.title)}</h3></div>
          </div>
          <p class="cc-blurb">${esc(c.blurb)}</p>
          <div class="meter-row"><span class="meter" style="flex:1"><i style="width:${m}%;background:${c.accent}"></i></span><span>${m}%</span></div>
          <div class="muted" style="font-size:12.5px">${done}/${c.units.length} units at 70%+ · ${flashcards(c.code).length} flashcards</div>
        </div>`;
      }).join('')}
    </div>
    <div class="card" style="border-left:3px solid #3f3f46">
      <h3 style="font-size:17px;margin-bottom:8px">The AI tutor runs locally</h3>
      <p class="muted" style="margin:0;font-size:14px">
        This hosted page is the curriculum demo (your login and scores are saved in this browser). The full
        product — server-side progress, assignment tracking, and a streaming AI tutor powered by a local Ollama
        model — runs on your own machine with no cloud bill. Clone
        <a href="https://github.com/julianantoine/tutor-portal" target="_blank" rel="noopener" style="color:var(--accent-ink)">julianantoine/tutor-portal</a>
        and run <code>./start.sh</code>.
      </p>
    </div>`;
  $$('#content .course-card').forEach(el => el.addEventListener('click', () => courseView(el.dataset.code)));
}

/* -------------------------------------------------------------- course --- */
function courseView(code) {
  state.code = code; state.unit = null; markNav(code);
  const c = DATA.courses.find(x => x.code === code);
  const p = loadProgress();
  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow" style="color:var(--ink-3)">${esc(c.code)} · ${c.credits} credits</div>
      <h1>${esc(c.title)}</h1>
      <p>${esc(c.blurb)}</p>
      <div class="meter-row" style="max-width:420px;margin-top:16px">
        <span class="meter"><i style="width:${courseMastery(code)}%;background:${c.accent}"></i></span>
        <span><strong>${courseMastery(code)}%</strong> course mastery</span>
      </div>
    </div>
    <div class="row-between" style="margin-bottom:14px">
      <h2 style="font-size:20px">Units</h2>
      <button class="btn btn-ghost btn-sm" id="allCards">Flashcards · all units</button>
    </div>
    <div id="unitList">${c.units.map((u, i) => {
      const m = p[u.id] || 0;
      const tag = m >= 70 ? '<span class="tag ok">passed</span>' : (m > 0 ? '<span class="tag warn">in&nbsp;progress</span>' : '<span class="tag neutral">new</span>');
      return `<div class="unit-row" data-unit="${esc(u.id)}">
        <span class="u-num">${i + 1}</span>
        <div class="u-main"><div class="u-title">${esc(u.title)}</div><div class="u-sum">${esc(u.summary)}</div></div>
        <div class="u-right">${tag}<span class="mini-bar"><i style="width:${m}%;background:${pctColor(m)}"></i></span><span class="u-pct">${m}%</span></div>
      </div>`;
    }).join('')}</div>`;
  $$('#unitList .unit-row').forEach(el => el.addEventListener('click', () => unitView(code, el.dataset.unit)));
  $('#allCards').addEventListener('click', () => {
    openModal('Flashcards — ' + c.short, '<div id="host"></div>');
    drawCards($('#host'), flashcards(code));
  });
}

/* ---------------------------------------------------------------- unit --- */
function unitView(code, uid) {
  state.code = code; state.unit = uid; markNav(code);
  const c = DATA.courses.find(x => x.code === code);
  const u = c.units.find(x => x.id === uid);
  const idx = c.units.findIndex(x => x.id === uid) + 1;

  $('#content').innerHTML = `
    <div class="page-head">
      <a class="btn btn-ghost btn-sm" id="back" style="color:var(--ink-2)">← ${esc(c.short)}</a>
      <div class="eyebrow" style="color:var(--ink-3);margin-top:18px">${esc(c.code)} · Unit ${idx} of ${c.units.length}</div>
      <h1>${esc(u.title)}</h1><p>${esc(u.summary)}</p>
    </div>
    <div class="tabs">
      <button class="tab active" data-t="learn">Learn</button>
      <button class="tab" data-t="cards">Flashcards</button>
      <button class="tab" data-t="quiz">Quiz</button>
    </div>
    <div class="tab-panel active" id="p-learn"></div>
    <div class="tab-panel" id="p-cards"></div>
    <div class="tab-panel" id="p-quiz"></div>`;
  $('#back').addEventListener('click', () => courseView(code));

  $('#p-learn').innerHTML = `
    <div class="learn-block"><h3>Key concepts</h3>
      ${u.concepts.map(k => `<div class="concept"><div class="c-t">${esc(k.t)}</div><div class="c-d">${esc(k.d)}</div></div>`).join('')}</div>
    <div class="learn-block"><h3>Formulas &amp; rules</h3>
      ${u.formulas.map(f => `<div class="formula"><span class="f-name">${esc(f.n)}</span><span class="f-eq">${esc(f.e)}</span><span class="f-note">${esc(f.note)}</span></div>`).join('')}</div>
    <div class="learn-block"><h3>Worked example</h3>
      <div class="example-card"><h4>${esc(u.example.problem)}</h4>
        <ol>${u.example.steps.map(s => `<li>${esc(s)}</li>`).join('')}</ol>
        <div class="answer-box"><strong>Answer:</strong> ${esc(u.example.answer)}</div></div></div>
    <div class="grid grid-2">
      <div class="learn-block"><h3>Common traps</h3>${u.traps.map(t => `<div class="trap">${esc(t)}</div>`).join('')}</div>
      <div class="learn-block"><h3>Practise these</h3>
        ${u.practice.map((p, i) => `<div class="practice-item">
          <div class="practice-q"><strong>Q${i + 1}.</strong> ${esc(p.q)}</div>
          <button class="btn btn-ghost btn-sm reveal-btn" data-a="${i}">Show answer</button>
          <div class="practice-a" id="a${i}" hidden>${esc(p.a)}</div></div>`).join('')}</div>
    </div>`;
  $$('#p-learn .reveal-btn').forEach(b => b.addEventListener('click', () => {
    const el = $('#a' + b.dataset.a);
    el.hidden = !el.hidden; b.textContent = el.hidden ? 'Show answer' : 'Hide answer';
  }));

  drawCards($('#p-cards'), flashcards(code, uid));
  quizPanel($('#p-quiz'), code, uid);

  $$('.tab').forEach(t => t.addEventListener('click', () => {
    $$('.tab').forEach(x => x.classList.toggle('active', x === t));
    $$('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'p-' + t.dataset.t));
  }));
}

/* ----------------------------------------------------------- flashcards --- */
function drawCards(host, cards) {
  if (!cards.length) { host.innerHTML = `<div class="empty">No flashcards here.</div>`; return; }
  const st = { idx: 0, flipped: false };
  const draw = () => {
    const c = cards[st.idx];
    host.innerHTML = `
      <div class="fc-wrap">
        <div class="fc ${st.flipped ? 'flipped' : ''}" id="fcEl"><div class="fc-inner">
          <div class="fc-face fc-front"><div class="fc-kicker">Prompt</div><div class="fc-text">${esc(c.front)}</div></div>
          <div class="fc-face fc-back"><div class="fc-kicker">Answer</div><div class="fc-text small">${esc(c.back)}</div></div>
        </div></div>
        <div class="fc-controls">
          <button class="btn btn-ghost btn-sm" id="prev" ${st.idx === 0 ? 'disabled' : ''}>← Prev</button>
          <button class="btn btn-primary btn-sm" id="flip">Flip</button>
          <button class="btn btn-ghost btn-sm" id="next" ${st.idx === cards.length - 1 ? 'disabled' : ''}>Next →</button>
          <span class="fc-counter">${st.idx + 1} / ${cards.length}</span>
        </div></div>`;
    $('#fcEl', host).addEventListener('click', () => { st.flipped = !st.flipped; draw(); });
    $('#flip', host).addEventListener('click', () => { st.flipped = !st.flipped; draw(); });
    const p = $('#prev', host), n = $('#next', host);
    if (p) p.addEventListener('click', () => { st.idx--; st.flipped = false; draw(); });
    if (n) n.addEventListener('click', () => { st.idx++; st.flipped = false; draw(); });
  };
  draw();
}

/* ----------------------------------------------------------------- quiz --- */
function quizPanel(host, code, unit) {
  const bank = (DATA.quiz[code] || []).filter(q => q.unit === unit);
  if (!bank.length) { host.innerHTML = `<div class="empty">No quiz for this unit.</div>`; return; }
  const best = loadProgress()[unit] || 0;
  host.innerHTML = `
    <div class="card" style="max-width:640px">
      <h3 style="font-size:19px;margin-bottom:8px">Unit quiz</h3>
      <p class="muted" style="margin:0 0 16px">${bank.length} questions · 70% to pass.${best ? ` Your best so far: <strong>${best}%</strong>.` : ''} Graded in your browser; your best score is saved.</p>
      <button class="btn btn-accent" id="start">Start quiz</button>
    </div>`;
  $('#start', host).addEventListener('click', () => start(host, bank, code, unit));
}

function start(host, bank, code, unit) {
  host.innerHTML = `<form id="qf">${bank.map((q, i) => `
    <div class="quiz-q"><div class="qq-text">${i + 1}. ${esc(q.q)}</div>
      ${q.opts.map((o, j) => `<label class="opt"><input type="radio" name="q${i}" value="${j}" /> <span>${esc(o)}</span></label>`).join('')}
    </div>`).join('')}<button class="btn btn-accent" type="submit">Submit answers</button></form>`;
  $$('.opt input', host).forEach(r => r.addEventListener('change', () =>
    $$(`input[name="${r.name}"]`, host).forEach(x => x.closest('.opt').classList.toggle('sel', x.checked))));
  $('#qf', host).addEventListener('submit', e => {
    e.preventDefault();
    const picks = bank.map((_, i) => { const s = $(`input[name="q${i}"]:checked`, host); return s ? +s.value : -1; });
    if (picks.includes(-1)) { alert('Answer every question first.'); return; }
    let score = 0;
    const rows = bank.map((q, i) => { const ok = picks[i] === q.answer; if (ok) score++; return { q, given: picks[i], ok }; });
    const pct = Math.round(100 * score / bank.length);
    if (code && unit) setProgress(code, unit, pct);
    host.innerHTML = `
      <div class="result-banner ${pct >= 70 ? 'pass' : 'fail'}">
        <div class="rb-score">${pct}%</div>
        <div class="rb-txt"><strong>${pct >= 70 ? 'Passed — unit marked complete' : 'Not passed yet (need 70%)'}</strong>
        <small>${score} of ${bank.length} correct</small></div>
        <div class="spacer"></div><button class="btn btn-primary btn-sm" id="retry">Retry</button>
      </div>
      ${rows.map((r, i) => `<div class="quiz-q"><div class="qq-text">${i + 1}. ${esc(r.q.q)}</div>
        ${r.q.opts.map((o, j) => {
          let cls = 'opt';
          if (j === r.q.answer) cls += ' right'; else if (j === r.given) cls += ' wrong';
          return `<div class="${cls}"><span>${esc(o)}</span>${j === r.q.answer ? '<span class="spacer"></span><span class="tag ok">correct</span>' : (j === r.given ? '<span class="spacer"></span><span class="tag bad">your pick</span>' : '')}</div>`;
        }).join('')}
        <div class="quiz-explain"><strong>Why:</strong> ${esc(r.q.explain)}</div></div>`).join('')}`;
    $('#retry', host).addEventListener('click', () => start(host, bank, code, unit));
    renderNav();
  });
}

/* --------------------------------------------------------------- modal --- */
function openModal(title, html) {
  let ov = $('#modalOverlay');
  if (!ov) {
    ov = document.createElement('div');
    ov.id = 'modalOverlay'; ov.className = 'modal-overlay';
    ov.innerHTML = `<div class="modal"><div class="modal-head"><h3 id="modalTitle"></h3><button class="icon-btn" id="modalClose">✕</button></div><div class="modal-body" id="modalBody"></div></div>`;
    document.body.appendChild(ov);
    ov.addEventListener('click', e => { if (e.target === ov) closeModal(); });
    $('#modalClose', ov).addEventListener('click', closeModal);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
  }
  $('#modalTitle').textContent = title;
  $('#modalBody').innerHTML = html;
  ov.classList.add('open');
}
function closeModal() { const ov = $('#modalOverlay'); if (ov) ov.classList.remove('open'); }
