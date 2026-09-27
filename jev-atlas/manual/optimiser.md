Source: https://alejandroerickson.com/mockent/adit/#/manual/optimiser
Fetched: 2026-09-22

10. Optimiser
ADIT User Manual · Release 7.4 · Section 10 of 13

The programme optimiser chooses which candidate drill targets to fund in the coming season under a budget and a rig-day limit.

Candidate targets

Each target belongs to a project and has a number of holes, metres, cost, rig days, a probability of success, the in-situ value it would add if successful, and the earliest date it can start. Candidate targets in the left column lists them. Targets are maintained by project geologists with support's help.

Running it

Set the budget, rig days, objective (expected value, metres tested, or probability of success) and, if wanted, a minimum number of targets per commodity. The selection recomputes as you change them. The stamp shows the expected value, cost, rig days and metres of the selection; the table marks each target selected or gives the reason it is not (budget exhausted, rig days exhausted). Lock forces a target in whenever it fits; Exclude removes it from consideration for this run.

The method is stated under the stamp: locked targets first, then the best expected value per dollar until a constraint binds, then pairwise swaps that improve the objective. It does not model rig type, seasonal windows or shared mobilisation; treat the result as a starting point for the programme plan.

Scenarios

Save scenario stores the constraints and the selection under a name. Saved scenarios lists them with who saved them and when, and can delete them.

← 9. Approvals
11. Administration →

© Brannock Geosystems. ADIT is a trademark of Brannock Geosystems. This document describes release 7.4 and is superseded by the release notes for any later version.
