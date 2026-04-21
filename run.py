# /// script
# dependencies = [
#   "playwright>=1.40.0",
# ]
# ///

"""Camoufox Harness CLI (async)."""
import asyncio
import sys
from admin import ensure_daemon
from helpers import *

HELP = """Camoufox Harness — Playwright-based browser automation with anti-detect.

Read SKILL.md for the default workflow and examples.

Typical usage:
  uv run camoufox-harness <<'PY'
  import asyncio
  async def test():
      await goto("https://example.com")
      await wait_for_load()
      print(await page_info())
  asyncio.run(test())
  PY

Helpers are pre-imported. The daemon auto-starts Camoufox browser.
"""


async def main_async():
    if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
        print(HELP)
        return

    if sys.stdin.isatty():
        sys.exit(
            "camoufox-harness reads Python from stdin. Use:\n"
            "  uv run camoufox-harness <<'PY'\n"
            "  print(page_info())\n"
            "  PY"
        )

    await ensure_daemon()

    code = sys.stdin.read()

    # Execute async code
    # Wrap in async function if needed
    if "await " in code:
        exec(code)
    else:
        # Auto-await for simple scripts
        result = eval(code)
        if asyncio.iscoroutine(result):
            await result


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
