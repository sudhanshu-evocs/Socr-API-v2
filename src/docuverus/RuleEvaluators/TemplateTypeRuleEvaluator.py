import logging

from docuverus.RuleEvaluators.RuleEvaluator import RuleEvaluator
from docuverus.Utils.Messages import MessageCode
from docuverus.Utils.TemplateNameUtilities import normalize_template_name


class TemplateTypeRuleEvaluator(RuleEvaluator):
    def __init__(self, template_type):
        self.template_type = template_type

    def evaluate(self, rule: dict, metadata: dict) -> None:
        logging.info(f"Evaluating template type rule")
        if "valid" in rule["template"] and rule["template"]["valid"] == "Fail":
            return
        if normalize_template_name(rule["template"]["name"]) == normalize_template_name(self.template_type):
            rule["template"]["actual"] = self.template_type
            rule["template"]["valid"] = "Pass"
            rule["template"]["validation_message_code"] = MessageCode.MSG_TEMPLATE_TYPE_MATCH
        else:
            rule["template"]["actual"] = self.template_type
            rule["template"]["valid"] = "Fail"
            rule["template"]["validation_message_code"] = MessageCode.MSG_TEMPLATE_TYPE_DOES_NOT_MATCH
