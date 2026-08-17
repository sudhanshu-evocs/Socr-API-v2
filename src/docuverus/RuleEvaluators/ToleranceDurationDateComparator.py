import logging
from datetime import timedelta

from docuverus.RuleEvaluators.DateComparator import DateComparator
from docuverus.Utils.Messages import MessageCode


class ToleranceDurationDateComparator(DateComparator):
    def compare(
        self,
        input_rule,
        creation_datetime,
        modification_datetime,
        expected_tolerance,
        expected_duration,
    ):
        logging.info(f"Evaluating tolerance duration date comparator")
        if creation_datetime == "None" or modification_datetime == "None":
            self.update_input_rule(
                input_rule,
                "created",
                (creation_datetime != "None"),
                (MessageCode.MSG_CREATION_DATE_FOUND if (creation_datetime != "None") else MessageCode.MSG_CREATION_DATE_NOT_FOUND),
            )
            self.update_input_rule(
                input_rule,
                "modified",
                (modification_datetime != "None"),
                (
                    MessageCode.MSG_MODIFICATION_DATE_FOUND
                    if (modification_datetime != "None")
                    else MessageCode.MSG_MODIFICATION_DATE_NOT_FOUND
                ),
            )
            self.set_final_validation(input_rule, False, self.final_invalid_message)
        else:
            actual_duration = modification_datetime - creation_datetime
            actual_variance = actual_duration - expected_duration
            is_valid = actual_variance >= timedelta(seconds=0) and actual_variance <= expected_tolerance

            if is_valid:
                self.update_input_rule(input_rule, "created", True, MessageCode.MSG_CREATION_DATE_FOUND)
                self.update_input_rule(input_rule, "modified", True, MessageCode.MSG_DATES_VALID_TOLERANCE)
                self.set_final_validation(input_rule, True, self.final_valid_message)
            else:
                self.update_input_rule(input_rule, "created", True, MessageCode.MSG_CREATION_DATE_FOUND)
                self.update_input_rule(input_rule, "modified", False, MessageCode.MSG_DATES_INVALID_TOLERANCE)
                self.set_final_validation(input_rule, False, self.final_invalid_message)
