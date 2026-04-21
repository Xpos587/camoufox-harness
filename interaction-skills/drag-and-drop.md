# Drag And Drop

Drag-and-drop can be driven via Playwright's native API or low-level input events. Use native API when possible.

## Native Playwright drag-and-drop (preferred)

Playwright has built-in drag-and-drop support:

```python
# Simple drag from one element to another
await _page.drag_and_drop("#source", "#target")

# With specific position
source = _page.locator("#source")
target = _page.locator("#target")
await source.drag_to(target)
```

This works for most HTML5 drag-and-drop implementations.

## Coordinate-based dragging (fallback)

For sites with custom drag implementations:

```python
# Get source element position
source = await _page.locator("#source").bounding_box()
target = await _page.locator("#target").bounding_box()

# Mouse down on source
await _page.mouse.move(source["x"] + source["width"]/2, source["y"] + source["height"]/2)
await _page.mouse.down()

# Move to target (with intermediate points for realism)
await _page.mouse.move(target["x"] + target["width"]/2, target["y"] + target["height"]/2, steps=10)
await _page.mouse.up()
```

## Sortable lists (drag to reorder)

For sortable items (jQuery UI Sortable, React DnD, etc.):

```python
# Drag item 1 to position 3
item1 = _page.locator(".sortable-item").nth(0)
item3 = _page.locator(".sortable-item").nth(2)

await item1.drag_to(item3)
```

**jQuery UI Sortable specific:**
```python
# jQuery uses specific events
await _page.locator(".sortable-item").nth(0).drag_to(
    _page.locator(".sortable-item").nth(2)
)
```

## Canvas-based dragging

For canvas elements (diagram editors, whiteboards):

```python
# Coordinate-based approach
canvas = await _page.locator("canvas").bounding_box()

# Mouse down on canvas
await _page.mouse.down(button="left", x=canvas["x"] + 100, y=canvas["y"] + 100)

# Drag
await _page.mouse.move(canvas["x"] + 200, y=canvas["y"] + 200, steps=5)

# Mouse up
await _page.mouse.up()
```

## File drag-and-drop

See `uploads.md` for file uploads via drag-and-drop zones.

## Human-like dragging

For anti-detect purposes, add randomness:

```python
import random

source = await _page.locator("#source").bounding_box()
target = await _page.locator("#target").bounding_box()

# Random delay before starting
await random_delay(0.5, 1.5)

# Mouse down with random position offset
offset_x = random.uniform(0.2, 0.8) * source["width"]
offset_y = random.uniform(0.2, 0.8) * source["height"]
await _page.mouse.move(source["x"] + offset_x, source["y"] + offset_y)
await _page.mouse.down()

# Move with random speed and slight curve
steps = random.randint(5, 15)
for i in range(steps):
    progress = i / steps
    # Add slight curve
    curve_x = random.uniform(-20, 20) * math.sin(progress * math.pi)
    x = (source["x"] + source["width"]/2) * (1 - progress) + (target["x"] + target["width"]/2) * progress + curve_x
    y = (source["y"] + source["height"]/2) * (1 - progress) + (target["y"] + target["height"]/2) * progress
    await _page.mouse.move(x, y)
    await random_delay(0.05, 0.15)

await _page.mouse.up()
```

## Touch-based dragging (mobile)

For touch devices or mobile emulation:

```python
# Touch start
await _page.touch.tap(100, 100)

# Touch move
await _page.touch.move(200, 200)

# Touch end
await _page.touch.tap(200, 200)
```

## Verification after drag

Always verify drag succeeded:

```python
# Drag element
await _page.drag_and_drop("#source", "#target")

# Verify position changed
source_pos = await _page.locator("#source").bounding_box()
target_pos = await _page.locator("#target").bounding_box()

# Or check for success indicator
success = await _page.locator(".drag-success").is_visible()
```

## Best Practices

1. **Use native API first** — `drag_and_drop()` works for most cases
2. **Screenshot before/after** — verify drag visually
3. **Add delays for anti-detect** — use `human_click()` patterns
4. **Handle sortable lists** — drag to specific index/position
5. **Test coordinate approach** — fallback if native doesn't work
6. **Verify success** — check position or success indicators

## Framework-Specific Notes

**React DnD:**
- Uses HTML5 drag-and-drop API
- Native `drag_and_drop()` should work

**jQuery UI Sortable:**
- Also HTML5-based
- May need `steps` parameter for smooth animation

**SortableJS:**
- Uses native HTML5 API
- Has `data-id` attributes for items

**Vue.Draggable:**
- Wrapper around SortableJS
- Same approach applies

**Custom canvas implementations:**
- Always coordinate-based
- May need to simulate multiple pointer events
