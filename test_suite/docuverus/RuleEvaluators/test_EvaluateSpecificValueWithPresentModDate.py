from docuverus.RuleEvaluators.DateRuleEvaluator import DateRuleEvaluator
from test_suite.support.testing_utilities import generate_json_for_date_comparator


def test_valid_when_creation_date_matches_specific_value_and_modDate_is_present():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20220209135314-05'00'",
        "Present",
        "D:20220209135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE",
        "D:20230210135314-05'00'",
        "Pass",
        "MSG_MODIFICATION_DATE_FOUND",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20220209135314-05'00'",
        "modDate": "D:20230210135314-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_date_does_not_matches_specific_value_and_modDate_is_present():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20220209135314-05'00'",
        "Present",
        "D:20240310135314-05'00'",
        "Fail",
        "MSG_CREATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE",
        "D:20230210135314-05'00'",
        "Pass",
        "MSG_MODIFICATION_DATE_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20240310135314-05'00'",
        "modDate": "D:20230210135314-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_date_matches_specific_value_and_modDate_is_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20240310135314-05'00'",
        "Present",
        "D:20240310135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE",
        "None",
        "Fail",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "D:20240310135314-05'00'", "modDate": ""}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_date_and_modDate_are_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20240310135314-05'00'",
        "Present",
        "None",
        "Fail",
        "MSG_CREATION_DATE_NOT_FOUND",
        "None",
        "Fail",
        "MSG_MODIFICATION_DATE_NOT_FOUND",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "", "modDate": ""}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_validate_creation_and_modification_date_format_when_creation_date_is_in_invalid_format():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20230210135314-05'00'",
        "D:20231023110520-04'00'",
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
