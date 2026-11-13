from datetime import date
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from report_analyst.core.arelle_check import XbrlProblem
from report_analyst.core.esrs_taxonomy import TaxonomyUnavailableError
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import Taxonomy, TaxonomyConcept

TAXONOMY = Taxonomy(
    identifier="https://example.org/build",
    name="Sample ESRS Taxonomy",
    version="2026-08-30",
    entry_point="https://example.org/esrs.xsd",
    namespaces={"esrs": "https://example.org/esrs"},
    concepts=[
        TaxonomyConcept(
            name="esrs:Consolidated",
            label="Prepared on a consolidated basis",
            kind="yes/no",
            data_type="xbrli:booleanItemType",
            period_type="duration",
        )
    ],
)
TAGS = [
    SourceTag(id=id, source_id="source-1", document_id="document-hash", concept=concept, value="true")
    for id, concept in [("1", "esrs:Consolidated"), ("2", "esrs:Consolidated"), ("3", "esrs:Removed")]
]
SOURCES = [
    {
        "id": "source-1",
        "tags": [
            {"id": "1", "text": "Prepared on a consolidated basis: true"},
            {"id": "2", "text": "Prepared on a consolidated basis: true"},
            {"id": "3", "text": "esrs:Removed: true"},
        ],
    }
]


def panel(tags, sources):
    from report_analyst.ui.xbrl_check import display_xbrl_check

    display_xbrl_check(tags, sources)


@pytest.fixture
def check(monkeypatch):
    monkeypatch.setenv("ESRS_TAXONOMY_PATH", "/packages/esrs")
    monkeypatch.setattr("report_analyst.ui.xbrl_check.current_taxonomy", lambda: TAXONOMY)
    check = Mock(return_value=[])
    monkeypatch.setattr("report_analyst.ui.xbrl_check.check_xbrl", check)
    return check


def run_panel(tags=TAGS, sources=SOURCES):
    app = AppTest.from_function(panel, kwargs={"tags": tags, "sources": sources})
    app.run()
    assert not app.exception
    return app


def submit(app, lei="529900T8BM49AURSDO55", start=date(2025, 1, 1), end=date(2025, 12, 31)):
    app.text_input[0].input(lei)
    app.date_input[0].set_value(start)
    app.date_input[1].set_value(end)
    app.button[0].click().run()
    assert not app.exception
    return app


def test_panel_asks_for_tags_first(check):
    app = run_panel(tags=[], sources=[])

    assert "Tag a source first" in app.info[0].value
    assert not app.button


def test_panel_explains_a_missing_taxonomy(monkeypatch):
    def unavailable():
        raise TaxonomyUnavailableError("Set ESRS_TAXONOMY_PATH.")

    monkeypatch.setattr("report_analyst.ui.xbrl_check.current_taxonomy", unavailable)

    app = run_panel()

    assert "Set ESRS_TAXONOMY_PATH." in app.info[0].value


def test_panel_needs_the_company_and_period(check):
    app = submit(run_panel(), lei=" ")

    assert app.error[0].value == "Enter the company LEI and the reporting period."
    check.assert_not_called()


def test_panel_needs_a_period_that_ends_after_it_starts(check):
    app = submit(run_panel(), start=date(2025, 12, 31), end=date(2025, 1, 1))

    assert app.error[0].value == "The period must end after it starts."
    check.assert_not_called()


def test_panel_checks_the_known_tags_and_shows_the_result(check):
    check.return_value = [
        XbrlProblem("2", "Element esrs:Consolidated type boolean value error: maybe"),
        XbrlProblem(None, "Could not load nace-codes.xsd"),
    ]

    app = submit(run_panel())

    report, package = check.call_args.args
    assert 'id="tag-1"' in report and 'id="tag-2"' in report and 'id="tag-3"' not in report
    assert package == "/packages/esrs"
    assert app.success[0].value == "1 of 2 tags make valid XBRL."
    assert "**Prepared on a consolidated basis: true**  \n  Element esrs:Consolidated type boolean" in app.error[0].value
    assert app.warning[0].value == "Tags whose concept is not in this taxonomy were left out: 1"
    assert app.caption[0].value.startswith("Problems in the ESRS package itself, not in your tags: 1")
