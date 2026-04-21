"""Browser control via Camoufox (Playwright API). Read, edit, extend — this file is yours."""
import json
import os
import random
import time
from pathlib import Path
from typing import Optional

import requests


def _load_env():
    p = Path(__file__).parent / ".env"
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("''))


_load_env()

NAME = os.environ.get("CH_NAME", "default")
API_URL = os.environ.get("CH_API_URL", "http://127.0.0.1:8765")
INTERNAL = ("about:", "data:", "chrome://", "chrome-extension://")

# Persistent profile directory
PROFILE_DIR = Path.home() / ".config" / "camoufox-harness" / "profiles" / NAME
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def _api_call(method: str, path: str, data: dict = None) -> dict:
    """Make API call to daemon."""
    url = f"{API_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url, params=data, timeout=30)
        elif method == "POST":
            r = requests.post(url, json=data, timeout=30)
        elif method == "DELETE":
            r = requests.delete(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unknown method: {method}")
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise RuntimeError(f"API call failed: {e}")


# --- navigation / page ---
def goto(url: str, wait_until: str = "domcontentloaded") -> dict:
    """Navigate to URL. Returns {url, title}."""
    return _api_call("POST", "/goto", {"url": url, "wait_until": wait_until})


def page_info() -> dict:
    """{url, title, w, h, viewport} — current page state."""
    return _api_call("GET", "/page_info")


def wait_for_load(timeout: float = 15.0) -> bool:
    """Wait for page load complete."""
    return _api_call("GET", "/wait_for_load", {"timeout": timeout}).get("ready", False)


# --- input ---
def click(selector: str, button: str = "left", clicks: int = 1) -> dict:
    """Click element by CSS selector."""
    return _api_call("POST", "/click", {"selector": selector, "button": button, "clicks": clicks})


def type_text(selector: str, text: str, delay: float = 0.05) -> dict:
    """Type text into element."""
    return _api_call("POST", "/type", {"selector": selector, "text": text, "delay": delay})


def press_key(key: str, modifiers: list = None) -> dict:
    """Press keyboard key (Enter, Tab, Escape, etc.)."""
    return _api_call("POST", "/press", {"key": key, "modifiers": modifiers or []})


def scroll(direction: str = "down", amount: int = 300) -> dict:
    """Scroll page (up/down/left/right)."""
    return _api_call("POST", "/scroll", {"direction": direction, "amount": amount})


# --- visual ---
def screenshot(path: str = "/tmp/shot.png", full: bool = False) -> str:
    """Take screenshot. Returns path to saved file."""
    r = _api_call("GET", "/screenshot", {"full": full})
    import base64
    with open(path, "wb") as f:
        f.write(base64.b64decode(r["data"]))
    return path


def snapshot() -> dict:
    """Get accessibility tree snapshot with element refs."""
    return _api_call("GET", "/snapshot")


# --- utility ---
def wait(seconds: float = 1.0):
    """Sleep for specified seconds."""
    time.sleep(seconds)


def random_delay(min_sec: float = 0.5, max_sec: float = 2.0):
    """Random delay for anti-detect humanize."""
    time.sleep(random.uniform(min_sec, max_sec))


def js(expression: str) -> any:
    """Execute JavaScript in page context."""
    return _api_call("POST", "/js", {"expression": expression}).get("value")


def get_html() -> str:
    """Get page HTML."""
    return _api_call("GET", "/html").get("html", "")


def get_text() -> str:
    """Get page visible text."""
    return _api_call("GET", "/text").get("text", "")


# --- tabs ---
def list_tabs() -> list:
    """List all tabs."""
    return _api_call("GET", "/tabs").get("tabs", [])


def current_tab() -> dict:
    """Get current tab info."""
    return _api_call("GET", "/current_tab")


def new_tab(url: str = "about:blank") -> dict:
    """Open new tab."""
    return _api_call("POST", "/tabs", {"url": url})


def switch_tab(tab_id: int) -> dict:
    """Switch to tab by index."""
    return _api_call("POST", "/switch_tab", {"tab_id": tab_id})


def close_tab() -> dict:
    """Close current tab."""
    return _api_call("DELETE", "/tab")


# --- cookie/storage ---
def get_cookies() -> list:
    """Get all cookies."""
    return _api_call("GET", "/cookies").get("cookies", [])


def set_cookies(cookies: list) -> dict:
    """Set cookies."""
    return _api_call("POST", "/cookies", {"cookies": cookies})


def get_local_storage() -> dict:
    """Get localStorage."""
    return _api_call("GET", "/storage").get("localStorage", {})


def set_local_storage(items: dict) -> dict:
    """Set localStorage items."""
    return _api_call("POST", "/storage", {"localStorage": items})


# --- proxy/geoip ---
def set_proxy(proxy: dict) -> dict:
    """Set proxy for browser. {server, username, password}."""
    return _api_call("POST", "/proxy", proxy)


def set_geolocation(lat: float, lon: float) -> dict:
    """Set geolocation."""
    return _api_call("POST", "/geolocation", {"latitude": lat, "longitude": lon})


# --- session ---
def save_profile(name: str) -> dict:
    """Save current session to named profile."""
    return _api_call("POST", "/profile/save", {"name": name})


def load_profile(name: str) -> dict:
    """Load named profile."""
    return _api_call("POST", "/profile/load", {"name": name})


# --- anti-detect helpers ---
def human_click(selector: str) -> dict:
    """Human-like click with random delays and cursor movement."""
    random_delay(0.1, 0.3)
    result = click(selector)
    random_delay(0.5, 1.5)
    return result


def human_type(selector: str, text: str, typo_rate: float = 0.02) -> dict:
    """Human-like typing with random delays and occasional typos."""
    result = {"typed": text}
    for char in text:
        if random.random() < typo_rate and char.isalnum():
            # Typo: random nearby key
            wrong = random.choice("abcdefghijklmnopqrstuvwxyz")
            type_text(selector, wrong)
            time.sleep(random.uniform(0.1, 0.3))
            press_key("Backspace")
            time.sleep(random.uniform(0.1, 0.2))
        type_text(selector, char)
        time.sleep(random.uniform(0.05, 0.15))
    random_delay(0.3, 0.8)
    return result


def stealth_mode(enable: bool = True) -> dict:
    """Enable/disable stealth mode (humanize, fingerprint randomization)."""
    return _api_call("POST", "/stealth", {"enabled": enable})
