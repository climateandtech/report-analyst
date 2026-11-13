"""The form for tagging a saved PDF source with an ESRS concept and its value."""

import logging
from typing import Any

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from report_analyst.core.tagging import (
    PERCENT,
    PURE,
    SET_MENU,
    YEAR,
    InvalidTagError,
    create_tag,
    data_type,
    unit_choices,
)
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import TaxonomyConcept

logger = logging.getLogger(__name__)

SHOWN_LENGTH = 80


def display_source_tagging(concept: TaxonomyConcept, sources: list[dict], cache_manager: Any) -> None:
    """Tag a saved source with the concept. Each source comes with its tags, as made by `with_tags`."""
    st.markdown("**Tag a source**")
    if not sources:
        st.info("Save a source in the viewer first: select text in the PDF, then choose Add evidence.")
        return

    by_id = {source["id"]: source for source in sources}
    names = {
        source["id"]: f"{index} \N{MIDDLE DOT} Page {source['page']} \N{MIDDLE DOT} {_short(source['selected_text'])}"
        for index, source in enumerate(sources, 1)
    }
    source = by_id[st.selectbox("Source", list(by_id), format_func=names.get, key="tag_source")]
    # The concept and source are part of each key, so a value entered for one is not kept for another.
    key = f"tag_value_{concept.name}_{source['id']}"
    with st.form(f"tag_{concept.name}"):
        if concept.kind == "number":
            entered, unit, decimals = _number_inputs(concept, key)
        else:
            entered, unit, decimals = _value_input(concept, source, key), None, None
        submitted = st.form_submit_button("Save tag")
    if submitted:
        _save(concept, source, entered, unit, decimals, cache_manager)

    if source["tags"]:
        st.markdown("Tags on this source  \n" + "\n".join(f"- {tag['text']}" for tag in source["tags"]))


def _value_input(concept: TaxonomyConcept, source: dict, key: str) -> Any:
    if concept.kind == "narrative":
        return st.text_area("Value", value=source["selected_text"], key=key)
    if concept.kind == "yes/no":
        return st.radio("Value", ["Yes", "No"], horizontal=True, key=key) == "Yes"
    if concept.kind == "menu" and concept.options:
        names = [option.name for option in concept.options]
        option_labels = {option.name: option.label for option in concept.options}
        if data_type(concept) == SET_MENU:
            return st.multiselect("Value", names, format_func=option_labels.get, key=key)
        return st.selectbox("Value", names, format_func=option_labels.get, index=None, key=key)
    if data_type(concept) == YEAR:
        # XBRL years have four digits.
        return st.number_input("Year", min_value=1000, max_value=9999, value=None, step=1, key=key)
    if concept.kind == "date":
        return st.date_input("Value", value=None, key=key)
    return st.text_input("Code" if concept.kind == "menu" else "Value", key=key)


def _number_inputs(concept: TaxonomyConcept, key: str) -> tuple[str, str | None, int]:
    value_column, unit_column, decimals_column = st.columns(3)
    units = unit_choices(concept)
    value = value_column.text_input(
        "Value in %" if data_type(concept) == PERCENT else "Value", placeholder="For example 1240", key=key
    )
    if units == [PURE]:
        unit = None
    elif units:
        unit = unit_column.selectbox("Unit", units, key=f"{key}_unit")
    else:
        unit = unit_column.text_input("Currency", placeholder="For example EUR", key=f"{key}_currency")
    decimals = decimals_column.number_input(
        "Decimal places",
        value=0,
        step=1,
        help="How many decimal places the number in the report has. Use -3 if it is rounded to thousands.",
        key=f"{key}_decimals",
    )
    return value, unit, int(decimals)


def _save(
    concept: TaxonomyConcept, source: dict, entered: Any, unit: str | None, decimals: int | None, cache_manager: Any
) -> None:
    try:
        cache_manager.save_source_tag(create_tag(concept, source, entered, unit, decimals))
    except InvalidTagError as error:
        st.error(str(error))
    except SQLAlchemyError:
        logger.error(f"Could not save a tag for {concept.name} on source {source['id']}", exc_info=True)
        st.error("Could not save this tag. Try again.")
    else:
        # The viewer above the form was already drawn, so it shows the new tag after a rerun.
        st.rerun()


def with_tags(sources: list[dict], tags: list[SourceTag], concepts: dict[str, TaxonomyConcept]) -> list[dict]:
    """Give each saved source its tags as {id, text}, for the viewer's list and the form."""
    return [
        {
            **source,
            "tags": [
                {"id": tag.id, "text": _tag_text(tag, concepts.get(tag.concept))}
                for tag in tags
                if tag.source_id == source["id"]
            ],
        }
        for source in sources
    ]


def _tag_text(tag: SourceTag, concept: TaxonomyConcept | None) -> str:
    """A tag as people read it, such as "Gross scope 1 GHG emissions: 1240 tCO2e".

    Without its concept, for example when the taxonomy is not set up, the concept name is shown instead.
    """
    if concept and concept.options:
        option_labels = {option.name: option.label for option in concept.options}
        value = ", ".join(option_labels.get(name, name) for name in tag.value.split())
    else:
        value = _short(tag.value)
    unit = f" {tag.unit}" if tag.unit and tag.unit != PURE else ""
    return f"{concept.label if concept else tag.concept}: {value}{unit}"


def _short(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= SHOWN_LENGTH else f"{text[: SHOWN_LENGTH - 1]}\N{HORIZONTAL ELLIPSIS}"
