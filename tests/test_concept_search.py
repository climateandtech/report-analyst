from report_analyst.core.concept_search import search_concepts, standards
from report_analyst.models.taxonomy import EsrsReference, TaxonomyConcept

DASH = "\N{EN DASH}"


def concept(name, label, kind, group, section=None, requirement=None, paragraph=None, datapoint=None):
    references = [
        EsrsReference(section=section, disclosure_requirement=requirement, paragraph=paragraph, datapoint_id=datapoint)
    ]
    return TaxonomyConcept(
        name=f"esrs:{name}",
        label=label,
        kind=kind,
        data_type="xbrli:stringItemType",
        period_type="duration",
        group=group,
        esrs_references=references if section else [],
    )


# Listed out of taxonomy order on purpose.
SCOPE1 = concept(
    "Scope1",
    "Absolute gross scope 1 GHG emissions",
    "number",
    f"[210800] E1-8 {DASH} Gross scope 1 and 2 GHG emissions",
    "ESRS E1",
    "E1-8",
    "30",
    "ESRS26_E1-8_01",
)
EMPLOYEES = concept(
    "Employees",
    "Total number of employees",
    "number",
    f"[310500] S1-6 {DASH} Characteristics of the undertaking's employees",
    "ESRS S1",
    "S1-6",
    "40",
    "ESRS26_S1-6_01",
)
PLAN = concept(
    "PlanTextBlock",
    "Disclosure of the plan",
    "narrative",
    f"[210100] E1-1 {DASH} Transition plan for climate change mitigation",
    "ESRS E1",
    "E1-1",
    "5",
    "ESRS26_E1-1_01",
)
POLICY_NAME = concept("NameOfPolicyIes", "Name of policy(ies)", "text", f"[100500] ESRS 2 GDR-P {DASH} Policies")
BASIS = concept(
    "Consolidated",
    "Sustainability statement has been prepared on a consolidated basis",
    "yes/no",
    f"[100100] ESRS 2 BP-1 {DASH} Basis for preparation of the sustainability statement",
    "ESRS 2",
    "BP-1",
    "3",
    "ESRS26_BP-1_01",
)
CONCEPTS = [SCOPE1, EMPLOYEES, PLAN, POLICY_NAME, BASIS]


def names(concepts):
    return [concept.name for concept in concepts]


def test_without_a_query_all_concepts_follow_group_order():
    assert search_concepts(CONCEPTS) == [BASIS, POLICY_NAME, PLAN, SCOPE1, EMPLOYEES]


def test_every_word_must_match_in_any_order_and_case():
    assert names(search_concepts(CONCEPTS, "SCOPE 1")) == ["esrs:Scope1"]
    assert names(search_concepts(CONCEPTS, "1 scope")) == ["esrs:Scope1"]
    assert search_concepts(CONCEPTS, "scope employees") == []


def test_words_match_their_start_and_numbers_match_whole():
    policy_scope = concept(
        "PolicyScope",
        "Description of scope of policy",
        "narrative",
        f"[101300] GDR-P {DASH} Policies",
        "ESRS 2",
        "GDR-P",
        "13",
    )

    assert names(search_concepts([SCOPE1, policy_scope], "emiss")) == ["esrs:Scope1"]
    assert names(search_concepts([SCOPE1, policy_scope], "scope 1")) == ["esrs:Scope1"]


def test_search_matches_the_disclosure_requirement_and_datapoint():
    assert names(search_concepts(CONCEPTS, "e1-8")) == ["esrs:Scope1"]
    assert names(search_concepts(CONCEPTS, "ESRS26_S1-6_01")) == ["esrs:Employees"]


def test_search_matches_the_group():
    assert names(search_concepts(CONCEPTS, "transition")) == ["esrs:PlanTextBlock"]


def test_search_matches_the_paragraph():
    assert names(search_concepts(CONCEPTS, "e1-1 5")) == ["esrs:PlanTextBlock"]


def test_filters_by_standard():
    assert names(search_concepts(CONCEPTS, standard="ESRS E1")) == ["esrs:PlanTextBlock", "esrs:Scope1"]


def test_filters_by_kind():
    assert names(search_concepts(CONCEPTS, kind="number")) == ["esrs:Scope1", "esrs:Employees"]


def test_query_and_filters_combine():
    assert names(search_concepts(CONCEPTS, "gross", standard="ESRS E1", kind="number")) == ["esrs:Scope1"]
    assert search_concepts(CONCEPTS, "gross", kind="narrative") == []


def test_standards_follow_group_order():
    assert standards(CONCEPTS) == ["ESRS 2", "ESRS E1", "ESRS S1"]
