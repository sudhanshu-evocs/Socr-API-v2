# AGENTS.md

Quick reference for Codex agents working in this repo.

## Project snapshot
- Python 3.12 Flask service under `src/docuverus` for document metadata validation, rule evaluators, fraud detection, and template detection.
- Large JSON ruleset library under `src/docuverus/RuleEvaluators/TemplateJson`.
- Main pytest suite lives in `test_suite`, with many PDFs under `test_documents`.
- Frontend is a Create React App in `react-app`.

## Repo layout
- `src/docuverus/app.py`: Flask entrypoint.
- `src/docuverus/RuleEvaluators`: rule engine implementations.
- `src/docuverus/RuleEvaluators/TemplateJson`: template-specific metadata rules.
- `src/docuverus/FraudDetector`: fraud detection and metadata extraction.
- `test_suite`: primary pytest suite.
- `test_documents`: PDF fixtures used by tests.
- `react-app`: CRA UI.
- `scripts`: helper scripts, including Azure blob utilities and legacy metadata conversion tooling.

## Dev setup and dependencies
- Python deps: `pip install -r src/requirements.txt`.
- React deps: `npm install` in `react-app`.
- Docker: `docker compose build` and `docker compose up`.

## Running
- API: `python src/docuverus/app.py` (expects `PYTHONPATH` to include `src`).
- Tests (per README):
  - Repo root:
    - `pytest`
  - `set PYTHONPATH=%PYTHONPATH%;%CD%\src;%CD%\test_suite`
  - `cd test_suite`
  - `pytest`
  - macOS/Linux:
    - `export PYTHONPATH="$PYTHONPATH:$(pwd)/src:$(pwd)/test_suite"`
    - `cd test_suite`
    - `pytest`
  - Legacy metadata converter tests:
    - `pytest scripts/tests/test_LegacyMetadataConverter.py`

## Coding standards
- Python 3.12+.
- Format with Black, line length 140 (`pyproject.toml`).
- isort uses Black profile.
- Keep dependency changes in `src/requirements.txt`.
- Pre-commit is configured in `.pre-commit-config.yaml`; use `pre-commit run --all-files` when making broad changes.

## Common workflows
- Run a single test file:
  - `cd test_suite`
  - `pytest docuverus/Utils/test_PDFUtilities.py`
- Run a single test case:
  - `cd test_suite`
  - `pytest docuverus/Utils/test_PDFUtilities.py -k test_extract_xref_fonts_works_for_citizens_bank_pdf`

## Slow/Skipped tests
- Examples of longer running or experimental tests are marked with `@pytest.mark.skip()`:
  - `test_suite/docuverus/Models/test_TemplateRuleSetModel.py`
  - `test_suite/docuverus/Utils/test_PDFUtilities.py`
  - `test_suite/docuverus/Utils/test_DataUtils.py`
  - `test_suite/docuverus/RuleEvaluators/test_FontRuleEvaluator.py`
  - `test_suite/docuverus/FraudDetector/test_FraudDetector.py`
- If you unskip these, expect heavier PDF processing and filesystem traversal over `test_documents`.

## Deep review workflow
- For a deep code review, prioritize findings over summaries: list bugs, regressions, security risks, and missing-test coverage first, ordered by severity with file/line references.
- Review in this order:
  - Flask entrypoints and workflow wiring: `src/docuverus/app.py` and `src/docuverus/Workflow`
  - Rule engine core: `src/docuverus/RuleEvaluators`, especially `RuleSetFactory`, `CompositeRuleEvaluator`, `SingleValueRuleEvaluator`, `DateRuleEvaluator`, `FileSizeRuleEvaluator`, and `FontRuleEvaluator`
  - Detection pipeline: `src/docuverus/FraudDetector` and `src/docuverus/TemplateDetector`
  - Template JSON corpus under `src/docuverus/RuleEvaluators/TemplateJson`
  - Utilities and tests under `src/docuverus/Utils` and `test_suite`
  - Scripts in `scripts`
- Treat `scripts/generated_rulesets` as generated output. Review the generator and fixtures before treating generated JSON diffs as authoritative source changes.
- Start a review with `pytest` from the repo root, then rerun targeted files for any subsystem you inspect more deeply.
- The React app in `react-app` is small and should usually be a lower-priority sanity pass unless the change touches frontend/backend contracts directly.

## Notes for changes
- Rule changes often require edits in `src/docuverus/RuleEvaluators/TemplateJson` and related evaluators in `src/docuverus/RuleEvaluators`.
- PDF fixtures in `test_documents` are large; avoid editing unless specifically required.
- Keep README updated if workflows change.
