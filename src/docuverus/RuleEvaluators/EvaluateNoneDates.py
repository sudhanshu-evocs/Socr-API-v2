import logging

from docuverus.RuleEvaluators.DateComparator import DateComparator
from docuverus.Utils.Messages import MessageCode

MODIFIED_KEY = "modified"

CREATED_KEY = "created"

CREATION_DATE_STRING = "Creation"

MODIFICATION_DATE_STRING = "Modification"


class EvaluateNoneDates(DateComparator):

    def compare(
        self,
        input_rule,
        creation_datetime,
        modification_datetime,
        expected_tolerance,
        expected_duration,
    ):
        logging.info(f"Evaluating creation and modified dates with none value")
        is_CreationDate_valid = self.update_dates_rule(
            creation_datetime,
            input_rule,
            CREATED_KEY,
            MessageCode.MSG_CREATION_DATE_NOT_FOUND,
            MessageCode.MSG_CREATION_DATE_SHOULD_BE_NONE,
        )
        is_ModificationDate_valid = self.update_dates_rule(
            modification_datetime,
            input_rule,
            MODIFIED_KEY,
            MessageCode.MSG_MODIFICATION_DATE_NOT_FOUND,
            MessageCode.MSG_MODIFICATION_DATE_SHOULD_BE_NONE,
        )

        is_valid = is_CreationDate_valid and is_ModificationDate_valid
        final_validation_message = self.final_valid_message if is_valid else self.final_invalid_message
        self.set_final_validation(input_rule, is_valid, final_validation_message)

    def update_dates_rule(self, datetime, input_rule, key, pass_message_code, fail_message_code):
        is_date_valid = datetime == "None"
        date_message_code = pass_message_code if is_date_valid else fail_message_code
        logging.info(f"Updating Date rule for None Dates")
        self.update_input_rule(input_rule, key, is_date_valid, date_message_code)
        return is_date_valid
