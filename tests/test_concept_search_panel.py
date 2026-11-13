from streamlit.testing.v1 import AppTest

from report_analyst.core.esrs_taxonomy import TAXONOMY_PATH_ENV
from report_analyst.models.taxonomy import Taxonomy, TaxonomyConcept

TAXONOMY = Taxonomy(
    identifier="https://example.org/build",
    name="Sample ESRS Taxonomy",
    version="2026-08-30",
    concepts=[
        TaxonomyConcept(
            name=f"esrs:{name}",
            label=label,
            kind=kind,
            data_type="xbrli:stringItemType",
            period_type="duration",
            group="[210800] E1-8 Gross scope 1 and 2 GHG emissions",
        )
        for name, label, kind in [
            ("Scope1", "Gross scope 1 GHG emissions", "number"),
            ("PolicyTextBlock", "Description of climate policy", "narrative"),
            ("GasCovered", "Gas covered", "menu"),
        ]
    ],
)


def panel():
    from unittest.mock import Mock

    from report_analyst.ui.concept_search import display_concept_search

    display_concept_search([], Mock())


def run_panel():
    app = AppTest.from_function(panel)
    app.run()
    assert not app.exception
    return app


def labels(app):
    return list(app.dataframe[0].value["Concept"])


def test_panel_explains_how_to_set_up_the_taxonomy(monkeypatch):
    monkeypatch.delenv(TAXONOMY_PATH_ENV, raising=False)

    app = run_panel()

    assert TAXONOMY_PATH_ENV in app.info[0].value
    assert not app.dataframe


def loaded_panel(monkeypatch, tmp_path):
    # Each test gets its own path, so the cached taxonomy of another test is not reused.
    monkeypatch.setenv(TAXONOMY_PATH_ENV, str(tmp_path))
    monkeypatch.setattr("report_analyst.ui.concept_search.load_esrs_taxonomy", lambda path: TAXONOMY)
    return run_panel()


def test_panel_lists_all_concepts(monkeypatch, tmp_path):
    app = loaded_panel(monkeypatch, tmp_path)

    assert labels(app) == ["Gross scope 1 GHG emissions", "Description of climate policy", "Gas covered"]
    assert app.caption[0].value == "3 of 3 concepts, Sample ESRS Taxonomy 2026-08-30"
    assert app.caption[1].value == "Select a concept to tag a source with it."


def test_panel_searches_and_filters(monkeypatch, tmp_path):
    app = loaded_panel(monkeypatch, tmp_path)

    app.text_input(key="concept_search_query").input("policy").run()
    assert labels(app) == ["Description of climate policy"]

    app.text_input(key="concept_search_query").input("").run()
    app.selectbox(key="concept_search_kind").select("menu").run()
    assert labels(app) == ["Gas covered"]
