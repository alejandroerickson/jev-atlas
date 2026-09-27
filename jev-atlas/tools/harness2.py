"""Second-round rules for the merged ADIT atlas: the upgraded harness (2026-09-22).

merge.py calls `upgrade()` after it has assembled the controls. Every change here is a
rule over the fragments' entries, never hand-edited JSON. What the harness added, and
what this file does with it (the contract is harness/ATLAS-FORMAT-ADDENDUM.md):

- `href` keeps '#/route' fragments: the page-scoped catch-all regexes ("any link that
  is not a chrome label is a record name") become one entry per route the page links
  to, keyed by `href_regex`. The Portfolio registers' project-name links, which had no
  entry, get one the same way.
- `row_label` in a table row is now the row's identifying cells, not the nearest label:
  entries that keyed a row by a label the reader no longer reports (the Portfolio
  "Needs attention" ledger, search result kinds, notification read state, the
  approval status chip) are rekeyed by route, `section` or `row_label_regex`.
- identical row buttons (Lock, Locked, Exclude, Update, Remove, Edit) are keyed with the
  row identity the reader now reports, and their descriptions say how rows differ.
- `landmark` separates the top bar, the breadcrumb, the footer and the account menu.
- native date inputs and visually hidden radios/checkboxes are offered by the reader, so
  the virtual controls that stood in for them are dropped and the native controls get
  entries (each verified live: offered, fillable or clickable, value kept on Save).
"""
import copy
import re

ID = {"PRJ": r"PRJ-\d+", "PRG": r"PRG-\d+-\d+", "WF": r"WF-\d+-\d+", "LAB": r"LAB-\d+-\d+", "RES": r"RES-\d+-\d+"}
PROJECT = f"#/projects/{ID['PRJ']}$"
PROGRAMME = f"#/programmes/{ID['PRG']}$"
APPROVAL = f"#/approvals/{ID['WF']}$"
BATCH = f"#/assays/{ID['LAB']}$"
ESTIMATE = f"#/resources/estimates/{ID['RES']}$"

# What a link to each kind of record does, said once.
OPENS = {
    PROJECT: "opens that project's record (Overview tab) in Projects",
    PROGRAMME: "opens that programme's page (Overview tab) in Programmes",
    APPROVAL: "opens that approval request in Approvals, where it is decided",
    BATCH: "opens that sample batch in Assays",
    ESTIMATE: "opens that resource estimate in Resources",
}


# ---------------------------------------------------------------- catch-alls by route
# (area, page) -> the routes its catch-all actually covered in the whole-app check, each
# with its own description. The entry keeps the catch-all's region unless one is given.
CATCH_ALL_ROUTES = {
    ("projects", "projects-register"): [
        (PROJECT, "A project (id or name): " + OPENS[PROJECT] + ".",
         "Filtering the register (the left column and the filter bar do that)."),
    ],
    ("projects", "project-overview"): [
        (PROGRAMME, "A programme of this project, in the Programmes panel: " + OPENS[PROGRAMME] + ".",
         "The project's own Programmes tab (the tab row), which lists every programme with its figures.", "Overview, Programmes panel"),
        (APPROVAL, "An open approval request on this project, in the Open items panel: " + OPENS[APPROVAL] + ".",
         "Deciding it: the request's own page in Approvals.", "Overview, Open items panel"),
    ],
    ("projects", "project-programmes"): [
        (PROGRAMME, "A programme of this project: " + OPENS[PROGRAMME] + ".", "Opening the project (it is the page you are on)."),
        (PROJECT, "The project named in the Project column (this project): opens its Overview tab.", "Opening a programme (the programme name in the same row)."),
    ],
    ("projects", "project-drilling"): [
        (PROJECT, "The project named in the Project column (this project): opens its Overview tab.", "Opening a drillhole (the hole id in the same row)."),
    ],
    ("projects", "project-assays"): [
        (PROJECT, "The project named in the Project column (this project): opens its Overview tab.", "Opening a sample batch (the batch id in the same row)."),
    ],
    ("projects", "project-budget"): [
        (PROGRAMME, "A programme in the ledger table: " + OPENS[PROGRAMME] + ".", "Changing a budget: budgets are set at creation and changed by support."),
        (PROJECT, "The project named in the Project column (this project): opens its Overview tab.", "Opening a programme (the programme name in the same row)."),
    ],
    ("projects", "project-approvals"): [
        (APPROVAL, "An approval request on this project: " + OPENS[APPROVAL] + ".", "Deciding it: the request's own page in Approvals."),
    ],
    ("programmes", "programmes-list"): [
        (PROGRAMME, "A programme's name in a row: " + OPENS[PROGRAMME] + ", the same as its id.", "Opening the project (the project name in the same row)."),
        (PROJECT, "The project a programme belongs to: " + OPENS[PROJECT] + ".", "Opening the programme (its id or name in the same row). Filtering this list: phase group (left column) and programme type."),
    ],
    ("programmes", "programmes-schedule"): [
        (PROGRAMME, "A programme on the timeline: " + OPENS[PROGRAMME] + ".", "Moving or rescheduling it: dates are set on the programme's own page."),
    ],
    ("programmes", "programmes-rigs"): [
        (PROGRAMME, "The programme this row's rig is on: " + OPENS[PROGRAMME] + ".", "Updating the rig (the Update button in the same row)."),
    ],
    ("programmes", "programmes-camps"): [
        (PROJECT, "The project this row's camp serves: " + OPENS[PROJECT] + ".", "Changing the camp itself."),
    ],
    ("programmes", "programmes-crew-rotations"): [
        (PROGRAMME, "The programme this rotation belongs to: " + OPENS[PROGRAMME] + ", where crew are assigned or removed.", "Changing the rotation from this list."),
    ],
    ("programmes", "programme-overview"): [
        (PROJECT, "The project this programme belongs to (under the title, and in tables): " + OPENS[PROJECT] + ".", "Moving the programme to another project: a programme's project is fixed when the programme is created."),
        ("#/programmes/camps$", "The camp that serves this programme: opens the Camps list in Programmes.", "Changing the camp."),
    ],
    **{("programmes", p): [
        (PROJECT, "The project this programme belongs to (under the title, and in tables): " + OPENS[PROJECT] + ".", "Moving the programme to another project: a programme's project is fixed when the programme is created."),
    ] for p in ("programme-crew", "programme-logistics", "programme-holes", "programme-approval")},
    ("drilling-assays", "drilling-list"): [
        (PROJECT, "The project this row's hole belongs to: " + OPENS[PROJECT] + ".", "Opening the hole (its hole id in the same row)."),
    ],
    ("drilling-assays", "drilling-intercepts"): [
        (PROJECT, "The project this row's intercept is in: " + OPENS[PROJECT] + ".", "Opening the hole (the Hole column)."),
    ],
    ("drilling-assays", "drilling-hole"): [
        (PROJECT, "The project this hole belongs to (under the hole id): " + OPENS[PROJECT] + ".", "Opening its drilling programme (the programme link beside it)."),
        (PROGRAMME, "The drilling programme this hole belongs to (under the hole id): " + OPENS[PROGRAMME] + ".", "Opening its project (the project link beside it)."),
    ],
    ("drilling-assays", "assays-batches"): [
        (PROJECT, "The project this row's batch belongs to: " + OPENS[PROJECT] + ".", "Opening the batch (its batch id in the same row)."),
    ],
    ("drilling-assays", "assays-qaqc"): [
        (f"#/projects/{ID['PRJ']}/assays$", "A project in the By project table: opens that project's Assays tab in Projects.", "Opening a batch; changing tolerances (Administration)."),
        (r"#/assays\?(.*&)?lab=", "A laboratory in the By laboratory table: opens the sample batch list filtered to that laboratory.", "Changing tolerances (Administration)."),
    ],
    ("drilling-assays", "assays-batch"): [
        (PROJECT, "The project this batch belongs to (under the batch id): " + OPENS[PROJECT] + ".", "Opening the samples' holes (the hole links in the tables)."),
    ],
    ("resources-optimiser", "resources-portfolio"): [
        (f"#/projects/{ID['PRJ']}/resource$", "A project in the released estimates table: opens that project's Resource tab in Projects.", "Opening the estimate itself (Estimates in the left column)."),
    ],
    ("resources-optimiser", "resources-estimates"): [
        (PROJECT, "The project this row's estimate belongs to: " + OPENS[PROJECT] + ".", "Opening the estimate (its id in the same row)."),
    ],
    ("resources-optimiser", "resources-forecast"): [
        (ESTIMATE, "The project named in a forecast row: opens the estimate that row is taken from (the latest estimate on that project).", "Changing the forecast; it is computed."),
    ],
    ("resources-optimiser", "resources-valuation"): [
        (ESTIMATE, "The project named in a valuation row: opens the released estimate valued in that row.", "Changing the value; it is computed from the inputs above the table."),
    ],
    ("resources-optimiser", "optimiser"): [
        (PROJECT, "The project this row's target is on: " + OPENS[PROJECT] + ".", "Locking or excluding the target (the buttons at the end of the same row)."),
    ],
    ("resources-optimiser", "optimiser-targets"): [
        (PROJECT, "The project this row's target is on: " + OPENS[PROJECT] + ".", "Changing the target: targets are maintained by project geologists with support."),
    ],
}

# ---------------------------------------------------------------- Portfolio (portfolio-global)
LEDGER_REGION = "Needs attention ledger (kind, item, due date, current step on one line)"
LEDGER_NOT_FOR = "Acting on the item: the record it opens."
PORTFOLIO_NEW = [
    # The ledger: each kind is told apart by where it links (and a vacancy by the colon in
    # its text). Written when the reader gave every ledger link the first line's kind as its
    # row label; since the third round (2026-09-22) it gives the link's own line, and the
    # route keys still hold.
    {"key": {"page": "portfolio", "section": "Needs attention", "role": "link", "href_regex": APPROVAL},
     "region": LEDGER_REGION,
     "what": "An approval request that is overdue or due soon (the kind to its left says which; the step it waits on is at the end of the line): " + OPENS[APPROVAL] + ".",
     "not_for": LEDGER_NOT_FOR},
    {"key": {"page": "portfolio", "section": "Needs attention", "role": "link", "href_regex": f"#/projects/{ID['PRJ']}/tenure$"},
     "region": LEDGER_REGION,
     "what": "A tenement expiring soon (tenement number, then its project): opens that project's Tenure tab, where a renewal is lodged.",
     "not_for": LEDGER_NOT_FOR},
    {"key": {"page": "portfolio", "section": "Needs attention", "role": "link", "href_regex": BATCH},
     "region": LEDGER_REGION,
     "what": "A sample batch on QAQC hold (batch id, then its project): " + OPENS[BATCH] + ", where it is reviewed.",
     "not_for": LEDGER_NOT_FOR},
    {"key": {"page": "portfolio", "section": "Needs attention", "role": "link", "href_regex": PROGRAMME},
     "region": LEDGER_REGION,
     "what": "A programme past its budget variance threshold: " + OPENS[PROGRAMME] + ".",
     "not_for": LEDGER_NOT_FOR},
    {"key": {"page": "portfolio", "section": "Needs attention", "role": "link", "href_regex": PROJECT, "text_regex": r":\s"},
     "region": LEDGER_REGION,
     "what": "A vacancy: a project with a role nobody fills (project, then the role): " + OPENS[PROJECT] + ".",
     "not_for": LEDGER_NOT_FOR},
    {"key": {"page": "portfolio", "section": "Needs attention", "role": "link", "href_regex": PROJECT},
     "region": LEDGER_REGION,
     "what": "A project whose stage-gate review is due: " + OPENS[PROJECT] + ", where the Stage-gate decision is recorded.",
     "not_for": LEDGER_NOT_FOR},
    {"key": {"page": "portfolio", "section": "Active projects", "role": "link", "href_regex": PROJECT},
     "region": "Active projects table",
     "what": "A project (id or name): " + OPENS[PROJECT] + ".",
     "not_for": "The full register with filters and closed projects (Full register)."},
    {"key": {"page": "portfolio-budget", "role": "link", "href_regex": f"#/projects/{ID['PRJ']}/budget$"},
     "region": "Budget table, project id column",
     "what": "A project's id: opens that project's Budget tab in Projects (its programme ledgers).",
     "not_for": "Changing a budget (set at creation, changed by support), or the budget-variance requests (Variance requests)."},
    *[{"key": {"page": page, "landmark": "main", "role": "link", "href_regex": PROJECT},
       "region": f"Project register grouped by {by} (one table per {by})",
       "what": "A project (id or name): " + OPENS[PROJECT] + ".",
       "not_for": f"Filtering by {by}; every {by} is listed, each under its own heading."}
      for page, by in (("portfolio-commodity", "commodity"), ("portfolio-jurisdiction", "jurisdiction"))],
]
# Entries dropped because the row label they keyed on is no longer reported.
PORTFOLIO_DROP = [{"page": "portfolio", "row_label": k, "role": "link"} for k in
                  ("Approval overdue", "Approval due", "Tenure expiring", "QAQC hold", "Gate due", "Vacancy")]

# Search results and notifications: the row label is now "kind · detail", "unread · kind ...".
ROW_LABEL_TO_REGEX = {
    **{("search", k): f"^{k}( ·|$)" for k in
       ("project", "programme", "hole", "batch", "sample", "approval", "estimate", "tenement", "user")},
    ("notifications", "unread"): "^unread( ·|$)",
    ("notifications", "read"): "^read( ·|$)",
}

# ---------------------------------------------------------------- approvals
# The request head's project link was keyed by the status chip that preceded it (one entry
# per status); the reader now reports that chip only by accident. One entry, by route.
APPROVAL_STATUS_CHIPS = ("pending", "approved", "returned", "rejected", "withdrawn")

# ---------------------------------------------------------------- landmarks
TOP_SECTIONS = ("Portfolio", "Projects", "Programmes", "Drilling", "Assays", "Resources", "Optimiser", "Admin")
BANNER_TEXT = {"ADIT home", "User Manual (opens in a new tab)"}
BANNER_REGEX = {"^Notifications(,|$)", "Account menu$", "^Switch to the (light|dark) theme$"}
BREADCRUMB = "navigation: Breadcrumb"
BREADCRUMB_SHARED = {
    "key": {"role": "link", "landmark": BREADCRUMB},
    "region": "Breadcrumb above the title",
    "what": "Goes up to the list or section it names, above the record or form this page shows.",
    "not_for": "Saving anything (leaving a form this way discards its unsaved changes), or the top-bar link of the same name (the same list, reached from the top bar).",
}

# ---------------------------------------------------------------- native controls replacing virtual ones
# page -> (why the virtual control is no longer needed, [new entries]).
DATE = "Written as a calendar date (YYYY-MM-DD; other common date spellings are converted)."
NATIVE = {
    "programmes-new": ("native date inputs", [
        {"key": {"page": "programmes-new", "role": "textbox", "text": "Start"}, "region": "New programme form",
         "what": "The programme's planned start date. " + DATE, "not_for": "The end date, which is its own field."},
        {"key": {"page": "programmes-new", "role": "textbox", "text": "End"}, "region": "New programme form",
         "what": "The programme's planned end date. " + DATE, "not_for": "The start date, which is its own field."},
    ]),
    "project-edit-dialog": ("native date input", [
        {"key": {"page": "project-edit-dialog", "role": "textbox", "text": "Next gate"}, "region": "Edit project dialog",
         "what": "The date of the project's next stage-gate review, shown in the project header and the register's Next gate column. " + DATE,
         "not_for": "Recording a stage-gate decision (the Stage-gate decision button on the project). The date is kept when the dialog is saved."},
    ]),
    "programme-assign-crew-dialog": ("native date inputs", [
        {"key": {"page": "programme-assign-crew-dialog", "role": "textbox", "text": "Rotation start"}, "region": "Assign crew dialog",
         "what": "First day of this person's rotation on the programme. " + DATE, "not_for": "The last day, which is Rotation end."},
        {"key": {"page": "programme-assign-crew-dialog", "role": "textbox", "text": "Rotation end"}, "region": "Assign crew dialog",
         "what": "Last day of this person's rotation on the programme. " + DATE, "not_for": "The first day, which is Rotation start."},
    ]),
    "programme-logistics-item-dialog": ("native date input", [
        {"key": {"page": "programme-logistics-item-dialog", "role": "textbox", "text": "Scheduled"}, "region": "Logistics item dialog",
         "what": "The date the item is scheduled for: flight, delivery, service start. " + DATE,
         "not_for": "The cost or status of the item, which are their own fields."},
    ]),
    "update-hole-dialog": ("native date input", [
        {"key": {"page": "update-hole-dialog", "role": "textbox", "text": "Completed"}, "region": "Update hole dialog",
         "what": "The date the hole reached its final depth. " + DATE + " Saved with the dialog.",
         "not_for": "Status or depth (their own fields in the dialog). Clearing it removes the hole's completion date."},
    ]),
    "programmes-list": ("type pills offered as their labels (hidden radios)", [
        {"key": {"page": "programmes-list", "role": "radio"}, "region": "Programme list, type filter above the table",
         "what": "One programme type (drilling, geophysics, geochem and so on). Pressing it lists only programmes of that type; pressing the type already chosen clears the filter, so every type is listed again.",
         "not_for": "Choosing which phase group is listed (in the field, in planning, complete, all), which is the left column; changing the type of a programme."},
    ]),
    "assays-new": ("hole pills offered as their labels (hidden checkboxes)", [
        {"key": {"page": "assays-new", "role": "checkbox"}, "region": "New sample dispatch form, logged holes awaiting dispatch",
         "what": "A logged hole of the chosen project (hole id and metres). Ticked, the hole goes in this dispatch: its samples are numbered and sent to the chosen laboratory when the dispatch is submitted. Pressing it again leaves it out.",
         "not_for": "Choosing the project or laboratory (the selects above); submitting (Submit dispatch). Holes of another project: listed once that project is chosen in Project."},
    ]),
}
EXTRA_NATIVE = [
    # Newly offered hidden radios with no virtual predecessor.
    {"key": {"page": "drilling-intercepts", "role": "radio"}, "region": "Intercepts filters, commodity pills",
     "what": "One commodity. Pressing it shows only intercepts of that commodity; pressing the chosen commodity again shows every commodity. The choice lasts while the page is open.",
     "not_for": "Changing cut-offs (Price deck and cut-offs, under Admin), or the Significant only tick box beside it."},
]
# Two identical labels under the Indicated and Inferred legends: the section tells them apart.
ESTIMATE_CATEGORIES = [
    {"key": {"page": "resources-estimate-new", "row_label": "Tonnes, Mt", "section": cat}, "region": f"New estimate form, {cat} block",
     "what": f"Tonnage of the {cat.lower()} category of the new estimate, in million tonnes. At least one of the two tonnage fields must be above zero for Save draft to work.",
     "not_for": f"The other category's tonnage (its own field under the other heading), grade (the field beside it), or measured tonnes (added by the database geologist after QP review)."}
    for cat in ("Indicated", "Inferred")
] + [
    {"key": {"page": "resources-estimate-new", "text_regex": "^(Open )?Grade,", "section": cat}, "region": f"New estimate form, {cat} block",
     "what": f"Average grade of the {cat.lower()} category, in the unit shown in its label (which follows the project's commodity).",
     "not_for": "The cut-off grade (the Cut-off field), the other category's grade, or tonnage."}
    for cat in ("Indicated", "Inferred")
]

# ---------------------------------------------------------------- identical row buttons
# (page, text) -> extra key fields and a sentence saying how the rows differ. The reader
# gives each button its row's identity, and Jev sees it (`row`) when labels repeat.
ROW_BUTTONS = {
    ("optimiser", "Lock"): ({"row_label_regex": r"(^|· )T-\d+$"},
                            "Its row tells it apart (target status, target id)."),
    ("optimiser", "Locked"): ({"row_label_regex": r"(^|· )T-\d+$"},
                              "Its row tells it apart (target status, target id)."),
    ("optimiser", "Exclude"): ({"row_label_regex": r"(^|· )T-\d+$"},
                               "Its row tells it apart (target status, target id)."),
    ("programmes-rigs", "Update"): ({"row_label_regex": r"^RIG-\d+$"},
                                    "Its row tells it apart (rig id)."),
    ("programme-crew", "Remove"): ({"section": "Crew assignments"},
                                   "Its row tells it apart (person's name)."),
    ("programme-logistics", "Edit"): ({"row_label_regex": r"^LG-\d+$"},
                                      "Its row tells it apart (item id)."),
    ("admin-users", "Edit"): ({"section": "Users"},
                              "Its row tells it apart (account holder's name)."),
}


def _same(key, want):
    return all(key.get(k) == v for k, v in want.items()) and set(key) == set(want)


def upgrade(controls, pages, dialog_overlays, guard_prefix):  # noqa: C901 (one pass, one rule per step)
    """Apply the rules; returns (controls, report). Pages are changed in place (virtual controls)."""
    report = {}
    out = []
    replaced_catch_alls = set()
    for c in controls:
        k = c["key"]
        area, page = c.get("area"), k.get("page")
        tr = k.get("text_regex", "")

        # 1. catch-all record-link regexes -> one entry per route
        if tr.startswith("^" + guard_prefix) and (area, page) in CATCH_ALL_ROUTES:
            for spec in CATCH_ALL_ROUTES[(area, page)]:
                href, what, not_for = spec[:3]
                e = {"key": {"page": page, "role": "link", "href_regex": href}, "region": spec[3] if len(spec) > 3 else c["region"],
                     "what": what, "not_for": not_for, "area": area}
                out.append(e)
            replaced_catch_alls.add((area, page))
            continue

        # 2. Portfolio ledger entries keyed on a row label no longer reported
        if any(_same(k, d) for d in PORTFOLIO_DROP):
            report.setdefault("ledger entries dropped", 0)
            report["ledger entries dropped"] += 1
            if _same(k, PORTFOLIO_DROP[0]):  # the new ledger and register entries go where the first one was
                for e in PORTFOLIO_NEW:
                    out.append(dict(copy.deepcopy(e), area=area))
            continue

        # 3. search kinds and notification read state -> row_label_regex
        if (page, k.get("row_label")) in ROW_LABEL_TO_REGEX and k.get("role") == "link":
            k = c["key"] = {"page": page, "role": "link", "row_label_regex": ROW_LABEL_TO_REGEX[(page, k["row_label"])]}
            report["rekeyed by row_label_regex"] = report.get("rekeyed by row_label_regex", 0) + 1

        # 4. approval head project link: one entry by route instead of one per status chip
        if page == "approval-detail" and k.get("role") == "link" and k.get("row_label") in APPROVAL_STATUS_CHIPS:
            if k["row_label"] != APPROVAL_STATUS_CHIPS[0]:
                continue
            c["key"] = {"page": page, "role": "link", "href_regex": PROJECT, "section_regex": "^(?!Request$|Other requests)"}
            c["what"] = "The project this request belongs to (in the head, after the workflow name and status): " + OPENS[PROJECT] + "."
        if page == "approval-detail" and k.get("row_label") == "Subject":
            k["section"] = "Request"

        # 5. Watching list in the Portfolio left column
        if _same(k, {"row_label": "Watching", "role": "link"}):
            k["landmark"] = "navigation: In this section"

        # 6. landmarks for the top bar and the breadcrumbs
        if area == "portfolio-global" and not page:
            if k.get("role") == "link" and (k.get("text") in TOP_SECTIONS or k.get("text_regex", "").startswith("^Approvals")):
                k["landmark"] = "navigation: Sections"
                c["region"] = "Top bar, section links"
            elif k.get("text") in BANNER_TEXT or k.get("text_regex") in BANNER_REGEX:
                k["landmark"] = "banner"
            elif k.get("text") == "Search the tenant":
                k["landmark"] = "search"
        if c["region"].lower().startswith("breadcrumb") and k.get("role") == "link":
            k["landmark"] = BREADCRUMB
            c["region"] = re.sub(r"\s*\(the (top|main) navigation[^)]*\)", "", c["region"])

        # 7. identical row buttons
        rb = ROW_BUTTONS.get((page, k.get("text")))
        if rb and k.get("role", "button") == "button":
            k.update(rb[0])
            if rb[1] not in c["what"]:
                c["what"] = c["what"].rstrip() + " " + rb[1]

        # 8. estimate categories: the section names the category
        if page == "resources-estimate-new" and (k.get("row_label") == "Tonnes, Mt" or k.get("text_regex") == "^(Open )?Grade,"):
            first = k.get("row_label") == "Tonnes, Mt"
            for e in ESTIMATE_CATEGORIES[:2] if first else ESTIMATE_CATEGORIES[2:]:
                out.append(dict(copy.deepcopy(e), area=area))
            report["estimate category entries"] = report.get("estimate category entries", 0) + 2
            continue

        out.append(c)

    missing = set(CATCH_ALL_ROUTES) - replaced_catch_alls
    assert not missing, f"catch-alls not found: {missing}"
    report["catch-alls replaced by route entries"] = len(replaced_catch_alls)

    # 9. virtual controls the reader now offers natively
    dropped = []
    for pid, (why, entries) in NATIVE.items():
        assert pages[pid].get("virtual_controls_js"), pid
        pages[pid].pop("virtual_controls_js")
        dropped.append(f"{pid} ({why})")
        for e in entries:
            e = copy.deepcopy(e)
            e["area"] = pages[pid]["area"]
            out.append(e)
    for e in EXTRA_NATIVE:
        out.append(dict(copy.deepcopy(e), area=pages[e["key"]["page"]]["area"]))
    report["virtual controls dropped"] = dropped
    report["virtual controls kept"] = sorted(p for p, v in pages.items() if v.get("virtual_controls_js"))
    return out, report
