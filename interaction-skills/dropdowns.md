# Dropdowns

Split dropdowns into native selects, custom overlays, searchable comboboxes, and virtualized menus. Always re-measure after opening because option geometry often appears late.

## Native `<select>` elements

Playwright handles these natively:

```python
# Select by visible text
await _page.locator("select#country").select_option("Canada")

# Select by value
await _page.locator("select#country").select_option(value="ca")

# Select by index
await _page.locator("select#country").select_option(index=1)

# Get all options
options = await _page.locator("select#country option").all_text_contents()
```

## Custom dropdown overlays (click-based)

Most modern dropdowns are `<div>` overlays that appear on click:

```python
# Click to open
await click("#dropdown-trigger")

# Wait for options to appear
await wait_for_load()

# Click option (may need scroll into view)
await click("[data-value='option1']")
```

**Troubleshooting:**
- If options aren't clickable: options may be in a portal or require hover first
- If click doesn't work: try coordinate click after screenshot
- If options disappear: use `human_click()` with random delays

## Searchable comboboxes (React Select, Ant Design, etc.)

Input + dropdown pattern:

```python
# Click combobox
await click("[role='combobox']")

# Type to search
await type_text("input[type='text']", "search query")

# Wait for results
await wait_for_load()

# Click first result
await click(".virtualized-option:first-child")
```

**React Select specific:**
```python
# React Select uses specific selectors
await click("#react-select-container")
await type_text("input", "query")
await click(".react-select__option:first-child")
```

## Virtualized menus (react-window, react-virtualized)

Only renders visible options. Scroll to reveal more:

```python
# Click to open
await click("#virtual-dropdown")

# Scroll through options
for i in range(5):
    await scroll("down", 100)
    await random_delay(0.1, 0.3)

# Click visible option
await click("[data-index='42']")
```

## Hover-based dropdowns (menus)

Some dropdowns appear on hover, not click:

```python
# Hover over trigger
await _page.locator("#menu-trigger").hover()

# Wait for menu
await wait_for_load()

# Click menu item
await click(".menu-item")
```

## Multi-select dropdowns

```python
# Select multiple options
await click("#multi-select")
await click("[data-value='opt1']")
await click("[data-value='opt2']")

# Or use Playwright's select_option with list
await _page.locator("select#multi").select_option(["opt1", "opt2"])
```

## Best Practices

1. **Screenshot after opening** — verify dropdown is visible before clicking options
2. **Wait for options** — `wait_for_load()` or explicit wait for option selector
3. **Use specific selectors** — `data-value`, `data-index`, `role` are stable
4. **Handle virtualization** — scroll if options aren't visible
5. **Avoid coordinate clicks** — use selectors unless dropdown is iframe/shadow DOM
6. **Test with different states** — disabled options, loading states, empty states

## Framework-Specific Quirks

**Material UI:**
- Uses `role="button"` and `data-value`
- Options may have `aria-disabled="true"` for disabled items

**Ant Design:**
- Uses `.ant-select-dropdown` class
- Searchable comboboxes have input inside the trigger

**Bootstrap:**
- Uses `.dropdown-menu` with `.dropdown-item`
- May require `.show` class on parent for visibility

**jQuery UI:**
- Uses `.ui-menu-item` with `ui-menu-item-wrapper`
- May need `.ui-menu-item` hover before click
