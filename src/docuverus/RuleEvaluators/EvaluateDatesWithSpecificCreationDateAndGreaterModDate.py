import logging

from docuverus.RuleEvaluators.DateComparator import DateComparator
from docuverus.Utils.DateTimeUtilities import DateTimeUtilities
from docuverus.Utils.Messages import MessageCode

CREATION_DATE_STRING = "Creation"

MODIFICATION_DATE_STRING = "Modification"


class EvaluateDatesWithSpecificCreationDateAndGreaterModDate(DateComparator):
    def compare(
        self,
        input_rule,
        creation_datetime,
        modification_datetime,
        expected_tolerance,
        expected_duration,
    ):
        logging.info(f"Evaluating Dates with specific creation date and greater modified date")
        expected_creation_date = input_rule["dates"]["created"]["state"]

        expected_creation_datetime = DateTimeUtilities.create(expected_creation_date)

        is_CreationDate_valid = expected_creation_datetime == creation_datetime
        if is_CreationDate_valid:
            self.update_input_rule(
                input_rule,
                "created",
                True,
                MessageCode.MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE,
            )
        else:
            self.update_input_rule(
                input_rule,
                "created",
                False,
                MessageCode.MSG_CREATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE,
            )

        is_ModificationDate_valid = modification_datetime > creation_datetime
        if is_ModificationDate_valid:
            self.update_input_rule(
                input_rule,
                "modified",
                True,
                MessageCode.MSG_VALID_MODIFICATION_DATE,
            )
        else:
            self.update_input_rule(
                input_rule,
                "modified",
                False,
                MessageCode.MSG_INVALID_MODIFICATION_DATE,
            )

        is_valid = is_CreationDate_valid and is_ModificationDate_valid
        final_validation_message = self.final_valid_message if is_valid else self.final_invalid_message
        self.set_final_validation(input_rule, is_valid, final_validation_message)
