"""Start the app temporarily and verify the local Streamlit HTTP endpoints."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request


BASE_DIR = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PORT = 8765


def wait_for_server(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
    raise SystemExit(f"Streamlit did not start within {timeout:.0f}s: {last_error}")


def main() -> None:
    env = os.environ.copy()
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.headless=true",
        f"--server.address={HOST}",
        f"--server.port={PORT}",
    ]
    process = subprocess.Popen(
        command,
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        health_url = f"http://{HOST}:{PORT}/_stcore/health"
        wait_for_server(health_url)
        for url in [health_url, f"http://{HOST}:{PORT}/"]:
            with urllib.request.urlopen(url, timeout=10) as response:
                body = response.read(2048)
                if response.status != 200:
                    raise SystemExit(f"{url} returned status {response.status}")
                if not body:
                    raise SystemExit(f"{url} returned an empty body")
                print(f"OK {url} {response.status} {len(body)} bytes")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    main()
