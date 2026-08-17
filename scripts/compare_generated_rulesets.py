#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent

from src.GeneratedRulesetComparator import GeneratedRulesetComparator


DEFAULT_GENERATED_ROOT = Path("/Users/jmruzik/workspace/socr-api-v2/scripts/generated_rulesets")
DEFAULT_BANK_REF_DIR = Path(
    "/Users/jmruzik/workspace/socr-api-v2/src/docuverus/RuleEvaluators/TemplateJson/BankStatementsRuleJson"
)
DEFAULT_INCOME_REF_DIR = Path(
    "/Users/jmruzik/workspace/socr-api-v2/src/docuverus/RuleEvaluators/TemplateJson/EarningStatementsRuleJson"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Compare generated legacy-converted rulesets with canonical TemplateJson rulesets.")
    parser.add_argument("--generated-root", default=str(DEFAULT_GENERATED_ROOT), help="Root directory containing generated rulesets")
    parser.add_argument("--bank-ref-dir", default=str(DEFAULT_BANK_REF_DIR), help="Bank template reference directory")
    parser.add_argument("--income-ref-dir", default=str(DEFAULT_INCOME_REF_DIR), help="Income template reference directory")
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional explicit report output path. Defaults to <generated-root>/comparison_report.json",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable info-level logging")
    return parser.parse_args()


def configure_logging(verbose):
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, format="%(levelname)s: %(message)s")


def print_summary(report):
    for dataset_name in ("bank", "income"):
        dataset = report["datasets"][dataset_name]
        summary = dataset["summary"]
        print(
            f"{dataset_name}: matched={summary['matched_files']} identical={summary['identical_files']} "
            f"different={summary['different_files']} generated_only={summary['generated_only_files']} "
            f"reference_only={summary['reference_only_files']} ambiguous={summary['ambiguous_matches']}"
        )
        for matched_file in dataset["matched_files"]:
            if matched_file["status"] == "different":
                print(
                    f"  DIFF {matched_file['generated_file']} vs {matched_file['reference_file']}: "
                    f"changed_rules={matched_file['changed_rules']} "
                    f"generated_only_rules={len(matched_file['generated_only_rules'])} "
                    f"reference_only_rules={len(matched_file['reference_only_rules'])}"
                )
        for file_name in dataset["generated_only_files"]:
            print(f"  GENERATED_ONLY {file_name}")
        for file_name in dataset["reference_only_files"]:
            print(f"  REFERENCE_ONLY {file_name}")
        for ambiguous in dataset["ambiguous_matches"]:
            print(
                f"  AMBIGUOUS normalized_key={ambiguous['normalized_key']} "
                f"generated={json.dumps(ambiguous['generated_files'])} "
                f"reference={json.dumps(ambiguous['reference_files'])}"
            )


def main():
    args = parse_args()
    configure_logging(args.verbose)

    comparator = GeneratedRulesetComparator(
        generated_root=args.generated_root,
        bank_reference_dir=args.bank_ref_dir,
        income_reference_dir=args.income_ref_dir,
        report_path=args.report_path,
    )
    report = comparator.compare()
    print_summary(report)

    overall = report["overall"]
    has_differences = any(
        overall[key] > 0
        for key in (
            "different_files",
            "generated_only_files",
            "reference_only_files",
            "ambiguous_matches",
        )
    )
    return 1 if has_differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
