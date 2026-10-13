"""Export the tutorial's core tasks (Blocks 1-5) as a Jupyter/Colab notebook.

The fallback for the workshop day: if the browser tool or the WiFi fails, the same
core tasks are available as a notebook.

    uv run python scripts/export_tutorial_colab.py
    # writes agenticbrainrot/static/tutorial/tutorial_core_tasks.ipynb

Upload that file to Colab (File -> Upload notebook) to make the backup Colab notebook;
the page also links it for download.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK_DIR = ROOT / "docs" / "tutorial" / "bank"
STATIC_DIR = ROOT / "agenticbrainrot" / "static" / "tutorial"
OUT = STATIC_DIR / "tutorial_core_tasks.ipynb"

sys.dont_write_bytecode = True
sys.path.insert(0, str(STATIC_DIR))
import tutorial_runner as runner  # noqa: E402


def _lines(text: str) -> list[str]:
    parts = text.splitlines(keepends=True)
    return parts or [""]


def md_cell(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text)}


def code_cell(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _lines(text)}


def fill_prompt(text: str, params: dict) -> str:
    return runner.PLACEHOLDER.sub(lambda m: runner.display_value(params[m.group(1)]), text)


def build_notebook() -> dict:
    cells = [
        md_cell(
            "# Python crash course – core tasks\n\n"
            "The same core tasks as the browser tutorial at canistillcode.org/tutorial/.\n\n"
            "1. *File → Save a copy in Drive* first, so your changes are kept.\n"
            "2. Run the cells in order (Shift+Enter).\n"
            "3. If things get confusing: *Runtime → Restart session and run all*.\n\n"
            "Each task has a code cell to edit, and a hidden worked solution after it."
        ),
    ]
    for path in sorted(BANK_DIR.glob("block*.json")):
        block = json.loads(path.read_text(encoding="utf-8"))
        cells.append(md_cell(f"## {block['block']}. {block['title']}\n\n{block['explanation_md']}"))
        for t in block["templates"]:
            if t["kind"] != "core":
                continue
            params = runner.generate(t.get("generator"), t["fixed_seed"])
            cells.append(md_cell(f"### {t['title']}\n\n{fill_prompt(t['prompt_md'], params)}"))
            cells.append(code_cell(runner.substitute_code(t["starter_code"], params)))
            hint = " ".join(t["hints"])
            cells.append(md_cell(f"<details><summary>Hint</summary>\n\n{fill_prompt(hint, params)}\n\n</details>"))
            solution = runner.substitute_code(t["reference"], params)
            cells.append(
                md_cell(f"<details><summary>Worked solution</summary>\n\n```python\n{solution}\n```\n\n</details>")
            )
    for i, cell in enumerate(cells):
        cell["id"] = f"cell-{i:03d}"  # nbformat 4.5 requires cell ids
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "colab": {"provenance": []},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    nb = build_notebook()
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(nb['cells'])} cells)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
