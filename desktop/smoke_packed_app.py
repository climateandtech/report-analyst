"""Smoke-test a packed .app: numpy/fitz import and Streamlit health."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

URL_MARKER = "OSA_DESKTOP_URL="


def app_paths(app: Path) -> tuple[Path, Path, Path]:
    resources = app / "Contents" / "Resources"
    python = resources / "python" / "bin" / "python3"
    if sys.platform == "win32":
        python = resources / "python" / "python.exe"
    launcher = resources / "run_app.py"
    return resources, python, launcher


def assert_python_allows_native_libs(python: Path) -> None:
    """Ad-hoc hardened Python must disable library validation or .so loads fail."""
    if sys.platform != "darwin":
        return
    listing = subprocess.check_output(  # noqa: S603
        ["/usr/bin/codesign", "-d", "--entitlements", ":-", str(python)],
        stderr=subprocess.STDOUT,
    ).decode("utf-8", errors="replace")
    if "disable-library-validation" not in listing:
        raise SystemExit(
            f"{python} is missing com.apple.security.cs.disable-library-validation; "
            "numpy/pandas native extensions will fail with a Team ID error"
        )


def assert_imports(resources: Path, python: Path) -> None:
    script = (
        "import os, sys\n"
        f"os.chdir({str(resources)!r})\n"
        f"sys.path.insert(0, {str(resources)!r})\n"
        "import numpy, fitz\n"
        "import report_analyst.streamlit_app\n"
        "print('packed-import-ok', numpy.__version__)\n"
    )
    subprocess.check_call(  # noqa: S603
        [str(python), "-c", script],
        env={**os.environ, "PYTHONNOUSERSITE": "1"},
    )


def assert_streamlit_health(resources: Path, python: Path, launcher: Path) -> None:
    env = {**os.environ, "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.Popen(  # noqa: S603
        [str(python), str(launcher)],
        cwd=str(resources),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    url = None
    try:
        assert proc.stdout is not None
        deadline = time.time() + 90
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line.startswith(URL_MARKER):
                url = line[len(URL_MARKER) :].strip()
                break
        if not url:
            raise SystemExit("packed app never printed OSA_DESKTOP_URL")
        health = url.rstrip("/") + "/_stcore/health"
        for _ in range(90):
            try:
                with urllib.request.urlopen(health, timeout=2) as response:  # noqa: S310
                    if response.status == 200:
                        print("packed-health-ok", url)
                        return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(1)
        raise SystemExit(f"Streamlit health never became ready at {health}")
    finally:
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise SystemExit(f"usage: {argv[0]} /path/to/App.app")
    app = Path(argv[1]).resolve()
    if not app.is_dir():
        raise SystemExit(f"missing app bundle: {app}")
    resources, python, launcher = app_paths(app)
    if not python.is_file() or not launcher.is_file():
        raise SystemExit(f"packed runtime missing under {resources}")
    assert_python_allows_native_libs(python)
    assert_imports(resources, python)
    assert_streamlit_health(resources, python, launcher)


if __name__ == "__main__":
    main(sys.argv)
