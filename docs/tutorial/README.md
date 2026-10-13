# Browser Python tutorial (`/tutorial/`)

A Python crash course that runs entirely in the browser, built for the 21 Oct 2026 workshop
(about 20 psychologists, new to Python). The teaching plan is [plan.md](plan.md).

- Blocks 1–5 run in the page; Block 6 links to the organiser's Colab notebook.
- Each block has an explanation, one **check task** (pass it and the block is done), **core
  tasks** done together in the room (fixed seeds, so everyone sees the same numbers) and a
  **practice ladder**, levels 1–5.
- Every task is a template. "New example" gives a fresh variant from a new seed.
- Code is checked in the browser with Pyodide. Hint after one failed run; worked solution after two.
- Progress is saved in `localStorage` (`tutorial_v1`). Nothing is sent to the server.

## The no-backend rule

After the one `GET /tutorial/`, the page makes **no requests to the Django app**: no API
endpoints, no HTMX, no form posts, no telemetry, no auto-save. Allowed traffic: static files
(Whitenoise), the Pyodide CDN (`cdn.jsdelivr.net/pyodide/v0.27.4`, the same version as the
homepage demo, so the cache is shared) and its packages.

This is a deliberate exception to the guideline "use HTMX for all dynamic updates", decided by
Andy for this feature. It is also recorded in `agenticbrainrot/tutorial/views.py`.

Base template audit (13 Oct 2026): the navbar, footer, messages partial and `project.js` make no
calls to the app after load (no polling, no `hx-trigger="load"`). So the page extends the normal
`base.html`, with two changes:

- it does not load htmx (nothing on the page uses it);
- it blanks `rollbar_client_token`, so the Rollbar browser reporter is not included. Rollbar
  is a third party, not the app, but it would send error payloads off the machine.

Learner code itself is not network-sandboxed (Pyodide can fetch). That is accepted; the tutorial
adds no `pyfetch` helpers.

The e2e test `test_no_backend_hits_after_first_load` records every request while using the page
and fails if any goes to the app origin outside `/static/`.

## Study integrity

The tutorial does not touch the `challenges` app, its fixtures, the `Challenge` model,
`static/js/pyodide-worker.js`, `static/js/code-editor.js` or any study template. Tutorial tasks
are never stored in or loaded from the database. The app has no models and no migrations.

## Files

```
agenticbrainrot/tutorial/                     the Django app (TemplateView, url name tutorial:index)
  templates/tutorial/index.html               the page, including Block 6
  tests/                                      view, runner and bank tests
agenticbrainrot/static/tutorial/
  tutorial.js                                 UI: blocks, tasks, staircase, storage
  tutorial-worker.js                          Pyodide worker (tutorial only)
  tutorial_runner.py                          task runner: shared by the worker and the validator
  bank.bundle.json                            GENERATED – the whole bank, one request
  tutorial_core_tasks.ipynb                   GENERATED – core tasks as a notebook (fallback)
  tutorial.css                                what Bulma lacks
  vendor/                                     self-hosted CodeMirror 5.65.13 and SweetAlert2 11.14.5
docs/tutorial/bank/block1.json … block5.json  task sources, one file per block (edit these)
scripts/build_tutorial_bank.py                validate the sources, write bank.bundle.json
scripts/export_tutorial_colab.py              write the fallback notebook
```

`tutorial_runner.py` is the key design choice: the browser worker fetches it as a static file,
and the validator imports it under CPython. So the bank is validated with exactly the rules the
learner's browser applies (fresh namespace, deep-copied params, reseeded random state, bounded
output, the comparison rules). The e2e suite then re-runs a sample in real Pyodide.

The consent gate exempts `tutorial:index`, so logged-in users who have not consented can use it.
The page is `noindex, nofollow` and not in the sitemap.

## Adding or changing a task

1. Edit `docs/tutorial/bank/blockN.json`. The schema is in the spec (tasks.md section 5); a
   template looks like this:

   ```json
   {
     "schema_version": 1, "id": "b2-avg-L4", "block": 2, "kind": "practice", "level": 4,
     "title": "Average takings",
     "prompt_md": "The list `week` holds @@n@@ days of takings. Store the average in `average`.",
     "starter_code": "week = @@week@@\n# your code here\n",
     "generator": "def generate(rng):\n    n = rng.randint(4, 7)\n    return {'n': n, 'week': [rng.randint(100, 600) for _ in range(n)]}",
     "reference": "week = @@week@@\naverage = sum(week) / len(week)\n",
     "checks": [{"id": "avg", "type": "variable", "name": "average"}],
     "hints": ["Add the list up with sum(), then divide by len()."],
     "wrong_examples": ["week = @@week@@\naverage = sum(week)\n"],
     "alternative_solutions": []
   }
   ```

   - Placeholders are `@@name@@` only. In code they become `repr(value)`; in the prompt the
     plain text (strings without quotes). Braces in code are untouched.
   - `kind`: `check`, `core` (needs an integer `fixed_seed`), `practice` or `fix` (both need a
     `level`; `fix` tasks sit in Block 3's ladder).
   - Check types: `variable`, `function` (with `calls`, which may use `"@@param@@"`), `stdout`
     (`normalise`: `strip` or `exact`), `no_error`. Expected values come from running the
     reference with the same params and seed. Numbers compare with `math.isclose`; `True` is not
     accepted for `1`.
   - Randomness tasks: the prompt must name the random call, how many draws and in what order,
     and the template needs at least one `alternative_solutions` entry.
   - Only core tasks may set `allow_plot`. Check the data (e.g. `history`), never the picture.
   - Optional `solution_md`: a short note shown with the worked solution.
2. Validate and rebuild:

   ```bash
   uv run python scripts/build_tutorial_bank.py --block 2   # quick: one block, writes nothing
   uv run python scripts/build_tutorial_bank.py             # full: all blocks, writes the bundle
   uv run python scripts/export_tutorial_colab.py           # refresh the fallback notebook
   ```

   For every template and 30 seeds, the validator checks that the reference passes, the starter
   code fails, every wrong example fails and every alternative passes, and that there are at
   least 10 distinct variants. Templates may import only `random`, `math` and
   `matplotlib.pyplot`. Markdown is pre-rendered with raw HTML disabled.
3. Commit the source **and** the regenerated `bank.bundle.json`. `pytest` fails if the bundle is
   stale.

## How the page behaves

**Flow per block.** Explanation, then "Already know this? Try the check task." Pass it and the
block is done, and its ladder starts at level 3. Fail it and there is no penalty: go to the core
tasks, and the ladder starts at level 1. Blocks and core tasks are always freely accessible.

**Staircase** (practice only; the level changes once per variant, when Next is pressed):

| outcome | rating | next level |
|---|---|---|
| passed, solution not viewed | too easy | +2 |
| | easy | +1 |
| | just right (or no rating) | same; a 2nd consecutive "just right" → +1 |
| | hard | same |
| | too hard | −1 |
| failed, or solution viewed | – | −1 |
| skipped without running | – | same |

Clamped to 1–5. Anything but "just right" resets the streak; so does a promotion.

**Worker safety.** One operation at a time; every message carries `workerGen` and `opId`, and
stale replies are ignored. Deadlines: 60 s for Python start-up and for each package load,
5 s per run (started after packages load), 2 s per generator. On a run timeout the worker is
terminated and a fresh one started; the learner's code stays in the editor. If start-up fails,
"Try again" creates a fresh worker.

**Editor.** CodeMirror 5: 4-space indent, Tab inserts spaces, Shift+Tab dedents, Ctrl/⌘+Enter
runs, Esc leaves the editor (for keyboard users). Real tab characters are highlighted. Pasting
code with tabs shows a toast offering "Convert tabs to spaces".

## Tests

```bash
uv run pytest agenticbrainrot/tutorial                 # views, runner, bank validation
uv run pytest tests/e2e/test_tutorial.py -m e2e --base-url http://localhost:8000   # needs a dev server
```

The e2e suite covers: Pyodide ready; solve a task and reload (progress and code restored);
New example changes the numbers; `while True: pass` → timeout → restart → next run works;
tab/space mix → friendly message; a core plot shows an image; a sample of references pass in
the real worker; no backend hits after the first load.

## Manual checks for Andy (before 20 Oct)

- [ ] Chrome, Firefox, Safari, Edge: open `/tutorial/`, do one task per block, reload, check
      progress is kept.
- [ ] An older laptop: first load time, run time of the Block 3 and Block 5 plotting tasks.
- [ ] Cold load throttled to "Fast 3G" in DevTools (clear the cache first): explanations
      readable while Python loads; Run enabled once ready.
- [ ] 20 tabs at once on one laptop as a rough load test (static files only, so the server
      should not notice).
- [ ] Private/incognito window: the "can't save progress" banner appears and the page still works.
- [ ] Paste code with tabs (e.g. from an email): highlighted, toast offers to convert.
- [ ] Block 6: the Colab link opens the right notebook.
- [ ] Read every task and explanation (the bank was AI-drafted on 13–14 Oct for review on
      17–18 Oct).

## Fallbacks for the day

- `tutorial_core_tasks.ipynb` (generated by `scripts/export_tutorial_colab.py`) holds the core
  tasks of Blocks 1–5 with hidden hints and solutions. It is served at
  `/static/tutorial/tutorial_core_tasks.ipynb` and linked from the page; link it from the
  pre-workshop email too. Upload it to Colab to make the backup Colab notebook.
- If the WiFi fails: a phone hotspot for the Pyodide download (cached after the first load),
  and pairing at shared laptops.

## Deadline cuts

None so far. (If Block 5's ladder is cut, write `BLOCK 5 LADDER CUT` and the reason here; the
validator then allows the missing levels.)

## Open questions for Andy

1. Link "Tutorial" from the site navbar, or keep it unlisted (shared only with the workshop)?
   Currently unlisted.
2. Keep `noindex` after the workshop? Currently noindex.
3. Confirm the review window: Sat 17 – Sun 18 Oct.
