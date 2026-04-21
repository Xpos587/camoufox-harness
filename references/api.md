# Camoufox Harness — Full API Reference

Complete list of all available helper functions in `helpers.py`.

## Navigation

| Function | Description | Example |
|----------|-------------|---------|
| `goto(url, wait_until)` | Navigate to URL | `await goto("https://example.com")` |
| `page_info()` | Get {url, title, w, h} | `await page_info()` |
| `wait_for_load(timeout)` | Wait for page load | `await wait_for_load(15)` |
| `wait(seconds)` | Sleep for N seconds | `await wait(1)` |
| `random_delay(min, max)` | Random anti-detect delay | `await random_delay(0.5, 2)` |

## Input

| Function | Description | Example |
|----------|-------------|---------|
| `click(selector, button, clicks)` | Click element | `await click("#btn", "left", 2)` |
| `type_text(selector, text, delay)` | Type into element | `await type_text("#input", "text")` |
| `press_key(key, modifiers)` | Press keyboard key | `await press_key("Enter", ["Control"])` |
| `scroll(direction, amount)` | Scroll page | `await scroll("down", 500)` |
| `human_click(selector)` | Human-like click | `await human_click("#btn")` |
| `human_type(selector, text)` | Human-like typing | `await human_type("#input", "text")` |

## Tabs

| Function | Description | Example |
|----------|-------------|---------|
| `new_tab(url)` | Create new tab | `await new_tab("https://example.com")` |
| `switch_tab(tab_id)` | Switch to tab | `await switch_tab(0)` |
| `close_tab()` | Close current tab | `await close_tab()` |
| `list_tabs()` | List all tabs | `await list_tabs()` |
| `current_tab()` | Get current tab info | `await current_tab()` |
| `ensure_real_tab()` | Auto-recovery from internal | `await ensure_real_tab()` |

## Data Extraction

| Function | Description | Example |
|----------|-------------|---------|
| `screenshot(path, full)` | Take screenshot | `await screenshot("/tmp/shot.png")` |
| `snapshot()` | Get accessibility tree | `await snapshot()` |
| `get_html()` | Get page HTML | `await get_html()` |
| `get_text()` | Get visible text | `await get_text()` |
| `js(expression)` | Execute JavaScript | `await js("document.title")` |

## Events

| Function | Description | Example |
|----------|-------------|---------|
| `drain_events()` | Get/clear event buffer | `await drain_events()` |

## Storage

| Function | Description | Example |
|----------|-------------|---------|
| `get_cookies()` | Get all cookies | `await get_cookies()` |
| `set_cookies(cookies)` | Set cookies | `await set_cookies(cookies)` |
| `get_local_storage()` | Get localStorage | `await get_local_storage()` |
| `set_local_storage(items)` | Set localStorage | `await set_local_storage({"key": "value"})` |

## Video Recording

| Function | Description | Example |
|----------|-------------|---------|
| `record_screen(func, video_dir, fps)` | Record screen to MP4 | `await record_screen(demo, fps=10)` |
| `get_video_path()` | Get video file path | `await get_video_path()` |

## Domain Skills

| Function | Description | Example |
|----------|-------------|---------|
| `save_domain_skill(site, content)` | Save learned patterns | `await save_domain_skill("github", content)` |

## Utility

| Function | Description | Example |
|----------|-------------|---------|
| `stealth_mode(enable)` | Toggle stealth mode | `await stealth_mode(True)` |
| `get_profile_dir()` | Get profile directory path | `get_profile_dir()` |
| `_cleanup()` | Close browser context | `await _cleanup()` |

## Event Types

Events collected in buffer (accessed via `drain_events()`):

| Type | Fields | Description |
|------|--------|-------------|
| `dialog` | message, dialog_type | Alert/confirm/prompt dialogs |
| `load` | url | Page load events |
| `console` | level, text | Console log messages |
| `error` | message | Page errors |

## Advanced Usage

### Custom event handling

```python
# Check for dialogs after navigation
await goto("https://example.com")
events = await drain_events()
dialogs = [e for e in events if e["type"] == "dialog"]

if dialogs:
    print(f"Dialog detected: {dialogs[0]['message']}")
```

### iframe targeting

```python
# Find iframe by URL substring
frame = await iframe_target("https://embed.example.com")
if frame:
    result = await frame.evaluate("document.title")
```

### Persistent profiles

```bash
# Use multiple named profiles
CH_NAME=profile1 uv run run.py <<'PY'
await goto("https://example.com")
PY

# Each profile has separate cookies/storage
# ~/.config/camoufox-harness/profiles/profile1/
# ~/.config/camoufox-harness/profiles/profile2/
```

### Video recording workflow

```python
async def demo_workflow():
    await goto("https://example.com")
    await click("#search")
    await type_text("#search", "test")
    await press_key("Enter")
    await wait_for_load()
    return {"status": "done"}

# Record to ~/Videos/camoufox-recordings/
info = await record_screen(demo_workflow, fps=10)
print(f"Video: {info['video_path']}")
```

## Type Signatures

```python
async def goto(url: str, wait_until: str = "domcontentloaded") -> dict
async def page_info() -> dict
async def wait_for_load(timeout: float = 15.0) -> bool
async def wait(seconds: float = 1.0) -> None
async def random_delay(min_sec: float = 0.5, max_sec: float = 2.0) -> None

async def click(selector: str, button: str = "left", clicks: int = 1) -> dict
async def type_text(selector: str, text: str, delay: float = 0.05) -> dict
async def press_key(key: str, modifiers: list = None) -> dict
async def scroll(direction: str = "down", amount: int = 300) -> dict

async def screenshot(path: str = "/tmp/shot.png", full: bool = False) -> str
async def snapshot() -> dict
async def get_html() -> str
async def get_text() -> str
async def js(expression: str) -> Any

async def new_tab(url: str = "about:blank") -> dict
async def switch_tab(tab_id: int) -> dict
async def close_tab() -> dict
async def list_tabs(include_chrome: bool = True) -> list
async def current_tab() -> dict

async def get_cookies() -> list
async def set_cookies(cookies: list) -> dict
async def get_local_storage() -> dict
async def set_local_storage(items: dict) -> dict

async def record_screen(func: Callable, video_dir: str = None, fps: int = 10) -> dict
async def drain_events() -> list
```
