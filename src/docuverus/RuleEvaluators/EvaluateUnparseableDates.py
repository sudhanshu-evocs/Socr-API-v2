import logging

from docuverus.RuleEvaluators.DateComparator import DateComparator
from docuverus.Utils.Messages import MessageCode

MODIFIED_KEY = "modified"

CREATED_KEY = "created"

CREATION_DATE_STRING = "Creation"

MODIFICATION_DATE_STRING = "Modification"


class EvaluateUnparseableDates(DateComparator):
    def __init__(self, created_unparseable, modified_unparseable):
        super().__init__()
        self.created_unparseable = created_unparseable
        self.modified_unparseable = modified_unparseable

    def compare(
        self,
        input_rule,
        creation_datetime,
        modification_datetime,
        expected_tolerance,
        expected_duration,
    ):
        logging.info(f"Evaluating unparseable dates.")
        if self.created_unparseable:
            self.update_input_rule(input_rule, CREATED_KEY, False, MessageCode.MSG_INVALID_DATE_FORMAT)
        else:
            self.update_input_rule(input_rule, CREATED_KEY, True, MessageCode.MSG_CREATION_DATE_FOUND)
        if self.modified_unparseable:
            self.update_input_rule(input_rule, MODIFIED_KEY, False, MessageCode.MSG_INVALID_DATE_FORMAT)
        else:
            self.update_input_rule(input_rule, MODIFIED_KEY, True, MessageCode.MSG_MODIFICATION_DATE_FOUND)
