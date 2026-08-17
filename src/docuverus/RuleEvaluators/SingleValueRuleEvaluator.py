import logging
import re

from docuverus.RuleEvaluators.RuleEvaluator import RuleEvaluator


class SingleValueRuleEvaluator(RuleEvaluator):
    def __init__(self, template_type, single_value_name, pass_message_code, fail_message_code):
        self.template_type = template_type
        self.single_value_name = single_value_name
        self.pass_message_code = pass_message_code
        self.fail_message_code = fail_message_code

    def evaluate(self, rule: dict, metadata: dict) -> None:
        logging.info(f"Evaluating single value rule evaluator for {self.single_value_name}")
        single_value = metadata.get(self.single_value_name)
        matches = []
        if self.single_value_name in rule:
            rule[self.single_value_name]["actual"] = single_value
            if rule[self.single_value_name]["name"] == "":
                if rule[self.single_value_name]["name"] == single_value:
                    matches = [""]
            else:
                matches = re.findall(rule[self.single_value_name]["name"], single_value)

            if len(matches) > 0:
                rule[self.single_value_name]["valid"] = "Pass"
                rule[self.single_value_name]["validation_message_code"] = self.pass_message_code
            else:
                rule[self.single_value_name]["valid"] = "Fail"
                rule[self.single_value_name]["validation_message_code"] = self.fail_message_code
        else:
            rule[self.single_value_name] = {
                "name": "",
                "actual": single_value,
                "valid": "Pass",
                "validation_message_code": self.pass_message_code,
            }
