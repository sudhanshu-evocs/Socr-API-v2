# Guide: Update a rule JSON in `socr-api-v2`, build the wheel, bring it into `socr-api`, and open PRs

This workflow touches two repos:

- `<workspace-root-directory>/socr-api-v2` is the source of truth for the `docuverus` package.
- `<workspace-root-directory>/socr-api` consumes that package from `vendor/`.

## 1. Start from clean branches

```bash
cd <workspace-root-directory>/socr-api-v2
git checkout -b <story-number>-rule-updates

cd <workspace-root-directory>/socr-api
git checkout -b <story-number>-rule-updates
```

## 2. Find and edit the correct rule JSON in `socr-api-v2`

The rule JSON files live here:

- Bank statements: `<workspace-root-directory>/socr-api-v2/src/docuverus/RuleEvaluators/TemplateJson/BankStatementsRuleJson`
- Earnings statements: `<workspace-root-directory>/socr-api-v2/src/docuverus/RuleEvaluators/TemplateJson/EarningStatementsRuleJson`

Edit the JSON file directly in your editor.

Quick validation after the edit:

```bash
python3 -m json.tool "src/docuverus/RuleEvaluators/TemplateJson/BankStatementsRuleJson/Bank of America.json" >/dev/null
```

If you changed formatting broadly or want canonical formatting, use the existing repo script:

```bash
python3 ./scripts/standardize_template_json.py --dry-run
```

If the dry run shows formatting fixes you want to keep:

```bash
python3 ./scripts/standardize_template_json.py
```

## 3. Run a quick test pass in `socr-api-v2` - Changing rules may cause tests to fail, and we will need to update the expectations eventually, but ensure failures are limited

At minimum, make sure the package still imports and the test suite starts cleanly.

If you do not already have a venv for this repo:

```bash
cd <workspace-root-directory>/socr-api-v2
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
pip install build
```

Run tests, if they fail, they should be minimal and related to the rules you changed before proceeding:

```bash
cd <workspace-root-directory>/socr-api-v2
pytest
```


## 4. Bump the `docuverus` version before building the wheel

The current package version is in:

- `<workspace-root-directory>/socr-api-v2/pyproject.toml`

Right now it is `0.2.4`. Bump it before building, for example to `0.2.5`.

Why this matters:

- The wheel filename changes.
- `socr-api` pins the wheel by filename in `requirements.txt`.
- A version bump makes the consumer PR explicit and avoids reinstall/cache confusion.

## 5. Build the wheel in `socr-api-v2`

From the repo root:

```bash
cd <workspace-root-directory>/socr-api-v2
python3 -m build
```

The wheel will land in `dist/`, for example:

```text
<workspace-root-directory>/socr-api-v2/dist/docuverus-0.2.5-py3-none-any.whl
```

The JSON rule files are already configured as package data in `pyproject.toml`, so building the wheel is enough. You do not need to manually copy JSON files into the wheel.

## 6. Bring the new wheel into `socr-api`

Copy the wheel into `vendor/`:

```bash
cp <workspace-root-directory>/socr-api-v2/dist/docuverus-0.2.5-py3-none-any.whl \
   <workspace-root-directory>/socr-api/vendor/
```

Now update the pinned wheel reference in:

- `<workspace-root-directory>/socr-api/requirements.txt`

## 7. Install the new wheel in `socr-api`

If you use a local venv for `socr-api`, activate it and reinstall:

```bash
cd <workspace-root-directory>/socr-api
pip install --force-reinstall ./vendor/docuverus-0.2.5-py3-none-any.whl
```

If you are only updating for the pipeline:
`<workspace-root-directory>/socr-api/Dockerfile` already copies `vendor/` and runs `pip install -r requirements.txt`, so a rebuild through the pipeline will pick up the new wheel.

## 8. Commit the changes carefully

### In `socr-api-v2`

Commit only:

- The rule JSON you changed
- `pyproject.toml`
- Any intentional test updates

Example:

```bash
cd <workspace-root-directory>/socr-api-v2
git add src/docuverus/RuleEvaluators/TemplateJson/.../YourTemplate.json pyproject.toml
git commit -m "Update template rule for YourTemplate"
```

### In `socr-api`

Commit only:

- The new wheel in `vendor/`
- The `requirements.txt` wheel reference

Example:

```bash
cd <workspace-root-directory>/socr-api
git add vendor/docuverus-0.2.5-py3-none-any.whl requirements.txt
git commit -m "Update vendored docuverus wheel to 0.2.5"
```

If you want to keep `vendor/` tidy, you can also remove the old wheel and commit that deletion, but only if the repo expects one active wheel version at a time.

## 9. Push and open the PRs

Push both branches:

```bash
git -C <workspace-root-directory>/socr-api-v2 push -u origin <story-number>-rule-updates
git -C <workspace-root-directory>/socr-api push -u origin <story-number>-rule-updates
```

Open:

1. A `socr-api-v2` PR with the rule change and version bump.
2. A `socr-api` PR that references the `socr-api-v2` PR and says which `docuverus` version it vendors.

Good PR notes:

- What template/rule changed
- Why it changed
- Which tests you ran
- The new `docuverus` version
- The exact wheel filename you vendored into `socr-api`

## Quick checklist

- Edited the right JSON file in `socr-api-v2`
- Validated JSON syntax
- Bumped `docuverus` version in `pyproject.toml`
- Built the wheel with `python3 -m build`
- Copied the new wheel into `socr-api/vendor/`
- Updated the pinned wheel line in `socr-api/requirements.txt`
- Opened the source PR and consumer PR
