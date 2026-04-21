# Camoufox Harness — Install & Setup

Playwright-based browser automation using Camoufox (Firefox anti-detect browser).

## Quick Install

```bash
git clone https://github.com/Xpos587/camoufox-harness
cd camoufox-harness
uv sync
```

## Start Daemon

```bash
# Start in background
uv run admin.py start

# Or run directly (foreground)
uv run daemon.py
```

## Verify Installation

```bash
uv run run.py <<'PY'
goto("https://example.com")
wait_for_load()
print(page_info())
PY
```

## Configure Environment

Create `.env` file (optional):

```bash
# Instance name (for multiple browsers)
CH_NAME=default

# API URL (default: http://127.0.0.1:8765)
CH_API_URL=http://127.0.0.1:8765

# Daemon host/port
CH_HOST=127.0.0.1
CH_PORT=8765
```

## Anti-Detect Features

Camoufox includes built-in anti-detection:

- **humanize**: Human-like mouse movement and delays
- **geoip**: Geolocation spoofing
- **fingerprint**: Randomized browser fingerprint
- **nagle**: Network timing optimization

Enable per-request:

```python
from helpers import stealth_mode, human_click, human_type

stealth_mode(enable=True)
human_click("#submit-button")
human_type("#search", "query")
```

## Profile Management

Save/load browser sessions:

```python
# Save current session (cookies, localStorage)
save_profile("mysession")

# Load saved session
load_profile("mysession")
```

## Daemon Commands

```bash
uv run admin.py start     # Start daemon
uv run admin.py stop      # Stop daemon
uv run admin.py restart   # Restart daemon
uv run admin.py status    # Check status
```

## Troubleshooting

**Daemon not responding:**
```bash
uv run admin.py restart
```

**Port already in use:**
```bash
# Change port in .env
echo "CH_PORT=8766" >> .env
uv run admin.py restart
```

**Camoufox download stuck:**
First run downloads Firefox binary (~300MB). Check `/tmp/camoufox-harness-*.log` for progress.
