# Browser-Harness Features for Camoufox-Harness — Design

> **Goal:** Add tab marking, ensure_real_tab, iframe support, and domain skills from browser-harness

**Architecture:** Extend existing async helpers.py with browser-harness patterns, adapted for Playwright API

**Tech Stack:** Playwright async API, Camoufox remote server

---

## Tab Marking

**Функция:** `_mark_tab()` — prepend 🟢 к title

```python
async def _mark_tab():
    """Prepend 🟢 to tab title so user can see which tab agent controls."""
    await _ensure_connection()
    try:
        await _page.evaluate("if(!document.title.startsWith('🟢 '))document.title='🟢 '+document.title")
    except Exception:
        pass
```

**Интеграция:**
- Вызывать в `new_tab()` после создания
- Вызывать в `switch_tab()` после переключения
- В `current_tab()` возвращать title с маркером

**Unmark:** при `switch_tab()` — сначала снять 🟢 со старой вкладки

## ensure_real_tab()

**Функция:** Auto-recovery от stale/internal tabs

```python
async def ensure_real_tab():
    """Switch to a real user tab if current is internal/stale."""
    await _ensure_connection()
    tabs = await list_tabs(include_chrome=False)
    if not tabs:
        return None
    try:
        cur = await current_tab()
        if cur["url"] and not cur["url"].startswith(INTERNAL):
            return cur
    except Exception:
        pass
    # Switch to first real tab
    await switch_tab(tabs[0]["id"])
    return tabs[0]
```

**Изменения:**
- `list_tabs()` добавить `include_chrome` параметр
- Фильтровать `INTERNAL` URLs
- `current_tab()` обрабатывать stale session

## iframe_target()

**Функция:** Поиск iframe по URL substring

```python
async def iframe_target(url_substr: str):
    """First iframe whose URL contains `url_substr`. Returns frame object."""
    await _ensure_connection()
    for frame in _page.frames:
        if url_substr in frame.url:
            return frame
    return None
```

**Использование:**
```python
frame = await iframe_target("checkout.com")
await frame.click("#pay")
await frame.type_text("#email", "test@example.com")
```

## Domain Skills

**Структура:** `domain-skills/<site>/` с `.md` файлами

**Автогенерация агентом:**
```python
async def save_domain_skill(site: str, content: str):
    """Save learned patterns to domain-skills/<site>/<timestamp>.md"""
    skill_dir = Path(__file__).parent / "domain-skills" / site
    skill_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (skill_dir / f"{timestamp}.md").write_text(content)
```

**Что сохранять:**
- Private API endpoints
- Stable selectors (data-*, aria-*, role)
- URL patterns
- Framework quirks
- Traps и selectors что НЕ работают

**goto() enhancement:**
```python
async def goto(url: str) -> dict:
    """Navigate and return available domain skills."""
    # ... existing code ...
    domain = urlparse(url).hostname.removeprefix("www.").split(".")[0]
    skill_dir = Path(__file__).parent / "domain-skills" / domain
    skills = sorted(p.name for p in skill_dir.rglob("*.md")) if skill_dir.exists() else []
    return {"url": _page.url, "title": await _page.title(), "domain_skills": skills[:10]}
```

## Files to Modify

- **helpers.py** — добавить все 4 фичи
- **SKILL.md** — документация для domain skills
- **domain-skills/.gitkeep** — создать директорию

## Testing

- Тест tab marking: создать tab, проверить 🟢 в title
- Тест ensure_real_tab: перейти на internal tab, вызвать ensure_real_tab, проверить переключение
- Тест iframe_target: создать page с iframe, найти по URL
- Тест domain skills: goto на URL, проверить возвращаемый список skills

## Error Handling

- `_mark_tab()` — silent fail (try/except)
- `ensure_real_tab()` — return None если нет real tabs
- `iframe_target()` — return None если не найден
- `save_domain_skill()` — raise если ошибка записи
