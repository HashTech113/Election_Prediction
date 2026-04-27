"""Unified launcher for the Election Prediction Dashboard.

Boots, in one terminal:
    * Tamil Nadu backend (HTTP server) on TN_BACKEND_PORT  (default 8101)
    * Kerala     backend (FastAPI/uvicorn) on KL_BACKEND_PORT (default 8201)
    * Tamil Nadu frontend (Vite) on TN_FRONTEND_PORT       (default 5174)
    * Kerala     frontend (Vite) on KL_FRONTEND_PORT       (default 5175)
    * Landing page (static)        on LANDING_PORT          (default 5173)

The landing page lives at:
    http://127.0.0.1:<LANDING_PORT>/

Each frontend is started with VITE_API_BASE_URL pre-wired to its backend so
the existing dashboards talk to their own API without any code changes.

After spawning everything, the launcher actively probes both backend
/api/health endpoints and both Vite dev ports so failed boots are
reported on the launcher console — not silently as "only Kerala opens".

Usage:
    python run_all.py

Stop everything with Ctrl+C — all child processes are terminated cleanly.
"""
from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TN_DIR = ROOT / "tamilnadu"
KL_DIR = ROOT / "kerala"
LANDING_DIR = ROOT / "landing_page"


def env_port(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"[warn] {name}={raw!r} is not an int, falling back to {default}")
        return default


TN_BACKEND_PORT = env_port("TN_BACKEND_PORT", 8101)
KL_BACKEND_PORT = env_port("KL_BACKEND_PORT", 8201)
TN_FRONTEND_PORT = env_port("TN_FRONTEND_PORT", 5174)
KL_FRONTEND_PORT = env_port("KL_FRONTEND_PORT", 5175)
LANDING_PORT = env_port("LANDING_PORT", 5173)
HOST = os.getenv("HOST", "0.0.0.0")


def _start(name: str, cmd, cwd: Path | None = None, env: dict | None = None):
    print(f"[start] {name}: {' '.join(str(c) for c in cmd)}  (cwd={cwd or ROOT})")
    return subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else str(ROOT),
        env=env,
        stdout=None,
        stderr=None,
    )


def _local_ipv4() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def _port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


def _probe_http(url: str, timeout: float = 1.2) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except (urllib.error.URLError, socket.timeout, ConnectionError):
        return False


def _wait_for(label: str, ready_fn, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ready_fn():
            print(f"[ready] {label}")
            return True
        time.sleep(0.4)
    print(f"[warn]  {label}  did not become ready within {timeout:.0f}s")
    return False


def _check_paths() -> None:
    missing = []
    for label, path in [
        ("Tamil Nadu folder", TN_DIR),
        ("Kerala folder", KL_DIR),
        ("Landing page folder", LANDING_DIR),
        ("TN backend server.py", TN_DIR / "backend" / "server.py"),
        ("Kerala backend main.py", KL_DIR / "backend" / "main.py"),
        ("TN frontend package.json", TN_DIR / "frontend" / "package.json"),
        ("Kerala frontend package.json", KL_DIR / "frontend" / "package.json"),
        ("Landing index.html", LANDING_DIR / "index.html"),
    ]:
        if not path.exists():
            missing.append(f"  - {label}: {path}")
    if missing:
        print("[fatal] Required paths are missing:")
        print("\n".join(missing))
        sys.exit(1)

    if shutil.which("npm") is None:
        print("[fatal] npm not found in PATH — install Node.js (>= 18) first.")
        sys.exit(1)


def _check_ports_free() -> None:
    """Bail out *before* spawning if any port we need is already taken.

    This is the most common reason a dashboard "won't open" — Vite or
    uvicorn happily fall back to a random free port and the launcher
    points the user at the wrong one.
    """
    busy = []
    for label, port in [
        ("TN backend", TN_BACKEND_PORT),
        ("Kerala backend", KL_BACKEND_PORT),
        ("TN frontend", TN_FRONTEND_PORT),
        ("Kerala frontend", KL_FRONTEND_PORT),
        ("Landing page", LANDING_PORT),
    ]:
        if _port_in_use(port):
            busy.append(f"  - {label} port {port}")
    if busy:
        print(
            "[fatal] One or more required ports are already in use. Free them or "
            "override via env vars (TN_BACKEND_PORT, TN_FRONTEND_PORT, "
            "KL_BACKEND_PORT, KL_FRONTEND_PORT, LANDING_PORT):"
        )
        print("\n".join(busy))
        sys.exit(1)


def _spawn_tn_backend() -> subprocess.Popen:
    env = os.environ.copy()
    env["HOST"] = HOST
    env["PORT"] = str(TN_BACKEND_PORT)
    cmd = [sys.executable, "server.py"]
    return _start("tn-backend", cmd, cwd=TN_DIR / "backend", env=env)


def _spawn_kl_backend() -> subprocess.Popen:
    env = os.environ.copy()
    env["HOST"] = HOST
    env["PORT"] = str(KL_BACKEND_PORT)
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--app-dir",
        str(KL_DIR / "backend"),
        "--host",
        HOST,
        "--port",
        str(KL_BACKEND_PORT),
    ]
    return _start("kl-backend", cmd, cwd=KL_DIR, env=env)


def _spawn_frontend(name: str, frontend_dir: Path, port: int, api_url: str) -> subprocess.Popen:
    env = os.environ.copy()
    env["VITE_API_BASE_URL"] = api_url
    env["VITE_API_URL"] = api_url
    env["VITE_DEV_HOST"] = HOST
    env["VITE_DEV_PORT"] = str(port)
    npm = shutil.which("npm") or "npm"
    # `--strictPort` makes Vite fail loudly instead of jumping to a random
    # port when the requested one is busy — so the launcher's printed URL
    # is always the actual URL.
    cmd = [
        npm,
        "run",
        "dev",
        "--",
        "--host",
        HOST,
        "--port",
        str(port),
        "--strictPort",
    ]
    return _start(name, cmd, cwd=frontend_dir, env=env)


def _spawn_landing() -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "http.server",
        str(LANDING_PORT),
        "--bind",
        HOST,
        "--directory",
        str(LANDING_DIR),
    ]
    return _start("landing", cmd, cwd=LANDING_DIR)


def _ensure_npm_install(frontend_dir: Path) -> None:
    if (frontend_dir / "node_modules").exists():
        return
    print(f"[setup] Installing npm packages in {frontend_dir} (first run only)…")
    npm = shutil.which("npm") or "npm"
    result = subprocess.run([npm, "install"], cwd=str(frontend_dir))
    if result.returncode != 0:
        print(f"[fatal] npm install failed in {frontend_dir}")
        sys.exit(result.returncode)


def main() -> None:
    _check_paths()
    _check_ports_free()
    _ensure_npm_install(TN_DIR / "frontend")
    _ensure_npm_install(KL_DIR / "frontend")

    tn_api_url = f"http://127.0.0.1:{TN_BACKEND_PORT}"
    kl_api_url = f"http://127.0.0.1:{KL_BACKEND_PORT}"

    procs: list[subprocess.Popen] = []
    procs.append(_spawn_tn_backend())
    procs.append(_spawn_kl_backend())
    time.sleep(0.6)
    procs.append(
        _spawn_frontend(
            "tn-frontend",
            TN_DIR / "frontend",
            TN_FRONTEND_PORT,
            tn_api_url,
        )
    )
    procs.append(
        _spawn_frontend(
            "kl-frontend",
            KL_DIR / "frontend",
            KL_FRONTEND_PORT,
            kl_api_url,
        )
    )
    procs.append(_spawn_landing())

    print("\n[probe] Waiting for services to come up…")
    tn_ok = _wait_for(
        f"TN backend     http://127.0.0.1:{TN_BACKEND_PORT}/api/health",
        lambda: _probe_http(f"http://127.0.0.1:{TN_BACKEND_PORT}/api/health"),
        timeout=45.0,
    )
    kl_ok = _wait_for(
        f"Kerala backend http://127.0.0.1:{KL_BACKEND_PORT}/api/health",
        lambda: _probe_http(f"http://127.0.0.1:{KL_BACKEND_PORT}/api/health"),
        timeout=45.0,
    )
    tn_fe = _wait_for(
        f"TN frontend    http://127.0.0.1:{TN_FRONTEND_PORT}",
        lambda: _port_in_use(TN_FRONTEND_PORT),
        timeout=60.0,
    )
    kl_fe = _wait_for(
        f"Kerala frontend http://127.0.0.1:{KL_FRONTEND_PORT}",
        lambda: _port_in_use(KL_FRONTEND_PORT),
        timeout=60.0,
    )
    landing_ok = _wait_for(
        f"Landing page    http://127.0.0.1:{LANDING_PORT}",
        lambda: _port_in_use(LANDING_PORT),
        timeout=15.0,
    )

    local_ip = _local_ipv4()

    print("\n" + "=" * 64)
    print(" Election Prediction Dashboard — unified launcher is live")
    print("=" * 64)
    status = lambda ok: "OK " if ok else "FAIL"
    print(f"  [{status(landing_ok)}] Landing page (open this):   http://127.0.0.1:{LANDING_PORT}")
    print(f"  [{status(tn_fe)}] Tamil Nadu dashboard:       http://127.0.0.1:{TN_FRONTEND_PORT}")
    print(f"  [{status(kl_fe)}] Kerala dashboard:           http://127.0.0.1:{KL_FRONTEND_PORT}")
    print(f"  [{status(tn_ok)}] Tamil Nadu API:             http://127.0.0.1:{TN_BACKEND_PORT}/api/health")
    print(f"  [{status(kl_ok)}] Kerala API:                 http://127.0.0.1:{KL_BACKEND_PORT}/api/health")
    if local_ip and HOST in {"0.0.0.0", "::"}:
        print()
        print(f"  LAN landing page:           http://{local_ip}:{LANDING_PORT}")
        print(f"  LAN TN dashboard:           http://{local_ip}:{TN_FRONTEND_PORT}")
        print(f"  LAN Kerala dashboard:       http://{local_ip}:{KL_FRONTEND_PORT}")

    if not all([tn_ok, kl_ok, tn_fe, kl_fe]):
        print(
            "\n[!] One or more services failed to come up. Scroll up for the "
            "child process output — most often this is a Python import error "
            "in the failing backend, or an `npm install` that hasn't finished."
        )

    print("\nPress Ctrl+C to stop everything.\n")

    def shutdown(*_: object) -> None:
        print("\n[stop] Shutting down all servers…")
        for proc in procs:
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except Exception:
                    pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            for proc in procs:
                if proc.poll() is not None:
                    print(
                        f"[fatal] A child process exited (code={proc.returncode}). "
                        "Stopping the rest."
                    )
                    shutdown()
            time.sleep(0.6)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
