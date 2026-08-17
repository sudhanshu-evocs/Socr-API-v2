from datetime import timedelta

from docuverus.RuleEvaluators.DateRuleEvaluator import DateRuleEvaluator
from docuverus.Utils.Messages import MessageCode, ValidStates


class DateOverrideRule:
    MIN_OVERRIDE_DELTA = timedelta(seconds=0)
    MAX_OVERRIDE_DELTA = timedelta(hours=5)
    OVERRIDDEN_RULE_NAMES = ("template", "producer", "creator", "author", "file_size", "fonts")
    ALLOWED_NON_PASS_MESSAGE_CODES = {
        "fonts": {MessageCode.MSG_FONT_RULE_NOT_APPLICABLE},
    }

    def __init__(self, date_rule_evaluator=None):
        self.date_rule_evaluator = date_rule_evaluator or DateRuleEvaluator()

    def apply(self, rule_set, metadata):
        if not self._all_non_date_validators_pass(rule_set):
            return False

        creation_datetime = self.date_rule_evaluator.parse_date_string_into_datetime(metadata.get("creationDate", ""), rule_set, "created")
        modification_datetime = self.date_rule_evaluator.parse_date_string_into_datetime(metadata.get("modDate", ""), rule_set, "modified")

        if creation_datetime in (None, "None") or modification_datetime in (None, "None"):
            return False

        delta = modification_datetime - creation_datetime
        if delta <= self.MIN_OVERRIDE_DELTA or delta >= self.MAX_OVERRIDE_DELTA:
            return False

        self._rewrite_date_results(rule_set)
        return True

    def _all_non_date_validators_pass(self, rule_set):
        for rule_name in self.OVERRIDDEN_RULE_NAMES:
            field_rule = rule_set.get(rule_name, {})
            if field_rule.get("valid") == ValidStates.STATE_PASS:
                continue
            if field_rule.get("validation_message_code") in self.ALLOWED_NON_PASS_MESSAGE_CODES.get(rule_name, set()):
                continue
            return False
        return True

    def _rewrite_date_results(self, rule_set):
        rule_set["dates"]["modified"]["valid"] = ValidStates.STATE_FDR
        rule_set["dates"]["modified"]["validation_message_code"] = MessageCode.MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO
        rule_set["dates"]["valid"] = ValidStates.STATE_FDR
        rule_set["dates"]["validation_message_code"] = MessageCode.MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO
