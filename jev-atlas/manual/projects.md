Source: https://alejandroerickson.com/mockent/adit/#/manual/projects
Fetched: 2026-09-22

4. Projects
ADIT User Manual · Release 7.4 · Section 4 of 13

A project is an exploration property: one commodity, one jurisdiction, one or more tenements, a stage in the pipeline and a budget for the fiscal year.

The register

Projects lists active projects by default. The left column cuts the register to on-hold or closed projects, to one commodity, or to one stage. The Find box matches id, name or jurisdiction. Columns include the project geologist (a dashed vacant chip when the role is unfilled), area under tenure, budget, spent with a progress bar, forecast against budget and the next gate date.

Creating a project

New project asks for a name, commodity, jurisdiction, country, area, fiscal-year budget, project geologist and description. New projects start at Reconnaissance and are numbered by the tenant's auto-numbering rule. You need the project.write permission.

The project record
TAB	WHAT IT HOLDS
Overview	Budget, area, holes, significant intercepts and the latest estimate; the description, the team, the stage history; recent programmes; open items (pending approvals, batches on hold, expiring tenements); comments.
Tenure	Every tenement with its type, holder, expiry, area, annual expenditure commitment, spend against it and rent due. Lodge renewal starts the tenement-renewal workflow.
Programmes	The project's programmes, all phases. New programme opens the programme form with this project selected.
Drilling	Hole counts and metres, the best intercept, and the hole table.
Assays	The project's sample batches.
Resource	The latest released estimate (or the latest of any status), its categories, in-situ value at the price deck and the P10/P50/P90 forecast; the estimate history.
Budget	The project ledger, spend by month against plan, programme budgets by type, and the programme ledgers.
Approvals	Every request raised on the project.
Activity	The audit trail for the project and its records.
Comments

Most records have a comments panel at the foot of their overview. Type @ and a colleague's first name to notify them. The project manager and project geologist are notified of every comment on their project.

Stage-gate decisions

A project leaves a stage by a stage-gate decision. Users with the gate.decide permission (the Exploration Manager by default) press Stage-gate decision on the project and choose one of:

Advance to the next stage. From the Stage-gate decision stage, advancing hands the project to the development group and closes it in ADIT with the outcome advanced.
Place on hold at the current stage, or Resume a held project.
Relinquish: close the project, lapse its tenure at the next expiry and make its records read-only.

A reasoning of at least twenty characters is required and is written verbatim to the audit log. Where the decision needs a formal review first, raise a stage-gate approval request from Approvals (section 9); the gate pack and recommendation travel with it and the decision itself is then recorded here.

Editing

Edit changes the name, description, project geologist, next gate date and year-end forecast. Budget, commodity and jurisdiction are set at creation and changed by support.

← 3. Portfolio
5. Programmes →

© Brannock Geosystems. ADIT is a trademark of Brannock Geosystems. This document describes release 7.4 and is superseded by the release notes for any later version.
