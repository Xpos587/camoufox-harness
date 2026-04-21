# Cross-Origin Iframes

Cross-origin iframes block direct DOM access but Playwright's frame API handles most cases.

## Finding iframes

```python
# Find iframe by URL substring
frame = await iframe_target("checkout.com")
if frame:
    # Work with the frame
    await frame.locator("#pay-button").click()
```

## Working with frames

Playwright frames have the same API as pages:

```python
# Find frame
frame = await iframe_target("embedded-widget.com")

if frame:
    # Click inside iframe
    await frame.locator("#button").click()

    # Type in iframe inputs
    await frame.locator("#email").fill("user@example.com")

    # Get iframe content
    text = await frame.locator("body").text_content()

    # Screenshot iframe
    await frame.screenshot(path="/tmp/iframe.png")
```

## List all frames

```python
# Get all frames on current page
for frame in _page.frames:
    print(f"Frame: {frame.url}")
```

## Wait for iframe to load

```python
# Find frame
frame = await iframe_target("widget.com")

if frame:
    # Wait for frame to be ready
    await frame.wait_for_load_state("domcontentloaded")

    # Now interact
    await frame.locator("#ready-button").click()
```

## Nested iframes

For iframes within iframes:

```python
# Get parent frame
parent = await iframe_target("parent.com")

if parent:
    # Get child frame from parent
    child_frames = parent.frames
    for child in child_frames:
        if "child.com" in child.url:
            # Interact with nested iframe
            await child.locator("#button").click()
```

## Same-origin iframes

If iframe is same-origin, you can also access via selector:

```python
# Click inside same-origin iframe
await _page.frame_locator("iframe#my-frame").locator("#button").click()
```

## Cross-origin limitations

Cross-origin iframes have restrictions:
- Cannot access `frame.contentDocument` directly
- Cannot read iframe HTML via JS
- Must use Playwright's frame API

**Solution:** Always use `iframe_target()` or frame locators.

## Troubleshooting

**Frame not found:**
- Check iframe URL substring matches
- Wait for page to load: `await wait_for_load()`
- Verify iframe exists: `len(_page.frames) > 1`

**Frame actions fail:**
- Frame may not be ready: `await frame.wait_for_load_state()`
- Element may be in shadow DOM: use piercing selectors
- Frame may be sandboxed: check `sandbox` attribute

**Frame URL is about:blank:**
- Frame hasn't loaded yet: wait for navigation
- Frame src may be set via JS: wait for element

## Best Practices

1. **Use `iframe_target()`** — find frames by URL substring
2. **Wait for frames** — ensure frame is loaded before interaction
3. **Handle nulls** — `iframe_target()` returns None if not found
4. **Screenshot first** — verify iframe content is visible
5. **Check frame count** — `len(_page.frames)` to see how many frames exist
