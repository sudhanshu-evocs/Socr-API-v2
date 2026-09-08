"""Page-one PDF rendering that does not touch SOCR PDF extraction."""

from __future__ import annotations

import fitz
import numpy as np


def render_first_page(pdf_bytes: bytes, dpi: int = 200) -> np.ndarray:
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        if document.page_count < 1:
            raise ValueError("The uploaded PDF has no pages.")
        page = document.load_page(0)
        scale = dpi / 72.0
        pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY, alpha=False)
        image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width).copy()

    if image.size == 0 or image.shape[0] < 2 or image.shape[1] < 2:
        raise ValueError("Page 1 could not be rendered as a usable image.")
    return image
