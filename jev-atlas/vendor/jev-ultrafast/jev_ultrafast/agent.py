"""The complete agent loop. Typed choices, observable state, bounded execution."""

import base64
import os
import time
from pathlib import Path

from .browser import Browser, StalePage
from .model import action_space, annotate, choose, current_atlas, elements_debug, field_context, field_text
from .questions import MAX_STEPS
from .runlog import open_run

# Local change: a run whose last cycle of 1..LOOP_MAX_CYCLE actions (same page, same
# control) has repeated LOOP_REPEATS times in a row is stopped. JEV_LOOP_REPEATS=0 turns it off.
LOOP_REPEATS = int(os.environ.get("JEV_LOOP_REPEATS", "3"))
LOOP_MAX_CYCLE = 4


def repeating_cycle(signatures):
    """The length of the cycle the last actions repeat LOOP_REPEATS times, else None."""
    if LOOP_REPEATS < 2:
        return None
    for length in range(1, LOOP_MAX_CYCLE + 1):
        n = len(signatures)
        if n >= LOOP_REPEATS * length and all(
            signatures[n - length:] == signatures[n - (k + 1) * length:n - k * length] for k in range(1, LOOP_REPEATS)
        ):
            return length
    return None


class Agent:
    def __init__(self, url, goals, *, record_dir=None, screenshots=False):
        task = goals.strip() if isinstance(goals, str) else "\n".join(goals).strip()
        if not task:
            raise ValueError("Supply a task")
        plan = [task]
        self.pending_text = None
        # Local change: the atlas is application knowledge; without JEV_ATLAS there is none.
        self.atlas = current_atlas()
        self.run_log = open_run(task, self.atlas)
        self.pending_step = None
        self.browser = Browser(url)
        self.record_dir = Path(record_dir) if record_dir else None
        self.screenshots = screenshots or bool(record_dir) or bool(self.run_log)
        try:
            page = annotate(self.browser.observe(screenshot=self.screenshots), self.browser)
        except Exception:
            self.browser.close()
            self.finish_run("error")
            raise
        self.state = dict(
            browser=self.browser,
            goal="\n".join(plan),
            page=page,
            decision=None,
            history=[],
            status="ready",
            plan=plan,
            plan_index=0,
            decisions=[],
            text_calls=[],
            elapsed_ms=0,
            started_at=None,
            record=bool(self.record_dir),
        )
        if self.record_dir:
            self.record_dir.mkdir(parents=True, exist_ok=True)
            if page.get("screenshot"):  # a capture may have timed out; the run goes on
                (self.record_dir / "000000.jpg").write_bytes(base64.b64decode(page["screenshot"]))
        if self.run_log:
            self.run_log.frame(page, 0)

    def flush_step(self):
        """Write the buffered step once its frame has arrived.

        Local change: the frame is captured while Jev is deciding the next step,
        so the capture never sits between an action and the next decision.
        """
        if getattr(self, "pending_step", None) is None:
            return
        record, page = self.pending_step
        self.pending_step = None
        self.state["browser"].wait_capture()
        record.setdefault("timings_ms", {})["screenshot"] = (page.get("timings") or {}).get("screenshot_ms")
        if getattr(self, "run_log", None):
            self.run_log.step(record, page)
        if getattr(self, "record_dir", None) and page.get("screenshot"):
            (self.record_dir / f"{record.get('elapsed_ms', 0):06d}.jpg").write_bytes(
                base64.b64decode(page["screenshot"])
            )

    def finish_run(self, status=None):
        if not getattr(self, "run_log", None):
            return
        state = getattr(self, "state", {})
        if status is None and state.get("stop_reason", "").startswith("loop"):
            status = "LOOP"
        if status is None:
            status = {"done": "DONE", "blocked": "BLOCKED"}.get(state.get("status"))
            if status is None:
                steps, calls = len(state.get("history", [])), len(state.get("decisions", []))
                status = "steps-exhausted" if steps >= MAX_STEPS or calls >= MAX_STEPS * 2 else "error"
        self.run_log.finish(status, state.get("model"))

    def snapshot(self):
        return {
            **{k: v for k, v in self.state.items() if k != "browser"},
            "elements": action_space(self.state["page"]["actions"])[0],
        }

    def command(self, name, body=None):
        body = body or {}
        state = self.state
        if name == "tick":
            try:
                self.command("predict", {})
                if state["decision"] is None:
                    return self.snapshot()  # an automatic wait consumed this tick
                return self.command("act", {"fingerprint": state["page"]["fingerprint"]})
            except StalePage:
                state["decision"] = None
                state["status"] = "ready"
                state["page"] = annotate(state["browser"].observe(screenshot=self.screenshots), state["browser"])
                state["elapsed_ms"] = round((time.perf_counter() - state["started_at"]) * 1000)
                return self.snapshot()
        elif name == "predict":
            if not state["browser"]:
                raise ValueError("Start a demo first")
            if state["started_at"] is None:
                state["started_at"] = time.perf_counter()
            if not state["browser"].fresh(state["page"]):
                state["page"] = annotate(state["browser"].observe(screenshot=self.screenshots), state["browser"])
            state["decision"] = None
            if state["status"] in {"done", "blocked"}:
                raise ValueError("This run has stopped. Start a fresh demo.")
            if len(state["decisions"]) >= MAX_STEPS * 2:
                raise ValueError("Reached the demo's model-call budget")
            # Local change: a busy indicator covering the controls is not a page to
            # decide from. Wait it out without spending a model call, at most three
            # times in a row, then let Jev see the page with busy: true.
            if state["page"].get("busy") and getattr(self, "auto_waits", 0) < 3:
                self.auto_waits = getattr(self, "auto_waits", 0) + 1
                return self.auto_wait()
            self.auto_waits = 0
            if getattr(self, "screenshots", False) and not state["page"].get("screenshot"):
                state["browser"].start_capture(state["page"])
            state["decision"] = choose(state["page"], state["goal"], state["history"])
            answered = state["decision"].get("model")
            if answered and state.get("model") != answered:
                state["model"] = answered
                print(f"Jev model: {answered}", flush=True)
            self.flush_step()
            state["decisions"].append(
                {
                    **state["decision"],
                    "fingerprint": state["page"]["fingerprint"],
                    "elapsed_ms": round((time.perf_counter() - state["started_at"]) * 1000),
                }
            )
            state["status"] = "predicted"
        elif name == "act":
            decision, page = state["decision"], state["page"]
            if not decision or body.get("fingerprint") != page["fingerprint"]:
                raise ValueError("Observe and choose before acting")
            # Consume once, before any mutation or model call. A retry cannot double-click.
            state["decision"] = None
            selected = decision["choice"]
            if selected in {"DONE", "BLOCKED"}:
                if not state["browser"].fresh(page):
                    state["status"] = "ready"
                    raise StalePage("Page changed since the decision. Choose again.")
                state["status"] = "done" if selected == "DONE" else "blocked"
                state["plan_index"] = int(selected == "DONE")
                state["elapsed_ms"] = round((time.perf_counter() - state["started_at"]) * 1000)
                self.pending_step = (self.step_record(decision, page, page, None, None, None), page)
                self.flush_step()
                self.finish_run()
                return self.snapshot()
            action = next(a for a in page["actions"] if a["id"] == selected)
            if len(state["history"]) >= MAX_STEPS:
                state["status"] = "blocked"
                raise ValueError(f"Stopped at the {MAX_STEPS}-action demo budget")
            text, helper = None, None
            if action["kind"] == "fill":
                if not state["browser"].fresh(page):
                    raise StalePage("Page changed before text generation. Choose again.")
                context = field_context(state["goal"], action, page, state["history"])
                if self.pending_text and self.pending_text[0] == context:
                    _, text, helper = self.pending_text
                else:
                    text, helper = field_text(context)
                    self.pending_text = (context, text, helper)
                    state["text_calls"].append({**helper, "field": action["label"], "value": text})
            # Browser.act checks freshness immediately before input, including after text generation.
            state["browser"].act(action, page, text=text)
            self.pending_text = None
            state["elapsed_ms"] = round((time.perf_counter() - state["started_at"]) * 1000)
            # Record execution before observing. A stale post-action observation must not erase the action.
            state["history"].append(
                {
                    "step": len(state["history"]) + 1,
                    "action": action["label"],
                    "kind": action["kind"],
                    "choice": selected,
                    "probability": decision["probabilities"][selected],
                    "confidence": decision["confidence"],
                    "latency_ms": decision["latency_ms"],
                    "text": text,
                    "text_helper": helper["model"] if helper else None,
                    "text_latency_ms": helper["latency_ms"] if helper else 0,
                    "operation": decision["operation"],
                    "target": decision["target"],
                    "model": decision.get("model"),
                    "page_changed": None,
                    "url": page["url"],
                    "usage": decision["usage"],
                    "executed_ms": round((time.perf_counter() - state["started_at"]) * 1000),
                    "elapsed_ms": state["elapsed_ms"],
                }
            )
            observed = annotate(state["browser"].observe(screenshot=False), state["browser"])
            state["page"] = observed
            if getattr(self, "screenshots", False):
                state["browser"].start_capture(observed)
            state["elapsed_ms"] = round((time.perf_counter() - state["started_at"]) * 1000)
            state["history"][-1].update(
                page_changed=observed["fingerprint"] != page["fingerprint"],
                url=observed["url"],
                elapsed_ms=state["elapsed_ms"],
            )
            self.pending_step = (
                self.step_record(decision, page, observed, action, text, helper),
                observed,
            )
            repeated = state["history"][-3:]
            state["status"] = (
                "blocked"
                if len(repeated) == 3 and all(h["page_changed"] is False and h["kind"] != "wait" for h in repeated)
                else "ready"
            )
            # Local change: stop a run that repeats one cycle of actions on the same pages
            # (jev-atlas). Replayed on the 43 runs logged on 2026-09-26, it fired on 10,
            # all failures, and on no run that passed. Waiting on a loading page is not a loop.
            if action["kind"] != "wait":
                self.cycle = getattr(self, "cycle", []) + [
                    (page["url"], action["label"], tuple(a["label"] for a in page["actions"]))
                ]
            length = repeating_cycle(getattr(self, "cycle", []))
            if length and state["status"] != "blocked":
                state["status"] = "blocked"
                state["stop_reason"] = f"loop: the same {length} action(s) {LOOP_REPEATS} times in a row"
                print(f"Loop stop: {state['stop_reason']}", flush=True)
        else:
            raise ValueError("Unknown command")
        return self.snapshot()

    def auto_wait(self):
        """One step of waiting out a busy page. No model call, but a recorded step."""
        state, page = self.state, self.state["page"]
        self.flush_step()
        print("Auto-wait: a busy indicator covers the page; waiting without asking Jev", flush=True)
        state["browser"].settle()
        observed = annotate(state["browser"].observe(screenshot=False), state["browser"])
        state["page"] = observed
        if getattr(self, "screenshots", False):
            state["browser"].start_capture(observed)
        state["elapsed_ms"] = round((time.perf_counter() - state["started_at"]) * 1000)
        changed = observed["fingerprint"] != page["fingerprint"]
        decision = {
            "operation": "WAIT", "target": None, "choice": "wait", "confidence": None,
            "probabilities": {}, "policy": "auto-wait-busy", "original_operation": None,
            "latency_ms": 0, "model": None,
        }
        action = {"label": "Wait for the page to update", "kind": "wait"}
        state["history"].append(
            {
                "step": len(state["history"]) + 1,
                "action": action["label"],
                "kind": "wait",
                "choice": "wait",
                "probability": None,
                "confidence": None,
                "latency_ms": 0,
                "text": None,
                "text_helper": None,
                "text_latency_ms": 0,
                "operation": "WAIT",
                "target": None,
                "policy": "auto-wait-busy",
                "model": None,
                "page_changed": changed,
                "url": observed["url"],
                "usage": {},
                "executed_ms": state["elapsed_ms"],
                "elapsed_ms": state["elapsed_ms"],
            }
        )
        self.pending_step = (self.step_record(decision, page, observed, action, None, None), observed)
        state["status"] = "ready"
        state["decision"] = None
        return self.snapshot()

    def step_record(self, decision, page, observed, action, text, helper):
        """One line of steps.jsonl: exactly what was sent, what came back, what ran."""
        request = decision.get("request") or {}
        return {
            "url": observed.get("url"),
            "title": observed.get("title"),
            "state": request.get("state"),
            "questions": request.get("questions"),
            "response": decision.get("raw_answers"),
            "model": decision.get("model"),
            "operation": decision["operation"],
            "target": decision["target"],
            "target_label": action["label"] if action else None,
            "policy": decision.get("policy"),
            "original_operation": decision.get("original_operation"),
            "choice": decision["choice"],
            "kind": action["kind"] if action else None,
            "text": text,
            "confidence": decision["confidence"],
            "probabilities": decision["probabilities"],
            "page_changed": None if action is None else observed["fingerprint"] != page["fingerprint"],
            # Diagnostics for the atlas author. Deliberately outside `state`: Jev never sees it.
            "elements_debug": elements_debug(page),
            # Local change: the atlas page and open overlays this step matched (None without an
            # atlas), so a failed run can be replayed against a revised atlas (jev-atlas learn).
            "atlas_page": page.get("page_id"),
            "atlas_overlays": page.get("overlays"),
            "elapsed_ms": self.state.get("elapsed_ms", 0),
            "timings_ms": {
                "settle": (observed.get("timings") or {}).get("settle_ms"),
                "snapshot": (observed.get("timings") or {}).get("snapshot_ms"),
                "jev": decision.get("latency_ms"),
                "text_model": helper["latency_ms"] if helper else None,
            },
        }

    def run(self):
        while self.state["status"] not in {"done", "blocked"}:
            yield self.command("tick")

    def close(self):
        try:
            self.flush_step()
        except Exception:
            pass
        self.finish_run()
        self.browser.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
