Source: https://alejandroerickson.com/mockent/adit/#/manual/assays
Fetched: 2026-09-22

7. Assays
ADIT User Manual · Release 7.4 · Section 7 of 13

Assays holds sample batches: the dispatches of samples to a laboratory, the results that come back, and the quality checks on them.

Batch lifecycle
STATUS	MEANING
submitted	Dispatched; the laboratory has not confirmed receipt.
in-prep	Crushing and pulverising.
analysing	At the instrument.
received	Results imported; QAQC checks run; awaiting review.
qaqc-hold	A check failed and the batch is withheld from intercepts and estimates.
accepted	Reviewed and released. Holes move to assayed.
rejected	Returned to the laboratory for re-assay.
Dispatching samples

New dispatch: choose the project and laboratory, tick the logged holes to include, and submit. Sample numbers are assigned on dispatch. Control samples are inserted at the tenant rule of one standard, one blank and one field duplicate per twenty samples. The holes move to sampled.

Reviewing a batch

The batch page shows the sample count, insertions, insertion rate, failures, the share above cut-off and the turnaround against the laboratory's quoted days. Each QAQC failure is listed with the sample, the kind of check and what was measured against what was expected. Users with qaqc.review (the Database Geologist) can:

Import results on a batch still at the laboratory, which runs the checks and moves it to received.
Accept batch, confirming each failure has been reviewed.
Place on hold while the laboratory re-runs the failed checks.
Reject, with the reason sent to the laboratory.

The project geologist and database geologist are notified of every status change.

Tolerances

A standard fails when it is outside the tenant's sigma tolerance of its certified value. A blank fails above a multiple of the detection limit. A field duplicate fails when its half absolute relative difference is above the limit, for pairs above cut-off. The values are set under Admin → QAQC tolerances (section 11).

QAQC summary and the sample register

QAQC summary gives the pass rate by month, failures by project and the record by laboratory (checks, failures, pass rate, mean against quoted turnaround). Sample register lists every sample in the tenant; narrow by id, project and type before paging.

← 6. Drilling
8. Resources →

© Brannock Geosystems. ADIT is a trademark of Brannock Geosystems. This document describes release 7.4 and is superseded by the release notes for any later version.
