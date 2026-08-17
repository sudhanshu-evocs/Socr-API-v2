# SOCR API v2 Architecture

## Scope and source of truth

This document describes the architecture currently implemented in `socr-api-v2` as of 2026-07-29. The Python source and automated tests are authoritative. The supplied diagram, `/Users/jmruzik/Downloads/Metadata Logic Workflow 2026.png`, is treated as supplementary historical context and is called out where it differs from the code.

The repository is a Python 3.12+ Flask service for PDF metadata validation and fraud-oriented rule evaluation. It also contains a small Create React App client, a packaged rule corpus, PDF utilities, and maintenance scripts for converting and updating rules.

The implemented request path is:

```text
HTTP/React client
  -> Flask route
  -> public Python API
  -> PDF metadata extraction
  -> packaged rule-set loading
  -> composite rule evaluation
  -> FraudDetector result classification
  -> JSON response
```

The repository does not currently implement database persistence, OCR/read-data extraction, document-type identification, or automatic template identification as services.

## Runtime and deployment architecture

### Python service

- `src/docuverus/app.py` creates the Flask application, enables CORS, and exposes the HTTP routes.
- The development entrypoint runs on `0.0.0.0:5000`.
- `docker-compose.yml` builds the service and maps host port 5000 to container port 5000.
- `Dockerfile` uses `python:3.12-slim`, copies `src`, `test_suite`, and `test_documents`, installs `src/requirements.txt`, sets `PYTHONPATH=/app/src`, and runs `src/docuverus/app.py`.
- Package metadata and runtime dependencies are defined in `pyproject.toml`. Packaged JSON rules and utility JSON lists are included as package data.

### React client

`react-app/src/App.js` is a manual validation UI. It:

1. Loads template names from `GET http://localhost:5000/template_names`.
2. Sends the selected PDF and caller-selected template to `POST /validate_metadata`.
3. Displays the returned JSON.
4. Can send a selected font to `POST /highlight_fonts` to receive a highlighted PDF byte response.

`react-app/src/components/FileUpload.js` is an older upload component that targets `/upload`, a route not implemented by the Flask service and not used by the current `App` component.

## Public interfaces

### `POST /validate_metadata`

Implemented in `src/docuverus/app.py::upload_file`.

Expected multipart fields:

- `file`: uploaded PDF bytes.
- `template`: caller-supplied template name.

The route validates that both fields exist and that a filename was supplied. It delegates to `docuverus.api.validate_metadata(file_bytes, template_name)` and returns the resulting dictionary as JSON with HTTP 200. Missing file/template inputs return HTTP 400 with an error message.

The caller supplies the template. The route does not call `TemplateDetector`, infer a document type, or select a template automatically.

### `GET /template_names`

Implemented in `src/docuverus/app.py::template_names`. It calls `docuverus.api.get_template_names()` and returns a sorted JSON list of template names discovered from the packaged rule directories.

### `POST /highlight_fonts`

Implemented in `src/docuverus/app.py::highlight_fonts`. It accepts uploaded PDF bytes and a `fonts` value, calls `PDFUtilities.highlight_usages_of_fonts_in_byte_representation_of_pdf`, and returns the resulting PDF bytes. The route does not validate that either multipart field is present before access.

### `GET /api`

Returns the health-style response `{"message": "Hello, World!"}`. It is not part of the metadata validation pipeline.

### Python API

`src/docuverus/api.py` exposes two primary functions:

- `validate_metadata(pdf_bytes, template_name, rule_packages=None) -> dict`
  - Builds a `RuleSetFactory` for the bank-statement and earnings-statement packages.
  - Builds a `CompositeRuleEvaluator` for the requested template.
  - Builds a `FraudDetector`.
  - Extracts metadata from the bytes.
  - Returns the detector’s validation-result dictionary.
- `get_template_names(rule_packages=None) -> list[str]`
  - Returns sorted names from the configured rule packages.

## Implemented metadata validation flow

### 1. Route and API construction

`/validate_metadata` reads the uploaded stream into memory. `api.validate_metadata` creates the rule factory, evaluator, and detector for the caller-provided template on each request.

### 2. PDF and metadata extraction

`src/docuverus/FraudDetector/MetadataExtractor.py::MetadataExtractor.extract_metadata` uses PyMuPDF (`fitz`) to open the PDF from the byte stream and collects:

- Standard PDF metadata such as `creationDate`, `modDate`, `producer`, `creator`, and `author`.
- `template`, set to the supplied template value.
- `image_file`, determined by accumulated extracted text. A PDF is treated as image-only when the extracted text remains below the 50-character threshold.
- `file_size`, calculated by the file-size helper.
- `paystub_count`, calculated by `get_count_of_paystubs`.
- `fonts`, extracted by scanning PDF cross-reference objects with `PDFUtilities.extract_xref_fonts`.

`MetadataExtractor.extract_xml_metadata` is an additional XML metadata helper; it is not called by the public validation path.

The extractor has an error-path caveat: it sets an `exception` marker when `fitz.open` fails but then continues using `pdf_document`. The detector has logic for metadata dictionaries containing `exception`, but malformed PDFs should be considered an area for defensive hardening.

### 3. Rule-set discovery

`RuleSetFactory` uses `importlib.resources` to enumerate JSON files in these packages:

- `docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson`
- `docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson`

The current corpus contains 428 JSON files: 220 bank-statement files and 208 earnings-statement files. Each file contains a JSON array of rule-set objects. `get_template_rules` loads all rules and compares normalized template names case-insensitively while removing whitespace. Multiple rule sets may match one template.

`get_template_names` deduplicates normalized names while preserving one display name for each normalized value, then returns the names sorted by the API layer.

If no rule set matches the requested template, `FraudDetector` creates an empty rule set and marks the template as unknown.

### 4. Composite evaluation

`CompositeRuleEvaluatorFactory.create(template_type)` applies these evaluators in order:

1. `TemplateTypeRuleEvaluator` — confirms the rule-set template matches the requested template.
2. `FileSizeRuleEvaluator` — validates constant, linear, or unknown file-size rules.
3. `SingleValueRuleEvaluator` for `producer` — applies the producer regex.
4. `SingleValueRuleEvaluator` for `creator` — applies the creator regex.
5. `BrowserPrintedSingleValueOverrideRuleEvaluator` — changes failed producer/creator matches to `FDR` when the actual values match the browser-printed prefix list.
6. `SingleValueRuleEvaluator` for `author` — applies author rules when present; absent author rules are treated as passing.
7. `FontRuleEvaluator` — compares required and optional font definitions, subtype, encoding, and multiplicity.
8. `DateRuleEvaluator` — evaluates creation/modification date states and relationships.

Evaluators mutate each rule-set dictionary by adding fields such as `actual`, `valid`, and `validation_message_code`.

### 5. Fraud/result classification

`FraudDetector.get_document_validations_for_metadata` makes the following decisions:

1. Metadata containing `exception` returns a default `Fail` / `MSG_INVALID_PDF_FILE` result.
2. `image_file=True` returns `Fail` / `MSG_INVALID_IMAGE_DOCUMENT` and a not-applicable rule-set representation containing extracted metadata.
3. All matching rule sets are evaluated.
4. The first rule set with no `Fail` values is selected as a passing result. For browser-printed metadata, both font and file-size rules must also be `Pass`.
5. A date override is checked. If all non-date validators pass and the parsed modification date is strictly after creation and less than five hours later, the result becomes `FDR` / `MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO`.
6. An unknown requested template returns `FDR` / `MSG_UNKNOWN_TEMPLATE_TYPE`.
7. A rule set identified as browser printed returns `FDR` / `MSG_BROWSER_PRINTED_DOCUMENT` when it fails the normal validation path.
8. Invalid producer/creator metadata returns `Fail` / `MSG_INVALID_FILE`.
9. Remaining unresolved cases return `FDR` / `MSG_FURTHER_DOCUMENTATION_REQUIRED`, with rule sets sorted by field validation state.
10. Result finalization can clamp a result to a rule-set `maximum_validation_level` and can force a non-browser-printed font failure to final `Fail`.

The implemented workflow therefore distinguishes ordinary validation failure (`Fail`), fraud/document-review states (`FDR`), and successful validation (`Pass`).

## Rule-set schema

The canonical JSON rule structure is represented by objects containing these major fields:

```json
{
  "template": {"name": "..."},
  "producer": {"name": "..."},
  "creator": {"name": "..."},
  "author": {"name": "..."},
  "file_size": {"algorithm": "Constant", "min": 0, "max": 0},
  "fonts": {
    "required_fonts": [],
    "optional_fonts": []
  },
  "dates": {
    "created": {"state": "Present"},
    "modified": {"state": "Equal"}
  }
}
```

The `author` field is optional in many rule sets and is added as a passing rule when absent. Date rules support `None`, `Present`, `Equal`, `Greater`, `Lesser`, specific PDF dates, tolerances, durations, and unparseable-date handling through the evaluator strategy classes.

The Pydantic `TemplateRuleSetModel` documents validation constraints for the rule shape, including allowed `maximum_validation_level` values and the restriction that created and modified dates cannot both have the `Present` state. The live public API mutates dictionaries directly and does not explicitly instantiate this model.

## Result contract

Typical responses contain:

```json
{
  "final_validation_results": {
    "valid": "Pass|FDR|Fail",
    "validation_message_code": "MSG_*"
  },
  "template_rule_set_validation_results": [
    {
      "template": {},
      "producer": {},
      "creator": {},
      "author": {},
      "file_size": {},
      "fonts": {},
      "dates": {}
    }
  ]
}
```

Nested rule results normally include expected rule values, actual extracted values, a validation state, and a message code. Message-code constants are defined in `src/docuverus/Utils/Messages.py`; resource lists in `browserprinted_list.json` and `invalidproducercreator_list.json` drive browser-printed and invalid metadata detection.

## Supporting components and maintenance workflows

### Present but not wired into the Flask route

- `TemplateDetector.get_template_confidences` is a stub with no implementation.
- `CompleteMetadataWorkflow` coordinates named-template results and a generic fallback. Its precedence is pass first, then FDR, then fail, then generic validation.
- `MultiTemplateFraudDetector` can run a detector for multiple template-confidence candidates, but it is not called by `api.validate_metadata`.
- `NamedTemplateFraudDetectorFactory` exists but creates a `FraudDetector` with `None` dependencies and is not used by the public route.

These classes are covered by workflow tests and represent an intended or experimental multi-template workflow, not the currently executable HTTP architecture. The multi-template implementation also passes the confidence collection as the extractor’s `template_type`, which should be treated as a potential integration defect if that workflow is activated.

### Rule maintenance scripts

The `scripts` directory supports the rule corpus lifecycle:

- `convert_legacy_metadata_to_rulesets.py` and `scripts/src/LegacyMetadataConverter.py` convert legacy tabular/JSON metadata into canonical rule JSON.
- `compare_generated_rulesets.py` and `scripts/src/GeneratedRulesetComparator.py` compare generated output with canonical rules.
- `standardize_template_json.py` normalizes canonical JSON formatting.
- `apply_ruleset_updates_from_report.py` and `scripts/src/TemplateJsonUpdaterFromReport.py` apply targeted updates, with a dry-run option.

These are maintenance/build workflows and are not invoked by the running Flask service.

## Current versus diagrammed architecture

| Area | Current repository behavior | Diagram implication |
|---|---|---|
| Entry point | Flask routes in `app.py`; template is supplied by the caller | Diagram starts with a broader core workflow and does not show the actual Flask route |
| Document type | No document-type service or classifier in this repository | Diagram shows document-type identification as a separate service |
| Template identification | `TemplateDetector` is stubbed; current validation uses the supplied template | Diagram shows automatic template identification and confidence flow |
| Metadata | PyMuPDF extracts PDF metadata, fonts, file size, image-only status, and paystub count | Diagram’s metadata loop is directionally related but omits the concrete extractor |
| Validation | Rule JSON is loaded locally and evaluated by a composite evaluator and `FraudDetector` | Diagram shows the comparator loop but not the current class boundaries or result precedence |
| Browser printed | Producer/creator prefixes, font checks, file-size checks, and FDR outcomes are implemented | Diagram’s browser-printed branch is broadly consistent but should show the actual rule interaction |
| Database | No database client, bootstrap, or persistence code is present | Diagram’s database persistence is unsupported by this repository |
| OCR/read-data | No OCR or business-data extraction service is present | Diagram’s read-data stage is external or future-state, not current code |
| Frontend | React client calls template listing, validation, and font highlighting endpoints | Diagram omits the client and font-highlighting side path |
| Image PDFs | Image-only PDFs are returned as invalid image documents | This outcome should be explicit in the updated validation flow |

## Recommendations for updating the source diagram

1. Label the diagram with a version/date and a legend distinguishing “implemented in `socr-api-v2`” from “external or future-state.”
2. Replace the current core-service sequence with the actual HTTP path: client → Flask route → `api.validate_metadata` → `MetadataExtractor` → `RuleSetFactory`/rule JSON → composite evaluators → `FraudDetector` → JSON response.
3. Show that the template is caller-supplied today. Put automatic template detection and confidence scoring in a dashed, future-state section until `TemplateDetector` is implemented and wired into the route.
4. Add the concrete extraction outputs: PDF metadata, image-only flag, file size, paystub count, and fonts.
5. Show rule-set evaluation as a local rule-corpus operation, including producer/creator, browser-printed override, file size, fonts, dates, and final state precedence.
6. Add explicit terminal outcomes: `Pass`, `Fail`, and `FDR` with representative message-code categories for invalid PDFs, image PDFs, browser-printed documents, unknown templates, further documentation, and save-as/date overrides.
7. Show `/template_names` and `/highlight_fonts` as side endpoints rather than implying they are part of validation.
8. Remove database, OCR/read-data, and document-type-service steps from the implemented path, or label them clearly as external integrations/future architecture.
9. Preserve the diagram’s useful domain notes about browser-printed documents and font extraction, but mark them as policy/rule notes instead of mixing them into the executable control flow.

