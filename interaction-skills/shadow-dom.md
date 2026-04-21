# Shadow DOM

Shadow DOM encapsulates DOM trees within components. Playwright can pierce shadow DOM automatically.

## Accessing shadow DOM elements

Playwright pierces shadow DOM by default:

```python
# This works even if element is inside shadow DOM
await click("#shadow-button")
await _page.locator("#shadow-input").fill("text")
```

## Piercing multiple shadow roots

For deeply nested shadow DOM:

```python
# Playwright automatically traverses all shadow roots
await _page.locator("deep-root >> #inner-button").click()
```

The `>>` combinator pierces shadow boundaries.

## Custom shadow piercing

For specific shadow root access:

```python
# Get shadow host
host = await _page.locator("custom-widget").element_handle()

# Access shadow root
shadow_root = await host.evaluate_handle("el => el.shadowRoot")

# Query inside shadow root
button = await shadow_root.evaluate_handle(
    "root => root.querySelector('#button')"
)
await button.click()
```

## Wait for shadow DOM content

Shadow DOM may load asynchronously:

```python
# Wait for shadow element
await _page.wait_for_selector("custom-widget >> #shadow-button", state="visible")

# Now interact
await click("custom-widget >> #shadow-button")
```

## List shadow hosts

Find all elements with shadow DOM:

```python
# Find all shadow hosts
hosts = await _page.locator("*").all()
for host in hosts:
    has_shadow = await host.evaluate("el => !!el.shadowRoot")
    if has_shadow:
        print(f"Shadow host: {await host.evaluate('el => el.tagName')}")
```

## Shadow DOM in iframes

Combine shadow DOM with iframe access:

```python
# Get frame
frame = await iframe_target("widget.com")

if frame:
    # Access shadow DOM inside frame
    await frame.locator("custom-widget >> #shadow-button").click()
```

## Web Components

Many web components use shadow DOM:

```python
# Example: <video-element> with shadow DOM
await _page.locator("video-element >> #play-button").click()

# Example: <date-picker> with shadow DOM
await _page.locator("date-picker >> .calendar-day").click()
```

## Open vs closed shadow DOM

- **Open shadow DOM** — accessible via `element.shadowRoot`
- **Closed shadow DOM** — not accessible via JS

Playwright can pierce both open and closed shadow DOM in most cases.

## Troubleshooting

**Selector doesn't work:**
- Verify element is actually in shadow DOM
- Try `>>` combinator for explicit piercing
- Wait for shadow content to load: `wait_for_selector()`

**Can't access shadow root:**
- May be closed shadow DOM (uncommon)
- Try coordinate click as fallback
- Screenshot to verify element position

**Shadow DOM not loading:**
- Component may need interaction to initialize
- Check for JavaScript errors
- Wait for custom events: `wait_for_event()`

## Best Practices

1. **Use >> combinator** — explicit shadow piercing
2. **Wait for shadow content** — shadow DOM may load async
3. **Screenshot first** — verify shadow DOM is visible
4. **Test selectors** — shadow DOM selectors can be complex
5. **Fallback to coordinates** — if shadow piercing fails

## Framework-Specific Notes

**LitElement:**
- Uses open shadow DOM by default
- Custom elements with `@customElement('tag-name')`

**Polymer:**
- Open shadow DOM
- May use `<dom-module>` for templates

**Angular Elements:**
- Open shadow DOM
- View encapsulation via shadow DOM

**Vue Web Components:**
- Can use shadow DOM
- Check component configuration

**Shady DOM (polyfill):**
- Older browsers use polyfill
- Playwright handles transparently
