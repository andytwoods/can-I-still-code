# Content plan – Python crash course (prj-011)

_Rewritten 13 Oct 2026 after reviews by GPT, Gemini and Qwen ([plan_review.md](plan_review.md)). Built backwards from Hiro's notebook ([what it assumes](hiro_notebook_requirements.md)). The course outline is in [overview.md](overview.md); this file is what we teach, block by block._

**Goal:** about 20 psychologists, new to Python, leave able to *read and change* code like Hiro's, above all **functions**, using three patterns:

1. **Step and record**: loop, update, add to a `history` list, plot it.
2. **Wrap and repeat**: one run in a function; call it many times; count or average.
3. **Sweep and compare**: run the function for several settings; pick the best.

**No running model.** Each block uses small, standalone examples drawn from Hiro's own topics (savings, coin flips, shop stock), so his notebook feels familiar and any block can be done on its own.

## How practice works (Andy, 13 Oct)

**Unlimited practice in the browser.** People can try as many examples as they like.
- Every task is a **template**. A "New example" button fills it with fresh numbers or names, as often as wanted.
- Answers are **checked in the browser** with Pyodide: the reference solution works out the right answer for that variant, and the learner's code is run against it.
- **Feedback** shows expected versus actual output. A hint appears after one failed try; a worked solution after two.
- A **staircase** sets the next task's level (1–5) from whether the check passed and the learner's rating ("too easy" … "too hard").
- **Skip ahead:** each block opens with a check task. Pass it and the block is done; move on, or pick up that block's **Extras**.
- **Everyone does the same core task** in each block, and the room **regroups** at the end of every block. The staircase and extras are for practice and fast finishers; they never set the pace.
- Progress is **saved in the browser after every task**, so a refresh loses nothing. Nothing is stored on the server.

Each block below lists its **core** (live, together), **practice** (template tasks, unlimited) and **extras** (optional).

---

## Block 1 · 0–10 min · Getting going

- **Check task (skip ahead):** fix one broken line and make it print the right message.
- **Core, live:**
  - Open the tool (link on the screen and in the pre-workshop email).
    - It loads Python in the browser; the first load takes a few seconds.
  - Type `print("hello")`, run it, see the output underneath.
    - Code goes in the box; output appears below it.
  - Change the message and run again.
    - Running again replaces the old output.
  - Break it on purpose: `print("hello"` (missing bracket).
    - Read the **last line** of the error first; it names the problem.
    - The line number points at, or just after, the mistake.
- `#` starts a comment; Python ignores the rest of the line.
- **Watch for:** people retyping everything after an error instead of fixing one character.
- **Practice (levels 1–5):**
  1. Change the text being printed.
  2. Print two lines.
  3. Fix a missing bracket.
  4. Fix a missing quote mark.
  5. Fix a misspelt name (`pritn`).

## Block 2 · 10–25 min · Values and lists

- **Check task (skip ahead):** given a list of daily takings, print the total and the average.
- **Values and variables (5 min):**
  - `takings = 250` stores a value under a name.
  - Arithmetic: `+ - * /`; powers are `**`.
    - **Quirk:** `^` is not a power in Python. `3 ^ 2` gives `1`, with no error.
  - `/` always gives a decimal (`7 / 2` is `3.5`); `//` drops the remainder (`7 // 2` is `3`).
  - `print(f"Takings: {takings}")`: the `f` before the quote lets you put values inside `{ }`.
  - **Quirks:**
    - Names are case-sensitive: `Total` and `total` are different.
    - `True`, `False` and `None` need capitals.
- **Lists (10 min):**
  - `week = [250, 310, 180, 400, 520]`.
  - Counting from 0: `week[0]` is Monday, `week[4]` is Friday.
    - **Quirk:** `week[1]` is the *second* item, not the first.
  - `len(week)`, `sum(week)`, `min(week)`, `max(week)`.
  - Average: `sum(week) / len(week)`.
  - Add a day: `week.append(610)`.
    - The dot means "do this to the list"; the list itself changes.
  - Which day was best: `week.index(max(week))`, a position counted from 0.
- **Example to build live:** a week of café takings: total, average, best day, add Saturday.
- **Watch for:**
  - Off-by-one answers from counting from 1.
  - `week.append(610)` written as `week = week.append(610)`, which empties the variable.
- **Practice (levels 1–5):**
  1. Read one item from a list.
  2. Change one item.
  3. Append a value and print the new length.
  4. Work out the average.
  5. Find the position of the largest value.
- **Extras:** E1 formatting numbers; E2 slicing; E3 multiple assignment.

## Block 3 · 25–45 min · Loops, decisions, and pattern 1

- **Check task (skip ahead):** count how many days in a list took more than £300.
- **Indentation first (5 min):**
  - In Python, **the indent decides** what is inside a loop or an `if`.
  - Show two versions of the same loop, where only the indent of the last line differs:
    - indented: it runs every time round the loop;
    - not indented: it runs once, after the loop.
    - Different answers, and **no error**. This is the main reason indentation matters.
  - One indent = **4 spaces**.
    - The Tab key types 4 spaces in the tool, in Colab and in most editors.
  - **Tabs versus spaces:**
    - A real tab character and spaces look the same on screen, but Python treats them differently.
    - Mixing them gives `IndentationError` or `TabError`.
    - It usually happens when pasting code from an email, a PDF or a web page.
    - The fix: delete the indent and press Tab again.
  - A line ending in `:` must be followed by an indented block.
  - Colab may indent by 2 spaces while Hiro's code uses 4.
    - Both work, but every line in one block must match.
    - _(Check Colab's current default before the day.)_
- **Loops (5 min):**
  - `for day in week:` goes through each item.
  - `for i in range(5):` counts 0, 1, 2, 3, 4.
    - **Quirk:** `range(5)` stops at 4, not 5.
  - Adding up as you go: `total = 0`, then `total += amount` inside the loop.
    - `total += amount` is short for `total = total + amount`.
- **Decisions (4 min):**
  - `if amount > 300:` … `elif amount > 200:` … `else:`.
    - **Quirk:** `elif`, not `else if`.
  - `==` compares, `=` stores.
    - `if total = 5:` is an error; `if total == 5:` is a question.
  - `and`, `or`, `not` are written as words.
- **Pattern 1, step and record (6 min):**
  - Savings: £1,000 at 0.5% a month, for 24 months.
  - Each month: add interest, then `history.append(balance)`.
  - Plot it:
    - `import matplotlib.pyplot as plt`
    - `plt.plot(history)`, `plt.xlabel("Month")`, `plt.ylabel("Balance (£)")`, `plt.show()`
  - Point out: this is the same shape as Hiro's mortgage section.
- **Watch for:**
  - Forgetting the colon.
  - `total = 0` placed *inside* the loop, so it resets every time.
  - `history.append(...)` indented at the wrong level, giving one point instead of 24.
- **Practice (levels 1–5):**
  1. Print the numbers 1 to n.
  2. Add up a list with a loop.
  3. Count items above a threshold.
  4. Step and record a growing value.
  5. Stop recording once a target is reached.
- **"Fix the indentation" tasks (all levels):**
  - Code that runs but gives the wrong answer because one line is indented wrongly.
  - Code with a tab/space mix to repair.
- **Extras:** E4 `while` and `break`; E5 list comprehensions; E10 more quirks.

## Break · 45–55 min

- Quiet help for anyone stuck.
- People ahead carry on with extras.

## Block 4 · 55–80 min · Functions and randomness (the heart of the session)

- **Check task (skip ahead):** write a function that takes a list and returns its average.
- **Writing a function (7 min):**
  - ```python
    def add_interest(balance, rate):
        return balance * (1 + rate)
    ```
  - `def`, a name, arguments in brackets, a colon, an indented body.
  - Calling it: `add_interest(1000, 0.005)`.
  - A default value: `def add_interest(balance, rate=0.005):`.
    - Now `add_interest(1000)` works too.
- **`print` versus `return` (4 min):**
  - A function only hands back a value if it says `return`.
  - Without `return`, the function gives back `None`.
  - `print` only shows a value on screen; `return` hands it back so you can store it.
  - Demo: a function that prints instead of returns; `x = f(5)` then `x` is `None`.
- **Outside variables (3 min):**
  - A function can read a variable defined outside it.
  - Change that variable later and the function's answer changes, silently.
  - Hiro warns about exactly this in his shop section; better to pass it in as an argument.
- **Randomness (4 min):**
  - `import random`
  - `random.random()`: a decimal between 0 and 1.
  - `random.randint(1, 6)`: a dice roll (here **both ends are included**, unlike `range`).
  - `random.choice(week)`: one item at random.
  - `random.seed(1)`: the same "random" numbers every run, so results can be checked.
- **Pattern 2, wrap and repeat (5 min):**
  - `flip_coins(n)` flips n coins and returns the number of heads.
  - Call it 1,000 times with a `for` loop; count runs with 7 or more heads out of 10.
  - Share of runs = count / 1,000. That is a probability, estimated by simulation.
- **Hiro link (2 min):**
  - His Exercise 1 asks people to give a function a second argument.
  - Practise it now: change a savings function that uses a fixed rate so the rate becomes an argument.
- **Watch for:**
  - Forgetting `return`.
  - Calling a function before running the cell that defines it.
  - Mixing up `randint` (includes the top number) and `range` (does not).
- **Practice (levels 1–5):**
  1. Call a function with different arguments.
  2. Change a default value.
  3. Add an argument to an existing function.
  4. Write a function with `return`.
  5. Wrap a small simulation in a function and repeat it.
- **Extras:** E6 functions and outside variables, in more depth; E7 the one-line `sum(... for _ in range(n))` form.

## Block 5 · 80–95 min · Pattern 3, as a short demonstration

- **Check task (skip ahead):** try three settings of a function and print which gave the highest result.
- **Demo (8 min):**
  - A bakery orders loaves each morning; demand is random; unsold loaves are wasted.
  - `profit(order)` runs 1,000 random days and returns the average daily profit.
  - Try orders from 20 to 60 in a loop; store each result in a list.
  - Plot profit against order size; find the best order.
  - Point out: the top of the curve is flat, so being roughly right is enough.
  - Same shape as Hiro's fish-and-chip shop.
- **Everyone, one change (5 min):**
  - Change the cost of a loaf.
  - **Predict first**: will the best order go up or down? Then rerun.
- **Talking point (2 min):**
  - One run is not a finding; the spread across runs is.
- **Practice (levels 1–5):**
  1. Run a function for each setting in a list.
  2. Store the results in a list.
  3. Find the best setting.
  4. Plot results against settings.
  5. Compare two versions of a model on one plot.
- **Extras:** E8 extend the bakery (a cost for running out); E9 objects and dot syntax.

## Block 6 · 95–120 min · Working in notebooks (Colab), inside Hiro's notebook

Hiro's session is in Colab, so the last 25 minutes are spent in *his* notebook.

- **Own copy first (3 min):**
  - Open his link.
  - *File → Save a copy in Drive*.
  - Check the title now says "Copy of…". Without this, nothing they type is saved.
  - Doing this early exposes Google login problems while there is time to fix them.
- **Text and code cells (3 min):**
  - Text cells explain; code cells run.
  - Shift+Enter runs a cell and moves to the next.
  - The number in `[ ]` shows the order cells were run in.
- **Run order and hidden state (5 min):**
  - Run his import cell, then the mortgage cell.
  - Change `payment`, rerun only the plot cell: the chart does not change. Ask why.
    - The plot uses `history`, made by the earlier cell, which was not rerun.
  - Fix: rerun from the top.
  - Bigger fix: *Runtime → Restart session and run all*.
  - His notebook warns twice about this exact problem.
  - Indentation check: add a line inside one of his loops and match his 4 spaces.
- **His Exercise 1 (10 min, pairs):**
  - Give `mortgage_balance` a second argument, `principal`.
  - **Predict first**: will a £500,000 flat cost half as much a month as a £1,000,000 one?
  - Then run it for £750,000, £500,000 and £250,000.
  - This is exactly what they practised in Block 4.
- **Getting help, and leaving with it (4 min):**
  - His Answers section hides code behind *Show code*.
  - A disconnected runtime means: rerun from the top.
  - *File → Download → Download .ipynb* to keep a copy; it opens in Jupyter and VS Code too.
  - Exit question: which setting did you change, and what happened?

---

## Extras (optional, self-paced in the tool)

Each extra is a short explanation, a worked example and unlimited template tasks. Where Hiro's notebook uses it, the extra says where.

| | Extra | Where Hiro uses it |
|---|---|---|
| E1 | Formatting numbers: `{x:.2f}`, `{x:,}` | Every `print` in his notebook |
| E2 | Slicing: `xs[2:5]`, `xs[-1]` | Results at the end of a history |
| E3 | Multiple assignment: `S, I, R = 990, 10, 0`; looping over pairs | Epidemic model |
| E4 | `while` and `break`: "keep going until…" | Binary search, birthday threshold, payoff time |
| E5 | List comprehensions: `[f(x) for x in xs]` | Fish-stock sweep, birthdays |
| E6 | Functions reading outside variables, in depth | His warning about `cost` |
| E7 | `sum(f() for _ in range(n))` and the `_` name | Birthdays, hiring |
| E8 | Extend the shop example | Fish-stock section |
| E9 | Objects and dot syntax: `agent.status`, `agent.infect()` | His agent-based model |
| E10 | More quirks: `b = a` shares one list rather than copying it; a function can change a list it is given; `0.1 + 0.2` is not exactly `0.3` | His functions that change the population list |

Anyone who finishes Block 5 and the extras moves on to the first sections of Hiro's notebook (mortgage, Monte Carlo).

## What the tool needs

- Pyodide with `matplotlib` (plots shown as images under the code).
- Two kinds of check: **function checks** (call `f(7)`, expect 7; already built on canistillcode.org) and **variable checks** (after running, `average` should equal 4.5; new).
- Editor set so **Tab inserts 4 spaces** and pasted tab characters are shown or converted; error messages for `IndentationError` / `TabError` explained in plain English.
- Task templates with a generator and a reference solution; "New example" button; hint and worked solution.
- Staircase, skip-ahead check per block, progress saved in the browser after every task.
- A **backup Colab notebook** with the same core tasks, in case the tool or the WiFi fails.

## Not covering

Classes in depth, numpy, `set()`, `enumerate`, `plt.subplots`, `random.expovariate`. Hiro's notebook explains these where it uses them.

## If running late

Cut first: Block 5 shrinks to the demo with no practice. **Never cut:** Block 4's functions, and Block 6's own-copy step and Exercise 1.

## Before the day

- Preflight on a few laptops and browsers, and on a slow connection.
- Ask people (in the pre-workshop email) to open the tool and Hiro's notebook link the day before, and check their Google login.

## Still to decide

- How far into his notebook Hiro expects people to get in his session.
- The task bank: 5 core topics × 5 levels × 2 templates = 50, plus 10 extras (about 28 templates), plus "fix the indentation" templates. AI-drafted, every template's checks run automatically, then reviewed by Andy. About 2 days.
