"""OpenCV SIFT comparison with geometric validation and explainable scoring."""

from __future__ import annotations

import base64
from time import perf_counter

import cv2
import numpy as np

from .baseline_manager import BaselineManager
from .config import SiftConfig
from .pdf_renderer import render_first_page
from .schemas import empty_result
from .template_mapping import resolve_template_mapping


def _elapsed_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 2)


def _grid_coverage(points: np.ndarray, width: int, height: int, grid_size: int) -> float:
    if not len(points) or width <= 0 or height <= 0:
        return 0.0
    normalized_x = np.clip(points[:, 0] / width, 0, 0.999999)
    normalized_y = np.clip(points[:, 1] / height, 0, 0.999999)
    cells = {(int(x * grid_size), int(y * grid_size)) for x, y in zip(normalized_x, normalized_y)}
    return len(cells) / float(grid_size * grid_size)


def _resize_to_width(image: np.ndarray, maximum_width: int) -> np.ndarray:
    if maximum_width <= 0 or image.shape[1] <= maximum_width:
        return image
    scale = maximum_width / image.shape[1]
    return cv2.resize(image, (maximum_width, max(1, round(image.shape[0] * scale))), interpolation=cv2.INTER_AREA)


def _jpeg_data_url(image: np.ndarray, maximum_width: int) -> str:
    preview = _resize_to_width(image, maximum_width)
    encoded, buffer = cv2.imencode(".jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if not encoded:
        raise ValueError("OpenCV could not encode the SIFT visualization.")
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode("ascii")


def _spatially_distributed_matches(matches: list, keypoints: list, image_shape: tuple, limit: int, grid_size: int = 4) -> list:
    """Choose strong matches across the page instead of clustering around one logo or table."""
    if limit <= 0:
        return []
    height, width = image_shape[:2]
    buckets: dict[tuple[int, int], list] = {}
    for match in sorted(matches, key=lambda candidate: candidate.distance):
        x, y = keypoints[match.queryIdx].pt
        cell = (min(grid_size - 1, int(x / max(1, width) * grid_size)), min(grid_size - 1, int(y / max(1, height) * grid_size)))
        buckets.setdefault(cell, []).append(match)

    selected: list = []
    active_cells = sorted(buckets)
    while active_cells and len(selected) < limit:
        next_cells = []
        for cell in active_cells:
            if buckets[cell] and len(selected) < limit:
                selected.append(buckets[cell].pop(0))
            if buckets[cell]:
                next_cells.append(cell)
        active_cells = next_cells
    return selected


def _draw_explained_matches(
    reference: np.ndarray,
    reference_keypoints: list,
    test_image: np.ndarray,
    test_keypoints: list,
    matches: list,
    detailed: bool = False,
) -> np.ndarray:
    """Draw labeled pages, colored region lines, and visible keypoint endpoints."""
    reference_color = cv2.cvtColor(reference, cv2.COLOR_GRAY2BGR) if reference.ndim == 2 else reference.copy()
    test_color = cv2.cvtColor(test_image, cv2.COLOR_GRAY2BGR) if test_image.ndim == 2 else test_image.copy()
    header_height = 72
    image_height = max(reference_color.shape[0], test_color.shape[0])
    reference_width = reference_color.shape[1]
    canvas = np.full((header_height + image_height, reference_width + test_color.shape[1], 3), 248, dtype=np.uint8)
    canvas[header_height : header_height + reference_color.shape[0], :reference_width] = reference_color
    canvas[header_height : header_height + test_color.shape[0], reference_width:] = test_color

    cv2.putText(canvas, "BASELINE REFERENCE", (24, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (76, 29, 149), 2, cv2.LINE_AA)
    cv2.putText(canvas, "UPLOADED PDF", (reference_width + 24, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (76, 29, 149), 2, cv2.LINE_AA)
    cv2.line(canvas, (reference_width, 0), (reference_width, canvas.shape[0]), (203, 213, 225), 2)

    # Colors identify broad vertical page regions, not match quality.
    region_colors = ((52, 168, 83), (235, 139, 32), (37, 99, 235), (185, 60, 210))
    line_layer = canvas.copy()
    endpoints: list[tuple[tuple[int, int], tuple[int, int], tuple[int, int, int]]] = []
    for match in matches:
        reference_x, reference_y = reference_keypoints[match.queryIdx].pt
        test_x, test_y = test_keypoints[match.trainIdx].pt
        region_index = min(3, int(reference_y / max(1, reference.shape[0]) * 4))
        color = region_colors[region_index]
        left_point = (round(reference_x), round(reference_y) + header_height)
        right_point = (round(test_x) + reference_width, round(test_y) + header_height)
        cv2.line(line_layer, left_point, right_point, color, 1 if detailed else 2, cv2.LINE_AA)
        endpoints.append((left_point, right_point, color))

    canvas = cv2.addWeighted(line_layer, 0.78, canvas, 0.22, 0)
    radius = 3 if detailed else 5
    for left_point, right_point, color in endpoints:
        cv2.circle(canvas, left_point, radius + 2, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(canvas, right_point, radius + 2, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(canvas, left_point, radius, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, right_point, radius, color, -1, cv2.LINE_AA)
    return canvas


class SiftComparator:
    def __init__(self, config: SiftConfig | None = None, baseline_manager: BaselineManager | None = None):
        self.config = config or SiftConfig.from_environment()
        self.baseline_manager = baseline_manager or BaselineManager(self.config)

    def compare_pdf(self, pdf_bytes: bytes, template: str, document_type: str = "") -> dict:
        total_started = perf_counter()
        mapping = resolve_template_mapping(template, document_type)
        if mapping is None:
            result = empty_result("NO_REFERENCE", template, f'No baseline reference mapping is configured for {template}.')
            result["total_sift_time_ms"] = _elapsed_ms(total_started)
            return result

        reference_path = self.baseline_manager.reference_path(mapping)
        if not reference_path.is_file():
            result = empty_result(
                "NO_REFERENCE",
                mapping.display_name,
                f"No baseline reference image is available for {mapping.display_name}.",
                mapping.key,
            )
            result["total_sift_time_ms"] = _elapsed_ms(total_started)
            return result

        result = empty_result("ERROR", mapping.display_name, "The experimental comparison could not be completed.", mapping.key)
        result["reference_found"] = True
        try:
            reference = self.baseline_manager.load(mapping)
            result["reference_loaded"] = True

            render_started = perf_counter()
            test_image = render_first_page(pdf_bytes, self.config.render_dpi)
            result["render_time_ms"] = _elapsed_ms(render_started)
            result["test_rendered"] = True
            self._attach_previews(result, reference, test_image)

            feature_started = perf_counter()
            sift = cv2.SIFT_create()
            reference_keypoints, reference_descriptors = sift.detectAndCompute(reference, None)
            test_keypoints, test_descriptors = sift.detectAndCompute(test_image, None)
            result["feature_detection_time_ms"] = _elapsed_ms(feature_started)
            result["reference_keypoints"] = len(reference_keypoints)
            result["test_keypoints"] = len(test_keypoints)

            if reference_descriptors is None or test_descriptors is None:
                return self._low_match(result, total_started, "One of the images did not contain usable SIFT descriptors.")

            matching_started = perf_counter()
            matcher = cv2.BFMatcher(cv2.NORM_L2)
            nearest_matches = matcher.knnMatch(reference_descriptors, test_descriptors, k=2)
            valid_pairs = [pair for pair in nearest_matches if len(pair) == 2]
            good_matches = [first for first, second in valid_pairs if first.distance < self.config.lowe_ratio * second.distance]
            result["raw_matches"] = len(valid_pairs)
            result["good_matches"] = len(good_matches)

            if len(good_matches) < self.config.minimum_good_matches:
                result["matching_time_ms"] = _elapsed_ms(matching_started)
                return self._low_match(result, total_started, "Too few Lowe-ratio matches were available for geometric validation.")

            reference_points = np.float32([reference_keypoints[match.queryIdx].pt for match in good_matches])
            test_points = np.float32([test_keypoints[match.trainIdx].pt for match in good_matches])
            try:
                homography, mask = cv2.findHomography(
                    reference_points.reshape(-1, 1, 2),
                    test_points.reshape(-1, 1, 2),
                    cv2.RANSAC,
                    self.config.ransac_reprojection_threshold,
                )
            except cv2.error:
                result["matching_time_ms"] = _elapsed_ms(matching_started)
                return self._low_match(result, total_started, "The matched points could not produce a valid homography.")
            result["matching_time_ms"] = _elapsed_ms(matching_started)
            if homography is None or mask is None:
                return self._low_match(result, total_started, "No geometrically consistent homography was found.")

            inlier_mask = mask.ravel().astype(bool)
            inlier_matches = int(inlier_mask.sum())
            inlier_ratio = inlier_matches / len(good_matches)
            reference_coverage = _grid_coverage(
                reference_points[inlier_mask], reference.shape[1], reference.shape[0], self.config.coverage_grid_size
            )
            test_coverage = _grid_coverage(
                test_points[inlier_mask], test_image.shape[1], test_image.shape[0], self.config.coverage_grid_size
            )
            feature_coverage = min(reference_coverage, test_coverage)
            minimum_keypoints = min(len(reference_keypoints), len(test_keypoints))
            target_matches = max(1.0, self.config.target_good_match_ratio * minimum_keypoints)
            normalized_match_strength = min(1.0, len(good_matches) / target_matches)

            # Experimental, uncalibrated formula. Raw correspondence strength is
            # tempered by RANSAC consistency and document-wide inlier coverage.
            similarity_score = 0.30 * normalized_match_strength + 0.45 * inlier_ratio + 0.25 * feature_coverage
            layout_match = (
                inlier_matches >= self.config.layout_minimum_inliers
                and inlier_ratio >= self.config.layout_minimum_inlier_ratio
                and feature_coverage >= self.config.layout_minimum_coverage
            )
            if similarity_score >= self.config.visual_match_threshold and layout_match:
                status = "VISUAL_MATCH"
            elif similarity_score >= self.config.partial_match_threshold:
                status = "PARTIAL_MATCH"
            else:
                status = "LOW_MATCH"

            result.update(
                {
                    "status": status,
                    "homography_found": True,
                    "inlier_matches": inlier_matches,
                    "inlier_ratio": round(inlier_ratio, 4),
                    "feature_coverage": round(feature_coverage, 4),
                    "similarity_score": round(float(np.clip(similarity_score, 0.0, 1.0)), 4),
                    "layout_match": layout_match,
                    "message": "Visual template comparison completed. This experimental result does not affect SOCR validation.",
                    "error": None,
                    "total_sift_time_ms": _elapsed_ms(total_started),
                }
            )
            self._attach_match_visualization(
                result,
                reference,
                reference_keypoints,
                test_image,
                test_keypoints,
                [match for match, is_inlier in zip(good_matches, inlier_mask) if is_inlier],
            )
            result["total_sift_time_ms"] = _elapsed_ms(total_started)
            return result
        except (ValueError, cv2.error) as error:
            result["error"] = str(error)
            result["message"] = "The experimental visual comparison encountered an invalid PDF, image, or OpenCV operation."
            result["total_sift_time_ms"] = _elapsed_ms(total_started)
            return result
        except Exception as error:  # Final isolation boundary: never propagate into SOCR.
            result["error"] = str(error)
            result["message"] = "The experimental visual comparison failed independently of SOCR validation."
            result["total_sift_time_ms"] = _elapsed_ms(total_started)
            return result

    @staticmethod
    def _low_match(result: dict, total_started: float, message: str) -> dict:
        result.update(
            {
                "status": "LOW_MATCH",
                "homography_found": False,
                "inlier_matches": 0,
                "inlier_ratio": 0.0,
                "feature_coverage": 0.0,
                "similarity_score": 0.0,
                "layout_match": False,
                "message": message,
                "error": None,
                "total_sift_time_ms": _elapsed_ms(total_started),
            }
        )
        return result

    def _attach_previews(self, result: dict, reference: np.ndarray, test_image: np.ndarray) -> None:
        """Attach UI-only page previews without allowing encoding failures to affect SIFT."""
        try:
            result["reference_preview"] = _jpeg_data_url(reference, self.config.preview_max_width)
            result["test_preview"] = _jpeg_data_url(test_image, self.config.preview_max_width)
        except (ValueError, cv2.error) as error:
            result["visualization_error"] = str(error)

    def _attach_match_visualization(
        self,
        result: dict,
        reference: np.ndarray,
        reference_keypoints: list,
        test_image: np.ndarray,
        test_keypoints: list,
        inlier_matches: list,
    ) -> None:
        """Attach clear and detailed RANSAC views; neither view alters scoring."""
        try:
            clear_matches = _spatially_distributed_matches(
                inlier_matches,
                reference_keypoints,
                reference.shape,
                self.config.visualization_clear_matches,
                self.config.coverage_grid_size,
            )
            detailed_matches = _spatially_distributed_matches(
                inlier_matches,
                reference_keypoints,
                reference.shape,
                self.config.visualization_max_matches,
                self.config.coverage_grid_size,
            )
            if not clear_matches:
                return
            clear_visualization = _draw_explained_matches(
                reference,
                reference_keypoints,
                test_image,
                test_keypoints,
                clear_matches,
            )
            detailed_visualization = _draw_explained_matches(
                reference,
                reference_keypoints,
                test_image,
                test_keypoints,
                detailed_matches,
                detailed=True,
            )
            result["match_visualization"] = _jpeg_data_url(clear_visualization, self.config.match_visualization_max_width)
            result["visualized_matches"] = len(clear_matches)
            result["detailed_match_visualization"] = _jpeg_data_url(
                detailed_visualization, self.config.match_visualization_max_width
            )
            result["detailed_visualized_matches"] = len(detailed_matches)
        except (ValueError, cv2.error) as error:
            result["visualization_error"] = str(error)
