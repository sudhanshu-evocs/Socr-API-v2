# Introduction
SOCR Revamp

# Getting Started
1.	Installation process
- See CI/CD for socr_revamp below
2.	Software dependencies
- Runtime package dependencies are defined in `pyproject.toml`; development and service dependencies are listed in `src/requirements.txt`.

# Build, Install, and Test

## Building the Python package

The package metadata and build configuration are defined in `pyproject.toml`. Use Python 3.11 or newer:

For the purpose of packaging, versioning rules, vendor installation, offline deployment, and the complete release checklist, see [PACKAGE_GENERATION.md](PACKAGE_GENERATION.md).

The recommended verified build command is:

```bash
python scripts/build_package.py
```

To build manually:

```bash
python -m pip install --upgrade build
python -m build
```

This creates the distributable artifacts in `dist/`:

- `docuverus-<version>.tar.gz` — source distribution
- `docuverus-<version>-py3-none-any.whl` — wheel distribution

To install the compiled Wheel package locally from `dist/`:

```powershell
pip install dist/docuverus-0.3.3-py3-none-any.whl
```

To install the source tarball archive:

```powershell
pip install dist/docuverus-0.3.3.tar.gz
```

To install the project in editable mode during development:

```powershell
pip install -e .
```

## Testing

Run pytest from the repository root:

```bash
pytest
```

## Local experimental SIFT comparison

The temporary OpenCV SIFT visual-template experiment lives under `experimental/sift_comparison` and is excluded from the `docuverus` package. SOCR remains authoritative; SIFT never changes `Pass`, `FDR`, or `Fail`.

To enable it for the local React/Flask development launcher:

```powershell
.\start.ps1 -EnableSift
```

The equivalent environment-variable form is `$env:ENABLE_SIFT_COMPARISON = "true"` followed by `.\start.ps1`. Restart an already-running backend after enabling the experiment; the SIFT routes are registered only at process startup.

If Docker Compose owns port 5000, enable the experiment with the local-only overlay:

```powershell
docker compose -f docker-compose.yml -f docker-compose.sift.yml up -d --build api
```

Register a known-good baseline separately before testing another document:

```powershell
python -m experimental.sift_comparison.register_baseline --template "Chase Bank" --document-type bank_statement --file "C:\path\known_good_chase.pdf"
```

Registration refuses to overwrite an existing reference. See `experimental/sift_comparison/README.md` for mappings, scoring, and removal instructions. With the feature flag absent or false, the original backend command is used and the SIFT tab is hidden.

# Contribute
Keep this file up to date if you change how things work.

# CI/CD for socr_revamp
## Docker
docker compose build
docker compose up

docker run -it socr_revamp-app bash -c "cd test_suite && pytest"

## Virtual Environments
### Creating and Activating (Windows)
```bash
python -m venv venv
venv\Scripts\activate.bat
```

## PIP and dependency management
### Installing dependencies
```bash
pip install -r src/requirements.txt
```

## Pre-commit hooks
### Installing pre-commit:
```bash
pip install pre-commit
pre-commit install
```
### Running pre-commit hooks manually on all files (for first use, or to see changes before committing):
```bash
pre-commit run --all-files
```

## Testing
### Running tests
```bash
pytest
```

### Running legacy metadata converter tests
```bash
pytest scripts/tests/test_LegacyMetadataConverter.py
```

### Converting legacy to new - step by step
* Run python3 ./scripts/convert_legacy_metadata_to_rulesets.py

### Comparing generated rulesets to canonical TemplateJson rulesets
* Run `python3 ./scripts/compare_generated_rulesets.py`
* Review the terminal summary and `scripts/generated_rulesets/comparison_report.json`

### Standardizing canonical TemplateJson formatting
* Run `python3 ./scripts/standardize_template_json.py --dry-run`
* Review the terminal summary, then rerun without `--dry-run` to rewrite `src/docuverus/RuleEvaluators/TemplateJson` into canonical diff-friendly formatting

### Applying targeted TemplateJson updates from the comparison report
* Run `python3 ./scripts/apply_ruleset_updates_from_report.py --comparison-report ./scripts/generated_rulesets/comparison_report.json --dry-run`
* Review the terminal summary and `scripts/generated_rulesets/template_update_report.json`
* Run the standardizer after applying updates if you want to reconfirm the reference corpus is still in canonical formatting
* Rerun without `--dry-run` to write targeted updates into `src/docuverus/RuleEvaluators/TemplateJson`

## Immediate TODOs
* Need to get rid of TemplateJson/Generic
* 
