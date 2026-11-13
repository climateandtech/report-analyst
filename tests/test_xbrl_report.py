from datetime import date

from defusedxml.ElementTree import fromstring

from report_analyst.core.xbrl_report import xbrl_report
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import Taxonomy, TaxonomyConcept, TaxonomyOption

NAMESPACE = "https://example.org/esrs"
XBRLI = "{http://www.xbrl.org/2003/instance}"
LINK = "{http://www.xbrl.org/2003/linkbase}"
XLINK = "{http://www.w3.org/1999/xlink}"


def concept(name, kind, data_type, period_type="duration", options=()):
    return TaxonomyConcept(
        name=f"esrs:{name}", label=name, kind=kind, data_type=data_type, period_type=period_type, options=list(options)
    )


TAXONOMY = Taxonomy(
    identifier="https://example.org/build",
    name="Sample ESRS Taxonomy",
    version="2026-08-30",
    entry_point="https://example.org/esrs.xsd",
    namespaces={"esrs": NAMESPACE},
    concepts=[
        concept("Scope1", "number", "dtr-types:ghgEmissionsItemType"),
        concept("Revenue", "number", "xbrli:monetaryItemType"),
        concept("Share", "number", "dtr-types:percentItemType"),
        concept("Groups", "menu", "enum2:enumerationSetItemType", options=[TaxonomyOption(name="esrs:A", label="A")]),
        concept("Policy", "narrative", "dtr-types:textBlockItemType"),
        concept("LastUpdate", "date", "xbrli:dateItemType", period_type="instant"),
    ],
)


def tag(id, name, value, unit=None, decimals=None):
    return SourceTag(
        id=id,
        source_id="source-1",
        document_id="document-hash",
        concept=f"esrs:{name}",
        value=value,
        unit=unit,
        decimals=decimals,
    )


TAGS = [
    tag("1a", "Scope1", "1240", "tCO2e", 0),
    tag("2b", "Revenue", "5000000", "EUR", -3),
    tag("3c", "Share", "0.25", "pure", 2),
    tag("4d", "Groups", "esrs:A esrs:B"),
    tag("5e", "Policy", 'Covers <all> sites & "offices"'),
    tag("6f", "LastUpdate", "2025-11-30"),
]


def report():
    return fromstring(xbrl_report(TAGS, TAXONOMY, "529900T8BM49AURSDO55", date(2025, 1, 1), date(2025, 12, 31)))


def facts(root):
    return {fact.get("id"): fact for fact in root if fact.tag.startswith(f"{{{NAMESPACE}}}")}


def test_report_links_to_the_taxonomy_entry_point():
    assert report().find(f"{LINK}schemaRef").get(f"{XLINK}href") == "https://example.org/esrs.xsd"


def test_report_has_the_company_and_a_context_per_period_type():
    contexts = {context.get("id"): context for context in report().iter(f"{XBRLI}context")}

    assert {context.findtext(f".//{XBRLI}identifier") for context in contexts.values()} == {"529900T8BM49AURSDO55"}
    assert contexts["duration"].findtext(f".//{XBRLI}startDate") == "2025-01-01"
    assert contexts["duration"].findtext(f".//{XBRLI}endDate") == "2025-12-31"
    assert contexts["instant"].findtext(f".//{XBRLI}instant") == "2025-12-31"


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


def test_text_is_escaped():
    assert facts(report())["tag-5e"].text == 'Covers <all> sites & "offices"'
