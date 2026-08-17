from docuverus.Utils.Messages import MessageCode


class DateComparator:
    def __init__(self):
        self.final_valid_message = MessageCode.MSG_VALID_CREATION_MODIFICATION_DATES
        self.final_invalid_message = MessageCode.MSG_INVALID_CREATION_MODIFICATION_DATES

    def compare(
        self,
        input_rule,
        creation_datetime,
        modification_datetime,
        expected_tolerance,
        expected_duration,
    ):
        pass

    def update_input_rule(self, input_rule, key, valid, message_code):
        input_rule["dates"][key]["valid"] = "Pass" if valid else "Fail"
        input_rule["dates"][key]["validation_message_code"] = message_code

    def set_final_validation(self, input_rule, valid, message_code):
        input_rule["dates"]["valid"] = "Pass" if valid else "Fail"
        input_rule["dates"]["validation_message_code"] = message_code


class ValidateDateFormats(DateComparator):
    def validate(self, input_rule):
        self.update_input_rule(input_rule, "created", False, MessageCode.MSG_INVALID_DATE_FORMAT)
        self.update_input_rule(input_rule, "modified", False, MessageCode.MSG_INVALID_DATE_FORMAT)
        self.set_final_validation(input_rule, False, MessageCode.MSG_INVALID_DATE_FORMAT)
