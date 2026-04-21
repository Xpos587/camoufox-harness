# Dialogs

Browser dialogs (`alert`, `confirm`, `prompt`, `beforeunload`) freeze the JS thread. Playwright handles these natively via event handlers.

## Detection

`drain_events()` auto-surfaces any open dialog: dialog events are captured by `_on_dialog()` handler.

```python
events = await drain_events()
for e in events:
    if e["type"] == "dialog":
        print(e["dialog_type"])   # "alert", "confirm", "prompt", "beforeunload"
        print(e["message"])       # the dialog text
```

## Reactive: dismiss via Playwright (preferred)

Works even when JS is frozen. Handles all dialog types including `beforeunload`.

```python
# Get pending dialog info
events = await drain_events()
dialog_events = [e for e in events if e["type"] == "dialog"]

if dialog_events:
    # Dialog is pending, need to handle it
    # Playwright's page.on("dialog") handler already fired
    # To dismiss, you need to handle it before navigation/action
    pass
```

**Note:** Playwright handles dialogs automatically if you set up handlers. For manual control:

```python
# Set up dialog handler before action
async def handle_dialog(dialog):
    print(f"Dialog: {dialog.message}")
    await dialog.accept()  # or dialog.dismiss()

_page.on("dialog", handle_dialog)

# Now trigger the dialog
await click("#button_that_shows_alert")
```

## Proactive: stub via JS

Prevents dialogs from ever appearing. Good when you expect multiple `alert()`/`confirm()` calls in sequence.

```python
await js("""
window.__dialogs__=[];
window.alert=m=>window.__dialogs__.push(String(m));
window.confirm=m=>{window.__dialogs__.push(String(m));return true;};
window.prompt=(m,d)=>{window.__dialogs__.push(String(m));return d||'';};
""")
# ... do actions that trigger dialogs ...
msgs = await js("window.__dialogs__||[]")
```

Tradeoffs:
- Stubs are lost on page navigation -- must re-run the snippet
- `confirm()` always returns `true` (auto-approves)
- Detectable by antibot (`window.alert.toString()` reveals non-native code)
- Does NOT handle `beforeunload`

## beforeunload specifically

Fires when navigating away from a page with unsaved changes (forms, editors, upload pages). The page freezes until the user clicks Leave/Stay.

```python
# Set up handler before navigation
async def handle_beforeunload(dialog):
    print(f"Beforeunload: {dialog.message}")
    await dialog.accept()  # click "Leave"

_page.on("dialog", handle_beforeunload)

# Now navigate
await goto("https://new-url.com")
```

## Best Practices

1. **Check for dialogs after actions** — `drain_events()` will show if dialog appeared
2. **Handle before navigation** — set up dialog handler before `goto()` if you expect beforeunload
3. **Use reactive approach** — Playwright's dialog handlers are cleaner than JS stubs
4. **Don't forget to accept/dismiss** — unhandled dialogs freeze the page
