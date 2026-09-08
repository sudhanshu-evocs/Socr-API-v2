"""Seed local baselines from explicitly named valid repository fixtures."""

from __future__ import annotations

from pathlib import Path

from .baseline_manager import BaselineManager
from .config import SiftConfig


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TEST_DOCUMENTS = REPOSITORY_ROOT / "test_documents"

# One representative page-1 reference per explicit SOCR template. Ambiguous
# fixtures are intentionally omitted rather than guessed into the wrong template.
KNOWN_GOOD_FIXTURES = (
    ("1st Bank", "bank_statement", "Valid_1stBank_Statement.pdf"),
    ("Ally", "bank_statement", "Valid_Ally_Bank_Statement.pdf"),
    ("Bank of America", "bank_statement", "Valid_Bank_of_America_Statement.pdf"),
    ("Capital One", "bank_statement", "Valid_Capital_One_Bank_Statement.pdf"),
    ("Charles Schwab Bank", "bank_statement", "Valid_Charles_Schwab_Bank_with_more_fonts_on_2nd_page.pdf"),
    ("Chase Bank", "bank_statement", "Valid_Chase_Bank_with_prefix_in_fonts.pdf"),
    ("Chime Bank", "bank_statement", "Valid_Chime_bank_statement.pdf"),
    ("Citadel", "bank_statement", "Valid_Citadel_Bank_Statement.pdf"),
    ("Citizens Bank", "bank_statement", "Valid_Citizens_Bank_Statement.pdf"),
    ("Navy FCU", "bank_statement", "Valid_Navy_FCU_bank.pdf"),
    ("Novo", "bank_statement", "Valid_novo_bank_statement.pdf"),
    ("People's United", "bank_statement", "Valid_People_United_Bank_Statement_with_single_font.pdf"),
    ("PNC Bank", "bank_statement", "Valid_PNC_Bank_for_font_multiplicity.pdf"),
    ("TD Bank", "bank_statement", "Valid_TD_Bank_Statement.pdf"),
    ("ADP1", "paystub", "Valid_ADP_Paystub_Not_Getting_Metadata_Read.pdf"),
    ("ADPNA", "paystub", "Valid_ADPNA_POI.PDF"),
    ("Gusto", "paystub", "Valid_Gusto_single_page.pdf"),
    ("Insperity", "paystub", "Valid_Odd_Insperity_Paystub.pdf"),
    ("Justworks", "paystub", "Valid_Justworks_Paystub_for_fonts.pdf"),
    ("Paychex", "paystub", "Valid_single-paystub_paychex_paystub.pdf"),
    ("Paycom", "paystub", "Valid_Paycom_Paystub_2024.pdf"),
    ("Paycor", "paystub", "Valid_paycor_1_page_paystub.pdf"),
    ("Rippling", "paystub", "Valid_rippling_paystub_for_fonts_check.pdf"),
)


def main() -> int:
    manager = BaselineManager(SiftConfig.from_environment())
    registered = 0
    skipped = 0
    for template, document_type, filename in KNOWN_GOOD_FIXTURES:
        fixture = TEST_DOCUMENTS / filename
        if not fixture.is_file():
            raise FileNotFoundError(f"Known-good fixture is missing: {fixture}")
        try:
            path = manager.register_pdf(template, document_type, fixture.read_bytes())
            print(f"REGISTERED {template}: {path}")
            registered += 1
        except FileExistsError:
            print(f"SKIPPED {template}: baseline already exists")
            skipped += 1

    print(f"Completed: {registered} registered, {skipped} already present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
