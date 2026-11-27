import os
import shutil
from datetime import date

import pytest

from report_analyst.core.xbrl.arelle_check import check_xbrl
from report_analyst.core.xbrl.esrs_taxonomy import TAXONOMY_PATH_ENV, load_esrs_taxonomy
from report_analyst.core.xbrl.inline_report import inline_report
from report_analyst.core.xbrl.xbrl_report import xbrl_report
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import Taxonomy, TaxonomyConcept

BASE = "https://example.org/sample/"
TAXONOMY = Taxonomy(
    identifier=BASE,
    name="Sample",
    version="1",
    entry_point=BASE + "sample.xsd",
    namespaces={"sample": BASE[:-1]},
    concepts=[
        TaxonomyConcept(
            name="sample:Consolidated",
            label="Prepared on a consolidated basis",
            kind="yes/no",
            data_type="xbrli:booleanItemType",
            period_type="duration",
        ),
        TaxonomyConcept(
            name="sample:Amount", label="Amount", kind="number", data_type="xbrli:decimalItemType", period_type="duration"
        ),
    ],
)
LEI, START, END = "529900T8BM49AURSDO55", date(2025, 1, 1), date(2025, 12, 31)


def write_package(root):
    """A taxonomy package with a yes/no and a number concept, in a single top-level folder as packages are."""
    folder = root / "sample"
    (folder / "META-INF").mkdir(parents=True)
    (folder / "schemas").mkdir()
    (folder / "META-INF" / "taxonomyPackage.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<tp:taxonomyPackage xmlns:tp="http://xbrl.org/2016/taxonomy-package" xml:lang="en">'
        f"<tp:identifier>{BASE}</tp:identifier><tp:name>Sample</tp:name><tp:version>1</tp:version>"
        f'<tp:entryPoints><tp:entryPoint><tp:name>Sample</tp:name><tp:entryPointDocument href="{BASE}sample.xsd"/>'
        "</tp:entryPoint></tp:entryPoints></tp:taxonomyPackage>"
    )
    (folder / "META-INF" / "catalog.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">'
        f'<rewriteURI uriStartString="{BASE}" rewritePrefix="../schemas/"/></catalog>'
    )
    (folder / "schemas" / "sample.xsd").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        f'xmlns:xbrli="http://www.xbrl.org/2003/instance" targetNamespace="{BASE[:-1]}" elementFormDefault="qualified">'
        '<xs:import namespace="http://www.xbrl.org/2003/instance" '
        'schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>'
        '<xs:element id="sample_Consolidated" name="Consolidated" type="xbrli:booleanItemType" '
        'substitutionGroup="xbrli:item" xbrli:periodType="duration" nillable="true"/>'
        '<xs:element id="sample_Amount" name="Amount" type="xbrli:decimalItemType" '
        'substitutionGroup="xbrli:item" xbrli:periodType="duration" nillable="true"/></xs:schema>'
    )
    return folder


def report(value, taxonomy=TAXONOMY):
    tags = [SourceTag(id="1", source_id="source-1", document_id="document-hash", concept="sample:Consolidated", value=value)]
    return xbrl_report(tags, taxonomy, LEI, START, END)


@pytest.fixture(params=["folder", "zip"])
def package(request, tmp_path):
    folder = write_package(tmp_path)
    if request.param == "folder":
        return folder
    return shutil.make_archive(str(tmp_path / "sample"), "zip", tmp_path, "sample")


def test_valid_tags_have_no_problems(package):
    assert check_xbrl(report("true"), package) == []


def test_a_problem_names_its_tag(package):
    problems = check_xbrl(report("maybe"), package)

    assert [problem.tag_id for problem in problems] == ["1"]
    assert "boolean" in problems[0].message
    assert not problems[0].message.startswith("[")


def test_a_problem_outside_the_tags_has_no_tag(package):
    missing = TAXONOMY.model_copy(update={"entry_point": BASE + "missing.xsd"})

    problems = [problem for problem in check_xbrl(report("true", missing), package) if "missing.xsd" in problem.message]

    assert problems
    assert all(problem.tag_id is None for problem in problems)


def sample_tag(id, concept, value, unit=None, decimals=None):
    return SourceTag(id=id, source_id="source-1", document_id="d", concept=concept, value=value, unit=unit, decimals=decimals)


SOURCES = [
    {"id": "source-1", "page": 1, "span_start": 0, "selected_text": "Prepared on a consolidated basis, for 1,240 sites."}
]


def test_inline_report_makes_valid_xbrl(package):
    tags = [sample_tag("1", "sample:Consolidated", "true"), sample_tag("2", "sample:Amount", "1240", "pure", 0)]
    inline, written_below = inline_report(tags, SOURCES, TAXONOMY, LEI, START, END)

    assert written_below == []
    assert check_xbrl(inline, package) == []


def test_inline_problem_names_its_tag(package):
    tags = [sample_tag("1", "sample:Consolidated", "true"), sample_tag("2", "sample:Consolidated", "maybe")]
    inline, written_below = inline_report(tags, SOURCES, TAXONOMY, LEI, START, END)

    problems = [problem for problem in check_xbrl(inline, package) if problem.tag_id == "2"]
    assert written_below == ["2"]
    assert any("boolean" in problem.message for problem in problems)


# A concept that needs the identifier of its policy.
POLICY_NAME = "esrs:NameOfPolicyIes"


@pytest.mark.skipif(not os.getenv(TAXONOMY_PATH_ENV), reason=f"{TAXONOMY_PATH_ENV} is not set")
def test_tags_on_the_2026_draft_make_valid_xbrl():
    taxonomy = load_esrs_taxonomy()
    tags = [
        SourceTag(id=str(index), source_id="s", document_id="d", concept=name, value=value, unit=unit, decimals=decimals)
        for index, (name, value, unit, decimals) in enumerate(
            [
                ("esrs:AbsoluteGrossScope1GhgEmissionsGeneratedDuringTheReportingPeriod", "1240", "tCO2e", 0),
                ("esrs:ActionsAndResourcesAreRelatedToAreasWithWaterStress", "true", None, None),
                ("esrs:DateOfTheLastUpdateOfTheMaterialityAssessment", "2025-11-30", None, None),
                (
                    "esrs:AffectedSocialStakeholderGroupsThatAreCoveredByTheOverarchingHumanRightsPolicyIdentified",
                    "esrs:OwnWorkforceMember esrs:WorkersInTheValueChainMember",
                    None,
                    None,
                ),
            ]
        )
    ]
    tags.append(
        SourceTag(id="4", source_id="s", document_id="d", concept=POLICY_NAME, value="Climate policy", identifier="P1")
    )
    xbrl = xbrl_report(tags, taxonomy, LEI, START, END)

    problems = check_xbrl(xbrl, os.environ[TAXONOMY_PATH_ENV])

    assert [problem for problem in problems if problem.tag_id] == []


@pytest.mark.skipif(not os.getenv(TAXONOMY_PATH_ENV), reason=f"{TAXONOMY_PATH_ENV} is not set")
def test_inline_tags_on_the_2026_draft_make_valid_xbrl():
    emissions = "Die Scope-1-Emissionen betrugen 1.240 t CO2e."
    water = "Our actions focus on areas with water stress."
    tags = [
        SourceTag(id=id, source_id=source_id, document_id="d", concept=name, value=value, unit=unit, decimals=decimals)
        for id, source_id, name, value, unit, decimals in [
            ("1", "a", "esrs:AbsoluteGrossScope1GhgEmissionsGeneratedDuringTheReportingPeriod", "1240", "tCO2e", 0),
            (
                "2",
                "a",
                "esrs:ActionsAndResourcesInRelationToClimateChangeMitigationAndAdaptationTextBlock",
                emissions,
                None,
                None,
            ),
            ("3", "b", "esrs:ActionsAndResourcesAreRelatedToAreasWithWaterStress", "true", None, None),
            (
                "4",
                "b",
                "esrs:AffectedSocialStakeholderGroupsThatAreCoveredByTheOverarchingHumanRightsPolicyIdentified",
                "esrs:OwnWorkforceMember",
                None,
                None,
            ),
        ]
    ]
    sources = [
        {"id": "a", "page": 3, "span_start": 0, "selected_text": emissions},
        {"id": "b", "page": 5, "span_start": 0, "selected_text": water},
        {"id": "c", "page": 7, "span_start": 0, "selected_text": "Our Climate policy covers all sites."},
    ]
    tags.append(
        SourceTag(id="5", source_id="c", document_id="d", concept=POLICY_NAME, value="Climate policy", identifier="P1")
    )
    inline, written_below = inline_report(tags, sources, load_esrs_taxonomy(), LEI, START, END)

    problems = check_xbrl(inline, os.environ[TAXONOMY_PATH_ENV])

    assert [problem for problem in problems if problem.tag_id] == []
    assert written_below == ["4"]
