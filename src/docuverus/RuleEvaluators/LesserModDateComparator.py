import logging

from docuverus.RuleEvaluators.DateComparator import DateComparator
from docuverus.Utils.Messages import MessageCode

MODIFIED_KEY = "modified"

CREATED_KEY = "created"


class LesserModDateComparator(DateComparator):

    def compare(
        self,
        input_rule,
        creation_datetime,
        modification_datetime,
        expected_tolerance,
        expected_duration,
    ):
        logging.info(f"Evaluating Dates with lesser modified date ")
        self.update_input_rule(input_rule, CREATED_KEY, True, MessageCode.MSG_CREATION_DATE_FOUND)
        try:
            if modification_datetime < creation_datetime:
                self.update_input_rule(input_rule, MODIFIED_KEY, True, MessageCode.MSG_VALID_MODIFICATION_DATE)
                self.set_final_validation(input_rule, True, self.final_valid_message)
            else:
                self.update_input_rule(input_rule, MODIFIED_KEY, False, MessageCode.MSG_INVALID_MODIFICATION_DATE)
                self.set_final_validation(input_rule, False, self.final_invalid_message)
        except TypeError:
            self.update_input_rule(input_rule, MODIFIED_KEY, False, MessageCode.MSG_INVALID_MODIFICATION_DATE)
            self.set_final_validation(input_rule, False, self.final_invalid_message)
