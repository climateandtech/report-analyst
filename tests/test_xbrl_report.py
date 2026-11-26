from datetime import date

import pytest
from defusedxml.ElementTree import fromstring

from report_analyst.core.xbrl.xbrl_report import xbrl_report
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import Taxonomy, TaxonomyConcept, TaxonomyIdentifier, TaxonomyOption

NAMESPACE = "https://example.org/esrs"
XBRLI = "{http://www.xbrl.org/2003/instance}"
LINK = "{http://www.xbrl.org/2003/linkbase}"
XLINK = "{http://www.w3.org/1999/xlink}"
XBRLDI = "{http://xbrl.org/2006/xbrldi}"


def concept(name, kind, data_type, period_type="duration", options=(), identifier=None):
    return TaxonomyConcept(
        name=f"esrs:{name}",
        label=name,
        kind=kind,
        data_type=data_type,
        period_type=period_type,
        options=list(options),
        identifier=identifier,
    )


TAXONOMY = Taxonomy(
    identifier="https://example.org/build",
    name="Sample ESRS Taxonomy",
    version="2026-08-30",
    entry_point="https://example.org/esrs.xsd",
    namespaces={"esrs": NAMESPACE},
    concepts=[
        concept("Substance", "text", "xbrli:stringItemType"),
        concept("Scope1", "number", "dtr-types:ghgEmissionsItemType"),
        concept("Revenue", "number", "xbrli:monetaryItemType"),
        concept("Share", "number", "dtr-types:percentItemType"),
        concept("Groups", "menu", "enum2:enumerationSetItemType", options=[TaxonomyOption(name="esrs:A", label="A")]),
        concept("Policy", "narrative", "dtr-types:textBlockItemType"),
        concept("LastUpdate", "date", "xbrli:dateItemType", period_type="instant"),
        concept(
            "PolicyName",
            "text",
            "xbrli:stringItemType",
            identifier=TaxonomyIdentifier(dimension="esrs:PolicyAxis", label="Identifier of policy(ies)", element="esrs:TYP"),
        ),
    ],
)


def tag(id, name, value, unit=None, decimals=None, identifier=None):
    return SourceTag(
        id=id,
        source_id="source-1",
        document_id="document-hash",
        concept=f"esrs:{name}",
        value=value,
        unit=unit,
        decimals=decimals,
        identifier=identifier,
    )


TAGS = [
    tag("1a", "Scope1", "1240", "tCO2e", 0),
    tag("2b", "Revenue", "5000000", "EUR", -3),
    tag("3c", "Share", "0.25", "pure", 2),
    tag("4d", "Groups", "esrs:A esrs:B"),
    tag("5e", "Policy", 'Covers <all> sites & "offices"'),
    tag("6f", "LastUpdate", "2025-11-30"),
]


def report(tags=TAGS):
    return fromstring(xbrl_report(tags, TAXONOMY, "529900T8BM49AURSDO55", date(2025, 1, 1), date(2025, 12, 31)))


def facts(root):
    return {fact.get("id"): fact for fact in root if fact.tag.startswith(f"{{{NAMESPACE}}}")}


def contexts(root):
    return {context.get("id"): context for context in root.iter(f"{XBRLI}context")}


def identifier_in(context):
    member = context.find(f"{XBRLI}scenario/{XBRLDI}typedMember")
    return member.get("dimension"), member.findtext(f"{{{NAMESPACE}}}TYP")


def test_report_links_to_the_taxonomy_entry_point():
    assert report().find(f"{LINK}schemaRef").get(f"{XLINK}href") == "https://example.org/esrs.xsd"


def test_report_has_the_company_and_a_context_per_period_type():
    found = contexts(report())

    assert {context.findtext(f".//{XBRLI}identifier") for context in found.values()} == {"529900T8BM49AURSDO55"}
    assert found["duration"].findtext(f".//{XBRLI}startDate") == "2025-01-01"
    assert found["duration"].findtext(f".//{XBRLI}endDate") == "2025-12-31"
    assert found["instant"].findtext(f".//{XBRLI}instant") == "2025-12-31"


def test_each_tag_is_a_fact_named_after_the_tag():
    found = facts(report())

    assert list(found) == ["tag-1a", "tag-2b", "tag-3c", "tag-4d", "tag-5e", "tag-6f"]
    assert found["tag-1a"].tag == f"{{{NAMESPACE}}}Scope1"
    assert [found[id].get("contextRef") for id in found] == ["duration"] * 5 + ["instant"]


def test_numbers_have_their_unit_and_decimals():
    root = report()
    found = facts(root)
    measures = {unit.get("id"): unit.findtext(f"{XBRLI}measure") for unit in root.iter(f"{XBRLI}unit")}

    assert [
        (found[id].text, found[id].get("unitRef"), found[id].get("decimals")) for id in ("tag-1a", "tag-2b", "tag-3c")
    ] == [
        ("1240", "tCO2e", "0"),
        ("5000000", "EUR", "-3"),
        ("0.25", "pure", "2"),
    ]
    assert measures == {"tCO2e": "utr:tCO2e", "EUR": "iso4217:EUR", "pure": "xbrli:pure"}


def test_menu_options_are_written_with_their_namespace():
    assert facts(report())["tag-4d"].text == f"{NAMESPACE}#A {NAMESPACE}#B"


def test_text_block_is_written_as_html():
    # Like in the iXBRL report, where a text block's value is the HTML of its passage.
    assert facts(report())["tag-5e"].text == 'Covers &lt;all&gt; sites &amp; "offices"'


@pytest.mark.parametrize(("value", "written"), [("R&D", "R&amp;D"), ("Lead", "Lead")], ids=["text with &", "other text"])
def test_text_with_markup_characters_is_written_as_html(value, written):
    assert facts(report([tag("7g", "Substance", value)]))["tag-7g"].text == written


def test_tag_with_an_identifier_gets_its_own_context():
    root = report([tag("7g", "PolicyName", "Climate policy", identifier="P1")])
    context = contexts(root)["duration-7g"]

    assert identifier_in(context) == ("esrs:PolicyAxis", "P1")
    assert context.findtext(f".//{XBRLI}identifier") == "529900T8BM49AURSDO55"
    assert context.findtext(f".//{XBRLI}startDate") == "2025-01-01"
    assert facts(root)["tag-7g"].get("contextRef") == "duration-7g"


def test_two_tags_with_the_same_identifier_get_a_context_each():
    root = report(
        [
            tag("7g", "PolicyName", "Climate policy", identifier="P1"),
            tag("8h", "PolicyName", "Climate and energy policy", identifier="P1"),
        ]
    )

    assert [facts(root)[id].get("contextRef") for id in ("tag-7g", "tag-8h")] == ["duration-7g", "duration-8h"]
    assert [identifier_in(contexts(root)[id]) for id in ("duration-7g", "duration-8h")] == [("esrs:PolicyAxis", "P1")] * 2


def test_identifier_is_escaped():
    root = report([tag("7g", "PolicyName", "Climate policy", identifier="P&1 <a>")])

    assert identifier_in(contexts(root)["duration-7g"]) == ("esrs:PolicyAxis", "P&1 <a>")


@pytest.mark.parametrize(
    "without_identifier",
    [tag("7g", "PolicyName", "Climate policy"), tag("7g", "Scope1", "1240", "tCO2e", 0, identifier="P1")],
    ids=["tag saved without its identifier", "concept that needs no identifier"],
)
def test_tag_without_an_identifier_its_concept_needs_uses_the_period_context(without_identifier):
    root = report([without_identifier])

    assert facts(root)["tag-7g"].get("contextRef") == "duration"
    assert list(contexts(root)) == ["duration", "instant"]
