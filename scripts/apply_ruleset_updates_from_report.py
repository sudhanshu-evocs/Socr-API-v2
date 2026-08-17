#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent

from src.TemplateJsonUpdaterFromReport import TemplateJsonUpdaterFromReport


DEFAULT_COMPARISON_REPORT = Path("/Users/jmruzik/workspace/socr-api-v2/scripts/generated_rulesets/comparison_report.json")
DEFAULT_GENERATED_ROOT = Path("/Users/jmruzik/workspace/socr-api-v2/scripts/generated_rulesets")
DEFAULT_BANK_REF_DIR = Path(
    "/Users/jmruzik/workspace/socr-api-v2/src/docuverus/RuleEvaluators/TemplateJson/BankStatementsRuleJson"
)
DEFAULT_INCOME_REF_DIR = Path(
    "/Users/jmruzik/workspace/socr-api-v2/src/docuverus/RuleEvaluators/TemplateJson/EarningStatementsRuleJson"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Apply targeted TemplateJson updates from a comparison_report.json file.")
    parser.add_argument(
        "--comparison-report",
        default=str(DEFAULT_COMPARISON_REPORT),
        help="Path to comparison_report.json",
    )
    parser.add_argument("--generated-root", default=None, help="Optional override for generated rulesets root")
    parser.add_argument("--bank-ref-dir", default=str(DEFAULT_BANK_REF_DIR), help="Bank template reference directory")
    parser.add_argument("--income-ref-dir", default=str(DEFAULT_INCOME_REF_DIR), help="Income template reference directory")
    parser.add_argument(
        "--out-report",
        default=None,
        help="Optional explicit updater report path. Defaults to <generated-root>/template_update_report.json",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute and report actions without writing TemplateJson files")
    parser.add_argument("--verbose", action="store_true", help="Enable info-level logging")
    return parser.parse_args()


def configure_logging(verbose):
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, format="%(levelname)s: %(message)s")


def print_summary(report):
    print(f"dry_run={report['dry_run']}")
    for dataset_name in ("bank", "income"):
        dataset = report["datasets"][dataset_name]
        summary = dataset["summary"]
        print(
            f"{dataset_name}: updated_existing_files={summary['updated_existing_files']} "
            f"created_new_files={summary['created_new_files']} appended_rules={summary['appended_rules']} "
            f"filled_scalar_gaps={summary['filled_scalar_gaps']} "
            f"flagged_reference_only_rules={summary['flagged_reference_only_rules']} "
            f"files_written={summary['files_written']}"
        )
        for action in dataset["file_actions"]:
            print(
                f"  {action['action'].upper()} template={action['template_name']} "
                f"reference_file={action['reference_file']} appended_rules={action['appended_rules']} "
                f"filled_scalar_gaps={action['filled_scalar_gaps']}"
            )
        for flagged in dataset["reference_only_flags"]:
            print(
                f"  FLAG_REFERENCE_ONLY reference_file={flagged['reference_file']} "
                f"templates={flagged['flagged_reference_only_rules']}"
            )


def main():
    args = parse_args()
    configure_logging(args.verbose)

    updater = TemplateJsonUpdaterFromReport(
        comparison_report_path=args.comparison_report,
        bank_reference_dir=args.bank_ref_dir,
        income_reference_dir=args.income_ref_dir,
        generated_root=args.generated_root,
        out_report=args.out_report,
        dry_run=args.dry_run,
    )
    report = updater.apply()
    print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
