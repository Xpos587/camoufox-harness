# /// script
# dependencies = [
#   "playwright>=1.40.0",
#   "camoufox[geoip]>=0.4.0",
# ]
# ///

"""Async browser control via Camoufox remote server."""
import asyncio
import json
import os
import random
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, BrowserContext


def _load_env():
    p = Path(__file__).parent / ".env"
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

NAME = os.environ.get("CH_NAME", "default")
WS_URL = os.environ.get("CH_WS_URL", "ws://127.0.0.1:9222/camoufox")
INTERNAL = ("about:", "data:", "chrome://", "chrome-extension://")

PROFILE_DIR = Path.home() / ".config" / "camoufox-harness" / "profiles" / NAME
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

EVENTS_BUF = 500

# Global state
_playwright = None
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_page: Optional[Page] = None
_events = deque(maxlen=EVENTS_BUF)


def _on_dialog(dialog):
    _events.append({"type": "dialog", "message": dialog.message, "dialog_type": dialog.type})


def _on_load():
    _events.append({"type": "load", "url": _page.url})


def _on_console(msg):
    _events.append({"type": "console", "level": msg.type, "text": msg.text})


def _on_error(error):
    _events.append({"type": "error", "message": str(error)})


async def _ensure_connection():
    """Connect to Camoufox remote server if not connected."""
    global _playwright, _browser, _context, _page

    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.firefox.connect(WS_URL)
        _context = _browser.contexts[0]

        if _context.pages:
            _page = _context.pages[0]
        else:
            _page = await _context.new_page()

        # Subscribe to events
        _page.on("dialog", _on_dialog)
        _page.on("load", _on_load)
        _page.on("console", _on_console)
        _page.on("pageerror", _on_error)
        
        await _mark_tab()


# --- navigation / page ---
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


async def page_info() -> dict:
    """{url, title, w, h} — current page state."""
    await _ensure_connection()
    vp = await _page.viewport_size()
    return {
        "url": _page.url,
        "title": await _page.title(),
        "w": vp["width"],
        "h": vp["height"],
    }


async def wait_for_load(timeout: float = 15.0) -> bool:
    """Wait for page load complete."""
    await _ensure_connection()
    try:
        await _page.wait_for_load_state("domcontentloaded", timeout=timeout * 1000)
        return True
    except:
        return False


# --- input ---
async def click(selector: str, button: str = "left", clicks: int = 1) -> dict:
    """Click element by CSS selector."""
    await _ensure_connection()
    await _page.locator(selector).click(button=button, click_count=clicks)
    return {"clicked": selector}


async def type_text(selector: str, text: str, delay: float = 0.05) -> dict:
    """Type text into element."""
    await _ensure_connection()
    el = _page.locator(selector)
    await el.fill("")
    await el.type(text, delay=delay * 1000)
    return {"typed": text}


async def press_key(key: str, modifiers: list = None) -> dict:
    """Press keyboard key (Enter, Tab, Escape, etc.)."""
    await _ensure_connection()
    mods = []
    if modifiers:
        mod_map = {"Alt": "Alt", "Control": "Control", "Meta": "Meta", "Shift": "Shift"}
        mods = [mod_map.get(m, m) for m in modifiers]
    await _page.keyboard.press(key, modifiers=mods)
    return {"pressed": key}


async def scroll(direction: str = "down", amount: int = 300) -> dict:
    """Scroll page (up/down/left/right)."""
    await _ensure_connection()
    if direction == "down":
        await _page.evaluate(f"window.scrollBy(0, {amount})")
    elif direction == "up":
        await _page.evaluate(f"window.scrollBy(0, -{amount})")
    elif direction == "left":
        await _page.evaluate(f"window.scrollBy(-{amount}, 0)")
    elif direction == "right":
        await _page.evaluate(f"window.scrollBy({amount}, 0)")
    return {"scrolled": direction}


# --- visual ---
async def screenshot(path: str = "/tmp/shot.png", full: bool = False) -> str:
    """Take screenshot. Returns path to saved file."""
    await _ensure_connection()
    data = await _page.screenshot(full_page=full)
    with open(path, "wb") as f:
        f.write(data)
    return path


async def snapshot() -> dict:
    """Get accessibility tree snapshot with element refs."""
    await _ensure_connection()
    snap = await _page.accessibility.snapshot()
    return {"snapshot": snap, "element_count": _count_elements(snap)}


def _count_elements(node, count=0):
    """Recursively count elements in accessibility tree."""
    if not isinstance(node, dict):
        return count
    count += 1
    for child in node.get("children", []):
        count = _count_elements(child, count)
    return count


# --- utility ---
async def js(expression: str):
    """Execute JavaScript in page context."""
    await _ensure_connection()
    return await _page.evaluate(expression)


async def get_html() -> str:
    """Get page HTML."""
    await _ensure_connection()
    return await _page.content()


async def get_text() -> str:
    """Get page visible text."""
    await _ensure_connection()
    return await _page.evaluate("document.body.innerText")


async def wait(seconds: float = 1.0):
    """Sleep for specified seconds."""
    await asyncio.sleep(seconds)


async def random_delay(min_sec: float = 0.5, max_sec: float = 2.0):
    """Random delay for anti-detect humanize."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


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


# --- tabs ---
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


async def close_tab() -> dict:
    """Close current tab."""
    await _ensure_connection()
    await _page.close()
    # Switch to first available page
    if _context.pages:
        global _page
        _page = _context.pages[0]
        await _mark_tab()
    return {"closed": True}


async def iframe_target(url_substr: str) -> Optional:
    """Find first iframe whose URL contains `url_substr`. Returns frame object or None.

    Usage:
        frame = await iframe_target("checkout.com")
        if frame:
            await frame.locator("#pay").click()
            await frame.locator("#email").fill("test@example.com")
    """
    if not url_substr:
        return None

    await _ensure_connection()
    for frame in _page.frames:
        frame_url = getattr(frame, 'url', '') or ''
        if frame_url and url_substr in frame_url:
            return frame
    return None


# --- cookie/storage ---
async def get_cookies() -> list:
    """Get all cookies."""
    await _ensure_connection()
    return await _context.cookies()


async def set_cookies(cookies: list) -> dict:
    """Set cookies."""
    await _ensure_connection()
    await _context.add_cookies(cookies)
    return {"set": True}


async def get_local_storage() -> dict:
    """Get localStorage."""
    await _ensure_connection()
    return await _page.evaluate("Object.assign({}, localStorage)")


async def set_local_storage(items: dict) -> dict:
    """Set localStorage items."""
    await _ensure_connection()
    for k, v in items.items():
        await _page.evaluate(f"localStorage.setItem({repr(k)}, {repr(v)})")
    return {"set": True}


# --- session ---
async def save_profile(name: str) -> dict:
    """Save current browser state to profile."""
    await _ensure_connection()
    profile_path = PROFILE_DIR / name
    profile_path.mkdir(parents=True, exist_ok=True)

    cookies = await _context.cookies()
    (profile_path / "cookies.json").write_text(json.dumps(cookies))

    ls = await _page.evaluate("Object.assign({}, localStorage)")
    (profile_path / "localStorage.json").write_text(json.dumps(ls))

    return {"saved": name, "path": str(profile_path)}


async def load_profile(name: str) -> dict:
    """Load browser state from profile."""
    await _ensure_connection()
    profile_path = PROFILE_DIR / name
    if not profile_path.exists():
        raise RuntimeError(f"Profile not found: {name}")

    cookies_file = profile_path / "cookies.json"
    if cookies_file.exists():
        cookies = json.loads(cookies_file.read_text())
        await _context.add_cookies(cookies)

    ls_file = profile_path / "localStorage.json"
    if ls_file.exists():
        ls = json.loads(ls_file.read_text())
        for k, v in ls.items():
            await _page.evaluate(f"localStorage.setItem({repr(k)}, {repr(v)})")

    return {"loaded": name}


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


# --- anti-detect helpers ---
async def human_click(selector: str) -> dict:
    """Human-like click with random delays."""
    await random_delay(0.1, 0.3)
    result = await click(selector)
    await random_delay(0.5, 1.5)
    return result


async def human_type(selector: str, text: str, typo_rate: float = 0.02) -> dict:
    """Human-like typing with random delays and typos."""
    for char in text:
        if random.random() < typo_rate and char.isalnum():
            wrong = random.choice("abcdefghijklmnopqrstuvwxyz")
            await type_text(selector, wrong)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await press_key("Backspace")
            await asyncio.sleep(random.uniform(0.1, 0.2))
        await type_text(selector, char)
        await asyncio.sleep(random.uniform(0.05, 0.15))
    await random_delay(0.3, 0.8)
    return {"typed": text}


async def stealth_mode(enable: bool = True) -> dict:
    """Toggle stealth mode."""
    # Camoufox handles stealth via launch parameters
    return {"stealth": enable}


# --- events ---
async def drain_events() -> list:
    """Get accumulated events, clear buffer."""
    events = list(_events)
    _events.clear()
    return events
