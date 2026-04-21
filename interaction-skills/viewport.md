# Viewport

Control viewport size for responsive testing and coordinate-based interactions.

## Get current viewport

```python
vp = await _page.viewport_size()
print(f"Viewport: {vp['width']}x{vp['height']}")
```

Also available via `page_info()`:
```python
info = await page_info()
print(f"Viewport: {info['w']}x{info['h']}")
```

## Set viewport size

```python
# Set viewport before navigation
await _page.set_viewport_size({"width": 1920, "height": 1080})
await goto("https://example.com")
```

## Common viewport sizes

```python
VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080},
    "laptop": {"width": 1366, "height": 768},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 375, "height": 667}
}

await _page.set_viewport_size(VIEWPORTS["mobile"])
await goto("https://example.com")
```

## Responsive testing

Test how site behaves at different sizes:

```python
for size_name, size in VIEWPORTS.items():
    await _page.set_viewport_size(size)
    await goto("https://example.com")
    screenshot_path = f"/tmp/{size_name}.png"
    await screenshot(screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")
```

## Viewport and coordinates

Coordinate clicks depend on viewport size:

```python
# Set viewport
await _page.set_viewport_size({"width": 1920, "height": 1080})

# Click at coordinates (relative to viewport)
await _page.mouse.click(960, 540)  # Center of 1920x1080
```

## Device emulation

For more realistic mobile testing:

```python
# Create context with device viewport
context = await _browser.new_context(
    viewport={"width": 375, "height": 667},
    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)..."
)

page = await context.new_page()
# Use page instead of _page
await page.goto("https://example.com")
```

## Screenshot with viewport

Screenshots respect current viewport:

```python
# Set mobile viewport
await _page.set_viewport_size({"width": 375, "height": 667})

# Screenshot will be 375x667 (unless full_page=True)
await screenshot("/tmp/mobile.png")
```

## Scroll and viewport

Scrolling affects coordinate clicks but not viewport size:

```python
# Viewport is fixed
vp = await _page.viewport_size()  # e.g., 1920x1080

# Scroll changes page offset
await scroll("down", 500)

# Coordinates are relative to viewport, not page
await _page.mouse.click(100, 100)  # Still viewport-relative
```

## Full page screenshot

For pages larger than viewport:

```python
# Capture entire page (including scrolled content)
await screenshot("/tmp/full.png", full=True)
```

## Troubleshooting

**Layout breaks at small sizes:**
- Site may not be responsive
- Elements may overlap or be hidden
- Use screenshot to verify layout

**Coordinates don't match:**
- Coordinates are viewport-relative
- Scroll affects page position, not viewport
- Screenshot to verify click targets

**Viewport not applied:**
- Set viewport before navigation
- Some sites may override viewport
- Check for CSS viewport constraints

## Best Practices

1. **Set viewport early** — before page load
2. **Use standard sizes** — match real devices
3. **Screenshot to verify** — check layout visually
4. **Test responsive breakpoints** — mobile, tablet, desktop
5. **Consider device emulation** — for realistic mobile testing

## Common Viewport Sizes

| Device | Width | Height | Use Case |
|:-------|-------|--------|:---------|
| Desktop 1080p | 1920 | 1080 | Full HD desktop |
| Desktop 720p | 1366 | 768 | Laptop |
| Tablet Portrait | 768 | 1024 | iPad portrait |
| Tablet Landscape | 1024 | 768 | iPad landscape |
| Mobile | 375 | 667 | iPhone SE |
| Mobile Large | 414 | 896 | iPhone 11 Pro |
| Mobile Small | 320 | 568 | iPhone 5 |
