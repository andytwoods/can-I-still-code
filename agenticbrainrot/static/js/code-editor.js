/**
 * Code editor controller — manages CodeMirror, Pyodide worker,
 * timing, telemetry, and draft auto-save.
 *
 * Supports re-initialisation when HTMX swaps in new challenge content.
 */

(function () {
    "use strict";

    // -- State --
    var editor = null;
    var worker = null;
    var pyodideReady = false;
    var lintCallbacks = {};
    var lintIdCounter = 0;
    var timerInterval = null;
    var startTime = null;
    var elapsedSeconds = 0;
    var activeSeconds = 0;
    var lastKeystrokeTime = null;
    var draftInterval = null;
    var IDLE_THRESHOLD_MS = 120000; // 2 minutes
    var BLUR_THRESHOLD_MS = 30000; // 30 seconds

    // Telemetry
    var pasteCount = 0;
    var pasteTotalChars = 0;
    var keystrokeCount = 0;
    var tabBlurCount = 0;
    var lastBlurTime = null;
    var idleSeconds = 0;

    var THEMES = {
        "default": "default",
        "dark": "dracula",
        "light": "default",
        "dracula": "dracula",
        "solarized-light": "solarized light",
        "solarized-dark": "solarized dark"
    };

    // -- Reset telemetry for new challenge --
    function resetTelemetry() {
        elapsedSeconds = 0;
        activeSeconds = 0;
        idleSeconds = 0;
        pasteCount = 0;
        pasteTotalChars = 0;
        keystrokeCount = 0;
        tabBlurCount = 0;
        lastBlurTime = null;
        lastKeystrokeTime = null;
        startTime = null;
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = null;
        if (draftInterval) clearInterval(draftInterval);
        draftInterval = null;
    }

    // -- CodeMirror 5 setup --
    function initEditor() {
        var editorEl = document.getElementById("code-editor");
        if (!editorEl) return;

        // Destroy previous editor if it exists
        if (editor) {
            var wrapper = editor.getWrapperElement();
            if (wrapper && wrapper.parentNode) {
                wrapper.parentNode.removeChild(wrapper);
            }
            editor = null;
        }
        // Clear previous CodeMirror DOM
        editorEl.innerHTML = "";

        // Read skeleton code from JSON script tag
        var skeletonEl = document.getElementById("skeleton-code-data");
        var skeleton = skeletonEl ? JSON.parse(skeletonEl.textContent) : "";

        editor = CodeMirror(editorEl, {
            value: skeleton,
            mode: "python",
            lineNumbers: true,
            indentUnit: 4,
            tabSize: 4,
            lineWrapping: true,
            spellcheck: false,
            autofocus: true,
            gutters: ["CodeMirror-lint-markers"],
            lint: {
                getAnnotations: pythonLinter,
                async: true
            }
        });

        // Add telemetry listeners to CodeMirror
        editor.on("change", function (cm, change) {
            if (change.origin !== "setValue") {
                keystrokeCount++;
                lastKeystrokeTime = Date.now();
            }
        });

        editor.on("inputRead", function (cm, change) {
            if (change.origin === "paste") {
                pasteCount++;
                pasteTotalChars += change.text.join("\n").length;
            }
        });

        // Custom theme setter for CM5
        editor.setTheme = function (themeName) {
            var cmTheme = THEMES[themeName] || "default";

            // Special handling for site-syncing default
            if (themeName === "default") {
                var siteTheme = document.documentElement.getAttribute("data-theme") || "light";
                cmTheme = siteTheme === "dark" ? "dracula" : "default";
            }

            editor.setOption("theme", cmTheme);
        };

        // Initialize theme from select or localStorage
        var themeSelect = document.getElementById("theme-select");
        if (themeSelect) {
            var savedTheme = localStorage.getItem("editor-theme") || "default";
            themeSelect.value = savedTheme;
            editor.setTheme(savedTheme);

            themeSelect.addEventListener("change", function () {
                var theme = themeSelect.value;
                editor.setTheme(theme);
                localStorage.setItem("editor-theme", theme);
            });
        }

        // Restore draft if available
        var attemptUuid = document.getElementById("attempt-uuid");
        if (attemptUuid) {
            var draft = localStorage.getItem("draft_" + attemptUuid.value);
            if (draft) {
                editor.setValue(draft);
            }
        }

        // Auto-save draft every 30 seconds
        draftInterval = setInterval(function () {
            if (attemptUuid && editor) {
                localStorage.setItem("draft_" + attemptUuid.value, editor.getValue());
            }
        }, 30000);

        // Enable buttons if Pyodide is already ready
        if (pyodideReady) {
            var runBtn = document.getElementById("run-btn");
            var submitBtn = document.getElementById("submit-btn");
            if (runBtn) runBtn.disabled = false;
            if (submitBtn) submitBtn.disabled = false;
            startTimer();
        }
    }

    // -- Python Linter using Pyodide Worker --
    function pythonLinter(text, updateLinting, options, cm) {
        if (!pyodideReady || !worker) {
            updateLinting(cm, []);
            return;
        }

        var id = ++lintIdCounter;
        lintCallbacks[id] = function (results) {
            var annotations = results.map(function (r) {
                return {
                    from: CodeMirror.Pos(r.line - 1, r.col - 1),
                    to: CodeMirror.Pos(r.line - 1, r.col),
                    message: r.message,
                    severity: r.severity
                };
            });
            updateLinting(cm, annotations);
        };

        worker.postMessage({
            type: "lint",
            code: text,
            id: id
        });
    }

    // -- Toast notifications --
    function showToast(message, type, duration) {
        var toast = document.createElement("div");
        toast.className = "notification " + type;
        toast.style.cssText =
            "position:fixed;top:1rem;right:1rem;z-index:9999;min-width:280px;" +
            "max-width:400px;opacity:0;transition:opacity 0.3s ease;box-shadow:0 4px 12px rgba(0,0,0,0.15);";
        toast.innerHTML = message;

        document.body.appendChild(toast);
        // Trigger reflow then fade in
        toast.offsetHeight; // eslint-disable-line no-unused-expressions
        toast.style.opacity = "1";

        if (duration > 0) {
            setTimeout(function () {
                toast.style.opacity = "0";
                setTimeout(function () { toast.remove(); }, 300);
            }, duration);
        }

        return toast;
    }

    // -- Pyodide Worker --
    function initPyodide() {
        var loadingToast = showToast(
            '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span> Loading Python environment…',
            "is-info is-light", 0
        );

        var loadStart = Date.now();
        worker = new Worker("/static/js/pyodide-worker.js");

        worker.onmessage = function (e) {
            var msg = e.data;

            switch (msg.type) {
                case "ready":
                    pyodideReady = true;

                    // Replace loading toast with success
                    loadingToast.style.opacity = "0";
                    setTimeout(function () { loadingToast.remove(); }, 300);
                    showToast(
                        '<span class="icon"><i class="fas fa-check"></i></span> Python environment ready.',
                        "is-success is-light", 2000
                    );

                    // Report load time
                    var loadMs = Date.now() - loadStart;
                    var loadMsInput = document.getElementById("pyodide-load-ms");
                    if (loadMsInput) loadMsInput.value = loadMs;

                    // Mark editor ready
                    var editorReadyInput = document.getElementById("editor-ready");
                    if (editorReadyInput) editorReadyInput.value = "true";

                    // Start timer and enable buttons
                    startTimer();
                    enableButtons();
                    break;

                case "init_error":
                    loadingToast.style.opacity = "0";
                    setTimeout(function () { loadingToast.remove(); }, 300);
                    showToast(
                        "<strong>The code execution environment couldn't load.</strong> " +
                        "Please check your internet connection and reload the page. " +
                        '<button class="button is-small is-warning mt-2" onclick="location.reload()">Reload</button>',
                        "is-danger", 0
                    );
                    break;

                case "stdout":
                    appendOutput(msg.text, "stdout");
                    break;

                case "stderr":
                    appendOutput(msg.text, "stderr");
                    break;

                case "lint_result":
                    if (lintCallbacks[msg.id]) {
                        lintCallbacks[msg.id](msg.results);
                        delete lintCallbacks[msg.id];
                    }
                    break;

                case "result":
                    clearRunTimeout();
                    displayTestResults(msg.results);
                    enableButtons();
                    break;

                case "error":
                    clearRunTimeout();
                    appendOutput("Error: " + msg.error, "stderr");
                    enableButtons();
                    break;
            }
        };

        worker.postMessage({ type: "init" });
    }

    function enableButtons() {
        var runBtn = document.getElementById("run-btn");
        var submitBtn = document.getElementById("submit-btn");
        if (runBtn) runBtn.disabled = false;
        if (submitBtn) submitBtn.disabled = false;
    }

    // -- Timer --
    function startTimer() {
        if (timerInterval) return; // already running
        startTime = Date.now();
        lastKeystrokeTime = Date.now();
        timerInterval = setInterval(updateTimer, 1000);
    }

    function updateTimer() {
        if (!startTime) return;
        elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
        var mins = Math.floor(elapsedSeconds / 60);
        var secs = elapsedSeconds % 60;
        var timerEl = document.getElementById("timer-display");
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
        timerInterval = null;
    }

    // -- Output --
    function appendOutput(text, stream) {
        var outputEl = document.getElementById("output");
        if (!outputEl) return;
        var line = document.createElement("pre");
        line.className = stream === "stderr" ? "has-text-danger" : "";
        line.textContent = text;
        outputEl.appendChild(line);
        outputEl.scrollTop = outputEl.scrollHeight;
    }

    function clearOutput() {
        var outputEl = document.getElementById("output");
        var testResultsEl = document.getElementById("test-results");
        if (outputEl) outputEl.innerHTML = "";
        if (testResultsEl) testResultsEl.innerHTML = "";
    }

    // -- Test Results --
    function displayTestResults(results) {
        var testResultsEl = document.getElementById("test-results");
        if (!testResultsEl) return;
        testResultsEl.innerHTML = "";

        var passed = 0;
        var total = results.length;

        results.forEach(function (r) {
            var div = document.createElement("div");
            div.className = "notification " + (r.passed ? "is-success" : "is-danger") + " is-light py-2 px-3 mb-2";

            var content = (r.passed ? "PASS" : "FAIL") + ": " + r.description;
            if (r.input && r.input.length > 0) {
                content += "\n  Input: " + r.input.map(function (a) { return JSON.stringify(a); }).join(", ");
            }
            if (!r.passed && r.error) {
                content += "\n  Error: " + r.error;
            } else if (!r.passed) {
                content += "\n  Expected: " + JSON.stringify(r.expected) + "\n  Got:      " + JSON.stringify(r.actual);
            }
            div.style.whiteSpace = "pre-wrap";
            div.style.fontFamily = "monospace";
            div.style.fontSize = "0.85em";
            div.textContent = content;
            testResultsEl.appendChild(div);

            if (r.passed) passed++;
        });

        // Summary
        var summary = document.createElement("div");
        summary.className = "notification " + (passed === total ? "is-success" : "is-warning") + " mt-3";
        summary.innerHTML = "<strong>" + passed + " / " + total + " tests passed</strong>";
        testResultsEl.appendChild(summary);

        // Store results for submission
        var testsPassed = document.getElementById("tests-passed");
        var testsTotal = document.getElementById("tests-total");
        if (testsPassed) testsPassed.value = passed;
        if (testsTotal) testsTotal.value = total;
    }

    // -- Tab blur tracking --
    document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
            lastBlurTime = Date.now();
        } else if (lastBlurTime) {
            var blurDuration = Date.now() - lastBlurTime;
            if (blurDuration > BLUR_THRESHOLD_MS) {
                tabBlurCount++;
                idleSeconds += Math.floor(blurDuration / 1000);
            }
            lastBlurTime = null;
        }
    });

    // -- Run/Submit handlers --
    var runTimeout = null;
    var RUN_TIMEOUT_MS = 30000; // 30 seconds

    function runCode() {
        if (!editor || !worker || !pyodideReady) return;
        clearOutput();
        var runBtn = document.getElementById("run-btn");
        var submitBtn = document.getElementById("submit-btn");
        if (runBtn) runBtn.disabled = true;
        if (submitBtn) submitBtn.disabled = true;

        var testCasesEl = document.getElementById("test-cases-data");
        var testCases = testCasesEl ? JSON.parse(testCasesEl.textContent) : [];

        // Set timeout — kill worker and restart if code runs too long
        if (runTimeout) clearTimeout(runTimeout);
        runTimeout = setTimeout(function () {
            worker.terminate();
            appendOutput("Timeout: your code took longer than 30 seconds. Please optimise and try again.", "stderr");
            enableButtons();
            // Restart worker
            pyodideReady = false;
            initPyodide();
        }, RUN_TIMEOUT_MS);

        worker.postMessage({
            type: "run",
            code: editor.getValue(),
            testCases: testCases,
        });
    }

    function clearRunTimeout() {
        if (runTimeout) {
            clearTimeout(runTimeout);
            runTimeout = null;
        }
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
        var attemptUuid = document.getElementById("attempt-uuid");
        if (attemptUuid) {
            localStorage.removeItem("draft_" + attemptUuid.value);
        }

        stopTimer();
    }

    function setInput(id, value) {
        var el = document.getElementById(id);
        if (el) el.value = value;
    }

    // -- Bind buttons (called on init and after HTMX swaps) --
    function bindButtons() {
        var runBtn = document.getElementById("run-btn");
        var submitBtn = document.getElementById("submit-btn");
        var timerEl = document.getElementById("timer-display");

        if (runBtn) {
            runBtn.disabled = !pyodideReady;
            runBtn.onclick = runCode;
        }
        if (submitBtn) {
            submitBtn.disabled = !pyodideReady;
            submitBtn.onclick = function () {
                runCode();
                // Wait for results then submit
                var checkReady = setInterval(function () {
                    var testsPassed = document.getElementById("tests-passed");
                    if (testsPassed && testsPassed.value !== "") {
                        clearInterval(checkReady);
                        prepareSubmission();
                    }
                }, 200);
            };
        }

        // Timer toggle
        if (timerEl) {
            timerEl.style.cursor = "pointer";
            timerEl.title = "Click to toggle timer visibility";
            timerEl.onclick = function () {
                timerEl.style.visibility = timerEl.style.visibility === "hidden" ? "visible" : "hidden";
            };
        }
    }

    // -- Initialise a new challenge (called on page load and HTMX swap) --
    function initChallenge() {
        var editorEl = document.getElementById("code-editor");
        if (!editorEl) return; // Not a challenge page

        resetTelemetry();
        initEditor();
        bindButtons();
    }

    // -- Init --
    function init() {
        initChallenge();
        initPyodide();

        // Beforeunload warning
        window.addEventListener("beforeunload", function (e) {
            if (editor && editor.getValue().trim()) {
                e.preventDefault();
            }
        });

        // Listen for HTMX submission
        document.addEventListener("htmx:beforeRequest", function (e) {
            if (e.detail.elt && e.detail.elt.id === "challenge-form") {
                prepareSubmission();
            }
        });

        // Re-initialise editor when HTMX swaps in new challenge content
        document.addEventListener("htmx:afterSwap", function (e) {
            // Only reinit if the swap target contains a code editor
            if (e.detail.target && e.detail.target.querySelector("#code-editor")) {
                initChallenge();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
