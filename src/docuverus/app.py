import logging
import os
import sys
import time

# Add parent 'src' directory to sys.path so 'docuverus' package resolves automatically
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify, request
from flask_cors import CORS

from docuverus.Utils.PDFUtilities import PDFUtilities
from docuverus import api

_log = logging.getLogger("API")

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB upload limit
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_MIME_TYPES = {"application/pdf", "application/octet-stream"}


def _is_valid_pdf(file) -> bool:
    """Return True if the uploaded file starts with the PDF magic bytes %PDF."""
    header = file.stream.read(4)
    file.stream.seek(0)  # Reset stream so it can be read again downstream
    return header == b"%PDF"

SWAGGER_UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SOCR API Documentation</title>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  <style>
    html { box-sizing: border-box; overflow-y: scroll; }
    *, *:before, *:after { box-sizing: inherit; }
    body { margin: 0; background: #ffffff; }
    .swagger-ui .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" charset="UTF-8"></script>
  <script>
    window.onload = function() {
      window.ui = SwaggerUIBundle({
        spec: {
          openapi: "3.0.0",
          info: {
            title: "SOCR Document Metadata API",
            version: "2.0.0",
            description: "Automated document metadata validation, template detection, and fraud analysis engine."
          },
          paths: {
            "/api": {
              get: {
                summary: "Health Check",
                description: "Returns API operational status",
                responses: {
                  "200": { description: "API status operational" }
                }
              }
            },
            "/template_names": {
              get: {
                summary: "List Template Names",
                description: "Returns a JSON array of supported template names",
                responses: {
                  "200": { description: "List of template names" }
                }
              }
            },
            "/validate_metadata": {
              post: {
                summary: "Validate Document Metadata",
                description: "Validates PDF document metadata against specified rule sets",
                requestBody: {
                  content: {
                    "multipart/form-data": {
                      schema: {
                        type: "object",
                        properties: {
                          file: { type: "string", format: "binary", description: "PDF document file" },
                          template: { type: "string", description: "Template name (e.g. Chase Bank, Ally)" }
                        },
                        required: ["file", "template"]
                      }
                    }
                  }
                },
                responses: {
                  "200": { description: "Validation results JSON" },
                  "400": { description: "Missing file or template parameter" }
                }
              }
            },
            "/detect_template": {
              post: {
                summary: "Detect Document Template",
                description: "Suggests a template and document class from the PDF metadata fingerprint",
                requestBody: {
                  content: {
                    "multipart/form-data": {
                      schema: {
                        type: "object",
                        properties: {
                          file: { type: "string", format: "binary", description: "PDF document file" }
                        },
                        required: ["file"]
                      }
                    }
                  }
                },
                responses: {
                  "200": { description: "Ranked template detection result" },
                  "400": { description: "Missing PDF file" }
                }
              }
            },
            "/highlight_fonts": {
              post: {
                summary: "Highlight PDF Fonts",
                description: "Highlights font usages in the provided PDF document",
                requestBody: {
                  content: {
                    "multipart/form-data": {
                      schema: {
                        type: "object",
                        properties: {
                          file: { type: "string", format: "binary", description: "PDF document file" },
                          fonts: { type: "string", description: "Font name to highlight" }
                        },
                        required: ["file", "fonts"]
                      }
                    }
                  }
                },
                responses: {
                  "200": { description: "Annotated PDF binary stream" }
                }
              }
            }
          }
        },
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIBundle.SwaggerUIStandalonePreset
        ]
      });
    };
  </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
@app.route("/docs", methods=["GET"])
def api_docs():
    return SWAGGER_UI_HTML, 200, {"Content-Type": "text/html"}


@app.route("/validate_metadata", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    if "template" not in request.values.keys():
        return jsonify({"error": "No given template"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No given file"}), 400
    if not _is_valid_pdf(file):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    template_name = request.values["template"]
    file_bytes = file.stream.read()
    file_size_kb = round(len(file_bytes) / 1024, 1)
    _log.info("POST /validate_metadata — template='%s' size=%sKB ip=%s",
              template_name, file_size_kb, request.remote_addr)
    t_start = time.perf_counter()
    try:
        result = api.validate_metadata(file_bytes, template_name)
        verdict = result.get("final_validation_results", {}).get("valid", "?")
        duration = round(time.perf_counter() - t_start, 3)
        _log.info("Response 200 — verdict=%s duration=%ss", verdict, duration)
        return jsonify(result), 200
    except Exception as e:
        duration = round(time.perf_counter() - t_start, 3)
        _log.error("Response 500 — error=%s duration=%ss", e, duration)
        return jsonify({"error": "Failed to process the document"}), 500


@app.route("/detect_template", methods=["POST"])
def detect_template():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No given file"}), 400

    file_bytes = file.stream.read()
    file_size_kb = round(len(file_bytes) / 1024, 1)
    _log.info("POST /detect_template — filename='%s' size=%sKB ip=%s",
              file.filename, file_size_kb, request.remote_addr)
    t_start = time.perf_counter()
    try:
        result = api.detect_template(file_bytes, file.filename)
        detected = result.get("template_name", "?")
        confidence = result.get("confidence", "?")
        duration = round(time.perf_counter() - t_start, 3)
        _log.info("Response 200 — detected='%s' confidence=%s duration=%ss", detected, confidence, duration)
        return jsonify(result), 200
    except Exception:
        duration = round(time.perf_counter() - t_start, 3)
        _log.error("Response 422 — template detection failed duration=%ss", duration)
        return jsonify({"error": "Template detection could not read this PDF"}), 422


@app.route("/template_names", methods=["GET"])
def template_names():
    return jsonify(api.get_template_names()), 200


@app.route("/template_categories", methods=["GET"])
def template_categories():
    return jsonify(api.get_template_categories()), 200



@app.route("/highlight_fonts", methods=["POST"])
def highlight_fonts():
    if "file" not in request.files or "fonts" not in request.values:
        return jsonify({"error": "Missing file or fonts parameter"}), 400
    try:
        result = PDFUtilities.highlight_usages_of_fonts_in_byte_representation_of_pdf(
            request.files["file"].stream.read(), request.values["fonts"], (1, 0, 0)
        )
        return result, 200
    except Exception as e:
        app.logger.error(f"Error in highlight_fonts: {e}")
        return jsonify({"error": "Failed to highlight fonts in the document"}), 500


@app.route("/api", methods=["GET"])
def api_status():
    return jsonify({"message": "Hello, World!"})


if __name__ == "__main__":
    use_waitress = os.environ.get("FLASK_ENV") == "production" or os.environ.get("USE_WAITRESS", "true").lower() == "true"
    if use_waitress:
        try:
            from waitress import serve
            print("Serving production WSGI server (Waitress) on http://0.0.0.0:5000...")
            serve(app, host="0.0.0.0", port=5000)
        except ImportError:
            app.run(host="0.0.0.0", port=5000)
    else:
        app.run(host="0.0.0.0", port=5000)

