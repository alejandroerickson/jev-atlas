# ADIT goal set (keep this folder away from whoever writes the shim)

The people writing the ADIT atlas **must not read this folder**. Two goals are
marked `tuning`: they may be shown to the shim authors and used to try an
atlas out. The other six are `held-out`. They are for measuring only.

Every goal is written the way someone would dictate it: the outcome, the record
and the values, but never a control name or a route. Every run starts at
`#/portfolio` with a freshly reset tenant, signed in as Marguerite Okonkwo
(Exploration Manager, the demo tenant's default user). "Me" in a goal means her.

Each goal was carried out once by hand, on 2026-09-22, through the live app's own
controls over the DevTools protocol (clicks and form input, with no state
written directly), and then the tenant was reset. The checker for each goal is in
[`check.py`](check.py), and it reads `adit.tenant.v1` from the browser after the
run. `pass` means every fact in `details.required` holds: the goal's whole stated
end state (the right record, the right field, every value the goal gives) and, where
it is cheap to see in the audit log, that the run did not do the same kind of thing to
a wrong record. Checks were tightened on 2026-09-22 after a G4 run passed with the
wrong programme lead; see "Check history" at the end.

| id | split | pages a person crosses |
|---|---|---|
| G1 new-project | tuning | Portfolio → Projects → New project form → project page |
| G2 gate-hold | held-out | Portfolio → Sable Dome → Stage-gate decision dialog |
| G3 tenure-renewal | held-out | account menu (switch to Hamish) → Wolverine Creek → Tenure tab → Lodge renewal dialog |
| G4 new-programme | held-out | account menu (switch to Kieran) → Copper Hollow → Programmes tab → programme form |
| G5 approve-variance | tuning | Portfolio or Approvals → request page → Approve dialog |
| G6 return-request | held-out | Approvals → request page → Return dialog (reason) |
| G7 release-estimate | held-out | switch to Tomasz → request → Approve; switch back → request → Approve |
| G8 move-gate | held-out | Projects → Lorimer → Edit dialog → Next gate |

## G1 new-project (tuning)

> we just staked some ground up in the yukon, set it up as a new gold project, call it quartz flat, it's about 55 square k's, four hundred thousand for the year and give it to kieran

Pass: exactly one project named "Quartz Flat" (case-insensitive) with commodity
Au, project geologist Kieran Holloway, budget 400,000, jurisdiction containing
Yukon, country Canada and area 55; no other project created or edited.

## G2 gate-hold (held-out)

> sable dome's gate is coming up and i don't want to hand it over yet, the phase two results were too thin, just park it where it is for now

Pass: PRJ-0433 Sable Dome has status `on-hold` and is still at stage `decision`
("park it where it is"), its only gate audit entries are `gate.hold`, and no other
project got a gate decision.

## G3 tenure-renewal (held-out)

> can you do hamish's job for a sec, the wolverine creek claim that runs out end of november, get the renewal going on it

Pass: tenement 382742 (Wolverine Creek, expires 2026-11-28) has status
`renewal-lodged`, there is exactly one tenement-renewal request whose subject is
382742 and Hamish requested it, and no other tenement was touched or renewal
submitted. Only the Tenure & Permitting Officer sees Lodge renewal, so the agent
has to switch user from the account menu.

## G4 new-programme (held-out)

> kieran wants a mapping program on copper hollow in the spring, northern claims, about 120 grand, april through may, set it up under his name

Pass: exactly one new programme on PRJ-0441 Copper Hollow, type `mapping`, budget
120,000, lead Kieran Holloway, starting in April 2027 and ending in May 2027, and no
programme created elsewhere. The programme form has no lead field: the lead is
whoever creates it, so the agent has to switch to Kieran. (Marguerite can reach a
New programme form from the Programmes section, and one run that did so passed
the old check with her as lead.)

## G5 approve-variance (tuning)

> tomasz answered yolanda's question on the mount aster overrun so go ahead and sign that off

Pass: WF-2026-0152 (Budget variance, Mount Aster) has status `approved`, its
Manager approval step was approved by Marguerite, and no other request was decided.

## G6 return-request (held-out)

> the copper hollow scout RC request, bounce it back to kieran, i want the rig costs broken out before i say yes

Pass: WF-2026-0146 (Programme approval, Scout RC, Copper Hollow) has status
`returned`, the return note mentions the rig, and no other request was decided.

## G7 release-estimate (held-out)

> bellamy ridge's maiden resource has to go out this week, tomasz has finished his QP review so do his step as him and then release it as me

Pass: estimate RES-2026-03 has status `released`, WF-2026-0159 is `approved`, the
audit shows the QP review approved by Tomasz and the Manager release approved by
Marguerite, and no other request was decided.

## G8 move-gate (held-out)

> lorimer's gate is slipping, move it to the end of january

Pass: PRJ-0421 Lorimer's next gate date is 2027-01-25 to 2027-01-31, its name,
stage, status, geologist, planned budget and forecast are unchanged, and no other
project was edited. Details: exactly 2027-01-31.

## Side effects

`check.py` also lists every audit entry the run added, except sign-ins. That
shows collateral actions, for example approving the wrong request or posting a
comment instead of deciding, and those are counted in the failure modes.

## Check history

On 2026-09-22 every G and E check was tightened to require all of the goal's stated
end state, plus "no same-kind change to a wrong record" read from the run's audit
entries (see the comment above `check_world` in `check.py`). Both walkthroughs still
pass 20/20. Runs are saved without the final tenant, so old results could only be
re-scored from the fields each result row kept (`details` and `side_effects`); on
those, two earlier passes would now fail: G4 rep 0 in `g-with-h3` (lead Marguerite,
not Kieran) and E6 rep 2 in `e-without-h3` (the note was not in the Budget check
decision note). The stored `pass` values in `results/` were not rewritten. The G8 and
E10 "other fields unchanged" facts could not be re-checked for old runs.
