# Jev Atlas — an atlas that teaches Jev an enterprise app, and learns from its failures

Jev (TypeSafe's choice model) drives a real browser through Browser Use's `jev-ultrafast`
harness. On every step it picks one action from what is on screen. The **atlas** is
documentation of the application — what each screen and control is for, and where other
jobs live — attached to what Jev sees. It is bootstrapped by LLM agents that read the app's
manual and look at every screen, and it **learns**: when a goal still fails, a model reads
the failed run and the manual and proposes a lesson about the app; code checks the lesson
(no values, nothing copied from the goal, attaches to something that was on screen), a
person accepts it, and the atlas is rebuilt with it.

The app is [ADIT](https://alejandroerickson.com/mockent/adit/#/portfolio), a fictional
mineral-exploration management system with synthetic data, in the browser's localStorage
(`adit.tenant.v1`, `adit.session.v1`), so clearing those keys resets it.

## Run the demo

Needs [uv](https://docs.astral.sh/uv/), Google Chrome or Chromium, a TypeSafe API key, and
an OpenAI-compatible key for the text helper (it writes what Jev chooses to type) and the
learner.

```sh
jev-atlas/harness/bootstrap.sh     # once: install the vendored harness's dependencies, run its tests
cp jev-atlas/vendor/jev-ultrafast/.env.example jev-atlas/vendor/jev-ultrafast/.env
#   fill in TYPESAFE_API_KEY, and TEXT_MODEL_API_KEY / TEXT_MODEL_BASE_URL / TEXT_MODEL
#   (the runs below used OpenAI: https://api.openai.com/v1, gpt-5.6-luna). The learner uses the
#   same key unless LEARN_API_KEY / LEARN_BASE_URL / LEARN_MODEL (default gpt-5.5) say otherwise.
jev-atlas/demo.sh all            # opens a visible Chrome and runs the whole story:
                                 # five goals without the atlas, with it, then learning rounds
                                 # until nothing fails, then the replay page
```

`demo.sh all` first sets any accepted lessons aside, so it starts from the atlas the agents
wrote and learns again. It asks before accepting each round's lessons (`--yes` accepts every
lesson that passed the checks). Other commands: `demo.sh run with|without` (one pass on the
current atlas, which as published includes the learned lessons), `demo.sh learn`,
`demo.sh reset` (sets accepted lessons aside and rebuilds the base atlas), `demo.sh report`.
Each session is a folder `demo/sessions/<stamp>/` (`session.json`, and `report/index.html`,
the replay: every step's screen, what Jev chose and how sure it was, the atlas note it read,
and each lesson as before/after text). Pass or fail is always `goals/check.py` reading the
app's data, never the agent's own DONE.

The session behind the blog post is in `demo/sessions/20260926-123842/`; open its
`report/index.html` in a browser.

## Watch single runs

```sh
jev-atlas/chrome.sh show        # a visible Chrome on :9333
jev-atlas/inspect.sh            # the harness's inspector: http://127.0.0.1:8776 without the atlas, :8777 with it
```

Type a goal, click **Start demo**, then **Run automatically**. Start demo resets ADIT's
demonstration data first (`ADIT_RESET_ON_START=0` keeps it), so every run starts from the
same state. The two inspectors share the one Chrome and its data, so run one at a time. A
run that repeats the same actions is stopped (status `LOOP`).

## Results (2026-09-26)

Every run answered by `jev-1.13.0` (requested as `jev-latest`); ADIT reset before each run;
outcomes checked by `goals/check.py`. Numbers are steps.

The demo session (`demo/sessions/20260926-123842/`), one run per goal per stage:

| Stage | G5 | G2 | G3 | G7 | E9 | Passed |
|---|---|---|---|---|---|---|
| Without the atlas | ✓ 4 | ✗ 7 | ✗ 23 | ✗ 2 | ✗ 5 | 1/5 |
| With the atlas (`2026-09-22-merged-h4`) | ✓ 4 | ✓ 6 | ✓ 7 | ✓ 10 | ✗ 60 | 4/5 |
| After one learning round (`+learned-3`) | ✓ 4 | ✓ 6 | ✓ 7 | ✓ 10 | ✓ 14 | 5/5 |

Five runs per goal per condition afterwards, with the loop stop on and the learned atlas
(`goals/results/rel5-{without,with}.jsonl`): **without the atlas 5/25** (only G5), **with
it 25/25**. Each goal took the same number of steps in all five runs, so from the same
starting data the runs repeat. Two of the without-atlas failures were API errors. This is
a demonstration on five goals, one of which (E9) the atlas learned from, not a benchmark.

## What is here

| Path | What it is |
|---|---|
| `adit.env` | Start URL, atlas path, runs directory, default goal, ports, harness copy, browser. |
| `demo.sh`, `demo.py` | The demo: runs, learning rounds, sessions, replay page. |
| `chrome.sh` | Starts a Chrome on its own DevTools port (9333) with a throwaway profile (`~/.cache/adit-chrome-profile`). `show` makes it visible, `stop` stops it. |
| `run.sh` | One headless run of one condition: `jev-atlas/run.sh without "goal"`. |
| `inspect.sh` | The inspector, for watching (port 8776 without the atlas, 8777 with it). |
| `atlas/adit.json` | The atlas (how it was made: `atlas/README.md`). |
| `atlas/learned/` | Lessons: `pending/`, `accepted/` (applied last by `merge.py`), `rejected/`, `archive/`. |
| `manual/` | A plain-text mirror of ADIT's user manual, which the atlas authors and the learner read. |
| `docs/` | `ATLAS-FORMAT.md` (the atlas contract) and `BUILDING-A-SHIM.md` (how to write one for another app). |
| `harness/` | `bootstrap.sh`, the pinned upstream (`UPSTREAM`), our changes as one patch, and the atlas field reference (`ATLAS-FORMAT-ADDENDUM.md`). |
| `vendor/jev-ultrafast/` | Browser Use's harness at the pinned commit with our changes applied (MIT; its own `LICENSE`). |
| `tools/` | Atlas generators, merge and self-check; `learn.py` (propose, check, accept lessons); `report.py` (replay page); `summarize_runs.py` prints a table per run. |
| `goals/` | The goals, their checkers and the batch driver (`baseline.py`); `results/` holds the numbers above. **Atlas authors: do not read this folder.** |
| `demo/sessions/` | The recorded demo session. |
| `runs/` | Where `run.sh` and `inspect.sh` runs land (not committed). |

## Configuration

The launchers export `BU_CDP_URL` and `BU_NAME` from `adit.env`, and those override the
harness's `.env`, so no other browser or profile is touched. To use another browser,
profile, ports or harness copy without editing `adit.env`, export:

| Variable | Default | Meaning |
|---|---|---|
| `JEV_CLONE` | `jev-atlas/vendor/jev-ultrafast` | The harness. |
| `ADIT_CDP_URL` | `http://127.0.0.1:9333` | DevTools address of the demo Chrome. |
| `ADIT_BU_NAME` | `adit` | Name of the harness's browser daemon; use a distinct one per concurrent setup. |
| `ADIT_CHROME_PROFILE` | `~/.cache/adit-chrome-profile` | Throwaway profile for `chrome.sh`. |
| `ADIT_PORT_WITHOUT`, `ADIT_PORT_WITH` | `8776`, `8777` | Inspector ports. |
| `ADIT_RUN_DIR` | `jev-atlas/runs` | Where runs and logs land. |

To reset ADIT by hand: Admin → System settings → Reset demonstration tenant, or
`jev-atlas/vendor/jev-ultrafast/.venv/bin/python jev-atlas/goals/check.py reset` with the
demo Chrome running; `… check.py check G5` checks one goal's outcome.
