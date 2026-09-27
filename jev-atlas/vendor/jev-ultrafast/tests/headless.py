"""A throwaway headless Chrome for running snapshot.js and the executor against fixtures.

Local change: the upstream tests never run the page reader in a browser. These do,
over plain CDP (the `websockets` package browser-harness already installs), and are
skipped when no Chrome or Chromium binary is on the machine.
"""

import itertools
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

BINARIES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")


def find_chrome():
    wanted = os.environ.get("JEV_TEST_CHROME")
    if wanted:
        return wanted
    for name in BINARIES:
        found = shutil.which(name)
        if found and Path(found).is_file():
            return found
    return None


class Chrome:
    """One headless browser with one page, driven over a flat CDP websocket."""

    def __init__(self, width=1120, height=780):
        from websockets.sync.client import connect

        binary = find_chrome()
        if not binary:
            raise RuntimeError("No Chrome binary")
        self.profile = tempfile.mkdtemp(prefix="jev-test-chrome-")
        self.process = subprocess.Popen(
            [binary, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-first-run",
             "--no-default-browser-check", "--remote-debugging-port=0",
             f"--user-data-dir={self.profile}", f"--window-size={width},{height}", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        port_file = Path(self.profile) / "DevToolsActivePort"
        deadline = time.monotonic() + 20
        while not port_file.exists() or len(port_file.read_text().splitlines()) < 2:
            if time.monotonic() > deadline or self.process.poll() is not None:
                self.close()
                raise RuntimeError("Chrome did not start")
            time.sleep(0.05)
        port, path = port_file.read_text().splitlines()[:2]
        self.ws = connect(f"ws://127.0.0.1:{port}{path}", max_size=None)
        self.ids = itertools.count(1)
        target = self.send("Target.createTarget", url="about:blank")["targetId"]
        self.session = self.send("Target.attachToTarget", targetId=target, flatten=True)["sessionId"]
        self.call("Emulation.setDeviceMetricsOverride", width=width, height=height,
                  deviceScaleFactor=1, mobile=False)
        self.call("Page.enable")

    def send(self, method, session_id=None, **params):
        message = {"id": next(self.ids), "method": method, "params": params}
        if session_id:
            message["sessionId"] = session_id
        self.ws.send(json.dumps(message))
        while True:
            reply = json.loads(self.ws.recv(timeout=20))
            if reply.get("id") == message["id"]:
                if "error" in reply:
                    raise RuntimeError(reply["error"])
                return reply.get("result", {})

    def call(self, method, **params):
        return self.send(method, session_id=self.session, **params)

    def load(self, html, url="http://fixture.test/app/"):
        """Serve `html` at `url` (intercepted, nothing touches the network) and wait for load."""
        self.call("Fetch.enable", patterns=[{"urlPattern": "http://fixture.test/*"}])
        message = {"id": next(self.ids), "method": "Page.navigate", "params": {"url": url},
                   "sessionId": self.session}
        self.ws.send(json.dumps(message))
        import base64
        while True:
            event = json.loads(self.ws.recv(timeout=20))
            if event.get("method") == "Fetch.requestPaused":
                self.ws.send(json.dumps({
                    "id": next(self.ids), "method": "Fetch.fulfillRequest", "sessionId": self.session,
                    "params": {"requestId": event["params"]["requestId"], "responseCode": 200,
                               "responseHeaders": [{"name": "Content-Type", "value": "text/html"}],
                               "body": base64.b64encode(html.encode()).decode()}}))
            if event.get("method") == "Page.loadEventFired":
                break
        self.call("Fetch.disable")
        return self

    def evaluate(self, expression):
        result = self.call("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
        if result.get("exceptionDetails"):
            raise RuntimeError(result["exceptionDetails"])
        return result.get("result", {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        shutil.rmtree(self.profile, ignore_errors=True)
