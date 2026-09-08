"""Configuration for the local-only SIFT experiment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parent
DEFAULT_REFERENCE_ROOT = EXPERIMENT_ROOT / "references"


def _environment_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _environment_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _environment_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class SiftConfig:
    enabled: bool = False
    reference_root: Path = DEFAULT_REFERENCE_ROOT
    render_dpi: int = 200
    lowe_ratio: float = 0.75
    minimum_good_matches: int = 10
    ransac_reprojection_threshold: float = 5.0
    coverage_grid_size: int = 4
    target_good_match_ratio: float = 0.15
    layout_minimum_inliers: int = 10
    layout_minimum_inlier_ratio: float = 0.35
    layout_minimum_coverage: float = 0.25
    visual_match_threshold: float = 0.65
    partial_match_threshold: float = 0.40
    preview_max_width: int = 800
    match_visualization_max_width: int = 1600
    visualization_clear_matches: int = 40
    visualization_max_matches: int = 120

    @classmethod
    def from_environment(cls) -> "SiftConfig":
        reference_override = os.environ.get("SIFT_REFERENCE_ROOT")
        return cls(
            enabled=_environment_flag("ENABLE_SIFT_COMPARISON"),
            reference_root=Path(reference_override).resolve() if reference_override else DEFAULT_REFERENCE_ROOT,
            render_dpi=_environment_int("SIFT_RENDER_DPI", 200),
            lowe_ratio=_environment_float("SIFT_LOWE_RATIO", 0.75),
            minimum_good_matches=_environment_int("SIFT_MINIMUM_GOOD_MATCHES", 10),
            ransac_reprojection_threshold=_environment_float("SIFT_RANSAC_THRESHOLD", 5.0),
            coverage_grid_size=_environment_int("SIFT_COVERAGE_GRID_SIZE", 4),
            target_good_match_ratio=_environment_float("SIFT_TARGET_GOOD_MATCH_RATIO", 0.15),
            layout_minimum_inliers=_environment_int("SIFT_LAYOUT_MINIMUM_INLIERS", 10),
            layout_minimum_inlier_ratio=_environment_float("SIFT_LAYOUT_MINIMUM_INLIER_RATIO", 0.35),
            layout_minimum_coverage=_environment_float("SIFT_LAYOUT_MINIMUM_COVERAGE", 0.25),
            visual_match_threshold=_environment_float("SIFT_VISUAL_MATCH_THRESHOLD", 0.65),
            partial_match_threshold=_environment_float("SIFT_PARTIAL_MATCH_THRESHOLD", 0.40),
            preview_max_width=_environment_int("SIFT_PREVIEW_MAX_WIDTH", 800),
            match_visualization_max_width=_environment_int("SIFT_VISUALIZATION_MAX_WIDTH", 1600),
            visualization_clear_matches=_environment_int("SIFT_VISUALIZATION_CLEAR_MATCHES", 40),
            visualization_max_matches=_environment_int("SIFT_VISUALIZATION_MAX_MATCHES", 120),
        )
