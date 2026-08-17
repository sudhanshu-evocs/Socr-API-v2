from docuverus.RuleEvaluators.DateRuleEvaluator import DateRuleEvaluator
from test_suite.support.testing_utilities import generate_json_for_date_comparator


def test_valid_when_creation_date_and_mod_date_matches_with_specific_value_and_unequal():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20220209135314-05'00'",
        "D:20230210135314-05'00'",
        "D:20220209135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE",
        "D:20230210135314-05'00'",
        "Pass",
        "MSG_MODIFICATION_DATE_MATCHES_SPECIFIC_VALUE",
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


def test_valid_when_creation_date_and_mod_date_matches_with_specific_value_and_equal():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20220209135314-05'00'",
        "D:20220209135314-05'00'",
        "D:20220209135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE",
        "D:20220209135314-05'00'",
        "Pass",
        "MSG_MODIFICATION_DATE_MATCHES_SPECIFIC_VALUE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20220209135314-05'00'",
        "modDate": "D:20220209135314-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_date_and_mod_date_does_not_matches_specific_value():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20230209135314-05'00'",
        "D:20240210135314-05'00'",
        "D:20220209135314-05'00'",
        "Fail",
        "MSG_CREATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE",
        "D:20230210135314-05'00'",
        "Fail",
        "MSG_MODIFICATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20220209135314-05'00'",
        "modDate": "D:20230210135314-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_date_matches_but_moddate_does_not_matches_specific_value():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20220209135314-05'00'",
        "D:20240210135314-05'00'",
        "D:20220209135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE",
        "D:20230210135314-05'00'",
        "Fail",
        "MSG_MODIFICATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20220209135314-05'00'",
        "modDate": "D:20230210135314-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_date_does_not_matches_but_moddate_matches_specific_value():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20230209135314-05'00'",
        "D:20230210135314-05'00'",
        "D:20220209135314-05'00'",
        "Fail",
        "MSG_CREATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE",
        "D:20230210135314-05'00'",
        "Pass",
        "MSG_MODIFICATION_DATE_MATCHES_SPECIFIC_VALUE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {
        "creationDate": "D:20220209135314-05'00'",
        "modDate": "D:20230210135314-05'00'",
    }
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_date_is_none_but_moddate_matches_specific_value():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20230209135314-05'00'",
        "D:20230210135314-05'00'",
        "None",
        "Fail",
        "MSG_CREATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE",
        "D:20230210135314-05'00'",
        "Pass",
        "MSG_MODIFICATION_DATE_MATCHES_SPECIFIC_VALUE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "None", "modDate": "D:20230210135314-05'00'"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalid_when_creation_date_matches_specific_value_but_moddate_is_none():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20230210135314-05'00'",
        "D:20230210135314-05'00'",
        "D:20230210135314-05'00'",
        "Pass",
        "MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE",
        "None",
        "Fail",
        "MSG_MODIFICATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "D:20230210135314-05'00'", "modDate": "None"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_validate_creation_and_modification_date_format_():
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


def test_validate_fixed_create_date_and_variable_mod_date():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20220317122558-05'00'",
        "Greater",
        "D:20220317122558-05'00'",
        "Pass",
        "MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE",
        "D:20240816104352-05'00'",
        "Pass",
        "MSG_VALID_MODIFICATION_DATE",
        "Pass",
        "MSG_VALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "D:20220317122558-05'00'", "modDate": "D:20240816104352-05'00'"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result


def test_invalidate_fixed_create_date_with_equal_mod_date():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "D:20220317122558-05'00'",
        "Greater",
        "D:20220317122558-05'00'",
        "Pass",
        "MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE",
        "D:20220317122558-05'00'",
        "Fail",
        "MSG_INVALID_MODIFICATION_DATE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"creationDate": "D:20220317122558-05'00'", "modDate": "D:20220317122558-05'00'"}
    date_evaluator = DateRuleEvaluator()
    date_evaluator.evaluate(input_rule, metadata)

    assert input_rule == expected_rule_result
