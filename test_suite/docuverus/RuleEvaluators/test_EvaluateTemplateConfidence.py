from docuverus.RuleEvaluators.EvaluateTemplateConfidence import (
    EvaluateTemplateConfidence,
)


def test_template_prediction_confidence():
    templates = [
        {"name": "Template A", "actual_confidence": 96},
        {"name": "Template B", "actual_confidence": 85},
    ]

    rule_evaluator = EvaluateTemplateConfidence(templates=templates)
    result = rule_evaluator.evaluate()

    assert result[0]["status"] == "valid"

    assert result[1]["status"] == "invalid"


def test_template_prediction_confidence_for_default_confidence_value():
    templates = [{"name": "Template C", "actual_confidence": 92}]

    rule_evaluator = EvaluateTemplateConfidence(templates=templates)
    result = rule_evaluator.evaluate()

    assert result[0]["status"] == "invalid"
