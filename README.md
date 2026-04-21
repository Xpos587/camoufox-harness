# Camoufox Harness

> Playwright-based browser automation using [Camoufox](https://github.com/daijro/camoufox) — Firefox with built-in anti-detection.

## Features

- **Anti-Detect**: Human-like behavior, fingerprint randomization, geoip spoofing
- **Playwright Async API**: Modern async browser automation
- **Event-Driven**: Real-time events (dialog detection, console logs, errors)
- **Camoufox Remote Server**: WebSocket endpoint for browser control
- **Profile Persistence**: Save/load browser sessions
- **Domain Skills**: Auto-generated patterns for websites (private APIs, stable selectors, traps)
- **PEP 723**: Inline dependencies — no venv locking

## Quick Start

```bash
git clone https://github.com/Xpos587/camoufox-harness
cd camoufox-harness
uv run admin.py start
```

```python
uv run run.py <<'PY'
import asyncio
async def test():
    await goto("https://example.com")
    await wait_for_load()
    print(await page_info())
asyncio.run(test())
PY
```

## Documentation

- `install.md` — Installation & setup
- `SKILL.md` — Agent usage guide (including domain skills)
- `helpers.py` — Core API reference
- `domain-skills/` — Auto-generated site patterns
- `interaction-skills/` — Reusable UI patterns:
  - `connection.md` — Startup sequence, tab visibility, auto-recovery
  - `cookies.md` — Cookie management and session persistence
  - `cross-origin-iframes.md` — Working with iframes across origins
  - `dialogs.md` — Handling alert/confirm/prompt/beforeunload
  - `downloads.md` — Browser-triggered downloads
  - `drag-and-drop.md` — Drag and drop operations
  - `dropdowns.md` — Native selects, comboboxes, virtualized menus
  - `network-requests.md` — Request interception and monitoring
  - `print-as-pdf.md` — PDF generation
  - `shadow-dom.md` — Piercing shadow DOM
  - `uploads.md` — File upload handling
  - `viewport.md` — Viewport control and responsive testing

## Architecture

```
┌─────────────┐    WebSocket    ┌──────────────────┐    Playwright    ┌──────────┐
│   Agent     │ ◀─────────────▶ │ Camoufox Remote  │ ────────────────▶ │ Camoufox │
│ (run.py)    │   (connect)     │ Server           │                  │ (Firefox) │
└─────────────┘                 └──────────────────┘                  └──────────┘
```

Camoufox remote server provides WebSocket endpoint. Agent connects via Playwright's `firefox.connect()`. Events flow through Playwright event handlers.

## Anti-Detect Features

| Feature | Description |
|---------|-------------|
| **humanize** | Random delays, human-like cursor movement |
| **geoip** | Geolocation spoofing |
| **fingerprint** | Randomized browser fingerprint |
| **nagle** | Network timing optimization |

## License

MIT — see LICENSE
