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
          <p class="muted">Read a regression output, make a prediction, interpret every coefficient and judge significance — four questions in five minutes.</p>
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
      <p class="muted">Each exam gives a regression output and four questions: predict, interpret all coefficients,
      judge statistical significance and assess a prediction. You have five minutes.</p>
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
    const kinds = { P: "Predict", I: "Interpret", S: "Significance", R: "Reliability" };
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
  // examiner interrupts once per question with a follow-up. Optional recordings never leave the device.
  const FOLLOWUP_SECONDS = 45;

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

    const voice = () => {
      const vs = canSpeak ? speechSynthesis.getVoices() : [];
      return vs.find((v) => /en-GB/i.test(v.lang)) || vs.find((v) => /^en/i.test(v.lang)) || null;
    };
    const opts = { speak: canSpeak, record: false, interrupt: true };
    // Speak text; resolve when finished (with a time-based fallback because onend is unreliable in some browsers).
    const say = (text) => new Promise((resolve) => {
      const live = stage.querySelector("[data-live]");
      if (live) live.textContent = text;
      if (!opts.speak) return resolve();
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      const v = voice();
      if (v) u.voice = v;
      u.rate = 0.98;
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
          <li>At the end you see what the examiner was listening for, the model answers and (if you choose) your own recordings.</li>
        </ol>
        <fieldset class="options">
          <label><input type="checkbox" id="o-speak" ${canSpeak ? "checked" : "disabled"}> Read questions aloud ${canSpeak ? "" : "(not supported in this browser)"}</label>
          <label><input type="checkbox" id="o-int" checked> Interrupt me with follow-up questions</label>
          <label><input type="checkbox" id="o-rec" ${canRecord ? "" : "disabled"}> Record my answers so I can listen back (stays on this device) ${canRecord ? "" : "(not supported)"}</label>
        </fieldset>
        <p class="small muted">${items.length} questions · ${mmss(items.reduce((s, it) => s + it.seconds, 0))} answer time plus ${FOLLOWUP_SECONDS} seconds per follow-up.</p>
        <div class="row"><button class="btn primary" id="go">Start examiner mode</button></div>
      </div>`;
    stage.querySelector("#go").onclick = async () => {
      opts.speak = stage.querySelector("#o-speak").checked;
      opts.interrupt = stage.querySelector("#o-int").checked;
      opts.record = stage.querySelector("#o-rec").checked;
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
            <p class="sr-only" data-live role="status" aria-live="polite"></p>
          </div>`;
        const $ = (s) => stage.querySelector(s);
        let recorder = null, chunks = [];
        if (stream) {
          recorder = new MediaRecorder(stream);
          recorder.ondataavailable = (e) => chunks.push(e.data);
          recorder.start();
        }
        const res = { item: it, asked: false, askedAt: null, mainUsed: 0, audio: null };
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
        const startTick = () => { stop(); tick = setInterval(onTick, 1000); };
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
          const done = () => resolve(res);
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
      stage.innerHTML = `
        <div class="card stack">
          <h2>Your examiner review</h2>
          <p class="muted">For each question: what the examiner was listening for in the follow-up, and the model answer.
          ${results.some((r) => r.audio) ? "Listen to your recording and ask yourself: did I mention the key point? Did I hesitate or ramble?" : ""}</p>
        </div>
        ${results.map((r, i) => `
          <div class="card stack">
            <div class="eyebrow">Question ${i + 1}${r.item.label ? " · " + esc(r.item.label) : ""} · answered in ${mmss(r.mainUsed)} of ${mmss(r.item.seconds)}</div>
            <p><strong>${esc(r.item.prompt)}</strong></p>
            ${r.asked ? `<div class="followup"><div class="eyebrow">Follow-up${r.askedAt != null ? ` · after ${mmss(r.askedAt)}` : ""}</div><p>${esc(r.item.followup.ask)}</p>
              <div class="eyebrow">The examiner listens for</div><p>${esc(r.item.followup.listen)}</p></div>` : ""}
            ${r.audio ? `<audio controls src="${r.audio}" style="width:100%"></audio>` : ""}
            <div class="row"><button class="btn" data-toggle="answer" aria-expanded="false">Show answer</button></div>
            <div class="answer" data-answer hidden><div class="eyebrow">Model answer</div>${r.item.answerHtml}</div>
          </div>`).join("")}
        <div class="row"><button class="btn primary" id="again">Try again</button><a class="btn" href="${meta.back}">Back to the exam</a></div>`;
      wireToggles(stage);
      stage.querySelector("#again").onclick = () => route();
      results.forEach((r) => r.audio && cleanup.push(() => URL.revokeObjectURL(r.audio)));
    }
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
        label: q.tool, prompt: q.prompt, seconds: Math.round(q.minutes * 60) + 30, followup: q.followup,
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
    }, r.questions.map((q) => ({ label: "", prompt: q.prompt, seconds: 75, followup: q.followup, answerHtml: paras(q.answer) })));
  }

  function notFound() {
    render(`<h1>Page not found</h1><p><a href="#/">Go to the start page</a></p>`, "", "Not found");
  }

  // sessionStorage can be unavailable (private mode); fall back silently
  function sessionStorageGet(k) { try { return sessionStorage.getItem(k); } catch { return null; } }
  function sessionStorageSet(k, v) { try { sessionStorage.setItem(k, v); } catch { /* ignore */ } }

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
      default: return notFound();
    }
  }

  fetch("data/content.json")
    .then((r) => r.json())
    .then((data) => {
      C = data;
      C.questions.forEach((q) => (Q[q.id] = q));
      window.addEventListener("hashchange", route);
      route();
    })
    .catch(() => { main.innerHTML = `<p>Could not load the exam content. Please reload the page.</p>`; });
})();
