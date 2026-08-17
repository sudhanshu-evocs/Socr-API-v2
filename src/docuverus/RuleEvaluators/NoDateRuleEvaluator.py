import logging

from docuverus.RuleEvaluators.DateComparator import DateComparator
from docuverus.Utils.Messages import MessageCode, ValidStates


class NoDateRuleComparator(DateComparator):
    def compare(
        self,
        input_rule,
        creation_datetime,
        modification_datetime,
        expected_tolerance,
        expected_duration,
    ):
        logging.info(f"No Dates found in the document")
        input_rule["dates"]["created"]["valid"] = ValidStates.STATE_FDR
        input_rule["dates"]["created"]["validation_message_code"] = MessageCode.ERROR_INVALID_DATE_RULE

        input_rule["dates"]["modified"]["valid"] = ValidStates.STATE_FDR
        input_rule["dates"]["modified"]["validation_message_code"] = MessageCode.ERROR_INVALID_DATE_RULE

        input_rule["dates"]["valid"] = ValidStates.STATE_FDR
        input_rule["dates"]["validation_message_code"] = MessageCode.ERROR_UNKNOWN_DATE_VALIDATION_RULE
