"""Checks an XBRL report with Arelle against the ESRS taxonomy package."""

import json
import shutil
import tempfile
from pathlib import Path
from typing import NamedTuple

from arelle.api.Session import Session
from arelle.RuntimeOptions import RuntimeOptions

from report_analyst.core.xbrl_report import FACT_ID


class XbrlProblem(NamedTuple):
    """A problem Arelle found, on a tag or, without a tag id, in the taxonomy package itself."""

    tag_id: str | None
    message: str


def check_xbrl(report: str, package: str | Path) -> list[XbrlProblem]:
    """Check the report offline, with the taxonomy package as a zip or an unzipped folder."""
    package = Path(package)
    with tempfile.TemporaryDirectory() as folder:
        report_file = Path(folder) / "report.xbrl"
        report_file.write_text(report, encoding="utf-8")
        if package.is_dir():
            # Arelle reads packages only from a zip, with the package folder at its top.
            package = Path(shutil.make_archive(str(Path(folder) / "package"), "zip", package.parent, package.name))
        options = RuntimeOptions(
            entrypointFile=str(report_file),
            packages=[str(package)],
            validate=True,
            internetConnectivity="offline",
            logFormat="%(message)s",
        )
        with Session() as session:
            session.run(options, logFileName="logToBuffer")
            log = json.loads(session.get_logs("json"))["log"]
    return [_problem(entry) for entry in log if entry["level"] != "info"]


def _problem(entry: dict) -> XbrlProblem:
    fact = f"#{FACT_ID}"
    hrefs = [ref.get("href", "") for ref in entry.get("refs", [])]
    tag_id = next((href.partition(fact)[2] for href in hrefs if fact in href), None)
    return XbrlProblem(tag_id, entry["message"]["text"])
