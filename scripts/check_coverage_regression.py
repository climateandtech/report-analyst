"""Coverage regression checks for quality gate (touched modules + changed lines)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModuleCoverage:
    """Line coverage for one source file."""

    rel_path: str
    module: str
    percent: float


@dataclass(frozen=True)
class CoverageIssue:
    """One regression finding."""

    kind: str
    message: str


def module_from_rel_path(rel_path: str) -> str:
    """Map ``app/foo.py`` or ``core/foo.py`` to dotted module name."""
    path = rel_path.replace("\\", "/")
    if path.endswith(".py"):
        path = path[:-3]
    return path.replace("/", ".")


def normalize_app_rel(rel_path: str, *, monorepo_prefix: str = "") -> str:
    """Strip monorepo git prefix from a repo-relative app path."""
    rel = rel_path.replace("\\", "/").lstrip("/")
    prefix = monorepo_prefix.rstrip("/")
    if prefix and rel.startswith(f"{prefix}/"):
        rel = rel[len(prefix) + 1 :]
    return rel


def parse_module_coverage(
    coverage_json: dict[str, Any],
    *,
    repo_root: Path | None = None,
    monorepo_prefix: str = "",
) -> dict[str, ModuleCoverage]:
    """Index pytest-cov JSON by repo-relative source path."""
    out: dict[str, ModuleCoverage] = {}
    root = repo_root.resolve() if repo_root else None
    prefix = monorepo_prefix.rstrip("/")

    for key, payload in (coverage_json.get("files") or {}).items():
        key_norm = str(key).replace("\\", "/")
        if root is not None:
            try:
                rel_path = Path(key_norm).resolve().relative_to(root).as_posix()
            except ValueError:
                if prefix and f"/{prefix}/" in key_norm:
                    rel_path = key_norm.split(f"/{prefix}/", 1)[1]
                elif prefix and key_norm.startswith(f"{prefix}/"):
                    rel_path = key_norm[len(prefix) + 1 :]
                else:
                    rel_path = key_norm.split("/")[-1]
        else:
            if prefix and f"/{prefix}/" in key_norm:
                rel_path = key_norm.split(f"/{prefix}/", 1)[1]
            elif prefix and key_norm.startswith(f"{prefix}/"):
                rel_path = key_norm[len(prefix) + 1 :]
            else:
                rel_path = key_norm

        rel_path = normalize_app_rel(rel_path, monorepo_prefix="")
        summary = payload.get("summary") or {}
        percent = float(summary.get("percent_covered", 0.0))
        module = module_from_rel_path(rel_path)
        out[rel_path] = ModuleCoverage(rel_path=rel_path, module=module, percent=percent)
    return out


def load_baseline(path: Path) -> dict[str, float]:
    """Load ``scripts/coverage-baseline.json`` module percentages."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    modules = data.get("modules") or {}
    return {str(k): float(v) for k, v in modules.items()}


def git_file_change_status(git_root: Path, base_ref: str, repo_rel: str) -> str:
    """Return git name-status code for a path vs ``base_ref...HEAD`` (A/M/D or empty)."""
    if not base_ref:
        return ""
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(git_root),
                "diff",
                "--name-status",
                f"{base_ref}...HEAD",
                "--",
                repo_rel,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    for line in (proc.stdout or "").splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2 and parts[1].strip() == repo_rel:
            return parts[0].strip()[:1]
    proc2 = subprocess.run(
        ["git", "-C", str(git_root), "ls-files", "--others", "--exclude-standard", repo_rel],
        check=False,
        capture_output=True,
        text=True,
    )
    if (proc2.stdout or "").strip():
        return "A"
    return ""


def repo_rel_for_git(rel_path: str, layout: str, monorepo_prefix: str) -> str:
    """Normalize app-relative path to git path (``bot/core/x.py`` in monorepo)."""
    rel = normalize_app_rel(rel_path, monorepo_prefix="")
    prefix = monorepo_prefix.rstrip("/")
    if layout == "monorepo" and prefix:
        if rel.startswith(f"{prefix}/"):
            return rel
        return f"{prefix}/{rel}"
    return rel


def check_module_regression(
    *,
    app_files: list[str],
    coverage_by_path: dict[str, ModuleCoverage],
    baseline: dict[str, float],
    git_root: Path,
    base_ref: str,
    layout: str,
    monorepo_prefix: str,
    min_new: float,
    max_drop: float,
) -> list[CoverageIssue]:
    """Compare touched modules to baseline and minimums for new modules."""
    issues: list[CoverageIssue] = []
    for rel in app_files:
        rel = normalize_app_rel(rel, monorepo_prefix=monorepo_prefix)
        cov = coverage_by_path.get(rel)
        if cov is None:
            issues.append(
                CoverageIssue(
                    kind="missing",
                    message=f"{rel}: no coverage data (module not measured by pytest-cov)",
                )
            )
            continue

        repo_rel = repo_rel_for_git(rel, layout, monorepo_prefix)
        status = git_file_change_status(git_root, base_ref, repo_rel)
        base_pct = baseline.get(cov.module)

        if status == "A":
            if cov.percent + 1e-6 < min_new:
                issues.append(
                    CoverageIssue(
                        kind="new_module",
                        message=(
                            f"{rel}: {cov.percent:.1f}% covered "
                            f"(new module minimum {min_new:.1f}%)"
                        ),
                    )
                )
            continue

        if base_pct is None:
            continue

        if cov.percent + max_drop + 1e-6 < base_pct:
            issues.append(
                CoverageIssue(
                    kind="regression",
                    message=(
                        f"{rel}: {cov.percent:.1f}% covered "
                        f"(baseline {base_pct:.1f}%, max drop {max_drop:.1f}%)"
                    ),
                )
            )
    return issues


def run_diff_cover(
    *,
    repo_root: Path,
    coverage_xml: Path,
    compare_ref: str,
    fail_under: float,
) -> tuple[int, str]:
    """Run diff-cover on changed lines vs ``compare_ref``."""
    if not coverage_xml.is_file():
        return 0, "diff-cover skipped: coverage.xml missing"
    if not compare_ref:
        return 0, "diff-cover skipped: no compare ref"
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "diff_cover.diff_cover_tool",
                str(coverage_xml),
                f"--compare-branch={compare_ref}",
                f"--fail-under={fail_under}",
            ],
            check=False,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return 0, f"diff-cover skipped: {exc}"
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def format_report(
    module_issues: list[CoverageIssue],
    diff_cover_rc: int,
    diff_cover_output: str,
) -> str:
    """Human-readable gate report block."""
    lines = ["=== COVERAGE REGRESSION ==="]
    if module_issues:
        for issue in module_issues:
            lines.append(f"{issue.kind.upper()}: {issue.message}")
    else:
        lines.append("module baseline: OK (touched modules)")

    if diff_cover_output:
        lines.append("")
        lines.append("--- changed lines (diff-cover) ---")
        lines.append(diff_cover_output)
    if diff_cover_rc != 0:
        lines.append("")
        lines.append(
            f"CHANGED_LINES: FAIL (require covered changed lines; diff-cover exit {diff_cover_rc})"
        )
    elif diff_cover_output and "skipped" not in diff_cover_output.lower():
        lines.append("")
        lines.append("CHANGED_LINES: OK")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry for quality gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-json", type=Path, required=True)
    parser.add_argument("--coverage-xml", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, required=True)
    parser.add_argument("--monorepo-prefix", default="")
    parser.add_argument("--base-ref", default="")
    parser.add_argument("--layout", choices=("standalone", "monorepo"), default="standalone")
    parser.add_argument("--min-new", type=float, default=80.0)
    parser.add_argument("--max-drop", type=float, default=0.0)
    parser.add_argument("--diff-cover-fail-under", type=float, default=90.0)
    parser.add_argument("--app-file", action="append", default=[], dest="app_files")
    # Back-compat alias
    parser.add_argument("--bot-root", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root
    if args.bot_root is not None:
        repo_root = args.bot_root

    if not args.app_files:
        print("coverage-regression: no app files to check", file=sys.stderr)
        return 0

    if not args.coverage_json.is_file():
        print(f"coverage-regression: missing {args.coverage_json}", file=sys.stderr)
        return 1

    coverage_json = json.loads(args.coverage_json.read_text(encoding="utf-8"))
    coverage_by_path = parse_module_coverage(
        coverage_json,
        repo_root=repo_root,
        monorepo_prefix=args.monorepo_prefix,
    )
    baseline = load_baseline(args.baseline)

    module_issues = check_module_regression(
        app_files=args.app_files,
        coverage_by_path=coverage_by_path,
        baseline=baseline,
        git_root=args.git_root,
        base_ref=args.base_ref,
        layout=args.layout,
        monorepo_prefix=args.monorepo_prefix,
        min_new=args.min_new,
        max_drop=args.max_drop,
    )

    diff_rc, diff_out = run_diff_cover(
        repo_root=repo_root,
        coverage_xml=args.coverage_xml,
        compare_ref=args.base_ref,
        fail_under=args.diff_cover_fail_under,
    )

    print(format_report(module_issues, diff_rc, diff_out))

    if module_issues or diff_rc != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
