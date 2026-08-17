# Minimal Step APIs With In-Memory Workflow State

## Summary
Keep the minimal synchronous v1 API family:

- `POST /api/v1/document-type-identification`
- `POST /api/v1/template-identification`
- `POST /api/v1/metadata-validation`
- `POST /api/v1/read-data`

Do not add a new database table for workflow state. Assume `core-api` invokes these four APIs as one immediate workflow and keeps intermediate values in memory for that workflow only. `core-api` remains the orchestrator and passes `document_type` and `template` forward explicitly.

## API Contracts
`document-type-identification`
```json
{ "file_base64": "data:application/pdf;base64,..." }
```

Response:
```json
{ "document_type": "PAYSTUB", "confidence": 0.97 }
```

`template-identification`
```json
{ "file_base64": "data:application/pdf;base64,...", "document_type": "PAYSTUB" }
```

Response:
```json
{ "template": "ADP", "confidence": 0.94 }
```

`metadata-validation`
```json
{ "file_base64": "data:application/pdf;base64,...", "document_type": "PAYSTUB", "template": "ADP" }
```

Response:
```json
{
  "status": "PASS",
  "message_code": "MSG_VALID_FILE",
  "checks": [
    { "name": "producer", "status": "PASS", "message_code": "MSG_PRODUCER_MATCH" }
  ]
}
```

`read-data`
```json
{ "file_base64": "data:application/pdf;base64,...", "document_type": "PAYSTUB", "template": "ADP" }
```

Response:
```json
{
  "status": "PASS",
  "trust_level": "TRUSTED",
  "fields": {
    "gross_pay": "11283.33",
    "net_pay": "6812.99",
    "pay_date": "2026-01-30"
  }
}
```

## Future Upgrades or other APIs
`is-consecutive-current-etc...`
```json
{
  "applicant": {
    "first_name": "John"
  },
  "paystub_data": [
    {
      "gross_pay": "11283.33",
      "net_pay": "6812.99",
      "pay_date": "2026-01-30"
    },
    {
      "gross_pay": "11283.33",
      "net_pay": "6812.99",
      "pay_date": "2026-01-30"
    }
  ]
}
```

Response:
```json
{
  "is_consecutive": "true",
  "is_current": "false",
  "name_matched": "true",
  "final_socr_status": "VALID",
  "monthly_gross_pay": "1234.56",
  "monthly_net_pay": "10.00",
  "number_of_weeks": "4"
}
```

## Workflow State
`core-api` keeps this in memory only for the active upload-processing workflow:
- `document_type`
- `document_type_confidence`
- `template`
- `template_confidence`
- `metadata_validation_status`
- `metadata_message_code`
- `metadata_checks`

No DB persistence is required for step 1-3 outputs. If the process dies mid-workflow, the workflow is retried from the beginning.

## Database Updates
### Upload bootstrap before step APIs
This remains in the current `DocumentUpload` flow:

- Insert `mstApplicationDocument`
- Set linkage columns on `mstApplicationDocument`
  - `EmployerNumber` for paystubs
  - `BankStatementNumber` for bank statements
- Keep existing parent-row creation/linking so downstream writes have targets:
  - `mstApplicationIncome` for paystubs
  - `mstApplicationBanking` for bank statements
- Keep `mstOCRBankData` shell-row creation for bank uploads if current screens still depend on it

### Per-step DB ownership
`document-type-identification`
- No database writes

`template-identification`
- No database writes

`metadata-validation`
- No database writes

`read-data`
- This is the only step that writes extracted or normalized results to the database

For both document types, `read-data` updates:
- `mstApplicationDocument`
  - `OCRData`
  - `OCRDataXML`
  - `EncodedOCR`

For `PAYSTUB`, `read-data` updates:
- `mstIncomePaystubData`
- `mstApplicationsecondarydata`
- `mstApplicationIncome`
- `mstOCREmploymentIncomeData`
- `mstApplicationIncomeHeader`
- `mstApplicationIncomeSummary`
- `mstApplicationEmployer`
  Only employer fields derived from extracted data

For `BANK_STATEMENT`, `read-data` updates:
- `mstApplicationBanking`
- `mstOCRBankData`

### Current-flow correction
Today `core-api` writes several paystub business tables before the final OCR/fraud boundary is complete. In the new design, keep document-row creation at upload time, but move all extracted-data writes behind `read-data` so step ownership is clean:
- Step 1-3: classification and validation only
- Step 4: all business persistence

### Operational tables
- `trnDocumentSOCRStatus` should not be part of the new direct step flow
- `Trndocumentnodesocrlogs` may remain for logging, but not as required workflow state

## Test Plan
- Paystub happy path: step 1-3 perform no DB writes; step 4 updates all paystub result tables.
- Bank happy path: step 1-3 perform no DB writes; step 4 updates bank result tables.
- Metadata fail path: step 3 returns `FAIL`; step 4 may still run and writes `trust_level: UNTRUSTED`.
- Verify `mstApplicationDocument` raw OCR fields are written only by `read-data`.
- Verify retry-from-start behavior works if the in-memory workflow is interrupted.
- Verify no dependency remains on `trnDocumentSOCRStatus`.

## Assumptions
- V1 scope remains `PAYSTUB` and `BANK_STATEMENT`.
- `core-api` executes the four steps in one immediate workflow and does not need cross-request recovery for intermediate state.
- Minimal request payloads are preserved.
- Existing business tables remain the system of record for extracted paystub and bank data.
