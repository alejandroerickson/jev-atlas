# Harness for the ADIT demo

A patched copy of Browser Use's [`jev-ultrafast`](https://github.com/browser-use/jev-ultrafast)
(MIT, Copyright (c) 2026 Browser Use), for driving the public mock app ADIT
(https://alejandroerickson.com/mockent/adit/). The patched copy is vendored in
`../vendor/jev-ultrafast/`: the repository's first commit is upstream at the pinned commit,
unchanged, and the second applies `local-changes.patch`, so the diff between them is the
record of what was changed.

```bash
jev-atlas/harness/bootstrap.sh                 # the vendored copy: uv sync --frozen, then the tests
jev-atlas/harness/bootstrap.sh ~/elsewhere     # or a fresh copy: download the pinned tarball, patch, sync, test
```

The tests: 116, of which the 26 in `tests/test_snapshot_dom.py` drive a headless Chrome and
are skipped when they find none. Then copy `.env.example` to `.env` and fill in the keys.

| File | What it is |
|---|---|
| `UPSTREAM` | Upstream repository URL and pinned commit. |
| `local-changes.patch` | Full `diff -ruN` from that commit to the working harness (excludes `.venv`, `.env`, caches, runs). |
| `bootstrap.sh` | Install and test the vendored copy, or download, patch, install and test a fresh one. |
| `ATLAS-FORMAT-ADDENDUM.md` | The atlas contract for this harness, including app-specific `selectors`. The overview and writing rules are `../docs/ATLAS-FORMAT.md`. |

To refresh the patch after changing the harness, diff a pristine extraction of the
pinned tarball against it with the same exclusions (`diff -ruN -x .venv -x .env
-x .git -x .pytest_cache -x __pycache__ -x runs -x artifacts -x '*.pyc' a b`).

Environment added in the third round (2026-09-22; details in the addendum):
`JEV_TODAY` (the date the text helper takes as today, for reproducible runs),
`JEV_TODAY_FACT=1` (also tell Jev the date in the page context) and
`JEV_SHARE_NOTES=0` (repeat atlas notes on every element instead of sharing them).
The rule and BLOCKED wording, today's date and row context also change what a run
**without** an atlas sends, so a without-atlas baseline from before this round is
not directly comparable.

Fourth round (2026-09-22): **PRESS_ENTER**, a new operation. Runs showed Jev typing a
record code into ADIT's top-bar search box and then clicking "Open Search the tenant"
over and over without reaching the results. That form has no Search button: it submits
on Enter only, and the harness had no way to press Enter. The "Open …" click it kept
choosing is the harness's own twin of every text field (meant for date pickers and
suggestion lists); on a search box it only focuses the field. Both fixes are generic and
apply with and without an atlas:
- `snapshot.js` offers a `submit` action (operation `PRESS_ENTER`, target head
  `press_enter_target`) on a single-line `<input>` that holds a value and is either a
  search field (`type=search`, `role=searchbox`, or inside `<search>`/`role=search`) or
  the focused field (the one just typed into). A textarea is never offered.
- The executor focuses the field and sends Enter (`keyDown` with `"\r"`, which also
  triggers a form's implicit submission, then `keyUp`); no click, no text model call.
- A plain search box (no `list`, `aria-haspopup`, `aria-autocomplete`, `aria-controls`,
  `aria-owns` or `aria-expanded`) no longer gets the "Open …" click twin.
- Live check, headless Chrome, 2026-09-22: typing `PRJ-0468` into ADIT's search box and
  PRESS_ENTER lands on `#/search?q=PRJ-0468` with the one matching project.
- Tests: `tests/fixtures/search-form.html` (four DOM tests) and three in `tests/test_agent.py`.


Jev Atlas demo (2026-09-26): the GPT-5 text-model hunk (`max_completion_tokens`,
`reasoning_effort`), and the step log records `atlas_page`, `atlas_overlays` and each
element's `role` for the learner. Then, after live inspector runs got stuck:
- **Loop stop.** A run whose last one to four actions (same URL, same control, same set
  of controls on the page) have repeated three times in a row stops with status `LOOP`;
  waits are not counted. `JEV_LOOP_REPEATS` sets the count (`0` turns it off). Replayed on
  the 43 runs logged on 2026-09-26, it fired on 10, all failures, none a run that passed;
  it would have stopped E9's four-step cycle after 15 actions instead of 60. It applies with
  and without an atlas. It could in principle stop a run that would have recovered; no
  logged run did.
- **`JEV_BEFORE_RUN`.** A shell command the inspector runs on every Start demo, before
  opening the page. `../inspect.sh` sets it to reset ADIT's demonstration data
  (`goals/check.py reset`), unless `ADIT_RESET_ON_START=0`.
