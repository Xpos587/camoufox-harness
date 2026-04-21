# Camoufox Interaction Skills

Reusable UI patterns for browser automation with Playwright + Camoufox.

## Available Skills

### Core Patterns
- **connection.md** — Startup sequence, tab visibility, auto-recovery
- **cookies.md** — Cookie management and session persistence
- **viewport.md** — Viewport control and responsive testing

### Interaction Patterns
- **dialogs.md** — Handling alert/confirm/prompt/beforeunload
- **dropdowns.md** — Native selects, comboboxes, virtualized menus
- **uploads.md** — File upload handling
- **drag-and-drop.md** — Drag and drop operations

### Advanced Patterns
- **cross-origin-iframes.md** — Working with iframes across origins
- **shadow-dom.md** — Piercing shadow DOM
- **network-requests.md** — Request interception and monitoring
- **downloads.md** — Browser-triggered downloads
- **print-as-pdf.md** — PDF generation

## Usage

Skills are automatically available when using camoufox-harness. Reference them when encountering specific UI challenges:

```python
# Reference the relevant skill
# Example: encountering a dialog
# See: interaction-skills/dialogs.md

events = await drain_events()
dialogs = [e for e in events if e["type"] == "dialog"]
```

## Framework Coverage

Skills cover patterns for:
- React (React Select, Material UI, Ant Design)
- Vue (Vue.Draggable, Vue components)
- jQuery UI (Sortables, dialogs)
- Web Components (LitElement, Polymer)
- Custom implementations

## Best Practices

1. **Screenshot first** — Verify UI state before interaction
2. **Check for events** — Use `drain_events()` after actions
3. **Handle edge cases** — Empty states, loading states, errors
4. **Test selectors** — Use stable selectors (data-*, aria-*, role)
5. **Add random delays** — Use `human_click()` for anti-detect

## Contributing

When you discover a new UI pattern that isn't covered:
1. Test the pattern thoroughly
2. Document the approach
3. Add to appropriate skill file or create new one
4. Commit with clear message
