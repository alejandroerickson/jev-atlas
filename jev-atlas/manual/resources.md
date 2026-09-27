Source: https://alejandroerickson.com/mockent/adit/#/manual/resources
Fetched: 2026-09-22

8. Resources
ADIT User Manual · Release 7.4 · Section 8 of 13

Resources holds resource estimates and what they are worth under the corporate price deck.

Estimates

An estimate belongs to a project and has an as-of date, a method, a cut-off, an author, a reviewer and one block per category: measured, indicated and inferred, each with tonnes, grade and contained metal. Statuses run draft → internal-review → qp-review → released; an estimate replaced by a later one is superseded. Only released estimates count in the portfolio figures.

New estimate (permission resource.write) takes the project, method, cut-off and the indicated and inferred blocks; measured blocks are entered by the database geologist after QP review. The estimate is saved as a draft.

Releasing an estimate

On a draft, Submit for release raises the resource-release workflow: Database sign-off (Database Geologist) → QP review (Project Geologist) → Manager release (Exploration Manager). The estimate moves to internal review while it runs and to released when the last step is approved. Change status moves an unreleased estimate between draft, internal review and QP review, or marks it superseded, and sets the reviewer.

Value and forecast
Portfolio resources
In-situ value at the deck for every project with a released estimate, by project, commodity and category.
In-situ value
The same with a price factor and a uniform recovery applied, for screening. No costs are deducted.
Forecast
P10, P50 and P90 contained metal for the latest estimate on each project.
Price deck
The price and unit for each commodity, its source and date, and the default cut-off. Administrators edit it; every valuation changes at once.
Copper is priced per pound. ADIT converts at 2,204.62 lb per tonne when it values contained copper.
← 7. Assays
9. Approvals →

© Brannock Geosystems. ADIT is a trademark of Brannock Geosystems. This document describes release 7.4 and is superseded by the release notes for any later version.
