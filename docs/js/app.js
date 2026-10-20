/* Exam Practice — single-page app with hash routes. Content comes from data/content.json. */
(() => {
  "use strict";

  const main = document.getElementById("main");
  let C = null; // content
  let Q = {}; // questions by id
  let stopTimer = () => {};

  // ------------------------------------------------------------ helpers
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const paras = (s) => String(s).split(/\n\n+/).map((p) => `<p>${esc(p)}</p>`).join("");
  const size = (b) => (b > 1e6 ? `${(b / 1e6).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1e3))} KB`);
  const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
  const toolTag = (t) => `<span class="tag ${t.toLowerCase()}">${esc(t)}</span>`;
  const pick = (arr, avoid) => {
    const pool = arr.length > 1 ? arr.filter((x) => x.id !== avoid) : arr;
    return pool[Math.floor(Math.random() * pool.length)];
  };
  const minutes = (m) => `${m % 1 ? m.toFixed(1) : m} min`;

  function fileCard(key) {
    const d = C.datasets[key];
    return `<a class="file" href="files/${encodeURIComponent(d.file)}" download aria-label="Download ${esc(d.name)}, ${esc(d.file)}, ${size(d.size)}">
      <div><div>${esc(d.name)}</div><div class="name">${esc(d.file)} · ${size(d.size)}</div></div>
      <span aria-hidden="true">⤓</span></a>`;
  }

  function setNav(section) {
    document.querySelectorAll("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === section));
  }

  function render(html, section, title) {
    stopTimer();
    stopTimer = () => {};
    main.innerHTML = html;
    setNav(section);
    document.title = `${title ? title + " · " : ""}Exam Practice`;
    window.scrollTo(0, 0);
    main.focus({ preventScroll: true });
  }

  // ------------------------------------------------------------ timer
  function mountTimer(el, totalMin) {
    const total = totalMin * 60;
    let elapsed = 0, running = false, last = 0, tick = null, announced = false;
    el.innerHTML = `
      <div class="timer card">
        <div>
          <h3>Exam timer</h3>
          <div class="row">
            <button class="btn primary" data-act="start">Start timer</button>
            <button class="btn" data-act="pause" disabled>Pause</button>
            <button class="btn" data-act="reset" disabled>Reset</button>
          </div>
        </div>
        <div class="clocks">
          <div class="clock remaining"><div class="label">Time remaining</div><div class="value" data-v="left">${mmss(total)}</div></div>
          <div class="clock"><div class="label">Elapsed</div><div class="value" data-v="elapsed">0:00</div></div>
        </div>
      </div>
      <p class="notice" data-v="notice" role="status" aria-live="polite" hidden></p>`;
    const $ = (s) => el.querySelector(s);
    const btn = (a) => el.querySelector(`[data-act="${a}"]`);
    const draw = () => {
      const left = total - elapsed;
      $('[data-v="left"]').textContent = left >= 0 ? mmss(left) : `−${mmss(-left)}`;
      $('[data-v="elapsed"]').textContent = mmss(elapsed);
      const over = left <= 0;
      el.querySelector(".timer").classList.toggle("expired", over);
      if (over && !announced) {
        announced = true;
        const n = $('[data-v="notice"]');
        n.hidden = false;
        n.textContent = "Time is up. The elapsed clock keeps running so you can see how far over you went.";
      }
    };
    const loop = () => {
      const now = performance.now();
      elapsed += (now - last) / 1000;
      last = now;
      draw();
    };
    btn("start").onclick = () => {
      if (running) return;
      running = true; last = performance.now();
      tick = setInterval(loop, 250);
      btn("start").disabled = true; btn("pause").disabled = false; btn("reset").disabled = false;
      btn("start").textContent = "Resume";
    };
    btn("pause").onclick = () => {
      running = false; clearInterval(tick);
      btn("start").disabled = false; btn("pause").disabled = true;
    };
    btn("reset").onclick = () => {
      running = false; clearInterval(tick); elapsed = 0; announced = false;
      $('[data-v="notice"]').hidden = true;
      btn("start").disabled = false; btn("start").textContent = "Start timer";
      btn("pause").disabled = true; btn("reset").disabled = true;
      draw();
    };
    return () => clearInterval(tick);
  }

  // ------------------------------------------------------------ question panel
  function questionPanel(q, extra = "") {
    const d = C.datasets[q.dataset];
    return `
      <div class="card stack">
        <div class="split">
          <div class="row">${toolTag(q.tool)}<span class="muted small">${esc(q.id)} · ${esc(d.name)}</span></div>
          <span class="muted small">${minutes(q.minutes)} estimated</span>
        </div>
        <p class="question-text">${esc(q.prompt)}</p>
        <div class="row small muted">${q.skills.map((s) => `<span class="tag">${esc(s)}</span>`).join(" ")}</div>
        <div class="row">
          <button class="btn" data-toggle="answer" aria-expanded="false">Show answer</button>
          ${extra}
        </div>
        <div class="answer" data-answer hidden>
          <div class="eyebrow">Answer</div>
          <p><strong>${esc(q.answer)}</strong></p>
          <div class="eyebrow">${q.tool === "SQL" ? "Reference query" : "One way to get there"}</div>
          ${q.tool === "SQL" ? `<pre><code>${esc(q.solution)}</code></pre>` : `<p>${esc(q.solution)}</p>`}
        </div>
      </div>`;
  }

  function wireToggles(root) {
    root.querySelectorAll('[data-toggle="answer"]').forEach((b) => {
      b.onclick = () => {
        const a = b.closest(".card").querySelector("[data-answer]");
        a.hidden = !a.hidden;
        b.setAttribute("aria-expanded", String(!a.hidden));
        b.textContent = a.hidden ? "Show answer" : "Hide answer";
      };
    });
  }

  // ------------------------------------------------------------ pages
  function home() {
    const nEx = C.exams.length, nQ = C.questions.length, nR = C.regression.length;
    render(`
      <section class="hero">
        <div class="eyebrow">Oral exam practice</div>
        <h1>Practise the exam you will actually sit</h1>
        <p class="muted">In the oral exam you receive one full <strong>data manipulation</strong> exam (Excel and SQL)
        and one full <strong>data interpretation</strong> exam (regression). Everything here is built from the course
        cases and datasets, and every answer is computed from the files you download.</p>
      </section>
      <div class="card stack home-feature" style="margin-bottom:1rem">
        <div class="eyebrow">New · Examiner mode 🎙</div>
        <h2>Rehearse the oral part, out loud</h2>
        <p class="muted">The oral defense has no preparation time. In Examiner mode the site reads each question aloud,
        gives you a countdown to answer out loud, and interrupts with the follow-up questions an examiner asks —
        "why that join?", "is that significant?", "say it to the CFO". Afterwards you see what the examiner was listening for
        and can play back your own answers.</p>
        <div class="row"><button class="btn primary" id="try-examiner">Try a regression exam in Examiner mode</button></div>
      </div>
      <div class="grid">
        <div class="card stack">
          <div class="eyebrow">Data manipulation</div>
          <h2>${nEx} exams · ${nQ} questions</h2>
          <p class="muted">Each exam pairs one Excel file with one SQL database: five questions in ${C.exams[0].minutes} minutes.</p>
          <div class="row"><a class="btn primary" href="#/manipulation">Exams</a><a class="btn" href="#/questions">Question bank</a></div>
        </div>
        <div class="card stack">
          <div class="eyebrow">Data interpretation</div>
          <h2>${nR} regression exams</h2>
          <p class="muted">Use one regression output to make four business decisions — plan, compare groups, simplify the model, and judge whether a prediction can be trusted — in five minutes.</p>
          <div class="row"><a class="btn primary" href="#/interpretation">Regression exams</a></div>
        </div>
        <div class="card stack">
          <div class="eyebrow">Files</div>
          <h2>${Object.keys(C.datasets).length} datasets</h2>
          <p class="muted">Download each case file once and keep it open. Data descriptions explain each file's quirks.</p>
          <div class="row"><a class="btn" href="#/datasets">Datasets</a></div>
        </div>
      </div>`, "", "");
    document.getElementById("try-examiner").onclick = () => {
      location.hash = `#/regression/${pick(C.regression).id}/examiner`;
    };
  }

  function manipulation() {
    const excel = Object.entries(C.datasets).filter(([, d]) => d.tool === "Excel");
    const sql = Object.entries(C.datasets).filter(([k, d]) => d.tool === "SQL" && k !== "fiftyville");
    const opts = (list) => `<option value="">Any</option>` + list.map(([k, d]) => `<option value="${k}">${esc(d.name)}</option>`).join("");
    render(`
      <div class="eyebrow">Data manipulation</div>
      <h1>Data manipulation exams</h1>
      <p class="muted">Each exam combines Excel and SQL questions on two data files. You have ${C.exams[0].minutes} minutes,
      including opening and importing the files.</p>
      <div class="row" style="margin:1.25rem 0 2rem">
        <button class="btn primary" id="random">Choose one for me</button>
        <a class="btn" href="#/questions">Practise single questions</a>
      </div>
      <h2 class="section-title">Browse all ${C.exams.length} exams</h2>
      <div class="filters">
        <label class="small">Excel file<br><select id="fe">${opts(excel)}</select></label>
        <label class="small">SQL database<br><select id="fs">${opts(sql)}</select></label>
      </div>
      <div class="list" id="list"></div>`, "manipulation", "Data manipulation exams");
    const draw = () => {
      const fe = document.getElementById("fe").value, fs = document.getElementById("fs").value;
      const list = C.exams.filter((e) => (!fe || e.datasets[0] === fe) && (!fs || e.datasets[1] === fs));
      document.getElementById("list").innerHTML = list.map((e) => `
        <a class="item" href="#/exam/${e.id}">
          <div><div class="title">${e.id} · ${esc(C.datasets[e.datasets[0]].name)} + ${esc(C.datasets[e.datasets[1]].name)}</div>
          <div class="meta">${e.questions.map((id) => Q[id].tool).join(" · ")} · about ${minutes(e.estimate)} of work</div></div>
          <span aria-hidden="true">→</span></a>`).join("") || `<p class="muted">No exams match.</p>`;
    };
    document.getElementById("fe").onchange = draw;
    document.getElementById("fs").onchange = draw;
    document.getElementById("random").onclick = () => {
      const last = sessionStorageGet("lastExam");
      location.hash = `#/exam/${pick(C.exams, last).id}`;
    };
    draw();
  }

  function exam(id) {
    const e = C.exams.find((x) => x.id === id);
    if (!e) return notFound();
    sessionStorageSet("lastExam", id);
    const qs = e.questions.map((q) => Q[q]);
    render(`
      <a href="#/manipulation" class="small">← Back to exams</a>
      <div class="eyebrow" style="margin-top:1rem">${e.id} · Data manipulation exam · ${e.minutes} minutes</div>
      <h1>Data manipulation exam ${e.id}</h1>
      <div class="row" style="margin:1rem 0">
        <button class="btn primary" id="dlall">⤓ Download both exam files</button>
        <a class="btn" href="#/exam/${e.id}/examiner">🎙 Examiner mode</a>
      </div>
      <div class="files">${e.datasets.map(fileCard).join("")}</div>
      <div id="timer" style="margin-top:1.25rem"></div>
      <p class="muted small" style="margin-top:0.5rem">Download and open both files before you press Start. Importing the files is part of the timed exam.</p>
      <hr>
      <div class="exam">
        <div class="qnav" role="tablist" aria-label="Exam questions">
          ${qs.map((q, i) => `<button role="tab" data-i="${i}"><span class="num">0${i + 1}</span><span class="label">${esc(q.id)} · ${esc(q.tool)}</span></button>`).join("")}
        </div>
        <div id="qpanel"></div>
      </div>`, "manipulation", `Exam ${e.id}`);
    stopTimer = mountTimer(document.getElementById("timer"), e.minutes);
    const panel = document.getElementById("qpanel");
    let cur = 0;
    const show = (i) => {
      cur = i;
      panel.innerHTML = questionPanel(qs[i], `
        <span style="flex:1"></span>
        <button class="btn" data-step="-1" ${i === 0 ? "disabled" : ""}>Previous</button>
        <button class="btn" data-step="1" ${i === qs.length - 1 ? "disabled" : ""}>Next</button>`);
      wireToggles(panel);
      panel.querySelectorAll("[data-step]").forEach((b) => (b.onclick = () => show(cur + Number(b.dataset.step))));
      document.querySelectorAll(".qnav button").forEach((b, j) => b.setAttribute("aria-current", String(j === i)));
    };
    document.querySelectorAll(".qnav button").forEach((b) => (b.onclick = () => show(Number(b.dataset.i))));
    document.getElementById("dlall").onclick = () => {
      main.querySelectorAll(".files a.file").forEach((a, k) => setTimeout(() => a.click(), k * 400));
    };
    show(0);
  }

  function questionBank(params) {
    const ds = Object.entries(C.datasets);
    render(`
      <div class="eyebrow">Data manipulation</div>
      <h1>Question bank</h1>
      <p class="muted">All ${C.questions.length} questions that exams are built from. Filter by tool or file, or search for a skill such as <code>SUMIF</code> or <code>HAVING</code>.</p>
      <div class="filters">
        <select id="ft" aria-label="Tool"><option value="">Excel and SQL</option><option>Excel</option><option>SQL</option></select>
        <select id="fd" aria-label="Dataset"><option value="">All datasets</option>${ds.map(([k, d]) => `<option value="${k}">${esc(d.name)}</option>`).join("")}</select>
        <input type="search" id="fq" placeholder="Search questions or skills" aria-label="Search">
      </div>
      <p class="small muted" id="count"></p>
      <div class="list" id="list"></div>`, "manipulation", "Question bank");
    const ft = document.getElementById("ft"), fd = document.getElementById("fd"), fq = document.getElementById("fq");
    if (params.get("dataset")) fd.value = params.get("dataset");
    const draw = () => {
      const t = ft.value, d = fd.value, s = fq.value.trim().toLowerCase();
      const list = C.questions.filter((q) => (!t || q.tool === t) && (!d || q.dataset === d) &&
        (!s || (q.prompt + " " + q.skills.join(" ")).toLowerCase().includes(s)));
      document.getElementById("count").textContent = `${list.length} question${list.length === 1 ? "" : "s"}`;
      document.getElementById("list").innerHTML = list.map((q) => `
        <a class="item" href="#/question/${q.id}">
          <div><div class="title">${esc(q.prompt)}</div>
          <div class="meta">${esc(q.id)} · ${esc(q.tool)} · ${esc(C.datasets[q.dataset].name)} · ${minutes(q.minutes)}</div></div>
          <span aria-hidden="true">→</span></a>`).join("");
    };
    [ft, fd].forEach((el) => (el.onchange = draw));
    fq.oninput = draw;
    draw();
  }

  function question(id) {
    const q = Q[id];
    if (!q) return notFound();
    const same = C.questions.filter((x) => x.dataset === q.dataset);
    const i = same.indexOf(q);
    const prev = same[i - 1], next = same[i + 1];
    render(`
      <a href="#/questions?dataset=${q.dataset}" class="small">← ${esc(C.datasets[q.dataset].name)} questions</a>
      <h1 style="margin-top:1rem">Question ${esc(q.id)}</h1>
      <div class="files" style="margin:1rem 0">${fileCard(q.dataset)}</div>
      ${questionPanel(q, `<span style="flex:1"></span>
        ${prev ? `<a class="btn" href="#/question/${prev.id}">Previous</a>` : ""}
        ${next ? `<a class="btn" href="#/question/${next.id}">Next</a>` : ""}`)}
      <p class="small muted" style="margin-top:1rem"><strong>About this file:</strong> ${esc(C.datasets[q.dataset].about)}</p>`,
      "manipulation", `Question ${q.id}`);
    wireToggles(main);
  }

  function interpretation() {
    render(`
      <div class="eyebrow">Data interpretation</div>
      <h1>Data interpretation exams</h1>
      <p class="muted">Each exam gives one regression output and four decisions to make with it: a planning prediction,
      the size of a group difference, which variable (if any) to drop, and whether a prediction can be trusted.
      You have five minutes.</p>
      <div class="row" style="margin:1.25rem 0 2rem"><button class="btn primary" id="random">Choose one for me</button></div>
      <h2 class="section-title">All ${C.regression.length} exams</h2>
      <div class="list">${C.regression.map((r) => `
        <a class="item" href="#/regression/${r.id}">
          <div><div class="title">${esc(r.id)} · ${esc(r.title)}</div>
          <div class="meta">${r.table.length === 4 ? "With interaction" : "Two predictors"} · ${esc(r.source)}</div></div>
          <span aria-hidden="true">→</span></a>`).join("")}</div>`, "interpretation", "Data interpretation exams");
    document.getElementById("random").onclick = () => {
      location.hash = `#/regression/${pick(C.regression, sessionStorageGet("lastReg")).id}`;
    };
  }

  function regressionReference(r) {
    return `
      <div class="card stack">
        <div class="vars">
          <div class="var"><div class="k">${esc(r.y.name)}</div><div class="small muted">Outcome · ${esc(r.y.unit)}</div></div>
          <div class="var"><div class="k">${esc(r.x.name)}</div><div class="small muted">${esc(r.x.unit)} · Range: ${r.x.range[0].toLocaleString()}–${r.x.range[1].toLocaleString()}</div></div>
          <div class="var"><div class="k">${esc(r.d.name)}</div><div class="small muted">0 = ${esc(r.d.ref)} (reference group)<br>1 = ${esc(r.d.comp)}</div></div>
        </div>
        <div class="equation">${esc(r.equation)}</div>
        <div class="table-wrap"><table>
          <thead><tr><th>Parameter</th><th>Term</th><th>Estimate</th><th>p-value</th></tr></thead>
          <tbody>${r.table.map((t) => `<tr><td>${esc(t.param)}</td><td>${esc(t.term)}</td><td class="num">${esc(t.estimate)}</td><td class="num">${esc(t.p)}</td></tr>`).join("")}</tbody>
        </table></div>
        <p class="small muted">${esc(r.source)}</p>
      </div>`;
  }

  function regressionExam(id) {
    const r = C.regression.find((x) => x.id === id);
    if (!r) return notFound();
    sessionStorageSet("lastReg", id);
    const kinds = { P: "Plan", G: "Group gap", S: "Simplify", R: "Trust" };
    render(`
      <a href="#/interpretation" class="small">← Back to data interpretation exams</a>
      <div class="eyebrow" style="margin-top:1rem">Data interpretation exam · ${esc(r.id)}</div>
      <h1>${esc(r.title)}</h1>
      <p class="muted">${esc(r.intro)}</p>
      <div class="row" style="margin-bottom:1rem"><a class="btn" href="#/regression/${r.id}/examiner">🎙 Examiner mode: answer out loud</a></div>
      <div id="timer"></div>
      <hr>
      <div class="exam">
        <div class="qnav" role="tablist" aria-label="Exam questions">
          ${r.questions.map((q, i) => `<button role="tab" data-i="${i}"><span class="num">0${i + 1}</span><span class="label">${kinds[q.kind]}</span></button>`).join("")}
        </div>
        <div class="stack">
          <div class="card" id="qcard"></div>
          ${regressionReference(r)}
        </div>
      </div>`, "interpretation", r.title);
    stopTimer = mountTimer(document.getElementById("timer"), r.minutes);
    const card = document.getElementById("qcard");
    let cur = 0;
    const show = (i) => {
      cur = i;
      const q = r.questions[i];
      card.innerHTML = `
        <div class="stack">
          <div class="eyebrow">Question ${i + 1} · ${kinds[q.kind]}</div>
          <p class="question-text">${esc(q.prompt)}</p>
          <div class="row">
            <button class="btn" data-toggle="answer" aria-expanded="false">Show answer</button>
            <span style="flex:1"></span>
            <button class="btn" data-step="-1" ${i === 0 ? "disabled" : ""}>Previous</button>
            <button class="btn" data-step="1" ${i === r.questions.length - 1 ? "disabled" : ""}>Next</button>
          </div>
          <div class="answer" data-answer hidden><div class="eyebrow">Answer</div>${paras(q.answer)}</div>
        </div>`;
      wireToggles(card.parentElement);
      card.querySelectorAll("[data-step]").forEach((b) => (b.onclick = () => show(cur + Number(b.dataset.step))));
      document.querySelectorAll(".qnav button").forEach((b, j) => b.setAttribute("aria-current", String(j === i)));
    };
    document.querySelectorAll(".qnav button").forEach((b) => (b.onclick = () => show(Number(b.dataset.i))));
    show(0);
  }

  function datasets() {
    render(`
      <div class="eyebrow">Files</div>
      <h1>Datasets</h1>
      <p class="muted">These are the files the exams use. The two largest course databases are cut down to practice subsets so they download quickly; all answers are computed on exactly these files.</p>
      <div class="stack" style="margin-top:1.5rem">
        ${Object.entries(C.datasets).map(([k, d]) => `
          <div class="card stack">
            <div class="split">
              <div><div class="row">${toolTag(d.tool)}<span class="small muted">${esc(d.case)}</span></div><h2 style="margin-top:0.4rem">${esc(d.name)}</h2></div>
              <a class="btn" href="files/${encodeURIComponent(d.file)}" download>⤓ ${esc(d.file)} · ${size(d.size)}</a>
            </div>
            <p>${esc(d.about)}</p>
            <a class="small" href="#/questions?dataset=${k}">${d.questions} questions use this file →</a>
          </div>`).join("")}
      </div>`, "datasets", "Datasets");
  }

  // ------------------------------------------------------------ examiner mode
  // The browser reads each question aloud, the student answers out loud against a countdown, and the
  // examiner interrupts once per question with a follow-up. Optional recordings never leave the device;
  // optional transcripts use the browser's speech recognition and are kept in this browser only.
  const FOLLOWUP_SECONDS = 45;
  const ATTEMPTS_KEY = "examiner-attempts";
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

  // Speech-to-text that writes into whichever answer is currently being given.
  // Chrome copes badly with stopping and restarting recognition quickly, so the recogniser runs for the whole
  // exam: while the examiner speaks its results are simply ignored, and a watchdog restarts it if Chrome ends it.
  const CAPTURE_GRACE_MS = 800; // words finalised just after the student's turn ends still count
  function makeListener(onText, onStatus) {
    if (!SpeechRec) return null;
    const rec = new SpeechRec();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";
    let target = null, capturing = false, pausedAt = 0, keepAlive = true, running = false, starting = false;
    const start = () => {
      if (!keepAlive || running || starting) return;
      starting = true;
      try { rec.start(); } catch { starting = false; }
    };
    const watchdog = setInterval(start, 1500);
    const listener = {
      failed: false,
      listen(res, part) { target = { res, part }; capturing = true; start(); },
      pause() { if (capturing) { capturing = false; pausedAt = Date.now(); } },
      stop() { keepAlive = false; capturing = false; target = null; clearInterval(watchdog); try { rec.abort(); } catch { /* ignore */ } },
    };
    rec.onstart = () => { starting = false; running = true; onStatus(true); };
    rec.onend = () => { starting = false; running = false; onStatus(false); if (keepAlive) setTimeout(start, 250); };
    rec.onerror = (e) => {
      if (/not-allowed/.test(e.error)) { keepAlive = false; listener.failed = true; clearInterval(watchdog); }
    };
    rec.onresult = (e) => {
      const accept = capturing || Date.now() - pausedAt < CAPTURE_GRACE_MS;
      let interim = "";
      for (let k = e.resultIndex; k < e.results.length; k++) {
        const r = e.results[k];
        if (r.isFinal) { if (accept && target) target.res.text[target.part] += r[0].transcript.trim() + " "; }
        else if (capturing) interim += r[0].transcript;
      }
      if (capturing) onText(target, interim);
    };
    start();
    return listener;
  }

  // ---- checklist: does the answer mention each key point?
  const WORDNUM = { zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
    eleven: 11, twelve: 12, thirteen: 13, fourteen: 14, fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18,
    nineteen: 19, twenty: 20, thirty: 30, forty: 40, fifty: 50, sixty: 60, seventy: 70, eighty: 80, ninety: 90, hundred: 100 };
  function numbersIn(text) {
    let t = text.toLowerCase();
    while (/\d,\d{3}/.test(t)) t = t.replace(/(\d),(\d{3})/g, "$1$2");
    const out = [];
    const re = /(\d+(?:\.\d+)?)(\s*(million|thousand|k)\b)?/g;
    let m;
    while ((m = re.exec(t))) out.push(parseFloat(m[1]) * (m[3] === "million" ? 1e6 : m[3] ? 1e3 : 1));
    t.split(/[^a-z]+/).forEach((w) => { if (w in WORDNUM) out.push(WORDNUM[w]); });
    return out;
  }
  function pointMet(kp, text) {
    if (kp.number != null) {
      // alt: the same amount in the model's own units (e.g. 60 for 6,000 invoices measured in hundreds)
      const targets = [kp.number, ...(kp.alt || [])].map(Math.abs);
      return numbersIn(text).some((n) => targets.some((target) => {
        const d = Math.abs(n - target);
        return kp.tol ? d <= kp.tol * target + 0.005 : d < 1e-6;
      }));
    }
    const t = ` ${text.toLowerCase().replace(/\s+/g, " ")} `;
    return kp.terms.some((term) => t.includes(term.toLowerCase()));
  }
  const checklistHtml = (points, text) => points.map((kp) => {
    const ok = text.trim() && pointMet(kp, text);
    return `<li class="${ok ? "ok" : "miss"}"><span aria-hidden="true">${ok ? "✅" : "❌"}</span> ${esc(kp.label)}<span class="sr-only">${ok ? " — mentioned" : " — missing"}</span></li>`;
  }).join("");
  const score = (items) => items.reduce((s, it) => s + it.keypoints.filter((kp) => it.text.trim() && pointMet(kp, it.text)).length, 0);
  const maxScore = (items) => items.reduce((s, it) => s + it.keypoints.length, 0);

  function loadAttempts() { try { return JSON.parse(localStorage.getItem(ATTEMPTS_KEY) || "[]"); } catch { return []; } }
  function saveAttempts(list) { try { localStorage.setItem(ATTEMPTS_KEY, JSON.stringify(list.slice(0, 20))); } catch { /* ignore */ } }

  // Review page: transcript (editable), key-point checklist, follow-up, model answer, recording.
  function renderReview(el, review, attemptIndex) {
    const total = () => `${score(review.items)} of ${maxScore(review.items)} key points mentioned`;
    el.innerHTML = `
      <div class="card stack">
        <h2>Your examiner review</h2>
        <p class="muted">Below each question you can see what you said, which key points you mentioned, what the examiner
        listened for in the follow-up, and the model answer. The checklist matches words, not meaning — if the speech
        recognition misheard you or you said it differently, correct the text and the checklist updates.</p>
        <p><strong data-total>${total()}</strong> · ${esc(new Date(review.when).toLocaleString())}</p>
      </div>
      ${review.items.map((it, i) => `
        <div class="card stack" data-item="${i}">
          <div class="split">
            <div class="eyebrow">Question ${i + 1}${it.label ? " · " + esc(it.label) : ""}${it.mainUsed != null ? ` · answered in ${mmss(it.mainUsed)} of ${mmss(it.seconds)}` : ""}</div>
            <span class="tag" data-score>${it.keypoints.filter((kp) => it.text.trim() && pointMet(kp, it.text)).length} / ${it.keypoints.length}</span>
          </div>
          <p><strong>${esc(it.prompt)}</strong></p>
          ${it.asked ? `<div class="followup"><div class="eyebrow">Follow-up${it.askedAt != null ? ` · after ${mmss(it.askedAt)}` : ""}</div><p>${esc(it.followupAsk)}</p>
            <div class="eyebrow">The examiner listens for</div><p>${esc(it.listen)}</p></div>` : ""}
          ${it.audio ? `<audio controls src="${it.audio}" style="width:100%"></audio>` : ""}
          <label class="small muted" for="said-${i}">What you said</label>
          <textarea id="said-${i}" rows="4" placeholder="No transcript. Type what you said (or would say) and the checklist will check it.">${esc(it.text)}</textarea>
          <ul class="checklist" data-check>${checklistHtml(it.keypoints, it.text)}</ul>
          <div class="row"><button class="btn" data-toggle="answer" aria-expanded="false">Show model answer</button></div>
          <div class="answer" data-answer hidden><div class="eyebrow">Model answer</div>${it.answerHtml}</div>
        </div>`).join("")}
      <div class="row"><button class="btn primary" data-again>Try again</button><a class="btn" href="${review.back}">Back to the exam</a><a class="btn" href="#/attempts">All my attempts</a></div>`;
    wireToggles(el);
    el.querySelector("[data-again]").onclick = () => { location.hash = review.again; route(); };
    let saveTimer = null;
    el.querySelectorAll("[data-item]").forEach((card) => {
      const it = review.items[Number(card.dataset.item)];
      card.querySelector("textarea").oninput = (e) => {
        it.text = e.target.value;
        card.querySelector("[data-check]").innerHTML = checklistHtml(it.keypoints, it.text);
        card.querySelector("[data-score]").textContent = `${it.keypoints.filter((kp) => it.text.trim() && pointMet(kp, it.text)).length} / ${it.keypoints.length}`;
        el.querySelector("[data-total]").textContent = total();
        clearTimeout(saveTimer);
        saveTimer = setTimeout(() => {
          const list = loadAttempts();
          if (list[attemptIndex] && list[attemptIndex].when === review.when) {
            list[attemptIndex].items.forEach((saved, k) => { saved.text = review.items[k].text; });
            saveAttempts(list);
          }
        }, 400);
      };
    });
  }

  function examinerMode(meta, items) {
    const canSpeak = "speechSynthesis" in window;
    const canRecord = !!(navigator.mediaDevices && window.MediaRecorder);
    render(`
      <a href="${meta.back}" class="small">← Back to the exam</a>
      <div class="eyebrow" style="margin-top:1rem">Examiner mode · ${esc(meta.id)}</div>
      <h1>${esc(meta.title)}</h1>
      <div class="stack"><div id="stage" class="stack"></div>${meta.reference || ""}</div>`, meta.section, `Examiner mode · ${meta.id}`);
    const stage = document.getElementById("stage");
    let cleanup = [];
    stopTimer = () => { cleanup.forEach((f) => f()); cleanup = []; if (canSpeak) speechSynthesis.cancel(); };

    // Voice choice: the student's saved pick, else the most natural-sounding English voice available.
    const PREFERRED = [/Google UK English/i, /^Daniel/i, /Serena/i, /^Kate/i, /Samantha/i, /Google US English/i, /Natural/i];
    // macOS ships novelty voices (Bahh, Bells, Zarvox…) that make no sense for an examiner.
    const NOVELTY = /^(Albert|Bad News|Bahh|Bells|Boing|Bubbles|Cellos|Good News|Jester|Organ|Superstar|Trinoids|Whisper|Wobble|Zarvox)\b/i;
    const rank = (v) => { const i = PREFERRED.findIndex((re) => re.test(v.name)); return i < 0 ? PREFERRED.length : i; };
    const englishVoices = () => (canSpeak ? speechSynthesis.getVoices() : [])
      .filter((v) => /^en/i.test(v.lang) && !NOVELTY.test(v.name))
      .sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name));
    const prefs = { voice: localGet("examiner-voice"), rate: Number(localGet("examiner-rate")) || 1 };
    const voice = () => {
      const vs = englishVoices();
      return vs.find((v) => v.name === prefs.voice)
        || PREFERRED.map((re) => vs.find((v) => re.test(v.name))).find(Boolean)
        || vs.find((v) => /en-GB/i.test(v.lang)) || vs[0] || null;
    };
    const opts = { speak: canSpeak, record: false, interrupt: true, transcribe: !!SpeechRec };
    let listener = null, micOn = false;
    // Speak text; resolve when finished (with a time-based fallback because onend is unreliable in some browsers).
    const say = (text) => new Promise((resolve) => {
      if (listener) listener.pause(); // don't transcribe the examiner's own voice
      const live = stage.querySelector("[data-live]");
      if (live) live.textContent = text;
      if (!opts.speak) return resolve();
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      const v = voice();
      if (v) u.voice = v;
      u.rate = prefs.rate;
      let done = false;
      const finish = () => { if (!done) { done = true; clearTimeout(t); resolve(); } };
      const t = setTimeout(finish, 1500 + text.length * 75);
      u.onend = finish;
      u.onerror = finish;
      speechSynthesis.speak(u);
    });

    // ---- setup screen
    stage.innerHTML = `
      <div class="card stack">
        <p>${esc(meta.intro)}</p>
        <ol class="small">
          <li>The examiner reads each question aloud. Answer <strong>out loud</strong>, as you would in the oral exam.</li>
          <li>Somewhere during your answer the examiner <strong>interrupts with a follow-up question</strong>. Answer it, then finish your main answer.</li>
          <li>At the end you see <strong>what you said, written down</strong>, a checklist of the key points you mentioned or
          missed, what the examiner was listening for and the model answers. Your attempts are saved in this browser.</li>
        </ol>
        <fieldset class="options">
          <label><input type="checkbox" id="o-speak" ${canSpeak ? "checked" : "disabled"}> Read questions aloud ${canSpeak ? "" : "(not supported in this browser)"}</label>
          <label><input type="checkbox" id="o-int" checked> Interrupt me with follow-up questions</label>
          <label><input type="checkbox" id="o-txt" ${SpeechRec ? "checked" : "disabled"}> Write down what I say ${SpeechRec ? "" : "(not supported in this browser — use Chrome or Edge, or type your answers on the review page)"}</label>
          <label><input type="checkbox" id="o-rec" ${canRecord ? "" : "disabled"}> Record my answers so I can listen back (stays on this device) ${canRecord ? "" : "(not supported)"}</label>
        </fieldset>
        ${canSpeak ? `
        <div class="voice-row">
          <label class="small">Examiner voice<br><select id="o-voice" aria-label="Examiner voice"></select></label>
          <label class="small">Speed <span id="o-rate-val">${prefs.rate.toFixed(1)}×</span><br>
            <input type="range" id="o-rate" min="0.7" max="1.4" step="0.1" value="${prefs.rate}" aria-label="Speaking speed"></label>
          <button class="btn" id="o-test" type="button">▶ Test voice</button>
        </div>` : ""}
        ${SpeechRec ? `<p class="small muted">Writing down your answers uses your browser's speech recognition. In Chrome, the audio is sent to Google to be converted to text; this site itself stores nothing on a server.</p>` : ""}
        <p class="small muted">${items.length} questions · ${mmss(items.reduce((s, it) => s + it.seconds, 0))} answer time plus ${FOLLOWUP_SECONDS} seconds per follow-up.</p>
        <div class="row"><button class="btn primary" id="go">Start examiner mode</button></div>
      </div>`;
    if (canSpeak) {
      const sel = stage.querySelector("#o-voice");
      const fill = () => {
        const vs = englishVoices();
        const current = voice();
        sel.innerHTML = vs.map((v) => `<option value="${esc(v.name)}"${current && v.name === current.name ? " selected" : ""}>${esc(v.name)}${v.name.includes("(") ? "" : ` (${esc(v.lang)})`}</option>`).join("")
          || `<option value="">Browser default</option>`;
      };
      fill();
      // Chrome loads its voice list asynchronously.
      speechSynthesis.addEventListener("voiceschanged", fill);
      cleanup.push(() => speechSynthesis.removeEventListener("voiceschanged", fill));
      sel.onchange = () => { prefs.voice = sel.value; localSet("examiner-voice", sel.value); };
      const rate = stage.querySelector("#o-rate");
      rate.oninput = () => {
        prefs.rate = Number(rate.value);
        stage.querySelector("#o-rate-val").textContent = `${prefs.rate.toFixed(1)}×`;
        localSet("examiner-rate", String(prefs.rate));
      };
      stage.querySelector("#o-test").onclick = () => {
        const keep = opts.speak; opts.speak = true;
        say("Good morning. Let's start with the first question. Please explain your answer out loud.").then(() => { opts.speak = keep; });
      };
    }
    stage.querySelector("#go").onclick = async () => {
      opts.speak = stage.querySelector("#o-speak").checked;
      opts.interrupt = stage.querySelector("#o-int").checked;
      opts.record = stage.querySelector("#o-rec").checked;
      opts.transcribe = stage.querySelector("#o-txt").checked;
      if (opts.transcribe) {
        listener = makeListener((target, interim) => {
          const box = stage.querySelector("[data-heard]");
          if (box && target) box.textContent = (target.res.text[target.part] + interim).slice(-240) || "…";
        }, (on) => {
          micOn = on;
          const s = stage.querySelector("[data-mic]");
          if (s) s.textContent = on ? "🎤 listening" : "🎤 reconnecting…";
        });
        if (listener) cleanup.push(() => listener.stop());
      }
      let stream = null;
      if (opts.record) {
        try {
          stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          cleanup.push(() => stream.getTracks().forEach((t) => t.stop()));
        } catch {
          opts.record = false;
        }
      }
      run(stream);
    };

    async function run(stream) {
      const results = [];
      for (let i = 0; i < items.length; i++) {
        results.push(await askOne(items[i], i, stream));
        if (!stage.isConnected) return;
      }
      if (stream) stream.getTracks().forEach((t) => t.stop());
      await say("That's all the questions. Thank you.");
      if (listener) listener.stop();
      summary(results);
    }

    function askOne(it, i, stream) {
      return new Promise((resolve) => {
        stage.innerHTML = `
          <div class="card stack examiner">
            <div class="split">
              <div class="eyebrow">Question ${i + 1} of ${items.length}${it.label ? " · " + esc(it.label) : ""}</div>
              ${stream ? `<span class="tag rec">● Recording</span>` : ""}
            </div>
            <p class="question-text">${esc(it.prompt)}</p>
            <div class="followup" data-fu hidden>
              <div class="eyebrow">Examiner interrupts</div>
              <p class="question-text">${esc(it.followup.ask)}</p>
            </div>
            <div class="split">
              <div class="clock remaining"><div class="label" data-phase>Listen…</div><div class="value" data-left>${mmss(it.seconds)}</div></div>
              <div class="row">
                <button class="btn" data-act="repeat">Repeat</button>
                <button class="btn primary" data-act="done" disabled>I'm done</button>
              </div>
            </div>
            ${listener ? `<div class="heard"><div class="split"><div class="eyebrow">Heard so far</div><span class="small" data-mic>${micOn ? "🎤 listening" : "🎤 starting…"}</span></div><p data-heard>…</p></div>` : ""}
            <p class="sr-only" data-live role="status" aria-live="polite"></p>
          </div>`;
        const $ = (s) => stage.querySelector(s);
        let recorder = null, chunks = [];
        if (stream) {
          recorder = new MediaRecorder(stream);
          recorder.ondataavailable = (e) => chunks.push(e.data);
          recorder.start();
        }
        const res = { item: it, asked: false, askedAt: null, mainUsed: 0, audio: null, text: { main: "", fu: "" } };
        let left = it.seconds, fuLeft = FOLLOWUP_SECONDS, phase = "intro", tick = null, finished = false;
        // Interrupt somewhere between 35% and 65% of the main answer time.
        const interruptAt = Math.round(it.seconds * (0.35 + Math.random() * 0.3));
        const stop = () => clearInterval(tick);
        cleanup.push(stop);

        const draw = () => {
          $("[data-left]").textContent = mmss(phase === "followup" ? fuLeft : Math.max(0, left));
          $("[data-phase]").textContent = { intro: "Listen…", main: "Your answer", followup: "Follow-up answer", speaking: "Examiner speaking…" }[phase];
          $('[data-act="done"]').disabled = !(phase === "main" || phase === "followup");
        };
        // Every time the student's turn (re)starts, listen into the right part of the answer.
        const startTick = () => {
          stop(); tick = setInterval(onTick, 1000);
          if (listener && (phase === "main" || phase === "followup")) listener.listen(res, phase === "main" ? "main" : "fu");
        };
        const onTick = () => {
          if (phase === "main") {
            left -= 1; res.mainUsed += 1;
            if (opts.interrupt && !res.asked && it.seconds - left >= interruptAt) return interrupt("Sorry to interrupt. ");
            if (left <= 0) return endMain();
          } else if (phase === "followup") {
            fuLeft -= 1;
            if (fuLeft <= 0) return endFollowup();
          }
          draw();
        };
        const interrupt = async (lead) => {
          stop();
          res.asked = true; res.askedAt = it.seconds - left;
          phase = "speaking"; draw();
          $("[data-fu]").hidden = false;
          await say(lead + it.followup.ask);
          if (finished) return;
          phase = "followup"; draw(); startTick();
        };
        const endFollowup = async () => {
          stop();
          if (left > 0) {
            phase = "speaking"; draw();
            await say("Thank you. Please finish your answer to the main question.");
            if (finished) return;
            $("[data-fu]").hidden = true;
            phase = "main"; draw(); startTick();
          } else {
            finish();
          }
        };
        const endMain = async () => {
          stop();
          if (opts.interrupt && !res.asked) return interrupt(left <= 0 ? "Time. One more question before we move on. " : "Before we move on: ");
          finish();
        };
        const finish = () => {
          if (finished) return;
          finished = true; stop();
          if (listener) listener.pause();
          // Give the recogniser a moment to deliver the last words before moving on.
          const done = () => setTimeout(() => resolve(res), listener ? 700 : 0);
          if (recorder && recorder.state !== "inactive") {
            recorder.onstop = () => { res.audio = URL.createObjectURL(new Blob(chunks, { type: recorder.mimeType })); done(); };
            recorder.stop();
          } else done();
        };

        $('[data-act="done"]').onclick = () => (phase === "followup" ? endFollowup() : endMain());
        $('[data-act="repeat"]').onclick = async () => {
          if (phase === "speaking") return;
          const prev = phase; stop(); phase = "speaking"; draw();
          await say(prev === "followup" ? it.followup.ask : it.prompt);
          if (finished) return;
          phase = prev === "intro" ? "main" : prev; draw(); startTick();
        };
        (async () => {
          phase = "speaking"; draw();
          await say(`Question ${i + 1}. ${it.prompt}`);
          if (finished) return;
          phase = "main"; draw(); startTick();
        })();
      });
    }

    function summary(results) {
      const review = {
        when: new Date().toISOString(), title: meta.title, id: meta.id, back: meta.back, again: location.hash,
        items: results.map((r) => ({
          label: r.item.label, prompt: r.item.prompt, followupAsk: r.item.followup.ask, listen: r.item.followup.listen,
          answerHtml: r.item.answerHtml, keypoints: r.item.keypoints, asked: r.asked, askedAt: r.askedAt,
          mainUsed: r.mainUsed, seconds: r.item.seconds,
          text: (r.text.main.trim() + (r.text.fu.trim() ? `\n\n[Follow-up] ${r.text.fu.trim()}` : "")).trim(),
        })),
      };
      const list = loadAttempts();
      list.unshift(review);
      saveAttempts(list);
      // Recordings are shown on this page only; they are not saved.
      results.forEach((r, i) => { if (r.audio) { review.items[i].audio = r.audio; cleanup.push(() => URL.revokeObjectURL(r.audio)); } });
      renderReview(stage, review, 0);
      if (listener && listener.failed) {
        stage.insertAdjacentHTML("afterbegin", `<p class="notice">Speech recognition was blocked (microphone permission), so nothing was written down. You can type your answers below.</p>`);
      }
    }
  }

  function attempts(index) {
    const list = loadAttempts();
    if (index != null) {
      const review = list[index];
      if (!review) return notFound();
      render(`<a href="#/attempts" class="small">← All my attempts</a>
        <div class="eyebrow" style="margin-top:1rem">Examiner mode · ${esc(review.id)}</div>
        <h1>${esc(review.title)}</h1><div id="stage" class="stack"></div>`, "attempts", "My attempt");
      renderReview(document.getElementById("stage"), review, index);
      return;
    }
    render(`
      <div class="eyebrow">Examiner mode</div>
      <h1>My attempts</h1>
      <p class="muted">Your Examiner mode attempts (up to the last 20), saved in this browser only. Open one to see
      what you said and which key points you covered.</p>
      <div class="list" style="margin-top:1rem">${list.map((a, i) => `
        <a class="item" href="#/attempts/${i}">
          <div><div class="title">${esc(a.title)}</div>
          <div class="meta">${esc(new Date(a.when).toLocaleString())} · ${score(a.items)} of ${maxScore(a.items)} key points</div></div>
          <span aria-hidden="true">→</span></a>`).join("") || `<p class="muted">No attempts yet. Open any exam and press 🎙 Examiner mode.</p>`}</div>
      ${list.length ? `<div class="row" style="margin-top:1.5rem"><button class="btn" id="clear">Delete all attempts</button></div>` : ""}`,
      "attempts", "My attempts");
    const clear = document.getElementById("clear");
    if (clear) clear.onclick = () => { if (confirm("Delete all saved attempts from this browser?")) { saveAttempts([]); attempts(); } };
  }

  function examExaminer(id) {
    const e = C.exams.find((x) => x.id === id);
    if (!e) return notFound();
    examinerMode({
      id: e.id, title: `Data manipulation exam ${e.id}`, back: `#/exam/${e.id}`, section: "manipulation",
      intro: `Open ${C.datasets[e.datasets[0]].file} and ${C.datasets[e.datasets[1]].file} first. Work in Excel and your SQL tool while you talk the examiner through what you are doing and why.`,
    }, e.questions.map((qid) => {
      const q = Q[qid];
      return {
        label: q.tool, prompt: q.prompt, seconds: Math.round(q.minutes * 60) + 30, followup: q.followup, keypoints: q.keypoints,
        answerHtml: `<p><strong>${esc(q.answer)}</strong></p>${q.tool === "SQL" ? `<pre><code>${esc(q.solution)}</code></pre>` : `<p>${esc(q.solution)}</p>`}`,
      };
    }));
  }

  function regressionExaminer(id) {
    const r = C.regression.find((x) => x.id === id);
    if (!r) return notFound();
    examinerMode({
      id: r.id, title: r.title, back: `#/regression/${r.id}`, section: "interpretation", intro: r.intro,
      reference: regressionReference(r),
    }, r.questions.map((q) => ({ label: "", prompt: q.prompt, seconds: 75, followup: q.followup, keypoints: q.keypoints, answerHtml: paras(q.answer) })));
  }

  function notFound() {
    render(`<h1>Page not found</h1><p><a href="#/">Go to the start page</a></p>`, "", "Not found");
  }

  // Browser storage can be unavailable (private mode); fall back silently
  function sessionStorageGet(k) { try { return sessionStorage.getItem(k); } catch { return null; } }
  function sessionStorageSet(k, v) { try { sessionStorage.setItem(k, v); } catch { /* ignore */ } }
  function localGet(k) { try { return localStorage.getItem(k); } catch { return null; } }
  function localSet(k, v) { try { localStorage.setItem(k, v); } catch { /* ignore */ } }

  // ------------------------------------------------------------ router
  function route() {
    const [path, query] = location.hash.replace(/^#/, "").split("?");
    const parts = path.split("/").filter(Boolean);
    const params = new URLSearchParams(query || "");
    switch (parts[0]) {
      case undefined: return home();
      case "manipulation": return manipulation();
      case "exam": return parts[2] === "examiner" ? examExaminer(parts[1]) : exam(parts[1]);
      case "questions": return questionBank(params);
      case "question": return question(parts[1]);
      case "interpretation": return interpretation();
      case "regression": return parts[2] === "examiner" ? regressionExaminer(parts[1]) : regressionExam(parts[1]);
      case "datasets": return datasets();
      case "attempts": return attempts(parts[1] != null ? Number(parts[1]) : null);
      default: return notFound();
    }
  }

  // no-cache: revalidate with the server so students always get the latest questions after an update
  fetch("data/content.json", { cache: "no-cache" })
    .then((r) => r.json())
    .then((data) => {
      C = data;
      C.questions.forEach((q) => (Q[q.id] = q));
      window.addEventListener("hashchange", route);
      route();
    })
    .catch(() => { main.innerHTML = `<p>Could not load the exam content. Please reload the page.</p>`; });
})();
