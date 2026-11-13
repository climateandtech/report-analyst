"""The ESRS concepts panel, for finding the concept that fits a saved source."""

import os
from pathlib import Path
from typing import Any, get_args

import pandas as pd
import streamlit as st

from report_analyst.core.concept_search import search_concepts, standards
from report_analyst.core.esrs_taxonomy import TAXONOMY_PATH_ENV, TaxonomyUnavailableError, load_esrs_taxonomy
from report_analyst.models.taxonomy import ConceptKind, Taxonomy, TaxonomyConcept
from report_analyst.ui.source_tagging import display_source_tagging

ALL = "All"


@st.cache_resource(show_spinner="Loading the ESRS taxonomy...")
def _taxonomy(path: str, modified: float | None) -> Taxonomy:
    # The modified time is part of the cache key, so a replaced package loads again.
    return load_esrs_taxonomy(path)


def display_concept_search(sources: list[dict], cache_manager: Any) -> None:
    with st.expander("ESRS concepts", expanded=False):
        path = os.getenv(TAXONOMY_PATH_ENV, "")
        modified = Path(path).stat().st_mtime if path and Path(path).exists() else None
        try:
            taxonomy = _taxonomy(path, modified)
        except TaxonomyUnavailableError as error:
            st.info(f"ESRS concepts are not available. {error}")
            return

        query = st.text_input("Search", placeholder="For example scope 1, E1-8 or ESRS26_E1-8_01", key="concept_search_query")
        standard_column, kind_column = st.columns(2)
        standard = standard_column.selectbox("Standard", [ALL, *standards(taxonomy.concepts)], key="concept_search_standard")
        kind = kind_column.selectbox("Kind", [ALL, *get_args(ConceptKind)], key="concept_search_kind")
        found = search_concepts(taxonomy.concepts, query, None if standard == ALL else standard, None if kind == ALL else kind)
        st.caption(f"{len(found)} of {len(taxonomy.concepts)} concepts, {taxonomy.name} {taxonomy.version}")

        # No key, so a new result list also clears the selected row and it cannot point at another concept.
        results = st.dataframe(
            pd.DataFrame([_row(concept) for concept in found], columns=["Concept", "Reference", "Kind", "Group", "Link"]),
            column_config={"Link": st.column_config.LinkColumn("Knowledge Hub", display_text="Open")},
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        if not results.selection.rows:
            st.caption("Select a concept to tag a source with it.")
            return
        concept = found[results.selection.rows[0]]
        _show_details(concept)
        display_source_tagging(concept, sources, {known.name: known for known in taxonomy.concepts}, cache_manager)


def _row(concept: TaxonomyConcept) -> dict:
    return {
        "Group": concept.group,
        "Concept": concept.label,
        "Kind": concept.kind,
        "Reference": "; ".join(_reference(reference) for reference in concept.esrs_references),
        "Link": next((reference.url for reference in concept.esrs_references if reference.url), None),
    }


def _reference(reference) -> str:
    paragraph = " ".join(part for part in (reference.paragraph, reference.subparagraph, reference.clause) if part)
    return " \N{MIDDLE DOT} ".join(part for part in (reference.disclosure_requirement, paragraph) if part)


def _show_details(concept: TaxonomyConcept) -> None:
    st.markdown(f"**{concept.label}**")
    datapoints = ", ".join(reference.datapoint_id for reference in concept.esrs_references if reference.datapoint_id)
    st.markdown(
        f"Concept `{concept.name}`  \nData type `{concept.data_type}`, period `{concept.period_type}`"
        + (f"  \nDatapoint {datapoints}" if datapoints else "")
    )
    if concept.kind != "menu":
        return
    if not concept.options:
        st.caption(f"The options come from `{concept.options_domain}`, which is not in the taxonomy package.")
        return
    with st.container(height=200):
        st.markdown("\n".join(f"- {option.label}" for option in concept.options))
