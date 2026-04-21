# Camoufox Harness — Install & Setup

Playwright-based browser automation using Camoufox (Firefox anti-detect browser).

## Skill Usage

This skill is installed at `~/Skills/camoufox-harness/` and includes a persistent code installation.

```bash
cd ~/Skills/camoufox-harness
./camoufox-harness <<'PY'
await goto("https://example.com")
await wait_for_load()
print(await page_info())
PY
```

## Repository Installation

For development or standalone use:

```bash
git clone https://github.com/Xpos587/camoufox-harness
cd camoufox-harness
```

## First Run

```bash
# Test installation (from repo or skill directory)
./run.py <<'PY'
await goto("https://example.com")
await wait_for_load()
print(await page_info())
PY
```

**First run downloads Firefox binary** (~300MB) via Camoufox. One-time operation.

## Configure Environment

Create `.env` file in `code/` directory (optional):

```bash
# Instance name (for multiple browser profiles)
CH_NAME=default

# Browser settings
CH_HEADLESS=true          # Headless mode
CH_HUMANIZE=true           # Human-like delays
CH_GEOIP=true              # Auto geolocation
CH_LOCALE=en-US            # Language/region
```

## Data Persistence

All browser data persists automatically in `~/.config/camoufox-harness/profiles/<CH_NAME>/`:

- Cookies
- localStorage
- Session state
- Extensions

No manual save/load needed — data survives restarts.

## Multiple Profiles

```bash
# Profile 1
cd code
CH_NAME=work ./run.py <<'PY'
await goto("https://github.com")
PY

# Profile 2 (separate cookies/storage)
CH_NAME=personal ./run.py <<'PY'
await goto("https://github.com")
PY
```

Each profile stores data in:
- `~/.config/camoufox-harness/profiles/work/`
- `~/.config/camoufox-harness/profiles/personal/`

## Anti-Detect Features

Camoufox includes built-in anti-detection:

- **humanize**: Human-like mouse movement and delays
- **geoip**: Geolocation spoofing based on IP
- **fingerprint**: Randomized browser fingerprint via BrowserForge
- **UBO**: uBlock Origin with ad/tracker blocking

Enabled via environment variables (see above).

### Human-like Interaction

```python
await human_click("#submit-button")  # Random delays
await human_type("#search", "query")  # Typing variation
await random_delay(0.5, 2)            # Random pause
```

## Video Recording

Record agent actions as MP4:

```python
async def demo():
    await goto("https://example.com")
    await click("#button")
    await wait(1)

info = await record_screen(demo, fps=10)
print(f"Video: {info['video_path']}")
# → ~/Videos/camoufox-recordings/recording-...mp4
```

Works in headless mode (uses Playwright screenshots).

## Domain Skills

Pre-configured patterns for 67+ websites in `code/domain-skills/`:

- **GitHub**: Trending repos, API data
- **Amazon**: Product search, prices
- **Ozon**: Search, scam detection, seller trust
- **Google**: Maps, Scholar
- **Twitter/X**: Search, profiles
- **Reddit**: Threads, comments
- **LinkedIn**: Profiles, jobs
- And 60+ more...

```python
# Example: GitHub trending
await goto("https://github.com/trending")
await wait_for_load()
await wait(2)

repos = json.loads(await js("""
  Array.from(document.querySelectorAll('article.Box-row')).map(el => ({
    name: el.querySelector('h2 a')?.innerText,
    url: 'https://github.com' + el.querySelector('h2 a')?.href
  }))
"""))
```

## Troubleshooting

**First run slow?**
Downloading Firefox binary (~300MB). Check progress in terminal output.

**Port conflicts?**
No ports used — persistent context architecture, no daemon needed.

**Camoufox binary location:**
Downloads to `~/.local/share/camoufox/` or system temp. Reused on subsequent runs.

**Headless vs headful:**
```bash
# Headless (default)
CH_HEADLESS=true ./run.py <<'PY' ... PY

# Headful (visible browser)
CH_HEADLESS=false ./run.py <<'PY' ... PY
```

**Profile corruption?**
```bash
# Reset profile
rm -rf ~/.config/camoufox-harness/profiles/default/
```

## Dependencies

Dependencies are declared in `pyproject.toml` and `run.py` (PEP 723):

```bash
playwright>=1.40.0
camoufox[geoip]>=0.4.0
pillow>=10.0.0
imageio[ffmpeg]>=2.31.0
```

No manual install needed — script is self-executing via PEP 723.

## Architecture

```
┌─────────────┐    Async API    ┌──────────────────┐    Playwright    ┌──────────┐
│   Agent     │ ────────────────▶ │  Persistent     │ ────────────────▶ │ Camoufox │
│  (run.py)   │   (direct)       │  BrowserContext │                  │ (Firefox) │
└─────────────┘                  └──────────────────┘                  └──────────┘
```

**No daemon, no WebSocket, no remote server** — direct Playwright async API.

## Next Steps

- **[README.md](README.md)** — Project overview and features
- **[CLAUDE.md](code/CLAUDE.md)** — Architecture and conventions
- **[SKILL.md](SKILL.md)** — Agent usage guide
- **[helpers.py](code/helpers.py)** — Full API reference with docstrings
