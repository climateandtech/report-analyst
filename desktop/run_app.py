"""Launch the Streamlit analyst app on localhost for the desktop shell."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

APP_DATA_DIR_NAME = "Open Sustainability Analyst"
URL_PREFIX = "OSA_DESKTOP_URL="


def repo_root() -> Path:
    """Return the directory that contains report_analyst/streamlit_app.py."""
    here = Path(__file__).resolve().parent
    candidates = (here, here.parent)
    for candidate in candidates:
        if (candidate / "report_analyst" / "streamlit_app.py").is_file():
            return candidate
    raise SystemExit("Cannot find report_analyst next to the desktop launcher")


def app_data_dir(
    platform_name: str | None = None,
    environ: dict[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the per-user directory for SQLite, logs, and .env."""
    platform_name = sys.platform if platform_name is None else platform_name
    environ = os.environ if environ is None else environ
    home = Path.home() if home is None else home
    if platform_name == "win32":
        base = environ.get("APPDATA") or str(home / "AppData" / "Roaming")
        return Path(base) / APP_DATA_DIR_NAME
    if platform_name == "darwin":
        return home / "Library" / "Application Support" / APP_DATA_DIR_NAME
    return home / ".local" / "share" / "open-sustainability-analyst"


def bundled_python(prefix: Path, platform_name: str | None = None) -> Path:
    """Return the interpreter inside a python-build-standalone prefix."""
    platform_name = sys.platform if platform_name is None else platform_name
    if platform_name == "win32":
        return prefix / "python.exe"
    return prefix / "bin" / "python3"


def pick_port() -> int:
    """Bind an ephemeral localhost port and return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def desktop_url(port: int) -> str:
    """Return the localhost URL the Electron window loads."""
    return f"http://127.0.0.1:{port}"


def streamlit_argv(port: int, app_path: Path) -> list[str]:
    """Argv for `python -m streamlit`, so shebangs in the prefix are unused."""
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--server.fileWatcherType",
        "none",
        "--browser.gatherUsageStats",
        "false",
    ]


def _load_env_files(root: Path, data_dir: Path) -> None:
    from dotenv import load_dotenv

    load_dotenv(root / ".env")
    load_dotenv(data_dir / ".env", override=True)


def isolate_local_store(data_dir: Path, environ: dict[str, str] | None = None) -> Path:
    """Point the process at one on-disk SQLite file and keep user files beside it.

    A repository ``.env`` may set ``DATABASE_URL`` to Postgres. The desktop app
    replaces that after dotenv loads so analysis stays in this directory.
    """
    environ = os.environ if environ is None else environ
    storage = data_dir / "storage"
    (storage / "cache").mkdir(parents=True, exist_ok=True)
    (storage / "llm_cache").mkdir(parents=True, exist_ok=True)
    (data_dir / "temp").mkdir(parents=True, exist_ok=True)
    (data_dir / "logs").mkdir(parents=True, exist_ok=True)
    db_file = (storage / "cache" / "analysis.db").resolve()
    environ["STORAGE_PATH"] = str(storage)
    environ["DATABASE_URL"] = "sqlite:///" + db_file.as_posix()
    environ["OSA_TEMP_DIR"] = str(data_dir / "temp")
    environ["OSA_LOG_FILE"] = str(data_dir / "logs" / "app.log")
    environ["USE_POSTGRES_FILE_STORAGE"] = "false"
    return db_file


def main() -> None:
    """Start Streamlit bound to 127.0.0.1 and print OSA_DESKTOP_URL for Electron."""
    root = repo_root()
    data_dir = app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["PYTHONNOUSERSITE"] = "1"
    os.environ["QUESTIONSETS_PATH"] = str(root / "report_analyst" / "questionsets")
    os.chdir(root)
    _load_env_files(root, data_dir)
    isolate_local_store(data_dir)

    port = pick_port()
    print(f"{URL_PREFIX}{desktop_url(port)}", flush=True)
    app_path = root / "report_analyst" / "streamlit_app.py"
    # Replace this process with the same interpreter. argv is built locally, not from user input.
    os.execv(sys.executable, streamlit_argv(port, app_path))  # noqa: S606


if __name__ == "__main__":
    main()
