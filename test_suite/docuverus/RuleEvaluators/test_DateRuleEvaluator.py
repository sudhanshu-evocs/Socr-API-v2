import fitz

from docuverus.RuleEvaluators.DateComparator import DateComparator
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


def test_valid_when_create_date_is_present_and_mod_date_is_within_default_tolerance_of_1_sec():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20240103223248-08'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20240103223249-08'00'",
        "Pass",
        "MSG_DATES_VALID_TOLERANCE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20240103223248-08'00'",
        "modDate": "D:20240103223249-08'00'",
    }

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_create_date_is_present_and_mod_date_is_within_1_sec_but_tolerance_is_explicitly_zero():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20240103223248-08'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20240103223249-08'00'",
        "Fail",
        "MSG_DATES_INVALID_TOLERANCE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    input_rule["dates"]["modified"]["tolerance"] = 0
    expected_rule_result["dates"]["modified"]["tolerance"] = 0
    metadata = {
        "creationDate": "D:20240103223248-08'00'",
        "modDate": "D:20240103223249-08'00'",
    }

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


def test_validate_creation_and_modification_date_format_with_unparsable_created_and_parsable_modified():
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


def test_valid_when_modification_date_less_than_creation_date_and_rule_is_written_as_Lesser():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Lesser",
        "D:20230412160033Z00'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20230412150033Z00'00'",
        "Pass",
        "MSG_VALID_MODIFICATION_DATE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "D:20230412160033Z00'00'", "modDate": "D:20230412150033Z00'00'"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_date_evaluator_for_given_rule_not_found():
    date_comparator = DateComparator()
    mapping = {("anything", "anything", False, False): date_comparator}
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "not anything",
        "not anything",
        "D:20230412160033Z00'00'",
        "FDR",
        "ERROR_INVALID_DATE_RULE",
        "D:20230412150033Z00'00'",
        "FDR",
        "ERROR_INVALID_DATE_RULE",
        "FDR",
        "ERROR_UNKNOWN_DATE_VALIDATION_RULE",
    )

    date_evaluator = DateRuleEvaluator(mapping)
    date_evaluator.evaluate(input_rule, {"creationDate": "D:20230412160033Z00'00'", "modDate": "D:20230412150033Z00'00'"})

    assert input_rule == expected_rule_result


def test_valid_when_created_and_modified_null_and_present():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "None",
        "Present",
        "None",
        "Pass",
        "MSG_CREATION_DATE_NOT_FOUND",
        "D:20230412150033Z00'00'",
        "Pass",
        "MSG_MODIFICATION_DATE_FOUND",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, {"creationDate": "", "modDate": "D:20230412150033Z00'00'"})

    assert input_rule == expected_rule_result


def test_invalid_when_created_and_modified_null_and_present():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "None",
        "Present",
        "D:20230412150033Z00'00'",
        "Fail",
        "MSG_CREATION_DATE_SHOULD_BE_NONE",
        "None",
        "Fail",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, {"creationDate": "D:20230412150033Z00'00'", "modDate": ""})

    assert input_rule == expected_rule_result


def test_invalid_when_created_and_modified_null_and_present():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "None",
        "Present",
        "D:20230412150033Z00'00'",
        "Fail",
        "MSG_CREATION_DATE_SHOULD_BE_NONE",
        "None",
        "Fail",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, {"creationDate": "D:20230412150033Z00'00'", "modDate": ""})

    assert input_rule == expected_rule_result


def test_valid_date_formats_using_paycor_date_samples():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20210303200357+00'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20210303200357+00'00'",
        "Pass",
        "MSG_DATES_VALID_TOLERANCE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, {"creationDate": "D:20210303200357+00'00'", "modDate": "D:20210303200357+00'00'"})

    assert input_rule == expected_rule_result


def test_valid_date_formats_when_UTC_format():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20230221173311UTC00'00'",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20230221173311UTC00'00'",
        "Pass",
        "MSG_DATES_VALID_TOLERANCE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, {"creationDate": "D:20230221173311UTC00'00'", "modDate": "D:20230221173311UTC00'00'"})

    assert input_rule == expected_rule_result


def test_valid_date_format_for_adpna_poi():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Equal",
        "D:20220517191732\r\n",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20220517191732\r\n",
        "Pass",
        "MSG_DATES_VALID_TOLERANCE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, {"creationDate": "D:20220517191732\r\n", "modDate": "D:20220517191732\r\n"})

    assert input_rule == expected_rule_result


def test_validate_date_with_greater_no_tolerance():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Greater",
        "8/7/2023 11:56:35",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "D:20230811124916-04'00'",
        "Pass",
        "MSG_VALID_MODIFICATION_DATE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, {"creationDate": "8/7/2023 11:56:35", "modDate": "D:20230811124916-04'00'"})

    assert input_rule == expected_rule_result


def test_validate_date_with_only_yyyy_mm_dd():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "None",
        "D:20230404",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "None",
        "Pass",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )

    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, {"creationDate": "D:20230404", "modDate": ""})

    assert input_rule == expected_rule_result
