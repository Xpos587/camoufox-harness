# /// script
# dependencies = [
#   "httpx>=0.25.0",
#   "psutil>=5.9.0",
# ]
# ///

"""Daemon management for Camoufox Harness.

Run with: uv run admin.py
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx
import psutil


NAME = os.environ.get("CH_NAME", "default")
API_URL = os.environ.get("CH_API_URL", "http://127.0.0.1:8765")
PID_FILE = Path(f"/tmp/camoufox-harness-{NAME}.pid")
DAEMON_SCRIPT = Path(__file__).parent / "daemon.py"


def is_running():
    """Check if daemon is running."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text())
        return psutil.pid_exists(pid)
    except (ValueError, psutil.NoSuchProcess):
        return False


def is_responsive():
    """Check if daemon API is responding."""
    try:
        with httpx.Client() as client:
            r = client.get(f"{API_URL}/health", timeout=2.0)
            return r.status_code == 200
    except httpx.HTTPError:
        return False


def start_daemon():
    """Start the daemon process."""
    if is_running():
        print(f"Daemon already running (name={NAME})", file=sys.stderr)
        return
    
    print(f"Starting Camoufox daemon (name={NAME})...", file=sys.stderr)
    
    # Start daemon in background
    log_file = Path(f"/tmp/camoufox-harness-{NAME}.log")
    process = subprocess.Popen(
        ["uv", "run", str(DAEMON_SCRIPT)],
        start_new_session=True,
        stdout=log_file.open("a"),
        stderr=subprocess.STDOUT,
    )
    
    # Wait for daemon to become responsive
    deadline = time.time() + 30
    while time.time() < deadline:
        if is_responsive():
            print(f"Daemon started (PID={process.pid})", file=sys.stderr)
            return
        time.sleep(0.5)
    
    raise RuntimeError("Daemon failed to start within 30 seconds")


def stop_daemon():
    """Stop the daemon process."""
    if not PID_FILE.exists():
        print("Daemon not running", file=sys.stderr)
        return
    
    try:
        pid = int(PID_FILE.read_text())
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to exit
        deadline = time.time() + 10
        while time.time() < deadline:
            if not psutil.pid_exists(pid):
                print(f"Daemon stopped (PID={pid})", file=sys.stderr)
                return
            time.sleep(0.2)
        
        # Force kill if needed
        os.kill(pid, signal.SIGKILL)
        print(f"Daemon force killed (PID={pid})", file=sys.stderr)
    except (ValueError, psutil.NoSuchProcess, ProcessLookupError):
        pass
    finally:
        try:
            PID_FILE.unlink()
        except FileNotFoundError:
            pass


def restart_daemon():
    """Restart the daemon."""
    stop_daemon()
    time.sleep(1)
    start_daemon()


def ensure_daemon():
    """Ensure daemon is running, start if not."""
    if is_running() and is_responsive():
        return
    start_daemon()


def status():
    """Show daemon status."""
    if is_running():
        pid = int(PID_FILE.read_text())
        responsive = is_responsive()
        print(f"Daemon: running (PID={pid}, responsive={responsive})")
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
        # Default: ensure daemon is running
        ensure_daemon()
