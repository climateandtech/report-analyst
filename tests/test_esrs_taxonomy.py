import os
import shutil
from pathlib import Path

import pytest

from report_analyst.core.esrs_taxonomy import TAXONOMY_PATH_ENV, TaxonomyUnavailableError, load_esrs_taxonomy
from report_analyst.models.taxonomy import EsrsReference, TaxonomyOption

BASE = "https://example.org/taxonomy/esrs/2026-08-30/"
ROLE = BASE + "roles/"
GROUP = "[210800] E1-8 \N{EN DASH} Gross scope 1 and 2 GHG emissions"

ELEMENTS = {
    "Scope1": 'type="dtr-types:ghgEmissionsItemType" substitutionGroup="xbrli:item"',
    "PolicyTextBlock": 'type="dtr-types:textBlockItemType" substitutionGroup="xbrli:item"',
    "GasCovered": (
        'type="enum2:enumerationItemType" substitutionGroup="xbrli:item" '
        f'enum2:domain="esrs:GasMember" enum2:linkrole="{ROLE}role-999" enum2:headUsable="false"'
    ),
    "CountriesCovered": (
        'type="enum2:enumerationSetItemType" substitutionGroup="xbrli:item" '
        f'enum2:domain="country:CountryDomain" enum2:linkrole="{ROLE}role-999" enum2:headUsable="false"'
    ),
    "EmissionsHeader": 'type="xbrli:stringItemType" substitutionGroup="xbrli:item" abstract="true"',
    "EmissionsTable": 'type="xbrli:stringItemType" substitutionGroup="xbrldt:hypercubeItem" abstract="true"',
    "GasAxis": 'type="xbrli:stringItemType" substitutionGroup="xbrldt:dimensionItem" abstract="true"',
    "GasMember": 'type="dtr-types:domainItemType" substitutionGroup="xbrli:item" abstract="true"',
    "Co2Member": 'type="dtr-types:domainItemType" substitutionGroup="xbrli:item" abstract="true"',
    "Ch4Member": 'type="dtr-types:domainItemType" substitutionGroup="xbrli:item" abstract="true"',
}

LABELS = {
    "Scope1": "Gross scope 1 GHG emissions",
    "PolicyTextBlock": "Description of climate policy",
    "GasCovered": "Gas covered",
    "CountriesCovered": "Countries covered",
    "GasMember": "Gas",
    "Co2Member": "Carbon dioxide",
    "Ch4Member": "Methane",
}

SCOPE1_REFERENCE = """
    <ref:Name>ESRS</ref:Name><ref:Section>ESRS E1</ref:Section><ref:Number>E1-8</ref:Number>
    <ref:Paragraph>30</ref:Paragraph><ref:Subparagraph>a</ref:Subparagraph><ref:Clause>i</ref:Clause>
    <ref:URI>https://example.org/e1/30/a/i</ref:URI><ref:DatapointId>ESRS26_E1-8_01</ref:DatapointId>"""

# The same ESRS reference twice, and one reference to other legislation.
REFERENCES = {"Scope1": [SCOPE1_REFERENCE, SCOPE1_REFERENCE, "<ref:Name>SFDR</ref:Name><ref:Number>2022/1288</ref:Number>"]}

PRESENTATION = {"role-210800": ("EmissionsHeader", ["Scope1", "PolicyTextBlock", "GasCovered", "CountriesCovered"])}

# Out of order on purpose, options follow the order attribute.
DEFINITION = {"role-999": [("GasMember", "Ch4Member", 2), ("GasMember", "Co2Member", 1)]}

SCHEMA_NAMESPACES = (
    'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:link="http://www.xbrl.org/2003/linkbase" '
    'xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xbrli="http://www.xbrl.org/2003/instance" '
    f'xmlns:enum2="http://xbrl.org/2020/extensible-enumerations-2.0" xmlns:esrs="{BASE[:-1]}" '
    'xmlns:country="https://xbrl.org/2024/iso3166"'
)


def _schema(namespace, appinfo="", body=""):
    return (
        f'<?xml version="1.0" encoding="utf-8"?><xs:schema {SCHEMA_NAMESPACES} targetNamespace="{namespace}">'
        f"<xs:annotation><xs:appinfo>{appinfo}</xs:appinfo></xs:annotation>{body}</xs:schema>"
    )


def _linkbase_refs(*kinds):
    return "".join(
        f'<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/{kind}LinkbaseRef" '
        f'xlink:href="{kind}.xml"/>'
        for kind in kinds
    )


ROLE_TYPES = (
    f'<link:roleType roleURI="{ROLE}role-210800"><link:definition>{GROUP}</link:definition></link:roleType>'
    f'<link:roleType roleURI="{ROLE}role-999"><link:definition>[999] Enumeration: Gas</link:definition></link:roleType>'
)


def _linkbase(links):
    return (
        '<?xml version="1.0" encoding="utf-8"?><link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:ref="http://www.xbrl.org/2006/ref">'
        f"{links}</link:linkbase>"
    )


def _loc(schema, name):
    return f'<link:loc xlink:type="locator" xlink:href="{schema}#esrs_{name}" xlink:label="loc_{name}"/>'


def _resource_link(schema, link, arc, resource, items):
    """One extended link that attaches resources to concepts, as label and reference linkbases do."""
    body = ""
    for name, resources in items.items():
        body += _loc(schema, name)
        for index, content in enumerate(resources):
            body += f'<link:{resource} xlink:type="resource" xlink:label="res_{name}_{index}" {content}'
            body += f'<link:{arc} xlink:type="arc" xlink:from="loc_{name}" xlink:to="res_{name}_{index}"/>'
    return f'<link:{link} xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">{body}</link:{link}>'


def _entry_points(*schemas):
    return "".join(
        f'<tp:entryPoint><tp:name>{schema}</tp:name><tp:entryPointDocument href="{BASE}{schema}"/></tp:entryPoint>'
        for schema in schemas
    )


def write_package(root: Path, layout="single", elements=None, arc_use=""):
    """Write a small taxonomy package.

    single: one schema with concepts and all linkbases, as in the 2026 draft.
    split: a core schema with concepts, labels and references, and an "all" schema that imports it and adds
    presentation and definition, as in the 2024 taxonomy. The core entry point comes first.
    """
    folder = root / "example.org" / "esrs"
    folder.mkdir(parents=True)
    (root / "META-INF").mkdir()
    items = "".join(
        f'<xs:element id="esrs_{name}" name="{name}" xbrli:periodType="duration" {attributes}/>'
        for name, attributes in (elements or ELEMENTS).items()
    )
    if layout == "single":
        concepts, entry_points = "esrs.xsd", _entry_points("esrs.xsd")
        (folder / concepts).write_text(
            _schema(BASE[:-1], _linkbase_refs("label", "reference", "presentation", "definition") + ROLE_TYPES, items)
        )
    else:
        concepts, entry_points = "core.xsd", _entry_points("core.xsd", "all.xsd")
        (folder / concepts).write_text(_schema(BASE[:-1], _linkbase_refs("label", "reference") + ROLE_TYPES, items))
        core_import = f'<xs:import namespace="{BASE[:-1]}" schemaLocation="{BASE}core.xsd"/>'
        (folder / "all.xsd").write_text(
            _schema(BASE + "all", _linkbase_refs("presentation", "definition"), core_import), encoding="utf-8"
        )

    (root / "META-INF" / "taxonomyPackage.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><tp:taxonomyPackage xmlns:tp="http://xbrl.org/2016/taxonomy-package">'
        f"<tp:identifier>{BASE}build/2026-09-18</tp:identifier><tp:name>Sample ESRS Taxonomy</tp:name>"
        f"<tp:version>2026-08-30</tp:version><tp:entryPoints>{entry_points}</tp:entryPoints></tp:taxonomyPackage>"
    )
    (root / "META-INF" / "catalog.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">'
        f'<rewriteURI uriStartString="{BASE}" rewritePrefix="../example.org/esrs/"/></catalog>'
    )

    # A German label is written too, the loader returns the English one.
    labels = {
        name: [f'xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="en">{text}</link:label>']
        for name, text in LABELS.items()
    }
    labels["Scope1"].append('xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="de">Scope-1</link:label>')
    (folder / "label.xml").write_text(_linkbase(_resource_link(concepts, "labelLink", "labelArc", "label", labels)))

    references = {
        name: [f'xlink:role="http://www.xbrl.org/2003/role/reference">{parts}</link:reference>' for parts in parts_list]
        for name, parts_list in REFERENCES.items()
    }
    (folder / "reference.xml").write_text(
        _linkbase(_resource_link(concepts, "referenceLink", "referenceArc", "reference", references)), encoding="utf-8"
    )

    (folder / "presentation.xml").write_text(
        _linkbase(
            "".join(
                f'<link:presentationLink xlink:type="extended" xlink:role="{ROLE}{role}">'
                + "".join(_loc(concepts, name) for name in [parent, *children])
                + "".join(
                    '<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" '
                    f'xlink:from="loc_{parent}" xlink:to="loc_{child}"/>'
                    for child in children
                )
                + "</link:presentationLink>"
                for role, (parent, children) in PRESENTATION.items()
            )
        ),
        encoding="utf-8",
    )

    (folder / "definition.xml").write_text(
        _linkbase(
            "".join(
                f'<link:definitionLink xlink:type="extended" xlink:role="{ROLE}{role}">'
                + "".join(_loc(concepts, name) for name in {name for arc in arcs for name in arc[:2]})
                + "".join(
                    '<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" '
                    f'xlink:from="loc_{parent}" xlink:to="loc_{child}" order="{order}" {arc_use}/>'
                    for parent, child, order in arcs
                )
                + "</link:definitionLink>"
                for role, arcs in DEFINITION.items()
            )
        ),
        encoding="utf-8",
    )
    return root


@pytest.fixture(params=["single", "split"])
def package(request, tmp_path):
    return write_package(tmp_path / "package", request.param)


def concepts_by_name(taxonomy):
    return {concept.name: concept for concept in taxonomy.concepts}


def test_loads_package_metadata(package):
    taxonomy = load_esrs_taxonomy(package)

    assert taxonomy.identifier == BASE + "build/2026-09-18"
    assert taxonomy.name == "Sample ESRS Taxonomy"
    assert taxonomy.version == "2026-08-30"
    assert taxonomy.namespaces == {"esrs": BASE[:-1]}


@pytest.mark.parametrize(("layout", "schema"), [("single", "esrs.xsd"), ("split", "all.xsd")])
def test_entry_point_is_the_complete_one(tmp_path, layout, schema):
    assert load_esrs_taxonomy(write_package(tmp_path, layout)).entry_point == BASE + schema


def test_loads_only_reportable_concepts(package):
    names = concepts_by_name(load_esrs_taxonomy(package))

    assert set(names) == {"esrs:Scope1", "esrs:PolicyTextBlock", "esrs:GasCovered", "esrs:CountriesCovered"}


def test_loads_concept_details(package):
    scope1 = concepts_by_name(load_esrs_taxonomy(package))["esrs:Scope1"]

    assert scope1.label == "Gross scope 1 GHG emissions"
    assert scope1.kind == "number"
    assert scope1.data_type == "dtr-types:ghgEmissionsItemType"
    assert scope1.period_type == "duration"
    assert scope1.group == GROUP
    assert scope1.esrs_references == [
        EsrsReference(
            section="ESRS E1",
            disclosure_requirement="E1-8",
            paragraph="30",
            subparagraph="a",
            clause="i",
            datapoint_id="ESRS26_E1-8_01",
            url="https://example.org/e1/30/a/i",
        )
    ]


def test_concept_kind_follows_its_data_type(package):
    kinds = {name: concept.kind for name, concept in concepts_by_name(load_esrs_taxonomy(package)).items()}

    assert kinds == {
        "esrs:Scope1": "number",
        "esrs:PolicyTextBlock": "narrative",
        "esrs:GasCovered": "menu",
        "esrs:CountriesCovered": "menu",
    }


def test_menu_options_follow_taxonomy_order_without_the_domain_head(package):
    gas = concepts_by_name(load_esrs_taxonomy(package))["esrs:GasCovered"]

    assert gas.options_domain == "esrs:GasMember"
    assert gas.options == [
        TaxonomyOption(name="esrs:Co2Member", label="Carbon dioxide"),
        TaxonomyOption(name="esrs:Ch4Member", label="Methane"),
    ]


def test_menu_with_options_outside_the_package_keeps_its_domain(package):
    countries = concepts_by_name(load_esrs_taxonomy(package))["esrs:CountriesCovered"]

    assert countries.options_domain == "country:CountryDomain"
    assert countries.options == []


def test_zip_and_folder_load_the_same_concepts(package, tmp_path):
    archive = shutil.make_archive(str(tmp_path / "taxonomy"), "zip", root_dir=package.parent, base_dir=package.name)

    assert load_esrs_taxonomy(archive) == load_esrs_taxonomy(package)


def test_path_comes_from_the_setting(package, monkeypatch):
    monkeypatch.setenv(TAXONOMY_PATH_ENV, str(package))

    assert load_esrs_taxonomy().version == "2026-08-30"


def test_missing_setting_is_reported(monkeypatch):
    monkeypatch.delenv(TAXONOMY_PATH_ENV, raising=False)

    with pytest.raises(TaxonomyUnavailableError, match=TAXONOMY_PATH_ENV):
        load_esrs_taxonomy()


def test_missing_package_is_reported(tmp_path):
    with pytest.raises(TaxonomyUnavailableError, match="No ESRS taxonomy package"):
        load_esrs_taxonomy(tmp_path / "missing")


def test_unreadable_package_is_reported(tmp_path):
    package = write_package(tmp_path / "package")
    (package / "META-INF" / "taxonomyPackage.xml").write_text("not xml", encoding="utf-8")

    with pytest.raises(TaxonomyUnavailableError, match="Could not read"):
        load_esrs_taxonomy(package)


def test_package_without_a_complete_entry_point_is_reported(tmp_path):
    package = write_package(tmp_path / "package", "split")
    index = package / "META-INF" / "taxonomyPackage.xml"
    index.write_text(index.read_text().replace(_entry_points("all.xsd"), ""))

    with pytest.raises(TaxonomyUnavailableError, match="entry point"):
        load_esrs_taxonomy(package)


def test_unknown_data_type_is_reported(tmp_path):
    elements = {**ELEMENTS, "Odd": 'type="xbrli:anyURIItemType" substitutionGroup="xbrli:item"'}
    package = write_package(tmp_path / "package", elements=elements)

    with pytest.raises(TaxonomyUnavailableError, match="anyURIItemType"):
        load_esrs_taxonomy(package)


def test_concept_without_a_label_is_reported(tmp_path):
    elements = {**ELEMENTS, "Unlabelled": 'type="xbrli:stringItemType" substitutionGroup="xbrli:item"'}
    package = write_package(tmp_path / "package", elements=elements)

    with pytest.raises(TaxonomyUnavailableError, match="Unlabelled has no en label"):
        load_esrs_taxonomy(package)


def test_prohibited_relationships_are_reported(tmp_path):
    package = write_package(tmp_path / "package", arc_use='use="prohibited"')

    with pytest.raises(TaxonomyUnavailableError, match="removes relationships"):
        load_esrs_taxonomy(package)


@pytest.mark.skipif(not os.getenv(TAXONOMY_PATH_ENV), reason=f"{TAXONOMY_PATH_ENV} is not set")
def test_loads_the_2026_draft_package():
    taxonomy = load_esrs_taxonomy()

    assert taxonomy.version == "2026-08-30"
    assert taxonomy.entry_point == "https://xbrl.efrag.org/taxonomy/esrs/2026-08-30/esrs.xsd"
    assert len(taxonomy.concepts) == 444
