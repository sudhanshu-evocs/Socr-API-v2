#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent

from src.TemplateJsonCanonicalizer import TemplateJsonCanonicalizer


DEFAULT_TEMPLATE_JSON_ROOT = SCRIPT_DIR.parent / "src" / "docuverus" / "RuleEvaluators" / "TemplateJson"


def parse_args():
    parser = argparse.ArgumentParser(description="Standardize TemplateJson formatting for stable diffs.")
    parser.add_argument(
        "--template-json-root",
        default=str(DEFAULT_TEMPLATE_JSON_ROOT),
        help="Root directory containing TemplateJson JSON files",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report files that would change without rewriting them")
    parser.add_argument("--verbose", action="store_true", help="Enable info-level logging")
    return parser.parse_args()


def configure_logging(verbose):
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, format="%(levelname)s: %(message)s")


def collect_changes(root):
    canonicalizer = TemplateJsonCanonicalizer()
    root_path = Path(root)
    json_files = sorted(root_path.rglob("*.json"))
    pending_changes = []

    for path in json_files:
        current_text = path.read_text(encoding="utf-8")
        canonical_text = canonicalizer.dumps_rules(canonicalizer.load_rules(path), sort_rules=True)
        changed = current_text != canonical_text
        pending_changes.append(
            {
                "path": path,
                "changed": changed,
                "canonical_text": canonical_text,
            }
        )
    return pending_changes


def print_summary(root, pending_changes, dry_run):
    changed_paths = [item["path"] for item in pending_changes if item["changed"]]
    action = "would_change" if dry_run else "changed"
    print(f"root={Path(root)}")
    print(f"files_scanned={len(pending_changes)}")
    print(f"{action}_files={len(changed_paths)}")
    for path in changed_paths:
        print(f"  {action.upper()} {path}")


def main():
    args = parse_args()
    configure_logging(args.verbose)

    try:
        pending_changes = collect_changes(args.template_json_root)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error={exc}")
        return 1

    if not args.dry_run:
        for item in pending_changes:
            if item["changed"]:
                item["path"].write_text(item["canonical_text"], encoding="utf-8")

    print_summary(args.template_json_root, pending_changes, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
