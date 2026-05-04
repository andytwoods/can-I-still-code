/**
 * Pyodide Web Worker  -  executes Python code in a sandboxed environment.
 *
 * Messages IN:  { type: "init" }            -  load Pyodide
 *               { type: "run", code, testCases, referenceSolution }  -  execute code + tests
 *
 * Messages OUT: { type: "ready" }                                    -  Pyodide loaded
 *               { type: "init_error", error }                        -  Pyodide failed to load
 *               { type: "stdout", text }                             -  stdout line
 *               { type: "stderr", text }                             -  stderr line
 *               { type: "result", results, complexity, efficiencyRatio }  -  test results + metrics
 *               { type: "error", error }                             -  runtime error
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
            // Setup linting and complexity analysis
            pyodide.runPython(`
import sys
import ast
import math
import json
import time

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

def analyze_complexity(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    # Lines of code (non-blank)
    loc = sum(1 for line in code.split("\\n") if line.strip())

    # Cyclomatic complexity (McCabe): count decision points + 1
    cyclomatic = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Assert)):
            cyclomatic += 1
        elif isinstance(node, ast.BoolOp):
            cyclomatic += len(node.values) - 1

    # Maximum nesting depth
    def _max_depth(node, depth):
        nesting = (ast.If, ast.For, ast.While, ast.With, ast.Try,
                   ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        best = depth
        for child in ast.iter_child_nodes(node):
            child_depth = _max_depth(child, depth + 1 if isinstance(child, nesting) else depth)
            if child_depth > best:
                best = child_depth
        return best
    max_nesting = _max_depth(tree, 0)

    # Halstead metrics
    operators = {}
    operands = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp):
            k = type(node.op).__name__
            operators[k] = operators.get(k, 0) + 1
        elif isinstance(node, ast.UnaryOp):
            k = type(node.op).__name__
            operators[k] = operators.get(k, 0) + 1
        elif isinstance(node, ast.BoolOp):
            k = type(node.op).__name__
            operators[k] = operators.get(k, 0) + len(node.values) - 1
        elif isinstance(node, ast.Compare):
            for op in node.ops:
                k = type(op).__name__
                operators[k] = operators.get(k, 0) + 1
        elif isinstance(node, ast.Name):
            operands[node.id] = operands.get(node.id, 0) + 1
        elif isinstance(node, ast.Constant):
            k = repr(node.value)
            operands[k] = operands.get(k, 0) + 1

    n1 = len(operators)
    n2 = len(operands)
    N1 = sum(operators.values())
    N2 = sum(operands.values())
    vocabulary = n1 + n2
    length = N1 + N2
    volume = length * math.log2(vocabulary) if vocabulary > 1 else 0
    difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
    effort = round(difficulty * volume, 2)

    # Pythonic construct counts
    list_comps = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ListComp))
    dict_comps = sum(1 for n in ast.walk(tree) if isinstance(n, ast.DictComp))
    set_comps  = sum(1 for n in ast.walk(tree) if isinstance(n, ast.SetComp))
    generators = sum(1 for n in ast.walk(tree) if isinstance(n, ast.GeneratorExp))
    ternary    = sum(1 for n in ast.walk(tree) if isinstance(n, ast.IfExp))

    # Unique identifiers and function definitions
    unique_names = len({n.id for n in ast.walk(tree) if isinstance(n, ast.Name)})
    func_count   = sum(1 for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))

    return {
        "loc": loc,
        "cyclomatic_complexity": cyclomatic,
        "max_nesting_depth": max_nesting,
        "halstead_vocabulary": vocabulary,
        "halstead_volume": round(volume, 2),
        "halstead_difficulty": round(difficulty, 2),
        "halstead_effort": effort,
        "list_comprehensions": list_comps,
        "dict_comprehensions": dict_comps,
        "set_comprehensions": set_comps,
        "generators": generators,
        "ternary_expressions": ternary,
        "unique_identifiers": unique_names,
        "function_count": func_count,
    }

def measure_median_us(fn, inputs_list, n=200, timeout_s=2.0):
    """Run fn(*args) n times cycling through inputs_list. Returns median microseconds or None."""
    if not inputs_list or not callable(fn):
        return None
    times = []
    deadline = time.monotonic() + timeout_s
    i = 0
    while len(times) < n:
        if time.monotonic() > deadline:
            return None
        t0 = time.monotonic()
        fn(*inputs_list[i % len(inputs_list)])
        times.append((time.monotonic() - t0) * 1_000_000)
        i += 1
    times.sort()
    return times[n // 2]
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

            // Compute complexity metrics client-side; raw code never leaves the browser
            let complexity = null;
            try {
                const raw = pyodide.runPython(
                    `import json; json.dumps(analyze_complexity(${JSON.stringify(msg.code)}))`
                );
                complexity = JSON.parse(raw);
            } catch (_) { /* non-fatal */ }

            // Efficiency ratio: participant time / reference time (both timed in same Pyodide run)
            let efficiencyRatio = null;
            if (msg.referenceSolution) {
                try {
                    const funcMatch = msg.code.match(/^(?:def|class)\s+(\w+)/m);
                    const funcName = funcMatch ? funcMatch[1] : "solution";

                    // Only time standard function calls; skip class/operations-based tests
                    const timingInputs = msg.testCases.filter(tc => Array.isArray(tc.input)).map(tc => tc.input);

                    if (timingInputs.length > 0) {
                        const inputsJson = JSON.stringify(JSON.stringify(timingInputs));

                        // Time participant's function (already defined in Pyodide namespace)
                        const ptRaw = pyodide.runPython(
                            `import json; _ti = json.loads(${inputsJson}); json.dumps(measure_median_us(globals().get(${JSON.stringify(funcName)}), _ti))`
                        );
                        const participantUs = JSON.parse(ptRaw);

                        // Exec reference solution -- overwrites participant function, tests already ran
                        pyodide.runPython(msg.referenceSolution);

                        const rtRaw = pyodide.runPython(
                            `import json; json.dumps(measure_median_us(globals().get(${JSON.stringify(funcName)}), _ti))`
                        );
                        const refUs = JSON.parse(rtRaw);

                        if (participantUs !== null && refUs !== null && refUs > 0) {
                            efficiencyRatio = Math.round((participantUs / refUs) * 100) / 100;
                        }
                    }
                } catch (_) { /* non-fatal */ }
            }

            self.postMessage({ type: "result", results, complexity, efficiencyRatio });
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
