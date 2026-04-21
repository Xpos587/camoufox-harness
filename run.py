#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "playwright>=1.40.0",
#   "camoufox[geoip]>=0.4.0",
#   "pillow>=10.0.0",
#   "numpy>=1.24.0",
#   "imageio[ffmpeg]>=2.31.0",
# ]
# ///

"""Camoufox Harness CLI (async)."""
import asyncio
import sys
from helpers import *

HELP = """Camoufox Harness — Playwright-based browser automation with anti-detect.

Usage:
  uv run run.py <<'PY'
  await goto("https://example.com")
  await wait_for_load()
  print(await page_info())
  PY

Helpers are pre-imported. Persistent context saves data automatically.
"""


async def main_async():
    if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
        print(HELP)
        return

    if sys.stdin.isatty():
        sys.exit(
            "camoufox-harness reads Python from stdin. Use:\n"
            "  uv run run.py <<'PY'\n"
            "  await goto('https://example.com')\n"
            "  await wait_for_load()\n"
            "  print(await page_info())\n"
            "  PY"
        )

    code = sys.stdin.read()

    # Wrap in async function to support await
    lines = code.splitlines()
    wrapped = "async def _():\n    " + "\n    ".join(lines)
    exec(wrapped, globals())
    await _()



if __name__ == "__main__":
    asyncio.run(main_async())
