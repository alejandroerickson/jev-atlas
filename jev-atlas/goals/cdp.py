"""A tiny Chrome DevTools client: open a tab, evaluate JavaScript, close it.

Used by check.py to reset ADIT's state before a run and to read it after one.
Needs only `websockets` (present in the harness clone's venv and this repo's).
"""
import json
import os
import time
import urllib.request

from websockets.sync.client import connect

CDP = os.environ.get("ADIT_CDP_URL") or os.environ.get("BU_CDP_URL") or "http://127.0.0.1:9333"


class Tab:
    def __init__(self, url="about:blank", cdp=CDP):
        req = urllib.request.Request(f"{cdp}/json/new?{url}", method="PUT")
        info = json.loads(urllib.request.urlopen(req, timeout=10).read())
        self.id = info["id"]
        self.cdp = cdp
        self.ws = connect(info["webSocketDebuggerUrl"], max_size=2**26, open_timeout=10)
        self.n = 0
        self.wait_ready()

    def send(self, method, **params):
        self.n += 1
        mid = self.n
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv(timeout=30))
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def eval(self, expr, await_promise=True):
        r = self.send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=await_promise)
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"].get("exception", {}).get("description") or r["exceptionDetails"])
        return r.get("result", {}).get("value")

    def wait_ready(self, timeout=15):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                if self.eval("document.readyState") == "complete":
                    break
            except Exception:
                pass
            time.sleep(0.2)
        time.sleep(0.8)  # let the hash router render

    def goto(self, url):
        self.send("Page.navigate", url=url)
        time.sleep(0.3)
        self.wait_ready()

    def close(self):
        try:
            self.ws.close()
        finally:
            urllib.request.urlopen(f"{self.cdp}/json/close/{self.id}", timeout=10).read()
