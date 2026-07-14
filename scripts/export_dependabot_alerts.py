#!/usr/bin/env python3

import csv
import json
import logging
import subprocess
import sys
from pathlib import Path
logger = logging.getLogger(__name__)


def run_gh_api(owner: str, repo: str) -> list[dict]:
    """Retrieve all Dependabot alerts for a GitHub repository."""

    # Build the GitHub CLI command for the Dependabot Alerts API
    # --paginate requests all result pages instead of only the first page
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
    # Read repository information from command-line arguments.
    # Fall back to the default repository when no arguments are provided.
    owner = sys.argv[1] if len(sys.argv) > 1 else "climateandtech"
    print(sys.argv)
    repo = sys.argv[2] if len(sys.argv) > 2 else "report-analyst"

    # Use the third command-line argument as the output path.
    # If it is missing, save the CSV in the current directory.
    output_path = Path(sys.argv[3] if len(sys.argv) > 3 else "../report-analyst/data/dependabot_alerts/dependabot_alerts.csv")

    # Retrieve all Dependabot alerts from the selected repository.
    alerts = run_gh_api(owner, repo)

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