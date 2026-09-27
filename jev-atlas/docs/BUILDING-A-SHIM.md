# Building a shim for a web application: the playbook

A **shim** here is an atlas (see [`ATLAS-FORMAT.md`](ATLAS-FORMAT.md)) that lets the
Jev-driven browser agent carry out a loosely worded request on an application
without being told which controls to click. This is the process, with ADIT as the
worked example: its atlas is in [`../atlas/`](../atlas/) and its own account of how
it was made is [`../atlas/README.md`](../atlas/README.md). Claims about ADIT are
observed in that build (2026-09-22) unless marked **inferred**.

## 0. What you are building, and what you are not

The atlas is **product documentation, keyed to the DOM**. For each page: what it is
for, where the neighbouring tasks live (routing, worded positively; see §5), where it leads. For each
control: its region of the screen, what it does, and what it does *not* do that a
reader might think it does. It is not a script, a route or a list of steps.

- **Annotate, never filter.** Every control the harness sees is still offered to
  the model, described or not. Narrowing the page to a demonstrated route makes the
  control someone happened to touch look like the answer.
- **Describe purpose and scope, never procedure.** "Opens the approval dialog for
  the current step" is right; "to approve a request, first…" is the experiment
  answering itself.
- **Never name a record, a person, an amount, a year or a code** a task could use.

Why the shape: the TypeSafe docs' guidance for Choice is to give the model the full
list and write descriptions that separate options from each other, and to split a
description into fields when options keep being confused; accuracy falls as the
state fills with content unrelated to the decision. Long is not better.

## 1. Inputs

1. **Documentation**, in whatever form exists. ADIT has an in-app manual
   (`#/manual`), mirrored to [`../manual/`](../manual/). It supplies the product's
   own vocabulary, so the model's reading of the screen and a person's reading of
   the manual agree.
2. **A browser with a DevTools port and a throwaway profile**
   ([`../chrome.sh`](../chrome.sh)). If the application needs a sign-in, the person
   signs in by hand; no credential ever passes through the author. ADIT needs none.
3. **The list of areas that matter.** ADIT was split into seven: portfolio-global
   (top bar, account, search, notifications, manual, not-found), projects,
   programmes, drilling-assays, resources-optimiser, approvals, admin.
4. **What is safe to touch.** ADIT's data lives in the browser's localStorage and
   resets from Admin → System settings or by clearing `adit.tenant.v1` and
   `adit.session.v1`, so nothing a run does outlives the profile.
5. **Nothing about the tasks.** If an author is told one anyway, write it down.

## 2. Mirror the documentation to text

One Markdown file per section, each starting with its source and date:

```
Source: https://alejandroerickson.com/mockent/adit/#/manual/approvals
Fetched: 2026-09-22
```

Text, not HTML; the author will read all of it. If a documentation URL carries a
credential, strip it and grep the mirror to prove it is gone. With no documentation
at all, say so before starting: an atlas written from screens alone uses the
author's vocabulary rather than the product's, and is a weaker shim.

## 3. Survey the DOM, read-only

Before writing a description, find out what the harness can key on. Run the
harness's own reader (`jev_ultrafast/snapshot.js`) against each page and overlay, as
[`../tools/selfcheck.py`](../tools/selfcheck.py) does, and keep an element inventory
and a screenshot per state. Per page and per overlay, find out:

- **Which attribute is the stable key**, and whether it changes by region (test
  hooks such as `data-testid`, hand-written ids, or nothing but text and landmarks).
  ADIT has few ids, so its keys lean on `landmark`, `section`, `role` and
  `href_regex`.
- **Which controls arrive with no usable name**: icon buttons, fields whose label
  becomes their value, identical per-row buttons (ADIT: Lock, Exclude, Edit,
  Remove in tables, told apart by `row_label`).
- **Which widgets are not DOM elements**, and whether they have a JS API.
- **Everything that opens without changing the URL**: menus, trays, dialogs. ADIT
  has 25 overlays among 88 page entries.

Read only: open a dialog, read it, close it with its own Cancel. Note which things
ignore Escape.

## 4. Choose keys the harness can match

Prefer, in order: `track_id`/`id` → `id_regex` → (`landmark` or `section`,
`text`) → (`ancestor`, `text`) → (`page`, `text`) → `href_regex` → `row_label`.
The most specific thing that says *which* control this is, and that survives a
redeploy.

- **Specificity is weighted, not counted** (weights in the addendum). If two
  entries can both match, make the right one heavier, not longer.
- **A key that contains a record id is not a key.** Key record links by route
  pattern (`href_regex` on `#/projects/PRJ-…`) and describe what that kind of link
  does.
- **Test every key against captured states.** ADIT's whole-app check covers 114
  states and reports annotated / offered per area (5158 / 5158) plus flags for an
  entry landing in the wrong area, landmark or dialog.
- **Test overlay selectors three ways**: no match closed, a match open, none again
  after closing. An overlay selector that is always on poisons every page.

Where a key has to be generic, say so in a `note` and make the text true of all
matches.

## 5. Write the text as documentation

Pages get `what`, `not_here`, `leads_to`; controls get `region`, `what`, `not_for`.
`not_here` and `not_for` do the most work: they name the neighbour a reader would
confuse this with, and where the other thing lives. Check every description: does
it name a record or value? Does it describe a sequence? Would it be true if the task
were different? Does it separate this control from the one beside it?

Describe the traps that cost runs: fields that must be chosen from a list rather
than typed into, and buttons that do nothing while a form is invalid.

### Wording rules (measured on ADIT, 2026-09-22)

The first ADIT atlas hurt Jev in measured runs through its wording, not its content.
Replays showed that rewording is what matters: moving the same negative text to
another field, or prefixing it with "Elsewhere", did not help. These rules apply to
every string in the atlas, including what `facts_js` returns.

1. **Route, do not refuse.** `not_here` and `not_for` are never worded as a negation
   ("nothing on this page does X", "not here", "X happens in Y, not here", "this page
   cannot…"). Jev reads those as "you are blocked". Say where the thing lives:
   "Acting on an approval: the Approvals section." / "Changing records: each record's
   own page." Keep the information; drop the negation.
2. **State the situation, not the absence.** A fact such as "No actions are offered to
   you on this request" becomes the condition and where it changes: "Decision buttons:
   shown only to the role that owns the current step; the signed-in user can be
   changed from the account menu." Neutral state ("not ticked", "Table: no requests in
   this view.") is fine.
3. **No example values.** Nothing with a year or a specific date ("such as 30 November
   2026" becomes "a calendar date"), and no example record names or values at all
   (not even permission codes or audit action codes "for example"). Formats such as
   YYYY-MM-DD are fine.
4. **Purpose and destination, not procedure.** No "go back to…", "click X, then…",
   "use X": say what the control is for and where it leads.
5. **Short per-row text.** When many elements share one entry (row links, row
   buttons, sort headings), keep one clear shared description and make it short; the
   harness adds the row's identity, which carries the distinction.

Check with a grep over the built atlas, for example
`\bnot here\b|nothing (on|here)|cannot|can't|\bno \w+ (is|are) (offered|available)`
and `20\d\d`, and justify every remaining hit.

## 6. Live state: `facts_js` and `virtual_controls_js`

Authored text says what a page *is*; facts say what is on it *now*, which is how
the model knows it has arrived. ADIT's four `global_facts_js` report the signed-in
user and role, the highlighted section, the unread and awaiting counts, and the last
toast. Useful page facts: the open dialog's fields as `label = value` with required
ones marked, and whether there are unsaved changes. Run every expression live;
delete the ones that only ever return null; never let one throw or write; find
table columns by header, not by index.

Virtual controls are for widgets that are not DOM elements. Verify `set` against the
application's own change tracking (a Save button becoming enabled), on a freshly
loaded page.

## 7. The blind-author rule

The author of the atlas must not see the tasks it will be measured on. ADIT's goals
live in `../goals/`, which authors are told not to read; seven authors each wrote one
area's fragment (`../atlas/parts/`), and [`../tools/merge.py`](../tools/merge.py)
combines them by rule, never by hand-editing the JSON.

Blindness is not the whole of it: fixes found by watching one task fail, over and
over, converge on that task even with zero leaked values. So mark goals as
**tuning** or **held-out** before you start (ADIT: 2 tuning, 6 held-out), report a
tuning goal's success as what it is, and say how many times the atlas changed while
watching a task fail.

## 8. Side effects

Runs change data. Agree before running anything n times: where the mess goes (a
throwaway record or a resettable tenant), the teardown, which controls are
dangerous (anything that changes settings for other users, submits or overwrites),
and what the author will not open at all. The atlas describes dangerous controls
plainly; it does not hide them. ADIT sidesteps most of this: every run starts from a
reset tenant in its own browser profile.

## 9. Evaluate it

1. **Freeze the atlas** during measured runs; `run.json` records its version and a
   12-character sha256.
2. **Two conditions identical but for `JEV_ATLAS`**: same start URL, goal and harness
   build. [`../run.sh`](../run.sh) and [`../inspect.sh`](../inspect.sh) set it per
   condition.
3. **n ≥ 10 per cell**; close top-two probabilities flip between runs.
4. **Held-out goals**, never tuned on.
5. **Check the outcome in code**, not by the agent's DONE: ADIT's `goals/check.py`
   reads the tenant from localStorage after each run.
6. **Report the versioned model** that answered (`model` in `run.json`, e.g.
   `jev-1.13.0`), never "jev-latest".
7. **Keep a run table**: every run, in order, with the atlas and harness state at
   the time.

`python3 jev-atlas/tools/summarize_runs.py --runs <runs tree>` prints one table per
run from the logs.

## 10. Checklist

- [ ] Documentation mirrored to text, with source and date; credentials stripped and
      the stripping verified.
- [ ] Browser with its own DevTools port and profile; no credential through the author.
- [ ] Areas agreed; safe data and dangerous controls agreed; tasks not seen by the
      author, and goals split into tuning and held-out.
- [ ] Inventory per page and per overlay; stable keys identified; non-DOM widgets found.
- [ ] A page entry per route and per overlay; keys down the cascade; generic keys
      carry a `note`.
- [ ] Whole-app check: annotated / offered, zero misplaced entries; overlay selectors
      tested closed / open / closed.
- [ ] Every `facts_js` run live; `set` verified against the app's change tracking.
- [ ] No procedure, record, amount, year or code anywhere; grep for the obvious
      tokens and say you did.
- [ ] Wording rules of §5 applied: no refusal wording in `not_here`/`not_for`/facts,
      no example values, per-row text short; grep counts reported.
- [ ] Atlas frozen; both conditions, n ≥ 10, held-out goals, outcome checked in code,
      versioned model and run count reported.
- [ ] An atlas README: how it was made, what it covers, what it does not and why.
