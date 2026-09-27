"""Observed actions through Browser Harness; one CDP session, no per-step subprocess."""

import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path

from browser_harness.admin import ensure_daemon
from browser_harness.helpers import SCREENSHOT_IPC_RESPONSE_TIMEOUT_SECONDS, cdp

from . import atlas as atlas_file
from .model import current_atlas

# Atomically read visible content and controls, preserving actual DOM node identity.
# Local change (atlas shim): snapshot.js is an arrow function now, called with the
# dialog and busy selector lists. Both readers below are given the same lists, so a
# page cannot look settled to one and busy to the other.
SNAPSHOT = Path(__file__).with_name("snapshot.js").read_text()


def selectors():
    """The selector lists to inject: harness defaults plus the atlas's own."""
    return atlas_file.selector_lists(current_atlas())


def read_state(lists=None):
    """snapshot.js, bound to its selector lists."""
    return f"({SNAPSHOT})({json.dumps(lists if lists is not None else selectors())})"


def marker_expression(lists=None):
    return f"(() => {{ const state={read_state(lists)}; return state?.marker ?? null; }})()"

# Local change: one cheap read of everything settle() waits on. A component-heavy
# single-page application renders grids and toolbars in stages, and may hide the page
# behind a loading mask while it does, so a stable control count alone is not a
# finished page.
SETTLE_PROBE = """((SELECTORS) => {
  const SEL = SELECTORS || {};
  const CONTROLS='a[href],button,input,select,textarea,[role=button],[role=link],[role=tab],[role=option]';
  // The same lists snapshot.js is given: atlas.py's defaults plus the atlas's own.
  const DIALOG=(SEL.dialog||[]).join(',')||':not(*)';
  const BUSY=(SEL.busy||[]).join(',')||':not(*)';
  const shown=e=>{const r=e.getBoundingClientRect();
    return r.width>0 && r.height>0 && e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});};
  const BUSYISH=/busy|loading|spinner|progress/i;
  let covered=0, coveredBusy=0;
  for (const e of document.querySelectorAll(CONTROLS)) {
    if (!shown(e) || e.matches(':disabled')) continue;
    const r=e.getBoundingClientRect(), x=r.x+r.width/2, y=r.y+r.height/2;
    if (x<0 || y<0 || x>=innerWidth || y>=innerHeight) continue;
    try {
      const top=document.elementFromPoint(x,y);
      if (top===e || e.contains(top) || (top && top.contains(e))) continue;
      covered++;
      if (top && (BUSYISH.test(top.tagName) || BUSYISH.test((top.className||'')+''))) coveredBusy++;
    } catch { /* ignore */ }
  }
  return {url:location.href,
    controls:document.querySelectorAll(CONTROLS).length,
    covered,
    coveredBusy,
    busy:coveredBusy>0 || [...document.querySelectorAll(BUSY)].some(shown),
    dialog:[...document.querySelectorAll(DIALOG)].some(shown),
    resources:performance.getEntriesByType('resource').length};
})"""


def settle_probe(lists=None):
    """The settle probe, bound to the same selector lists as snapshot.js."""
    return f"{SETTLE_PROBE}({json.dumps(lists if lists is not None else selectors())})"

# Local change: the last frame per session, so a failed capture does not blank the view.
LAST_SCREENSHOT = {}


class StalePage(ValueError):
    """A decision no longer refers to the observed page."""


class Browser:
    def __init__(self, url):
        ensure_daemon()
        # Local change: resolved once per run, so every reader in this session --
        # snapshot.js, the settle probe and the marker -- sees the same lists. The
        # readers fall back to resolving them fresh if this was never set.
        self.selectors = selectors()
        self.target = cdp("Target.createTarget", url="about:blank", background=True)["targetId"]
        self.session = cdp("Target.attachToTarget", targetId=self.target, flatten=True)["sessionId"]
        # Local change: JEV_VIEWPORT=WIDTHxHEIGHT sizes the agent's tab. A wider
        # window keeps a responsive toolbar from collapsing into an overflow menu.
        width, height = 1120, 780
        try:
            wanted = os.environ.get("JEV_VIEWPORT", "").lower().split("x")
            if len(wanted) == 2:
                width, height = max(320, int(wanted[0])), max(320, int(wanted[1]))
        except ValueError:
            pass
        self.call("Emulation.setDeviceMetricsOverride", width=width, height=height,
                  deviceScaleFactor=1, mobile=False)
        # Keep rAF/menus rendering in an owned background tab, without activating the user's Chrome tab.
        self.call("Emulation.setFocusEmulationEnabled", enabled=True)
        # Local change: capturing an occluded tab's surface took 4-19 s on a live
        # application here, against ~100 ms once the tab is in front. JEV_SHOW_TAB=1
        # brings it forward, which is also the point when someone is watching the run.
        if os.environ.get("JEV_SHOW_TAB") == "1":
            cdp("Target.activateTarget", targetId=self.target)
        self.call("Page.navigate", url=url)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if self.evaluate("document.readyState") == "complete":
                break
            time.sleep(0.02)
        # Local change: an enterprise SPA is `complete` long before it has rendered
        # anything, so the first observation can see an empty page and the first
        # decision is made blind. Wait for the control count to stop changing.
        settle, last = time.monotonic() + 8, None
        while time.monotonic() < settle:
            count = self.evaluate(
                "document.querySelectorAll('a,button,input,select,textarea,"
                "[role=button],[role=link],[role=tab]').length")
            if count and count == last:
                break
            last = count
            time.sleep(0.4)

    def call(self, method, **params):
        return cdp(method, session_id=self.session, **params)

    def marker(self):
        """The page marker, reused within one tick.

        Local change (speed): a fill step asked for it three times and each ask
        re-ran the whole reader. observe() and act() drop the cache, so the read
        that guards input is always fresh; JEV_FRESH_CACHE_MS=0 disables it.
        """
        ttl = int(os.environ.get("JEV_FRESH_CACHE_MS", "2000")) / 1000
        cached, now = getattr(self, "_marker", None), time.monotonic()
        if cached and now - cached[0] < ttl:
            return cached[1]
        value = self.evaluate(marker_expression(getattr(self, "selectors", None)))
        self._marker = (now, value)
        return value

    def start_capture(self, page):
        """Capture the frame in the background. Jev never sees it, so it can
        overlap the model call instead of delaying it."""
        self.wait_capture()
        if page.get("screenshot"):
            return

        # Create the keys first: another thread may serialize this page while the
        # capture runs, and rebinding an existing key cannot resize the dict.
        page.setdefault("screenshot", None)
        page.setdefault("screenshot_mime", None)
        page.setdefault("timings", {}).setdefault("screenshot_ms", None)

        def run():
            data, mime, elapsed = capture(self.session)
            page["screenshot"], page["screenshot_mime"] = data, mime
            page["timings"]["screenshot_ms"] = elapsed

        self._capture = threading.Thread(target=run, daemon=True)
        self._capture.start()

    def wait_capture(self, timeout=65):
        thread, self._capture = getattr(self, "_capture", None), None
        if thread:
            thread.join(timeout)

    def evaluate(self, expression):
        response = self.call("Runtime.evaluate", expression=expression, returnByValue=True)
        if response.get("exceptionDetails"):
            raise StalePage("Document changed during evaluation")
        return response.get("result", {}).get("value")

    def settle(self):
        """Wait for the page to finish redrawing after an action.

        Local change: upstream waits two animation frames or 50 ms (200 ms for a
        combobox) and then observes. A single-page application tears the old view down
        and draws the new one well after that, so the observation lands on an empty
        page: the reader sees one element, the decision is made blind, and the run
        reports "no supported next action" while the tab is in fact fine.

        What this waits for, within JEV_SETTLE_MS:
        - three equal, non-zero control counts (750 ms quiet). Two were not enough:
          a data-heavy page read 42-43 controls right after a route change and
          56-61 once its grid and toolbar had rendered, so a two-poll wait
          could observe a page whose toolbar did not exist yet;
        - no visible loading mask, spinner or aria-busy element;
        - after a URL change, no new network resources between two polls;
        - and, when controls are covered although nothing is open, a covered count
          that has stopped falling. A loading mask over a toolbar otherwise reads
          as "15 controls are behind the open dialog" with no dialog at all.
        """
        budget = int(os.environ.get("JEV_SETTLE_MS", "4000"))
        if budget <= 0:
            return
        started = time.monotonic()
        deadline, patience = started + budget / 1000, started + budget / 2000
        counts, covers, resources, navigated = [], [], [], False
        while time.monotonic() < deadline:
            try:
                probe = self.evaluate(settle_probe(getattr(self, "selectors", None)))
            except (StalePage, RuntimeError):
                return  # navigating: the observe loop below already retries
            if not probe:
                return
            navigated = navigated or probe["url"] != getattr(self, "last_url", probe["url"])
            counts.append(probe["controls"])
            covers.append(probe["covered"])
            resources.append(probe["resources"])
            quiet = len(counts) >= 3 and probe["controls"] and len(set(counts[-3:])) == 1
            # A busy indicator actually covering controls is waited out in full: it
            # is why the toolbar was missing. A page that merely claims to be loading
            # must not cost the whole budget every step, so that half of it is enough.
            network = navigated and len(resources) >= 2 and resources[-1] != resources[-2]
            loading = probe.get("coveredBusy", 0) > 0 or (
                (probe["busy"] or network) and time.monotonic() < patience
            )
            if quiet and not loading:
                settled = probe["covered"] == 0 or probe["dialog"] or (
                    len(covers) >= 2 and covers[-1] == covers[-2]
                )
                if settled:
                    return
            time.sleep(0.25)

    def observe(self, screenshot=True):
        self._marker = None
        started = time.perf_counter()
        if getattr(self, "after_input", None):
            action, self.after_input = self.after_input, None
            # This is read-only and happens after execution was logged, even if navigation interrupts it.
            try:
                self.call(
                    "Runtime.evaluate",
                    expression="""(action => new Promise(resolve => {
                      const field=window.__jevFast?.nodes.get(action.node);
                      const autocomplete=action.kind==='fill' && field?.getAttribute('role')==='combobox';
                      let frames=0, stopped=false;
                      const finish=()=>{stopped=true;resolve()};
                      setTimeout(finish,autocomplete ? 200 : 50);
                      const ready=()=>{
                        if (stopped) return;
                        const ids=(field?.getAttribute('aria-controls')||field?.getAttribute('aria-owns')||'')
                          .split(/\\s+/).filter(Boolean);
                        const roots=ids.length ? ids.map(id=>document.getElementById(id)).filter(Boolean) : [document];
                        const options=roots.flatMap(root=>[...root.querySelectorAll('[role="option"]')]);
                        if (++frames>=2 && (!autocomplete || options.some(e=>{
                          const r=e.getBoundingClientRect();
                          return r.width && r.height && r.bottom>0 && r.top<innerHeight &&
                            e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
                        }))) finish();
                        else requestAnimationFrame(ready);
                      };
                      requestAnimationFrame(ready);
                    }))(""" + json.dumps(action) + ")",
                    awaitPromise=True,
                    returnByValue=True,
                )
            except RuntimeError:
                pass
            self.settle()
        settle_ms = round((time.perf_counter() - started) * 1000)
        for attempt in range(10):
            try:
                info = browser_operation(
                    {"operation": "observe", "session": self.session, "screenshot": screenshot,
                     "selectors": self.selectors}
                )
                info.setdefault("timings", {})["settle_ms"] = settle_ms
                self.last_url = info["url"]
                return info
            except StalePage:
                if attempt == 9:
                    raise
                time.sleep(0.02)
        raise StalePage("Page did not settle")

    def fresh(self, page, action=None):
        if action is not None and action["kind"] in {"click", "select", "submit"}:
            node = action["node"]
            if type(node) is not int:
                return False
            current = self.evaluate(
                "(() => { const c=window.__jevFast; "
                f"return c ? [c.pageKey(),c.guard(c.nodes.get({node}))] : null; }})()"
            )
            return current == [page["page_key"], page["guards"].get(str(node))]
        return self.marker() == page["marker"]

    def act(self, action, page, text=None):
        self._marker = None
        if not self.fresh(page, action):
            raise StalePage("Page changed since this decision. Observe again.")
        if action.get("virtual"):
            # A virtual control is written through the application's own API, which
            # the atlas supplies; it must confirm the write by returning true.
            written = self.evaluate(f"(({action['set']}))({json.dumps(text)})")
            if written is not True:
                raise RuntimeError("The virtual control did not confirm the value; nothing was written.")
            self.settle()
            self._marker = None
            return {"executed": action["id"]}
        if action["kind"] == "wait":
            time.sleep(0.1)
        result = browser_operation({"operation": "act", "session": self.session, "action": action, "text": text})
        self.after_input = action if action["kind"] != "wait" else None
        return result

    def close(self):
        self.wait_capture(timeout=5)
        if self.target:
            cdp("Target.closeTarget", targetId=self.target)
            self.target = None


def capture(session, fmt=None):
    """One screenshot. Returns (base64 or None, mime, elapsed ms)."""
    fmt = fmt or ("png" if os.environ.get("JEV_RUN_DIR") else "jpeg")
    started = time.perf_counter()
    try:
        # Local change: the generic cdp() timeout is 5 s, while Browser Harness allows 60 s
        # for its own screenshots; a live application can take longer than 5 s to paint.
        # The screenshot is only for watching — Jev decides from the element table — so a
        # slow or failed capture keeps the previous frame instead of ending the step.
        data = cdp(
            "Page.captureScreenshot",
            session_id=session,
            format=fmt,
            _response_timeout=SCREENSHOT_IPC_RESPONSE_TIMEOUT_SECONDS,
            **({"quality": 72} if fmt == "jpeg" else {}),
        )["data"]
        LAST_SCREENSHOT[session] = (data, f"image/{fmt}")
    except Exception:
        data = LAST_SCREENSHOT.get(session, (None, f"image/{fmt}"))[0]
    return data, LAST_SCREENSHOT.get(session, (None, f"image/{fmt}"))[1], round((time.perf_counter() - started) * 1000)


def fingerprint(state):
    content = {k: state[k] for k in ("url", "text", "actions", "scroll")}
    # Local change: `covered` is a hit test, resolved again immediately before input.
    # Keeping it out of page identity stops a passing overlay from reading as a new page.
    hit_test = ("covered", "covered_by", "covered_by_busy")
    content["actions"] = [{k: v for k, v in a.items() if k not in hit_test} for a in content["actions"]]
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


# Local change: native date/time inputs. Typing into Chrome's segmented date field
# with Input.insertText does not set it, so the executor writes these through the
# prototype's value setter and fires input and change, which is also what a
# framework-controlled input (React's value tracker) needs to see the change.
# Common spellings are converted to the one wire format each type accepts.
TEMPORAL_PARSE = {
    "date": ("%Y-%m-%d", ["%Y-%m-%d", "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
                          "%b %d %Y", "%B %d %Y", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"]),
    "time": ("%H:%M", ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p", "%I %p", "%I%p"]),
    "datetime-local": ("%Y-%m-%dT%H:%M", ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S",
                                          "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"]),
    "month": ("%Y-%m", ["%Y-%m", "%Y/%m", "%B %Y", "%b %Y", "%m/%Y"]),
}


def temporal_value(input_type, text):
    """`text` in the wire format of a native `input_type` field, or unchanged if it cannot be read."""
    from datetime import datetime

    wanted = TEMPORAL_PARSE.get(input_type)
    text = (text or "").strip()
    if not wanted:
        return text
    out, formats = wanted
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).strftime(out)
        except ValueError:
            continue
    return text


def same_tab():
    """Local change: links that would open a new tab open in the agent's own tab (JEV_SAME_TAB=0: off)."""
    return os.environ.get("JEV_SAME_TAB", "1") != "0"


def browser_operation(request):
    operation = request["operation"]
    session = request["session"]

    def call(method, **params):
        return cdp(method, session_id=session, **params)

    def evaluate(expression):
        result = call("Runtime.evaluate", expression=expression, returnByValue=True)
        if result.get("exceptionDetails"):
            if operation == "act" and request["action"]["kind"] == "select":
                raise RuntimeError("Dropdown execution was interrupted; inspect before retrying.")
            raise StalePage("Document changed during evaluation")
        return result.get("result", {}).get("value")

    if operation == "act":
        action = request["action"]
        kind = action["kind"]
        if kind == "scroll":
            # Local change: an inner pane only scrolls under the pointer. snapshot.js
            # reports the largest visible scrolling container; (550, 650) is the fallback.
            call("Input.dispatchMouseEvent", type="mouseWheel", x=action.get("x", 550),
                 y=action.get("y", 650), deltaX=0, deltaY=action["delta"])
        elif kind != "wait":
            if type(action["node"]) is not int:
                raise ValueError("Invalid observed node")
            # Code-owned node IDs refer to actual observed elements, never model-generated selectors.
            text = request.get("text")
            if kind == "fill" and action.get("input_type"):
                text = temporal_value(action["input_type"], text)
            target = evaluate("""((action,text,sameTab) => {
              const e=window.__jevFast?.nodes.get(action.node);
              if (!e?.isConnected || e.matches(':disabled') || e.closest('[aria-disabled="true"],[inert]') ||
                  !e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})) return null;
              if (action.kind==='fill' && (e.readOnly || e.getAttribute('aria-readonly')==='true')) return null;
              let r=e.getBoundingClientRect(), x=r.x+r.width/2, y=r.y+r.height/2;
              // Local change: a control observed beyond the side of a horizontally scrolling
              // container is brought into view before it is hit-tested.
              if (action.offscreen_x && (x<0 || x>=innerWidth)) {
                e.scrollIntoView({block:'nearest',inline:'center'});
                r=e.getBoundingClientRect(); x=r.x+r.width/2; y=r.y+r.height/2;
              }
              if (!r.width || !r.height || x<0 || y<0 || x>=innerWidth || y>=innerHeight) return null;
              if (!e.contains(document.elementFromPoint(x,y))) return null;
              // Local change: Enter goes to the field itself, focused without a click
              // (a click could open or close a list the field owns).
              if (action.kind==='submit') {
                e.focus();
                let a=document.activeElement;
                while (a?.shadowRoot?.activeElement) a=a.shadowRoot.activeElement;
                return a===e ? {x,y,submit:true} : null;
              }
              if (action.kind==='select') {
                if (e.tagName!=='SELECT' || ![...e.options].some(o=>o.value===action.value &&
                    !o.disabled && !o.closest('optgroup[disabled]'))) return null;
                e.value=action.value;
                e.dispatchEvent(new Event('input',{bubbles:true}));
                e.dispatchEvent(new Event('change',{bubbles:true}));
              }
              if (action.kind==='fill' && e.tagName==='INPUT' &&
                  ['date','time','datetime-local','month','week'].includes(e.type)) {
                // Try the value on a detached twin first: an unreadable value would clear the field.
                const twin=document.createElement('input');
                twin.type=e.type; twin.value=text;
                if (twin.value!==text) return {x,y,direct:true,accepted:false,type:e.type};
                const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
                e.focus();
                setter.call(e,text);
                e.dispatchEvent(new Event('input',{bubbles:true}));
                e.dispatchEvent(new Event('change',{bubbles:true}));
                return {x,y,direct:true,accepted:e.value===text,type:e.type};
              }
              // A link that would open a new tab is opened in this one, where the
              // agent can see it; the attribute is restored straight after the click.
              let retarget=false;
              if (sameTab && action.kind==='click') {
                const link=e.closest('a[href][target],area[href][target]');
                const t=(link?.getAttribute('target')||'').toLowerCase();
                if (link && t && !['_self','_top','_parent'].includes(t)) {
                  link.dataset.jevTarget=link.getAttribute('target');
                  link.setAttribute('target','_self');
                  retarget=true;
                }
              }
              return {x,y,retarget};
            })(""" + json.dumps(action) + "," + json.dumps(text) + "," + json.dumps(same_tab()) + ")")
            if target is None:
                if kind == "select":
                    raise RuntimeError("Dropdown execution was not confirmed; inspect before retrying.")
                raise StalePage("Target changed or is covered. Observe again.")
            if target.get("submit"):
                # Local change: PRESS_ENTER. A keyDown carrying "\r" also produces the
                # keypress that triggers a form's implicit submission.
                keys = dict(key="Enter", code="Enter", windowsVirtualKeyCode=13, nativeVirtualKeyCode=13)
                call("Input.dispatchKeyEvent", type="keyDown", text="\r", unmodifiedText="\r", **keys)
                call("Input.dispatchKeyEvent", type="keyUp", **keys)
            elif target.get("direct"):
                if not target.get("accepted"):
                    raise RuntimeError(
                        f"The {target.get('type')} field did not accept {text!r}; nothing was written. "
                        "Observe again before retrying."
                    )
            elif kind != "select":
                x, y = target["x"], target["y"]
                for event in ("mousePressed", "mouseReleased"):
                    call("Input.dispatchMouseEvent", type=event, x=x, y=y, button="left", clickCount=1)
                if kind == "fill":
                    call(
                        "Input.dispatchKeyEvent",
                        type="keyDown",
                        key="a",
                        code="KeyA",
                        modifiers=4 if sys.platform == "darwin" else 2,
                        commands=["selectAll"],
                    )
                    call(
                        "Input.dispatchKeyEvent",
                        type="keyUp",
                        key="a",
                        code="KeyA",
                        modifiers=4 if sys.platform == "darwin" else 2,
                    )
                    call("Input.insertText", text=request["text"])
                if target.get("retarget"):
                    try:
                        evaluate("""(() => { for (const a of document.querySelectorAll('[data-jev-target]')) {
                          a.setAttribute('target', a.dataset.jevTarget); delete a.dataset.jevTarget; } })()""")
                    except (StalePage, RuntimeError):
                        pass  # the click navigated away; the old document is gone
        return {"executed": action["id"]}

    started = time.perf_counter()
    info = evaluate(read_state(request.get("selectors")))
    if info is None:
        raise StalePage("Document is navigating")
    info["timings"] = {"snapshot_ms": round((time.perf_counter() - started) * 1000)}
    info["fingerprint"] = fingerprint(info)
    if request.get("screenshot", True):
        info["screenshot"], info["screenshot_mime"], info["timings"]["screenshot_ms"] = capture(session)
    return info
