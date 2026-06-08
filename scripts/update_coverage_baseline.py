"""Update scripts/coverage-baseline.json from a pytest-cov JSON report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from check_coverage_regression import normalize_app_rel, parse_module_coverage


def main(argv: list[str] | None = None) -> int:
    """Merge measured module percentages into the baseline file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-json", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--monorepo-prefix", default="")
    parser.add_argument("--app-file", action="append", default=[], dest="app_files")
    parser.add_argument(
        "--set-min-from-current",
        action="store_true",
        help="When set, only update modules listed in --app-file",
    )
    args = parser.parse_args(argv)

    data = json.loads(args.coverage_json.read_text(encoding="utf-8"))
    repo_root = args.coverage_json.resolve().parent.parent
    by_path = parse_module_coverage(
        data,
        repo_root=repo_root,
        monorepo_prefix=args.monorepo_prefix,
    )
    baseline_path = args.baseline
    existing: dict = {}
    if baseline_path.is_file():
        existing = json.loads(baseline_path.read_text(encoding="utf-8"))
    modules: dict[str, float] = dict(existing.get("modules") or {})

    targets = args.app_files or list(by_path.keys())
    for rel in targets:
        rel = normalize_app_rel(rel, monorepo_prefix=args.monorepo_prefix)
        cov = by_path.get(rel)
        if cov is None:
            continue
        modules[cov.module] = round(cov.percent, 2)

    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps({"modules": modules}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {baseline_path} ({len(modules)} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
