# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

BASE = "https://alejandroerickson.com/mockent/adit/"
PGEO = "u-twierzbicki"; SYS = "u-abarrientos"
SCENARIOS = {
 "resources": {"route": "/resources"},
 "estimates": {"route": "/resources/estimates"},
 "estimates-pgeo": {"route": "/resources/estimates", "user": PGEO},
 "estimates-review": {"route": "/resources/estimates?status=review"},
 "estimate-released": {"route": "/resources/estimates/RES-2026-01"},
 "estimate-draft-pgeo": {"route": "/resources/estimates/RES-2026-05", "user": PGEO},
 "new": {"route": "/resources/estimates/new", "user": PGEO},
 "forecast": {"route": "/resources/forecast"},
 "price-deck": {"route": "/resources/price-deck"},
 "price-deck-sys": {"route": "/resources/price-deck", "user": SYS},
 "valuation": {"route": "/resources/valuation"},
 "optimiser": {"route": "/optimiser"},
 "scenarios": {"route": "/optimiser/scenarios"},
 "targets": {"route": "/optimiser/targets"},
}
SCENARIOS.update({
 "submit-dlg": {"route": "/resources/estimates/RES-2026-05", "user": PGEO, "steps": [("click", "button:has-text('Submit for release')")]},
 "status-dlg": {"route": "/resources/estimates/RES-2026-05", "user": PGEO, "steps": [("click", "button:has-text('Change status')")]},
 "method": {"route": "/resources/estimates/RES-2026-05", "user": PGEO, "steps": [("click", "button.authority"), ("click", "summary")]},
 "mention": {"route": "/resources/estimates/RES-2026-05", "steps": [("fill", "textarea", "@Ti")]},
 "deck-edit": {"route": "/resources/price-deck", "user": SYS, "steps": [("click", "button:has-text('Edit deck')")]},
 "optimiser-save": {"route": "/optimiser", "steps": [("click", "button:has-text('Save scenario')")]},
})
SCENARIOS.update({
 "method": {"route": "/resources/estimates/RES-2026-05", "user": PGEO, "steps": [("click", "button.authority"), ("click", "main summary")]},
 "mention": {"route": "/resources/estimates/RES-2026-05", "steps": [("click", "textarea"), ("eval", "0"), ("press", "@"), ("press", "T")]},
})
SCENARIOS.update({
 "scenarios-saved": {"route": "/optimiser", "steps": [("click", "button:has-text('Save scenario')"), ("fill", "dialog[open] input", "shimtest"), ("click", "dialog[open] button:has-text('Save')"), ("goto", "/optimiser/scenarios")]},
 "optimiser-table": {"route": "/optimiser", "steps": [("eval", "document.querySelector('h2 ~ *, section.panel:last-of-type') && [...document.querySelectorAll('h2')].find(h=>h.innerText.includes('Candidate targets')).scrollIntoView()")]},
 "optimiser-table2": {"route": "/optimiser", "steps": [("eval", "window.scrollTo(0, document.body.scrollHeight)")]},
})
SCENARIOS.update({
 "optimiser-excluded": {"route": "/optimiser", "steps": [("eval", "[...document.querySelectorAll('button')].find(b=>b.innerText==='Exclude').click()"), ("eval", "window.scrollTo(0,0)")]},
 "method": {"route": "/resources/estimates/RES-2026-05", "user": PGEO, "steps": [("click", "button.authority"), ("click", "main details.values summary")]},
})
SCENARIOS.update({
 "submit-closed": {"route": "/resources/estimates/RES-2026-05", "user": PGEO, "steps": [("click", "button:has-text('Submit for release')"), ("click", "dialog[open] button:has-text('Cancel')")]},
 "status-closed": {"route": "/resources/estimates/RES-2026-05", "user": PGEO, "steps": [("click", "button:has-text('Change status')"), ("press", "Escape")]},
 "deck-closed": {"route": "/resources/price-deck", "user": SYS, "steps": [("click", "button:has-text('Edit deck')"), ("click", "dialog[open] button[aria-label='Close dialog']")]},
 "save-closed": {"route": "/optimiser", "steps": [("click", "button:has-text('Save scenario')"), ("click", "dialog[open] button:has-text('Cancel')")]},
 "menus-open": {"route": "/optimiser", "steps": [("click", "button[aria-label*='Account menu']")]},
 "notif-open": {"route": "/resources/estimates", "steps": [("click", "button[aria-label^='Notifications']")]},
 "new-saved": {"route": "/resources/estimates/new", "user": PGEO, "steps": [("fill", "main form fieldset input >> nth=0", "5")]},
 "est-notfound": {"route": "/resources/estimates/RES-9999-99"},
})
