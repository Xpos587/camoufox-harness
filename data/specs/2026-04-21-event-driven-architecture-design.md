# Camoufox Harness — Event-Driven Architecture Design

**Date:** 2026-04-21
**Status:** Draft
**Author:** Claude Code

## 1. Overview

Convert camoufox-harness from HTTP REST to event-driven architecture using Camoufox's built-in remote server (WebSocket). This enables real-time events (dialog detection, console logs, page errors) like browser-harness.

## 2. Architecture

### 2.1 Transport Layer

```
Agent (helpers.py) ──WebSocket──▶ Camoufox Remote Server ──Playwright──▶ Camoufox (Firefox)
                              WS: ws://localhost:9222/camoufox
```

- **No subprocess, stdin, stdout**
- **No custom WebSocket server** — use Camoufox built-in `launch_server()`
- **Playwright async API** for all operations

### 2.2 Components

| Component | Responsibility |
|:---|:---|
| **admin.py** | Start/stop Camoufox remote server daemon |
| **helpers.py** | Async API wrapper over Playwright remote connection |
| **run.py** | CLI entry point (async) |

### 2.3 Event Flow

```
Camoufox Event → Playwright → Event Queue (deque) → Agent (drain_events)
```

**Events:**
- `dialog` — alert/confirm/prompt opened
- `load` — page loaded
- `console` — console message
- `error` — JavaScript error

## 3. API Design

### 3.1 Connection Management

```python
# helpers.py
async def _ensure_connection():
    global _browser, _context, _page
    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.firefox.connect(WS_URL)
        _context = _browser.contexts[0]
        _page = _context.pages[0] or await _context.new_page()
        # Subscribe to events
        _page.on("dialog", _on_dialog)
        _page.on("load", _on_load)
        _page.on("console", _on_console)
        _page.on("pageerror", _on_error)
```

### 3.2 RPC Functions (async)

All functions return `dict` with results:

```python
async def goto(url: str, wait_until: str = "domcontentloaded") -> dict
async def page_info() -> dict
async def click(selector: str, button: str = "left", clicks: int = 1) -> dict
async def type_text(selector: str, text: str, delay: float = 0.05) -> dict
async def screenshot(path: str = "/tmp/shot.png", full: bool = False) -> str
```

### 3.3 Event Retrieval

```python
async def drain_events() -> list:
    """Get accumulated events, clear buffer."""
    events = list(_events)
    _events.clear()
    return events
```

## 4. Daemon Management

### 4.1 admin.py

```python
from camoufox.server import launch_server

def start_daemon():
    """Start Camoufox remote server in background thread."""
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    PID_FILE.write_text(str(os.getpid()))

def run_server():
    launch_server(
        headless=True,
        humanize=True,
        geoip=True,
        port=9222,
        ws_path='camoufox',
    )
```

**No subprocess** — `launch_server()` runs in thread.

## 5. Dependencies

All dependencies via PEP 723 (inline):

```python
# /// script
# dependencies = [
#   "playwright>=1.40.0",
#   "camoufox[geoip]>=0.4.0",
# ]
# ///
```

## 6. Migration from HTTP REST

| Before | After |
|:---|:---|
| `httpx.Client()` | `playwright.async_api` |
| FastAPI daemon | Camoufox launch_server |
| HTTP endpoints | WebSocket Playwright protocol |
| No events | Event queue + drain_events() |

## 7. Feature Parity with browser-harness

| Feature | Status |
|:---|:---|
| Dialog detection | ✅ `page.on("dialog")` |
| Event queue | ✅ `deque(maxlen=500)` |
| drain_events() | ✅ Implemented |
| Domain skills | ⏳ Port from browser-harness |
| Iframe support | ⏳ Playwright `frame_locator()` |
| Tab marking | ⏳ Add emoji to title |

## 8. Next Steps

1. Implement async helpers.py with Playwright connect
2. Implement admin.py with launch_server
3. Add drain_events() and event handlers
4. Port domain skills logic from browser-harness
5. Test dialog detection
