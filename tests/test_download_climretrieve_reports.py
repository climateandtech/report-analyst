"""Tests for downloading configured ClimRetrieve reports."""

from io import BytesIO

import pytest
from scripts.download_climretrieve_reports import (
    build_download_url,
    download_report,
    load_report_names,
    open_report,
)


def test_complete_profile_exposes_authoritative_report_names():
    assert len(load_report_names("climretrieve_complete")) == 13


def test_download_url_encodes_exact_report_filename():
    url = build_download_url("Starbucks Environmental & Social Impact Report 2022.pdf")

    assert url.endswith("Starbucks%20Environmental%20%26%20Social%20Impact%20Report%202022.pdf")


def test_open_report_rejects_untrusted_url():
    with pytest.raises(ValueError, match="Refusing"):
        open_report("file:///tmp/Report.pdf")


def test_download_report_writes_valid_pdf_atomically(tmp_path):
    downloaded = download_report(
        "Report.pdf",
        tmp_path,
        opener=lambda _url: BytesIO(b"%PDF-1.7\nreport"),
    )

    assert downloaded
    assert (tmp_path / "Report.pdf").read_bytes() == b"%PDF-1.7\nreport"
    assert not list(tmp_path.glob("*.part"))


def test_download_report_rejects_non_pdf_content(tmp_path):
    with pytest.raises(ValueError, match="not a PDF"):
        download_report(
            "Report.pdf",
            tmp_path,
            opener=lambda _url: BytesIO(b"<html>error</html>"),
        )

    assert not (tmp_path / "Report.pdf").exists()
