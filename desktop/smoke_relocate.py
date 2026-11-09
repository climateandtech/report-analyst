"""Move the bundled prefix, import numpy and fitz, then move it back."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from run_app import bundled_python

IMPORT_CHECK = (
    "import numpy, fitz, sys\n"
    "from pathlib import Path\n"
    "prefix = Path(sys.argv[1]).resolve()\n"
    "executable = Path(sys.executable).resolve()\n"
    "if prefix not in executable.parents:\n"
    "    raise SystemExit(f'interpreter {executable} is outside {prefix}')\n"
    "print('relocated-import-ok', numpy.__version__)\n"
)


def system_path() -> str:
    """PATH that does not prefer a user or Homebrew Python."""
    if sys.platform == "win32":
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        return os.pathsep.join(
            [
                str(Path(system_root) / "System32"),
                system_root,
            ]
        )
    return os.pathsep.join(["/usr/bin", "/bin", "/usr/sbin", "/sbin"])


def relocate_and_import(prefix: Path) -> None:
    """Move prefix to a temp dir, import from that interpreter, then restore it."""
    if not prefix.is_dir():
        raise SystemExit(f"missing prefix: {prefix}")
    destination_parent = Path(tempfile.mkdtemp(prefix="osa-prefix-", dir=prefix.parent))
    destination = destination_parent / "python"
    shutil.move(str(prefix), str(destination))
    try:
        binary = bundled_python(destination)
        env = os.environ.copy()
        env["PATH"] = system_path()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONNOUSERSITE"] = "1"
        env.pop("PYTHONHOME", None)
        env.pop("PYTHONPATH", None)
        # binary is the interpreter inside the prefix we just moved, not user input.
        subprocess.run(  # noqa: S603
            [str(binary), "-c", IMPORT_CHECK, str(destination)],
            check=True,
            env=env,
        )
    finally:
        if destination.exists() and not prefix.exists():
            shutil.move(str(destination), str(prefix))
        if destination_parent.exists():
            shutil.rmtree(destination_parent, ignore_errors=True)


def main() -> None:
    prefix = Path(__file__).resolve().parent / "python"
    relocate_and_import(prefix)


if __name__ == "__main__":
    main()
