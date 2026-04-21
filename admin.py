# /// script
# dependencies = [
#   "camoufox[geoip]>=0.4.0",
#   "psutil>=5.9.0",
# ]
# ///

"""Manage Camoufox remote server daemon."""
import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from threading import Thread

import psutil


NAME = os.environ.get("CH_NAME", "default")
PORT = int(os.environ.get("CH_PORT", "9222"))
WS_PATH = os.environ.get("CH_WS_PATH", "camoufox")
PID_FILE = Path(f"/tmp/camoufox-harness-{NAME}.pid")

# Server instance (global for stop)
_server_thread = None


def run_server():
    """Run Camoufox remote server (blocking)."""
    from camoufox.server import launch_server
    launch_server(
        headless=True,
        humanize=True,
        geoip=True,
        port=PORT,
        ws_path=WS_PATH,
    )


def is_running():
    """Check if daemon is running."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text())
        return psutil.pid_exists(pid)
    except (ValueError, psutil.NoSuchProcess):
        return False


def start_daemon():
    """Start Camoufox remote server in background thread."""
    global _server_thread

    if is_running():
        print(f"Daemon already running (name={NAME})", file=sys.stderr)
        return

    print(f"Starting Camoufox daemon (name={NAME}, port={PORT})...", file=sys.stderr)

    _server_thread = Thread(target=run_server, daemon=True)
    _server_thread.start()

    # Write PID (main process PID)
    PID_FILE.write_text(str(os.getpid()))
    print(f"Daemon started (WS: ws://localhost:{PORT}/{WS_PATH})", file=sys.stderr)


def stop_daemon():
    """Stop daemon."""
    if not PID_FILE.exists():
        print("Daemon not running", file=sys.stderr)
        return

    try:
        pid = int(PID_FILE.read_text())
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink()
        print(f"Daemon stopped (PID={pid})", file=sys.stderr)
    except (ValueError, ProcessLookupError):
        try:
            PID_FILE.unlink()
        except:
            pass


def restart_daemon():
    """Restart daemon."""
    stop_daemon()
    time.sleep(1)
    start_daemon()


async def ensure_daemon():
    """Ensure daemon is running."""
    if is_running():
        return
    start_daemon()
    await asyncio.sleep(2)  # Wait for server startup


def status():
    """Show daemon status."""
    if is_running():
        pid = int(PID_FILE.read_text())
        print(f"Daemon: running (PID={pid}, WS: ws://localhost:{PORT}/{WS_PATH})")
    else:
        print("Daemon: not running")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "start":
            start_daemon()
        elif cmd == "stop":
            stop_daemon()
        elif cmd == "restart":
            restart_daemon()
        elif cmd == "status":
            status()
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)
    else:
        asyncio.run(ensure_daemon())
