"""Safe lookup and development-only registration of baseline images."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .config import SiftConfig
from .pdf_renderer import render_first_page
from .template_mapping import BaselineMapping, resolve_template_mapping


class BaselineManager:
    def __init__(self, config: SiftConfig):
        self.config = config

    def reference_path(self, mapping: BaselineMapping) -> Path:
        return self.config.reference_root / mapping.category_directory / mapping.key / "reference.png"

    def load(self, mapping: BaselineMapping) -> np.ndarray | None:
        path = self.reference_path(mapping)
        if not path.is_file():
            return None
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None or image.size == 0:
            raise ValueError(f"Baseline reference is invalid or unreadable: {path}")
        return image

    def register_pdf(self, template: str, document_type: str, pdf_bytes: bytes) -> Path:
        mapping = resolve_template_mapping(template, document_type)
        if mapping is None:
            raise ValueError(f"No explicit SIFT baseline mapping exists for {template}.")

        path = self.reference_path(mapping)
        path.parent.mkdir(parents=True, exist_ok=True)
        image = render_first_page(pdf_bytes, self.config.render_dpi)
        encoded, png_bytes = cv2.imencode(".png", image)
        if not encoded:
            raise ValueError("OpenCV could not encode the baseline image.")

        try:
            with path.open("xb") as reference_file:
                reference_file.write(png_bytes.tobytes())
        except FileExistsError as error:
            raise FileExistsError(f"A baseline already exists and was not overwritten: {path}") from error
        return path
