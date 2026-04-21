# Camoufox Harness — Agent Skill

Playwright-based browser automation with anti-detect. Read `helpers.py` for all available functions.

## Quick Start

```python
# Navigate and interact
goto("https://example.com")
wait_for_load()
click("#submit-button")
type_text("#search", "query")
press_key("Enter")

# Get page data
info = page_info()  # {url, title, w, h}
html = get_html()
text = get_text()

# Screenshot
screenshot("/tmp/shot.png")

# Execute JavaScript
result = js("document.title")
```

## Anti-Detect Automation

```python
# Enable stealth mode
stealth_mode(enable=True)

# Human-like interaction
human_click("#button")       # Random delays
human_type("#input", "text") # Typo simulation

# Random delays
random_delay(0.5, 2.0)  # 0.5-2.0 seconds
wait(1.0)               # Fixed delay
```

## Page Interaction

```python
# Wait for load
wait_for_load(timeout=15.0)

# Scroll
scroll("down", 300)   # direction, amount
scroll("up", 300)

# Tabs
new_tab("https://example.com")
switch_tab(0)
close_tab()

# Snapshot (accessibility tree)
snap = snapshot()
```

## Cookies & Storage

```python
# Get/set cookies
cookies = get_cookies()
set_cookies([{"name": "key", "value": "val", "domain": ".example.com"}])

# LocalStorage
ls = get_local_storage()
set_local_storage({"key": "value"})
```

## Geolocation & Proxy

```python
# Set geolocation
set_geolocation(40.7128, -74.0060)  # NYC

# Set proxy (requires restart)
set_proxy({"server": "http://proxy:8080"})
```

## Profile Persistence

```python
# Save session
save_profile("github-session")

# Load session
load_profile("github-session")
```

## Best Practices

1. **Use stealth_mode()** for anti-bot sites
2. **Add random delays** between actions
3. **Check for blocking** after navigation
4. **Save profiles** for session persistence

## Example: E-commerce Search

```python
goto("https://shop.example.com")
wait_for_load()

human_type("#search", "laptop")
press_key("Enter")
wait_for_load()

# Check for blocking
text = get_text()
if "blocked" in text.lower():
    stealth_mode(enable=True)
    goto("https://shop.example.com")

# Get results
items = js("Array.from(document.querySelectorAll('.item')).map(el => el.textContent)")
print(items)
```
