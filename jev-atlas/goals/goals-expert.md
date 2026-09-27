# ADIT expert goal set (E1–E12)

The eight goals in [`goals.md`](goals.md) are deliberately vague and informal.
Alejandro's feedback (2026-09-22) was that real expert users of an enterprise
system don't talk like that. They name records by code (PRJ-####, WF-…, hole,
batch and estimate ids) or by full title, use the system's own words for tabs and
actions, and give exact values. This set is written that way. Each goal reads like
something a competent user would type to an assistant: one or two sentences,
specific, and not a list of clicks. Together the goals cover every section of the
app except the Optimiser and Admin.

The same rules as `goals.md` apply. Keep this folder away from whoever writes the
shim. Every run starts at `#/portfolio` on a freshly reset tenant, signed in as
Marguerite Okonkwo (Exploration Manager). All twelve goals are split `expert`
(held-out).

**Switching user.** Seven goals need a user other than Marguerite, because her
role (EXM) lacks `tenement.write`, `programme.write`, `hole.write`,
`resource.write`, `qaqc.review` and `crew.assign`, and the Budget check step
belongs to Finance. Each of these goals names the user to act as ("As Hamish
Ferrier, …"), because an expert would. That is more than the three switching goals
that were asked for: the role permissions leave no other way to cover those
sections. The remaining five run as Marguerite.

**Verified.** On 2026-09-22 each goal was carried out once through the live app's
own controls over the DevTools protocol, with
[`walkthrough_expert.py`](walkthrough_expert.py) on a throwaway headless Chrome.
Every goal failed its check before the walkthrough and passed after it (12/12),
and the tenant was reset after each one. The checks are in [`check.py`](check.py)
under E1–E12 and read `adit.tenant.v1`. `pass` means every fact in
`details.required` holds: the whole stated end state (exact values and text, the right
record and the right field) and, where the audit log makes it cheap, that the run did
not do the same kind of thing to a wrong record. `side_effects` lists every audit
entry the run added. The checks were tightened on 2026-09-22 (see "Check history" in
[`goals.md`](goals.md)); the walkthrough still passes 12/12.

```
python check.py list | grep '^E'          # the goals
python check.py goal E3                   # one goal's text
python check.py reset; python check.py check E3
python walkthrough_expert.py [E1 ...]     # re-verify completability
python baseline.py --n 3 --set expert --label expert-without   # measure; then python summarize.py expert-without
```

| id | slug | user | section · what it exercises |
|---|---|---|---|
| E1 | comment-batch | Marguerite | Assays · batch page comment panel |
| E2 | gate-hold-reason | Marguerite | Projects · Stage-gate decision dialog, hold with reasoning |
| E3 | lodge-renewal | **Hamish Ferrier** | Project → Tenure tab → Lodge renewal |
| E4 | create-programme | **Tomasz Wierzbicki** | Programmes · New programme form, all fields |
| E5 | reject-request | Marguerite | Approvals · Reject with reason |
| E6 | approve-as-finance | **Yolanda Mbeki** | Approvals · her own step (Budget check) only, with a note |
| E7 | qaqc-hold | **Priya Raghunathan** | Assays · batch review, Place on hold |
| E8 | update-hole | **Tomasz Wierzbicki** | Drilling · hole record, Update hole |
| E9 | create-estimate | **Tomasz Wierzbicki** | Resources · New estimate, blocks by category |
| E10 | edit-gate-forecast | Marguerite | Projects · Edit dialog, two fields |
| E11 | assign-crew | **Declan Sørensen** | Programmes · Assign crew, rotation dates |
| E12 | find-and-report | Marguerite | Find (filter by status on a project's batches), then report as a project comment |

## Goals and pass checks

**E1** — Post a comment on batch LAB-26-04483: "Geostat is re-running OREAS 252 and the ten samples either side; results due 2026-10-02."
Pass: exactly one new comment on batch LAB-26-04483, containing the quoted text (case, whitespace and a trailing full stop ignored), and no comment mentioning OREAS 252 on any other record.

**E2** — Record a stage-gate decision on PRJ-0468 Dunmore Flats: place it on hold at Reconnaissance, reasoning "Waiting on the legacy seismic reprocessing before we commit to DF-01."
Pass: PRJ-0468 is `on-hold` at stage `recon`, its gate audit entries are `gate.hold` only, the recorded reasoning contains the quoted text, and no other project got a gate decision.

**E3** — As Hamish Ferrier, lodge the renewal for tenement NMC 1174648 on PRJ-0387 Bellamy Ridge.
Pass: tenement NMC 1174648 is `renewal-lodged`, exactly one tenement-renewal request has it as subject and Hamish requested it, and no other tenement was touched or renewal submitted.

**E4** — As Tomasz Wierzbicki, create a geochem programme on PRJ-0468 Dunmore Flats called "Soil sampling, northern block", 2027-05-03 to 2027-06-25, budget 85,000 USD, objective "Soil grid on 200 m centres over the northern mineral claims."
Pass: exactly one new programme on PRJ-0468, type `geochem`, the exact name and objective, budget 85000, start 2027-05-03, end 2027-06-25, lead Tomasz (the creator), and no programme created elsewhere.

**E5** — Reject WF-2026-0146 (Scout RC, Copper Hollow) with the reason "Hold the rig spend until the land access agreement WF-2026-0155 is signed."
Pass: WF-2026-0146 is `rejected`, the rejection note contains the quoted reason, and no other request was decided.

**E6** — Switch to Yolanda Mbeki and approve the Budget check on WF-2026-0145 (cyanidation testwork, Wolverine Creek) with the note "Within the FY26 metallurgy allocation."
Pass: WF-2026-0145's Budget check step is `approved`, the audit shows Yolanda approved it, the step's decision note (not a comment) contains the quoted note, the Manager approval step is undecided and the request still `pending`, and no other request was decided.

**E7** — As Priya Raghunathan, place assay batch LAB-26-04464 from Kettle Lake on QAQC hold.
Pass: LAB-26-04464 is `qaqc-hold` (the seed has `received`), Priya made the change, and no other batch was changed.

**E8** — As Tomasz Wierzbicki, update hole WC-DDH-033 to completed at a depth of 362 m, completed 2026-09-22.
Pass: WC-DDH-033 is `completed`, depth 362 and completedOn 2026-09-22 (the seed has it `drilling` at 253 m), Tomasz made the change, and no other hole was changed.

**E9** — As Tomasz Wierzbicki, create a draft resource estimate for PRJ-0409 Kettle Lake: ordinary kriging, cut-off 0.3 % Ni, Indicated 4.2 Mt at 1.35 % Ni and Inferred 6.8 Mt at 1.10 % Ni.
Pass: exactly one new estimate on PRJ-0409, status `draft`, author Tomasz, method `Ordinary kriging`, cutoff 0.3, indicated (4.2, 1.35) and inferred (6.8, 1.1), and no other estimate changed.

**E10** — On PRJ-0409 Kettle Lake, move the next gate to 2027-04-15 and set the year-end forecast to 3,150,000 USD.
Pass: PRJ-0409 has nextGateOn 2027-04-15 and budget.forecast 3150000 (the seed has 2027-02-28 and 3,127,563), its name, stage, status, geologist and planned budget are unchanged, and no other project was edited.

**E11** — As Declan Sørensen, assign Ezra Lindqvist to PRG-2026-025 (Downhole EM, Phase 3 holes) as Geophysicist, rotation 2026-10-05 to 2026-10-19.
Pass: PRG-2026-025's crew has exactly one entry for f-09 (Ezra), role Geophysicist, 2026-10-05 to 2026-10-19; Declan made the assignment; the five seed crew members are kept (six in all); and no other programme's crew changed. Ezra has no overlapping rotation, so the app accepts the assignment.

**E12** — Find every assay batch on QAQC hold for Cerro Azufre (PRJ-0376) and post their batch ids as a comment on the project.
Pass: a new comment on PRJ-0376 whose batch ids are exactly LAB-26-04451 and LAB-26-04452 (the seed's two held Cerro Azufre batches). Naming another batch, for example LAB-26-04483 (on hold, but Sable Dome's), fails; `extra_ids` lists them.
