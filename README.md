# Camoufox Harness

> Playwright-based browser automation using [Camoufox](https://github.com/daijro/camoufox) — Firefox with built-in anti-detection.

## Features

- **Anti-Detect**: Human-like behavior, fingerprint randomization, geoip spoofing
- **Playwright API**: Modern async browser automation
- **REST Interface**: FastAPI daemon for language-agnostic access
- **Profile Persistence**: Save/load browser sessions
- **PEP 723**: Inline dependencies — no venv locking

## Quick Start

```bash
git clone https://github.com/Xpos587/camoufox-harness
cd camoufox-harness
uv sync
uv run admin.py start
```

```python
# uv run run.py <<'PY'
goto("https://example.com")
wait_for_load()
print(page_info())
# PY
```

## Documentation

- `install.md` — Installation & setup
- `SKILL.md` — Agent usage guide
- `helpers.py` — Core API reference

## Architecture

```
┌─────────────┐     HTTP      ┌──────────────┐     Playwright     ┌──────────┐
│   Agent     │ ────────────▶ │ FastAPI      │ ──────────────────▶ │ Camoufox │
│ (run.py)    │               │ daemon.py    │                    │ (Firefox) │
└─────────────┘               └──────────────┘                    └──────────┘
```

## Anti-Detect Features

| Feature | Description |
|---------|-------------|
| **humanize** | Random delays, human-like cursor movement |
| **geoip** | Geolocation spoofing |
| **fingerprint** | Randomized browser fingerprint |
| **nagle** | Network timing optimization |

## License

MIT — see LICENSE
