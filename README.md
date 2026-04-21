# Camoufox Harness

> Playwright-based browser automation using [Camoufox](https://github.com/daijro/camoufox) — Firefox with built-in anti-detection.

## Features

- **Anti-Detect**: Human-like behavior, fingerprint randomization, geoip spoofing
- **Playwright Async API**: Modern async browser automation
- **Event-Driven**: Real-time events (dialog detection, console logs, errors)
- **Persistent Context**: All data survives restarts (cookies, localStorage, session)
- **Domain Skills**: Auto-generated patterns for websites (private APIs, stable selectors, traps)
- **PEP 723**: Inline dependencies — no venv locking

## Quick Start

```bash
git clone https://github.com/Xpos587/camoufox-harness
cd camoufox-harness
```

```python
uv run run.py <<'PY'
await goto("https://example.com")
await wait_for_load()
print(await page_info())
PY
```

## Configuration

Create `.env` file (optional):

```bash
# Browser settings
CH_HEADLESS=true          # Headless mode
CH_HUMANIZE=true           # Human-like delays
CH_GEOIP=true              # Auto geolocation
CH_LOCALE=en-US            # Language/region

# Instance name (for multiple profiles)
CH_NAME=default
```

## Data Persistence

All browser data persists in `~/.config/camoufox-harness/profiles/<CH_NAME>/`:

- Cookies
- localStorage
- Session state
- Extensions

No manual save/load needed — just restart and continue where you left off.

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
┌─────────────┐    Async API    ┌──────────────────┐    Playwright    ┌──────────┐
│   Agent     │ ────────────────▶ │  Persistent     │ ────────────────▶ │ Camoufox │
│ (run.py)    │   (direct)       │  BrowserContext │                  │ (Firefox) │
└─────────────┘                  └──────────────────┘                  └──────────┘
```

Camoufox `AsyncNewBrowser` with `persistent_context=True` provides direct browser control. Data persists on disk between runs.

## Anti-Detect Features

| Feature | Description |
|---------|-------------|
| **humanize** | Random delays, human-like cursor movement |
| **geoip** | Geolocation spoofing based on IP |
| **fingerprint** | Randomized browser fingerprint via BrowserForge |
| **UBO** | uBlock Origin with ad/tracker blocking |

## License

MIT — see LICENSE
