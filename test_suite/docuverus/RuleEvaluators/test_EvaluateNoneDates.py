import fitz

from docuverus.RuleEvaluators.DateRuleEvaluator import DateRuleEvaluator
from test_suite.support.testing_utilities import generate_json_for_date_comparator


def test_valid_when_both_creation_and_modification_dates_are_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "None",
        "None",
        "None",
        "Pass",
        "MSG_CREATION_DATE_NOT_FOUND",
        "None",
        "Pass",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    filepath = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


# This is testing the EvaluateNoneModDate.py
def test_valid_when_create_date_is_present_and_mod_date_is_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "None",
        "D:20200521145033Z",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "None",
        "Pass",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    filepath = "../test_documents/Valid_Chime_Bank_Statement_with_mod_date_none.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_create_date_and_modDate_is_present_and_mod_date_should_be_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "None",
        "D:20200521145033Z",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20210521145033Z",
        "Fail",
        "MSG_MODIFICATION_DATE_SHOULD_BE_NONE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    filepath = "../test_documents/Valid_Chime_Bank_Statement_with_mod_date_none.pdf"
    fitz.open(filepath)
    metadata = {"creationDate": "D:20200521145033Z", "modDate": "D:20210521145033Z"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_create_date_and_modDate_are_none_but_create_date_should_be_present():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "None",
        "None",
        "Fail",
        "MSG_CREATION_DATE_NOT_FOUND",
        "None",
        "Pass",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    filepath = "../test_documents/Valid_Chime_Bank_Statement_with_mod_date_none.pdf"
    fitz.open(filepath)
    metadata = {"creationDate": "", "modDate": ""}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_create_date_is_none_but_create_date_should_be_present_and_modDate_is_present_but_should_be_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "None",
        "None",
        "Fail",
        "MSG_CREATION_DATE_NOT_FOUND",
        "D:20200521145033Z",
        "Fail",
        "MSG_MODIFICATION_DATE_SHOULD_BE_NONE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    filepath = "../test_documents/Valid_Chime_Bank_Statement_with_mod_date_none.pdf"
    fitz.open(filepath)
    metadata = {"creationDate": "", "modDate": "D:20200521145033Z"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_modDate_is_present_but_it_should_be_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "None",
        "None",
        "None",
        "Pass",
        "MSG_CREATION_DATE_NOT_FOUND",
        "D:20221018110520-04'00'",
        "Fail",
        "MSG_MODIFICATION_DATE_SHOULD_BE_NONE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "", "modDate": "D:20221018110520-04'00'"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_createDate_is_present_but_it_should_be_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "None",
        "None",
        "D:20221018110520-04'00'",
        "Fail",
        "MSG_CREATION_DATE_SHOULD_BE_NONE",
        "None",
        "Pass",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "D:20221018110520-04'00'", "modDate": ""}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_createDate_and_modDate_are_present_but_both_should_be_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "None",
        "None",
        "D:20221018110520-04'00'",
        "Fail",
        "MSG_CREATION_DATE_SHOULD_BE_NONE",
        "D:20231018110320-04'00'",
        "Fail",
        "MSG_MODIFICATION_DATE_SHOULD_BE_NONE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20221018110520-04'00'",
        "modDate": "D:20231018110320-04'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result
