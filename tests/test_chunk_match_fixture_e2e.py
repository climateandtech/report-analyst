"""Opt-in live test for regenerating the CT REIT embedding fixture."""

import os
from argparse import Namespace
from pathlib import Path

import pytest
from scripts.generate_chunk_match_fixture import build_fixture


@pytest.mark.e2e
@pytest.mark.skipif(
    os.getenv("CHUNK_MATCH_FIXTURE_E2E") != "1",
    reason="Set CHUNK_MATCH_FIXTURE_E2E=1 to call OpenAI and regenerate candidates",
)
def test_openai_maps_both_real_report_chunk_sizes():
    args = Namespace(
        data_dir=Path("notebooks/data"),
        output=Path("tests/fixtures/ct_reit_chunk_matching.json"),
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"),
        top_candidates=2,
    )

    fixture = build_fixture(args)

    assert set(fixture["chunks"]) == {"200", "400"}
