"""Register a known-good page-one reference for local testing."""

from __future__ import annotations

import argparse
from pathlib import Path

from .baseline_manager import BaselineManager
from .config import SiftConfig


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, help="Explicit SOCR template name, for example 'Chase Bank'.")
    parser.add_argument("--document-type", required=True, choices=("bank_statement", "paystub"))
    parser.add_argument("--file", required=True, type=Path, help="Known-good PDF. This is separate from normal document upload.")
    arguments = parser.parse_args()

    if not arguments.file.is_file() or arguments.file.suffix.casefold() != ".pdf":
        parser.error("--file must identify an existing PDF")
    path = BaselineManager(SiftConfig.from_environment()).register_pdf(
        arguments.template,
        arguments.document_type,
        arguments.file.read_bytes(),
    )
    print(f"Registered baseline without overwriting an existing reference: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
