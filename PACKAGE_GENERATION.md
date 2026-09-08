# Docuverus Package Generation and Release Guide

## Main motive

The `docuverus` package separates the document-validation engine from the SOCR API application that consumes it.

Without a package, the SOCR API must copy validation source files directly into its own repository. That makes it difficult to identify the deployed engine version, reuse the engine in another service, roll back a change, or prove that staging and production use identical code.

Packaging provides:

- **A versioned contract:** SOCR API can declare an exact version such as `docuverus==0.3.3`.
- **Independent releases:** validation rules can be built and tested separately from the consuming API.
- **Reusability:** other Python services can use the same metadata-validation implementation.
- **Repeatable deployment:** the same wheel tested in staging can be promoted to production.
- **Simple rollback:** the vendor reference can be changed back to a previously tested wheel.
- **Resource safety:** template and utility JSON files are shipped as package data instead of relying on repository-relative paths.

The package is not intended to bundle the React UI, PDF test fixtures, development tools, or an entire Python environment.

## Package contents

The build configuration is in `pyproject.toml`. It packages the Python modules under `src/docuverus` and includes:

- Metadata extraction and validation APIs
- Fraud and template detection
- Rule evaluators
- Bank statement and earnings statement template JSON files
- Utility JSON resources

The package currently requires Python 3.11 or newer. Its runtime dependencies are declared in `pyproject.toml`.

## Generated artifacts

A release produces two files:

```text
dist/
├── docuverus-<version>-py3-none-any.whl
└── docuverus-<version>.tar.gz
```

Use the `.whl` file for SOCR API installation. It is the built, directly installable artifact.

The `.tar.gz` file is a source distribution. It is useful as a fallback or for rebuilding the wheel, but it is not a normal ZIP archive and should not be manually extracted into the SOCR API.

## Build workflow

### 1. Choose the version

Update the project version in `pyproject.toml` before building a changed release:

```toml
[project]
name = "docuverus"
version = "0.3.4"
```

Version guidance:

- `0.3.3` to `0.3.4`: fixes and rule/template corrections
- `0.3.4` to `0.4.0`: backward-compatible features
- `1.x` to `2.0.0`: incompatible public API changes

Never publish different code under an existing version. If a `0.3.4` candidate fails, fix it and generate `0.3.5`.

### 2. Run the release helper

From the repository root:

```powershell
python scripts/build_package.py
```

The helper:

1. Reads the package name and version from `pyproject.toml`.
2. Runs the test suite unless `--skip-tests` is specified.
3. Builds both the wheel and source distribution.
4. Confirms the wheel contains Python modules and packaged JSON resources.
5. Writes a version-specific SHA-256 checksum file into `dist/`.

For a build-only development check:

```powershell
python scripts/build_package.py --skip-tests
```

The normal release path should not skip tests.

### 3. Inspect the result

For version `0.3.4`, expect:

```text
dist/docuverus-0.3.4-py3-none-any.whl
dist/docuverus-0.3.4.tar.gz
dist/SHA256SUMS-0.3.4.txt
```

The checksum allows teams to confirm that staging and production received the exact same files.

## Installing in the SOCR API vendor folder

Copy the current wheel into the SOCR API repository:

```text
socr-api/
├── requirements.txt
└── vendor/
    └── docuverus-0.3.4-py3-none-any.whl
```

Reference that exact artifact from the SOCR API `requirements.txt`:

```text
./vendor/docuverus-0.3.4-py3-none-any.whl
```

Install it with:

```powershell
python -m pip install -r requirements.txt
```

Do not place multiple active versions in the vendor folder. An older wheel may be retained in release storage, but the consuming repository should clearly reference only one version.

## Offline vendor installation

The Docuverus wheel does not embed third-party libraries. If the deployment environment cannot access PyPI, download the wheel and all its dependencies into the vendor directory:

```powershell
python -m pip download --dest .\vendor .\vendor\docuverus-0.3.4-py3-none-any.whl
```

Install from that directory without network access:

```powershell
python -m pip install --no-index --find-links=.\vendor -r requirements.txt
```

Download dependencies for the same operating system, CPU architecture, and Python version used by the deployment image.

## Consumer verification

After installation in the SOCR API environment, run:

```powershell
python -m pip show docuverus
python -m pip check
python -c "from docuverus.api import get_template_names; print(len(get_template_names()))"
```

Then run an integration test using a known PDF:

```python
from docuverus.api import validate_metadata

with open("known-document.pdf", "rb") as document:
    result = validate_metadata(document.read(), "Expected Template")

print(result["final_validation_results"])
```

## Staging and production

Use this promotion sequence:

```text
Build once
  → install in SOCR API
  → test locally and in CI
  → deploy the same artifact to staging
  → run API and PDF integration checks
  → promote the same artifact/container to production
```

Do not rebuild between staging and production. A rebuild creates another artifact, even when the version label is unchanged. Promote the tested wheel or the exact container image that contains it.

## Release checklist

- [ ] Package version was incremented in `pyproject.toml`.
- [ ] Runtime dependency changes were reviewed for SOCR API conflicts.
- [ ] Automated tests passed.
- [ ] Wheel and source distribution were generated.
- [ ] Wheel contains template and utility JSON files.
- [ ] Checksum was recorded.
- [ ] SOCR API vendor reference points to the new wheel.
- [ ] `pip show docuverus` reports the expected version.
- [ ] `pip check` reports no broken dependencies.
- [ ] Known valid and suspicious PDFs return the expected results.
- [ ] Staging deployment passed before production promotion.

## Important dependency note

`pyproject.toml` is the source of truth for package runtime dependencies. This repository's `src/requirements.txt` also contains service and development dependencies and may temporarily use different versions. Before releasing, reconcile incompatible pins so installing the wheel does not unexpectedly upgrade or downgrade the SOCR API environment.
