import json
import subprocess
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from src.GeneratedRulesetComparator import GeneratedRulesetComparator


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=4) + "\n", encoding="utf-8")


def rule(
    template="TemplateX",
    producer="^Producer.*",
    creator="^Creator.*",
    file_size=None,
    required_fonts=None,
    optional_fonts=None,
    created_state="Present",
    modified=None,
):
    return {
        "template": {"name": template},
        "producer": {"name": producer},
        "creator": {"name": creator},
        "file_size": file_size if file_size is not None else {"algorithm": "Unknown"},
        "fonts": {
            "required_fonts": required_fonts if required_fonts is not None else [],
            "optional_fonts": optional_fonts if optional_fonts is not None else [],
        },
        "dates": {
            "created": {"state": created_state},
            "modified": modified if modified is not None else {"state": "Equal"},
        },
    }


def font(name, type_="", encoding="", multiplicity=1):
    return {
        "name": name,
        "type": type_,
        "encoding": encoding,
        "multiplicity": multiplicity,
    }


def build_comparator(tmp_path):
    generated_root = tmp_path / "generated"
    bank_ref_dir = tmp_path / "refs" / "BankStatementsRuleJson"
    income_ref_dir = tmp_path / "refs" / "EarningStatementsRuleJson"

    return GeneratedRulesetComparator(
        generated_root=generated_root,
        bank_reference_dir=bank_ref_dir,
        income_reference_dir=income_ref_dir,
        report_path=generated_root / "comparison_report.json",
    )


def test_comparator_reports_identical_exact_match(tmp_path):
    comparator = build_comparator(tmp_path)
    bank_generated = tmp_path / "generated" / "BankStatementsRuleJson" / "Citi Bank.json"
    bank_reference = tmp_path / "refs" / "BankStatementsRuleJson" / "Citi Bank.json"
    payload = [rule(template="Citi Bank")]

    write_json(bank_generated, payload)
    write_json(bank_reference, payload)

    report = comparator.compare()

    matched = report["datasets"]["bank"]["matched_files"]
    assert matched[0]["status"] == "identical"
    assert report["overall"]["different_files"] == 0


def test_comparator_uses_normalized_filename_matching(tmp_path):
    comparator = build_comparator(tmp_path)
    generated = tmp_path / "generated" / "EarningStatementsRuleJson" / "Bank of America.json"
    reference = tmp_path / "refs" / "EarningStatementsRuleJson" / "Bank Of America.json"

    write_json(generated, [rule(template="Bank of America")])
    write_json(reference, [rule(template="Bank of America")])

    report = comparator.compare()
    matched = report["datasets"]["income"]["matched_files"]

    assert matched[0]["match_type"] == "normalized"
    assert matched[0]["status"] == "identical"


def test_comparator_reports_only_on_one_side(tmp_path):
    comparator = build_comparator(tmp_path)
    generated = tmp_path / "generated" / "BankStatementsRuleJson" / "Only Generated.json"
    reference = tmp_path / "refs" / "BankStatementsRuleJson" / "Only Reference.json"

    write_json(generated, [rule(template="Only Generated")])
    write_json(reference, [rule(template="Only Reference")])

    report = comparator.compare()
    bank = report["datasets"]["bank"]

    assert bank["generated_only_files"] == ["Only Generated.json"]
    assert bank["reference_only_files"] == ["Only Reference.json"]


def test_comparator_reports_ambiguous_normalized_matches(tmp_path):
    comparator = build_comparator(tmp_path)
    generated = tmp_path / "generated" / "BankStatementsRuleJson"
    reference = tmp_path / "refs" / "BankStatementsRuleJson"

    write_json(generated / "AB.json", [rule(template="AB")])
    write_json(generated / "A-B.json", [rule(template="A-B")])
    write_json(reference / "A B.json", [rule(template="A B")])

    report = comparator.compare()
    ambiguous = report["datasets"]["bank"]["ambiguous_matches"]

    assert ambiguous == [
        {
            "normalized_key": "ab",
            "generated_files": ["A-B.json", "AB.json"],
            "reference_files": ["A B.json"],
        }
    ]


def test_comparator_ignores_rule_and_font_order(tmp_path):
    comparator = build_comparator(tmp_path)
    generated = tmp_path / "generated" / "BankStatementsRuleJson" / "Ordered.json"
    reference = tmp_path / "refs" / "BankStatementsRuleJson" / "Ordered.json"

    alpha = rule(
        template="Ordered",
        producer="^A.*",
        required_fonts=[font("Beta"), font("Alpha")],
    )
    beta = rule(
        template="Ordered",
        producer="^B.*",
        required_fonts=[font("Delta"), font("Gamma")],
    )

    write_json(generated, [beta, alpha])
    write_json(reference, [{**alpha, "fonts": {"required_fonts": [font("Alpha"), font("Beta")], "optional_fonts": []}}, beta])

    report = comparator.compare()
    matched = report["datasets"]["bank"]["matched_files"]

    assert matched[0]["status"] == "identical"


def test_comparator_reports_field_level_diffs_and_extra_rules(tmp_path):
    comparator = build_comparator(tmp_path)
    generated = tmp_path / "generated" / "EarningStatementsRuleJson" / "Diff.json"
    reference = tmp_path / "refs" / "EarningStatementsRuleJson" / "Diff.json"

    write_json(
        generated,
        [
            rule(
                template="Diff",
                producer="^iText.*",
                required_fonts=[font("Helvetica"), font("Times-Roman")],
                file_size={"algorithm": "Constant", "min": 7, "max": 13},
            ),
            rule(template="Diff", producer="^zPDFium.*"),
        ],
    )
    write_json(
        reference,
        [
            rule(
                template="Diff",
                producer="^iText 2.1.7 by 1T3XT.*",
                required_fonts=[font("Helvetica", type_="Type1"), font("Times-Roman")],
                file_size={"min": 6, "max": 10},
            )
        ],
    )

    report = comparator.compare()
    matched = report["datasets"]["income"]["matched_files"][0]
    diff_paths = {item["path"] for item in matched["rule_diffs"][0]["differences"]}

    assert matched["status"] == "different"
    assert matched["changed_rules"] == 1
    assert len(matched["generated_only_rules"]) == 1
    assert len(matched["reference_only_rules"]) == 0
    assert "producer.name" in diff_paths
    assert "file_size.algorithm" in diff_paths
    assert "file_size.min" in diff_paths
    assert "file_size.max" in diff_paths
    assert any(path.startswith("fonts.required_fonts[") and path.endswith(".type") for path in diff_paths)


def test_cli_exit_code_and_report_output(tmp_path):
    generated_root = tmp_path / "generated"
    bank_generated = generated_root / "BankStatementsRuleJson" / "Mismatch.json"
    bank_reference = tmp_path / "refs" / "BankStatementsRuleJson" / "Mismatch.json"
    income_generated = generated_root / "EarningStatementsRuleJson"
    income_reference = tmp_path / "refs" / "EarningStatementsRuleJson"

    write_json(bank_generated, [rule(template="Mismatch", producer="^Generated.*")])
    write_json(bank_reference, [rule(template="Mismatch", producer="^Reference.*")])
    write_json(income_generated / "Match.json", [rule(template="Match")])
    write_json(income_reference / "Match.json", [rule(template="Match")])

    report_path = generated_root / "comparison_report.json"
    command = [
        sys.executable,
        str(Path(__file__).resolve().parents[2] / "scripts" / "compare_generated_rulesets.py"),
        "--generated-root",
        str(generated_root),
        "--bank-ref-dir",
        str(bank_reference.parent),
        "--income-ref-dir",
        str(income_reference),
        "--report-path",
        str(report_path),
    ]

    completed = subprocess.run(command, capture_output=True, text=True, cwd=Path(__file__).resolve().parents[2], check=False)

    assert completed.returncode == 1
    assert "bank: matched=1 identical=0 different=1" in completed.stdout
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["overall"]["different_files"] == 1
