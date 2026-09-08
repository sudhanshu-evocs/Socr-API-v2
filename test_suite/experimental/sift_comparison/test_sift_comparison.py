from __future__ import annotations

import io
from pathlib import Path

import pytest
from flask import Flask

cv2 = pytest.importorskip("cv2")

from experimental.sift_comparison.baseline_manager import BaselineManager
from experimental.sift_comparison.comparator import SiftComparator
from experimental.sift_comparison.config import SiftConfig
from experimental.sift_comparison.routes import create_experimental_blueprint
from experimental.sift_comparison.template_mapping import resolve_template_mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTS = REPOSITORY_ROOT / "test_documents"


def _config(reference_root: Path) -> SiftConfig:
    return SiftConfig(enabled=True, reference_root=reference_root, render_dpi=140)


def _pdf(name: str) -> bytes:
    return (DOCUMENTS / name).read_bytes()


def _register(config: SiftConfig, template: str, document_type: str, filename: str) -> Path:
    return BaselineManager(config).register_pdf(template, document_type, _pdf(filename))


def test_explicit_template_mapping_does_not_use_fuzzy_names():
    assert resolve_template_mapping("PNC", "Bank Statement").key == "PNC_Bank"
    assert resolve_template_mapping("Capital One Bank", "Bank Statement").key == "Capital_One"
    assert resolve_template_mapping("Citadel", "Bank Statement").key == "Citadel"
    assert resolve_template_mapping("ADP1", "Paystub / Earning Statement").key == "ADP1"
    assert resolve_template_mapping("Gusto", "Paystub / Earning Statement").key == "Gusto"
    assert resolve_template_mapping("Paycor", "Paystub / Earning Statement").key == "Paycor"
    assert resolve_template_mapping("TD Bank", "Bank Statement").key == "TD_Bank"
    assert resolve_template_mapping("PNC-ish", "Bank Statement") is None


def test_missing_chase_baseline_returns_no_reference_with_null_metrics(tmp_path):
    result = SiftComparator(_config(tmp_path)).compare_pdf(
        _pdf("Valid_Chase_Bank_with_prefix_in_fonts.pdf"), "Chase Bank", "Bank Statement"
    )

    assert result["status"] == "NO_REFERENCE"
    for field in (
        "similarity_score",
        "reference_keypoints",
        "test_keypoints",
        "raw_matches",
        "good_matches",
        "inlier_matches",
        "inlier_ratio",
        "feature_coverage",
        "layout_match",
        "reference_preview",
        "test_preview",
        "match_visualization",
        "visualized_matches",
        "detailed_match_visualization",
        "detailed_visualized_matches",
    ):
        assert result[field] is None


def test_baseline_registration_refuses_to_overwrite(tmp_path):
    config = _config(tmp_path)
    _register(config, "PNC Bank", "bank_statement", "Valid_PNC_Bank_for_font_multiplicity.pdf")

    with pytest.raises(FileExistsError, match="not overwritten"):
        _register(config, "PNC Bank", "bank_statement", "Valid_PNC_Bank_Statement_with_single_font.pdf")


def test_pnc_documents_execute_against_separately_registered_pnc_baseline(tmp_path):
    config = _config(tmp_path)
    _register(config, "PNC Bank", "bank_statement", "Valid_PNC_Bank_for_font_multiplicity.pdf")
    comparator = SiftComparator(config)

    baseline_document_result = comparator.compare_pdf(
        _pdf("Valid_PNC_Bank_for_font_multiplicity.pdf"), "PNC Bank", "Bank Statement"
    )
    different_document_result = comparator.compare_pdf(
        _pdf("Valid_PNC_Bank_Statement_with_single_font.pdf"), "PNC Bank", "Bank Statement"
    )

    assert baseline_document_result["status"] in {"VISUAL_MATCH", "PARTIAL_MATCH", "LOW_MATCH"}
    assert different_document_result["status"] in {"VISUAL_MATCH", "PARTIAL_MATCH", "LOW_MATCH"}
    assert baseline_document_result["reference_keypoints"] > 0
    assert different_document_result["test_keypoints"] > 0
    assert baseline_document_result["total_sift_time_ms"] >= 0
    assert baseline_document_result["reference_preview"].startswith("data:image/jpeg;base64,")
    assert baseline_document_result["test_preview"].startswith("data:image/jpeg;base64,")
    assert baseline_document_result["match_visualization"].startswith("data:image/jpeg;base64,")
    assert 0 < baseline_document_result["visualized_matches"] <= config.visualization_clear_matches
    assert baseline_document_result["detailed_match_visualization"].startswith("data:image/jpeg;base64,")
    assert baseline_document_result["visualized_matches"] <= baseline_document_result["detailed_visualized_matches"]
    assert baseline_document_result["detailed_visualized_matches"] <= config.visualization_max_matches


def test_chase_document_executes_after_separate_chase_registration(tmp_path):
    config = _config(tmp_path)
    _register(config, "Chase Bank", "bank_statement", "Valid_Chase_Bank_with_prefix_in_fonts.pdf")

    result = SiftComparator(config).compare_pdf(
        _pdf("Valid_Chase_Bank_with_different_prefix_for_same_font.pdf"), "Chase Bank", "Bank Statement"
    )

    assert result["status"] in {"VISUAL_MATCH", "PARTIAL_MATCH", "LOW_MATCH"}
    assert result["reference_found"] is True
    assert result["reference_loaded"] is True
    assert result["test_rendered"] is True


def test_wrong_template_controls_are_weaker_than_identical_pnc(tmp_path):
    config = _config(tmp_path)
    _register(config, "PNC Bank", "bank_statement", "Valid_PNC_Bank_for_font_multiplicity.pdf")
    comparator = SiftComparator(config)

    matching = comparator.compare_pdf(_pdf("Valid_PNC_Bank_for_font_multiplicity.pdf"), "PNC Bank", "Bank Statement")
    chase_control = comparator.compare_pdf(_pdf("Valid_Chase_Bank_with_prefix_in_fonts.pdf"), "PNC Bank", "Bank Statement")
    adp_control = comparator.compare_pdf(_pdf("Invalid_paystubs_matching_with_valid_ADP1_metadata.pdf"), "PNC Bank", "Bank Statement")

    assert matching["similarity_score"] > chase_control["similarity_score"]
    assert matching["similarity_score"] > adp_control["similarity_score"]
    assert chase_control["status"] != "VISUAL_MATCH"
    assert adp_control["status"] != "VISUAL_MATCH"


def test_corrupt_reference_returns_error_without_propagating(tmp_path):
    config = _config(tmp_path)
    mapping = resolve_template_mapping("Chase Bank", "Bank Statement")
    reference = BaselineManager(config).reference_path(mapping)
    reference.parent.mkdir(parents=True)
    reference.write_bytes(b"not an image")

    result = SiftComparator(config).compare_pdf(
        _pdf("Valid_Chase_Bank_with_prefix_in_fonts.pdf"), "Chase Bank", "Bank Statement"
    )

    assert result["status"] == "ERROR"
    assert result["reference_found"] is True
    assert result["error"]

    application = Flask(__name__)

    @application.post("/validate_metadata")
    def authoritative_socr():
        return {"final_validation_results": {"valid": "Pass"}}

    application.register_blueprint(create_experimental_blueprint(config))
    client = application.test_client()
    sift_response = client.post(
        "/api/experimental/sift-compare",
        data={
            "file": (io.BytesIO(_pdf("Valid_Chase_Bank_with_prefix_in_fonts.pdf")), "chase.pdf"),
            "template": "Chase Bank",
            "document_type": "Bank Statement",
        },
        content_type="multipart/form-data",
    )

    assert sift_response.get_json()["status"] == "ERROR"
    assert client.post("/validate_metadata").get_json()["final_validation_results"]["valid"] == "Pass"


def test_feature_flag_disabled_leaves_existing_routes_and_comparison_absent(tmp_path):
    application = Flask(__name__)

    @application.get("/existing")
    def existing():
        return {"status": "unchanged"}

    application.register_blueprint(create_experimental_blueprint(SiftConfig(enabled=False, reference_root=tmp_path)))
    client = application.test_client()

    assert client.get("/existing").get_json() == {"status": "unchanged"}
    assert client.get("/api/experimental/sift-config").get_json()["enabled"] is False
    assert client.post(
        "/api/experimental/sift-compare",
        data={"file": (io.BytesIO(b"pdf"), "test.pdf"), "template": "PNC Bank"},
        content_type="multipart/form-data",
    ).status_code == 404
