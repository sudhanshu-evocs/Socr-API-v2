# SOCR API V2 — UI Setup and Local Ruleset Testing Report

**Audience:** Engineering / tech lead  
**Scope:** How the React inspector is set up in this repository, how to run it locally, and how to test new TemplateJson rulesets through the UI.  
**Code basis:** `react-app/src/App.js`, `src/docuverus/app.py`, `start.ps1`, `docker-compose.yml`

---

## 1. Summary

The UI is a **Create React App** in `react-app`. It is a client-only inspector. It does **not** create or store rulesets.

Rulesets live in `src/docuverus/RuleEvaluators/TemplateJson` and are loaded by the **Flask API** on port **5000**. The UI on port **3000** (local) or **80** (Docker) calls that API to list templates, detect a template from a PDF, validate metadata, and optionally highlight fonts.

To test a new ruleset locally: add or update the JSON, **restart Flask**, refresh the UI, pick the new template name, upload a PDF, and review Pass / FDR / Fail.

---

## 2. How the UI is set up in this project

### 2.1 Layout

| Piece | Location | Role |
|---|---|---|
| Inspector UI | `react-app/src/App.js` | Single-page metadata validator |
| Styles | `react-app/src/App.css` | Layout and result views |
| Entry | `react-app/src/index.js` | Renders `App` only |
| Unused leftover | `react-app/src/components/FileUpload.js` | Posts to `/upload` (not implemented). Not used by `App`. |
| API | `src/docuverus/app.py` | Flask + CORS, port 5000 |
| Rulesets | `src/docuverus/RuleEvaluators/TemplateJson` | Bank statements and paystub JSON |

There is no React Router, no login, and no database. One page talks to the API.

### 2.2 How the UI finds the API

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
```

Local default is `http://localhost:5000`. Set `REACT_APP_API_URL` only if the API is elsewhere.

Flask enables CORS (`CORS(app)`), so the browser can call the API from `http://localhost:3000`.

### 2.3 API calls used by the UI

```text
Browser (CRA :3000 or Nginx :80)
    GET  /template_names          → dropdown / autocomplete
    GET  /template_categories     → Bank statements vs Paystubs tabs
    POST /detect_template         → auto-select after upload
    POST /validate_metadata       → file + selected template name
    POST /highlight_fonts         → highlighted PDF bytes
Flask :5000
    → extracts PDF metadata
    → loads matching TemplateJson ruleset
    → returns Pass / FDR / Fail JSON
```

Validation uses the **template the user selected**, not the detector result, if they override it.

---

## 3. Running the UI locally

Use this path to test new rulesets. Docker is optional.

### 3.1 Prerequisites

- Python 3.12+ and `pip install -r src/requirements.txt`
- Node.js (CRA uses Node 20 in Docker; a current LTS is fine locally)
- From `react-app`: `npm install` (first time only)

### 3.2 Start the API

From the repository root (PowerShell):

```powershell
$env:PYTHONPATH = "$PWD\src"
python src\docuverus\app.py
```

API: **http://localhost:5000**  
Swagger-style docs: **http://localhost:5000/docs**

### 3.3 Start the UI

```powershell
cd react-app
npm start
```

UI: **http://localhost:3000**

Alternatively from the repo root:

- `.\start.ps1` — opens API and UI in two PowerShell windows
- Root `package.json`: `npm run frontend` (UI only)

The top-right status should read **Validator ready**. **Validator unavailable** means the API is down or CORS/URL is wrong.

### 3.4 After changing a ruleset

1. Save JSON under `TemplateJson`.
2. **Restart the Flask process** so `/template_names` reloads.
3. Refresh the browser. The UI does not need a rebuild for JSON-only changes.

---

## 4. Docker (full stack)

`docker compose up` starts:

| Service | Image | Host port |
|---|---|---|
| `api` | Python 3.12, `src/docuverus/app.py` | 5000 |
| `web` | CRA production build served by Nginx | 80 |

The production frontend Dockerfile (`react-app/Dockerfile`) builds static assets and serves them from Nginx (`react-app/nginx.conf`). That is a static site, not hot reload.

`react-app/Dockerfile.dev` exists for CRA on port 3000 inside a container. Compose currently uses the production Nginx image.

For iterating on rulesets, **local Flask + `npm start`** is the practical setup.

---

## 5. UI flow for testing a new ruleset

The page title is **SOCR API V2 Rule Engine Metadata Inspector**. Progress is:

**1. Upload PDFs → 2. Assign templates → 3. Review results**

### Step 1 — Upload

- Drop or browse up to **10 PDFs**.
- Each file is listed with size and detection status.
- Upload triggers `POST /detect_template` (fingerprint vs known templates).

### Step 2 — Assign template

**Single file**

- Filter: All / Bank statements / Paystubs & earnings (`GET /template_categories`).
- Search templates (`GET /template_names` — every loaded ruleset, including a new one after API restart).
- Auto-detect may fill the template and show confidence. Confirm or change it.
- Weak/ambiguous detection requires a **manual** pick. For a brand-new ruleset, select the new name here.

**Multiple files**

- Each PDF has its own dropdown. Every file must have a template before Validate is enabled.

When assignment is complete, the panel shows **Ready to validate**. Click **Validate metadata** (or **Validate N documents**). That posts the file plus template name to `/validate_metadata`.

### Step 3 — Review

Overall verdict: **Pass**, **FDR** (manual review), or **Fail**.

Also shown:

- Rule counts (passed / review / failed)
- Risk score (UI-only, labeled **Testing only** — not an API fraud probability)
- Why this result (which rules drove Fail or FDR)
- Cards: template, producer, creator, file size, fonts, dates

| Tab | Purpose |
|---|---|
| Metadata Validator | Rule-by-rule expected vs found, message code, Pass/FDR/Fail |
| PDF Preview | Document; optional font highlight overlay |
| Raw Data Text | Copyable text report |
| Raw JSON Output | Full API payload for debugging the ruleset |

Batch: click a document tab to switch results. **Get highlighted file** downloads a PDF with font boxes.

---

## 6. Recommended test pass for a new ruleset

| Test | Action | Expected |
|---|---|---|
| Template appears | Restart API, refresh UI, search template list | New name is in autocomplete / batch dropdown |
| Known-good PDF | Upload a genuine document for that issuer, select the new template, Validate | Pass on rules that were implemented (producer, creator, fonts, dates, file size as configured) |
| Wrong template | Same PDF, select a different template | Fail or FDR on mismatch rules |
| Tampered / extra fonts / wrong producer | Upload a modified or mismatched PDF against the new template | Fail or FDR on the matching rule; checklist shows expected vs found |
| Auto-detect | Upload and note detector result | May be wrong for a brand-new fingerprint; **manual selection still validates** against the chosen name |

The UI cannot author JSON. Editing happens in `TemplateJson`; the UI is only **select → run → inspect**.

---

## 7. Limitations to know while testing

- Image files are partly handled in UI code; the `/validate_metadata` route currently accepts **PDFs only**. Use PDFs for ruleset testing.
- Risk score and “expected / found / why” explainability are **derived in the frontend** from the API JSON. The contract of record is **Raw JSON Output**.
- `FileUpload.js` is not part of this flow.
- Template list is loaded once on page load. After adding a ruleset, refresh after the API restart.

---

## 8. Quick checklist for a local session

1. Start API on `:5000` with `PYTHONPATH` including `src`.
2. Start UI: `cd react-app && npm start` → `:3000`.
3. Confirm **Validator ready**.
4. Confirm the new template name is in the list.
5. Upload PDF → assign template → Validate.
6. Check Metadata Validator + Raw JSON for Pass / FDR / Fail on each rule.
