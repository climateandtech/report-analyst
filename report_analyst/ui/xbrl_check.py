"""The panel that checks with Arelle that a report's tags make valid XBRL, and offers them as iXBRL and XBRL files."""

import os

import streamlit as st

from report_analyst.core.xbrl.arelle_check import XbrlProblem, check_xbrl
from report_analyst.core.xbrl.esrs_taxonomy import TAXONOMY_PATH_ENV, TaxonomyUnavailableError
from report_analyst.core.xbrl.inline_report import inline_report
from report_analyst.core.xbrl.xbrl_report import xbrl_report
from report_analyst.models.source_tag import SourceTag
from report_analyst.ui.concept_search import current_taxonomy


def display_xbrl_check(tags: list[SourceTag], sources: list[dict], report_name: str) -> None:
    """Check the tags and offer both files, named after the report.

    `sources` are the saved sources with their tags, as made by `with_tags`.
    """
    with st.expander("Check with Arelle", expanded=False):
        if not tags:
            st.info("Tag a source first. Then check here that the tags make valid XBRL.")
            return
        try:
            taxonomy = current_taxonomy()
        except TaxonomyUnavailableError as error:
            st.info(f"The check needs the ESRS taxonomy. {error}")
            return

        with st.form("xbrl_check"):
            lei_column, start_column, end_column = st.columns(3)
            lei = lei_column.text_input("Company LEI", help="The company's 20-character Legal Entity Identifier.")
            start = start_column.date_input("Period from", value=None)
            end = end_column.date_input("Period to", value=None)
            submitted = st.form_submit_button("Check")
        if not submitted:
            return
        if not (lei.strip() and start and end):
            st.error("Enter the company LEI and the reporting period.")
            return
        if end < start:
            st.error("The period must end after it starts.")
            return

        concepts = {concept.name for concept in taxonomy.concepts}
        known = [tag for tag in tags if tag.concept in concepts]
        lei = lei.strip()
        ixbrl_file, written_below = inline_report(known, sources, taxonomy, lei, start, end)
        with st.spinner("Checking with Arelle..."):
            problems = check_xbrl(ixbrl_file, os.environ[TAXONOMY_PATH_ENV])
        _show(problems, known, len(tags) - len(known), sources, written_below)
        # A download leaves the page as it is, so the check result stays.
        ixbrl_column, xbrl_column = st.columns(2)
        ixbrl_column.download_button(
            "Download iXBRL", ixbrl_file, f"{report_name}.xhtml", "application/xhtml+xml", on_click="ignore"
        )
        xbrl_column.download_button(
            "Download XBRL",
            xbrl_report(known, taxonomy, lei, start, end),
            f"{report_name}.xbrl",
            "application/xml",
            on_click="ignore",
        )


def _show(
    problems: list[XbrlProblem], known: list[SourceTag], left_out: int, sources: list[dict], written_below: list[str]
) -> None:
    texts = {tag["id"]: tag["text"] for source in sources for tag in source["tags"]}
    tag_problems = [problem for problem in problems if problem.tag_id]
    valid = len(known) - len({problem.tag_id for problem in tag_problems})
    if valid:
        st.success(f"{valid} of {len(known)} tags make valid XBRL.")
    if tag_problems:
        st.error(
            "\n".join(f"- **{texts.get(problem.tag_id, problem.tag_id)}**  \n  {problem.message}" for problem in tag_problems)
        )
    if written_below:
        st.info(
            "Written below their passage, because the value is not in its text:\n"
            + "\n".join(f"- {texts.get(tag_id, tag_id)}" for tag_id in written_below)
        )
    if left_out:
        st.warning(f"Tags whose concept is not in this taxonomy were left out: {left_out}")
    package_problems = [problem.message for problem in problems if not problem.tag_id]
    if package_problems:
        st.caption(
            f"Arelle also noted problems in the ESRS taxonomy package itself ({len(package_problems)}). "
            "They are not about your tags."
        )
        # A popover opens without a rerun, so the check result stays on the page.
        with st.popover("Details"):
            for message in package_problems:
                st.caption(message)
