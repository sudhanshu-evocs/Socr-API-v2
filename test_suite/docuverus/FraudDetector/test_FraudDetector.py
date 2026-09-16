import csv
import io
import json
import os
import logging
from unittest.mock import MagicMock

import pytest

from docuverus.FraudDetector.FraudDetector import FraudDetector
from docuverus.FraudDetector.MetadataExtractor import MetadataExtractor
from docuverus.RuleEvaluators.CompositeRuleEvaluator import (
    CompositeRuleEvaluatorFactory,
)
from docuverus.RuleEvaluators.RuleSetFactory import RuleSetFactory
from docuverus.Utils.FileUtilities import FileUtilities
from test_suite.support.assertions import assert_dict_contains
from test_suite.support.testing_utilities import find_most_similar_template_name


def _assert_invalid_boa_result(result, expected_final_valid):
    assert result["final_validation_results"]["valid"] == expected_final_valid
    assert len(result["template_rule_set_validation_results"]) == 5
    assert result["template_rule_set_validation_results"][0]["file_size"]["min"] == 144
    assert result["template_rule_set_validation_results"][0]["file_size"]["max"] == 424
    assert result["template_rule_set_validation_results"][1]["file_size"]["min"] == 200
    assert result["template_rule_set_validation_results"][1]["file_size"]["max"] == 250
    assert result["template_rule_set_validation_results"][2]["producer"]["name"] == "^iText.*"
    assert result["template_rule_set_validation_results"][4]["file_size"]["min"] == 5


def _create_date_override_candidate_rule():
    return {
        "template": {
            "name": "Any Template",
            "actual": "Any Template",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^ExpectedProducer.*",
            "actual": "ExpectedProducer v1",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "creator": {
            "name": "^ExpectedCreator.*",
            "actual": "ExpectedCreator v1",
            "valid": "Pass",
            "validation_message_code": "MSG_CREATOR_MATCH",
        },
        "author": {
            "name": "",
            "actual": "",
            "valid": "Pass",
            "validation_message_code": "MSG_AUTHOR_MATCH",
        },
        "file_size": {
            "algorithm": "Unknown",
            "actual": 123.0,
            "valid": "Pass",
            "validation_message_code": "MSG_VALID_FILE_SIZE_UNKNOWN",
        },
        "fonts": {
            "required_fonts": [],
            "optional_fonts": [],
            "additional_fonts": [],
            "valid": "Pass",
            "validation_message_code": "MSG_FONT_VALIDATION_VALID",
        },
        "dates": {
            "created": {
                "state": "Present",
                "actual": "D:20230829193231-05'00'",
                "valid": "Pass",
                "validation_message_code": "MSG_CREATION_DATE_FOUND",
            },
            "modified": {
                "state": "Equal",
                "actual": "D:20230829203231-05'00'",
                "valid": "Fail",
                "validation_message_code": "MSG_DATES_INVALID_TOLERANCE",
            },
            "valid": "Fail",
            "validation_message_code": "MSG_INVALID_CREATION_MODIFICATION_DATES",
        },
    }


def _create_valid_rule(maximum_validation_level=None):
    rule_set = {
        "template": {
            "name": "Any Template",
            "actual": "Any Template",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^ExpectedProducer.*",
            "actual": "ExpectedProducer v1",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "creator": {
            "name": "^ExpectedCreator.*",
            "actual": "ExpectedCreator v1",
            "valid": "Pass",
            "validation_message_code": "MSG_CREATOR_MATCH",
        },
        "author": {
            "name": "",
            "actual": "",
            "valid": "Pass",
            "validation_message_code": "MSG_AUTHOR_MATCH",
        },
        "file_size": {
            "algorithm": "Unknown",
            "actual": 123.0,
            "valid": "Pass",
            "validation_message_code": "MSG_VALID_FILE_SIZE_UNKNOWN",
        },
        "fonts": {
            "required_fonts": [],
            "optional_fonts": [],
            "additional_fonts": [],
            "valid": "Pass",
            "validation_message_code": "MSG_FONT_VALIDATION_VALID",
        },
        "dates": {
            "created": {
                "state": "None",
                "actual": "",
                "valid": "Pass",
                "validation_message_code": "MSG_CREATION_DATE_NOT_FOUND",
            },
            "modified": {
                "state": "None",
                "actual": "",
                "valid": "Pass",
                "validation_message_code": "MSG_MODIFICATION_DATE_NOT_FOUND",
            },
            "valid": "Pass",
            "validation_message_code": "MSG_VALID_CREATION_MODIFICATION_DATES",
        },
    }
    if maximum_validation_level is not None:
        rule_set["template"]["maximum_validation_level"] = maximum_validation_level
    return rule_set


def test_invalid_file_when_file_size_is_too_big_file1():
    # Arrange
    template_type = "Bank of America"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf"
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    _assert_invalid_boa_result(result, expected_final_valid="Fail")
    assert result["final_validation_results"]["validation_message_code"] == "MSG_INVALID_FILE"
    assert result["template_rule_set_validation_results"][0]["producer"]["valid"] == "Fail"


def test_invalid_file_when_file_size_is_too_big_file2():
    # Arrange
    template_type = "Bank of America"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big_2.pdf"
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    _assert_invalid_boa_result(result, expected_final_valid="FDR")
    assert result["final_validation_results"]["validation_message_code"] == "MSG_FURTHER_DOCUMENTATION_REQUIRED"
    assert result["template_rule_set_validation_results"][0]["producer"]["valid"] == "Pass"


def test_valid_results_for_another_valid_bank_of_america_statement():
    # Arrange
    template_type = "Bank of America"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"

    expected_result = {
        "template": {
            "name": "Bank of America",
            "actual": "Bank of America",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^TargetStream.*",
            "actual": "TargetStream StreamEDS rv1.7.41 for Bank of America",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "file_size": {
            "min": 144,
            "max": 424,
            "algorithm": "Constant",
            "actual": 308.695,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        },
    }
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    assert_dict_contains(result["template_rule_set_validation_results"][0], expected_result)


def test_valid_results_for_valid_td_bank_statement_to_validate_document():
    # Arrange
    template_type = "TD Bank"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Valid_TD_Bank_Statement_ios.pdf"

    expected_result = {
        "template": {
            "name": "TD Bank",
            "actual": "TD Bank",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^iOS Version.*",
            "actual": "iOS Version 16.3.1 (Build 20D67) Quartz PDFContext",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "file_size": {
            "min": 130,
            "max": 400,
            "algorithm": "Constant",
            "actual": 158.519,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        },
    }
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    assert_dict_contains(result["template_rule_set_validation_results"][0], expected_result)


def test_valid_results_for_valid_td_bank_statement_with_different_file_size_range_to_validate_document():
    # Arrange
    template_type = "TD Bank"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Valid_TD_Bank_Statement_opentext.pdf"

    expected_result = {
        "template": {
            "name": "TD Bank",
            "actual": "TD Bank",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^OpenText Output Transformation Engine.*",
            "actual": "OpenText Output Transformation Engine - 16.4.50                                                     ",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "file_size": {
            "min": 910,
            "max": 1100,
            "algorithm": "Constant",
            "actual": 956.42,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        },
    }
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    assert_dict_contains(result["template_rule_set_validation_results"][0], expected_result)


def test_valid_results_for_invalid_paychex_paystub():
    # Arrange
    template_type = "Paychex"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Invalid_paychex_for_file_size.pdf"

    expected_result = {
        "template": {
            "name": "Paychex",
            "actual": "Paychex",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^iText.*",
            "actual": "iText® 5.5.13.3 ©2000-2022 iText Group NV (AGPL-version)",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "file_size": {
            "min": 6,
            "max": 13,
            "algorithm": "Constant",
            "actual": 806.833,
            "valid": "Fail",
            "validation_message_code": "MSG_FILE_SIZE_INVALID",
        },
    }
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    assert result["final_validation_results"]["valid"] == "Fail"
    assert_dict_contains(result["template_rule_set_validation_results"][0], expected_result)


def test_valid_results_for_valid_paycor_single_page_paystub():
    # Arrange
    template_type = "Paycor"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Valid_paycor_1_page_paystub.pdf"

    expected_result = {
        "template": {
            "name": "Paycor",
            "actual": "Paycor",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^DynamicPDF Core Suite.*",
            "actual": "DynamicPDF Core Suite (Generator, Merger and ReportWriter) for .NET v11.42",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "file_size": {
            "min": 20,
            "max": 105,
            "algorithm": "Constant",
            "actual": 40.574,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        },
    }
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    assert_dict_contains(result["template_rule_set_validation_results"][0], expected_result)


def test_valid_font_metadata_for_paycor_paystub():
    template_type = "Paycor"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Valid_Paycor_Paystub_for_fonts.pdf"
    expected_result = {
        "fonts": {
            "required_fonts": [
                {
                    "name": "Helvetica",
                    "type": "",
                    "encoding": "",
                    "multiplicity": 1,
                    "actual_multiplicity": 1,
                    "valid": "Pass",
                    "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                },
                {
                    "name": "Helvetica-Bold",
                    "type": "",
                    "encoding": "",
                    "multiplicity": 1,
                    "actual_multiplicity": 1,
                    "valid": "Pass",
                    "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                },
                {
                    "name": "MICR",
                    "type": "",
                    "encoding": "",
                    "multiplicity": 1,
                    "actual_multiplicity": 1,
                    "valid": "Pass",
                    "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                },
            ],
            "optional_fonts": [
                {
                    "name": "ArialMT",
                    "type": "",
                    "encoding": "",
                    "multiplicity": 9999,
                    "actual_multiplicity": 1,
                    "valid": "Pass",
                    "validation_message_code": "MSG_OPTIONAL_FONT_MATCHED",
                }
            ],
            "additional_fonts": [],
            "valid": "Pass",
            "validation_message_code": "MSG_FONT_VALIDATION_VALID",
        }
    }

    result = fraud_detector.get_document_validations(file_path)

    print(result)
    assert_dict_contains(result["template_rule_set_validation_results"][0], expected_result)


def test_fraud_detector_is_not_case_sensitive_with_template_names():
    template_type = "intuit1"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )

    result = fraud_detector.get_document_validations("../test_documents/Valid_intuit_paystub.pdf")

    assert result["template_rule_set_validation_results"][0]["template"]["valid"] == "Pass"


def test_fraud_detector_is_not_case_sensitive_with_template_names_when_multiple_rulesets_for_template():
    template_type = "accenture"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )

    result = fraud_detector.get_document_validations("../test_documents/Invalid_accenture_paystub.pdf")

    assert result["template_rule_set_validation_results"][0]["template"]["valid"] == "Pass"


@pytest.mark.parametrize(
    ("maximum_validation_level", "expected_valid_state"),
    [
        ("FDR", "FDR"),
        ("Fail", "Fail"),
    ],
)
def test_maximum_validation_level_clamps_passing_result(maximum_validation_level, expected_valid_state):
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_valid_rule(maximum_validation_level=maximum_validation_level)]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "ExpectedProducer v1", "creator": "ExpectedCreator v1", "author": "", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": expected_valid_state,
        "validation_message_code": "MSG_FURTHER_VALIDATION_REQUIRED_UNTRUSTED_TEMPLATE",
    }
    assert result["template_rule_set_validation_results"][0]["template"]["valid"] == "Pass"


@pytest.mark.parametrize("template_type", ["No", " no ", "Unknown", " UNKNOWN "])
def test_maximum_validation_level_uses_unknown_template_code_for_no_and_unknown_templates(template_type):
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_valid_rule(maximum_validation_level="FDR")]

    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "ExpectedProducer v1", "creator": "ExpectedCreator v1", "author": "", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_VALIDATION_REQUIRED_UNKNOWN_TEMPLATE",
    }
    assert result["template_rule_set_validation_results"][0]["template"]["valid"] == "Pass"


def test_maximum_validation_level_clamps_date_override_result_to_fail():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_date_override_candidate_rule()]
    mock_rule_set_factory.get_template_rules.return_value[0]["template"]["maximum_validation_level"] = "Fail"

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {
        "creationDate": "D:20230829193231-05'00'",
        "modDate": "D:20230829203231-05'00'",
        "producer": "ExpectedProducer v1",
        "creator": "ExpectedCreator v1",
        "author": "",
        "image_file": False,
    }
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "Fail",
        "validation_message_code": "MSG_FURTHER_VALIDATION_REQUIRED_UNTRUSTED_TEMPLATE",
    }
    assert result["template_rule_set_validation_results"][0]["dates"]["valid"] == "FDR"


def test_maximum_validation_level_does_not_change_result_when_maximum_is_pass():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_valid_rule(maximum_validation_level="Pass")]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "ExpectedProducer v1", "creator": "ExpectedCreator v1", "author": "", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "Pass",
        "validation_message_code": "MSG_VALID_FILE",
    }


def test_maximum_validation_level_uses_most_restrictive_rule_set_in_unknown_result():
    first_rule_set = _create_invalid_known_template_rule()
    first_rule_set["template"]["maximum_validation_level"] = "Pass"
    second_rule_set = _create_invalid_known_template_rule()
    second_rule_set["template"]["maximum_validation_level"] = "Fail"
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [first_rule_set, second_rule_set]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "TargetStream StreamEDS", "creator": "Any Creator", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "Fail",
        "validation_message_code": "MSG_FURTHER_VALIDATION_REQUIRED_UNTRUSTED_TEMPLATE",
    }


def test_maximum_validation_level_result_preserves_untrusted_template_message_when_selected_fonts_fail():
    browser_printed_rule_set = _create_browser_printed_rule(fonts_valid="Fail")
    browser_printed_rule_set["template"]["maximum_validation_level"] = "Fail"
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [browser_printed_rule_set]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Chrome PDF Printer", "creator": "ExpectedCreator v1", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "Fail",
        "validation_message_code": "MSG_FURTHER_VALIDATION_REQUIRED_UNTRUSTED_TEMPLATE",
    }


def test_fraud_detector_gracefully_handles_empty_pdf_file():
    fraud_detector = FraudDetector(
        "Citizens Bank",
        rule_evaluator=CompositeRuleEvaluatorFactory.create("Citizens Bank"),
    )

    result = fraud_detector.get_document_validations("../test_documents/Invalid_Empty_PDF.pdf")

    assert result["final_validation_results"] == {
        "valid": "Fail",
        "validation_message_code": "MSG_INVALID_PDF_FILE",
    }


def test_fraud_detector_gracefully_handles_non_pdf_file():
    fraud_detector = FraudDetector(
        "Citizens Bank",
        rule_evaluator=CompositeRuleEvaluatorFactory.create("Citizens Bank"),
    )

    result = fraud_detector.get_document_validations("test_FraudDetector.py")

    assert result["final_validation_results"] == {
        "valid": "Fail",
        "validation_message_code": "MSG_INVALID_PDF_FILE",
    }


def test_fraud_detector_gracefully_handles_image_pdf_file():
    fraud_detector = FraudDetector(
        "Citizens Bank",
        rule_evaluator=CompositeRuleEvaluatorFactory.create("Citizens Bank"),
    )

    result = fraud_detector.get_document_validations("../test_documents/Invalid_Image_PDF.pdf")

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_INVALID_IMAGE_DOCUMENT",
    }
    image_rule_set = result["template_rule_set_validation_results"][0]
    assert image_rule_set["template"] == {
        "actual": "Citizens Bank",
        "valid": "NOT_APPLICABLE",
        "validation_message_code": "MSG_NOT_APPLICABLE",
    }
    assert "name" not in image_rule_set["template"]
    assert image_rule_set["producer"]["actual"] == "Microsoft: Print To PDF"
    assert image_rule_set["producer"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["producer"]["validation_message_code"] == "MSG_NOT_APPLICABLE"
    assert "name" not in image_rule_set["producer"]
    assert image_rule_set["creator"]["actual"] == ""
    assert image_rule_set["creator"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["creator"]["validation_message_code"] == "MSG_NOT_APPLICABLE"
    assert "name" not in image_rule_set["creator"]
    assert image_rule_set["author"]["actual"] == "Jim M"
    assert image_rule_set["author"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["author"]["validation_message_code"] == "MSG_NOT_APPLICABLE"
    assert "name" not in image_rule_set["author"]
    assert image_rule_set["file_size"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["file_size"]["validation_message_code"] == "MSG_NOT_APPLICABLE"
    assert "algorithm" not in image_rule_set["file_size"]
    assert image_rule_set["dates"]["created"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["dates"]["created"]["validation_message_code"] == "MSG_NOT_APPLICABLE"
    assert "state" not in image_rule_set["dates"]["created"]
    assert image_rule_set["dates"]["modified"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["dates"]["modified"]["validation_message_code"] == "MSG_NOT_APPLICABLE"
    assert "state" not in image_rule_set["dates"]["modified"]
    assert image_rule_set["dates"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["dates"]["validation_message_code"] == "MSG_NOT_APPLICABLE"
    assert image_rule_set["fonts"] == {}


def test_image_metadata_skips_rule_evaluators_and_returns_not_applicable_rule_set():
    empty_rule_set = {
        "template": {
            "name": "",
            "actual": "Any Template",
            "valid": "Fail",
            "validation_message_code": "MSG_TEMPLATE_TYPE_DOES_NOT_EXIST",
        },
        "file_size": {"algorithm": "Unknown"},
        "dates": {"created": {"state": "Unknown"}, "modified": {"state": "Unknown"}},
        "fonts": {},
        "producer": {"name": "Unknown"},
        "creator": {"name": "Unknown"},
        "author": {"name": "Unknown"},
    }
    mock_rule_evaluator = MagicMock()
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.create_empty_rule_set.return_value = empty_rule_set

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=mock_rule_evaluator,
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {
        "image_file": True,
        "template": "Any Template",
        "producer": "Chrome",
        "creator": "Safari",
        "author": "Jane Doe",
        "file_size": 123.45,
        "creationDate": "D:20200101000000",
        "modDate": "D:20200102000000",
    }
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_INVALID_IMAGE_DOCUMENT",
    }
    mock_rule_set_factory.get_template_rules.assert_not_called()
    mock_rule_evaluator.evaluate.assert_not_called()
    image_rule_set = result["template_rule_set_validation_results"][0]
    assert image_rule_set["template"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["template"]["validation_message_code"] == "MSG_NOT_APPLICABLE"
    assert "name" not in image_rule_set["template"]
    assert image_rule_set["producer"]["actual"] == "Chrome"
    assert image_rule_set["producer"]["valid"] == "NOT_APPLICABLE"
    assert "name" not in image_rule_set["producer"]
    assert image_rule_set["creator"]["actual"] == "Safari"
    assert image_rule_set["creator"]["valid"] == "NOT_APPLICABLE"
    assert "name" not in image_rule_set["creator"]
    assert image_rule_set["author"]["actual"] == "Jane Doe"
    assert image_rule_set["author"]["valid"] == "NOT_APPLICABLE"
    assert "name" not in image_rule_set["author"]
    assert image_rule_set["file_size"]["actual"] == 123.45
    assert image_rule_set["file_size"]["valid"] == "NOT_APPLICABLE"
    assert "algorithm" not in image_rule_set["file_size"]
    assert image_rule_set["dates"]["created"]["actual"] == "D:20200101000000"
    assert image_rule_set["dates"]["created"]["valid"] == "NOT_APPLICABLE"
    assert "state" not in image_rule_set["dates"]["created"]
    assert image_rule_set["dates"]["modified"]["actual"] == "D:20200102000000"
    assert image_rule_set["dates"]["modified"]["valid"] == "NOT_APPLICABLE"
    assert "state" not in image_rule_set["dates"]["modified"]
    assert image_rule_set["dates"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["fonts"] == {}


def test_image_metadata_unknown_template_returns_empty_rule_set_with_image_failure_code():
    empty_rule_set = {
        "template": {
            "name": "",
            "actual": "Unknown Image Template",
            "valid": "Fail",
            "validation_message_code": "MSG_TEMPLATE_TYPE_DOES_NOT_EXIST",
        },
        "file_size": {"algorithm": "Unknown"},
        "dates": {"created": {"state": "Unknown"}, "modified": {"state": "Unknown"}},
        "fonts": {},
        "producer": {"name": "Unknown"},
        "creator": {"name": "Unknown"},
        "author": {"name": "Unknown"},
    }
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.create_empty_rule_set.return_value = empty_rule_set
    mock_rule_evaluator = MagicMock()

    fraud_detector = FraudDetector(
        "Unknown Image Template",
        rule_evaluator=mock_rule_evaluator,
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"image_file": True, "template": "Unknown Image Template", "producer": "Safari", "creator": "", "author": ""}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_INVALID_IMAGE_DOCUMENT",
    }
    mock_rule_set_factory.get_template_rules.assert_not_called()
    mock_rule_evaluator.evaluate.assert_not_called()
    image_rule_set = result["template_rule_set_validation_results"][0]
    assert image_rule_set["template"]["actual"] == "Unknown Image Template"
    assert image_rule_set["template"]["valid"] == "NOT_APPLICABLE"
    assert image_rule_set["template"]["validation_message_code"] == "MSG_NOT_APPLICABLE"
    assert "name" not in image_rule_set["template"]
    assert image_rule_set["producer"]["actual"] == "Safari"
    assert image_rule_set["producer"]["valid"] == "NOT_APPLICABLE"
    assert "name" not in image_rule_set["producer"]
    assert "state" not in image_rule_set["dates"]["created"]
    assert "state" not in image_rule_set["dates"]["modified"]
    assert "algorithm" not in image_rule_set["file_size"]
    assert image_rule_set["fonts"] == {}


def _create_invalid_known_template_rule():
    return {
        "template": {
            "name": "Any Template",
            "actual": "Any Template",
            "valid": "Fail",
            "validation_message_code": "MSG_TEMPLATE_TYPE_DOES_NOT_MATCH",
        },
        "producer": {"name": "^ExpectedProducer.*", "valid": "Fail", "validation_message_code": "MSG_PRODUCER_DOES_NOT_MATCH"},
        "creator": {"name": "^ExpectedCreator.*", "valid": "Fail", "validation_message_code": "MSG_CREATOR_DOES_NOT_MATCH"},
    }


def _create_unknown_result_candidate_rule(
    template_name,
    producer_valid="Fail",
    creator_valid="Fail",
    fonts_valid="Fail",
    dates_valid="Fail",
    file_size_valid="Fail",
):
    return {
        "template": {
            "name": template_name,
            "actual": "Any Template",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^ExpectedProducer.*",
            "actual": "Actual Producer",
            "valid": producer_valid,
            "validation_message_code": "MSG_PRODUCER_MATCH" if producer_valid == "Pass" else "MSG_PRODUCER_DOES_NOT_MATCH",
        },
        "creator": {
            "name": "^ExpectedCreator.*",
            "actual": "Actual Creator",
            "valid": creator_valid,
            "validation_message_code": "MSG_CREATOR_MATCH" if creator_valid == "Pass" else "MSG_CREATOR_DOES_NOT_MATCH",
        },
        "author": {
            "name": "",
            "actual": "",
            "valid": "Fail",
            "validation_message_code": "MSG_AUTHOR_DOES_NOT_MATCH",
        },
        "fonts": {
            "required_fonts": [],
            "optional_fonts": [],
            "additional_fonts": [],
            "valid": fonts_valid,
            "validation_message_code": "MSG_FONT_VALIDATION_VALID" if fonts_valid == "Pass" else "MSG_FONT_VALIDATION_INVALID",
        },
        "dates": {
            "created": {"state": "None", "actual": "", "valid": "Pass", "validation_message_code": "MSG_CREATION_DATE_NOT_FOUND"},
            "modified": {"state": "None", "actual": "", "valid": "Pass", "validation_message_code": "MSG_MODIFICATION_DATE_NOT_FOUND"},
            "valid": dates_valid,
            "validation_message_code": (
                "MSG_VALID_CREATION_MODIFICATION_DATES"
                if dates_valid == "Pass"
                else "MSG_INVALID_CREATION_MODIFICATION_DATES"
            ),
        },
        "file_size": {
            "algorithm": "Unknown",
            "actual": 123.0,
            "valid": file_size_valid,
            "validation_message_code": "MSG_VALID_FILE_SIZE_UNKNOWN" if file_size_valid != "Fail" else "MSG_FILE_SIZE_INVALID",
        },
    }


def _create_browser_printed_rule(fonts_valid="Pass", file_size_valid="Pass"):
    return {
        "template": {
            "name": "Any Template",
            "actual": "Any Template",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^ExpectedProducer.*",
            "actual": "Chrome PDF Printer",
            "valid": "FDR",
            "validation_message_code": "MSG_PRODUCER_BROWSER_PRINTED",
        },
        "creator": {
            "name": "^ExpectedCreator.*",
            "actual": "ExpectedCreator v1",
            "valid": "Pass",
            "validation_message_code": "MSG_CREATOR_MATCH",
        },
        "author": {
            "name": "",
            "actual": "",
            "valid": "Pass",
            "validation_message_code": "MSG_AUTHOR_MATCH",
        },
        "file_size": {
            "algorithm": "Unknown",
            "actual": 123.0,
            "valid": file_size_valid,
            "validation_message_code": "MSG_VALID_FILE_SIZE_UNKNOWN",
        },
        "fonts": {
            "required_fonts": [],
            "optional_fonts": [],
            "additional_fonts": [],
            "valid": fonts_valid,
            "validation_message_code": "MSG_FONT_RULE_NOT_APPLICABLE",
        },
        "dates": {
            "created": {"state": "None", "actual": "", "valid": "Pass", "validation_message_code": "MSG_CREATION_DATE_NOT_FOUND"},
            "modified": {"state": "None", "actual": "", "valid": "Pass", "validation_message_code": "MSG_MODIFICATION_DATE_NOT_FOUND"},
            "valid": "Pass",
            "validation_message_code": "MSG_VALID_CREATION_MODIFICATION_DATES",
        },
    }


def test_browser_printed_metadata_invalid_known_template_when_producer_has_matching_prefix():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [
        {
            **_create_invalid_known_template_rule(),
            "producer": {
                "name": "^ExpectedProducer.*",
                "actual": "Chrome PDF Printer",
                "valid": "FDR",
                "validation_message_code": "MSG_PRODUCER_BROWSER_PRINTED",
            },
        }
    ]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Chrome PDF Printer", "creator": "Any Creator", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_BROWSER_PRINTED_DOCUMENT",
    }


def test_unknown_result_rule_sets_are_sorted_by_producer_then_creator_then_fonts_then_dates_then_file_size():
    best_producer = _create_unknown_result_candidate_rule("Best Producer", producer_valid="Pass")
    best_creator = _create_unknown_result_candidate_rule("Best Creator", producer_valid="FDR", creator_valid="Pass")
    best_fonts = _create_unknown_result_candidate_rule("Best Fonts", producer_valid="FDR", creator_valid="FDR", fonts_valid="Pass")
    best_dates = _create_unknown_result_candidate_rule(
        "Best Dates", producer_valid="FDR", creator_valid="FDR", fonts_valid="FDR", dates_valid="Pass"
    )
    best_file_size = _create_unknown_result_candidate_rule(
        "Best File Size", producer_valid="FDR", creator_valid="FDR", fonts_valid="FDR", dates_valid="FDR", file_size_valid="Pass"
    )
    worst_match = _create_unknown_result_candidate_rule("Worst Match")
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [
        worst_match,
        best_file_size,
        best_dates,
        best_fonts,
        best_creator,
        best_producer,
    ]

    fraud_detector = FraudDetector("Any Template", rule_evaluator=MagicMock(), rule_set_factory=mock_rule_set_factory)

    result = fraud_detector.get_document_validations_for_metadata({"producer": "Any Producer", "creator": "Any Creator", "image_file": False})

    assert [rule_set["template"]["name"] for rule_set in result["template_rule_set_validation_results"]] == [
        "Best Producer",
        "Best Creator",
        "Best Fonts",
        "Best Dates",
        "Best File Size",
        "Worst Match",
    ]
    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }


def test_unknown_result_rule_sets_treat_fdr_and_not_applicable_as_tied_and_preserve_input_order():
    first_middle = _create_unknown_result_candidate_rule("First Middle", producer_valid="FDR", creator_valid="NOT_APPLICABLE")
    second_middle = _create_unknown_result_candidate_rule("Second Middle", producer_valid="NOT_APPLICABLE", creator_valid="FDR")
    stronger_match = _create_unknown_result_candidate_rule("Stronger Match", producer_valid="Pass")
    weaker_match = _create_unknown_result_candidate_rule("Weaker Match")
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [
        second_middle,
        weaker_match,
        first_middle,
        stronger_match,
    ]

    fraud_detector = FraudDetector("Any Template", rule_evaluator=MagicMock(), rule_set_factory=mock_rule_set_factory)

    result = fraud_detector.get_document_validations_for_metadata({"producer": "Any Producer", "creator": "Any Creator", "image_file": False})

    assert [rule_set["template"]["name"] for rule_set in result["template_rule_set_validation_results"]] == [
        "Stronger Match",
        "Second Middle",
        "First Middle",
        "Weaker Match",
    ]


def test_unknown_result_with_first_rule_set_font_failure_returns_fdr():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_unknown_result_candidate_rule("Only Candidate")]

    fraud_detector = FraudDetector("Any Template", rule_evaluator=MagicMock(), rule_set_factory=mock_rule_set_factory)

    result = fraud_detector.get_document_validations_for_metadata({"producer": "Any Producer", "creator": "Any Creator", "image_file": False})

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }


def test_unknown_result_ignores_font_failure_in_non_selected_rule_set():
    better_match = _create_unknown_result_candidate_rule("Better Match", producer_valid="Pass", fonts_valid="Pass")
    worse_match = _create_unknown_result_candidate_rule("Worse Match")
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [worse_match, better_match]

    fraud_detector = FraudDetector("Any Template", rule_evaluator=MagicMock(), rule_set_factory=mock_rule_set_factory)

    result = fraud_detector.get_document_validations_for_metadata({"producer": "Any Producer", "creator": "Any Creator", "image_file": False})

    assert [rule_set["template"]["name"] for rule_set in result["template_rule_set_validation_results"]] == [
        "Better Match",
        "Worse Match",
    ]
    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }


def test_browser_printed_metadata_invalid_known_template_when_creator_has_matching_prefix():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [
        {
            **_create_invalid_known_template_rule(),
            "creator": {
                "name": "^ExpectedCreator.*",
                "actual": "Safari Browser PDF Creator",
                "valid": "FDR",
                "validation_message_code": "MSG_CREATOR_BROWSER_PRINTED",
            },
        }
    ]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Any Producer", "creator": "Safari Browser PDF Creator", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_BROWSER_PRINTED_DOCUMENT",
    }


def test_browser_printed_metadata_with_unknown_fonts_returns_browser_printed_document():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_browser_printed_rule(fonts_valid="FDR")]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Chrome PDF Printer", "creator": "ExpectedCreator v1", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_BROWSER_PRINTED_DOCUMENT",
    }


def test_browser_printed_metadata_with_font_failure_returns_fdr_and_preserves_message_code():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_browser_printed_rule(fonts_valid="Fail")]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Chrome PDF Printer", "creator": "ExpectedCreator v1", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_BROWSER_PRINTED_DOCUMENT",
    }


def test_browser_printed_metadata_with_not_applicable_file_size_returns_browser_printed_document():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_browser_printed_rule(file_size_valid="NOT_APPLICABLE")]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Chrome PDF Printer", "creator": "ExpectedCreator v1", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_BROWSER_PRINTED_DOCUMENT",
    }


def test_browser_printed_metadata_with_valid_fonts_and_file_size_returns_valid_file():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_browser_printed_rule()]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Chrome PDF Printer", "creator": "ExpectedCreator v1", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "Pass",
        "validation_message_code": "MSG_VALID_FILE",
    }


def test_browser_printed_metadata_invalid_unknown_template_when_prefix_matches():
    unknown_rule_set = {
        "template": {
            "name": "",
            "actual": "Unknown Template",
            "valid": "Fail",
            "validation_message_code": "MSG_TEMPLATE_TYPE_DOES_NOT_EXIST",
        },
        "file_size": {"algorithm": "Unknown"},
        "dates": {"created": {"state": "Unknown"}, "modified": {"state": "Unknown"}},
        "fonts": {},
        "producer": {"name": "Unknown"},
        "creator": {"name": "Unknown"},
        "author": {"name": "Unknown"},
    }
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = []
    mock_rule_set_factory.create_empty_rule_set.return_value = unknown_rule_set

    fraud_detector = FraudDetector(
        "Unknown Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Chrome PDF", "creator": "Any Creator", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_UNKNOWN_TEMPLATE_TYPE",
    }


def test_browser_printed_metadata_invalid_known_template_when_no_prefix_match_returns_invalid_file():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_invalid_known_template_rule()]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "TargetStream StreamEDS", "creator": "Bank Statement Engine", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }


def test_browser_printed_metadata_invalid_known_template_when_token_is_not_prefix_returns_invalid_file():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_invalid_known_template_rule()]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Generated in Chrome Browser", "creator": "Any Creator", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }


def test_browser_printed_metadata_invalid_known_template_when_prefix_matches_after_whitespace():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_invalid_known_template_rule()]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "   Chrome PDF Printer   ", "creator": "Any Creator", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }


def test_unknown_result_logs_warning_for_known_template_fallback(caplog):
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_invalid_known_template_rule()]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "TargetStream StreamEDS", "creator": "Bank Statement Engine", "image_file": False}

    with caplog.at_level(logging.WARNING):
        result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }
    assert "FraudDetector fell through to unknown result for template 'Any Template'" in caplog.text
    assert "'producer': 'Fail'" in caplog.text


def test_date_override_returns_fdr_when_other_validators_pass_and_modification_is_less_than_five_hours():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_date_override_candidate_rule()]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {
        "creationDate": "D:20230829193231-05'00'",
        "modDate": "D:20230829203231-05'00'",
        "producer": "ExpectedProducer v1",
        "creator": "ExpectedCreator v1",
        "author": "",
        "image_file": False,
    }
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO",
    }
    assert result["template_rule_set_validation_results"][0]["dates"]["valid"] == "FDR"
    assert result["template_rule_set_validation_results"][0]["dates"]["modified"]["valid"] == "FDR"
    assert result["template_rule_set_validation_results"][0]["dates"]["modified"]["validation_message_code"] == (
        "MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO"
    )


def test_date_override_allows_font_rule_not_applicable_when_other_validators_pass():
    mock_rule_set_factory = MagicMock()
    rule_set = _create_date_override_candidate_rule()
    rule_set["fonts"]["valid"] = "FDR"
    rule_set["fonts"]["validation_message_code"] = "MSG_FONT_RULE_NOT_APPLICABLE"
    rule_set["fonts"]["additional_fonts"] = [
        {
            "name": "NimbusSans-Bold",
            "type": "Type0",
            "encoding": "Identity-H",
            "actual_multiplicity": 1,
            "multiplicity": 0,
            "valid": "FDR",
            "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
        }
    ]
    mock_rule_set_factory.get_template_rules.return_value = [rule_set]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {
        "creationDate": "D:20230829193231-05'00'",
        "modDate": "D:20230829203231-05'00'",
        "producer": "ExpectedProducer v1",
        "creator": "ExpectedCreator v1",
        "author": "",
        "image_file": False,
    }
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO",
    }
    assert result["template_rule_set_validation_results"][0]["fonts"]["valid"] == "FDR"
    assert result["template_rule_set_validation_results"][0]["dates"]["valid"] == "FDR"


def test_date_override_does_not_trigger_when_modification_is_five_hours_or_more():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_date_override_candidate_rule()]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {
        "creationDate": "D:20230829193231-05'00'",
        "modDate": "D:20230830013231-05'00'",
        "producer": "ExpectedProducer v1",
        "creator": "ExpectedCreator v1",
        "author": "",
        "image_file": False,
    }
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }


def test_date_override_does_not_trigger_when_another_validator_fails():
    mock_rule_set_factory = MagicMock()
    rule_set = _create_date_override_candidate_rule()
    rule_set["producer"]["valid"] = "Fail"
    rule_set["producer"]["validation_message_code"] = "MSG_PRODUCER_DOES_NOT_MATCH"
    mock_rule_set_factory.get_template_rules.return_value = [rule_set]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {
        "creationDate": "D:20230829193231-05'00'",
        "modDate": "D:20230829203231-05'00'",
        "producer": "Unexpected Producer",
        "creator": "ExpectedCreator v1",
        "author": "",
        "image_file": False,
    }
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }


def test_date_override_does_not_recheck_rule_sets_that_already_pass():
    mock_rule_set_factory = MagicMock()
    passing_rule_set = _create_date_override_candidate_rule()
    passing_rule_set["dates"]["modified"]["valid"] = "Pass"
    passing_rule_set["dates"]["modified"]["validation_message_code"] = "MSG_VALID_MODIFICATION_DATE"
    passing_rule_set["dates"]["valid"] = "Pass"
    passing_rule_set["dates"]["validation_message_code"] = "MSG_VALID_CREATION_MODIFICATION_DATES"
    mock_rule_set_factory.get_template_rules.return_value = [passing_rule_set]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {
        "creationDate": "D:20230829193231-05'00'",
        "modDate": "D:20230829203231-05'00'",
        "producer": "ExpectedProducer v1",
        "creator": "ExpectedCreator v1",
        "author": "",
        "image_file": False,
    }
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "Pass",
        "validation_message_code": "MSG_VALID_FILE",
    }
    assert result["template_rule_set_validation_results"][0]["dates"]["valid"] == "Pass"


def test_invalid_producer_creator_metadata_invalid_known_template_when_raw_metadata_matches_returns_invalid_file():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_invalid_known_template_rule()]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "Adobe Acrobat Pro", "creator": "Any Creator", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "Fail",
        "validation_message_code": "MSG_INVALID_FILE",
    }


def test_invalid_producer_creator_metadata_invalid_known_template_when_creator_matches_returns_invalid_file():
    mock_rule_set_factory = MagicMock()
    mock_rule_set_factory.get_template_rules.return_value = [_create_invalid_known_template_rule()]

    fraud_detector = FraudDetector(
        "Any Template",
        rule_evaluator=MagicMock(),
        rule_set_factory=mock_rule_set_factory,
    )

    metadata = {"producer": "ExpectedProducer Engine", "creator": "Adobe Photoshop 2024", "image_file": False}
    result = fraud_detector.get_document_validations_for_metadata(metadata)

    assert result["final_validation_results"] == {
        "valid": "Fail",
        "validation_message_code": "MSG_INVALID_FILE",
    }


def test_valid_results_for_valid_paycor_single_page_paystub_for_complete_metadata_values():
    # Arrange
    template_type = "Paycor"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Valid_paycor_1_page_paystub.pdf"

    expected_result = {
        "template_rule_set_validation_results": [
            {
                "template": {
                    "name": "Paycor",
                    "actual": "Paycor",
                    "valid": "Pass",
                    "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
                },
                "author": {
                    "name": "",
                    "actual": "Paycor Inc.",
                    "valid": "Pass",
                    "validation_message_code": "MSG_AUTHOR_MATCH",
                },
                "producer": {
                    "name": "^DynamicPDF Core Suite.*",
                    "actual": "DynamicPDF Core Suite (Generator, Merger and ReportWriter) for .NET v11.42",
                    "valid": "Pass",
                    "validation_message_code": "MSG_PRODUCER_MATCH",
                },
                "creator": {
                    "name": "",
                    "actual": "",
                    "valid": "Pass",
                    "validation_message_code": "MSG_CREATOR_MATCH",
                },
                "file_size": {
                    "min": 20,
                    "max": 105,
                    "algorithm": "Constant",
                    "actual": 40.574,
                    "valid": "Pass",
                    "validation_message_code": "MSG_FILE_SIZE_VALID",
                },
                "fonts": {
                    "required_fonts": [
                        {
                            "name": "Helvetica",
                            "type": "",
                            "encoding": "",
                            "multiplicity": 1,
                            "actual_multiplicity": 1,
                            "valid": "Pass",
                            "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                        },
                        {
                            "name": "Helvetica-Bold",
                            "type": "",
                            "encoding": "",
                            "multiplicity": 1,
                            "actual_multiplicity": 1,
                            "valid": "Pass",
                            "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                        },
                        {
                            "name": "MICR",
                            "type": "",
                            "encoding": "",
                            "multiplicity": 1,
                            "actual_multiplicity": 1,
                            "valid": "Pass",
                            "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                        },
                    ],
                    "optional_fonts": [
                        {
                            "name": "ArialMT",
                            "type": "",
                            "encoding": "",
                            "multiplicity": 9999,
                            "actual_multiplicity": 1,
                            "valid": "Pass",
                            "validation_message_code": "MSG_OPTIONAL_FONT_MATCHED",
                        }
                    ],
                    "additional_fonts": [],
                    "valid": "Pass",
                    "validation_message_code": "MSG_FONT_VALIDATION_VALID",
                },
                "dates": {
                    "created": {
                        "state": "Present",
                        "actual": "D:20240403191414+00'00'",
                        "valid": "Pass",
                        "validation_message_code": "MSG_CREATION_DATE_FOUND",
                    },
                    "modified": {
                        "state": "Equal",
                        "actual": "D:20240403191414+00'00'",
                        "valid": "Pass",
                        "validation_message_code": "MSG_DATES_VALID_TOLERANCE",
                    },
                    "valid": "Pass",
                    "validation_message_code": "MSG_VALID_CREATION_MODIFICATION_DATES",
                },
            }
        ],
        "final_validation_results": {"valid": "Pass", "validation_message_code": "MSG_VALID_FILE"},
    }
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    assert result == expected_result


def test_valid_results_for_valid_Bank_of_America_Statement_for_complete_metadata_values():
    # Arrange
    template_type = "Bank of America"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"

    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    assert result["final_validation_results"] == {"valid": "Pass", "validation_message_code": "MSG_VALID_FILE"}
    assert len(result["template_rule_set_validation_results"]) == 1
    rule = result["template_rule_set_validation_results"][0]
    assert rule["template"]["name"] == "Bank of America"
    assert rule["producer"]["name"] == "^TargetStream.*"
    assert rule["file_size"]["min"] == 144
    assert rule["file_size"]["max"] == 424
    assert rule["fonts"]["valid"] == "Pass"
    assert rule["dates"]["valid"] == "Pass"


def test_valid_results_for_valid_Capital_One_Statement_for_complete_metadata_values():
    # Arrange
    template_type = "Capital One"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Valid_Capital_One_Bank_Statement.pdf"

    expected_result = {
        "template_rule_set_validation_results": [
            {
                "template": {
                    "name": "Capital One",
                    "actual": "Capital One",
                    "valid": "Pass",
                    "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
                },
                "producer": {
                    "name": "^iText.*",
                    "actual": "iText® 7.1.5 ©2000-2019 iText Group NV (CAPITAL ONE SERVICES, LLC; licensed version)",
                    "valid": "Pass",
                    "validation_message_code": "MSG_PRODUCER_MATCH",
                },
                "author": {
                    "actual": "",
                    "name": "",
                    "valid": "Pass",
                    "validation_message_code": "MSG_AUTHOR_MATCH",
                },
                "creator": {
                    "name": "^(Enterprise Imaging|$)",
                    "actual": "",
                    "valid": "Pass",
                    "validation_message_code": "MSG_CREATOR_MATCH",
                },
                "file_size": {
                    "algorithm": "Unknown",
                    "actual": 1601.487,
                    "valid": "NOT_APPLICABLE",
                    "validation_message_code": "MSG_VALID_FILE_SIZE_UNKNOWN",
                },
                "fonts": {
                    "required_fonts": [
                        {
                            "name": "Optimist-Bold",
                            "type": "",
                            "encoding": "",
                            "multiplicity": 1,
                            "actual_multiplicity": 1,
                            "valid": "Pass",
                            "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                        },
                        {
                            "name": "Optimist-Regular",
                            "type": "",
                            "encoding": "",
                            "multiplicity": 1,
                            "actual_multiplicity": 1,
                            "valid": "Pass",
                            "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                        },
                    ],
                    "optional_fonts": [],
                    "additional_fonts": [],
                    "valid": "Pass",
                    "validation_message_code": "MSG_FONT_VALIDATION_VALID",
                },
                "dates": {
                    "created": {
                        "state": "Present",
                        "actual": "D:20230603063852Z",
                        "valid": "Pass",
                        "validation_message_code": "MSG_CREATION_DATE_FOUND",
                    },
                    "modified": {
                        "state": "Equal",
                        "actual": "D:20230603063852Z",
                        "valid": "Pass",
                        "validation_message_code": "MSG_DATES_VALID_TOLERANCE",
                    },
                    "valid": "Pass",
                    "validation_message_code": "MSG_VALID_CREATION_MODIFICATION_DATES",
                },
            }
        ],
        "final_validation_results": {"valid": "Pass", "validation_message_code": "MSG_VALID_FILE"},
    }
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    assert result == expected_result


def test_valid_results_for_valid_Capital_One_Statement_for_complete_metadata_values_by_stream():
    # Arrange
    template_type = "Capital One"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Valid_Capital_One_Bank_Statement.pdf"

    expected_result = {
        "template_rule_set_validation_results": [
            {
                "template": {
                    "name": "Capital One",
                    "actual": "Capital One",
                    "valid": "Pass",
                    "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
                },
                "producer": {
                    "name": "^iText.*",
                    "actual": "iText® 7.1.5 ©2000-2019 iText Group NV (CAPITAL ONE SERVICES, LLC; licensed version)",
                    "valid": "Pass",
                    "validation_message_code": "MSG_PRODUCER_MATCH",
                },
                "author": {
                    "actual": "",
                    "name": "",
                    "valid": "Pass",
                    "validation_message_code": "MSG_AUTHOR_MATCH",
                },
                "creator": {
                    "name": "^(Enterprise Imaging|$)",
                    "actual": "",
                    "valid": "Pass",
                    "validation_message_code": "MSG_CREATOR_MATCH",
                },
                "file_size": {
                    "algorithm": "Unknown",
                    "actual": 1601.487,
                    "valid": "NOT_APPLICABLE",
                    "validation_message_code": "MSG_VALID_FILE_SIZE_UNKNOWN",
                },
                "fonts": {
                    "required_fonts": [
                        {
                            "name": "Optimist-Bold",
                            "type": "",
                            "encoding": "",
                            "multiplicity": 1,
                            "actual_multiplicity": 1,
                            "valid": "Pass",
                            "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                        },
                        {
                            "name": "Optimist-Regular",
                            "type": "",
                            "encoding": "",
                            "multiplicity": 1,
                            "actual_multiplicity": 1,
                            "valid": "Pass",
                            "validation_message_code": "MSG_REQUIRED_FONT_MATCHED",
                        },
                    ],
                    "optional_fonts": [],
                    "additional_fonts": [],
                    "valid": "Pass",
                    "validation_message_code": "MSG_FONT_VALIDATION_VALID",
                },
                "dates": {
                    "created": {
                        "state": "Present",
                        "actual": "D:20230603063852Z",
                        "valid": "Pass",
                        "validation_message_code": "MSG_CREATION_DATE_FOUND",
                    },
                    "modified": {
                        "state": "Equal",
                        "actual": "D:20230603063852Z",
                        "valid": "Pass",
                        "validation_message_code": "MSG_DATES_VALID_TOLERANCE",
                    },
                    "valid": "Pass",
                    "validation_message_code": "MSG_VALID_CREATION_MODIFICATION_DATES",
                },
            }
        ],
        "final_validation_results": {"valid": "Pass", "validation_message_code": "MSG_VALID_FILE"},
    }
    # Act

    metadata = MetadataExtractor().extract_metadata(io.BytesIO(open(file_path, "rb").read()), template_type)
    result = fraud_detector.get_document_validations_for_metadata(metadata)
    # Assert
    assert result == expected_result


def test_invalid_capital_one_bank_statement():
    template_type = "Capital One"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    file_path = "../test_documents/Invalid_Capital_One_Bank_Statement.pdf"
    # Act
    result = fraud_detector.get_document_validations(file_path)
    # Assert
    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_FURTHER_DOCUMENTATION_REQUIRED",
    }
    assert len(result["template_rule_set_validation_results"]) == 6
    assert result["template_rule_set_validation_results"][0]["producer"]["name"] == "^iText.*"
    assert result["template_rule_set_validation_results"][0]["producer"]["valid"] == "Pass"
    assert result["template_rule_set_validation_results"][0]["file_size"]["algorithm"] == "Unknown"
    assert result["template_rule_set_validation_results"][0]["file_size"]["valid"] == "NOT_APPLICABLE"


def test_valid_ally_bank_with_odd_date_format():
    template_type = "Ally"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )
    dates_expected_result = {
        "dates": {
            "created": {
                "state": "Present",
                "actual": "8/6/2020 08:23:08",
                "valid": "Pass",
                "validation_message_code": "MSG_CREATION_DATE_FOUND",
            },
            "modified": {
                "state": "None",
                "actual": "None",
                "valid": "Pass",
                "validation_message_code": "MSG_MODIFICATION_DATE_NOT_FOUND",
            },
            "valid": "Pass",
            "validation_message_code": "MSG_VALID_CREATION_MODIFICATION_DATES",
        }
    }

    file_path = "../test_documents/Valid_Ally_Bank_Statement.pdf"
    result = fraud_detector.get_document_validations(file_path)

    assert result["template_rule_set_validation_results"][0]["dates"] == dates_expected_result["dates"]


def test_fraud_detector_returns_unknown_template_results():
    template_type = "Completely Unknown Template Type"
    fraud_detector = FraudDetector(
        template_type,
        rule_evaluator=CompositeRuleEvaluatorFactory.create(template_type),
    )

    result = fraud_detector.get_document_validations("../test_documents/Valid_Ally_Bank_Statement.pdf")

    assert result["final_validation_results"] == {
        "valid": "FDR",
        "validation_message_code": "MSG_UNKNOWN_TEMPLATE_TYPE",
    }
    assert result["template_rule_set_validation_results"][0]["template"] == {
        "name": "",
        "actual": "Completely Unknown Template Type",
        "valid": "Fail",
        "validation_message_code": "MSG_TEMPLATE_TYPE_DOES_NOT_EXIST",
    }


# The tests below should be marked as skip, and are experimental to find fraud detector issues
@pytest.mark.skip()
def test_build_tsv_file():
    def get_last_two_subdirectories(file_path):
        # Split the file path into components
        path_components = file_path.split(os.sep)

        # Get the last two components
        last_two_components = path_components[-4:]

        # Join the last two components with the directory separator
        return os.sep.join(last_two_components)

    pdf_files = FileUtilities.get_all_files_recursively(
        "D:\Projects\curated_list_jamie1\curated_list_jamie1\Banking\Invalid"
    ) + FileUtilities.get_all_files_recursively("D:\Projects\curated_list_jamie1\curated_list_jamie1\Income\Invalid Income")

    with open("template-file-invalid.csv", "w") as file:
        for pdf in pdf_files:
            template_name = find_most_similar_template_name(pdf)
            file_name = get_last_two_subdirectories(pdf)

            file.write(f"{template_name}\t{file_name}\n")


def get_template_file_tuples_from_tsv_with_base_path(
    tsv_path="template-file.tsv",
    base_path="C:\Workspace\docuverus\dv-automation\RestassuredAPITesting\curated_list_jamie1",
):
    results = []
    with open(tsv_path, "r") as file:
        tsv = csv.reader(file, delimiter="\t")
        for line in tsv:
            results.append((line[0], base_path + "\\" + line[1]))

    return results


@pytest.mark.skip()
def test_template_file_tuples_method():
    template_files = get_template_file_tuples_from_tsv_with_base_path()
    for template, file in template_files:
        print(f"{template}, {file}")


@pytest.mark.skip()
@pytest.mark.parametrize(
    "template_name, file_path",
    get_template_file_tuples_from_tsv_with_base_path(),
)
def test_fraud_detector_on_documents_in_template_file_tsv(template_name, file_path):
    rule_set_factory = RuleSetFactory(
        [
            "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
            "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
        ]
    )
    # find template for file_path
    print(f"Template name: {template_name}: {file_path}")
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_name)

    # Refactor this so that RuleSetFactory is injected into FraudDetector
    fraud_detector = FraudDetector(template_name, rule_evaluator, rule_set_factory)

    result = fraud_detector.get_document_validations(file_path)
    print(json.dumps(result, indent=4))
    assert result["final_validation_results"]["valid"] != "Fail"


@pytest.mark.skip()
@pytest.mark.parametrize(
    "template_name, file_path",
    get_template_file_tuples_from_tsv_with_base_path("template-file-invalid.tsv"),
)
def test_fraud_detector_on_invalid_documents_in_template_file_tsv(template_name, file_path):
    rule_set_factory = RuleSetFactory(
        [
            "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
            "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
        ]
    )
    # find template for file_path
    print(f"Template name: {template_name}: {file_path}")
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_name)

    # Refactor this so that RuleSetFactory is injected into FraudDetector
    fraud_detector = FraudDetector(template_name, rule_evaluator, rule_set_factory)

    result = fraud_detector.get_document_validations(file_path)
    print(json.dumps(result, indent=4))
    assert result["final_validation_results"]["valid"] == "Fail"
