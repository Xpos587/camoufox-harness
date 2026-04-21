# Camoufox Harness — Agent Skill

Playwright-based browser automation with anti-detect. Read `helpers.py` for all available functions.

## Quick Start

```python
# Navigate and interact
await goto("https://example.com")
await wait_for_load()
await click("#submit-button")
await type_text("#search", "query")
await press_key("Enter")

# Get page data
info = await page_info()  # {url, title, w, h}
html = await get_html()
text = await get_text()

# Screenshot
await screenshot("/tmp/shot.png")

# Execute JavaScript
result = await js("document.title")

# Events
events = await drain_events()
```

## Anti-Detect Automation

```python
# Enable stealth mode
await stealth_mode(enable=True)

# Human-like interaction
await human_click("#button")       # Random delays
await human_type("#input", "text") # Typo simulation

# Random delays
await random_delay(0.5, 2.0)  # 0.5-2.0 seconds
await wait(1.0)               # Fixed delay
```

## Page Interaction

```python
# Wait for load
await wait_for_load(timeout=15.0)

# Scroll
await scroll("down", 300)   # direction, amount
await scroll("up", 300)

# Tabs
await new_tab("https://example.com")
await close_tab()

# Snapshot (accessibility tree)
snap = await snapshot()
```

## Cookies & Storage

```python
# Get/set cookies
cookies = await get_cookies()
await set_cookies([{"name": "key", "value": "val", "domain": ".example.com"}])

# LocalStorage
ls = await get_local_storage()
await set_local_storage({"key": "value"})
```

## Geolocation & Proxy

```python
# Set geolocation
await set_geolocation(40.7128, -74.0060)  # NYC
```

## Profile Persistence

All data persists automatically in `~/.config/camoufox-harness/profiles/<CH_NAME>/`:

- Cookies
- localStorage
- Session state

No manual save/load needed — just restart and continue.

### Multiple Profiles

```bash
# Use different profiles for separate sessions
CH_NAME=work uv run run.py <<'PY'
await goto("https://github.com")
PY

CH_NAME=personal uv run run.py <<'PY'
await goto("https://github.com")
PY
```

## Best Practices

1. **Use stealth_mode()** for anti-bot sites
2. **Add random delays** between actions
3. **Check for blocking** after navigation
4. **Use CH_NAME env var** for multiple profiles
5. **Always use async/await** — all functions are async
6. **Contribute domain skills** — When you learn non-obvious patterns about a site, save them with `save_domain_skill()`

## Example: E-commerce Search

```python
await goto("https://shop.example.com")
await wait_for_load()

await human_type("#search", "laptop")
await press_key("Enter")
await wait_for_load()

# Check for blocking
text = await get_text()
if "blocked" in text.lower():
    await stealth_mode(enable=True)
    await goto("https://shop.example.com")

# Get results
items = await js("Array.from(document.querySelectorAll('.item')).map(el => el.textContent)")
print(items)
```

## Event Detection

```python
# Navigate and capture events
await goto("https://example.com")
await wait_for_load()

# Get all events (load, console, dialog, errors)
events = await drain_events()

# Filter for specific event types
dialogs = [e for e in events if e.get('type') == 'dialog']
errors = [e for e in events if e.get('type') == 'error']
```

## Domain Skills

Domain skills are auto-generated `.md` files containing learned patterns for specific websites. When you navigate to a site, `goto()` returns available skills.

```python
# Navigate and check for existing skills
result = await goto("https://github.com")
print(result["domain_skills"])  # ['20260421-123456.md', ...]

# Save learned patterns
await save_domain_skill("github", """
# GitHub Login Patterns

## Stable Selectors
- Login button: `[href="/login"]`
- Email input: `#login_field`

## URL Patterns
- Direct login: https://github.com/login
- Session persists across subdomains

## Traps
- Avoid `.js-*` classes (obfuscated)
- 2FA may appear after successful auth
""")
```

**What to save in domain skills:**
- Private API endpoints
- Stable selectors (`data-*`, `aria-*`, `role`)
- URL patterns and query params
- Framework quirks
- Traps and selectors that DON'T work
```
