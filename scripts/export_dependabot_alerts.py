#!/usr/bin/env python3

import csv
import datetime
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "dependabot_alerts"


def get_repo_info() -> tuple[str, str]:
    """Retrieve the current GitHub owner and repository name using gh CLI."""
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "owner,name"],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    owner = data["owner"]["login"]
    repo = data["name"]
    return owner, repo


def run_gh_api(owner: str, repo: str) -> list[dict]:
    """Retrieve all Dependabot alerts for a GitHub repository."""

    # Build the GitHub CLI command for the Dependabot Alerts API
    # --paginate requests all result pages instead of only the first page
    # and joins them into a single JSON array
    command = [
        "gh",
        "api",
        f"repos/{owner}/{repo}/dependabot/alerts",
        "--paginate",
    ]

    # Execute the GitHub CLI command as a subprocess.
    #
    # check=True:
    #   Raises an exception if the command exits with an error.
    # capture_output=True:
    #   Captures stdout and stderr instead of printing them to the terminal.
    # text=True:
    #   Returns the captured output as strings instead of bytes.
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    # Convert the JSON response returned by the GitHub API
    # into a Python list containing one dictionary per alert.
    return json.loads(result.stdout)


def main() -> None:
    # Retrieve all Dependabot alerts from the current repository
    try:
        owner, repo = get_repo_info()
        alerts = run_gh_api(owner, repo)
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"gh failed: {error.stderr.strip()}") from error

    # Transform the nested GitHub API response into flat dictionaries
    # that can be written directly as rows in a CSV file.
    rows = []

    for alert in alerts:
        # Extract nested objects from the alert.
        # Empty dictionaries prevent errors when optional fields are missing.
        advisory = alert.get("security_advisory", {})
        vulnerability = alert.get("security_vulnerability", {})
        dependency = alert.get("dependency", {})
        package = dependency.get("package", {})

        # first_patched_version can be null when no patched version exists.
        # Using `or {}` ensures that `.get()` can still be called safely.
        patched = vulnerability.get("first_patched_version") or {}

        # Select and flatten the relevant alert properties for the CSV output.
        # Missing values are replaced with empty strings.
        rows.append(
            {
                "number": alert.get("number", ""),
                "severity": advisory.get("severity", ""),
                "package": package.get("name", ""),
                "ecosystem": package.get("ecosystem", ""),
                "manifest": dependency.get("manifest_path", ""),
                "scope": dependency.get("scope", ""),
                "state": alert.get("state", ""),
                "ghsa_id": advisory.get("ghsa_id", ""),
                "cve_id": advisory.get("cve_id", ""),
                "summary": advisory.get("summary", ""),
                "vulnerable_range": vulnerability.get(
                    "vulnerable_version_range",
                    "",
                ),
                "patched_version": patched.get("identifier", ""),
                "created_at": alert.get("created_at", ""),
                "url": alert.get("html_url", ""),
            }
        )

    # Define the column names and their order in the generated CSV file.
    fieldnames = [
        "number",
        "severity",
        "package",
        "ecosystem",
        "manifest",
        "scope",
        "state",
        "ghsa_id",
        "cve_id",
        "summary",
        "vulnerable_range",
        "patched_version",
        "created_at",
        "url",
    ]

    date = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M")
    output_path = OUTPUT_DIR / f"{date}_dependabot_alerts.csv"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create or overwrite the CSV file.
    #
    # newline="" prevents additional blank lines on some operating systems.
    # UTF-8 ensures that special characters are written correctly.
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write the column names as the first CSV row.
        writer.writeheader()

        # Write all transformed Dependabot alerts to the CSV file.
        writer.writerows(rows)

    # Print a short confirmation including the number of exported alerts.
    print(f"Exported {len(rows)} alerts to {output_path}")


# Run main() only when this file is executed directly.
# It will not run automatically when the file is imported as a module.
if __name__ == "__main__":
    main()
