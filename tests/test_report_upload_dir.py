"""Tests for report PDF upload directory resolution."""

import pytest

from report_analyst.core.report_data_client import ReportDataClient
from report_analyst.core.service import get_report_temp_dir, get_report_upload_dir


@pytest.fixture(autouse=True)
def clear_upload_dir_env(monkeypatch):
    """Isolate upload-dir env for each test."""
    for key in (
        "REPORT_ANALYST_UPLOAD_DIR",
        "REPORT_ANALYST_TEMP",
        "TEMP_DIR",
        "STORAGE_PATH",
    ):
        monkeypatch.delenv(key, raising=False)


def test_upload_dir_defaults_to_project_temp():
    upload_dir = get_report_upload_dir()
    assert upload_dir.name == "temp"
    assert upload_dir.is_dir()


def test_upload_dir_uses_storage_path_uploads_subdir(tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    monkeypatch.setenv("STORAGE_PATH", str(storage))

    upload_dir = get_report_upload_dir()

    assert upload_dir == storage / "uploads"
    assert upload_dir.is_dir()


def test_report_analyst_upload_dir_overrides_storage_path(tmp_path, monkeypatch):
    custom = tmp_path / "custom-uploads"
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path / "storage"))
    monkeypatch.setenv("REPORT_ANALYST_UPLOAD_DIR", str(custom))

    upload_dir = get_report_upload_dir()

    assert upload_dir == custom.resolve()
    assert upload_dir.is_dir()


def test_legacy_report_analyst_temp_still_works(tmp_path, monkeypatch):
    custom = tmp_path / "legacy-temp"
    monkeypatch.setenv("REPORT_ANALYST_TEMP", str(custom))

    upload_dir = get_report_upload_dir()

    assert upload_dir == custom.resolve()


def test_temp_dir_legacy_env(tmp_path, monkeypatch):
    custom = tmp_path / "config-temp"
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path / "storage"))
    monkeypatch.setenv("TEMP_DIR", str(custom))

    upload_dir = get_report_upload_dir()

    assert upload_dir == custom.resolve()


def test_get_report_temp_dir_is_alias(tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    monkeypatch.setenv("STORAGE_PATH", str(storage))

    assert get_report_temp_dir() == get_report_upload_dir()
    assert get_report_temp_dir() == storage / "uploads"


def test_report_data_client_default_uses_upload_dir(tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    monkeypatch.setenv("STORAGE_PATH", str(storage))

    client = ReportDataClient()

    assert client.temp_dir == get_report_upload_dir()
    assert client.temp_dir == storage / "uploads"


_MINIMAL_PDF = (
    b"%PDF-1.4\n%Test PDF\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
    b"xref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
)


def test_report_data_client_lists_pdfs_under_storage_uploads(tmp_path, monkeypatch):
    pytest.importorskip("fitz")
    storage = tmp_path / "storage"
    uploads = storage / "uploads"
    uploads.mkdir(parents=True)
    (uploads / "report.pdf").write_bytes(_MINIMAL_PDF)
    monkeypatch.setenv("STORAGE_PATH", str(storage))

    names = [r.name for r in ReportDataClient().list_reports()]

    assert "report.pdf" in names
