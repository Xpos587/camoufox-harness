# Connection & Tab Visibility

## Startup sequence

Camoufox remote server starts automatically when you run any command. The daemon ensures a connection is established before executing your code.

```python
# Connection is automatic - just run your code
await goto("https://example.com")
await wait_for_load()
```

The `_ensure_connection()` function handles:
- Connecting to Camoufox remote server via WebSocket
- Creating or reusing browser context
- Attaching to first available page
- Subscribing to events (dialog, load, console, error)

## Tab visibility

Tabs are marked with 🟢 prefix so you can see which tab the agent controls:

```python
# New tabs are automatically marked
await new_tab("https://example.com")  # Title shows "🟢 Example Domain"

# Switching tabs updates the mark
await switch_tab(0)  # Old tab unmarked, new tab marked
```

## Checking available tabs

```python
# List all tabs (including internal chrome:// pages)
tabs = await list_tabs()
for t in tabs:
    print(f"{t['id']}: {t['url'][:60]}")

# List only real user tabs (excludes chrome://, about://, etc.)
real_tabs = await list_tabs(include_chrome=False)
```

## Auto-recovery from stale tabs

If you end up on an internal page or stale session:

```python
# Automatically switch to first real user tab
tab = await ensure_real_tab()
if tab:
    print(f"Switched to: {tab['url']}")
else:
    print("No real tabs available")
```

## Current tab info

```python
# Get current tab details
info = await current_tab()
print(f"Tab {info['id']}: {info['title']}")
print(f"URL: {info['url']}")
```

## Bringing browser to front

Camoufox runs headless by default. For visible browser:

```python
# In admin.py, set headless=False when launching server:
# launch_server(headless=False, ...)
```

## Navigating

Prefer using existing tabs over creating new ones:

```python
# Use existing tab
tab = await ensure_real_tab()
await goto("https://example.com")

# Or create new tab
await new_tab("https://example.com")
```

## Connection troubleshooting

**Daemon not responding:**
```bash
uv run admin.py restart
```

**Connection errors:**
- Check Camoufox server is running: `uv run admin.py status`
- Verify WebSocket URL in `.env`: `CH_WS_URL=ws://127.0.0.1:9222/camoufox`
- Check for port conflicts: change `CH_PORT` in `.env`

**Stale sessions:**
- Use `ensure_real_tab()` to recover
- Or restart daemon: `uv run admin.py restart`
