"""Local change: a run leaves a record on disk when JEV_RUN_DIR is set.

One directory per run, `<JEV_RUN_DIR>/<YYYYmmdd-HHMMSS>-<slug of the goal>/`:

  run.json     goal, atlas, start/end, status, step count, model, wall time
  steps.jsonl  one JSON object per step, in order
  step-NN.png  the frame observed after that step (step-00 is the first page)

Nothing here is read back by the agent; it exists so a run can be examined
after the fact, which is what the inspector alone could not give.
"""

import base64
import json
import os
import re
import time
from pathlib import Path


def slug(text, limit=48):
    value = re.sub(r"[^a-z0-9]+", "-", (text or "run").lower()).strip("-")
    return (value[:limit].rstrip("-")) or "run"


class RunLog:
    def __init__(self, root, goal, atlas=None):
        self.dir = Path(root) / f"{time.strftime('%Y%m%d-%H%M%S')}-{slug(goal)}"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.started = time.perf_counter()
        self.steps = 0
        self.run = {
            "goal": goal,
            "atlas": getattr(atlas, "path", None),
            "atlas_version": getattr(atlas, "version", None),
            # Local change: the declared version is whatever the file says about
            # itself; the digest is of the bytes that were loaded, so a result can
            # be attributed to an atlas revision even when the version was not bumped.
            "atlas_sha256": getattr(atlas, "sha256", None),
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "ended_at": None,
            "status": "running",
            "step_count": 0,
            "model": None,
            "wall_ms": 0,
        }
        self.write_run()

    def write_run(self):
        self.run["step_count"] = self.steps
        self.run["wall_ms"] = round((time.perf_counter() - self.started) * 1000)
        (self.dir / "run.json").write_text(json.dumps(self.run, indent=2, default=str))

    def frame(self, page, index):
        data = (page or {}).get("screenshot")
        if not data:
            return None
        suffix = ".png" if (page.get("screenshot_mime") or "").endswith("png") else ".jpg"
        name = f"step-{index:02d}{suffix}"
        try:
            (self.dir / name).write_bytes(base64.b64decode(data))
        except (ValueError, OSError):
            return None
        return name

    def step(self, record, page=None):
        """Append one step and save the frame observed after it."""
        self.steps += 1
        record = {"step": self.steps, **record}
        record["screenshot"] = self.frame(page, self.steps)
        if record.get("model"):
            self.run["model"] = record["model"]
        with (self.dir / "steps.jsonl").open("a") as file:
            file.write(json.dumps(record, default=str) + "\n")
        self.write_run()

    def finish(self, status, model=None):
        self.run["status"] = status
        self.run["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        if model:
            self.run["model"] = model
        self.write_run()


def open_run(goal, atlas=None):
    """A RunLog when JEV_RUN_DIR is set, else None."""
    root = os.environ.get("JEV_RUN_DIR")
    return RunLog(root, goal, atlas) if root else None
