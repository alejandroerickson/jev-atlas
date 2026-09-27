Source: https://alejandroerickson.com/mockent/adit/#/manual/approvals
Fetched: 2026-09-22

9. Approvals
ADIT User Manual · Release 7.4 · Section 9 of 13

Approvals is the queue of workflow requests. Each request follows the steps of its workflow, and each step is owned by a role.

Workflows
WORKFLOW	RAISED FOR	STEPS
Programme approval	A costed programme	Technical review → Budget check → Manager approval
Budget variance	A forecast overrun above the threshold	Finance review → Manager approval
Stage-gate decision	A project at the end of a stage	Geology recommendation → Finance review → Gate decision
Land access agreement	Access to private or community land	Tenure review → Manager sign-off
Work permit	Ground disturbance	Permit lodgement → Regulator decision
Resource estimate release	An estimate leaving review	Database sign-off → QP review → Manager release
Tenement renewal	A tenement before expiry	Expenditure check → Renewal lodgement
Purchase order	Orders above the delegated limit	Logistics check → Finance approval
The queue

Awaiting me lists requests whose current step belongs to your role; the four most urgent are shown as tickets, the lead ticket first. All pending, Raised by me and Decided are the other cuts, and the left column also cuts by workflow. Each step has a service level in days; a request past its due date is marked overdue and appears in the Portfolio attention ledger.

Deciding

Open the request. If the current step is yours, the head offers Approve, Return and Reject.

Approve passes the step. The request moves to the next step and its owner is notified; on the last step the request is approved and its subject is updated (a programme becomes approved, an estimate released, a tenement's renewal lodged).
Return sends the request back to the requester to revise. A reason is required.
Reject ends the workflow. A reason is required and is sent to the requester.

A requester can Withdraw their own pending request. Comments on a request notify the requester. Every decision is written to the audit log with its note.

← 8. Resources
10. Optimiser →

