/* =========================================================================
   Tutor Portal — HOSTED STATIC DEMO (GitHub Pages)
   Full curriculum + flashcards + client-side graded quizzes, no backend.
   The real app (accounts, saved progress, streaming AI tutor) runs locally:
   clone the repo and run ./start.sh
   ========================================================================= */

const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
const pctColor = p => p >= 70 ? 'var(--green)' : p >= 40 ? 'var(--amber)' : 'var(--red)';

let DATA = { courses: [], quiz: {} };
const state = { code: null, unit: null };

/* --------------------------------------------------------------- load --- */
(async function boot() {
  try {
    const res = await fetch('curriculum.json');
    DATA = await res.json();
  } catch (e) {
    $('#content').innerHTML = `<div class="empty">Could not load curriculum.json — open this page from the repo's docs/ folder or the Pages site.</div>`;
    return;
  }
  renderNav();
  overview();
})();

function flashcards(course, unit) {
  const cards = [];
  const c = DATA.courses.find(x => x.code === course);
  if (!c) return cards;
  for (const u of c.units) {
    if (unit && u.id !== unit) continue;
    (u.concepts || []).forEach((k, i) => cards.push({ unit: u.id, front: k.t, back: k.d }));
    (u.formulas || []).forEach((k, i) => cards.push({ unit: u.id, front: k.n, back: `${k.e} — ${k.note}` }));
  }
  return cards;
}

function renderNav() {
  $('#navCourses').innerHTML = `<div class="nav-label">Courses</div>` + DATA.courses.map(c =>
    `<a class="nav-item" data-code="${esc(c.code)}">
      <span class="nav-dot" style="background:${c.accent}"></span>
      <span>${esc(c.short)}</span>
      <span class="m-pct">${c.units.length}u</span></a>`).join('');
  $$('#navCourses .nav-item').forEach(a => a.addEventListener('click', () => courseView(a.dataset.code)));
}

function markNav(code) {
  $$('#navCourses .nav-item').forEach(a => a.classList.toggle('active', a.dataset.code === code));
}

/* ------------------------------------------------------------ overview --- */
function overview() {
  state.code = null; state.unit = null; markNav(null);
  const units = DATA.courses.reduce((n, c) => n + c.units.length, 0);
  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow">Study plan</div>
      <h1>Bring the grades up.</h1>
      <p>${units} units across ${DATA.courses.length} courses. Work a unit top to bottom — read the concepts,
      study the worked example, flip the flashcards, pass the quiz at 70%.</p>
    </div>
    <div class="grid grid-2">
      ${DATA.courses.map(c => `
        <div class="card hoverable course-card" data-code="${esc(c.code)}">
          <div class="course-head">
            <span class="cc-dot" style="background:${c.accent}"></span>
            <div><div class="cc-code">${esc(c.code)} · ${c.credits} cr</div><h3>${esc(c.title)}</h3></div>
          </div>
          <p class="cc-blurb">${esc(c.blurb)}</p>
          <div class="muted" style="font-size:12.5px">${c.units.length} units · ${flashcards(c.code).length} flashcards</div>
        </div>`).join('')}
    </div>
    <div class="card" style="margin-top:22px;border-left:3px solid var(--accent)">
      <h3 style="font-size:17px;margin-bottom:8px">The AI tutor runs locally</h3>
      <p class="muted" style="margin:0;font-size:14px">
        This hosted page is the curriculum demo. The full product — username/password accounts, saved
        mastery, assignment tracking, and a streaming AI tutor powered by a local Ollama model — runs on
        your own machine with no cloud bill. Clone
        <a href="https://github.com/julianantoine/tutor-portal" target="_blank" rel="noopener" style="color:var(--accent)">julianantoine/tutor-portal</a>
        and run <code>./start.sh</code>.
      </p>
    </div>`;
  $$('#content .course-card').forEach(el => el.addEventListener('click', () => courseView(el.dataset.code)));
}

/* -------------------------------------------------------------- course --- */
function courseView(code) {
  state.code = code; state.unit = null; markNav(code);
  const c = DATA.courses.find(x => x.code === code);
  $('#content').innerHTML = `
    <div class="page-head">
      <div class="eyebrow" style="color:${c.accent}">${esc(c.code)} · ${c.credits} credits</div>
      <h1>${esc(c.title)}</h1>
      <p>${esc(c.blurb)}</p>
    </div>
    <div class="row-between" style="margin-bottom:14px">
      <h2 style="font-size:20px">Units</h2>
      <button class="btn btn-ghost btn-sm" id="allCards">Flashcards · all units</button>
    </div>
    <div id="unitList">${c.units.map((u, i) => `
      <div class="unit-row" data-unit="${esc(u.id)}">
        <span class="u-num">${i + 1}</span>
        <div class="u-main"><div class="u-title">${esc(u.title)}</div><div class="u-sum">${esc(u.summary)}</div></div>
        <div class="u-right"><span class="tag neutral">${u.concepts.length} concepts</span></div>
      </div>`).join('')}</div>`;
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
      <a class="btn btn-ghost btn-sm" id="back">← ${esc(c.short)}</a>
      <div class="eyebrow" style="color:${c.accent};margin-top:18px">${esc(c.code)} · Unit ${idx} of ${c.units.length}</div>
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
  host.innerHTML = `
    <div class="card" style="max-width:640px">
      <h3 style="font-size:19px;margin-bottom:8px">Unit quiz</h3>
      <p class="muted" style="margin:0 0 16px">${bank.length} questions · 70% to pass. Graded in your browser — the local app saves your best score.</p>
      <button class="btn btn-accent" id="start">Start quiz</button>
    </div>`;
  $('#start', host).addEventListener('click', () => start(host, bank));
}

function start(host, bank) {
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
    host.innerHTML = `
      <div class="result-banner ${pct >= 70 ? 'pass' : 'fail'}">
        <div class="rb-score">${pct}%</div>
        <div class="rb-txt"><strong>${pct >= 70 ? 'Passed' : 'Not passed yet (need 70%)'}</strong>
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
    $('#retry', host).addEventListener('click', () => start(host, bank));
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
  return true;
}
function closeModal() { const ov = $('#modalOverlay'); if (ov) ov.classList.remove('open'); }
