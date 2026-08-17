from docuverus.RuleEvaluators.TemplateTypeRuleEvaluator import TemplateTypeRuleEvaluator


def test_validation_success_for_matched_template():
    input_rule = {"template": {"name": "First Bank"}}
    expected_rule_result = {
        "template": {
            "name": "First Bank",
            "actual": "First Bank",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        }
    }

    template_type = "First Bank"
    rule_evaluator = TemplateTypeRuleEvaluator(template_type)
    # # Act
    rule_evaluator.evaluate(input_rule, None)

    # Assert
    assert input_rule == expected_rule_result


def test_validation_failure_for_unmatched_template():
    input_rule = {"template": {"name": "First Bank"}}
    expected_rule_result = {
        "template": {
            "name": "First Bank",
            "actual": "Second Bank",
            "valid": "Fail",
            "validation_message_code": "MSG_TEMPLATE_TYPE_DOES_NOT_MATCH",
        }
    }

    template_type = "Second Bank"
    rule_evaluator = TemplateTypeRuleEvaluator(template_type)
    # # Act
    rule_evaluator.evaluate(input_rule, None)

    # Assert
    assert input_rule == expected_rule_result


def test_template_type_rule_evaluator_is_not_case_sensitive():
    input_rule = {"template": {"name": "First Bank"}}
    expected_rule_result = {
        "template": {
            "name": "First Bank",
            "actual": "first bank",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        }
    }

    template_type = "first bank"
    rule_evaluator = TemplateTypeRuleEvaluator(template_type)

    rule_evaluator.evaluate(input_rule, None)

    assert input_rule == expected_rule_result


def test_template_handles_when_valid_does_not_exist():
    input_rule = {"template": {"name": "First Bank"}}
    expected_rule_result = {
        "template": {
            "name": "First Bank",
            "actual": "First Bank",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        }
    }

    template_type = "First Bank"
    rule_evaluator = TemplateTypeRuleEvaluator(template_type)

    rule_evaluator.evaluate(input_rule, None)

    assert input_rule == expected_rule_result


def test_template_type_rule_evaluator_ignores_inner_whitespace():
    input_rule = {"template": {"name": "JP Morgan Chase"}}
    expected_rule_result = {
        "template": {
            "name": "JP Morgan Chase",
            "actual": "JPMorgan Chase",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        }
    }

    template_type = "JPMorgan Chase"
    rule_evaluator = TemplateTypeRuleEvaluator(template_type)

    rule_evaluator.evaluate(input_rule, None)

    assert input_rule == expected_rule_result


def test_template_type_rule_evaluator_preserves_separator_differences():
    input_rule = {"template": {"name": "Police_Fire"}}
    expected_rule_result = {
        "template": {
            "name": "Police_Fire",
            "actual": "Police-Fire",
            "valid": "Fail",
            "validation_message_code": "MSG_TEMPLATE_TYPE_DOES_NOT_MATCH",
        }
    }

    template_type = "Police-Fire"
    rule_evaluator = TemplateTypeRuleEvaluator(template_type)

    rule_evaluator.evaluate(input_rule, None)

    assert input_rule == expected_rule_result
