---
name: camoufox-harness
description: >
  Use when the user wants to automate browser interactions, scrape websites, test web applications,
  or interact with e-commerce platforms like Ozon, Amazon, or GitHub. Trigger on requests like:
  "automate this website", "scrape product data", "test login flow", "interact with Ozon/Amazon",
  or any browser automation task requiring anti-detection features.
---

# Camoufox Harness — Browser Automation with Anti-Detection

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Core API](#core-api)
- [Domain Skills](#domain-skills)
- [Interaction Skills](#interaction-skills)
- [Video Recording](#video-recording)
- [Anti-Detect Features](#anti-detect-features)
- [Examples](#examples)

## Overview

Playwright-based browser automation using **Camoufox** (Firefox with built-in anti-detection).

**Key capabilities:**
- Navigate, click, type, scroll — full browser control
- Event-driven: dialog detection, console logs, errors
- Persistent context: cookies, localStorage, sessions survive restarts
- Anti-detect: humanize delays, fingerprint randomization, geoip spoofing
- Video recording: screen capture for demos/debugging
- Domain skills: 67+ pre-configured site patterns (GitHub, Amazon, Ozon, etc.)

**Workflow:**
```
User Query → Select Domain Skill → Run helpers.py functions → Extract data
```

## Prerequisites

**Dependencies** (auto-installed via PEP 723):
```bash
# No manual install needed - uv run resolves dependencies
playwright>=1.40.0
camoufox[geoip]>=0.4.0
pillow>=10.0.0
imageio[ffmpeg]>=2.31.0
```

**First run** downloads Firefox binary (~300MB) via Camoufox.

## Quick Start

Run from the skill directory (script is self-executing via PEP 723):

```bash
./camoufox-harness <<'PY'
await goto("https://example.com")
await wait_for_load()
print(await page_info())
PY
```

**All helpers are pre-imported** — no imports needed in your code.

## Core API

### Navigation

```python
# Navigate to URL
await goto("https://github.com")
await wait_for_load()

# Get page info
info = await page_info()
# → {"url": "...", "title": "...", "w": 1280, "h": 720}

# Take screenshot
await screenshot("/tmp/shot.png")
```

### Input

```python
# Click element
await click("#submit-button")

# Type text
await type_text("#search", "mechanical keyboard")

# Press key
await press_key("Enter")

# Scroll
await scroll("down", 500)
```

### Tabs

```python
# New tab (marked with 🟢)
await new_tab("https://example.com")

# Switch tab
await switch_tab(tab_id)

# List tabs
tabs = await list_tabs()
```

### Events

```python
# Drain accumulated events
events = await drain_events()

# Filter events
dialogs = [e for e in events if e["type"] == "dialog"]
errors = [e for e in events if e["type"] == "error"]
```

### Storage

```python
# Get cookies
cookies = await get_cookies()

# Get localStorage
storage = await get_local_storage()
```

## Domain Skills

Pre-configured patterns for 67+ websites in `code/domain-skills/`:

| Site | Skills | Use Cases |
|------|--------|-----------|
| **GitHub** | scraping, repo-actions | Trending repos, API data, commits |
| **Amazon** | product-search | Product cards, prices, ratings |
| **Ozon** | search, product-analysis, scam-detection | Product search, seller trust, review analysis |
| **Google** | maps, scholar | Maps data, academic papers |
| **Twitter/X** | search, profile | Tweet extraction, user data |
| **Reddit** | search, comments | Thread analysis, comment scraping |
| **LinkedIn** | profile, jobs | Profile data, job postings |
| **Netflix** | browse | Catalog scraping |
| **Stack Overflow** | search, answers | Question/answer extraction |

**Example: GitHub scraping**
```python
# Trending repos
await goto("https://github.com/trending")
await wait_for_load()
await wait(2)

repos = json.loads(await js("""
  Array.from(document.querySelectorAll('article.Box-row')).map(el => ({
    name: el.querySelector('h2 a')?.innerText,
    url: 'https://github.com' + el.querySelector('h2 a')?.href,
    stars: el.querySelector('a[href*="/stargazers"]')?.innerText
  }))
"""))
```

**Example: Ozon scam detection**
```python
# Search products
await goto("https://www.ozon.ru/search/?text=ноутбук")
products = json.loads(await js("/* extraction from domain-skills/ozon/search.md */"))

# Analyze seller trust
result = await full_scam_check(products[0]['url'])
# → {"verdict": "SAFE"/"CAUTION"/"AVOID", "score": 5, "red_flags": [...]}
```

## Interaction Skills

Reusable UI patterns in `code/interaction-skills/`:

| Skill | Description |
|-------|-------------|
| **dialogs.md** | alert/confirm/prompt handling |
| **dropdowns.md** | Native selects, virtualized menus |
| **uploads.md** | File upload via set_input_files() |
| **drag-and-drop.md** | Drag operations API |
| **network-requests.md** | Request interception/monitoring |
| **shadow-dom.md** | Piercing shadow DOM |
| **viewport.md** | Viewport control for responsive testing |

## Video Recording

Record agent actions as MP4 video:

```python
async def demo():
    await goto("https://example.com")
    await click("#button")
    await wait(1)

info = await record_screen(demo, fps=10)
# → {"video_path": "~/Videos/camoufox-recordings/recording-...mp4", "frames": 15}
```

**Works in headless mode** — uses Playwright screenshots, not screen capture.

## Anti-Detect Features

| Feature | Description |
|---------|-------------|
| **humanize** | Random delays, human-like cursor movement |
| **geoip** | Geolocation spoofing based on IP |
| **fingerprint** | Randomized browser fingerprint via BrowserForge |
| **UBO** | uBlock Origin with ad/tracker blocking |

**Configuration** (`code/.env` file):
```bash
CH_HEADLESS=true          # Headless mode
CH_HUMANIZE=true           # Human-like delays
CH_GEOIP=true              # Auto geolocation
CH_LOCALE=en-US            # Language/region
CH_NAME=default            # Instance name (for multiple profiles)
```

## Data Persistence

All browser data persists in `~/.config/camoufox-harness/profiles/<CH_NAME>/`:

- Cookies
- localStorage
- Session state
- Extensions

No manual save/load needed — just restart and continue.

## Examples

### Web scraping

```python
await goto("https://news.ycombinator.com")
await wait_for_load()

stories = json.loads(await js("""
  Array.from(document.querySelectorAll('.titleline > a')).map(a => ({
    title: a.innerText,
    url: a.href
  }))
"""))
```

### Form automation

```python
await goto("https://example.com/login")
await type_text("#email", "user@example.com")
await type_text("#password", "secret")
await click("#login-button")
await wait_for_load()
```

### E-commerce monitoring

```python
# Search Amazon
await goto("https://www.amazon.com/s?k=mechanical+keyboard")
await wait_for_load()
await wait(2)

products = json.loads(await js("/* from domain-skills/amazon/product-search.md */"))
deals = [p for p in products if int(p.get('discount_pct', 0)) >= 30]
```

### Multi-step workflow

```python
# Navigate through pages
await goto("https://example.com")
await click("#products")
await wait_for_load()

# Extract data
items = json.loads(await js("..."))

# Save to file
import json
with open("results.json", "w") as f:
    json.dump(items, f)
```

## Gotchas

- **First run**: Downloads Firefox binary (~300MB) — one-time operation
- **Event handlers**: Dialogs auto-detected via `drain_events()`
- **Selectors**: Use CSS selectors, avoid obfuscated classes
- **Dynamic content**: Use `await wait(1-2)` after page load for JS rendering
- **Profile persistence**: Data survives restarts in `~/.config/camoufox-harness/profiles/`

## Search First

Before writing new automation, search `domain-skills/` for existing patterns:

```bash
cd code
rg --files domain-skills
rg -n "ozon|scam" domain-skills
```

Only if struggling with a specific mechanic, look in `interaction-skills/` for helpers.

## Always Contribute Back

**If you learned anything non-obvious about how a site works, add it to `domain-skills/<site>/` before you finish.** The harness gets better only because agents file what they learn.

**Worth contributing:**
- **Private API** — XHR/fetch endpoints, request shape, auth (often 10× faster than DOM)
- **Stable selector** — beats the obvious one, or obfuscated class to avoid
- **Framework quirk** — "React combobox only commits on Escape", "Vue list only renders in scroll container"
- **URL pattern** — direct route, required query params, variant that skips loader
- **Wait** that `wait_for_load()` misses, with the reason
- **Trap** — stale drafts, legacy IDs, unicode quirks, CAPTCHA surfaces

**What a domain skill should capture:**
- URL patterns and query params
- Private APIs and payload shape
- Stable selectors (`data-*`, `aria-*`, `role`, semantic classes)
- Site structure — containers, items per page, framework, state location
- Framework/interaction quirks unique to this site
- Waits and reasons they're needed
- Traps and selectors that *don't* work

**Do not write:**
- **Raw pixel coordinates** — break on viewport/zoom/layout. Describe how to *locate* the target (selector, `scrollIntoView`, `aria-label`)
- **Run narration** or step-by-step of the specific task you just did
- **Secrets, cookies, session tokens, user-specific state**

## What Actually Works

- **Screenshots first** — use `screenshot()` to understand the page quickly, find visible targets
- **After goto** — always `wait_for_load()` then `await wait(1-2)` for JS rendering
- **DOM reads** — use `js(...)` for inspection and extraction (JSON output)
- **Verification** — `print(page_info())` for simple "is this alive?" check
- **Events** — check `drain_events()` for dialogs after actions that trigger prompts
- **Anti-detect** — use `human_click()`, `human_type()`, `random_delay()` for human-like behavior

## Design Constraints

- **Camoufox runs locally** — persistent context, no remote server needed
- **PEP 723 dependencies** — inline in `run.py`, `uv run` resolves automatically
- **Helpers stay short** — browser primitives in `helpers.py`
- **Don't add a manager layer** — no retries framework, session manager, config system
- **The code is the doc** — read `helpers.py` for inline documentation

## Repository

- **GitHub**: https://github.com/Xpos587/camoufox-harness
- **Documentation**: `code/README.md`, `code/CLAUDE.md`, `code/helpers.py` (inline docs)
- **Domain skills**: `code/domain-skills/` (67+ sites)
- **Interaction skills**: `code/interaction-skills/` (19 patterns)

## See Also

- **[references/api.md](references/api.md)** — Full API reference
- **[references/examples.md](references/examples.md)** — Common automation patterns
- **[code/CLAUDE.md](code/CLAUDE.md)** — Project architecture and conventions
