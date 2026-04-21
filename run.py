# /// script
# dependencies = [
#   "httpx>=0.25.0",
# ]
# ///

"""Camoufox Harness CLI.

Run with: uv run run.py < script.py
Or make executable: chmod +x run.py && ./run.py < script.py
"""
import sys
from admin import ensure_daemon, restart_daemon
from helpers import *

HELP = """Camoufox Harness — Playwright-based browser automation with anti-detect.

Read SKILL.md for the default workflow and examples.

Typical usage:
  uv run camoufox-harness <<'PY'
  goto("https://example.com")
  wait_for_load()
  print(page_info())
  PY

Helpers are pre-imported. The daemon auto-starts Camoufox browser.
"""


def main():
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
    ensure_daemon()
    exec(sys.stdin.read())


if __name__ == "__main__":
    main()
