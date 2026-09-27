Source: https://alejandroerickson.com/mockent/adit/#/manual/drilling
Fetched: 2026-09-22

6. Drilling
ADIT User Manual · Release 7.4 · Section 6 of 13

Drilling holds every drillhole in the tenant, across projects and programmes.

Hole statuses
STATUS	MEANING
planned	Collar designed; not started.
drilling	Rig on the hole.
completed	Reached target depth; not yet logged.
abandoned	Stopped short of three quarters of planned depth (lost hole, ground conditions).
logged	Geological logging done; awaiting sampling and dispatch.
sampled	Samples cut and dispatched; results pending.
assayed	Results received and the batch accepted. Intercepts are computed.
The hole list

Filter by hole id, project and hole type (DDH diamond, RC reverse circulation, AC aircore, Sonic). The left column cuts to holes drilling now, planned, awaiting sampling (logged) or abandoned. Columns give collar coordinates, azimuth and dip, planned and actual depth, the best intercept and the completion date. The column chart at the top shows holes completed by month, by commodity.

The hole record

Depth against plan, collar and orientation, sample counts, the best intercept, the rig and the logger, the batches the hole's samples went in. The downhole grade profile draws every assayed interval; intervals at or above cut-off are solid, below are dim, and the dashed line is the cut-off. The intercepts table lists runs above cut-off (one sample of internal dilution allowed); a significant intercept is at least one and a half times cut-off over the commodity's minimum length. The samples table lists every interval with its primary grade, secondary elements and any QAQC flag.

Update hole (permission hole.write) changes status, depth and completion date.

Intercepts

Significant intercepts in the left column lists intercepts across the tenant, sorted by grade × length, with a scatter of length against grade over cut-off. Untick Significant only to see everything above cut-off.

← 5. Programmes
7. Assays →

© Brannock Geosystems. ADIT is a trademark of Brannock Geosystems. This document describes release 7.4 and is superseded by the release notes for any later version.
