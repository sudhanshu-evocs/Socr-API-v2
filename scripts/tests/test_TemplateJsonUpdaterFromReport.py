import json
import subprocess
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from src.GeneratedRulesetComparator import GeneratedRulesetComparator
from src.TemplateJsonUpdaterFromReport import TemplateJsonUpdaterFromReport


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


def build_report(tmp_path, bank_generated_files=None, income_generated_files=None, bank_reference_files=None, income_reference_files=None):
    generated_root = tmp_path / "generated"
    bank_generated_dir = generated_root / "BankStatementsRuleJson"
    income_generated_dir = generated_root / "EarningStatementsRuleJson"
    bank_reference_dir = tmp_path / "refs" / "BankStatementsRuleJson"
    income_reference_dir = tmp_path / "refs" / "EarningStatementsRuleJson"

    for directory, files in (
        (bank_generated_dir, bank_generated_files or {}),
        (income_generated_dir, income_generated_files or {}),
        (bank_reference_dir, bank_reference_files or {}),
        (income_reference_dir, income_reference_files or {}),
    ):
        for file_name, payload in files.items():
            write_json(directory / file_name, payload)

    comparator = GeneratedRulesetComparator(
        generated_root=generated_root,
        bank_reference_dir=bank_reference_dir,
        income_reference_dir=income_reference_dir,
        report_path=generated_root / "comparison_report.json",
    )
    comparator.compare()

    return {
        "comparison_report_path": generated_root / "comparison_report.json",
        "generated_root": generated_root,
        "bank_reference_dir": bank_reference_dir,
        "income_reference_dir": income_reference_dir,
    }


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_updater_targets_existing_file_by_template_name_without_renaming(tmp_path):
    env = build_report(
        tmp_path,
        bank_generated_files={"Ally.json": [rule(template="Ally")]},
        bank_reference_files={"Ally Bank.json": [rule(template="Ally")]},
    )

    updater = TemplateJsonUpdaterFromReport(
        comparison_report_path=env["comparison_report_path"],
        bank_reference_dir=env["bank_reference_dir"],
        income_reference_dir=env["income_reference_dir"],
        generated_root=env["generated_root"],
    )
    report = updater.apply()

    bank_actions = report["datasets"]["bank"]["file_actions"]
    assert bank_actions[0]["reference_file"] == "Ally Bank.json"
    assert not (env["bank_reference_dir"] / "Ally.json").exists()


def test_updater_targets_existing_file_by_normalized_template_name(tmp_path):
    env = build_report(
        tmp_path,
        bank_generated_files={"ABCO FCU.json": [rule(template="ABCO FCU")]},
        bank_reference_files={"ABCOFCU.json": [rule(template="ABCOFCU")]},
    )

    updater = TemplateJsonUpdaterFromReport(
        comparison_report_path=env["comparison_report_path"],
        bank_reference_dir=env["bank_reference_dir"],
        income_reference_dir=env["income_reference_dir"],
        generated_root=env["generated_root"],
    )
    report = updater.apply()

    bank_actions = report["datasets"]["bank"]["file_actions"]
    assert bank_actions[0]["reference_file"] == "ABCOFCU.json"
    assert report["datasets"]["bank"]["summary"]["created_new_files"] == 0


def test_updater_fills_missing_scalars_and_normalizes_present_present_dates(tmp_path):
    env = build_report(
        tmp_path,
        bank_generated_files={
            "Gap.json": [
                rule(
                    template="Gap",
                    producer="^Generated.*",
                    creator="^Generated Creator.*",
                    file_size={"algorithm": "Constant", "min": 10, "max": 20},
                    created_state="Present",
                    modified={"state": "Present"},
                )
            ]
        },
        bank_reference_files={
            "Gap.json": [
                rule(
                    template="Gap",
                    producer="",
                    creator="",
                    file_size={"min": 10, "max": 20},
                    created_state="",
                    modified={},
                )
            ]
        },
    )

    updater = TemplateJsonUpdaterFromReport(
        comparison_report_path=env["comparison_report_path"],
        bank_reference_dir=env["bank_reference_dir"],
        income_reference_dir=env["income_reference_dir"],
        generated_root=env["generated_root"],
    )
    report = updater.apply()
    updated = load_json(env["bank_reference_dir"] / "Gap.json")[0]

    assert updated["producer"]["name"] == "^Generated.*"
    assert updated["creator"]["name"] == "^Generated Creator.*"
    assert updated["dates"]["created"]["state"] == "Present"
    assert updated["dates"]["modified"]["state"] == "Equal"
    assert updated["file_size"]["algorithm"] == "Constant"
    assert report["datasets"]["bank"]["summary"]["filled_scalar_gaps"] >= 5


def test_updater_preserves_typed_reference_fonts_for_paired_rules(tmp_path):
    env = build_report(
        tmp_path,
        income_generated_files={
            "Fonts.json": [
                rule(
                    template="Fonts",
                    required_fonts=[font("Helvetica", type_="", encoding=""), font("Times-Roman", type_="", encoding="")],
                )
            ]
        },
        income_reference_files={
            "Fonts.json": [
                rule(
                    template="Fonts",
                    required_fonts=[font("Helvetica", type_="Type1", encoding="WinAnsiEncoding"), font("Times-Roman", type_="Type1")],
                )
            ]
        },
    )

    updater = TemplateJsonUpdaterFromReport(
        comparison_report_path=env["comparison_report_path"],
        bank_reference_dir=env["bank_reference_dir"],
        income_reference_dir=env["income_reference_dir"],
        generated_root=env["generated_root"],
    )
    updater.apply()
    updated = load_json(env["income_reference_dir"] / "Fonts.json")[0]

    assert updated["fonts"]["required_fonts"][0]["type"] == "Type1"
    assert updated["fonts"]["required_fonts"][0]["encoding"] == "WinAnsiEncoding"
    assert updated["fonts"]["required_fonts"][1]["type"] == "Type1"


def test_updater_appends_generated_only_rule_and_backfills_exact_font_metadata(tmp_path):
    env = build_report(
        tmp_path,
        income_generated_files={
            "Append.json": [
                rule(
                    template="Append",
                    producer="^A.*",
                    required_fonts=[font("Helvetica", type_="", encoding="")],
                ),
                rule(
                    template="Append",
                    producer="^Z.*",
                    required_fonts=[font("Helvetica", type_="", encoding="")],
                    created_state="Present",
                    modified={"state": "Present"},
                ),
            ]
        },
        income_reference_files={
            "Append.json": [
                rule(
                    template="Append",
                    producer="^A.*",
                    required_fonts=[font("Helvetica", type_="Type1", encoding="WinAnsiEncoding")],
                )
            ]
        },
    )

    updater = TemplateJsonUpdaterFromReport(
        comparison_report_path=env["comparison_report_path"],
        bank_reference_dir=env["bank_reference_dir"],
        income_reference_dir=env["income_reference_dir"],
        generated_root=env["generated_root"],
    )
    report = updater.apply()
    updated_rules = load_json(env["income_reference_dir"] / "Append.json")
    appended = next(rule for rule in updated_rules if rule["producer"]["name"] == "^Z.*")

    assert len(updated_rules) == 2
    assert appended["fonts"]["required_fonts"][0]["type"] == "Type1"
    assert appended["fonts"]["required_fonts"][0]["encoding"] == "WinAnsiEncoding"
    assert appended["dates"]["modified"]["state"] == "Equal"
    assert report["datasets"]["income"]["summary"]["appended_rules"] == 1


def test_updater_keeps_and_flags_reference_only_rules(tmp_path):
    env = build_report(
        tmp_path,
        bank_generated_files={"Keep.json": [rule(template="Keep", producer="^A.*")]},
        bank_reference_files={
            "Keep.json": [
                rule(template="Keep", producer="^A.*"),
                rule(template="Keep", producer="^Z.*"),
            ]
        },
    )

    updater = TemplateJsonUpdaterFromReport(
        comparison_report_path=env["comparison_report_path"],
        bank_reference_dir=env["bank_reference_dir"],
        income_reference_dir=env["income_reference_dir"],
        generated_root=env["generated_root"],
    )
    report = updater.apply()
    updated_rules = load_json(env["bank_reference_dir"] / "Keep.json")

    assert len(updated_rules) == 2
    flagged = report["datasets"]["bank"]["file_actions"][0]["flagged_reference_only_rules"]
    assert len(flagged) == 1
    assert flagged[0]["producer"]["name"] == "^Z.*"


def test_updater_creates_new_file_for_unknown_template(tmp_path):
    env = build_report(
        tmp_path,
        income_generated_files={"Brand New.json": [rule(template="Brand/New Template", producer="^New.*")]},
        income_reference_files={},
    )

    updater = TemplateJsonUpdaterFromReport(
        comparison_report_path=env["comparison_report_path"],
        bank_reference_dir=env["bank_reference_dir"],
        income_reference_dir=env["income_reference_dir"],
        generated_root=env["generated_root"],
    )
    report = updater.apply()

    created_path = env["income_reference_dir"] / "Brand_New Template.json"
    assert created_path.exists()
    assert load_json(created_path)[0]["template"]["name"] == "Brand/New Template"
    assert report["datasets"]["income"]["summary"]["created_new_files"] == 1


def test_updater_dry_run_writes_only_report(tmp_path):
    env = build_report(
        tmp_path,
        bank_generated_files={"DryRun.json": [rule(template="DryRun", producer="^Generated.*")]},
        bank_reference_files={"DryRun.json": [rule(template="DryRun", producer="")]},
    )

    before = load_json(env["bank_reference_dir"] / "DryRun.json")
    updater = TemplateJsonUpdaterFromReport(
        comparison_report_path=env["comparison_report_path"],
        bank_reference_dir=env["bank_reference_dir"],
        income_reference_dir=env["income_reference_dir"],
        generated_root=env["generated_root"],
        dry_run=True,
    )
    report = updater.apply()

    after = load_json(env["bank_reference_dir"] / "DryRun.json")
    assert before == after
    assert report["dry_run"] is True
    assert (env["generated_root"] / "template_update_report.json").exists()


def test_updater_cli_reports_actions(tmp_path):
    env = build_report(
        tmp_path,
        income_generated_files={"Cli.json": [rule(template="Cli", producer="^Generated.*")]},
        income_reference_files={"Cli.json": [rule(template="Cli", producer="")]},
    )

    report_path = env["generated_root"] / "template_update_report.json"
    command = [
        sys.executable,
        str(Path(__file__).resolve().parents[2] / "scripts" / "apply_ruleset_updates_from_report.py"),
        "--comparison-report",
        str(env["comparison_report_path"]),
        "--generated-root",
        str(env["generated_root"]),
        "--bank-ref-dir",
        str(env["bank_reference_dir"]),
        "--income-ref-dir",
        str(env["income_reference_dir"]),
        "--out-report",
        str(report_path),
        "--dry-run",
    ]

    completed = subprocess.run(command, capture_output=True, text=True, cwd=Path(__file__).resolve().parents[2], check=False)

    assert completed.returncode == 0
    assert "dry_run=True" in completed.stdout
    assert "income: updated_existing_files=1" in completed.stdout
    assert report_path.exists()
