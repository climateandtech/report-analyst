#!/usr/bin/env python3
"""Download the exact reports configured for a ClimRetrieve benchmark."""

from __future__ import annotations

import argparse
import shutil
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import BinaryIO
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

import yaml

QUESTION_SET_DIRECTORY = Path(__file__).parent.parent / "report_analyst" / "questionsets"
RAW_REPORT_BASE_URL = "https://raw.githubusercontent.com/tobischimanski/ClimRetrieve/main/Reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--question-set",
        default="climretrieve_complete",
        help="Question-set YAML containing the authoritative documents list",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/climretrieve/reports"),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace reports that already exist",
    )
    return parser.parse_args()


def load_report_names(question_set: str) -> list[str]:
    path = QUESTION_SET_DIRECTORY / f"{question_set}_questions.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Question set not found: {path}")
    with path.open() as handle:
        config = yaml.safe_load(handle)
    reports = config.get("documents", [])
    if not reports:
        raise ValueError(f"Question set has no authoritative documents list: {path}")
    if len(reports) != len(set(reports)):
        raise ValueError(f"Question set contains duplicate documents: {path}")
    return reports


def build_download_url(filename: str) -> str:
    return f"{RAW_REPORT_BASE_URL}/{quote(filename, safe='')}"


def open_report(url: str) -> BinaryIO:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise ValueError(f"Refusing non-ClimRetrieve download URL: {url}")
    request = Request(  # noqa: S310 - URL scheme and host validated above
        url,
        headers={"User-Agent": "report-analyst-climretrieve-downloader"},
    )
    return urlopen(  # noqa: S310 - URL scheme and host validated above
        request,
        timeout=60,
    )


def download_report(
    filename: str,
    output_dir: Path,
    *,
    overwrite: bool = False,
    opener: Callable[[str], BinaryIO] = open_report,
) -> bool:
    """Download one PDF atomically; return False when already present."""
    destination = output_dir / filename
    if destination.exists() and not overwrite:
        return False
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with opener(build_download_url(filename)) as response:
            with NamedTemporaryFile(
                dir=output_dir,
                prefix=f".{filename}.",
                suffix=".part",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                header = response.read(5)
                if header != b"%PDF-":
                    raise ValueError(f"Downloaded content is not a PDF: {filename}")
                temporary.write(header)
                shutil.copyfileobj(response, temporary)
        temporary_path.replace(destination)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return True


def main() -> None:
    args = parse_args()
    reports = load_report_names(args.question_set)
    downloaded = 0
    for index, filename in enumerate(reports, start=1):
        changed = download_report(
            filename,
            args.output_dir,
            overwrite=args.overwrite,
        )
        downloaded += int(changed)
        action = "downloaded" if changed else "already present"
        print(f"[{index}/{len(reports)}] {action}: {filename}")
    print(f"Complete: {downloaded} downloaded, {len(reports) - downloaded} skipped.")


if __name__ == "__main__":
    main()
