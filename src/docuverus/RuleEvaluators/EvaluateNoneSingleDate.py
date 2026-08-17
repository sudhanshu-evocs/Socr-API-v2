import logging

from docuverus.RuleEvaluators.DateComparator import DateComparator

MODIFIED_KEY = "modified"
CREATED_KEY = "created"
CREATION_DATE_STRING = "Creation"
MODIFICATION_DATE_STRING = "Modification"


class EvaluateNoneSingleDate(DateComparator):
    def __init__(
        self,
        field_that_should_be_none,
        pass_created_message_code,
        fail_created_message_code,
        pass_modified_message_code,
        fail_modified_message_code,
    ):
        super().__init__()
        self.field_that_should_be_none = field_that_should_be_none
        self.pass_created_message_code = pass_created_message_code
        self.fail_created_message_code = fail_created_message_code
        self.pass_modified_message_code = pass_modified_message_code
        self.fail_modified_message_code = fail_modified_message_code

    def compare(
        self,
        input_rule,
        creation_datetime,
        modification_datetime,
        expected_tolerance,
        expected_duration,
    ):
        logging.info(f"Evaluating dates where create date or modified date is none.")
        is_CreationDate_valid = self.update_dates_rule(
            creation_datetime, input_rule, CREATED_KEY, self.pass_created_message_code, self.fail_created_message_code
        )
        is_ModificationDate_valid = self.update_dates_rule(
            modification_datetime,
            input_rule,
            MODIFIED_KEY,
            self.pass_modified_message_code,
            self.fail_modified_message_code,
        )

        is_valid = is_CreationDate_valid and is_ModificationDate_valid
        final_validation_message = self.final_valid_message if is_valid else self.final_invalid_message
        self.set_final_validation(input_rule, is_valid, final_validation_message)

    def update_dates_rule(self, datetime, input_rule, key, pass_message_code, fail_message_code):
        logging.info(f"Updating Date rule for single none date")
        if key != self.field_that_should_be_none:
            is_date_valid = datetime != "None"
            date_message = pass_message_code if is_date_valid else fail_message_code
        elif key == self.field_that_should_be_none:
            is_date_valid = datetime == "None"
            date_message = pass_message_code if is_date_valid else fail_message_code
        else:
            is_date_valid = False
            date_message = "Invalid State"
        self.update_input_rule(input_rule, key, is_date_valid, date_message)
        return is_date_valid
