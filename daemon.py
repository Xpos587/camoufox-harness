# /// script
# dependencies = [
#   "camoufox[geoip]>=0.4.0",
#   "fastapi>=0.104.0",
#   "uvicorn>=0.24.0",
# ]
# ///

"""Camoufox daemon with FastAPI REST. Manages browser sessions and automation.

Run with: uv run daemon.py
Or make executable: chmod +x daemon.py && ./daemon.py
"""
import asyncio
import base64
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from camoufox import Camoufox
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


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

# Config
NAME = os.environ.get("CH_NAME", "default")
HOST = os.environ.get("CH_HOST", "127.0.0.1")
PORT = int(os.environ.get("CH_PORT", "8765"))
PROFILE_DIR = Path.home() / ".config" / "camoufox-harness" / "profiles" / NAME
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = Path(f"/tmp/camoufox-harness-{NAME}.log")
PID_FILE = Path(f"/tmp/camoufox-harness-{NAME}.pid")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global browser state
browser_ctx = None
page = None
camoufox_instance = None


# Pydantic models for requests
class GotoRequest(BaseModel):
    url: str
    wait_until: str = "domcontentloaded"


class ClickRequest(BaseModel):
    selector: str
    button: str = "left"
    clicks: int = 1


class TypeRequest(BaseModel):
    selector: str
    text: str
    delay: float = 0.05


class PressRequest(BaseModel):
    key: str
    modifiers: list = []


class ScrollRequest(BaseModel):
    direction: str = "down"
    amount: int = 300


class JsRequest(BaseModel):
    expression: str


class ProxyRequest(BaseModel):
    server: str
    username: Optional[str] = None
    password: Optional[str] = None


class GeolocationRequest(BaseModel):
    latitude: float
    longitude: float


class ProfileRequest(BaseModel):
    name: str


class StealthRequest(BaseModel):
    enabled: bool = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage browser lifecycle."""
    global browser_ctx, page, camoufox_instance
    
    logger.info(f"Starting Camoufox daemon (name={NAME})")
    
    # Launch Camoufox with anti-detect features
    try:
        camoufox_instance = Camoufox(
            headless=True,
            humanize=True,  # Anti-detect human behavior
            geoip=True,     # GeoIP spoofing
            nagle=True,     # Network optimization
        )
        browser_ctx = camoufox_instance.__enter__()
        page = browser_ctx.new_page()
        logger.info("Camoufox browser started successfully")
    except Exception as e:
        logger.error(f"Failed to start Camoufox: {e}")
        raise
    
    # Write PID
    PID_FILE.write_text(str(os.getpid()))
    
    yield
    
    # Cleanup
    logger.info("Shutting down Camoufox daemon")
    try:
        if page:
            await page.close()
        if browser_ctx:
            await browser_ctx.close()
        if camoufox_instance:
            await camoufox_instance.__aexit__(None, None, None)
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        try:
            PID_FILE.unlink()
        except FileNotFoundError:
            pass


app = FastAPI(lifespan=lifespan)


# --- endpoints ---
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "name": NAME}


@app.post("/goto")
async def goto_page(req: GotoRequest):
    """Navigate to URL."""
    try:
        await page.goto(req.url, wait_until=req.wait_until)
        return {
            "url": page.url,
            "title": await page.title(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/page_info")
async def get_page_info():
    """Get current page info."""
    try:
        vp_size = await page.viewport_size()
        return {
            "url": page.url,
            "title": await page.title(),
            "w": vp_size["width"],
            "h": vp_size["height"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wait_for_load")
async def wait_for_load(timeout: float = 15.0):
    """Wait for page load."""
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout * 1000)
        return {"ready": True}
    except Exception:
        return {"ready": False}


@app.post("/click")
async def click_element(req: ClickRequest):
    """Click element by selector."""
    try:
        el = page.locator(req.selector)
        await el.click(button=req.button, click_count=req.clicks)
        return {"clicked": req.selector}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/type")
async def type_text(req: TypeRequest):
    """Type text into element."""
    try:
        el = page.locator(req.selector)
        await el.fill("")
        await el.type(req.text, delay=req.delay * 1000)
        return {"typed": req.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/press")
async def press_key(req: PressRequest):
    """Press keyboard key."""
    try:
        mods = []
        if req.modifiers:
            mod_map = {"Alt": "Alt", "Control": "Control", "Meta": "Meta", "Shift": "Shift"}
            mods = [mod_map.get(m, m) for m in req.modifiers]
        await page.keyboard.press(req.key, modifiers=mods)
        return {"pressed": req.key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scroll")
async def scroll_page(req: ScrollRequest):
    """Scroll page."""
    try:
        if req.direction == "down":
            await page.evaluate(f"window.scrollBy(0, {req.amount})")
        elif req.direction == "up":
            await page.evaluate(f"window.scrollBy(0, -{req.amount})")
        elif req.direction == "left":
            await page.evaluate(f"window.scrollBy(-{req.amount}, 0)")
        elif req.direction == "right":
            await page.evaluate(f"window.scrollBy({req.amount}, 0)")
        return {"scrolled": req.direction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/screenshot")
async def get_screenshot(full: bool = False):
    """Take screenshot."""
    try:
        data = await page.screenshot(full_page=full)
        return {"data": base64.b64encode(data).decode()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/snapshot")
async def get_snapshot():
    """Get accessibility tree snapshot."""
    try:
        snapshot = await page.accessibility.snapshot()
        return {"snapshot": snapshot, "element_count": _count_elements(snapshot)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _count_elements(node, count=0):
    """Recursively count elements in accessibility tree."""
    if not isinstance(node, dict):
        return count
    count += 1
    for child in node.get("children", []):
        count = _count_elements(child, count)
    return count


@app.post("/js")
async def run_js(req: JsRequest):
    """Execute JavaScript."""
    try:
        result = await page.evaluate(req.expression)
        return {"value": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/html")
async def get_html():
    """Get page HTML."""
    try:
        return {"html": await page.content()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/text")
async def get_text():
    """Get page visible text."""
    try:
        return {"text": await page.evaluate("document.body.innerText")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tabs")
async def list_tabs():
    """List all tabs (single-tab for now)."""
    return {
        "tabs": [
            {"id": 0, "url": page.url, "title": await page.title()}
        ]
    }


@app.get("/current_tab")
async def get_current_tab():
    """Get current tab info."""
    return {
        "id": 0,
        "url": page.url,
        "title": await page.title()
    }


@app.post("/tabs")
async def create_tab(req: dict):
    """Create new tab (opens new page in context)."""
    try:
        new_page = browser_ctx.new_page()
        await new_page.goto(req.get("url", "about:blank"))
        return {"id": 1, "url": new_page.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/switch_tab")
async def switch_tab(req: dict):
    """Switch tab (placeholder)."""
    return {"switched": req.get("tab_id")}


@app.delete("/tab")
async def close_tab():
    """Close current tab (placeholder)."""
    return {"closed": True}


@app.get("/cookies")
async def get_cookies():
    """Get all cookies."""
    try:
        return {"cookies": await browser_ctx.cookies()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cookies")
async def set_cookies_endpoint(req: dict):
    """Set cookies."""
    try:
        await browser_ctx.add_cookies(req.get("cookies", []))
        return {"set": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/storage")
async def get_storage():
    """Get localStorage."""
    try:
        ls = await page.evaluate("Object.assign({}, localStorage)")
        return {"localStorage": ls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/storage")
async def set_storage_endpoint(req: dict):
    """Set localStorage items."""
    try:
        for k, v in req.get("localStorage", {}).items():
            await page.evaluate(f"localStorage.setItem({repr(k)}, {repr(v)})")
        return {"set": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/proxy")
async def set_proxy_endpoint(req: ProxyRequest):
    """Set proxy (requires browser restart)."""
    return {"note": "Proxy changes require browser restart"}


@app.post("/geolocation")
async def set_geolocation_endpoint(req: GeolocationRequest):
    """Set geolocation."""
    try:
        await page.set_geolocation({"latitude": req.latitude, "longitude": req.longitude})
        return {"set": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/profile/save")
async def save_profile_endpoint(req: ProfileRequest):
    """Save current browser state to profile."""
    profile_path = PROFILE_DIR / req.name
    profile_path.mkdir(parents=True, exist_ok=True)
    
    # Save cookies
    cookies = await browser_ctx.cookies()
    (profile_path / "cookies.json").write_text(json.dumps(cookies))
    
    # Save localStorage
    ls = await page.evaluate("Object.assign({}, localStorage)")
    (profile_path / "localStorage.json").write_text(json.dumps(ls))
    
    return {"saved": req.name, "path": str(profile_path)}


@app.post("/profile/load")
async def load_profile_endpoint(req: ProfileRequest):
    """Load browser state from profile."""
    profile_path = PROFILE_DIR / req.name
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Load cookies
    cookies_file = profile_path / "cookies.json"
    if cookies_file.exists():
        cookies = json.loads(cookies_file.read_text())
        await browser_ctx.add_cookies(cookies)
    
    # Load localStorage
    ls_file = profile_path / "localStorage.json"
    if ls_file.exists():
        ls = json.loads(ls_file.read_text())
        for k, v in ls.items():
            await page.evaluate(f"localStorage.setItem({repr(k)}, {repr(v)})")
    
    return {"loaded": req.name}


@app.post("/stealth")
async def stealth_mode_endpoint(req: StealthRequest):
    """Toggle stealth mode."""
    return {"stealth": req.enabled}


def main():
    """Run daemon."""
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
