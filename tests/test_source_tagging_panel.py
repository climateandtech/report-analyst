import pytest
from streamlit.testing.v1 import AppTest

from report_analyst.core.cache_manager import CacheManager
from report_analyst.models.taxonomy import TaxonomyConcept, TaxonomyOption

SOURCE = {"id": "source-1", "document_id": "document-hash", "page": 14, "selected_text": "Scope 1 emissions were 1240 t"}


def concept(kind, data_type, label, options=()):
    return TaxonomyConcept(
        name=f"esrs:{label.replace(' ', '')}",
        label=label,
        kind=kind,
        data_type=data_type,
        period_type="duration",
        options=list(options),
    )


EMISSIONS = concept("number", "dtr-types:ghgEmissionsItemType", "Gross scope 1 GHG emissions")
POLICY = concept("narrative", "dtr-types:textBlockItemType", "Description of climate policy")
CONSOLIDATED = concept("yes/no", "xbrli:booleanItemType", "Prepared on a consolidated basis")
GROUPS = concept(
    "menu",
    "enum2:enumerationSetItemType",
    "Stakeholder groups",
    [
        TaxonomyOption(name="esrs:OwnWorkforceMember", label="Own workforce"),
        TaxonomyOption(name="esrs:WorkersMember", label="Workers"),
    ],
)


def form(concept, sources, database):
    import streamlit as st

    from report_analyst.core.cache_manager import CacheManager
    from report_analyst.ui.source_tagging import display_source_tagging, with_tags

    # Counts runs, so a test can see that saving reruns the page.
    st.session_state["runs"] = st.session_state.get("runs", 0) + 1
    # Like the viewer page, the sources come with their saved tags.
    cache_manager = CacheManager(database)
    sources = with_tags(sources, cache_manager.get_source_tags("document-hash"), {concept.name: concept})
    display_source_tagging(concept, sources, cache_manager)


@pytest.fixture
def database(tmp_path):
    return str(tmp_path / "tags.db")


def run_form(concept, database, sources=(SOURCE,)):
    app = AppTest.from_function(form, kwargs={"concept": concept, "sources": list(sources), "database": database})
    app.run()
    assert not app.exception
    return app


def save(app):
    app.button[0].click().run()
    assert not app.exception
    return app


def saved(database):
    return [
        (tag.concept, tag.value, tag.unit, tag.decimals) for tag in CacheManager(database).get_source_tags("document-hash")
    ]


def test_form_asks_for_a_saved_source_first(database):
    app = run_form(EMISSIONS, database, sources=[])

    assert "Save a source in the viewer first" in app.info[0].value
    assert not app.button


def test_form_saves_a_number_with_its_unit(database):
    app = run_form(EMISSIONS, database)

    app.text_input[0].input("1240")
    app.selectbox[1].select("ktCO2e")
    app.number_input[0].set_value(1)
    save(app)

    assert saved(database) == [("esrs:Grossscope1GHGemissions", "1240", "ktCO2e", 1)]
    assert "Gross scope 1 GHG emissions: 1240 ktCO2e" in app.markdown[-1].value


def test_form_shows_why_a_value_is_wrong_and_saves_nothing(database):
    app = run_form(EMISSIONS, database)

    app.text_input[0].input("1,240")
    save(app)

    assert "Enter a number" in app.error[0].value
    assert saved(database) == []


def test_form_starts_a_narrative_with_the_selected_text(database):
    save(run_form(POLICY, database))

    assert saved(database) == [("esrs:Descriptionofclimatepolicy", "Scope 1 emissions were 1240 t", None, None)]


def test_form_saves_yes_or_no(database):
    app = run_form(CONSOLIDATED, database)

    app.radio[0].set_value("No")
    save(app)

    assert saved(database) == [("esrs:Preparedonaconsolidatedbasis", "false", None, None)]


def test_form_saves_several_options_of_a_set_menu(database):
    app = run_form(GROUPS, database)

    app.multiselect[0].select("esrs:OwnWorkforceMember").select("esrs:WorkersMember")
    save(app)

    assert saved(database) == [("esrs:Stakeholdergroups", "esrs:OwnWorkforceMember esrs:WorkersMember", None, None)]
    assert "Stakeholder groups: Own workforce, Workers" in app.markdown[-1].value


def test_form_lists_only_the_selected_sources_tags(database):
    second = {**SOURCE, "id": "source-2", "page": 15, "selected_text": "Scope 2 emissions"}
    app = run_form(EMISSIONS, database, sources=[SOURCE, second])
    app.text_input[0].input("1240")
    save(app)

    app.selectbox(key="tag_source").select("source-2").run()

    assert not any("1240" in markdown.value for markdown in app.markdown)


def test_form_falls_back_to_the_first_source_when_the_selected_one_is_removed(database):
    second = {**SOURCE, "id": "source-2", "page": 15, "selected_text": "Scope 2 emissions"}
    app = run_form(POLICY, database, sources=[SOURCE, second])
    app.selectbox(key="tag_source").select("source-2").run()

    app.kwargs["sources"] = [SOURCE]
    app.run()

    assert not app.exception
    assert app.selectbox(key="tag_source").value == "source-1"


def test_saving_reruns_the_page_so_the_viewer_shows_the_tag(database):
    app = run_form(POLICY, database)

    save(app)
    assert app.session_state["runs"] == 3

    app.text_area[0].input(" ")
    save(app)
    assert app.session_state["runs"] == 4
