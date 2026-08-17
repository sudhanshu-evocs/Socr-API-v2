import fitz

from docuverus.RuleEvaluators.DateRuleEvaluator import DateRuleEvaluator
from test_suite.support.testing_utilities import generate_json_for_date_comparator


def test_valid_when_creation_and_modification_dates_are_present_and_equal():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20230412160033Z00'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20230412160033Z00'00'",
        "Pass",
        "MSG_DATES_VALID_TOLERANCE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    filepath = "../test_documents/Valid_TD_Bank_Statement_ios.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_and_modification_dates_are_present_and_unequal():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20221019192112-04'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20221020110520-04'00'",
        "Fail",
        "MSG_DATES_INVALID_TOLERANCE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    filepath = "../test_documents/Invalid_PNC_Bank_Statement_with_unequal_dates.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_valid_when_create_date_is_present_and_mod_date_is_within_tolerance_of_1_sec():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20220209135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20220209135315-05'00'",
        "Pass",
        "MSG_DATES_VALID_TOLERANCE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    input_rule["dates"]["modified"]["tolerance"] = 1
    expected_rule_result["dates"]["modified"]["tolerance"] = 1
    filepath = "../test_documents/Valid_Navy_FCU_Bank_Statement_with_1sec_diff_in_dates.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_valid_when_create_date_is_present_and_mod_date_is_within_tolerance_of_5_sec():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20220209135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20220209135319-05'00'",
        "Pass",
        "MSG_DATES_VALID_TOLERANCE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    input_rule["dates"]["modified"]["tolerance"] = 5
    expected_rule_result["dates"]["modified"]["tolerance"] = 5
    metadata = {
        "creationDate": "D:20220209135314-05'00'",
        "modDate": "D:20220209135319-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_valid_when_create_date_is_present_and_mod_date_is_within_tolerance_of_3_sec():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20220209135316-05'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20220209135320-05'00'",
        "Fail",
        "MSG_DATES_INVALID_TOLERANCE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    input_rule["dates"]["modified"]["tolerance"] = 3
    expected_rule_result["dates"]["modified"]["tolerance"] = 3
    metadata = {
        "creationDate": "D:20220209135316-05'00'",
        "modDate": "D:20220209135320-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_create_date_is_present_and_mod_date_is_less_than_create_date_with_tolerance_of_10_sec():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20220209135319-05'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20220209135316-05'00'",
        "Fail",
        "MSG_DATES_INVALID_TOLERANCE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    input_rule["dates"]["modified"]["tolerance"] = 10
    expected_rule_result["dates"]["modified"]["tolerance"] = 10
    metadata = {
        "creationDate": "D:20220209135319-05'00'",
        "modDate": "D:20220209135316-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_modDate_is_greater_than_createDate():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20221019192112-04'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20231020110520-04'00'",
        "Fail",
        "MSG_DATES_INVALID_TOLERANCE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20221019192112-04'00'",
        "modDate": "D:20231020110520-04'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_modDate_is_less_than_createDate():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20221019192112-04'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20221018110520-04'00'",
        "Fail",
        "MSG_DATES_INVALID_TOLERANCE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20221019192112-04'00'",
        "modDate": "D:20221018110520-04'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_valid_when_modification_date_is_1_hr_greater_than_creation_date():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Greater",
        "D:20220209135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20220209145314-05'00'",
        "Pass",
        "MSG_DATES_VALID_TOLERANCE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    input_rule["dates"]["modified"]["duration"] = 3600
    expected_rule_result["dates"]["modified"]["duration"] = 3600
    metadata = {
        "creationDate": "D:20220209135314-05'00'",
        "modDate": "D:20220209145314-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


#
def test_invalid_when_modification_date_is_not_greater_than_1_hr_by_creation_date():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Greater",
        "D:20220209135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20220209142314-05'00'",
        "Fail",
        "MSG_DATES_INVALID_TOLERANCE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    input_rule["dates"]["modified"]["duration"] = 3600
    expected_rule_result["dates"]["modified"]["duration"] = 3600
    metadata = {
        "creationDate": "D:20220209135314-05'00'",
        "modDate": "D:20220209142314-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_validate_creation_and_modification_date_format_():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Present",
        "D:18/07/2023",
        "Fail",
        "MSG_INVALID_DATE_FORMAT",
        "D:20231023110520-04'00'",
        "Pass",
        "MSG_MODIFICATION_DATE_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "D:18/07/2023", "modDate": "D:20231023110520-04'00'"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_valid_when_creation_and_modification_dates_are_present_and_equal_and_tolerance_and_duration_are_zero():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20230412160033Z00'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20230412160033Z00'00'",
        "Pass",
        "MSG_DATES_VALID_TOLERANCE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    input_rule["dates"]["modified"]["duration"] = 0
    expected_rule_result["dates"]["modified"]["duration"] = 0
    input_rule["dates"]["modified"]["tolerance"] = 0
    expected_rule_result["dates"]["modified"]["tolerance"] = 0
    filepath = "../test_documents/Valid_TD_Bank_Statement_ios.pdf"
    pdf_document = fitz.open(filepath)
    metadata = pdf_document.metadata
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_and_modification_none_when_rule_is_present_equal():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "None",
        "Fail",
        "MSG_CREATION_DATE_NOT_FOUND",
        "None",
        "Fail",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )

    metadata = {"creationDate": "None", "modDate": "None"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_and_modification_dates_are_present_and_equal_but_no_modified_exists():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20230412160033Z00'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "None",
        "Fail",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20230412160033Z00'00'",
        "modDate": "None",
    }

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result
