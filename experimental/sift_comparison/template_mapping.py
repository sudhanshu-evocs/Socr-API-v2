"""Explicit mappings from SOCR template names to local SIFT baselines."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineMapping:
    key: str
    category_directory: str
    display_name: str


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


_BANK_MAPPINGS = {
    "1st bank": BaselineMapping("1st_Bank", "bank_statements", "1st Bank"),
    "pnc": BaselineMapping("PNC_Bank", "bank_statements", "PNC Bank"),
    "pnc bank": BaselineMapping("PNC_Bank", "bank_statements", "PNC Bank"),
    "chase": BaselineMapping("Chase_Bank", "bank_statements", "Chase Bank"),
    "chase bank": BaselineMapping("Chase_Bank", "bank_statements", "Chase Bank"),
    "capitalone": BaselineMapping("Capital_One", "bank_statements", "Capital One"),
    "capital one": BaselineMapping("Capital_One", "bank_statements", "Capital One"),
    "capital one bank": BaselineMapping("Capital_One", "bank_statements", "Capital One"),
    "ally": BaselineMapping("Ally", "bank_statements", "Ally"),
    "ally bank": BaselineMapping("Ally", "bank_statements", "Ally"),
    "bank of america": BaselineMapping("Bank_of_America", "bank_statements", "Bank of America"),
    "charles schwab": BaselineMapping("Charles_Schwab_Bank", "bank_statements", "Charles Schwab Bank"),
    "charles schwab bank": BaselineMapping("Charles_Schwab_Bank", "bank_statements", "Charles Schwab Bank"),
    "chime": BaselineMapping("Chime_Bank", "bank_statements", "Chime Bank"),
    "chime bank": BaselineMapping("Chime_Bank", "bank_statements", "Chime Bank"),
    "citadel": BaselineMapping("Citadel", "bank_statements", "Citadel"),
    "citizens bank": BaselineMapping("Citizens_Bank", "bank_statements", "Citizens Bank"),
    "navy fcu": BaselineMapping("Navy_FCU", "bank_statements", "Navy FCU"),
    "novo": BaselineMapping("Novo", "bank_statements", "Novo"),
    "people s united": BaselineMapping("Peoples_United_Bank", "bank_statements", "People's United"),
    "peoples united": BaselineMapping("Peoples_United_Bank", "bank_statements", "People's United"),
    "peoples united bank": BaselineMapping("Peoples_United_Bank", "bank_statements", "Peoples United Bank"),
    "td bank": BaselineMapping("TD_Bank", "bank_statements", "TD Bank"),
}

_PAYSTUB_MAPPINGS = {
    "adp1": BaselineMapping("ADP1", "paystubs", "ADP1"),
    "adpna": BaselineMapping("ADPNA", "paystubs", "ADPNA"),
    "gusto": BaselineMapping("Gusto", "paystubs", "Gusto"),
    "insperity": BaselineMapping("Insperity", "paystubs", "Insperity"),
    "justworks": BaselineMapping("Justworks", "paystubs", "Justworks"),
    "paychex": BaselineMapping("Paychex", "paystubs", "Paychex"),
    "paycom": BaselineMapping("Paycom", "paystubs", "Paycom"),
    "paycor": BaselineMapping("Paycor", "paystubs", "Paycor"),
    "rippling": BaselineMapping("Rippling", "paystubs", "Rippling"),
}


def resolve_template_mapping(template: str, document_type: str = "") -> BaselineMapping | None:
    normalized_template = _normalize(template)
    normalized_type = _normalize(document_type)
    if normalized_type in {"paystub", "paystubs", "paystub earning statement", "paystubs earnings"}:
        return _PAYSTUB_MAPPINGS.get(normalized_template)
    if normalized_type in {"bank", "bank statement", "bank statements"}:
        return _BANK_MAPPINGS.get(normalized_template)

    bank_mapping = _BANK_MAPPINGS.get(normalized_template)
    paystub_mapping = _PAYSTUB_MAPPINGS.get(normalized_template)
    return bank_mapping if bank_mapping and not paystub_mapping else paystub_mapping if paystub_mapping and not bank_mapping else None
