"""Async browser control via Camoufox persistent context."""
import asyncio
import os
import random
import time
from collections import deque
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Optional

from camoufox.async_api import AsyncCamoufox


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
INTERNAL = ("about:", "data:", "chrome://", "chrome-extension://")

# Persistent profile directory - data survives restarts
PROFILE_DIR = Path.home() / ".config" / "camoufox-harness" / "profiles" / NAME
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

EVENTS_BUF = 500

# Camoufox configuration from environment
_CH_HEADLESS = os.environ.get("CH_HEADLESS", "true").lower() == "true"
_CH_HUMANIZE = os.environ.get("CH_HUMANIZE", "true").lower() == "true"
_CH_GEOIP = os.environ.get("CH_GEOIP", "true").lower() == "true"
_CH_LOCALE = os.environ.get("CH_LOCALE", None)

# Global state - persistent context only (no browser object)
_pw: Optional = None  # Playwright instance
_context: Optional = None  # BrowserContext
_page: Optional = None  # Page
_events = deque(maxlen=EVENTS_BUF)


def _on_event(evt_type, data):
    """Generic event handler - reduces 4 handlers to 1."""
    _events.append({"type": evt_type, **data})


async def _ensure_connection():
    """Start persistent Camoufox context if not started."""
    global _pw, _context, _page

    if _context is None:
        from playwright.async_api import async_playwright
        from camoufox.async_api import AsyncNewBrowser
        from camoufox.utils import launch_options

        # Build config (avoid duplicate launch_options calls)
        kwargs = {
            "headless": _CH_HEADLESS,
            "humanize": _CH_HUMANIZE,
            "geoip": _CH_GEOIP,
        }
        if _CH_LOCALE:
            kwargs["locale"] = _CH_LOCALE

        opt = launch_options(**kwargs)
        opt["user_data_dir"] = str(PROFILE_DIR)

        # Launch with persistent context
        _pw = await async_playwright().start()
        _context = await AsyncNewBrowser(_pw, persistent_context=True, from_options=opt)

        # Get first page or create new one
        _page = _context.pages[0] if _context.pages else await _context.new_page()

        # Subscribe to events (using generic handler)
        _page.on("dialog", lambda d: _on_event("dialog", {"message": d.message, "dialog_type": d.type}))
        _page.on("load", lambda: _on_event("load", {"url": _page.url}))
        _page.on("console", lambda m: _on_event("console", {"level": m.type, "text": m.text}))
        _page.on("pageerror", lambda e: _on_event("error", {"message": str(e)}))

        await _mark_tab()


def _connected(func):
    """Decorator: ensures connection before calling async function."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        await _ensure_connection()
        return await func(*args, **kwargs)
    return wrapper


async def _cleanup():
    """Close persistent context."""
    global _pw, _context, _page
    if _context:
        await _context.close()
        _context = None
        _page = None
    if _pw:
        await _pw.stop()
        _pw = None


# --- navigation / page ---
@_connected
async def goto(url: str, wait_until: str = "domcontentloaded") -> dict:
    """Navigate to URL. Returns {url, title, domain_skills}."""
    await _page.goto(url, wait_until=wait_until)
    from urllib.parse import urlparse
    domain = urlparse(url).hostname or ""
    domain = domain.removeprefix("www.").split(".")[0]
    skill_dir = Path(__file__).parent / "domain-skills" / domain
    skills = sorted(p.name for p in skill_dir.rglob("*.md"))[:10] if skill_dir.exists() else []
    return {"url": _page.url, "title": await _page.title(), "domain_skills": skills}


@_connected
async def page_info() -> dict:
    """{url, title, w, h} — current page state."""
    vp = _page.viewport_size
    return {"url": _page.url, "title": await _page.title(), "w": vp["width"], "h": vp["height"]}


@_connected
async def wait_for_load(timeout: float = 15.0) -> bool:
    """Wait for page load complete."""
    try:
        await _page.wait_for_load_state("domcontentloaded", timeout=timeout * 1000)
        return True
    except:
        return False


# --- input ---
@_connected
async def click(selector: str, button: str = "left", clicks: int = 1) -> dict:
    """Click element by CSS selector."""
    await _page.locator(selector).click(button=button, click_count=clicks)
    return {"clicked": selector}


@_connected
async def type_text(selector: str, text: str, delay: float = 0.05) -> dict:
    """Type text into element."""
    el = _page.locator(selector)
    await el.fill("")
    await el.type(text, delay=delay * 1000)
    return {"typed": text}


@_connected
async def press_key(key: str, modifiers: list = None) -> dict:
    """Press keyboard key (Enter, Tab, Escape, etc.)."""
    if modifiers:
        key = "+".join(modifiers + [key])
    await _page.keyboard.press(key)
    return {"pressed": key}


@_connected
async def scroll(direction: str = "down", amount: int = 300) -> dict:
    """Scroll page (up/down/left/right)."""
    await _page.evaluate(f"window.scrollBy(0, {amount if direction == 'down' else -amount if direction == 'up' else 0 if direction in ('up', 'down') else {amount if direction == 'right' else -amount}})")
    return {"scrolled": direction}


@_connected
async def screenshot(path: str = "/tmp/shot.png", full: bool = False) -> str:
    """Take screenshot. Returns path to saved file."""
    data = await _page.screenshot(full_page=full)
    Path(path).write_bytes(data)
    return path


@_connected
async def snapshot() -> dict:
    """Get accessibility tree snapshot with element refs."""
    snap = await _page.accessibility.snapshot()

    def count(node):
        return 1 + sum(count(c) for c in node.get("children", [])) if isinstance(node, dict) else 0

    return {"snapshot": snap, "element_count": count(snap)}


@_connected
async def get_video_path() -> Optional[str]:
    """Get path to video file for current page. Returns None if recording disabled.
    
    Note: Only works when using record_screen() - not continuous recording.
    """
    return None  # Screenshots don't support path query during recording


async def record_screen(video_dir: str, func, fps: int = 10):
    """Record page actions as screenshot sequence + video.

    Captures screenshots after each action, combines to MP4.
    Works in headless mode (uses Playwright screenshots).

    Args:
        video_dir: Directory to save video
        func: Async function to execute while recording
        fps: Target FPS (affects screenshot timing)

    Returns:
        {video_path, result}

    Example:
        async def demo():
            await goto("https://example.com")
            await click("button")

        info = await record_screen("/tmp/videos", demo)
        print(f"Video: {info['video_path']}")
    """
    await _ensure_connection()
    Path(video_dir).mkdir(parents=True, exist_ok=True)
    
    # Track screenshots and timing
    screenshots = []
    start_time = time.time()
    result = None
    
    # Wrap page.screenshot to capture all actions
    original_screenshot = _page.screenshot
    screenshot_dir = Path(video_dir) / "frames"
    screenshot_dir.mkdir(exist_ok=True)
    
    async def capturing_screenshot(**kwargs):
        """Wrapper that saves screenshots for video compilation."""
        timestamp = time.time() - start_time
        data = await original_screenshot(**kwargs)
        
        # Save with timestamp in filename for ordering
        frame_path = screenshot_dir / f"frame_{len(screenshots):04d}.png"
        frame_path.write_bytes(data)
        screenshots.append({"path": str(frame_path), "time": timestamp})
        
        return data
    
    # Temporarily replace screenshot method
    _page.screenshot = capturing_screenshot
    
    # Auto-capture at intervals
    capture_task = None
    
    async def auto_capture():
        """Capture screenshots periodically."""
        while True:
            await asyncio.sleep(1.0 / fps)
            try:
                await _page.screenshot(full_page=False)
            except:
                break
    
    try:
        # Start auto-capture
        capture_task = asyncio.create_task(auto_capture())
        
        # Run user function
        result = await func()
        
    finally:
        # Stop auto-capture
        if capture_task:
            capture_task.cancel()
            try:
                await capture_task
            except asyncio.CancelledError:
                pass
        
        # Restore original screenshot
        _page.screenshot = original_screenshot
    
    # Compile screenshots to video
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    video_path = str(Path(video_dir) / f"recording-{timestamp}.mp4")
    
    if screenshots:
        try:
            from PIL import Image
            import imageio
            
            # Load screenshots in order
            frames = [Image.open(s["path"]) for s in screenshots]
            
            # Save as MP4
            imageio.mimsave(video_path, frames, fps=fps)
            
            # Cleanup frame files
            for s in screenshots:
                Path(s["path"]).unlink(missing_ok=True)
            screenshot_dir.rmdir()
            
        except ImportError:
            # Fallback: save first screenshot as PNG
            fallback_path = str(Path(video_dir) / f"recording-{timestamp}.png")
            Path(screenshots[0]["path"]).rename(fallback_path)
            video_path = fallback_path
    
    return {"video_path": video_path, "result": result, "frames": len(screenshots)}


@_connected
async def js(expression: str):
    """Execute JavaScript in page context."""
    return await _page.evaluate(expression)


@_connected
async def get_html() -> str:
    """Get page HTML."""
    return await _page.content()


@_connected
async def get_text() -> str:
    """Get page visible text."""
    return await _page.evaluate("document.body.innerText")


async def wait(seconds: float = 1.0):
    """Sleep for specified seconds."""
    await asyncio.sleep(seconds)


async def random_delay(min_sec: float = 0.5, max_sec: float = 2.0):
    """Random delay for anti-detect humanize."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def _mark_tab():
    """Prepend 🟢 to tab title so user can see which tab agent controls."""
    try:
        await _page.evaluate("if(!document.title.startsWith('🟢 '))document.title='🟢 '+document.title")
    except:
        pass


async def _unmark_tab():
    """Remove 🟢 prefix from tab title."""
    try:
        await _page.evaluate("if(document.title.startsWith('🟢 '))document.title=document.title.slice(2)")
    except:
        pass


# --- tabs ---
@_connected
async def list_tabs(include_chrome: bool = True) -> list:
    """List all tabs."""
    tabs = []
    for i, p in enumerate(_context.pages):
        url = p.url
        if not include_chrome and url.startswith(INTERNAL):
            continue
        tabs.append({"id": i, "url": url, "title": await p.title()})
    return tabs


@_connected
async def ensure_real_tab():
    """Switch to a real user tab if current is internal/stale. Returns tab info or None."""
    tabs = await list_tabs(include_chrome=False)
    if not tabs:
        return None
    try:
        cur = await current_tab()
        if cur["url"] and not cur["url"].startswith(INTERNAL):
            return cur
    except:
        pass
    await switch_tab(tabs[0]["id"])
    return tabs[0]


@_connected
async def current_tab() -> dict:
    """Get current tab info."""
    tab_id = _context.pages.index(_page)
    return {"id": tab_id, "url": _page.url, "title": await _page.title()}


@_connected
async def switch_tab(tab_id: int) -> dict:
    """Switch to tab by id."""
    if tab_id < 0 or tab_id >= len(_context.pages):
        raise RuntimeError(f"Tab id {tab_id} out of range")
    await _unmark_tab()
    global _page
    _page = _context.pages[tab_id]
    await _page.bring_to_front()
    await _mark_tab()
    return {"id": tab_id, "url": _page.url}


@_connected
async def new_tab(url: str = "about:blank") -> dict:
    """Open new tab."""
    global _page
    _page = await _context.new_page()
    await _page.goto(url)
    await _mark_tab()
    return {"id": len(_context.pages) - 1, "url": _page.url}


@_connected
async def close_tab() -> dict:
    """Close current tab."""
    global _page
    await _page.close()
    if _context.pages:
        _page = _context.pages[0]
        await _mark_tab()
    return {"closed": True}


@_connected
async def iframe_target(url_substr: str) -> Optional:
    """Find first iframe whose URL contains `url_substr`. Returns frame object or None."""
    if not url_substr:
        return None
    for frame in _page.frames:
        if url_substr in (getattr(frame, 'url', '') or ''):
            return frame
    return None


# --- cookie/storage ---
@_connected
async def get_cookies() -> list:
    """Get all cookies."""
    return await _context.cookies()


@_connected
async def set_cookies(cookies: list) -> dict:
    """Set cookies."""
    await _context.add_cookies(cookies)
    return {"set": True}


@_connected
async def get_local_storage() -> dict:
    """Get localStorage."""
    return await _page.evaluate("Object.assign({}, localStorage)")


@_connected
async def set_local_storage(items: dict) -> dict:
    """Set localStorage items."""
    for k, v in items.items():
        await _page.evaluate(f"localStorage.setItem({repr(k)}, {repr(v)})")
    return {"set": True}


# --- session ---
# Note: save_profile/load_profile removed - persistence is automatic with user_data_dir


@_connected
async def save_domain_skill(site: str, content: str) -> dict:
    """Save learned patterns to domain-skills/<site>/<timestamp>.md"""
    skill_dir = Path(__file__).parent / "domain-skills" / site
    skill_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    skill_file = skill_dir / f"{timestamp}.md"
    skill_file.write_text(content)
    return {"saved": site, "path": str(skill_file), "timestamp": timestamp}


# --- anti-detect helpers ---
@_connected
async def human_click(selector: str) -> dict:
    """Human-like click with random delays."""
    await random_delay(0.1, 0.3)
    result = await click(selector)
    await random_delay(0.5, 1.5)
    return result


@_connected
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
    return {"stealth": enable}


# --- events ---
async def drain_events() -> list:
    """Get accumulated events, clear buffer."""
    events = list(_events)
    _events.clear()
    return events


# --- profile info ---
def get_profile_dir() -> str:
    """Get current persistent profile directory path."""
    return str(PROFILE_DIR)
