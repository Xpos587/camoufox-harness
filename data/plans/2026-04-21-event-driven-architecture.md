# Event-Driven Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert camoufox-harness from HTTP REST to event-driven architecture using Camoufox's built-in remote server (WebSocket) with Playwright async API.

**Architecture:** Agent connects to Camoufox remote server via Playwright's `firefox.connect()`. Events flow through Playwright event handlers into an in-memory queue. Agent retrieves events via `drain_events()`.

**Tech Stack:** `playwright>=1.40.0`, `camoufox[geoip]>=0.4.0`, async/await

---

## File Structure

**Modified files:**
- `helpers.py` — Replace httpx client with Playwright async API
- `admin.py` — Replace FastAPI with camoufox.server.launch_server
- `run.py` — Convert to async entry point
- `pyproject.toml` — Remove httpx, add playwright

**No new files** — refactoring existing code.

---

## Task 1: Update pyproject.toml dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Replace httpx with playwright**

```toml
[project]
name = "camoufox-harness"
version = "0.1.0"
description = "Playwright-based browser harness using Camoufox (Firefox anti-detect)"
requires-python = ">=3.11"
dependencies = [
    "playwright>=1.40.0",
    "camoufox[geoip]>=0.4.0",
]
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "deps: replace httpx with playwright, add camoufox[geoip]"
```

---

## Task 2: Implement async helpers.py with Playwright connect

**Files:**
- Modify: `helpers.py`

- [ ] **Step 1: Write PEP 723 header and imports**

```python
# /// script
# dependencies = [
#   "playwright>=1.40.0",
#   "camoufox[geoip]>=0.4.0",
# ]
# ///

"""Async browser control via Camoufox remote server."""
import asyncio
import os
import random
import time
from collections import deque
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
```

- [ ] **Step 2: Define global state and config**

```python
NAME = os.environ.get("CH_NAME", "default")
WS_URL = os.environ.get("CH_WS_URL", "ws://127.0.0.1:9222/camoufox")
INTERNAL = ("about:", "data:", "chrome://", "chrome-extension://")

PROFILE_DIR = Path.home() / ".config" / "camoufox-harness" / "profiles" / NAME
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

EVENTS_BUF = 500

# Global state
_playwright = None
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_page: Optional[Page] = None
_events = deque(maxlen=EVENTS_BUF)
```

- [ ] **Step 3: Write event handlers**

```python
def _on_dialog(dialog):
    _events.append({"type": "dialog", "message": dialog.message, "dialog_type": dialog.type})


def _on_load():
    _events.append({"type": "load", "url": _page.url})


def _on_console(msg):
    _events.append({"type": "console", "level": msg.type, "text": msg.text})


def _on_error(error):
    _events.append({"type": "error", "message": str(error)})
```

- [ ] **Step 4: Write connection manager**

```python
async def _ensure_connection():
    """Connect to Camoufox remote server if not connected."""
    global _playwright, _browser, _context, _page
    
    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.firefox.connect(WS_URL)
        _context = _browser.contexts[0]
        
        if _context.pages:
            _page = _context.pages[0]
        else:
            _page = await _context.new_page()
        
        # Subscribe to events
        _page.on("dialog", _on_dialog)
        _page.on("load", _on_load)
        _page.on("console", _on_console)
        _page.on("pageerror", _on_error)
```

- [ ] **Step 5: Write navigation functions**

```python
async def goto(url: str, wait_until: str = "domcontentloaded") -> dict:
    """Navigate to URL. Returns {url, title}."""
    await _ensure_connection()
    await _page.goto(url, wait_until=wait_until)
    return {"url": _page.url, "title": await _page.title()}


async def page_info() -> dict:
    """{url, title, w, h} — current page state."""
    await _ensure_connection()
    vp = await _page.viewport_size()
    return {
        "url": _page.url,
        "title": await _page.title(),
        "w": vp["width"],
        "h": vp["height"],
    }


async def wait_for_load(timeout: float = 15.0) -> bool:
    """Wait for page load complete."""
    await _ensure_connection()
    try:
        await _page.wait_for_load_state("domcontentloaded", timeout=timeout * 1000)
        return True
    except:
        return False
```

- [ ] **Step 6: Write input functions**

```python
async def click(selector: str, button: str = "left", clicks: int = 1) -> dict:
    """Click element by CSS selector."""
    await _ensure_connection()
    await _page.locator(selector).click(button=button, click_count=clicks)
    return {"clicked": selector}


async def type_text(selector: str, text: str, delay: float = 0.05) -> dict:
    """Type text into element."""
    await _ensure_connection()
    el = _page.locator(selector)
    await el.fill("")
    await el.type(text, delay=delay * 1000)
    return {"typed": text}


async def press_key(key: str, modifiers: list = None) -> dict:
    """Press keyboard key (Enter, Tab, Escape, etc.)."""
    await _ensure_connection()
    mods = []
    if modifiers:
        mod_map = {"Alt": "Alt", "Control": "Control", "Meta": "Meta", "Shift": "Shift"}
        mods = [mod_map.get(m, m) for m in modifiers]
    await _page.keyboard.press(key, modifiers=mods)
    return {"pressed": key}


async def scroll(direction: str = "down", amount: int = 300) -> dict:
    """Scroll page (up/down/left/right)."""
    await _ensure_connection()
    if direction == "down":
        await _page.evaluate(f"window.scrollBy(0, {amount})")
    elif direction == "up":
        await _page.evaluate(f"window.scrollBy(0, -{amount})")
    elif direction == "left":
        await _page.evaluate(f"window.scrollBy(-{amount}, 0)")
    elif direction == "right":
        await _page.evaluate(f"window.scrollBy({amount}, 0)")
    return {"scrolled": direction}
```

- [ ] **Step 7: Write visual functions**

```python
async def screenshot(path: str = "/tmp/shot.png", full: bool = False) -> str:
    """Take screenshot. Returns path to saved file."""
    await _ensure_connection()
    data = await _page.screenshot(full_page=full)
    with open(path, "wb") as f:
        f.write(data)
    return path


async def snapshot() -> dict:
    """Get accessibility tree snapshot with element refs."""
    await _ensure_connection()
    snap = await _page.accessibility.snapshot()
    return {"snapshot": snap, "element_count": _count_elements(snap)}


def _count_elements(node, count=0):
    """Recursively count elements in accessibility tree."""
    if not isinstance(node, dict):
        return count
    count += 1
    for child in node.get("children", []):
        count = _count_elements(child, count)
    return count
```

- [ ] **Step 8: Write utility functions**

```python
async def js(expression: str):
    """Execute JavaScript in page context."""
    await _ensure_connection()
    return await _page.evaluate(expression)


async def get_html() -> str:
    """Get page HTML."""
    await _ensure_connection()
    return await _page.content()


async def get_text() -> str:
    """Get page visible text."""
    await _ensure_connection()
    return await _page.evaluate("document.body.innerText")


def wait(seconds: float = 1.0):
    """Sleep for specified seconds."""
    time.sleep(seconds)


def random_delay(min_sec: float = 0.5, max_sec: float = 2.0):
    """Random delay for anti-detect humanize."""
    time.sleep(random.uniform(min_sec, max_sec))
```

- [ ] **Step 9: Write tabs functions**

```python
async def list_tabs() -> list:
    """List all tabs."""
    await _ensure_connection()
    ctx = _browser.contexts[0]
    return [{"id": i, "url": p.url, "title": await p.title()} for i, p in enumerate(ctx.pages)]


async def current_tab() -> dict:
    """Get current tab info."""
    await _ensure_connection()
    return {"id": 0, "url": _page.url, "title": await _page.title()}


async def new_tab(url: str = "about:blank") -> dict:
    """Open new tab."""
    await _ensure_connection()
    new_page = await _context.new_page()
    await new_page.goto(url)
    return {"id": len(_context.pages) - 1, "url": new_page.url}


async def close_tab() -> dict:
    """Close current tab."""
    await _ensure_connection()
    await _page.close()
    # Switch to first available page
    if _context.pages:
        global _page
        _page = _context.pages[0]
    return {"closed": True}
```

- [ ] **Step 10: Write cookie/storage functions**

```python
async def get_cookies() -> list:
    """Get all cookies."""
    await _ensure_connection()
    return await _context.cookies()


async def set_cookies(cookies: list) -> dict:
    """Set cookies."""
    await _ensure_connection()
    await _context.add_cookies(cookies)
    return {"set": True}


async def get_local_storage() -> dict:
    """Get localStorage."""
    await _ensure_connection()
    return await _page.evaluate("Object.assign({}, localStorage)")


async def set_local_storage(items: dict) -> dict:
    """Set localStorage items."""
    await _ensure_connection()
    for k, v in items.items():
        await _page.evaluate(f"localStorage.setItem({repr(k)}, {repr(v)})")
    return {"set": True}
```

- [ ] **Step 11: Write session functions**

```python
async def save_profile(name: str) -> dict:
    """Save current browser state to profile."""
    await _ensure_connection()
    profile_path = PROFILE_DIR / name
    profile_path.mkdir(parents=True, exist_ok=True)
    
    cookies = await _context.cookies()
    (profile_path / "cookies.json").write_text(json.dumps(cookies))
    
    ls = await _page.evaluate("Object.assign({}, localStorage)")
    (profile_path / "localStorage.json").write_text(json.dumps(ls))
    
    return {"saved": name, "path": str(profile_path)}


async def load_profile(name: str) -> dict:
    """Load browser state from profile."""
    await _ensure_connection()
    profile_path = PROFILE_DIR / name
    if not profile_path.exists():
        raise RuntimeError(f"Profile not found: {name}")
    
    cookies_file = profile_path / "cookies.json"
    if cookies_file.exists():
        cookies = json.loads(cookies_file.read_text())
        await _context.add_cookies(cookies)
    
    ls_file = profile_path / "localStorage.json"
    if ls_file.exists():
        ls = json.loads(ls_file.read_text())
        for k, v in ls.items():
            await _page.evaluate(f"localStorage.setItem({repr(k)}, {repr(v)})")
    
    return {"loaded": name}
```

- [ ] **Step 12: Write anti-detect helpers**

```python
async def human_click(selector: str) -> dict:
    """Human-like click with random delays."""
    random_delay(0.1, 0.3)
    result = await click(selector)
    random_delay(0.5, 1.5)
    return result


async def human_type(selector: str, text: str, typo_rate: float = 0.02) -> dict:
    """Human-like typing with random delays and typos."""
    for char in text:
        if random.random() < typo_rate and char.isalnum():
            wrong = random.choice("abcdefghijklmnopqrstuvwxyz")
            await type_text(selector, wrong)
            time.sleep(random.uniform(0.1, 0.3))
            await press_key("Backspace")
            time.sleep(random.uniform(0.1, 0.2))
        await type_text(selector, char)
        time.sleep(random.uniform(0.05, 0.15))
    random_delay(0.3, 0.8)
    return {"typed": text}


async def stealth_mode(enable: bool = True) -> dict:
    """Toggle stealth mode."""
    # Camoufox handles stealth via launch parameters
    return {"stealth": enable}
```

- [ ] **Step 13: Write event retrieval function**

```python
async def drain_events() -> list:
    """Get accumulated events, clear buffer."""
    events = list(_events)
    _events.clear()
    return events
```

- [ ] **Step 14: Add json import (used in save_profile)**

Add at top of file with other imports:
```python
import json
```

- [ ] **Step 15: Run syntax check**

```bash
cd /home/michael/Github/camoufox-harness
python -m py_compile helpers.py
```

Expected: No syntax errors

- [ ] **Step 16: Commit**

```bash
git add helpers.py
git commit -m "refactor: convert helpers.py to async Playwright API"
```

---

## Task 3: Implement admin.py with launch_server

**Files:**
- Modify: `admin.py`

- [ ] **Step 1: Write PEP 723 header and imports**

```python
# /// script
# dependencies = [
#   "camoufox[geoip]>=0.4.0",
#   "psutil>=5.9.0",
# ]
# ///

"""Manage Camoufox remote server daemon."""
import os
import signal
import sys
from pathlib import Path
from threading import Thread

import psutil
```

- [ ] **Step 2: Define config and server function**

```python
NAME = os.environ.get("CH_NAME", "default")
PORT = int(os.environ.get("CH_PORT", "9222"))
WS_PATH = os.environ.get("CH_WS_PATH", "camoufox")
PID_FILE = Path(f"/tmp/camoufox-harness-{NAME}.pid")

# Server instance (global for stop)
_server_thread = None


def run_server():
    """Run Camoufox remote server (blocking)."""
    from camoufox.server import launch_server
    launch_server(
        headless=True,
        humanize=True,
        geoip=True,
        port=PORT,
        ws_path=WS_PATH,
    )
```

- [ ] **Step 3: Write daemon management functions**

```python
def is_running():
    """Check if daemon is running."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text())
        return psutil.pid_exists(pid)
    except (ValueError, psutil.NoSuchProcess):
        return False


def start_daemon():
    """Start Camoufox remote server in background thread."""
    global _server_thread
    
    if is_running():
        print(f"Daemon already running (name={NAME})", file=sys.stderr)
        return
    
    print(f"Starting Camoufox daemon (name={NAME}, port={PORT})...", file=sys.stderr)
    
    _server_thread = Thread(target=run_server, daemon=True)
    _server_thread.start()
    
    # Write PID (main process PID)
    PID_FILE.write_text(str(os.getpid()))
    print(f"Daemon started (WS: ws://localhost:{PORT}/{WS_PATH})", file=sys.stderr)


def stop_daemon():
    """Stop daemon."""
    if not PID_FILE.exists():
        print("Daemon not running", file=sys.stderr)
        return
    
    try:
        pid = int(PID_FILE.read_text())
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink()
        print(f"Daemon stopped (PID={pid})", file=sys.stderr)
    except (ValueError, ProcessLookupError):
        try:
            PID_FILE.unlink()
        except:
            pass


def restart_daemon():
    """Restart daemon."""
    stop_daemon()
    import time
    time.sleep(1)
    start_daemon()


async def ensure_daemon():
    """Ensure daemon is running."""
    if is_running():
        return
    start_daemon()
    import time
    await asyncio.sleep(2)  # Wait for server startup


def status():
    """Show daemon status."""
    if is_running():
        pid = int(PID_FILE.read_text())
        print(f"Daemon: running (PID={pid}, WS: ws://localhost:{PORT}/{WS_PATH})")
    else:
        print("Daemon: not running")
```

- [ ] **Step 4: Add asyncio import for ensure_daemon**

Add at top:
```python
import asyncio
```

- [ ] **Step 5: Write CLI entry point**

```python
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "start":
            start_daemon()
        elif cmd == "stop":
            stop_daemon()
        elif cmd == "restart":
            restart_daemon()
        elif cmd == "status":
            status()
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)
    else:
        import asyncio
        asyncio.run(ensure_daemon())
```

- [ ] **Step 6: Run syntax check**

```bash
python -m py_compile admin.py
```

Expected: No syntax errors

- [ ] **Step 7: Commit**

```bash
git add admin.py
git commit -m "refactor: convert admin.py to use camoufox.server.launch_server"
```

---

## Task 4: Implement async run.py entry point

**Files:**
- Modify: `run.py`

- [ ] **Step 1: Write PEP 723 header and imports**

```python
# /// script
# dependencies = [
#   "playwright>=1.40.0",
# ]
# ///

"""Camoufox Harness CLI (async)."""
import asyncio
import sys
from admin import ensure_daemon
from helpers import *
```

- [ ] **Step 2: Write help text and async main**

```python
HELP = """Camoufox Harness — Playwright-based browser automation with anti-detect.

Read SKILL.md for the default workflow and examples.

Typical usage:
  uv run camoufox-harness <<'PY'
  goto("https://example.com")
  wait_for_load()
  print(page_info())
  PY

Helpers are pre-imported. The daemon auto-starts Camoufox browser.
"""


async def main_async():
    if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
        print(HELP)
        return
    
    if sys.stdin.isatty():
        sys.exit(
            "camoufox-harness reads Python from stdin. Use:\n"
            "  uv run camoufox-harness <<'PY'\n"
            "  print(page_info())\n"
            "  PY"
        )
    
    await ensure_daemon()
    
    code = sys.stdin.read()
    
    # Execute async code
    # Wrap in async function if needed
    if "await " in code:
        exec(code)
    else:
        # Auto-await for simple scripts
        result = eval(code)
        if asyncio.iscoroutine(result):
            await result
```

- [ ] **Step 3: Write sync entry point**

```python
def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run syntax check**

```bash
python -m py_compile run.py
```

Expected: No syntax errors

- [ ] **Step 5: Commit**

```bash
git add run.py
git commit -m "refactor: convert run.py to async entry point"
```

---

## Task 5: Test basic functionality

**Files:**
- Test: Manual verification

- [ ] **Step 1: Start daemon**

```bash
cd /home/michael/Github/camoufox-harness
uv run admin.py start
```

Expected: "Daemon started (WS: ws://localhost:9222/camoufox)"

- [ ] **Step 2: Check status**

```bash
uv run admin.py status
```

Expected: "Daemon: running (PID=..., WS: ws://localhost:9222/camoufox)"

- [ ] **Step 3: Test basic navigation**

```bash
uv run run.py <<'PY'
import asyncio
async def test():
    result = await goto("https://example.com")
    await wait_for_load()
    info = await page_info()
    print(f"URL: {info['url']}, Title: {info['title']}")
asyncio.run(test())
PY
```

Expected: "URL: https://example.com, Title: Example Domain"

- [ ] **Step 4: Test event detection**

```bash
uv run run.py <<'PY'
import asyncio
async def test():
    await goto("https://example.com")
    await wait_for_load()
    events = await drain_events()
    print(f"Events: {events}")
asyncio.run(test())
PY
```

Expected: Events list containing load event

- [ ] **Step 5: Stop daemon**

```bash
uv run admin.py stop
```

Expected: "Daemon stopped (PID=...)"

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "test: verify basic functionality works"
```

---

## Task 6: Update documentation

**Files:**
- Modify: `README.md`, `install.md`, `SKILL.md`

- [ ] **Step 1: Update README.md architecture diagram**

Replace HTTP REST diagram with:

```markdown
## Architecture

```
┌─────────────┐    WebSocket    ┌──────────────────┐    Playwright    ┌──────────┐
│   Agent     │ ◀─────────────▶ │ Camoufox Remote  │ ────────────────▶ │ Camoufox │
│ (run.py)    │   (connect)     │ Server           │                  │ (Firefox) │
└─────────────┘                 └──────────────────┘                  └──────────┘
```

Camoufox remote server provides WebSocket endpoint. Agent connects via Playwright's `firefox.connect()`. Events flow through Playwright event handlers.
```

- [ ] **Step 2: Update install.md with async usage**

Replace sync examples with async:

```markdown
## Test Installation

```bash
uv run run.py <<'PY'
import asyncio
async def test():
    await goto("https://example.com")
    await wait_for_load()
    print(await page_info())
asyncio.run(test())
PY
```
```

- [ ] **Step 3: Update SKILL.md with async examples**

Replace all sync examples with async:

```markdown
## Quick Start

```python
# Navigate and interact
await goto("https://example.com")
await wait_for_load()
await click("#submit-button")
await type_text("#search", "query")
await press_key("Enter")

# Get page data
info = await page_info()
html = await get_html()
text = await get_text()

# Events
events = await drain_events()
```
```

- [ ] **Step 4: Commit documentation**

```bash
git add README.md install.md SKILL.md
git commit -m "docs: update for async event-driven architecture"
```

---

## Task 7: Delete obsolete daemon.py

**Files:**
- Delete: `daemon.py`

- [ ] **Step 1: Remove FastAPI daemon**

```bash
rm /home/michael/Github/camoufox-harness/daemon.py
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "refactor: remove obsolete FastAPI daemon.py"
```

---

## Verification

After all tasks complete:

- [ ] **Verify daemon starts without errors**
  ```bash
  uv run admin.py start && uv run admin.py status
  ```

- [ ] **Verify async API works**
  ```bash
  uv run run.py <<'PY'
  import asyncio
  async def test():
      await goto("https://example.com")
      await wait_for_load()
      events = await drain_events()
      assert len(events) > 0, "No events detected"
      print("✓ All checks passed")
  asyncio.run(test())
  PY
  ```

- [ ] **Verify event detection**
  ```bash
  # Test that events are captured
  uv run run.py <<'PY'
  import asyncio
  async def test():
      await goto("javascript:alert('test')")
      await asyncio.sleep(0.5)
      events = await drain_events()
      dialog_events = [e for e in events if e.get('type') == 'dialog']
      assert len(dialog_events) > 0, "Dialog not detected"
      print(f"✓ Dialog detected: {dialog_events[0]}")
  asyncio.run(test())
  PY
  ```

---

## Summary

This plan refactors camoufox-harness from HTTP REST to event-driven architecture:

1. **helpers.py** — Playwright async API instead of httpx
2. **admin.py** — camoufox.server.launch_server instead of FastAPI
3. **run.py** — Async entry point
4. **Events** — drain_events() for event retrieval

Total: 7 tasks, ~90 steps.
