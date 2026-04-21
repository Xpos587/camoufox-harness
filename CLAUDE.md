---
name: camoufox-harness
description: Playwright-based browser automation with Camoufox anti-detect Firefox
type: project
---

# Camoufox Harness — Project Context

## Что это

Browser automation harness использующий Playwright async API + Camoufox (Firefox с встроенным anti-detect).

## Ключевые особенности

- **Async/await** — все функции асинхронные (современный Python)
- **Event-driven** — dialog, load, console, error события через `drain_events()`
- **Anti-detect** — humanize (случайные задержки), geoip (спуфинг локации), fingerprint randomization
- **Domain skills** — автогенерация паттернов для сайтов (private APIs, stable selectors, traps)
- **PEP 723** — inline зависимости в pyproject.toml (no venv locking)

## Файловая структура

```
camoufox-harness/
├── helpers.py              # Все async функции (41 функция)
├── admin.py                # Daemon management (start/stop/status)
├── run.py                  # CLI entry point (PEP 723 inline deps)
├── pyproject.toml          # Project metadata + dependencies
├── interaction-skills/     # Reusable UI patterns (19 skills)
├── domain-skills/          # Автогенерированные паттерны (67 sites)
├── data/
│   ├── plans/              # Implementation plans
│   └── specs/              # Design specs
├── SKILL.md                # Agent usage guide
├── install.md              # Installation & setup
└── README.md               # Project overview
```

## Установка

```bash
git clone https://github.com/Xpos587/camoufox-harness
cd camoufox-harness
uv run admin.py start
```

## Использование

```python
# Basic navigation
await goto("https://example.com")
await wait_for_load()
print(await page_info())

# Anti-detect automation
await human_click("#button")
await human_type("#input", "text")

# Events
events = await drain_events()
dialogs = [e for e in events if e["type"] == "dialog"]
```

## Architecture

```
┌─────────────┐    WebSocket    ┌──────────────────┐    Playwright    ┌──────────┐
│   Agent     │ ◀─────────────▶ │ Camoufox Remote  │ ────────────────▶ │ Camoufox │
│ (run.py)    │   (connect)     │ Server           │                  │ (Firefox) │
└─────────────┘                 └──────────────────┘                  └──────────┘
```

Camoufox remote server предоставляет WebSocket endpoint. Агент подключается через Playwright's `firefox.connect()`. События flow через Playwright event handlers.

## Environment Variables (.env)

```bash
CH_NAME=default                    # Instance name (для multiple browsers)
CH_WS_URL=ws://127.0.0.1:9222/camoufox  # WebSocket URL
CH_PORT=9222                       # Daemon port
```

## Ключевые функции helpers.py

### Navigation
- `goto(url)` — navigate to URL
- `wait_for_load(timeout)` — wait for page load
- `page_info()` — get {url, title, w, h}

### Input
- `click(selector)` — click element
- `type_text(selector, text)` — type into element
- `press_key(key)` — press keyboard key
- `scroll(direction, amount)` — scroll page

### Anti-Detect
- `human_click(selector)` — human-like click with random delays
- `human_type(selector, text)` — human-like typing with typos
- `random_delay(min, max)` — random delay
- `stealth_mode(enable)` — toggle stealth

### Tabs
- `new_tab(url)` — create new tab (marked with 🟢)
- `switch_tab(tab_id)` — switch to tab (updates mark)
- `close_tab()` — close current tab
- `ensure_real_tab()` — auto-recovery from internal tabs

### Events
- `drain_events()` — get accumulated events (dialog, load, console, error)

### Storage
- `get_cookies()` / `set_cookies()` — cookie management
- `save_profile(name)` / `load_profile(name)` — session persistence

## Domain Skills

Domain skills — это автогенерированные `.md` файлы с паттернами для конкретных сайтов:

```python
# Check for existing skills
result = await goto("https://github.com")
print(result["domain_skills"])  # ['20260421-123456.md', ...]

# Save learned patterns
await save_domain_skill("github", """
# GitHub Login Patterns

## Stable Selectors
- Login button: `[href="/login"]`
- Email input: `#login_field`

## URL Patterns
- Direct login: https://github.com/login

## Traps
- Avoid `.js-*` classes (obfuscated)
- 2FA may appear after successful auth
""")
```

## Interaction Skills

`interaction-skills/` содержит reusable UI patterns:
- dialogs.md — alert/confirm/prompt handling
- dropdowns.md — native selects, comboboxes
- uploads.md — file upload via set_input_files()
- drag-and-drop.md — drag_and_drop() API
- И ещё 15 skills

## Dependencies

- `playwright>=1.40.0` — async browser automation
- `camoufox[geoip]>=0.4.0` — Firefox anti-detect browser

## Testing

```bash
# Verify installation
uv run run.py <<'PY'
import asyncio
async def test():
    await goto("https://example.com")
    await wait_for_load()
    print(await page_info())
asyncio.run(test())
PY
```

## Deployment

Camoufox runs locally. Для remote deployment используйте:
- SSH tunneling для WebSocket
- Или обратитесь к Camoufox remote server docs

## Known Issues

- **Camoufox binary download** — первый запуск скачивает Firefox binary (~300MB)
- **Port conflicts** — измените `CH_PORT` в `.env` если порт занят
- **WebSocket connection** — убедитесь что daemon запущен (`uv run admin.py status`)
