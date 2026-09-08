"""Stable response shapes for the experimental endpoint."""

from __future__ import annotations

from typing import Any


METRIC_FIELDS = (
    "reference_keypoints",
    "test_keypoints",
    "raw_matches",
    "good_matches",
    "inlier_matches",
    "inlier_ratio",
    "feature_coverage",
    "similarity_score",
    "layout_match",
)


def empty_result(status: str, template: str, message: str, baseline_key: str | None = None, error: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status,
        "template": template,
        "baseline_key": baseline_key,
        "reference_found": False,
        "reference_loaded": False,
        "test_rendered": False,
        "homography_found": False,
        "message": message,
        "error": error,
        "render_time_ms": None,
        "feature_detection_time_ms": None,
        "matching_time_ms": None,
        "total_sift_time_ms": None,
        "reference_preview": None,
        "test_preview": None,
        "match_visualization": None,
        "visualized_matches": None,
        "detailed_match_visualization": None,
        "detailed_visualized_matches": None,
        "visualization_error": None,
    }
    result.update({field: None for field in METRIC_FIELDS})
    return result
