/**
 * Pyodide Web Worker  -  executes Python code in a sandboxed environment.
 *
 * Messages IN:  { type: "init" }            -  load Pyodide
 *               { type: "run", code, testCases }   -  execute code + tests
 *
 * Messages OUT: { type: "ready" }            -  Pyodide loaded
 *               { type: "init_error", error }  -  Pyodide failed to load
 *               { type: "stdout", text }     -  stdout line
 *               { type: "stderr", text }     -  stderr line
 *               { type: "result", results }  -  test results array
 *               { type: "error", error }     -  runtime error
 */

/* global importScripts, loadPyodide */

let pyodide = null;

self.onmessage = async function (e) {
    const msg = e.data;

    if (msg.type === "init") {
        try {
            importScripts("https://cdn.jsdelivr.net/pyodide/v0.27.4/full/pyodide.js");
            pyodide = await loadPyodide({
                stdout: (text) => self.postMessage({ type: "stdout", text }),
                stderr: (text) => self.postMessage({ type: "stderr", text }),
            });
            // Setup linting environment
            pyodide.runPython(`
import sys
import ast

def check_syntax(code):
    try:
        compile(code, "<string>", "exec")
        return []
    except SyntaxError as e:
        return [{
            "line": e.lineno or 1,
            "col": e.offset or 1,
            "message": e.msg,
            "severity": "error"
        }]
    except Exception as e:
        return [{
            "line": 1,
            "col": 1,
            "message": str(e),
            "severity": "error"
        }]
`);
            self.postMessage({ type: "ready" });
        } catch (err) {
            self.postMessage({ type: "init_error", error: err.message });
        }
    }

    if (msg.type === "lint") {
        if (!pyodide) return;
        try {
            const pyCode = `import json; json.dumps(check_syntax(${JSON.stringify(msg.code)}))`;
            const result = pyodide.runPython(pyCode);
            self.postMessage({ type: "lint_result", results: JSON.parse(result), id: msg.id });
        } catch (err) {
            // If check_syntax itself fails
            self.postMessage({ type: "lint_result", results: [{ line: 1, col: 1, message: err.message, severity: "error" }], id: msg.id });
        }
    }

    if (msg.type === "run") {
        if (!pyodide) {
            self.postMessage({ type: "error", error: "Pyodide not loaded" });
            return;
        }

        try {
            // Run the user's code to define functions/classes
            pyodide.runPython(msg.code);

            // Run test cases
            const results = [];
            for (const tc of msg.testCases) {
                try {
                    let result;
                    if (tc.input === "operations" || tc.input === "tree_ops") {
                        // Class-based tests  -  run operations sequence
                        result = runOperationTests(pyodide, tc);
                    } else {
                        // Standard function call tests
                        const args = tc.input || [];
                        const argsRepr = args.map(a => JSON.stringify(a)).join(", ");

                        // Detect the function name from the code
                        const funcMatch = msg.code.match(/^(?:def|class)\s+(\w+)/m);
                        const funcName = funcMatch ? funcMatch[1] : "solution";

                        const pyCode = `
import json
_args = json.loads('${JSON.stringify(args)}')
_result = ${funcName}(*_args)
json.dumps(_result) if not isinstance(_result, (int, float, bool, type(None))) else repr(_result)
`;
                        const rawResult = pyodide.runPython(pyCode);
                        result = parseResult(rawResult);
                    }

                    let passed;
                    if (tc.expected_in) {
                        // Multiple valid answers
                        passed = tc.expected_in.some(exp => deepEqual(result, exp));
                    } else if (tc.expected_sorted) {
                        // Sort inner lists for comparison
                        const sortedResult = Array.isArray(result)
                            ? result.map(r => Array.isArray(r) ? r.sort() : r).sort()
                            : result;
                        const sortedExpected = tc.expected_sorted.map(r => Array.isArray(r) ? r.sort() : r).sort();
                        passed = deepEqual(sortedResult, sortedExpected);
                    } else {
                        passed = deepEqual(result, tc.expected);
                    }

                    results.push({
                        description: tc.description,
                        passed,
                        actual: result,
                        expected: tc.expected || tc.expected_in || tc.expected_sorted,
                        input: tc.input || [],
                    });
                } catch (testErr) {
                    results.push({
                        description: tc.description,
                        passed: false,
                        error: testErr.message,
                        input: tc.input || [],
                    });
                }
            }

            self.postMessage({ type: "result", results });
        } catch (err) {
            self.postMessage({ type: "error", error: err.message });
        }
    }
};


function parseResult(raw) {
    if (raw === "True") return true;
    if (raw === "False") return false;
    if (raw === "None") return null;
    try {
        return JSON.parse(raw);
    } catch {
        // Try as number
        const num = Number(raw);
        if (!isNaN(num)) return num;
        return raw;
    }
}


function deepEqual(a, b) {
    if (a === b) return true;
    if (typeof a !== typeof b) return false;
    if (typeof a === "number" && typeof b === "number") {
        return Math.abs(a - b) < 1e-9;
    }
    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) return false;
        return a.every((val, i) => deepEqual(val, b[i]));
    }
    if (typeof a === "object" && a !== null && b !== null) {
        const keysA = Object.keys(a).sort();
        const keysB = Object.keys(b).sort();
        if (!deepEqual(keysA, keysB)) return false;
        return keysA.every(k => deepEqual(a[k], b[k]));
    }
    return false;
}


function runOperationTests(pyodide, tc) {
    // Execute class-based operation sequences
    const ops = tc.ops;
    const results = [];

    for (const op of ops) {
        if (op[0] === "init") {
            const args = op.slice(1).map(a => JSON.stringify(a)).join(", ");
            pyodide.runPython(`_instance = ${detectClassName(pyodide)}(${args})`);
            results.push(null);
        } else {
            const methodName = op[0];
            const args = op.slice(1).map(a => JSON.stringify(a)).join(", ");
            const raw = pyodide.runPython(
                `repr(_instance.${methodName}(${args}))`
            );
            results.push(parseResult(raw));
        }
    }
    return deepEqual(results, tc.expected);
}


function detectClassName(pyodide) {
    // Try common class names
    for (const name of ["LRUCache", "Trie", "TreeNode"]) {
        try {
            pyodide.runPython(`${name}`);
            return name;
        } catch { /* not defined */ }
    }
    return "Solution";
}
