"""Local Flask launcher that wraps, but does not modify, the V2 application."""

from __future__ import annotations

import os
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
source_root_string = str(SOURCE_ROOT)
if source_root_string not in sys.path:
    sys.path.insert(0, source_root_string)

from docuverus.app import app  # noqa: E402

from .config import SiftConfig  # noqa: E402
from .routes import create_experimental_blueprint  # noqa: E402


CONFIG = SiftConfig.from_environment()
app.register_blueprint(create_experimental_blueprint(CONFIG))


def main() -> None:
    use_waitress = os.environ.get("FLASK_ENV") == "production" or os.environ.get("USE_WAITRESS", "true").lower() == "true"
    if use_waitress:
        try:
            from waitress import serve

            print(f"Serving local V2 API with SIFT experiment enabled={CONFIG.enabled} on http://0.0.0.0:5000...")
            serve(app, host="0.0.0.0", port=5000)
            return
        except ImportError:
            pass
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
