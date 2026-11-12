"""Local QG must fail black --check the same way CI lint does."""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LINT_CHANGED = REPO_ROOT / "scripts" / "lint-changed.sh"


def test_lint_changed_fails_when_black_would_reformat(tmp_path: Path) -> None:
    bad = tmp_path / "bad_format.py"
    # 2-space indent is always reformatted by black.
    bad.write_text(
        textwrap.dedent("""\
            def f():
              return 1
            """),
        encoding="utf-8",
    )

    bash = shutil.which("bash")
    assert bash is not None
    result = subprocess.run(  # noqa: S603
        [bash, str(LINT_CHANGED), str(bad)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "black --check" in combined
    assert "would reformat" in combined or "Oh no" in combined
