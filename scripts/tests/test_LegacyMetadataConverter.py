import json
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from src.LegacyMetadataConverter import LegacyMetadataConverter


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=4) + "\n", encoding="utf-8")


def base_row(**overrides):
    row = {
        "creator": "CreatorX",
        "producer": "ProducerX",
        "created": "Present",
        "modified": "Equal",
        "template": "TemplateX",
        "file_size": "10-20",
        "font": "Helvetica",
    }
    row.update(overrides)
    return row


def build_converter(tmp_path):
    bank_ref_dir = tmp_path / "refs" / "BankStatementsRuleJson"
    income_ref_dir = tmp_path / "refs" / "EarningStatementsRuleJson"
    write_json(bank_ref_dir / "Citi Bank.json", [])
    write_json(income_ref_dir / "BenefitMall.json", [])

    out_dir = tmp_path / "generated"
    report_path = out_dir / "conversion_report.json"
    return LegacyMetadataConverter(
        bank_reference_dir=bank_ref_dir,
        income_reference_dir=income_ref_dir,
        out_dir=out_dir,
        report_path=report_path,
    )


def test_sentinel_template_maps_to_unknown_for_bank_and_income(tmp_path):
    converter = build_converter(tmp_path)
    bank_source = tmp_path / "BankMetadata.json"
    income_source = tmp_path / "Metadata.json"
    write_json(bank_source, [base_row(template="No")])
    write_json(income_source, [base_row(template="No")])

    report = converter.convert_from_file_paths(bank_source=bank_source, income_source=income_source)

    bank_unknown_file = tmp_path / "generated" / "BankStatementsRuleJson" / "Unknown.json"
    income_unknown_file = tmp_path / "generated" / "EarningStatementsRuleJson" / "Unknown.json"
    assert bank_unknown_file.exists()
    assert income_unknown_file.exists()

    assert json.loads(bank_unknown_file.read_text(encoding="utf-8"))[0]["template"]["name"] == "Unknown"
    assert json.loads(income_unknown_file.read_text(encoding="utf-8"))[0]["template"]["name"] == "Unknown"

    assert report["datasets"]["bank"]["match_counts"]["sentinel_to_unknown"] == 1
    assert report["datasets"]["income"]["match_counts"]["sentinel_to_unknown"] == 1


def test_filename_routing_uses_exact_then_normalized_then_new_file(tmp_path):
    converter = build_converter(tmp_path)
    bank_source = tmp_path / "BankMetadata.json"
    income_source = tmp_path / "Metadata.json"
    write_json(
        bank_source,
        [
            base_row(template="Citi Bank"),
            base_row(template="Citibank"),
            base_row(template="Brand/New Bank"),
        ],
    )
    write_json(income_source, [])

    report = converter.convert_from_file_paths(bank_source=bank_source, income_source=income_source)

    bank_output_dir = tmp_path / "generated" / "BankStatementsRuleJson"
    assert (bank_output_dir / "Citi Bank.json").exists()
    assert (bank_output_dir / "Brand_New Bank.json").exists()

    citi_rules = json.loads((bank_output_dir / "Citi Bank.json").read_text(encoding="utf-8"))
    assert [rule["template"]["name"] for rule in citi_rules] == ["Citi Bank", "Citibank"]

    assert report["datasets"]["bank"]["match_counts"]["exact"] == 1
    assert report["datasets"]["bank"]["match_counts"]["normalized"] == 1
    assert report["datasets"]["bank"]["match_counts"]["created_new"] == 1


def test_converter_clears_stale_generated_files_before_writing(tmp_path):
    converter = build_converter(tmp_path)
    bank_output_dir = tmp_path / "generated" / "BankStatementsRuleJson"
    write_json(bank_output_dir / "Stale Template.json", [base_row(template="Stale Template")])

    bank_source = tmp_path / "BankMetadata.json"
    income_source = tmp_path / "Metadata.json"
    write_json(bank_source, [base_row(template="Citi Bank")])
    write_json(income_source, [])

    converter.convert_from_file_paths(bank_source=bank_source, income_source=income_source)

    assert not (bank_output_dir / "Stale Template.json").exists()
    assert (bank_output_dir / "Citi Bank.json").exists()


def test_converter_parses_fonts_file_size_and_dates_into_new_schema(tmp_path):
    converter = build_converter(tmp_path)
    bank_source = tmp_path / "BankMetadata.json"
    income_source = tmp_path / "Metadata.json"
    write_json(
        bank_source,
        [
            base_row(
                template="New Template",
                created="7-10-2014",
                modified="5 HRS",
                file_size="20 - 45",
                font="Helvetica; Arial (O); ;",
            )
        ],
    )
    write_json(income_source, [])

    report = converter.convert_from_file_paths(bank_source=bank_source, income_source=income_source)
    converted_file = tmp_path / "generated" / "BankStatementsRuleJson" / "New Template.json"
    converted_rule = json.loads(converted_file.read_text(encoding="utf-8"))[0]

    assert converted_rule["dates"]["created"]["state"] == "D:20140710000000"
    assert converted_rule["dates"]["modified"]["state"] == "Equal"
    assert converted_rule["dates"]["modified"]["duration"] == 0
    assert converted_rule["dates"]["modified"]["tolerance"] == 18000
    assert converted_rule["file_size"] == {"algorithm": "Constant", "min": 20, "max": 45}

    assert converted_rule["fonts"]["required_fonts"] == [
        {"name": "Helvetica", "type": "", "encoding": "", "multiplicity": 1}
    ]
    assert converted_rule["fonts"]["optional_fonts"] == [
        {"name": "Arial", "type": "", "encoding": "", "multiplicity": 9999}
    ]
    assert report["datasets"]["bank"]["parse_fallbacks"]["font_empty_tokens"] == 2


def test_converter_emits_prefix_regex_for_single_value_fields(tmp_path):
    converter = build_converter(tmp_path)
    bank_source = tmp_path / "BankMetadata.json"
    income_source = tmp_path / "Metadata.json"
    write_json(
        bank_source,
        [
            base_row(
                template="1st Bank",
                producer="Style Report",
                creator="PCL2PDF (TM) from Visual Software",
            )
        ],
    )
    write_json(income_source, [])

    converter.convert_from_file_paths(bank_source=bank_source, income_source=income_source)
    converted_file = tmp_path / "generated" / "BankStatementsRuleJson" / "1st Bank.json"
    converted_rule = json.loads(converted_file.read_text(encoding="utf-8"))[0]

    assert converted_rule["producer"]["name"] == r"^Style Report.*"
    assert converted_rule["creator"]["name"] == r"^PCL2PDF \(TM\) from Visual Software.*"


def test_conversion_report_tracks_parse_fallbacks_and_present_present_rows(tmp_path):
    converter = build_converter(tmp_path)
    bank_source = tmp_path / "BankMetadata.json"
    income_source = tmp_path / "Metadata.json"
    write_json(
        bank_source,
        [
            base_row(
                template="No",
                created="NotADate",
                modified="AlsoNotADate",
                file_size="unknown",
                font="; ;",
            )
        ],
    )
    write_json(income_source, [base_row(template="BenefitMall", created="Present", modified="Present")])

    report = converter.convert_from_file_paths(bank_source=bank_source, income_source=income_source)

    bank_fallbacks = report["datasets"]["bank"]["parse_fallbacks"]
    assert bank_fallbacks["created_date_unparseable"] == 1
    assert bank_fallbacks["modified_date_unparseable"] == 1
    assert bank_fallbacks["file_size_unparseable"] == 1
    assert bank_fallbacks["font_no_valid_tokens"] == 1

    income_present_present = report["datasets"]["income"]["present_present"]
    assert income_present_present["count"] == 1
    assert income_present_present["templates"] == ["BenefitMall"]

    report_path = tmp_path / "generated" / "conversion_report.json"
    assert report_path.exists()
    parsed_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert parsed_report["overall"]["rows_processed"] == 2
