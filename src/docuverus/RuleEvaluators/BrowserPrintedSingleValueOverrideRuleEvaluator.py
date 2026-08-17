from docuverus.RuleEvaluators.RuleEvaluator import RuleEvaluator
from docuverus.Utils.BrowserPrintedDetector import BrowserPrintedDetector
from docuverus.Utils.Messages import MessageCode, ValidStates


class BrowserPrintedSingleValueOverrideRuleEvaluator(RuleEvaluator):
    _field_message_codes = {
        "producer": MessageCode.MSG_PRODUCER_BROWSER_PRINTED,
        "creator": MessageCode.MSG_CREATOR_BROWSER_PRINTED,
    }

    def evaluate(self, rule: dict, metadata: dict) -> None:
        for field_name, message_code in self._field_message_codes.items():
            if field_name not in rule:
                continue

            field_rule = rule[field_name]
            if field_rule.get("valid") != ValidStates.STATE_FAIL:
                continue

            actual_value = metadata.get(field_name)
            if not BrowserPrintedDetector.is_browser_printed_value(actual_value):
                continue

            field_rule["actual"] = actual_value
            field_rule["valid"] = ValidStates.STATE_FDR
            field_rule["validation_message_code"] = message_code
