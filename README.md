# Jev Atlas

Teaching a fast browser agent an enterprise app. [Jev](https://typesafe.ai), TypeSafe's
model for fast, typed decisions, drives a browser through Browser Use's
[jev-ultrafast](https://github.com/browser-use/jev-ultrafast): on each step it is shown
the controls on the screen and picks one. That works on a site made to be understood at
first sight. On [ADIT](https://alejandroerickson.com/mockent/adit/), a mock enterprise app
made for experts, it mostly doesn't.

The **atlas** is a shim between Jev and the app. A frontier model read ADIT's user manual,
went through every screen, and wrote down what each page and control is for; on every step
the atlas adds that to what Jev sees, without changing Jev or the question it is asked.
When a task still fails, a model reads the failed run and proposes lessons about the app,
code checks them, a person accepts them, and the atlas is rebuilt.

**Blog post:** [Jev Atlas: teaching a fast browser agent an enterprise app](https://alejandroerickson.com/2026/09/27/jev-atlas.html) (with a video of a run)
· **The app:** [ADIT](https://alejandroerickson.com/mockent/adit/) ([source](https://github.com/alejandroerickson/mockent))

On five tasks, Jev finished 1 without the atlas, 4 with it, and all 5 after one learning
round. Repeated five times each afterwards: 5/25 without the atlas, 25/25 with it. It is a
demonstration on five tasks, not a benchmark; the details are in
[`jev-atlas/README.md`](jev-atlas/README.md#results-2026-09-26).

## Run it

Needs macOS or Linux, [uv](https://docs.astral.sh/uv/), Google Chrome or Chromium, a
[TypeSafe](https://typesafe.ai) API key, and an OpenAI-compatible API key.

```sh
git clone https://github.com/alejandroerickson/jev-atlas.git && cd jev-atlas
jev-atlas/harness/bootstrap.sh    # install the harness's dependencies and run its tests
cp jev-atlas/vendor/jev-ultrafast/.env.example jev-atlas/vendor/jev-ultrafast/.env   # then fill in the keys
jev-atlas/demo.sh all             # without the atlas, with it, learning rounds, replay page
```

[`jev-atlas/README.md`](jev-atlas/README.md) has the keys to fill in, how to watch single
runs in the harness's inspector, and what each folder holds. The recorded session behind
the post, with a step-by-step replay page, is in
[`jev-atlas/demo/sessions/20260926-123842/`](jev-atlas/demo/sessions/20260926-123842/).

## Where things are

- [`jev-atlas/atlas/`](jev-atlas/atlas/): the atlas and how it was made.
- [`jev-atlas/tools/learn.py`](jev-atlas/tools/learn.py): the learning loop.
- [`jev-atlas/docs/`](jev-atlas/docs/): the atlas format, and a playbook for writing one for another app.
- [`jev-atlas/vendor/jev-ultrafast/`](jev-atlas/vendor/jev-ultrafast/): the harness, vendored. The
  repository's first commit is upstream unchanged and the second applies our changes, so
  the diff between them shows exactly what was changed; [`jev-atlas/harness/`](jev-atlas/harness/)
  has the same changes as one patch.

## Licence

MIT ([`LICENSE`](LICENSE)). The vendored harness is Browser Use's, also MIT, with its own
[`LICENSE`](jev-atlas/vendor/jev-ultrafast/LICENSE). ADIT and all its data are fictional.
