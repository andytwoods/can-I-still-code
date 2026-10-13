/**
 * Browser Python tutorial – UI controller.
 *
 * No requests to the Django app after page load: the bank is a static JSON file,
 * learner code runs in tutorial-worker.js (Pyodide), progress lives in localStorage.
 * See docs/tutorial/README.md.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "tutorial_v1";
  var STATE_SCHEMA = 1;
  var INIT_DEADLINE_MS = 60000;
  var PACKAGE_DEADLINE_MS = 60000;
  var RUN_DEADLINE_MS = 5000;
  var GENERATE_DEADLINE_MS = 2000;
  var BLOCK6 = 6;
  var KIND_LABELS = { check: "Check task", core: "Core task", practice: "Practice", fix: "Practice: fix it" };
  var RATING_STEPS = { too_easy: 2, easy: 1, just_right: 0, hard: 0, too_hard: -1 };

  var app = document.getElementById("tutorial-app");
  if (!app) return;

  function $(id) { return document.getElementById(id); }

  // ── small helpers ─────────────────────────────────────────────────────────

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  var PLACEHOLDER = /@@([A-Za-z_][A-Za-z0-9_]*)@@/g;

  function fillHtml(html, display) {
    return html.replace(PLACEHOLDER, function (m, name) {
      return Object.prototype.hasOwnProperty.call(display, name) ? escapeHtml(display[name]) : m;
    });
  }

  function fillCode(src, reprs) {
    return (src || "").replace(PLACEHOLDER, function (m, name) {
      return Object.prototype.hasOwnProperty.call(reprs, name) ? reprs[name] : m;
    });
  }

  function newSeed() {
    try {
      var a = new Uint32Array(1);
      window.crypto.getRandomValues(a);
      return a[0] % 1000000000;
    } catch (_) {
      return Math.floor(Math.random() * 1000000000);
    }
  }

  function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }

  function toast(message, type, action) {
    var container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      container.setAttribute("aria-live", "polite");
      document.body.appendChild(container);
    }
    var el = document.createElement("div");
    el.className = "notification toast " + (type || "is-info");
    var close = document.createElement("button");
    close.className = "delete";
    close.setAttribute("aria-label", "Dismiss");
    el.appendChild(close);
    var text = document.createElement("span");
    text.textContent = message;
    el.appendChild(text);
    function dismiss() {
      el.classList.add("toast-out");
      el.addEventListener("animationend", function () { el.remove(); }, { once: true });
      setTimeout(function () { if (el.isConnected) el.remove(); }, 600);
    }
    close.addEventListener("click", dismiss);
    if (action) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "button is-small is-white ml-2";
      btn.textContent = action.label;
      btn.addEventListener("click", function () { action.onClick(); dismiss(); });
      el.appendChild(btn);
    }
    container.appendChild(el);
    setTimeout(function () { if (el.isConnected) dismiss(); }, action ? 12000 : 5000);
  }
  if (!window.showToast) window.showToast = function (m, t) { toast(m, t); };

  // ── storage ───────────────────────────────────────────────────────────────

  var storageOk = true;

  function freshState(bankVersion) {
    return { schema_version: STATE_SCHEMA, bank_version: bankVersion, blocks: {}, ladders: {}, tasks: {}, current: { block: 1, taskId: null } };
  }

  function isObj(x) { return x !== null && typeof x === "object" && !Array.isArray(x); }

  function loadState(bank) {
    var raw = null;
    try {
      raw = window.localStorage.getItem(STORAGE_KEY);
    } catch (_) {
      storageOk = false;
      return freshState(bank.bank_version);
    }
    var st;
    try { st = raw ? JSON.parse(raw) : null; } catch (_) { st = null; }
    if (!isObj(st) || st.schema_version !== STATE_SCHEMA) return freshState(bank.bank_version);
    var out = freshState(bank.bank_version);
    if (isObj(st.blocks)) {
      Object.keys(st.blocks).forEach(function (k) {
        var b = st.blocks[k];
        if (isObj(b)) out.blocks[k] = { done: !!b.done, checkPassed: !!b.checkPassed, ladderStarted: !!b.ladderStarted };
      });
    }
    if (isObj(st.ladders)) {
      Object.keys(st.ladders).forEach(function (k) {
        var l = st.ladders[k];
        if (isObj(l) && typeof l.level === "number") {
          out.ladders[k] = { level: clamp(Math.round(l.level), 1, 5), streak: typeof l.streak === "number" ? l.streak : 0, taskId: typeof l.taskId === "string" && bank.tasks[l.taskId] ? l.taskId : null };
        }
      });
    }
    if (isObj(st.tasks)) {
      // A new bank version keeps progress only for task ids that still exist.
      Object.keys(st.tasks).forEach(function (id) {
        var t = st.tasks[id];
        if (!bank.tasks[id] || !isObj(t) || typeof t.seed !== "number") return;
        out.tasks[id] = {
          seed: t.seed,
          code: typeof t.code === "string" ? t.code : null,
          attempts: typeof t.attempts === "number" ? t.attempts : 0,
          fails: typeof t.fails === "number" ? t.fails : 0,
          passed: !!t.passed,
          everPassed: !!t.everPassed,
          hintShown: !!t.hintShown,
          solutionViewed: !!t.solutionViewed,
          rating: typeof t.rating === "string" ? t.rating : null,
        };
      });
    }
    if (isObj(st.current)) {
      var b = Number(st.current.block);
      if (b >= 1 && b <= BLOCK6) out.current.block = b;
      if (typeof st.current.taskId === "string" && bank.tasks[st.current.taskId]) out.current.taskId = st.current.taskId;
    }
    return out;
  }

  function saveState() {
    if (!storageOk) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (_) {
      storageOk = false;
      $("storage-banner").classList.remove("is-hidden");
    }
  }

  // ── Python worker client ──────────────────────────────────────────────────

  var py = {
    worker: null,
    gen: 0,
    opSeq: 0,
    ready: false,
    failed: false,
    pending: null,
    initTimer: null,
    packages: {},
    onReady: null,
    onFail: null,

    start: function () {
      this.stop();
      this.gen += 1;
      this.ready = false;
      this.failed = false;
      this.packages = {};
      var self = this;
      var gen = this.gen;
      this.worker = new Worker(app.dataset.workerUrl);
      this.worker.onmessage = function (e) { self.receive(e.data); };
      this.worker.onerror = function (e) {
        if (gen !== self.gen) return;
        if (!self.ready) self.initFailed("The Python worker could not start (" + (e.message || "error") + ").");
      };
      this.initTimer = setTimeout(function () {
        if (gen === self.gen && !self.ready) self.initFailed("Python took more than a minute to load.");
      }, INIT_DEADLINE_MS);
      this.worker.postMessage({ type: "init", workerGen: gen, runnerUrl: new URL(app.dataset.runnerUrl, window.location.href).href });
    },

    stop: function () {
      clearTimeout(this.initTimer);
      if (this.pending) {
        clearTimeout(this.pending.timer);
        var p = this.pending;
        this.pending = null;
        p.reject({ restarted: true });
      }
      if (this.worker) this.worker.terminate();
      this.worker = null;
      this.ready = false;
    },

    initFailed: function (why) {
      this.stop();
      this.failed = true;
      if (this.onFail) this.onFail(why);
    },

    receive: function (msg) {
      if (!msg || msg.workerGen !== this.gen) return; // reply from an old worker
      if (msg.type === "ready") {
        clearTimeout(this.initTimer);
        this.ready = true;
        if (this.onReady) this.onReady();
        return;
      }
      if (msg.type === "init_error") {
        this.initFailed("Python could not load: " + msg.error);
        return;
      }
      if (!this.pending || msg.opId !== this.pending.opId) return; // stale operation
      var p = this.pending;
      this.pending = null;
      clearTimeout(p.timer);
      p.resolve(msg);
      this.idle();
    },

    idle: function () {
      var self = this;
      setTimeout(function () { if (!self.pending && self.onIdle) self.onIdle(); }, 0);
    },

    busy: function () { return !!this.pending; },

    request: function (msg, deadlineMs, onTimeout) {
      var self = this;
      return new Promise(function (resolve, reject) {
        if (!self.ready) { reject({ notReady: true }); return; }
        if (self.pending) { reject({ busy: true }); return; }
        self.opSeq += 1;
        msg.opId = self.opSeq;
        msg.workerGen = self.gen;
        var entry = { opId: msg.opId, resolve: resolve, reject: reject };
        entry.timer = setTimeout(function () {
          if (self.pending !== entry) return;
          self.pending = null;
          onTimeout();
          reject({ timeout: true });
          self.idle();
        }, deadlineMs);
        self.pending = entry;
        self.worker.postMessage(msg);
      });
    },

    ensurePackages: function (names) {
      var self = this;
      var missing = names.filter(function (n) { return !self.packages[n]; });
      if (!missing.length) return Promise.resolve();
      return this.request({ type: "load_packages", packages: missing }, PACKAGE_DEADLINE_MS, function () {
        self.initFailed("Loading the plotting library took more than a minute.");
      }).then(function (msg) {
        if (msg.type !== "packages_loaded") {
          self.initFailed("The plotting library could not load: " + msg.error);
          throw { packageError: true };
        }
        missing.forEach(function (n) { self.packages[n] = true; });
      });
    },

    timeoutRestart: function () {
      // terminate() is the only way to stop runaway code in a worker
      this.start();
    },
  };

  // ── state ─────────────────────────────────────────────────────────────────

  var bank = null;
  var state = null;
  var cm = null;
  var variant = null; // { taskId, seed, params, display, reprs }
  var loadingTask = false;
  var waitingForIdle = false;

  function task() { return state.current.taskId ? bank.tasks[state.current.taskId] : null; }
  function blockInfo(n) { return bank.blocks.filter(function (b) { return b.block === n; })[0] || null; }
  function blockState(n) {
    if (!state.blocks[n]) state.blocks[n] = { done: false, checkPassed: false, ladderStarted: false };
    return state.blocks[n];
  }
  function ladder(n) {
    if (!state.ladders[n]) state.ladders[n] = { level: 1, streak: 0, taskId: null };
    return state.ladders[n];
  }
  function taskState(id) {
    var ts = state.tasks[id];
    if (!ts) {
      var t = bank.tasks[id];
      ts = state.tasks[id] = {
        seed: t.kind === "core" && typeof t.fixed_seed === "number" ? t.fixed_seed : newSeed(),
        code: null, attempts: 0, fails: 0, passed: false, everPassed: false,
        hintShown: false, solutionViewed: false, rating: null,
      };
    }
    return ts;
  }
  function tasksOf(n, kinds) {
    var b = blockInfo(n);
    if (!b) return [];
    return b.task_ids.map(function (id) { return bank.tasks[id]; }).filter(function (t) { return kinds.indexOf(t.kind) >= 0; });
  }
  function isPractice(t) { return t && (t.kind === "practice" || t.kind === "fix"); }

  function templateForLevel(n, level) {
    var options = tasksOf(n, ["practice", "fix"]);
    if (!options.length) return null;
    var exact = options.filter(function (t) { return t.level === level; });
    if (exact.length) return exact[Math.floor(Math.random() * exact.length)];
    // Nearest available level (a ladder may be incomplete while authoring)
    options.sort(function (a, b) { return Math.abs(a.level - level) - Math.abs(b.level - level); });
    return options[0];
  }

  function currentCode() { return cm ? cm.getValue() : $("editor").value; }
  function setCode(code) {
    if (cm) { cm.setValue(code); cm.clearHistory(); cm.refresh(); } else { $("editor").value = code; }
  }
  function saveCode() {
    var t = task();
    if (t && variant && variant.taskId === t.id) taskState(t.id).code = currentCode();
  }

  // ── rendering ─────────────────────────────────────────────────────────────

  function renderBlockList() {
    var ul = $("block-list");
    ul.innerHTML = "";
    bank.blocks.concat([{ block: BLOCK6, title: "Working in notebooks (Colab)" }]).forEach(function (b) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "#block-" + b.block;
      a.dataset.block = b.block;
      var done = b.block !== BLOCK6 && blockState(b.block).done;
      a.innerHTML = '<span class="tutorial-tick" aria-hidden="true">' + (done ? "✓" : "") + "</span>" +
        escapeHtml(b.block + ". " + b.title) + (done ? ' <span class="is-sr-only">(done)</span>' : "");
      if (b.block === state.current.block) { a.classList.add("is-active"); a.setAttribute("aria-current", "page"); }
      a.addEventListener("click", function (e) { e.preventDefault(); goBlock(b.block); });
      li.appendChild(a);
      ul.appendChild(li);
    });
  }

  function renderTabs() {
    var n = state.current.block;
    var ul = $("task-tabs");
    ul.innerHTML = "";
    var items = [];
    tasksOf(n, ["check"]).forEach(function (t) { items.push({ label: "Check task", id: t.id, match: function (c) { return c.id === t.id; } }); });
    tasksOf(n, ["core"]).forEach(function (t, i) { items.push({ label: "Core " + (i + 1), id: t.id, match: function (c) { return c.id === t.id; } }); });
    if (tasksOf(n, ["practice", "fix"]).length) {
      items.push({ label: "Practice (level " + ladder(n).level + ")", id: "__practice__", match: isPractice });
    }
    var cur = task();
    items.forEach(function (it) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "#";
      a.setAttribute("role", "tab");
      var passed = it.id !== "__practice__" && state.tasks[it.id] && state.tasks[it.id].everPassed;
      a.textContent = (passed ? "✓ " : "") + it.label;
      var active = cur && it.match(cur);
      if (active) { li.classList.add("is-active"); a.setAttribute("aria-selected", "true"); }
      a.addEventListener("click", function (e) {
        e.preventDefault();
        if (it.id === "__practice__") openPractice(); else openTask(it.id);
      });
      li.appendChild(a);
      ul.appendChild(li);
    });
  }

  function renderBlock() {
    var n = state.current.block;
    renderBlockList();
    if (n === BLOCK6) {
      $("block-view").classList.add("is-hidden");
      $("block6-view").classList.remove("is-hidden");
      return;
    }
    $("block6-view").classList.add("is-hidden");
    $("block-view").classList.remove("is-hidden");
    if (cm) cm.refresh(); // CodeMirror measures its gutter wrongly while hidden
    var b = blockInfo(n);
    $("block-title").textContent = n + ". " + b.title;
    $("block-explanation").innerHTML = b.explanation_html;
    var hasCheck = tasksOf(n, ["check"]).length > 0;
    $("check-offer").classList.toggle("is-hidden", !hasCheck || blockState(n).checkPassed || (task() && task().kind === "check"));
    renderTabs();
  }

  function setButtons() {
    var t = task();
    var ts = t ? taskState(t.id) : null;
    var ok = py.ready && !py.busy() && !!variant && !loadingTask;
    $("run-btn").disabled = !ok;
    $("new-btn").disabled = !ok || !t || !t.generator;
    $("hint-btn").disabled = !t || !ts || (ts.fails < 1 && !ts.hintShown);
    $("solution-btn").disabled = !t || !ts || (ts.fails < 2 && !ts.solutionViewed);
    $("next-btn").disabled = !t || loadingTask || py.busy();
    var note = "";
    if (t && ts && !ts.passed) {
      if (ts.fails < 1) note = "A hint unlocks after one try; a worked solution after two.";
      else if (ts.fails < 2) note = "A worked solution unlocks after one more try.";
    }
    $("unlock-note").textContent = note;
  }

  function clearFeedback() {
    $("results").innerHTML = "";
    $("output").textContent = "";
    $("output-wrap").classList.add("is-hidden");
    $("plots").innerHTML = "";
    $("hint-box").classList.add("is-hidden");
    $("solution-box").classList.add("is-hidden");
    $("rating").classList.add("is-hidden");
    $("check-failed-note").classList.add("is-hidden");
  }

  function renderTaskHeader(t) {
    $("task-title").textContent = t.title;
    $("task-kind").textContent = KIND_LABELS[t.kind];
    var lv = $("task-level");
    if (isPractice(t)) { lv.textContent = "Level " + t.level + " of 5"; lv.classList.remove("is-hidden"); }
    else lv.classList.add("is-hidden");
  }

  function showPromptPlaceholder(t) {
    $("task-prompt").innerHTML = py.failed
      ? "<p><em>Python is not running. Use “Try again” below.</em></p>"
      : '<p class="has-text-grey"><span class="icon"><i class="fas fa-spinner fa-spin" aria-hidden="true"></i></span> Preparing the task&hellip;</p>';
    renderTaskHeader(t);
  }

  // ── opening tasks ─────────────────────────────────────────────────────────

  function openTask(id, opts) {
    opts = opts || {};
    saveCode();
    state.current.taskId = id;
    var t = bank.tasks[id];
    state.current.block = t.block;
    variant = null;
    clearFeedback();
    renderBlock();
    showPromptPlaceholder(t);
    saveState();
    prepareVariant(opts.fresh);
  }

  function openPractice() {
    var n = state.current.block;
    var lad = ladder(n);
    blockState(n).ladderStarted = true;
    var t = lad.taskId && bank.tasks[lad.taskId] && bank.tasks[lad.taskId].block === n ? bank.tasks[lad.taskId] : null;
    if (!t || t.level !== lad.level) {
      t = templateForLevel(n, lad.level);
      if (!t) return;
      lad.taskId = t.id;
    }
    openTask(t.id);
  }

  function prepareVariant(fresh) {
    var t = task();
    if (!t) return;
    var ts = taskState(t.id);
    if (fresh) {
      ts.seed = newSeed();
      ts.code = null; ts.attempts = 0; ts.fails = 0; ts.passed = false;
      ts.hintShown = false; ts.solutionViewed = false; ts.rating = null;
    }
    if (!py.ready) { setButtons(); return; } // resumed from onReady
    if (py.busy()) { waitingForIdle = true; setButtons(); return; } // resumed from onIdle
    loadingTask = true;
    setButtons();
    var wantId = t.id;
    var seed = ts.seed;
    var done = function (params, display, reprs) {
      loadingTask = false;
      if (state.current.taskId !== wantId) { setButtons(); return; }
      variant = { taskId: wantId, seed: seed, params: params, display: display, reprs: reprs };
      $("task-prompt").innerHTML = fillHtml(t.prompt_html, display);
      renderTaskHeader(t);
      if (ts.code === null) ts.code = fillCode(t.starter_code, reprs);
      setCode(ts.code);
      if (ts.hintShown) showHint();
      if (ts.solutionViewed) showSolution();
      if (ts.passed && isPractice(t) && !ts.solutionViewed) showRating();
      setButtons();
      saveState();
    };
    if (!t.generator) { done({}, {}, {}); return; }
    py.request({ type: "generate", taskId: t.id, generatorSrc: t.generator, seed: seed }, GENERATE_DEADLINE_MS, function () {
      py.timeoutRestart();
    }).then(function (msg) {
      if (msg.type !== "generated") {
        loadingTask = false;
        $("task-prompt").innerHTML = '<p class="has-text-danger">This task could not be prepared (' + escapeHtml(msg.error) + "). Please tell the organiser.</p>";
        setButtons();
        return;
      }
      done(msg.params, msg.display, msg.reprs);
    }, function (err) {
      loadingTask = false;
      if (err && err.timeout) $("task-prompt").innerHTML = "<p>Preparing this task took too long. Python is restarting&hellip;</p>";
      setButtons();
    });
  }

  // ── running ───────────────────────────────────────────────────────────────

  function runCode() {
    var t = task();
    if (!t || !variant || !py.ready || py.busy() || loadingTask) return;
    var ts = taskState(t.id);
    var code = currentCode();
    ts.code = code;
    clearFeedback();
    $("results").innerHTML = '<p class="has-text-grey">Running&hellip;</p>';
    var seed = variant.seed;
    var params = variant.params;
    var timedOut = false;
    var run = function () {
      var pr = py.request({
        type: "run", code: code, referenceSrc: t.reference, params: params, injectParams: !!t.inject_params,
        checks: t.checks, seed: seed, allowPlot: !!t.allow_plot,
      }, RUN_DEADLINE_MS, function () { timedOut = true; py.timeoutRestart(); });
      setButtons();
      return pr;
    };
    var start = t.allow_plot ? py.ensurePackages(["matplotlib"]) : Promise.resolve();
    if (t.allow_plot && py.busy()) $("results").innerHTML = '<p class="has-text-grey">Loading the plotting library (first time only, up to a minute)&hellip;</p>';
    setButtons();
    $("run-btn").disabled = true;
    var stillHere = function () { return state.current.taskId === t.id && variant && variant.seed === seed; };
    start.then(run).then(function (msg) {
      ts.attempts += 1;
      if (!stillHere()) { // the learner moved on while it ran: record, don't render
        if (msg.type === "result") { ts.passed = !!msg.passed; if (msg.passed) ts.everPassed = true; else ts.fails += 1; }
        saveState();
        setButtons();
        return;
      }
      if (msg.type !== "result") {
        showSystemError("Something went wrong running your code: " + msg.error);
        setButtons();
        return;
      }
      renderResult(t, ts, msg);
    }, function (err) {
      if (!stillHere()) { setButtons(); saveState(); return; }
      if (err && err.timeout && timedOut) {
        ts.attempts += 1;
        ts.fails += 1;
        ts.passed = false;
        $("results").innerHTML = "";
        appendNotice("is-danger", "Your code took too long – is there a loop that never ends? Python is restarting (a few seconds).");
      } else if (err && err.packageError) {
        $("results").innerHTML = "";
      } else if (err && err.restarted) {
        $("results").innerHTML = "";
      }
      setButtons();
      saveState();
    });
  }

  function appendNotice(cls, text, extraHtml) {
    var div = document.createElement("div");
    div.className = "notification is-light py-2 px-3 mb-2 " + cls;
    div.textContent = text;
    if (extraHtml) div.insertAdjacentHTML("beforeend", extraHtml);
    $("results").appendChild(div);
    return div;
  }

  function showSystemError(text) {
    $("results").innerHTML = "";
    appendNotice("is-danger", text);
  }

  function renderResult(t, ts, msg) {
    var results = $("results");
    results.innerHTML = "";
    var learner = msg.learner;
    var passed = !!msg.passed;
    if (passed) {
      var head = appendNotice("is-success", "✓ Passed – well done!");
      head.classList.add("has-text-weight-semibold");
    }
    if (learner.error) {
      var e = learner.error;
      var box = document.createElement("div");
      box.className = "notification is-danger is-light py-2 px-3 mb-2";
      box.innerHTML = "<strong>✗ Error" + (e.line ? " on line " + e.line : "") + ":</strong> " + escapeHtml(e.friendly) +
        '<pre class="tutorial-error mt-2">' + escapeHtml(e.last_line) + "</pre>";
      results.appendChild(box);
      if (cm && e.line) {
        var h = cm.addLineClass(e.line - 1, "background", "tutorial-error-line");
        var clear = function () { cm.removeLineClass(h, "background", "tutorial-error-line"); cm.off("change", clear); };
        cm.on("change", clear);
      }
    }
    (learner.notes || []).forEach(function (n) { appendNotice("is-warning", "Note: " + n); });
    msg.checks.forEach(function (c) {
      var div = document.createElement("div");
      div.className = "notification is-light py-2 px-3 mb-2 tutorial-check " + (c.passed ? "is-success" : "is-danger");
      var html = "<strong>" + (c.passed ? "✓ PASS" : "✗ FAIL") + "</strong> " + escapeHtml(c.message);
      if (!c.passed && (c.expected !== "" || c.actual !== "")) {
        html += '<dl class="tutorial-diff"><dt>Expected</dt><dd><pre>' + escapeHtml(c.expected) + "</pre></dd>" +
          "<dt>Yours</dt><dd><pre>" + escapeHtml(c.actual) + "</pre></dd></dl>";
      }
      div.innerHTML = html;
      results.appendChild(div);
    });
    var out = learner.stdout + (learner.stderr ? "\n" + learner.stderr : "");
    if (out.trim()) {
      $("output").textContent = out;
      $("output-wrap").classList.remove("is-hidden");
    }
    var plots = $("plots");
    plots.innerHTML = "";
    (learner.plots || []).forEach(function (b64, i) {
      var img = document.createElement("img");
      img.src = "data:image/png;base64," + b64;
      img.alt = "Your plot " + (i + 1);
      img.className = "tutorial-plot";
      plots.appendChild(img);
    });

    ts.passed = passed;
    if (passed) {
      ts.everPassed = true;
      onPass(t, ts);
    } else {
      ts.fails += 1;
      if (t.kind === "check") $("check-failed-note").classList.remove("is-hidden");
    }
    renderTabs();
    setButtons();
    saveState();
  }

  function onPass(t, ts) {
    var bs = blockState(t.block);
    if (t.kind === "check") {
      bs.checkPassed = true;
      bs.done = true;
      if (!bs.ladderStarted) ladder(t.block).level = 3;
      appendNotice("is-info", "This block is done. Move on to the next block, or practise here if you like.");
      renderBlockList();
    } else if (t.kind === "core") {
      var cores = tasksOf(t.block, ["core"]);
      if (cores.every(function (c) { return state.tasks[c.id] && state.tasks[c.id].everPassed; })) {
        bs.done = true;
        renderBlockList();
      }
    } else if (isPractice(t) && !ts.solutionViewed) {
      showRating();
    }
  }

  function showRating() {
    var ts = taskState(task().id);
    $("rating").classList.remove("is-hidden");
    document.querySelectorAll("#rating [data-rating]").forEach(function (b) {
      var on = b.dataset.rating === ts.rating;
      b.classList.toggle("is-link", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  // ── hint, solution, next ──────────────────────────────────────────────────

  function showHint() {
    var t = task();
    var ts = taskState(t.id);
    ts.hintShown = true;
    var box = $("hint-box");
    box.innerHTML = "<strong>Hint:</strong> " + (t.hints_html || []).map(function (h) { return fillHtml(h, variant ? variant.display : {}); }).join("");
    box.classList.remove("is-hidden");
    saveState();
  }

  function solutionCode() {
    var t = task();
    return fillCode(t.reference, variant ? variant.reprs : {});
  }

  function showSolution() {
    var t = task();
    var ts = taskState(t.id);
    ts.solutionViewed = true;
    $("solution-code").textContent = solutionCode();
    $("solution-notes").innerHTML = t.solution_html ? fillHtml(t.solution_html, variant ? variant.display : {}) : "";
    $("solution-box").classList.remove("is-hidden");
    $("rating").classList.add("is-hidden");
    saveState();
  }

  function applyStaircase(t, ts) {
    var lad = ladder(t.block);
    var step;
    if (ts.attempts === 0 && !ts.solutionViewed) {
      step = 0; // skipped without running
      lad.streak = 0;
    } else if (!ts.passed || ts.solutionViewed) {
      step = -1;
      lad.streak = 0;
    } else {
      var rating = ts.rating || "just_right";
      step = RATING_STEPS[rating];
      if (rating === "just_right") {
        lad.streak += 1;
        if (lad.streak >= 2) { step = 1; }
      } else {
        lad.streak = 0;
      }
    }
    var before = lad.level;
    lad.level = clamp(lad.level + step, 1, 5);
    if (lad.level > before) lad.streak = 0; // a promotion resets the streak
    return lad.level - before;
  }

  function next() {
    var t = task();
    if (!t) return;
    saveCode();
    if (isPractice(t)) {
      var ts = taskState(t.id);
      var change = applyStaircase(t, ts);
      var lad = ladder(t.block);
      var nt = templateForLevel(t.block, lad.level);
      lad.taskId = nt.id;
      if (change > 0) toast("Up to level " + lad.level + ".", "is-success");
      else if (change < 0) toast("Level " + lad.level + " next – a bit easier.", "is-info");
      // Each Next is a new variant: new seed, fresh attempts.
      delete state.tasks[nt.id];
      openTask(nt.id);
      return;
    }
    var ids = blockInfo(t.block).task_ids;
    var seq = tasksOf(t.block, ["check", "core"]).map(function (x) { return x.id; });
    var i = seq.indexOf(t.id);
    if (t.kind === "check") {
      var cores = tasksOf(t.block, ["core"]);
      if (taskState(t.id).passed) { goBlock(t.block + 1); return; }
      if (cores.length) { openTask(cores[0].id); return; }
    }
    if (i >= 0 && i + 1 < seq.length) { openTask(seq[i + 1]); return; }
    if (ids.some(function (id) { return isPractice(bank.tasks[id]); })) { openPractice(); return; }
    goBlock(t.block + 1);
  }

  function goBlock(n) {
    saveCode();
    while (n < BLOCK6 && !blockInfo(n)) n += 1; // tolerate a bank without every block
    if (n > BLOCK6) n = BLOCK6;
    state.current.block = n;
    if (n === BLOCK6) {
      state.current.taskId = null;
      variant = null;
      renderBlock();
      saveState();
      window.scrollTo(0, 0);
      return;
    }
    var cores = tasksOf(n, ["core"]);
    var first = cores.length ? cores[0] : tasksOf(n, ["check"])[0];
    window.scrollTo(0, 0);
    if (first) openTask(first.id); else { renderBlock(); saveState(); }
  }

  // ── editor ────────────────────────────────────────────────────────────────

  function initEditor() {
    if (typeof CodeMirror === "undefined") return; // falls back to the plain textarea
    cm = CodeMirror.fromTextArea($("editor"), {
      mode: "python",
      lineNumbers: true,
      indentUnit: 4,
      tabSize: 4,
      indentWithTabs: false,
      lineWrapping: true,
      spellcheck: false,
      viewportMargin: Infinity,
      extraKeys: {
        "Tab": function (c) {
          if (c.somethingSelected() && c.getSelection().indexOf("\n") >= 0) c.indentSelection("add");
          else c.replaceSelection("    ");
        },
        "Shift-Tab": function (c) { c.indentSelection("subtract"); },
        "Ctrl-Enter": function () { runCode(); },
        "Cmd-Enter": function () { runCode(); },
        "Esc": function (c) { c.getInputField().blur(); }, // keyboard users can leave the editor
      },
    });
    cm.getInputField().setAttribute("aria-label", "Your Python code");
    cm.on("blur", function () { saveCode(); saveState(); });
    cm.on("change", function (c, change) {
      if (change.origin !== "paste") return;
      if (change.text.join("\n").indexOf("\t") < 0) return;
      toast("The code you pasted contains tab characters (shown highlighted). Python may complain about them.", "is-warning", {
        label: "Convert tabs to spaces",
        onClick: function () {
          var cur = c.getCursor();
          c.setValue(c.getValue().replace(/\t/g, "    "));
          c.setCursor(cur);
        },
      });
    });
    applyEditorTheme();
    new MutationObserver(applyEditorTheme).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  }

  function applyEditorTheme() {
    if (!cm) return;
    cm.setOption("theme", document.documentElement.getAttribute("data-theme") === "dark" ? "dracula" : "default");
  }

  // ── Python status ─────────────────────────────────────────────────────────

  function setPyStatus(kind, html) {
    var el = $("py-status");
    el.className = "notification is-light py-2 px-3 " + kind;
    el.innerHTML = html;
  }

  py.onReady = function () {
    setPyStatus("is-success", '<span class="icon"><i class="fas fa-check" aria-hidden="true"></i></span> Python is ready.');
    $("restart-box").classList.add("is-hidden");
    if (task() && !variant) prepareVariant(false);
    setButtons();
  };

  py.onIdle = function () {
    if (waitingForIdle) {
      waitingForIdle = false;
      if (task() && !variant) prepareVariant(false);
    }
    setButtons();
  };

  py.onFail = function (why) {
    setPyStatus("is-danger", "<strong>Python is not running.</strong> " + escapeHtml(why));
    $("restart-msg").textContent = why + " Your code is kept.";
    $("restart-box").classList.remove("is-hidden");
    setButtons();
  };

  // ── wiring ────────────────────────────────────────────────────────────────

  function wire() {
    $("run-btn").addEventListener("click", runCode);
    $("new-btn").addEventListener("click", function () { saveCode(); clearFeedback(); variant = null; prepareVariant(true); });
    $("hint-btn").addEventListener("click", showHint);
    $("solution-btn").addEventListener("click", function () { showSolution(); setButtons(); });
    $("next-btn").addEventListener("click", next);
    $("try-check-btn").addEventListener("click", function () {
      var c = tasksOf(state.current.block, ["check"])[0];
      if (c) openTask(c.id);
    });
    $("to-core-btn").addEventListener("click", function () {
      var c = tasksOf(state.current.block, ["core"])[0];
      if (c) openTask(c.id);
    });
    $("copy-solution-btn").addEventListener("click", function () { setCode(solutionCode()); saveCode(); saveState(); });
    $("retry-btn").addEventListener("click", function () {
      $("restart-box").classList.add("is-hidden");
      setPyStatus("is-info", '<span class="icon"><i class="fas fa-spinner fa-spin" aria-hidden="true"></i></span> Starting Python again&hellip;');
      py.start();
    });
    document.querySelectorAll("#rating [data-rating]").forEach(function (b) {
      b.addEventListener("click", function () {
        var t = task();
        if (!t) return;
        taskState(t.id).rating = b.dataset.rating;
        showRating();
        saveState();
      });
    });
    $("start-again-btn").addEventListener("click", function () {
      var reset = function () {
        state = freshState(bank.bank_version);
        saveState();
        goBlock(1);
      };
      if (window.Swal) {
        window.Swal.fire({
          title: "Start again?",
          text: "This clears your progress and code in this browser.",
          icon: "warning",
          showCancelButton: true,
          confirmButtonText: "Yes, start again",
          cancelButtonText: "Cancel",
        }).then(function (r) { if (r.isConfirmed) reset(); });
      } else {
        reset();
      }
    });
    window.addEventListener("pagehide", function () { saveCode(); saveState(); });
  }

  function boot() {
    py.start(); // start loading Pyodide immediately; explanations are readable meanwhile
    initEditor();
    wire();
    fetch(app.dataset.bankUrl, { credentials: "same-origin" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (data) {
      bank = data;
      state = loadState(bank);
      state.bank_version = bank.bank_version;
      if (!storageOk) $("storage-banner").classList.remove("is-hidden");
      if (state.current.block === BLOCK6) { renderBlock(); return; }
      if (state.current.block !== BLOCK6 && !blockInfo(state.current.block)) state.current.taskId = null;
      if (state.current.taskId) openTask(state.current.taskId);
      else goBlock(state.current.block || 1);
    }).catch(function (err) {
      var el = $("bank-error");
      el.textContent = "The tasks could not be loaded (" + err.message + "). Check your connection and reload the page.";
      el.classList.remove("is-hidden");
    });
  }

  // Expose a little for tests and debugging (read-only use).
  window.__tutorial = {
    get state() { return state; },
    get bank() { return bank; },
    get ready() { return py.ready; },
    setCode: function (c) { setCode(c); },
    getCode: function () { return currentCode(); },
    variantReprs: function () { return variant ? variant.reprs : null; },
    openTask: function (id) { openTask(id); },
    run: runCode,
  };

  boot();
}());
