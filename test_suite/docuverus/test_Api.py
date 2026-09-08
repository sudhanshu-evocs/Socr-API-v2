import importlib.resources
import json
from unittest.mock import MagicMock, patch

from docuverus import detect_template, get_template_names, validate_metadata
from docuverus.RuleEvaluators.RuleSetFactory import RuleSetFactory


def _create_unknown_template_metadata(producer, creator):
    return {
        "image_file": False,
        "creationDate": "",
        "modDate": "",
        "producer": producer,
        "creator": creator,
        "author": "",
        "file_size": 1,
        "paystub_count": 0,
        "fonts": [],
    }


def test_validate_metadata_returns_analysis_for_known_valid_pdf():
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    file_bytes = open(file_path, "rb").read()

    result = validate_metadata(pdf_bytes=file_bytes, template_name="bank of america")

    assert result["final_validation_results"]["valid"] == "Pass"
    assert result["final_validation_results"]["validation_message_code"] == "MSG_VALID_FILE"


def test_get_template_names_returns_sorted_names():
    template_names = get_template_names()

    assert template_names == sorted(template_names)
    assert "Bank of America" in template_names


def test_detect_template_auto_selects_ally_bank_statement():
    file_path = "../test_documents/Valid_Ally_Bank_Statement.pdf"
    file_bytes = open(file_path, "rb").read()

    result = detect_template(file_bytes, "Valid_Ally_Bank_Statement.pdf")

    assert result["auto_select"] is True
    assert result["template_name"] == "Ally"
    assert result["category"] == "Bank Statements"
    assert result["document_class"] == "Bank Statement"
    assert result["confidence"] >= 60


def test_validate_metadata_returns_fdr_for_possible_save_as_scenario():
    rule_set = {
        "template": {"name": "Generic_Bank_Statement"},
        "producer": {"name": "^SAP NetWeaver.*"},
        "creator": {"name": "^Form ZPYXXFO.*"},
        "file_size": {"algorithm": "Constant", "min": 1, "max": 20},
        "fonts": {
            "required_fonts": [
                {"name": "Helvetica", "type": "Type1", "encoding": "", "multiplicity": 1},
                {"name": "Helvetica-Bold", "type": "Type1", "encoding": "", "multiplicity": 1},
            ],
            "optional_fonts": [],
        },
        "dates": {
            "created": {"state": "Present"},
            "modified": {"state": "Equal"},
        },
    }
    metadata = {
        "image_file": False,
        "creationDate": "D:20200101000000",
        "modDate": "D:20200101010000",
        "producer": "SAP NetWeaver",
        "creator": "Form ZPYXXFO",
        "author": "",
        "file_size": 10,
        "paystub_count": 0,
        "fonts": [
            {"subtype": "Type1", "name": "Helvetica", "encoding": ""},
            {"subtype": "Type1", "name": "Helvetica-Bold", "encoding": ""},
        ],
    }
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [rule_set]

    with patch("docuverus.api.MetadataExtractor") as mock_metadata_extractor, patch(
        "docuverus.api.create_rule_set_factory", return_value=mock_rule_set_factory
    ):
        mock_metadata_extractor.return_value.extract_metadata.return_value = metadata

        result = validate_metadata(
            pdf_bytes=b"fake pdf bytes",
            template_name="Generic_Bank_Statement",
        )

    assert result["final_validation_results"]["valid"] == "FDR"
    assert result["final_validation_results"]["validation_message_code"] == "MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO"
    assert "reason" not in result["final_validation_results"]


def test_validate_metadata_returns_unknown_template_code_for_unknown_template():
    file_path = "../test_documents/Valid_Ally_Bank_Statement.pdf"
    file_bytes = open(file_path, "rb").read()

    result = validate_metadata(pdf_bytes=file_bytes, template_name="Completely Unknown Template Type")

    assert result["final_validation_results"]["valid"] == "FDR"
    assert result["final_validation_results"]["validation_message_code"] == "MSG_UNKNOWN_TEMPLATE_TYPE"


def test_validate_metadata_returns_unknown_template_fvr_code_for_no_template():
    rule_set = {
        "template": {"name": "No", "maximum_validation_level": "FDR"},
        "producer": {"name": "^SAP NetWeaver.*"},
        "creator": {"name": "^Form ZPYXXFO.*"},
        "file_size": {"algorithm": "Unknown"},
        "fonts": {"required_fonts": [], "optional_fonts": []},
        "dates": {
            "created": {"state": "Present"},
            "modified": {"state": "None"},
        },
    }
    metadata = {
        "image_file": False,
        "creationDate": "D:20200101000000",
        "modDate": "",
        "producer": "SAP NetWeaver",
        "creator": "Form ZPYXXFO",
        "author": "",
        "file_size": 10,
        "paystub_count": 0,
        "fonts": [],
    }
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [rule_set]

    with patch("docuverus.api.MetadataExtractor") as mock_metadata_extractor, patch(
        "docuverus.api.create_rule_set_factory", return_value=mock_rule_set_factory
    ):
        mock_metadata_extractor.return_value.extract_metadata.return_value = metadata

        result = validate_metadata(
            pdf_bytes=b"fake pdf bytes",
            template_name="No",
        )

    assert result["final_validation_results"]["valid"] == "FDR"
    assert result["final_validation_results"]["validation_message_code"] == (
        "MSG_FURTHER_VALIDATION_REQUIRED_UNKNOWN_TEMPLATE"
    )


def test_validate_metadata_unknown_template_preserves_browser_printed_producer_message_code():
    metadata = _create_unknown_template_metadata(producer="Chrome PDF Printer", creator="Any Creator")

    with patch("docuverus.api.MetadataExtractor") as mock_metadata_extractor:
        mock_metadata_extractor.return_value.extract_metadata.return_value = metadata

        result = validate_metadata(pdf_bytes=b"fake pdf bytes", template_name="Completely Unknown Template Type")

    assert result["final_validation_results"]["valid"] == "FDR"
    assert result["final_validation_results"]["validation_message_code"] == "MSG_UNKNOWN_TEMPLATE_TYPE"
    assert result["template_rule_set_validation_results"][0]["producer"]["validation_message_code"] == "MSG_PRODUCER_BROWSER_PRINTED"


def test_validate_metadata_unknown_template_preserves_browser_printed_creator_message_code():
    metadata = _create_unknown_template_metadata(producer="Any Producer", creator="Safari Browser PDF Creator")

    with patch("docuverus.api.MetadataExtractor") as mock_metadata_extractor:
        mock_metadata_extractor.return_value.extract_metadata.return_value = metadata

        result = validate_metadata(pdf_bytes=b"fake pdf bytes", template_name="Completely Unknown Template Type")

    assert result["final_validation_results"]["valid"] == "FDR"
    assert result["final_validation_results"]["validation_message_code"] == "MSG_UNKNOWN_TEMPLATE_TYPE"
    assert result["template_rule_set_validation_results"][0]["creator"]["validation_message_code"] == "MSG_CREATOR_BROWSER_PRINTED"


def test_validate_metadata_unknown_template_preserves_both_browser_printed_message_codes():
    metadata = _create_unknown_template_metadata(producer="Chrome PDF Printer", creator="Safari Browser PDF Creator")

    with patch("docuverus.api.MetadataExtractor") as mock_metadata_extractor:
        mock_metadata_extractor.return_value.extract_metadata.return_value = metadata

        result = validate_metadata(pdf_bytes=b"fake pdf bytes", template_name="Completely Unknown Template Type")

    assert result["final_validation_results"]["valid"] == "FDR"
    assert result["final_validation_results"]["validation_message_code"] == "MSG_UNKNOWN_TEMPLATE_TYPE"
    assert result["template_rule_set_validation_results"][0]["producer"]["validation_message_code"] == "MSG_PRODUCER_BROWSER_PRINTED"
    assert result["template_rule_set_validation_results"][0]["creator"]["validation_message_code"] == "MSG_CREATOR_BROWSER_PRINTED"


def test_public_import_surface_exposes_supported_api():
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    file_bytes = open(file_path, "rb").read()

    result = validate_metadata(pdf_bytes=file_bytes, template_name="bank of america")

    assert isinstance(get_template_names(), list)
    assert result["final_validation_results"]["valid"] == "Pass"


def test_rule_set_factory_can_load_packaged_template_json():
    rule_set_factory = RuleSetFactory(
        [
            "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
            "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
        ]
    )

    template_names = rule_set_factory.get_template_names()

    assert "Bank of America" in template_names


def test_browser_printed_list_json_is_packaged_resource():
    browser_printed_json = importlib.resources.files("docuverus.Utils").joinpath("browserprinted_list.json")
    browser_printed_data = json.loads(browser_printed_json.read_text(encoding="utf-8"))

    assert "browser_printed_list" in browser_printed_data
    assert "Chrome" in browser_printed_data["browser_printed_list"]
