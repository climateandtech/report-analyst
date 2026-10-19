"""Tests for the desktop launcher path and Streamlit argv helpers."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_APP = REPO_ROOT / "desktop" / "run_app.py"
REQUIREMENTS = REPO_ROOT / "requirements-desktop.txt"
FORBIDDEN = ("psycopg2", "faiss", "onnxruntime", "pytest", "boto3", "kubernetes")


def load_run_app():
    spec = importlib.util.spec_from_file_location("desktop_run_app", RUN_APP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def run_app():
    return load_run_app()


def test_repo_root_finds_streamlit_app(run_app):
    root = run_app.repo_root()
    assert (root / "report_analyst" / "streamlit_app.py").is_file()


def test_app_data_dir_uses_os_locations(run_app):
    home = Path("/Users/analyst")
    assert run_app.app_data_dir("darwin", {}, home) == (
        home / "Library" / "Application Support" / "Open Sustainability Analyst"
    )
    windows_env = {"APPDATA": r"C:\Users\analyst\AppData\Roaming"}
    assert (
        run_app.app_data_dir("win32", windows_env, home)
        == Path(r"C:\Users\analyst\AppData\Roaming") / "Open Sustainability Analyst"
    )


def test_app_data_dir_honors_the_sandbox_container(run_app, tmp_path):
    """The Mac App Store build passes its container path instead of the home folder."""
    container = tmp_path / "container"
    assert run_app.app_data_dir("darwin", {"OSA_APP_DATA_DIR": str(container)}, Path("/Users/analyst")) == container


def test_bundled_python_matches_standalone_layout(run_app):
    prefix = Path("/opt/osa/python")
    assert run_app.bundled_python(prefix, "darwin") == prefix / "bin" / "python3"
    assert run_app.bundled_python(prefix, "win32") == prefix / "python.exe"


def test_streamlit_argv_binds_localhost_and_skips_shebang(run_app):
    argv = run_app.streamlit_argv(8501, Path("report_analyst/streamlit_app.py"))
    assert argv[1:4] == ["-m", "streamlit", "run"]
    assert "--server.address" in argv
    assert argv[argv.index("--server.address") + 1] == "127.0.0.1"
    assert argv[argv.index("--server.port") + 1] == "8501"
    assert run_app.desktop_url(8501) == "http://127.0.0.1:8501"


def test_pick_port_is_a_free_localhost_port(run_app):
    port = run_app.pick_port()
    assert 1 <= port <= 65535


def test_prefix_check_flags_absolute_paths_in_the_library_tree(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "desktop_check_prefix_paths",
        REPO_ROOT / "desktop" / "check_prefix_paths.py",
    )
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)

    lib = tmp_path / "lib" / "python3.12"
    lib.mkdir(parents=True)
    (lib / "clean.py").write_text("x = 1\n", encoding="utf-8")
    (lib / "leaky.py").write_text(f"# built at {tmp_path}\n", encoding="utf-8")
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "streamlit").write_text(f"#!{tmp_path}/bin/python3\n", encoding="utf-8")

    leaked = checker.offending_files(tmp_path)
    assert leaked == [lib / "leaky.py"]


def test_isolate_local_store_forces_sqlite_file(run_app, tmp_path):
    environ = {"DATABASE_URL": "postgresql://analyst:secret@db/reports"}
    db_file = run_app.isolate_local_store(tmp_path, environ)
    assert db_file == (tmp_path / "storage" / "cache" / "analysis.db").resolve()
    assert environ["DATABASE_URL"] == "sqlite:///" + db_file.as_posix()
    assert environ["DATABASE_URL"].startswith("sqlite:")
    assert environ["STORAGE_PATH"] == str(tmp_path / "storage")
    assert Path(environ["OSA_TEMP_DIR"]).is_dir()
    assert environ["USE_POSTGRES_FILE_STORAGE"] == "false"


def test_remote_manifests_are_version_and_notice_files():
    """The git files Electron fetches are a version gate and a notice list."""
    release = json.loads((REPO_ROOT / "desktop" / "remote" / "release.json").read_text())
    notices = json.loads((REPO_ROOT / "desktop" / "remote" / "notices.json").read_text())
    package = json.loads((REPO_ROOT / "desktop" / "package.json").read_text())

    assert set(release) == {"version", "minVersion", "url"}
    assert re.fullmatch(r"\d+\.\d+\.\d+", release["version"])
    assert re.fullmatch(r"\d+\.\d+\.\d+", release["minVersion"])
    assert release["url"].startswith("https://")
    assert release["version"] == package["version"]
    assert isinstance(notices["notices"], list)
    for notice in notices["notices"]:
        assert re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", notice["id"])
        assert notice["message"].strip()
        assert "<" not in notice["message"]


def test_desktop_requirements_omit_server_only_packages():
    pinned = "\n".join(line.split("#", 1)[0].strip().lower() for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines())
    for name in FORBIDDEN:
        assert name not in pinned
    assert "streamlit==" in pinned
    assert "pymupdf==" in pinned
