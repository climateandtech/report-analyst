import pytest

from report_analyst.core.xbrl.inline_report import Mark, find_mark
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import TaxonomyConcept


def concept(kind, data_type):
    return TaxonomyConcept(name="esrs:Concept", label="Concept", kind=kind, data_type=data_type, period_type="duration")


EMISSIONS = concept("number", "dtr-types:ghgEmissionsItemType")
SHARE = concept("number", "dtr-types:percentItemType")
CONSOLIDATED = concept("yes/no", "xbrli:booleanItemType")
GROUPS = concept("menu", "enum2:enumerationSetItemType")
POLICY = concept("narrative", "dtr-types:textBlockItemType")
SUBSTANCE = concept("text", "xbrli:stringItemType")


def tag(value):
    return SourceTag(id="1", source_id="source-1", document_id="document-hash", concept="esrs:Concept", value=value)


def marked(value, concept, passage):
    start, end, ixt_format, scale = find_mark(tag(value), concept, passage)
    return passage[start:end], ixt_format, scale


def test_number_with_a_comma_for_thousands():
    assert find_mark(tag("1240"), EMISSIONS, "Emissions were 1,240 t") == Mark(15, 20, "ixt:num-dot-decimal")


def test_number_with_a_dot_for_thousands():
    assert marked("1240", EMISSIONS, "Emissionen: 1.240 t") == ("1.240", "ixt:num-comma-decimal", None)


@pytest.mark.parametrize("passage", ["1 240 t", "1\xa0240 t"])
def test_number_with_a_space_for_thousands(passage):
    assert marked("1240", EMISSIONS, passage) == (passage[:5], "ixt:num-dot-decimal", None)


def test_number_with_decimals_after_a_comma():
    assert marked("1240.5", EMISSIONS, "1.240,5 t") == ("1.240,5", "ixt:num-comma-decimal", None)


def test_number_inside_a_longer_number_is_not_found():
    assert find_mark(tag("1240"), EMISSIONS, "11,240 t") is None


def test_number_inside_a_year_is_skipped():
    assert find_mark(tag("0"), EMISSIONS, "In 2024: 0 incidents") == Mark(9, 10, "ixt:num-dot-decimal")


@pytest.mark.parametrize("passage", ["25 % of staff", "25% of staff"])
def test_percent_is_found_as_shown(passage):
    assert marked("0.25", SHARE, passage) == ("25", "ixt:num-dot-decimal", -2)


def test_negative_number_is_found_without_its_sign():
    assert marked("-1240", EMISSIONS, "(1,240)") == ("1,240", "ixt:num-dot-decimal", None)


def test_number_not_in_the_passage():
    assert find_mark(tag("1240"), EMISSIONS, "no number here") is None


@pytest.mark.parametrize("value, ixt_format", [("true", "ixt:fixed-true"), ("false", "ixt:fixed-false")])
def test_yes_no_covers_the_whole_passage(value, ixt_format):
    passage = "Prepared on a consolidated basis."
    assert find_mark(tag(value), CONSOLIDATED, passage) == Mark(0, len(passage), ixt_format)


def test_menu_is_never_in_the_passage():
    assert find_mark(tag("esrs:OwnWorkforceMember"), GROUPS, "Our own workforce") is None


def test_narrative_equal_to_the_passage():
    passage = "We cut emissions by half."
    assert find_mark(tag(passage), POLICY, passage) == Mark(0, len(passage))


def test_text_inside_the_passage():
    assert marked("lead", SUBSTANCE, "It contains lead.") == ("lead", None, None)


def test_text_not_in_the_passage():
    assert find_mark(tag("mercury"), SUBSTANCE, "It contains lead.") is None
