#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent

from src.LegacyMetadataConverter import LegacyMetadataConverter


DEFAULT_BANK_SOURCE = Path("/Users/jmruzik/workspace/socr-api/config/BankMetadata.json")
DEFAULT_INCOME_SOURCE = Path("/Users/jmruzik/workspace/socr-api/config/Metadata.json")
DEFAULT_BANK_REF_DIR = Path(
    "/Users/jmruzik/workspace/socr-api-v2/src/docuverus/RuleEvaluators/TemplateJson/BankStatementsRuleJson"
)
DEFAULT_INCOME_REF_DIR = Path(
    "/Users/jmruzik/workspace/socr-api-v2/src/docuverus/RuleEvaluators/TemplateJson/EarningStatementsRuleJson"
)
DEFAULT_OUT_DIR = Path("/Users/jmruzik/workspace/socr-api-v2/scripts/generated_rulesets")


def parse_args():
    parser = argparse.ArgumentParser(description="Convert socr-api legacy metadata JSON files into socr_revamp rule-set JSON files.")
    parser.add_argument("--bank-source", default=str(DEFAULT_BANK_SOURCE), help="Path to BankMetadata.json")
    parser.add_argument("--income-source", default=str(DEFAULT_INCOME_SOURCE), help="Path to Metadata.json")
    parser.add_argument("--bank-ref-dir", default=str(DEFAULT_BANK_REF_DIR), help="Bank template reference directory")
    parser.add_argument("--income-ref-dir", default=str(DEFAULT_INCOME_REF_DIR), help="Income template reference directory")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for generated rule-set JSON files")
    parser.add_argument("--report-path", default=None, help="Optional explicit report output path. Defaults to <out-dir>/conversion_report.json")
    parser.add_argument("--verbose", action="store_true", help="Enable info-level logging")
    return parser.parse_args()


def configure_logging(verbose):
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, format="%(levelname)s: %(message)s")


def main():
    args = parse_args()
    configure_logging(args.verbose)

    converter = LegacyMetadataConverter(
        bank_reference_dir=args.bank_ref_dir,
        income_reference_dir=args.income_ref_dir,
        out_dir=args.out_dir,
        report_path=args.report_path,
        verbose=args.verbose,
    )
    report = converter.convert_from_file_paths(
        bank_source=args.bank_source,
        income_source=args.income_source,
    )
    print(json.dumps(report["overall"], indent=4))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        logging.error("Conversion failed: %s", exc)
        raise SystemExit(1)
