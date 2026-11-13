from datetime import date

import pytest

from report_analyst.core.tagging import InvalidTagError, create_tag, unit_choices
from report_analyst.models.taxonomy import TaxonomyConcept, TaxonomyOption

SOURCE = {"id": "source-1", "document_id": "document-hash", "selected_text": "Scope 1 emissions were 1240 t"}
OPTIONS = [
    TaxonomyOption(name="esrs:OwnWorkforceMember", label="Own workforce"),
    TaxonomyOption(name="esrs:WorkersMember", label="Workers"),
]


def concept(kind, data_type, options=(), options_domain=None):
    return TaxonomyConcept(
        name="esrs:Sample",
        label="Sample",
        kind=kind,
        data_type=data_type,
        period_type="duration",
        options=list(options),
        options_domain=options_domain,
    )


NARRATIVE = concept("narrative", "dtr-types:textBlockItemType")
EMISSIONS = concept("number", "dtr-types:ghgEmissionsItemType")
PERCENT = concept("number", "dtr-types:percentItemType")
COUNT = concept("number", "xbrli:integerItemType")
MONEY = concept("number", "xbrli:monetaryItemType")
YES_NO = concept("yes/no", "xbrli:booleanItemType")
ONE_CHOICE = concept("menu", "enum2:enumerationItemType", OPTIONS)
SET = concept("menu", "enum2:enumerationSetItemType", OPTIONS)
COUNTRY = concept("menu", "enum2:enumerationItemType", options_domain="country:CountriesDomain")
DATE = concept("date", "xbrli:dateItemType")
YEAR = concept("date", "xbrli:gYearItemType")


def test_a_tag_keeps_its_source_and_concept():
    tag = create_tag(NARRATIVE, SOURCE, "  The policy covers all sites.  ")

    assert (tag.source_id, tag.document_id, tag.concept) == ("source-1", "document-hash", "esrs:Sample")
    assert (tag.value, tag.unit, tag.decimals) == ("The policy covers all sites.", None, None)
    assert tag.id != create_tag(NARRATIVE, SOURCE, "Text").id


def test_text_must_not_be_blank():
    with pytest.raises(InvalidTagError, match="Enter a value"):
        create_tag(NARRATIVE, SOURCE, "   ")


def test_a_number_keeps_its_unit_and_decimals():
    tag = create_tag(EMISSIONS, SOURCE, "1240.50", "ktCO2e", 2)

    assert (tag.value, tag.unit, tag.decimals) == ("1240.50", "ktCO2e", 2)


@pytest.mark.parametrize("entered", ["1,240", "1 240", "about 5", "", "NaN", "Infinity"])
def test_a_number_must_be_written_plainly(entered):
    with pytest.raises(InvalidTagError, match="Enter a number"):
        create_tag(EMISSIONS, SOURCE, entered, "tCO2e", 0)


def test_a_unit_must_fit_the_data_type():
    assert unit_choices(EMISSIONS)[0] == "tCO2e"

    with pytest.raises(InvalidTagError, match="MWh is not a unit for this concept"):
        create_tag(EMISSIONS, SOURCE, "1240", "MWh", 0)


def test_percent_is_stored_as_a_fraction():
    tag = create_tag(PERCENT, SOURCE, "25", None, 0)

    assert (tag.value, tag.unit, tag.decimals) == ("0.25", "pure", 2)
    assert unit_choices(PERCENT) == ["pure"]


def test_a_count_must_be_a_whole_number():
    assert create_tag(COUNT, SOURCE, "1E3", None, 0).value == "1000"

    with pytest.raises(InvalidTagError, match="whole number"):
        create_tag(COUNT, SOURCE, "12.5", None, 0)


def test_money_takes_a_currency_code():
    assert unit_choices(MONEY) == []
    assert create_tag(MONEY, SOURCE, "5000000", "EUR", -3).unit == "EUR"

    with pytest.raises(InvalidTagError, match="3-letter code"):
        create_tag(MONEY, SOURCE, "5000000", "euro", -3)


def test_yes_no_is_stored_as_true_or_false():
    assert create_tag(YES_NO, SOURCE, True).value == "true"
    assert create_tag(YES_NO, SOURCE, False).value == "false"


def test_a_menu_takes_one_of_its_options():
    assert create_tag(ONE_CHOICE, SOURCE, "esrs:WorkersMember").value == "esrs:WorkersMember"

    with pytest.raises(InvalidTagError, match="esrs:Other is not an option"):
        create_tag(ONE_CHOICE, SOURCE, "esrs:Other")


def test_a_set_menu_takes_one_or_more_options():
    assert create_tag(SET, SOURCE, ["esrs:OwnWorkforceMember", "esrs:WorkersMember"]).value == (
        "esrs:OwnWorkforceMember esrs:WorkersMember"
    )

    with pytest.raises(InvalidTagError, match="Choose at least one option"):
        create_tag(SET, SOURCE, [])


def test_a_menu_without_options_takes_a_code():
    assert create_tag(COUNTRY, SOURCE, " DE ").value == "DE"

    with pytest.raises(InvalidTagError, match="Enter a value"):
        create_tag(COUNTRY, SOURCE, "")


def test_dates_and_years():
    assert create_tag(DATE, SOURCE, date(2026, 3, 31)).value == "2026-03-31"
    assert create_tag(YEAR, SOURCE, 2030).value == "2030"


@pytest.mark.parametrize("empty_concept", [DATE, YEAR])
def test_a_date_or_year_must_be_entered(empty_concept):
    with pytest.raises(InvalidTagError, match="Enter a value"):
        create_tag(empty_concept, SOURCE, None)
