"""Feature-flagged Flask routes for the local SIFT experiment."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from .comparator import SiftComparator
from .config import SiftConfig


def create_experimental_blueprint(config: SiftConfig | None = None) -> Blueprint:
    active_config = config or SiftConfig.from_environment()
    blueprint = Blueprint("sift_experiment", __name__)

    @blueprint.get("/api/experimental/sift-config")
    def sift_config():
        return jsonify({"enabled": active_config.enabled, "label": "Experimental Visual Template Comparison (SIFT)"})

    if active_config.enabled:

        @blueprint.post("/api/experimental/sift-compare")
        def sift_compare():
            if "file" not in request.files:
                return jsonify({"error": "No file part"}), 400
            if "template" not in request.values:
                return jsonify({"error": "No given template"}), 400
            uploaded_file = request.files["file"]
            if uploaded_file.filename == "":
                return jsonify({"error": "No given file"}), 400

            result = SiftComparator(active_config).compare_pdf(
                uploaded_file.stream.read(),
                request.values["template"],
                request.values.get("document_type", ""),
            )
            return jsonify(result), 200

    return blueprint
