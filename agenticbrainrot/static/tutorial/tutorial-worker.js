/**
 * Pyodide Web Worker for the browser Python tutorial (/tutorial/).
 *
 * Separate from js/pyodide-worker.js (the study's worker), which must not change.
 * All task logic lives in tutorial_runner.py, which the page passes in by URL and
 * which the bank builder also runs under CPython. Data crosses the JS/Python
 * boundary as JSON strings only, so no PyProxy objects escape.
 *
 * Every reply carries the workerGen given at init and the request's opId; the
 * page ignores replies from a stale worker or operation.
 *
 * IN:  { type: "init", workerGen, runnerUrl }
 *      { type: "load_packages", opId, packages }
 *      { type: "generate", opId, taskId, generatorSrc, seed }
 *      { type: "run", opId, code, referenceSrc, params, injectParams, checks, seed, allowPlot }
 * OUT: { type: "ready" } | { type: "init_error", error }
 *      { type: "packages_loaded", opId } | { type: "packages_error", opId, error }
 *      { type: "generated", opId, taskId, params, display, reprs } | { type: "generate_error", opId, error }
 *      { type: "result", opId, learner, checks, passed } | { type: "run_error", opId, error }
 */

/* global importScripts, loadPyodide */

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.4/full/pyodide.js";

let pyodide = null;
let workerGen = 0;
let generateFn = null;
let runFn = null;

function reply(msg) {
    msg.workerGen = workerGen;
    self.postMessage(msg);
}

async function init(msg) {
    workerGen = msg.workerGen;
    try {
        importScripts(PYODIDE_URL);
        pyodide = await loadPyodide({
            // Learner output is captured inside Python; drop anything that leaks past it.
            stdout: () => {},
            stderr: () => {},
        });
        const resp = await fetch(msg.runnerUrl);
        if (!resp.ok) throw new Error("Could not fetch the task runner (" + resp.status + ")");
        pyodide.FS.writeFile("/home/pyodide/tutorial_runner.py", await resp.text());
        pyodide.runPython("import sys\nif '/home/pyodide' not in sys.path: sys.path.insert(0, '/home/pyodide')\nimport tutorial_runner");
        // These two proxies live as long as the worker; every call returns a plain JS string.
        generateFn = pyodide.globals.get("tutorial_runner").generate_json;
        runFn = pyodide.globals.get("tutorial_runner").run_task_json;
        reply({ type: "ready" });
    } catch (err) {
        reply({ type: "init_error", error: String(err && err.message || err) });
    }
}

async function loadPackages(msg) {
    try {
        await pyodide.loadPackage(msg.packages);
        reply({ type: "packages_loaded", opId: msg.opId });
    } catch (err) {
        reply({ type: "packages_error", opId: msg.opId, error: String(err && err.message || err) });
    }
}

function generate(msg) {
    try {
        const out = JSON.parse(generateFn(JSON.stringify({ generatorSrc: msg.generatorSrc, seed: msg.seed })));
        if (!out.ok) throw new Error(out.error);
        reply({ type: "generated", opId: msg.opId, taskId: msg.taskId, params: out.params, display: out.display, reprs: out.reprs });
    } catch (err) {
        reply({ type: "generate_error", opId: msg.opId, error: String(err && err.message || err) });
    }
}

function run(msg) {
    try {
        const out = JSON.parse(runFn(JSON.stringify({
            code: msg.code,
            referenceSrc: msg.referenceSrc,
            params: msg.params,
            injectParams: msg.injectParams,
            checks: msg.checks,
            seed: msg.seed,
            allowPlot: msg.allowPlot,
        })));
        reply({ type: "result", opId: msg.opId, learner: out.learner, checks: out.checks, passed: out.passed });
    } catch (err) {
        reply({ type: "run_error", opId: msg.opId, error: String(err && err.message || err) });
    }
}

self.onmessage = function (e) {
    const msg = e.data;
    if (msg.type === "init") return init(msg);
    if (!pyodide || !runFn) {
        reply({ type: "run_error", opId: msg.opId, error: "Python is not ready yet" });
        return;
    }
    if (msg.type === "load_packages") return loadPackages(msg);
    if (msg.type === "generate") return generate(msg);
    if (msg.type === "run") return run(msg);
};
