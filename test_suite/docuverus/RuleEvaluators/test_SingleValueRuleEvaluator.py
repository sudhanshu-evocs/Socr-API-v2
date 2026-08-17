import fitz

from docuverus.RuleEvaluators.SingleValueRuleEvaluator import SingleValueRuleEvaluator


def test_to_get_producer_targetstream_of_valid_bank_of_america_statement():
    input_rule = {"producer": {"name": "^TargetStream.*"}}
    expected_rule_result = {
        "producer": {
            "name": "^TargetStream.*",
            "actual": "TargetStream StreamEDS rv1.7.41 for Bank of America",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        }
    }
    filepath = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    template_type = "Bank of America"
    producer_evaluator = SingleValueRuleEvaluator(
        template_type, "producer", "MSG_PRODUCER_MATCH", "MSG_PRODUCER_DOES_NOT_MATCH"
    )
    producer_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert expected_rule_result == input_rule


def test_to_get_producer_ios_version_of_valid_td_bank_statement():
    input_rule = {"producer": {"name": "^iOS Version"}}
    expected_rule_result = {
        "producer": {
            "name": "^iOS Version",
            "actual": "iOS Version 16.3.1 (Build 20D67) Quartz PDFContext",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        }
    }
    filepath = "../test_documents/Valid_TD_Bank_Statement_ios.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    template_type = "TD Bank"
    producer_evaluator = SingleValueRuleEvaluator(
        template_type, "producer", "MSG_PRODUCER_MATCH", "MSG_PRODUCER_DOES_NOT_MATCH"
    )
    producer_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert expected_rule_result == input_rule


def test_producer_validation_on_invalid_bank_of_america_statement():
    input_rule = {"producer": {"name": "^TargetStream.*"}}
    expected_rule_result = {
        "producer": {
            "name": "^TargetStream.*",
            "actual": "Adobe PDF library 11.00",
            "valid": "Fail",
            "validation_message_code": "MSG_PRODUCER_DOES_NOT_MATCH",
        }
    }
    filepath = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    template_type = "Bank of America"
    producer_evaluator = SingleValueRuleEvaluator(
        template_type, "producer", "MSG_PRODUCER_MATCH", "MSG_PRODUCER_DOES_NOT_MATCH"
    )
    producer_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert expected_rule_result == input_rule


# write tests for creator and author to test single value evaluator functionality
def test_to_validate_creator_of_valid_bank_of_america_statement():
    input_rule = {"creator": {"name": "^Bank of America.*"}}
    expected_rule_result = {
        "creator": {
            "name": "^Bank of America.*",
            "actual": "Bank of America",
            "valid": "Pass",
            "validation_message_code": "MSG_CREATOR_MATCH",
        }
    }
    filepath = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    template_type = "Bank of America"
    producer_evaluator = SingleValueRuleEvaluator(
        template_type, "creator", "MSG_CREATOR_MATCH", "MSG_CREATOR_DOES_NOT_MATCH"
    )
    producer_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert expected_rule_result == input_rule


def test_to_validate_creator_of_valid_td_bank_statement():
    input_rule = {"creator": {"name": ""}}
    expected_rule_result = {
        "creator": {
            "name": "",
            "actual": "",
            "valid": "Pass",
            "validation_message_code": "MSG_CREATOR_MATCH",
        }
    }
    filepath = "../test_documents/Valid_TD_Bank_Statement_ios.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    template_type = "TD Bank"
    producer_evaluator = SingleValueRuleEvaluator(
        template_type, "creator", "MSG_CREATOR_MATCH", "MSG_CREATOR_DOES_NOT_MATCH"
    )
    producer_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert expected_rule_result == input_rule


def test_to_validate_creator_of_invalid_bank_of_america_statement():
    input_rule = {"creator": {"name": "^Bank of America.*"}}
    expected_rule_result = {
        "creator": {
            "name": "^Bank of America.*",
            "actual": "Adobe Illustrator CC 2014 (Windows)",
            "valid": "Fail",
            "validation_message_code": "MSG_CREATOR_DOES_NOT_MATCH",
        }
    }
    filepath = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    template_type = "Bank of America"
    producer_evaluator = SingleValueRuleEvaluator(
        template_type, "creator", "MSG_CREATOR_MATCH", "MSG_CREATOR_DOES_NOT_MATCH"
    )
    producer_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert expected_rule_result == input_rule


def test_single_value_rule_evaluator_validates_unknown_when_no_rule_for_key():
    input_rule = {}
    expected_rule_result = {
        "creator": {"name": "", "actual": "Adobe?", "valid": "Pass", "validation_message_code": "MSG_NO_RULE_FOR_KEY"}
    }

    metadata = {"creator": "Adobe?"}
    creator_evaluator = SingleValueRuleEvaluator("", "creator", "MSG_NO_RULE_FOR_KEY", "")
    creator_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_to_validate_producer_of_ADPNA_POI():
    input_rule = {"producer": {"name": "^PCL2PDF \(TM\) from Visual Software.*"}}
    expected_rule_result = {
        "producer": {
            "name": "^PCL2PDF \(TM\) from Visual Software.*",
            "actual": "PCL2PDF (TM) from Visual Software",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        }
    }
    filepath = "../test_documents/Valid_ADPNA_POI.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    template_type = "ADPNA"
    producer_evaluator = SingleValueRuleEvaluator(
        template_type, "producer", "MSG_PRODUCER_MATCH", "MSG_PRODUCER_DOES_NOT_MATCH"
    )
    producer_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert expected_rule_result == input_rule


def test_to_validate_copyright_symbol():
    input_rule = {"producer": {"name": "^iText® 5.5.12 ©2000-2017 iText Group NV \(AGPL-version\).*"}}
    expected_rule_result = {
        "producer": {
            "name": "^iText® 5.5.12 ©2000-2017 iText Group NV \(AGPL-version\).*",
            "actual": "iText® 5.5.12 ©2000-2017 iText Group NV (AGPL-version)",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        }
    }

    metadata = {"producer": "iText® 5.5.12 ©2000-2017 iText Group NV (AGPL-version)"}
    template_type = ""

    producer_evaluator = SingleValueRuleEvaluator(
        template_type, "producer", "MSG_PRODUCER_MATCH", "MSG_PRODUCER_DOES_NOT_MATCH"
    )
    producer_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_rule_result


def test_to_empty_creator_with_string_value():
    input_rule = {"creator": {"name": ""}}
    expected_rule_result = {
        "creator": {
            "name": "",
            "actual": "Workday BIRT Report Engine, version: 4.7.0",
            "valid": "Fail",
            "validation_message_code": "MSG_CREATOR_DOES_NOT_MATCH",
        }
    }

    metadata = {"creator": "Workday BIRT Report Engine, version: 4.7.0"}
    template_type = ""

    producer_evaluator = SingleValueRuleEvaluator(
        template_type, "creator", "MSG_CREATOR_MATCH", "MSG_CREATOR_DOES_NOT_MATCH"
    )
    producer_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_rule_result
