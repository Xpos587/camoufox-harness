# Browser-Harness Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tab marking, ensure_real_tab, iframe support, and domain skills from browser-harness to camoufox-harness

**Architecture:** Extend existing async helpers.py with browser-harness patterns, adapted for Playwright API

**Tech Stack:** Playwright async API, Camoufox remote server

---

### Task 1: Tab Marking (_mark_tab)

**Files:**

- Modify: `helpers.py` (add _mark_tab, _unmark_tab functions)

- [ ] **Step 1: Add _mark_tab and _unmark_tab functions**

Добавить в helpers.py после `# --- utility ---` секции:

```python
async def _mark_tab():
    """Prepend 🟢 to tab title so user can see which tab agent controls."""
    await _ensure_connection()
    try:
        await _page.evaluate("if(!document.title.startsWith('🟢 '))document.title='🟢 '+document.title")
    except Exception:
        pass


async def _unmark_tab():
    """Remove 🟢 prefix from tab title."""
    await _ensure_connection()
    try:
        await _page.evaluate("if(document.title.startsWith('🟢 '))document.title=document.title.slice(2)")
    except Exception:
        pass
```

- [ ] **Step 2: Integrate marking into new_tab()**

Модифицировать `new_tab()` функцию — добавить `await _mark_tab()` после создания:

```python
async def new_tab(url: str = "about:blank") -> dict:
    """Open new tab."""
    await _ensure_connection()
    new_page = await _context.new_page()
    await new_page.goto(url)
    # Update global _page to new tab
    global _page
    _page = new_page
    await _mark_tab()
    return {"id": len(_context.pages) - 1, "url": new_page.url}
```

- [ ] **Step 3: Add switch_tab() function**

Добавить `switch_tab()` функцию в `# --- tabs ---` секцию:

```python
async def switch_tab(tab_id: int) -> dict:
    """Switch to tab by id."""
    await _ensure_connection()
    ctx = _browser.contexts[0]
    if tab_id < 0 or tab_id >= len(ctx.pages):
        raise RuntimeError(f"Tab id {tab_id} out of range")
    # Unmark current tab
    await _unmark_tab()
    # Switch to new tab
    global _page
    _page = ctx.pages[tab_id]
    await _page.bring_to_front()
    await _mark_tab()
    return {"id": tab_id, "url": _page.url}
```

- [ ] **Step 4: Update current_tab() to include mark**

Модифицировать `current_tab()` чтобы возвращать title с маркером:

```python
async def current_tab() -> dict:
    """Get current tab info."""
    await _ensure_connection()
    ctx = _browser.contexts[0]
    tab_id = ctx.pages.index(_page)
    return {
        "id": tab_id,
        "url": _page.url,
        "title": await _page.title()
    }
```

- [ ] **Step 5: Commit**

```bash
git add helpers.py
git commit -m "feat: add tab marking with 🟢 prefix"
```

### Task 2: ensure_real_tab()

**Files:**

- Modify: `helpers.py` (add ensure_real_tab, update list_tabs)

- [ ] **Step 1: Update list_tabs() to support include_chrome parameter**

Модифицировать `list_tabs()`:

```python
async def list_tabs(include_chrome: bool = True) -> list:
    """List all tabs."""
    await _ensure_connection()
    ctx = _browser.contexts[0]
    tabs = []
    for i, p in enumerate(ctx.pages):
        url = p.url
        if not include_chrome and url.startswith(INTERNAL):
            continue
        tabs.append({"id": i, "url": url, "title": await p.title()})
    return tabs
```

- [ ] **Step 2: Add ensure_real_tab() function**

Добавить после `list_tabs()`:

```python
async def ensure_real_tab():
    """Switch to a real user tab if current is internal/stale. Returns tab info or None."""
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

- [ ] **Step 3: Commit**

```bash
git add helpers.py
git commit -m "feat: add ensure_real_tab for auto-recovery"
```

### Task 3: iframe_target()

**Files:**

- Modify: `helpers.py` (add iframe_target function)

- [ ] **Step 1: Add iframe_target() function**

Добавить в `# --- tabs ---` секцию после `close_tab()`:

```python
async def iframe_target(url_substr: str):
    """Find first iframe whose URL contains `url_substr`. Returns frame object or None."""
    await _ensure_connection()
    for frame in _page.frames:
        if url_substr in frame.url:
            return frame
    return None
```

- [ ] **Step 2: Add usage example in docstring**

Добавить пример использования:

```python
"""
Usage:
    frame = await iframe_target("checkout.com")
    if frame:
        await frame.click("#pay")
        await frame.type_text("#email", "test@example.com")
"""
```

- [ ] **Step 3: Commit**

```bash
git add helpers.py
git commit -m "feat: add iframe_target for cross-origin iframe support"
```

### Task 4: Domain Skills - Infrastructure

**Files:**

- Create: `domain-skills/.gitkeep`
- Modify: `helpers.py` (add save_domain_skill)

- [ ] **Step 1: Create domain-skills directory**

```bash
mkdir -p /home/michael/Github/camoufox-harness/domain-skills
touch /home/michael/Github/camoufox-harness/domain-skills/.gitkeep
```

- [ ] **Step 2: Add imports for domain skills**

Добавить в imports секцию helpers.py:

```python
from datetime import datetime
```

- [ ] **Step 3: Add save_domain_skill() function**

Добавить в `# --- session ---` секцию:

```python
async def save_domain_skill(site: str, content: str) -> dict:
    """Save learned patterns to domain-skills/<site>/<timestamp>.md

    Args:
        site: Domain name (e.g., 'github', 'linkedin')
        content: Markdown content with patterns discovered

    Returns:
        dict with path and timestamp
    """
    skill_dir = Path(__file__).parent / "domain-skills" / site
    skill_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    skill_file = skill_dir / f"{timestamp}.md"
    skill_file.write_text(content)
    return {"saved": site, "path": str(skill_file), "timestamp": timestamp}
```

- [ ] **Step 4: Commit**

```bash
git add domain-skills/ helpers.py
git commit -m "feat: add domain skills infrastructure"
```

### Task 5: Domain Skills - goto() Enhancement

**Files:**

- Modify: `helpers.py` (update goto to return domain_skills)

- [ ] **Step 1: Update goto() to return domain skills**

Модифицировать `goto()` функцию:

```python
async def goto(url: str, wait_until: str = "domcontentloaded") -> dict:
    """Navigate to URL. Returns {url, title, domain_skills}."""
    await _ensure_connection()
    await _page.goto(url, wait_until=wait_until)
    # Check for domain skills
    from urllib.parse import urlparse
    domain = urlparse(url).hostname or ""
    domain = domain.removeprefix("www.").split(".")[0]
    skill_dir = Path(__file__).parent / "domain-skills" / domain
    skills = []
    if skill_dir.exists():
        skills = sorted(p.name for p in skill_dir.rglob("*.md"))[:10]
    return {
        "url": _page.url,
        "title": await _page.title(),
        "domain_skills": skills
    }
```

- [ ] **Step 2: Commit**

```bash
git add helpers.py
git commit -m "feat: return domain skills in goto()"
```

### Task 6: Documentation

**Files:**

- Modify: `SKILL.md` (add domain skills section)

- [ ] **Step 1: Add Domain Skills section to SKILL.md**

Добавить в конец SKILL.md:

```markdown
## Domain Skills

Domain skills are auto-generated `.md` files containing learned patterns for specific websites. When you navigate to a site, `goto()` returns available skills.

```python
# Navigate and check for existing skills
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
- Session persists across subdomains

## Traps
- Avoid `.js-*` classes (obfuscated)
- 2FA may appear after successful auth
""")
```

**What to save in domain skills:**
- Private API endpoints
- Stable selectors (`data-*`, `aria-*`, `role`)
- URL patterns and query params
- Framework quirks
- Traps and selectors that DON'T work
```

- [ ] **Step 2: Update Best Practices section**

Добавить в Best Practices:

```markdown
6. **Contribute domain skills** — When you learn non-obvious patterns about a site, save them with `save_domain_skill()`
```

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "docs: add domain skills documentation"
```

### Task 7: Update README

**Files:**

- Modify: `README.md` (add domain skills mention)

- [ ] **Step 1: Add domain skills to Features**

Добавить в Features список:

```markdown
- **Domain Skills**: Auto-generated patterns for websites (private APIs, stable selectors, traps)
```

- [ ] **Step 2: Add domain skills to Documentation section**

Обновить Documentation секцию:

```markdown
- `install.md` — Installation & setup
- `SKILL.md` — Agent usage guide (including domain skills)
- `helpers.py` — Core API reference
- `domain-skills/` — Auto-generated site patterns
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: mention domain skills in README"
```

---

## Testing Verification

После выполнения всех задач:

1. **Tab marking**: Создать tab, проверить что title содержит 🟢
2. **ensure_real_tab**: Перейти на `about:blank`, вызвать `ensure_real_tab()`, проверить переключение
3. **iframe_target**: Создать page с iframe, найти по URL
4. **Domain skills**: `goto()` на URL, проверить что возвращает список skills

```bash
cd /home/michael/Github/camoufox-harness
uv run run.py <<'PY'
import asyncio
async def test():
    # Test tab marking
    await goto("https://example.com")
    info = await page_info()
    print("Title:", info["title"])
    assert "🟢" in info["title"]

    # Test ensure_real_tab
    await goto("about:blank")
    real = await ensure_real_tab()
    print("Real tab:", real)

    # Test domain skills
    result = await goto("https://example.com")
    print("Domain skills:", result.get("domain_skills", []))

asyncio.run(test())
PY
```
