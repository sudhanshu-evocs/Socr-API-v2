# Experimental Visual Template Comparison (SIFT)

This local-only R&D path compares page 1 of an uploaded PDF with an explicitly registered reference image. It does not determine authenticity and never affects SOCR's authoritative `Pass`, `FDR`, or `Fail` result.

## Enable locally

Run `start.ps1 -EnableSift`. The local launcher registers the experimental routes while importing Docuverus from this checkout's `src` directory. The equivalent environment-variable form is `$env:ENABLE_SIFT_COMPARISON = "true"` followed by `.\start.ps1`. With neither form enabled, `start.ps1` uses the original V2 launcher and the React tab is hidden. Restart an existing backend because routes are registered only at process startup.

## Register a known-good baseline

Baseline registration is separate from document testing and refuses to overwrite an existing `reference.png`:

```powershell
$env:ENABLE_SIFT_COMPARISON = "true"
python -m experimental.sift_comparison.register_baseline --template "PNC Bank" --document-type bank_statement --file "C:\path\known_good_pnc.pdf"
```

Use `--document-type paystub` for ADP1 or Gusto. No normal upload is ever promoted to a baseline.

To seed one representative baseline for every unambiguous `Valid_*` bank/paystub fixture in this repository:

```powershell
python -m experimental.sift_comparison.seed_known_good_baselines
```

The seeder skips existing baselines and never overwrites them. Templates without an unambiguous known-good fixture remain `NO_REFERENCE`.

### Docker Compose

If Docker already owns port 5000, use the local-only overlay instead of `start.ps1`:

```powershell
docker compose -f docker-compose.yml -f docker-compose.sift.yml up -d --build api
```

The overlay mounts `experimental/`, sets the feature flag, and replaces only the API container command. It does not alter the Docuverus wheel.

## Initial uncalibrated score

`normalized_match_strength = min(1, good_matches / (0.15 * min(reference_keypoints, test_keypoints)))`

`similarity = 0.30 * normalized_match_strength + 0.45 * RANSAC_inlier_ratio + 0.25 * feature_coverage`

Feature coverage is the lower occupied-cell fraction of reference and test inliers over a 4-by-4 grid. `VISUAL_MATCH` additionally requires distributed layout evidence. All weights and thresholds are experimental and configurable through `SIFT_*` environment variables in `config.py`.

## Removal

Remove `experimental/`, its tests, and the clearly marked React/startup integration. No production evaluator, ruleset, metadata extractor, or packaged Docuverus module depends on this directory.
