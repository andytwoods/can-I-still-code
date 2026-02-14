/**
 * Code editor controller — manages CodeMirror, Pyodide worker,
 * timing, telemetry, and draft auto-save.
 */

(function () {
    "use strict";

    // -- State --
    let editor = null;
    let worker = null;
    let pyodideReady = false;
    let timerInterval = null;
    let startTime = null;
    let elapsedSeconds = 0;
    let activeSeconds = 0;
    let lastKeystrokeTime = null;
    const IDLE_THRESHOLD_MS = 120000; // 2 minutes
    const BLUR_THRESHOLD_MS = 30000; // 30 seconds

    // Telemetry
    let pasteCount = 0;
    let pasteTotalChars = 0;
    let keystrokeCount = 0;
    let tabBlurCount = 0;
    let lastBlurTime = null;
    let idleSeconds = 0;

    // -- Selectors --
    const editorEl = document.getElementById("code-editor");
    const outputEl = document.getElementById("output");
    const runBtn = document.getElementById("run-btn");
    const submitBtn = document.getElementById("submit-btn");
    const skipBtn = document.getElementById("skip-btn");
    const timerEl = document.getElementById("timer-display");
    const pyodideStatus = document.getElementById("pyodide-status");
    const testResultsEl = document.getElementById("test-results");
    const progressEl = document.getElementById("progress-indicator");

    // -- CodeMirror 6 setup (loaded via CDN ESM) --
    // We use a textarea fallback for simplicity; CodeMirror 6 requires
    // ES modules which need import maps or bundlers. The textarea provides
    // a functional editor that works with Pyodide.
    function initEditor() {
        if (!editorEl) return;

        const textarea = document.createElement("textarea");
        textarea.id = "code-textarea";
        textarea.className = "textarea is-family-monospace";
        textarea.rows = 15;
        textarea.spellcheck = false;
        textarea.value = editorEl.dataset.skeleton || "";
        editorEl.appendChild(textarea);

        editor = {
            getValue: () => textarea.value,
            setValue: (v) => { textarea.value = v; },
        };

        // Telemetry listeners
        textarea.addEventListener("keydown", () => {
            keystrokeCount++;
            lastKeystrokeTime = Date.now();
        });

        textarea.addEventListener("paste", (e) => {
            pasteCount++;
            const pasted = (e.clipboardData || window.clipboardData).getData("text");
            pasteTotalChars += pasted.length;
        });

        // Restore draft if available
        const attemptUuid = document.getElementById("attempt-uuid");
        if (attemptUuid) {
            const draft = localStorage.getItem("draft_" + attemptUuid.value);
            if (draft) {
                textarea.value = draft;
            }
        }

        // Auto-save draft every 30 seconds
        setInterval(() => {
            if (attemptUuid && editor) {
                localStorage.setItem("draft_" + attemptUuid.value, editor.getValue());
            }
        }, 30000);
    }

    // -- Pyodide Worker --
    function initPyodide() {
        if (!pyodideStatus) return;

        pyodideStatus.textContent = "Loading Python environment...";
        pyodideStatus.className = "notification is-info is-light";

        const loadStart = Date.now();
        worker = new Worker("/static/js/pyodide-worker.js");

        worker.onmessage = function (e) {
            const msg = e.data;

            switch (msg.type) {
                case "ready":
                    pyodideReady = true;
                    pyodideStatus.textContent = "Python environment ready.";
                    pyodideStatus.className = "notification is-success is-light";
                    setTimeout(() => { pyodideStatus.style.display = "none"; }, 2000);

                    // Report load time
                    const loadMs = Date.now() - loadStart;
                    const loadMsInput = document.getElementById("pyodide-load-ms");
                    if (loadMsInput) loadMsInput.value = loadMs;

                    // Mark editor ready
                    const editorReadyInput = document.getElementById("editor-ready");
                    if (editorReadyInput) editorReadyInput.value = "true";

                    // Start timer now
                    startTimer();
                    if (runBtn) runBtn.disabled = false;
                    if (submitBtn) submitBtn.disabled = false;
                    break;

                case "init_error":
                    pyodideStatus.innerHTML =
                        "<strong>The code execution environment couldn't load.</strong> " +
                        "Please check your internet connection and reload the page. " +
                        '<button class="button is-small is-warning mt-2" onclick="location.reload()">Reload</button>';
                    pyodideStatus.className = "notification is-danger";
                    break;

                case "stdout":
                    appendOutput(msg.text, "stdout");
                    break;

                case "stderr":
                    appendOutput(msg.text, "stderr");
                    break;

                case "result":
                    displayTestResults(msg.results);
                    if (runBtn) runBtn.disabled = false;
                    if (submitBtn) submitBtn.disabled = false;
                    break;

                case "error":
                    appendOutput("Error: " + msg.error, "stderr");
                    if (runBtn) runBtn.disabled = false;
                    if (submitBtn) submitBtn.disabled = false;
                    break;
            }
        };

        worker.postMessage({ type: "init" });
    }

    // -- Timer --
    function startTimer() {
        startTime = Date.now();
        lastKeystrokeTime = Date.now();
        timerInterval = setInterval(updateTimer, 1000);
    }

    function updateTimer() {
        if (!startTime) return;
        elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
        const mins = Math.floor(elapsedSeconds / 60);
        const secs = elapsedSeconds % 60;
        if (timerEl) {
            timerEl.textContent =
                String(mins).padStart(2, "0") + ":" + String(secs).padStart(2, "0");
        }

        // Track idle time
        if (lastKeystrokeTime && (Date.now() - lastKeystrokeTime) > IDLE_THRESHOLD_MS) {
            idleSeconds++;
        } else {
            activeSeconds++;
        }
    }

    function stopTimer() {
        if (timerInterval) clearInterval(timerInterval);
    }

    // -- Output --
    function appendOutput(text, stream) {
        if (!outputEl) return;
        const line = document.createElement("pre");
        line.className = stream === "stderr" ? "has-text-danger" : "";
        line.textContent = text;
        outputEl.appendChild(line);
        outputEl.scrollTop = outputEl.scrollHeight;
    }

    function clearOutput() {
        if (outputEl) outputEl.innerHTML = "";
        if (testResultsEl) testResultsEl.innerHTML = "";
    }

    // -- Test Results --
    function displayTestResults(results) {
        if (!testResultsEl) return;
        testResultsEl.innerHTML = "";

        let passed = 0;
        let total = results.length;

        results.forEach((r) => {
            const div = document.createElement("div");
            div.className = "notification " + (r.passed ? "is-success" : "is-danger") + " is-light py-2 px-3 mb-2";

            let content = (r.passed ? "PASS" : "FAIL") + ": " + r.description;
            if (!r.passed && r.error) {
                content += " — " + r.error;
            } else if (!r.passed) {
                content += " — Expected: " + JSON.stringify(r.expected) + ", Got: " + JSON.stringify(r.actual);
            }
            div.textContent = content;
            testResultsEl.appendChild(div);

            if (r.passed) passed++;
        });

        // Summary
        const summary = document.createElement("div");
        summary.className = "notification " + (passed === total ? "is-success" : "is-warning") + " mt-3";
        summary.innerHTML = "<strong>" + passed + " / " + total + " tests passed</strong>";
        testResultsEl.appendChild(summary);

        // Store results for submission
        const testsPassed = document.getElementById("tests-passed");
        const testsTotal = document.getElementById("tests-total");
        if (testsPassed) testsPassed.value = passed;
        if (testsTotal) testsTotal.value = total;
    }

    // -- Tab blur tracking --
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
            lastBlurTime = Date.now();
        } else if (lastBlurTime) {
            const blurDuration = Date.now() - lastBlurTime;
            if (blurDuration > BLUR_THRESHOLD_MS) {
                tabBlurCount++;
                idleSeconds += Math.floor(blurDuration / 1000);
            }
            lastBlurTime = null;
        }
    });

    // -- Run/Submit handlers --
    function runCode() {
        if (!editor || !worker || !pyodideReady) return;
        clearOutput();
        if (runBtn) runBtn.disabled = true;
        if (submitBtn) submitBtn.disabled = true; // Also disable submit while running

        const testCasesEl = document.getElementById("test-cases-data");
        const testCases = testCasesEl ? JSON.parse(testCasesEl.textContent) : [];

        worker.postMessage({
            type: "run",
            code: editor.getValue(),
            testCases: testCases,
        });
    }

    function prepareSubmission() {
        // Fill telemetry hidden inputs before HTMX submits
        setInput("submitted-code", editor ? editor.getValue() : "");
        setInput("time-taken", elapsedSeconds.toString());
        setInput("active-time", activeSeconds.toString());
        setInput("idle-time", idleSeconds.toString());
        setInput("paste-count-input", pasteCount.toString());
        setInput("paste-total-chars-input", pasteTotalChars.toString());
        setInput("keystroke-count-input", keystrokeCount.toString());
        setInput("tab-blur-count-input", tabBlurCount.toString());

        // Clear draft
        const attemptUuid = document.getElementById("attempt-uuid");
        if (attemptUuid) {
            localStorage.removeItem("draft_" + attemptUuid.value);
        }

        stopTimer();
    }

    function setInput(id, value) {
        const el = document.getElementById(id);
        if (el) el.value = value;
    }

    // -- Init --
    function init() {
        initEditor();
        initPyodide();

        if (runBtn) {
            runBtn.disabled = true;
            runBtn.addEventListener("click", runCode);
        }
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.addEventListener("click", () => {
                runCode();
                // Wait for results then submit
                const checkReady = setInterval(() => {
                    const testsPassed = document.getElementById("tests-passed");
                    if (testsPassed && testsPassed.value !== "") {
                        clearInterval(checkReady);
                        prepareSubmission();
                    }
                }, 200);
            });
        }

        // Timer toggle
        if (timerEl) {
            timerEl.style.cursor = "pointer";
            timerEl.title = "Click to toggle timer visibility";
            timerEl.addEventListener("click", () => {
                timerEl.style.visibility = timerEl.style.visibility === "hidden" ? "visible" : "hidden";
            });
        }

        // Beforeunload warning
        window.addEventListener("beforeunload", (e) => {
            if (editor && editor.getValue().trim()) {
                e.preventDefault();
            }
        });

        // Listen for HTMX submission
        document.addEventListener("htmx:beforeRequest", (e) => {
            if (e.detail.elt && e.detail.elt.id === "challenge-form") {
                prepareSubmission();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
