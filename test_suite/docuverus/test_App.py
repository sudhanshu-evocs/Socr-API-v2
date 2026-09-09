import io
import json
import unittest
from unittest.mock import patch

import pytest

from docuverus.app import app
from test_suite.support.assertions import assert_dict_contains


class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_validate_metadata_no_file_part(self):
        response = self.app.post("/validate_metadata", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"No file part", response.data)

    def test_validate_metadata_no_selected_file(self):
        data = {"file": (io.BytesIO(b""), ""), "template": "template_name"}
        response = self.app.post("/validate_metadata", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"No given file", response.data)

    def test_validate_metadata_no_given_template(self):
        data = {"file": (io.BytesIO(b"my file contents"), "test_file.txt")}
        response = self.app.post("/validate_metadata", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"No given template", response.data)

    @patch("docuverus.app.api.validate_metadata")
    def test_validate_metadata_delegates_to_public_api(self, mock_validate_metadata):
        expected_return_value = {"final_validation_results": {"valid": "Pass", "validation_message_code": "MSG_VALID_FILE"}}
        mock_validate_metadata.return_value = expected_return_value

        file_bytes = b"%PDF-my file contents"
        data = {"file": (io.BytesIO(file_bytes), "test_file.txt"), "template": "bank of america"}
        response = self.app.post("/validate_metadata", data=data, content_type="multipart/form-data")

        mock_validate_metadata.assert_called_once_with(file_bytes, "bank of america")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode("utf-8")), expected_return_value)

    @patch("docuverus.app.api.detect_template")
    def test_detect_template_delegates_to_public_api(self, mock_detect_template):
        expected_return_value = {
            "auto_select": True,
            "template_name": "Ally",
            "category": "Bank Statements",
            "document_class": "Bank Statement",
            "confidence": 63,
        }
        mock_detect_template.return_value = expected_return_value
        file_bytes = b"pdf contents"

        response = self.app.post(
            "/detect_template",
            data={"file": (io.BytesIO(file_bytes), "ally.pdf")},
            content_type="multipart/form-data",
        )

        mock_detect_template.assert_called_once_with(file_bytes, "ally.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode("utf-8")), expected_return_value)

    def test_validate_metadata_successfully_returns_analysis_with_real_fraud_detector(self):
        expected_return_value = {"final_validation_results": {"valid": "Pass", "validation_message_code": "MSG_VALID_FILE"}}

        file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
        file_bytes = open(file_path, "rb").read()
        data = {"file": (io.BytesIO(file_bytes), "test_file.txt"), "template": "bank of america"}
        response = self.app.post("/validate_metadata", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        assert_dict_contains(json.loads(response.data.decode("utf-8")), expected_return_value)

    @patch("docuverus.app.api.validate_metadata")
    def test_validate_metadata_preserves_nested_browser_printed_message_codes_in_json_response(self, mock_validate_metadata):
        expected_return_value = {
            "final_validation_results": {"valid": "FDR", "validation_message_code": "MSG_UNKNOWN_TEMPLATE_TYPE"},
            "template_rule_set_validation_results": [
                {
                    "producer": {
                        "actual": "Chrome PDF Printer",
                        "name": "Unknown",
                        "valid": "FDR",
                        "validation_message_code": "MSG_PRODUCER_BROWSER_PRINTED",
                    },
                    "creator": {
                        "actual": "Safari Browser PDF Creator",
                        "name": "Unknown",
                        "valid": "FDR",
                        "validation_message_code": "MSG_CREATOR_BROWSER_PRINTED",
                    },
                }
            ],
        }
        mock_validate_metadata.return_value = expected_return_value

        file_bytes = b"%PDF-my file contents"
        data = {"file": (io.BytesIO(file_bytes), "test_file.txt"), "template": "Completely Unknown Template Type"}
        response = self.app.post("/validate_metadata", data=data, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode("utf-8")), expected_return_value)

    @patch("docuverus.app.PDFUtilities")
    def test_validate_metadata_creates_files_with_additional_fonts_highlighted(self, MockPDFUtilities):
        expected_return_value = "test-return-value"
        MockPDFUtilities.highlight_usages_of_fonts_in_byte_representation_of_pdf.return_value = expected_return_value
        file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
        file_bytes = open(file_path, "rb").read()
        data = {"file": (io.BytesIO(file_bytes), "test_file.txt"), "fonts": "Helvetica"}
        response = self.app.post("/highlight_fonts", data=data, content_type="multipart/form-data")

        print(file_bytes)
        MockPDFUtilities.highlight_usages_of_fonts_in_byte_representation_of_pdf.assert_called_once()
        MockPDFUtilities.highlight_usages_of_fonts_in_byte_representation_of_pdf.assert_called_once_with(file_bytes, "Helvetica", (1, 0, 0))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode("utf-8"), expected_return_value)

    def get_template_names_returns_templates_from_public_api(self, template_names):
        with patch("docuverus.app.api.get_template_names") as mock_get_template_names:
            mock_get_template_names.return_value = list(template_names)

            response = self.app.get("/template_names")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data.decode("utf-8")), list(template_names))


@pytest.fixture
def flask_app_tests():
    test_instance = FlaskAppTests()
    test_instance.setUp()
    return test_instance


@pytest.mark.parametrize("template_names", [{"template1", "template2"}, {"template3"}, {1, "2", "3"}])
def test_get_template_names_returns_templates_from_rule_set_factory(flask_app_tests, template_names):
    flask_app_tests.get_template_names_returns_templates_from_public_api(template_names)
