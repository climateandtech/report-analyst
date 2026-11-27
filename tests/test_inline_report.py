from datetime import date

import pytest
from defusedxml.ElementTree import fromstring

from report_analyst.core.xbrl.inline_report import Mark, find_mark, inline_report
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import Taxonomy, TaxonomyConcept, TaxonomyIdentifier, TaxonomyOption

NAMESPACE = "https://example.org/esrs"
XHTML = "{http://www.w3.org/1999/xhtml}"
IX = "{http://www.xbrl.org/2013/inlineXBRL}"
XBRLI = "{http://www.xbrl.org/2003/instance}"
XBRLDI = "{http://xbrl.org/2006/xbrldi}"


def concept(kind, data_type, name="Concept", label="Concept", options=(), identifier=None):
    return TaxonomyConcept(
        name=f"esrs:{name}",
        label=label,
        kind=kind,
        data_type=data_type,
        period_type="duration",
        options=list(options),
        identifier=identifier,
    )


EMISSIONS = concept("number", "dtr-types:ghgEmissionsItemType", "Scope1", "Gross scope 1 GHG emissions")
SHARE = concept("number", "dtr-types:percentItemType")
CONSOLIDATED = concept("yes/no", "xbrli:booleanItemType", "Consolidated")
GROUPS = concept("menu", "enum2:enumerationSetItemType", "Groups", options=[TaxonomyOption(name="esrs:A", label="A")])
POLICY = concept("narrative", "dtr-types:textBlockItemType", "Policy")
SUBSTANCE = concept("text", "xbrli:stringItemType")
POLICY_NAME = concept(
    "text",
    "xbrli:stringItemType",
    "PolicyName",
    identifier=TaxonomyIdentifier(dimension="esrs:PolicyAxis", label="Identifier of policy(ies)", element="esrs:TYP"),
)
TAXONOMY = Taxonomy(
    identifier="https://example.org/build",
    name="Sample ESRS Taxonomy",
    version="2026-08-30",
    entry_point="https://example.org/esrs.xsd",
    namespaces={"esrs": NAMESPACE},
    concepts=[EMISSIONS, CONSOLIDATED, GROUPS, POLICY, SUBSTANCE, POLICY_NAME],
)


def tag(value, id="1", concept="esrs:Concept", source_id="source-1", unit=None, decimals=None, identifier=None):
    return SourceTag(
        id=id,
        source_id=source_id,
        document_id="document-hash",
        concept=concept,
        value=value,
        unit=unit,
        decimals=decimals,
        identifier=identifier,
    )


def emissions(value, id="1", source_id="source-1"):
    return tag(value, id, "esrs:Scope1", source_id, "tCO2e", 0)


def source(text, id="source-1", page=1):
    return {"id": id, "page": page, "span_start": 0, "selected_text": text}


def report(tags, sources):
    """The parsed iXBRL report, which also checks it is well-formed, and the ids written below their passage."""
    xhtml, written_below = inline_report(tags, sources, TAXONOMY, "529900T8BM49AURSDO55", date(2025, 1, 1), date(2025, 12, 31))
    return fromstring(xhtml), written_below


def paragraphs(root):
    return root.find(f"{XHTML}body").findall(f"{XHTML}p")


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


def test_number_is_wrapped_in_its_passage():
    root, written_below = report([emissions("1240")], [source("Emissions were 1,240 t")])

    [fact] = root.iter(f"{IX}nonFraction")
    assert (fact.get("id"), fact.text, fact.get("format")) == ("tag-1", "1,240", "ixt:num-dot-decimal")
    assert (fact.get("name"), fact.get("unitRef"), fact.get("decimals")) == ("esrs:Scope1", "tCO2e", "0")
    assert written_below == []


def test_number_inside_a_narrative():
    passage = "Emissions were 1,240 t"
    root, written_below = report([emissions("1240"), tag(passage, "2", "esrs:Policy")], [source(passage)])

    [narrative] = root.iter(f"{IX}nonNumeric")
    assert narrative.get("id") == "tag-2"
    assert narrative.find(f"{IX}nonFraction").get("id") == "tag-1"
    assert written_below == []


def test_value_not_in_the_passage_is_written_below_it():
    root, written_below = report([emissions("999")], [source("Emissions were 1,240 t")])

    passage, line = paragraphs(root)
    assert "".join(passage.itertext()) == "Emissions were 1,240 t"
    assert "".join(line.itertext()) == "Gross scope 1 GHG emissions: 999 tCO2e"
    assert line.find(f"{IX}nonFraction").text == "999"
    assert written_below == ["1"]


def test_menu_is_written_below_its_passage():
    root, written_below = report([tag("esrs:A", concept="esrs:Groups")], [source("Group A is covered.")])

    assert paragraphs(root)[1].find(f"{IX}nonNumeric").text == f"{NAMESPACE}#A"
    assert written_below == ["1"]


def test_same_value_twice_on_one_passage():
    root, written_below = report([emissions("1240"), emissions("1240", "2")], [source("Emissions were 1,240 t")])

    assert [fact.get("id") for fact in paragraphs(root)[0].iter(f"{IX}nonFraction")] == ["tag-1"]
    assert written_below == ["2"]


def test_negative_number_has_a_sign():
    root, _ = report([emissions("-1240")], [source("Removals were (1,240) t")])

    [fact] = root.iter(f"{IX}nonFraction")
    assert (fact.text, fact.get("sign")) == ("1,240", "-")


def test_passage_text_is_escaped():
    passage = 'Sites & <offices>\n"worldwide"'
    root, _ = report([tag(passage, concept="esrs:Policy")], [source(passage)])

    assert "".join(paragraphs(root)[0].itertext()) == passage


@pytest.mark.parametrize(
    ("value", "concept", "escape"),
    [
        ("Covers all sites", "esrs:Policy", "true"),
        ("R&D", "esrs:Concept", "true"),
        ("Below <5 %", "esrs:Concept", "true"),
        ("Lead", "esrs:Concept", None),
    ],
    ids=["text block", "text with &", "text with <", "other text"],
)
def test_text_blocks_and_text_with_markup_characters_are_escaped(value, concept, escape):
    root, _ = report([tag(value, concept=concept)], [source(f"{value}.")])

    assert root.find(f".//{IX}nonNumeric").get("escape") == escape


def test_report_uses_transformation_registry_5():
    xhtml, _ = inline_report([], [], TAXONOMY, "529900T8BM49AURSDO55", date(2025, 1, 1), date(2025, 12, 31))

    # ESEF requires it from its 2025 rules on.
    assert 'xmlns:ixt="http://www.xbrl.org/inlineXBRL/transformation/2022-02-16"' in xhtml


def test_sources_follow_page_order():
    tags = [tag("true", "1", "esrs:Consolidated", "late"), tag("true", "2", "esrs:Consolidated", "early")]
    root, _ = report(tags, [source("On page 9.", "late", 9), source("On page 2.", "early", 2)])

    assert ["".join(p.itertext()) for p in paragraphs(root)] == ["On page 2.", "On page 9."]


def test_sources_without_tags_are_left_out():
    root, _ = report([emissions("1240")], [source("Emissions were 1,240 t"), source("No tags here.", "source-2")])

    assert ["".join(p.itertext()) for p in paragraphs(root)] == ["Emissions were 1,240 t"]


def test_report_links_to_the_taxonomy_and_holds_the_contexts_and_units():
    root, _ = report([emissions("1240")], [source("Emissions were 1,240 t")])

    header = root.find(f".//{IX}header")
    assert header.find(".//{http://www.xbrl.org/2003/linkbase}schemaRef") is not None
    assert {context.get("id") for context in header.iter("{http://www.xbrl.org/2003/instance}context")} == {
        "duration",
        "instant",
    }
    assert [unit.get("id") for unit in header.iter("{http://www.xbrl.org/2003/instance}unit")] == ["tCO2e"]


def test_inline_report_has_the_identifier_context():
    root, _ = report(
        [tag("Climate policy", concept="esrs:PolicyName", identifier="P1")], [source("Our Climate policy covers all sites.")]
    )

    context = root.find(f".//{XBRLI}context[@id='duration-1']")
    assert context.find(f".//{XBRLDI}typedMember/{{{NAMESPACE}}}TYP").text == "P1"
    assert root.find(f".//{IX}nonNumeric").get("contextRef") == "duration-1"
