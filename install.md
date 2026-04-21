# Camoufox Harness — Install & Setup

Playwright-based browser automation using Camoufox (Firefox anti-detect browser).

## Quick Install

```bash
git clone https://github.com/Xpos587/camoufox-harness
cd camoufox-harness
```

## Start Daemon

```bash
# Start Camoufox remote server
uv run admin.py start
```

## Verify Installation

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

## Configure Environment

Create `.env` file (optional):

```bash
# Instance name (for multiple browsers)
CH_NAME=default

# WebSocket URL (default: ws://127.0.0.1:9222/camoufox)
CH_WS_URL=ws://127.0.0.1:9222/camoufox

# Daemon port
CH_PORT=9222

# WebSocket path
CH_WS_PATH=camoufox
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

await stealth_mode(enable=True)
await human_click("#submit-button")
await human_type("#search", "query")
```

## Profile Management

Save/load browser sessions:

```python
# Save current session (cookies, localStorage)
await save_profile("mysession")

# Load saved session
await load_profile("mysession")
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
echo "CH_PORT=9223" >> .env
uv run admin.py restart
```

**Camoufox download stuck:**
First run downloads Firefox binary (~300MB). Check `/tmp/camoufox-harness-*.log` for progress.
