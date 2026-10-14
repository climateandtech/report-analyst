"""The published docs site lists real pages and can render its API reference."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_mkdocs_nav_pages_exist():
    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text())
    docs_dir = ROOT / config["docs_dir"]

    def pages(items):
        found = []
        for item in items:
            if isinstance(item, str):
                continue
            for value in item.values():
                if isinstance(value, str):
                    found.append(value)
                else:
                    found.extend(pages(value))
        return found

    listed = pages(config["nav"])
    assert listed
    local_pages = [page for page in listed if not page.startswith(("http://", "https://"))]
    missing = [page for page in local_pages if not (docs_dir / page).is_file()]
    assert missing == []
    mkdocs_text = (ROOT / "mkdocs.yml").read_text()
    assert "mkdocstrings:" in mkdocs_text
    assert "logo: assets/favicon.svg" in mkdocs_text
    assert "https://opensustainabilityanalyst.com/en" in mkdocs_text
    assert (docs_dir / "assets/favicon.svg").is_file()
    assert "opensustainabilityanalyst.com" in (docs_dir / "index.md").read_text()

    reference_pages = [
        page for page in local_pages if page.startswith("reference/") and page != "reference/index.md"
    ]
    assert reference_pages
    unlabeled = [
        page
        for page in reference_pages
        if "snippets/core.md" not in (docs_dir / page).read_text()
        and "snippets/enterprise.md" not in (docs_dir / page).read_text()
    ]
    assert unlabeled == []
    assert "snippets/enterprise.md" in (docs_dir / "guides/chunk-highlighting.md").read_text()
