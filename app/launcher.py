"""Desktop launcher: start the local server and open the browser.

This is the entry point for the packaged (PyInstaller) build. Double-clicking
the executable starts the offline web app on localhost and opens the default
browser to it. Everything stays on the machine.

Also runnable during development::

    python -m app.launcher
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

from app.web.server import app

HOST = "127.0.0.1"


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) != 0


def choose_port() -> int:
    """Prefer TT_PORT, then 8000+, else an OS-assigned free port."""
    env = os.environ.get("TT_PORT")
    if env and env.isdigit() and _port_is_free(int(env)):
        return int(env)
    for port in range(8000, 8010):
        if _port_is_free(port):
            return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def _open_when_ready(url: str, port: int) -> None:
    """Wait until the server accepts connections, then open the browser."""
    for _ in range(100):  # up to ~10s
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, port)) == 0:
                break
        time.sleep(0.1)
    if os.environ.get("TT_NO_BROWSER") != "1":
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 - headless / no browser is fine
            pass


def main() -> None:
    port = choose_port()
    url = f"http://{HOST}:{port}"

    print("=" * 58)
    print("  Offline Text Transformation")
    print(f"  Running at {url}")
    print("  Close this window (or press Ctrl+C) to stop.")
    print("=" * 58)

    threading.Thread(target=_open_when_ready, args=(url, port), daemon=True).start()

    try:
        uvicorn.run(app, host=HOST, port=port, log_level="warning")
    except KeyboardInterrupt:
        pass
    print("\nStopped.")


if __name__ == "__main__":
    sys.exit(main())
