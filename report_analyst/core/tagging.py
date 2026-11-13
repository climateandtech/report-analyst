"""Checks a value entered for an ESRS concept and turns it into a tag on a saved source."""

import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import TaxonomyConcept

PERCENT = "percentItemType"
WHOLE_NUMBER = "integerItemType"
MONEY = "monetaryItemType"
SET_MENU = "enumerationSetItemType"
YEAR = "gYearItemType"
# Percentages and counts have no unit, which XBRL writes as "pure".
PURE = "pure"
PURE_TYPES = {PERCENT, WHOLE_NUMBER, "decimalItemType"}
CURRENCY = re.compile(r"[A-Z]{3}")
# The recommended units of the XBRL Unit Type Registry (https://www.xbrl.org/utr/utr.xml),
# with the ones most used in ESRS reports first.
UNITS = {
    "ghgEmissionsItemType": ["tCO2e", "ktCO2e", "MtCO2e", "GtCO2e"],
    "energyItemType": [
        "MWh", "GWh", "TWh", "kWh", "Wh", "GJ", "TJ", "MJ", "kJ", "J", "mJ", "MMBTU", "Btu", "Boe",
        "MBoe", "MMBoe", "Mcfe", "MMcfe", "Bcfe", "Tcfe", "Cal", "ft_lb", "MWM", "GWM", "VAh", "dth", "MWd",
    ],  # fmt: skip
    "massItemType": ["t", "kt", "Mt", "Gt", "kg", "g", "lb", "oz", "ozt", "T", "kT", "MT", "GT"],
    "volumeItemType": ["m3", "l", "bbl", "MBbls", "MMBbls", "ft3", "Mcf", "MMcf", "Bcf", "Tcf", "gal", "bu", "aft"],
}


class InvalidTagError(ValueError):
    """The entered value does not fit the concept. The message says what to change."""


def unit_choices(concept: TaxonomyConcept) -> list[str]:
    """The units a number can have. Empty for money, where the currency code is typed."""
    return [PURE] if data_type(concept) in PURE_TYPES else list(UNITS.get(data_type(concept), []))


def create_tag(
    concept: TaxonomyConcept,
    source: dict,
    entered: Any,
    unit: str | None = None,
    decimals: int | None = None,
) -> SourceTag:
    """Check the entered value and return the tag to save.

    The value is a str for text, numbers and menus without options, a bool for yes/no, an option name
    for a menu, a list of option names for a set menu, a date for a date and an int for a year.
    """
    if concept.kind == "number":
        value, unit, decimals = _number(concept, entered, unit, decimals)
    else:
        value, unit, decimals = _value(concept, entered), None, None
    return SourceTag(
        id=uuid.uuid4().hex,
        source_id=source["id"],
        document_id=source["document_id"],
        concept=concept.name,
        value=value,
        unit=unit,
        decimals=decimals,
    )


def _value(concept: TaxonomyConcept, entered: Any) -> str:
    if concept.kind == "yes/no":
        return "true" if entered else "false"
    if concept.kind == "date":
        if entered is None:
            raise InvalidTagError("Enter a value.")
        return entered.isoformat() if isinstance(entered, date) else str(entered)
    if concept.kind == "menu" and concept.options:
        return _options(concept, entered)
    return _text(entered)


def _text(entered: str) -> str:
    text = entered.strip()
    if not text:
        raise InvalidTagError("Enter a value.")
    return text


def _options(concept: TaxonomyConcept, entered: Any) -> str:
    if data_type(concept) == SET_MENU:
        chosen, missing = entered, "Choose at least one option."
    else:
        chosen, missing = [entered] if entered else [], "Choose an option."
    if not chosen:
        raise InvalidTagError(missing)
    known = {option.name for option in concept.options}
    for name in chosen:
        if name not in known:
            raise InvalidTagError(f"{name} is not an option of this concept.")
    return " ".join(chosen)


def _number(concept: TaxonomyConcept, entered: str, unit: str | None, decimals: int) -> tuple[str, str, int]:
    number = _parse(entered)
    if data_type(concept) == WHOLE_NUMBER and number != number.to_integral_value():
        raise InvalidTagError("This concept takes a whole number.")
    if data_type(concept) == PERCENT:
        # XBRL writes 25 % as 0.25, so the number also has two more decimals.
        number, decimals = number.scaleb(-2), decimals + 2
    return format(number, "f"), _unit(concept, unit), decimals


def _parse(entered: str) -> Decimal:
    try:
        number = Decimal(entered.strip())
    except InvalidOperation:
        number = None
    if number is None or not number.is_finite():
        raise InvalidTagError("Enter a number, such as 1240 or 12.5, without thousands separators.")
    return number


def _unit(concept: TaxonomyConcept, unit: str | None) -> str:
    if data_type(concept) in PURE_TYPES:
        return PURE
    if data_type(concept) == MONEY:
        currency = (unit or "").strip().upper()
        if not CURRENCY.fullmatch(currency):
            raise InvalidTagError("Enter the currency as a 3-letter code, such as EUR.")
        return currency
    if unit not in unit_choices(concept):
        raise InvalidTagError(f"{unit} is not a unit for this concept.")
    return unit


def data_type(concept: TaxonomyConcept) -> str:
    """The data type without its prefix, such as percentItemType."""
    return concept.data_type.rpartition(":")[2]
