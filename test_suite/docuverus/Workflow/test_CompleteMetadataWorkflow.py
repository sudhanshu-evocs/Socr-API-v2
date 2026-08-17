import io
import json
from unittest import mock

from docuverus.FraudDetector.FraudDetector import FraudDetector
from docuverus.FraudDetector.MultiTemplateFraudDetector import (
    MultiTemplateFraudDetector,
)
from docuverus.TemplateDetector.TemplateDetector import TemplateDetector
from docuverus.Workflow.CompleteMetadataWorkflow import CompleteMetadataWorkflow


def _assert_valid_bank_of_america_result(result, actual_confidence=None):
    assert result["final_validation_results"] == {
        "valid": "Pass",
        "validation_message_code": "MSG_VALID_FILE",
    }
    assert len(result["template_rule_set_validation_results"]) == 1
    rule = result["template_rule_set_validation_results"][0]
    assert rule["template"]["name"] == "Bank of America"
    if actual_confidence is not None:
        assert rule["template"]["actual_confidence"] == actual_confidence
    assert rule["producer"]["name"] == "^TargetStream.*"
    assert rule["file_size"]["min"] == 144
    assert rule["file_size"]["max"] == 424
    assert rule["fonts"]["valid"] == "Pass"
    assert rule["dates"]["valid"] == "Pass"


def _assert_valid_td_bank_result(result):
    assert result["final_validation_results"] == {
        "valid": "Pass",
        "validation_message_code": "MSG_VALID_FILE",
    }
    assert len(result["template_rule_set_validation_results"]) == 1
    rule = result["template_rule_set_validation_results"][0]
    assert rule["template"]["name"] == "TD Bank"
    assert rule["producer"]["name"] == "^OpenText Output Transformation Engine.*"
    assert rule["file_size"]["min"] == 910
    assert rule["file_size"]["max"] == 1100
    assert rule["fonts"]["required_fonts"][1]["name"] == "Arial Bold"
    assert rule["fonts"]["required_fonts"][2]["name"] == "Times-Roman"
    assert rule["fonts"]["valid"] == "Pass"
    assert rule["dates"]["valid"] == "Pass"


def _assert_invalid_bank_of_america_result(result):
    assert result["final_validation_results"] == {
        "valid": "Fail",
        "validation_message_code": "MSG_INVALID_FILE",
    }
    assert len(result["template_rule_set_validation_results"]) == 5
    assert result["template_rule_set_validation_results"][0]["file_size"]["min"] == 144
    assert result["template_rule_set_validation_results"][0]["file_size"]["max"] == 424
    assert result["template_rule_set_validation_results"][1]["file_size"]["min"] == 200
    assert result["template_rule_set_validation_results"][1]["file_size"]["max"] == 250
    assert result["template_rule_set_validation_results"][2]["producer"]["name"] == "^iText.*"
    assert result["template_rule_set_validation_results"][4]["file_size"]["min"] == 5


def test_workflow_with_one_matching_template():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Bank of America", "actual_confidence": 95},
    ]
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    file_bytes = open(file_path, "rb").read()
    workflow = CompleteMetadataWorkflow(mock_template_detector)
    result = workflow.run(io.BytesIO(file_bytes))

    _assert_valid_bank_of_america_result(result[0], actual_confidence=95)


def test_workflow_with_one_matching_template_with_different_file():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "TD Bank", "actual_confidence": 97},
    ]
    file_path = "../test_documents/Valid_TD_Bank_Statement.pdf"
    file_bytes = open(file_path, "rb").read()
    workflow = CompleteMetadataWorkflow(mock_template_detector)
    result = workflow.run(io.BytesIO(file_bytes))

    _assert_valid_td_bank_result(result[0])


def test_workflow_with_one_matched_named_template_for_invalid_document():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Bank of America", "actual_confidence": 93},
    ]

    file_path = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf"
    file_bytes = open(file_path, "rb").read()
    fraud_detector = mock.MagicMock(spec=FraudDetector)

    generic_fraud_detector = mock.MagicMock(spec=FraudDetector)
    generic_fraud_detector.get_document_validations.return_value = []

    workflow = CompleteMetadataWorkflow(mock_template_detector, MultiTemplateFraudDetector(), generic_fraud_detector)

    result = workflow.run(io.BytesIO(file_bytes))

    _assert_invalid_bank_of_america_result(result[0])


def test_workflow_with_one_matching_template_against_two_templates_given():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Bank of America", "actual_confidence": 85},
        {"name": "TD Bank", "actual_confidence": 97},
    ]
    file_path = "../test_documents/Valid_TD_Bank_Statement.pdf"
    file_bytes = open(file_path, "rb").read()
    workflow = CompleteMetadataWorkflow(mock_template_detector)
    result = workflow.run(io.BytesIO(file_bytes))

    _assert_valid_td_bank_result(result[0])


def test_workflow_with_two_named_templates_for_valid_document():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "TD Bank", "actual_confidence": 97},
        {"name": "Citizens Bank", "actual_confidence": 83},
    ]

    file_path = "../test_documents/Valid_TD_Bank_Statement.pdf"
    file_bytes = open(file_path, "rb").read()

    generic_fraud_detector = mock.MagicMock(spec=FraudDetector)
    generic_fraud_detector.get_document_validations.return_value = {}

    workflow = CompleteMetadataWorkflow(mock_template_detector, MultiTemplateFraudDetector(), generic_fraud_detector)

    result = workflow.run(io.BytesIO(file_bytes))

    _assert_valid_td_bank_result(result[0])


# def test_generic_template_workflow():
#     mock_template_detector = mock.MagicMock(spec=TemplateDetector)
#     mock_template_detector.get_template_confidences.return_value = [{"name": "Generic Bank", "actual_confidence": 97}]
#
#     file_path = "../test_documents/Generic_Test_Purpose.pdf"
#
#     fraud_detector = mock.MagicMock(spec=FraudDetector)
#
#     generic_fraud_detector = mock.MagicMock(spec=FraudDetector)
#     generic_fraud_detector.get_document_validations.return_value = [{"final_validation_results": {"valid": "Pass"}}]
#
#     mock_untrusted_template_result_detector = mock.MagicMock(spec=UntrustedTemplateResultDetector)
#     mock_untrusted_template_result_detector.is_result_from_untrusted_template.return_value = False
#
#     workflow = CompleteMetadataWorkflow(
#         mock_template_detector, fraud_detector, generic_fraud_detector, mock_untrusted_template_result_detector
#     )
#
#     result = workflow.run(file_path)
#
#     assert result[0]["final_validation_results"]["valid"] == "Pass"


# If it runs through all the generic templates, and they all come back as not matching (invalid)
#  Generic templates never tell us invalid, only tells us that it did not match a generic template


# named_templates_tests:
# 1]With one matching valid named templates - done
# 2]With one matching invalid named template -done
# 3]With two valid named templates -done
# 4]With one with valid and one with invalid named template and both having higher confidence - result matches with valid one bcoz of higher confidence
# 5]With two invalid named templates with different confidence levels(one is above and one is below) - return the one which is above the threshold confidence
# 6]With two invalid named templates with same confidence(above threshold) - return both results
# 7]With two invalid named templates one fails for metadata and another fails for dates - return the template with FDR
# 8]With two named templates one with higher confidence but fails for matadata and another one with -done
# lower confidence but passes for metadata - return result of template that passed for metadata
# 9]If it doesn't matches any named templates get_template_confidences will return empty list check for generic rules in this case.


# 4
def test_complete_fraud_detection_workflow_with_one_valid_and_one_invalid_template():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "TD Bank", "actual_confidence": 93},
        {"name": "Bank of America", "actual_confidence": 91},
    ]

    file_path = "../test_documents/Valid_TD_Bank_Statement.pdf"
    file_bytes = open(file_path, "rb").read()
    workflow = CompleteMetadataWorkflow(mock_template_detector)

    result = workflow.run(io.BytesIO(file_bytes))

    assert result[0].get("final_validation_results")["valid"] == "Pass"


# 8
def test_complete_fraud_detection_workflow_with_two_named_templates_one_fails_and_another_passes_for_metadata():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "TD Bank", "actual_confidence": 92},
        {"name": "Bank of America", "actual_confidence": 88},
    ]

    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    file_bytes = open(file_path, "rb").read()
    workflow = CompleteMetadataWorkflow(mock_template_detector)

    result = workflow.run(io.BytesIO(file_bytes))

    assert result[0].get("template_rule_set_validation_results")[0]["template"]["name"] == "Bank of America"
    assert result[0].get("final_validation_results")["valid"] == "Pass"


def test_workflow_when_document_does_not_match_any_named_template():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = []

    file_path = "../test_documents/Valid_Ally_Bank_Statement.pdf"
    file_bytes = open(file_path, "rb").read()
    generic_fraud_detector = mock.MagicMock(spec=FraudDetector)
    # Figure out why this mocking is not working properly
    generic_fraud_detector.get_document_validations.return_value = [
        {"final_validation_results": {"valid": "generic fraud detector result"}}
    ]
    workflow = CompleteMetadataWorkflow(mock_template_detector, MultiTemplateFraudDetector(), generic_fraud_detector)

    result = workflow.run(io.BytesIO(file_bytes))

    assert result[0].get("final_validation_results")["valid"] == "generic fraud detector result"


def test_workflow_for_invalid_template_with_higher_confidence_prediction():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Bank of America", "actual_confidence": 93},
    ]
    file_path = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf"
    file_bytes = open(file_path, "rb").read()
    workflow = CompleteMetadataWorkflow(mock_template_detector)
    result = workflow.run(io.BytesIO(file_bytes))

    _assert_invalid_bank_of_america_result(result[0])


def test_workflow_with_templates_with_same_confidence_level():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Bank of America", "actual_confidence": 97},
        {"name": "TD Bank", "actual_confidence": 97},
    ]
    file_path = "../test_documents/Valid_TD_Bank_Statement.pdf"
    file_bytes = open(file_path, "rb").read()
    workflow = CompleteMetadataWorkflow(mock_template_detector)
    result = workflow.run(io.BytesIO(file_bytes))

    _assert_valid_td_bank_result(result[0])


def test_workflow_for_valid_template_with_lower_threshold_than_the_invalid_template_with_higher_threshold():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Bank of America", "actual_confidence": 97},
        {"name": "TD Bank", "actual_confidence": 91},
    ]
    file_path = "../test_documents/Valid_TD_Bank_Statement.pdf"
    file_bytes = open(file_path, "rb").read()
    workflow = CompleteMetadataWorkflow(mock_template_detector)
    result = workflow.run(io.BytesIO(file_bytes))

    _assert_valid_td_bank_result(result[0])


def test_fraud_detection_workflow_with_one_fraud_detector_result_returns_that_result():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Bank of America", "actual_confidence": 97},
    ]
    expected_result = [{"final_validation_results": {"valid": "Pass"}}]
    mock_multi_template_fraud_detector = mock.MagicMock(spec=MultiTemplateFraudDetector)
    mock_multi_template_fraud_detector.run.return_value = expected_result
    workflow = CompleteMetadataWorkflow(mock_template_detector, mock_multi_template_fraud_detector)

    result = workflow.run(io.BytesIO(b"test_file.pdf"))

    assert result[0] == expected_result[0]


def test_workflow_prefers_fdr_result_over_fail_result():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Template A", "actual_confidence": 95},
        {"name": "Template B", "actual_confidence": 93},
    ]
    expected_result = [
        {"final_validation_results": {"valid": "FDR", "validation_message_code": "MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO"}},
        {"final_validation_results": {"valid": "Fail", "validation_message_code": "MSG_INVALID_FILE"}},
    ]
    mock_multi_template_fraud_detector = mock.MagicMock(spec=MultiTemplateFraudDetector)
    mock_multi_template_fraud_detector.run.return_value = expected_result
    workflow = CompleteMetadataWorkflow(mock_template_detector, mock_multi_template_fraud_detector)

    result = workflow.run(io.BytesIO(b"test_file.pdf"))

    assert result[0] == expected_result[0]


def test_workflow_prefers_uncapped_pass_over_capped_fdr_result():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Template A", "actual_confidence": 95},
        {"name": "Template B", "actual_confidence": 93},
    ]
    expected_result = [
        {
            "final_validation_results": {
                "valid": "FDR",
                "validation_message_code": "MSG_FURTHER_VALIDATION_REQUIRED_UNTRUSTED_TEMPLATE",
            }
        },
        {
            "final_validation_results": {
                "valid": "Pass",
                "validation_message_code": "MSG_VALID_FILE",
            }
        },
    ]
    mock_multi_template_fraud_detector = mock.MagicMock(spec=MultiTemplateFraudDetector)
    mock_multi_template_fraud_detector.run.return_value = expected_result
    workflow = CompleteMetadataWorkflow(mock_template_detector, mock_multi_template_fraud_detector)

    result = workflow.run(io.BytesIO(b"test_file.pdf"))

    assert result[0] == expected_result[1]


def test_workflow_prefers_browser_printed_fdr_result_over_later_fdr_result():
    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_template_detector.get_template_confidences.return_value = [
        {"name": "Template A", "actual_confidence": 95},
        {"name": "Template B", "actual_confidence": 93},
    ]
    expected_result = [
        {
            "final_validation_results": {
                "valid": "FDR",
                "validation_message_code": "MSG_BROWSER_PRINTED_DOCUMENT",
            }
        },
        {
            "final_validation_results": {
                "valid": "FDR",
                "validation_message_code": "MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO",
            }
        },
    ]
    mock_multi_template_fraud_detector = mock.MagicMock(spec=MultiTemplateFraudDetector)
    mock_multi_template_fraud_detector.run.return_value = expected_result
    workflow = CompleteMetadataWorkflow(mock_template_detector, mock_multi_template_fraud_detector)

    result = workflow.run(io.BytesIO(b"test_file.pdf"))

    assert result[0] == expected_result[0]


def test_generic_fraud_detection_workflow_does_not_run_if_named_fraud_detection_workflow_returns_fdr():
    with open("docuverus/Workflow/test_data/invalid_named_template_workflow_response.json", "r") as data_file:
        passing_expected_result = json.load(data_file)

    mock_template_detector = mock.MagicMock(spec=TemplateDetector)
    mock_named_fraud_detector = mock.MagicMock(spec=MultiTemplateFraudDetector)
    mock_named_fraud_detector.run.return_value = [passing_expected_result]
    mock_generic_fraud_detector = mock.MagicMock(spec=FraudDetector)
    mock_generic_fraud_detector.get_document_validations.return_value = {}
    file_byte_reader = io.BytesIO(b"file.pdf")

    test_object = CompleteMetadataWorkflow(mock_template_detector, mock_named_fraud_detector, mock_generic_fraud_detector)

    result = test_object.run(file_byte_reader)

    assert result == [passing_expected_result]
    mock_generic_fraud_detector.get_document_validations.assert_not_called()
