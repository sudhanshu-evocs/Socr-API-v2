import importlib.resources
import json


class Messages:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Messages, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        with importlib.resources.open_text("docuverus.Utils.Data", "Messages.json") as file:
            self.messages = json.load(file)

    def getMessageCodeForMessage(self, message):
        for value in self.messages:
            if value["message"] == message:
                return value["code"]


class MessageCode:
    MSG_VALID_DATE_COMPARATOR = "MSG_VALID_DATE_COMPARATOR"
    MSG_VALID_PRODUCER = "MSG_VALID_PRODUCER"
    MSG_INVALID_PRODUCER = "MSG_INVALID_PRODUCER"
    MSG_VALID_CREATION_DATE = "MSG_VALID_CREATION_DATE"
    MSG_INVALID_CREATION_DATE = "MSG_INVALID_CREATION_DATE"
    MSG_CREATION_DATE_FOUND = "MSG_CREATION_DATE_FOUND"  # Creation date is present.
    MSG_CREATION_DATE_NOT_FOUND = "MSG_CREATION_DATE_NOT_FOUND"  # Creation date is not present.
    MSG_CREATION_DATE_SHOULD_BE_NONE = "MSG_CREATION_DATE_SHOULD_BE_NONE"  # Creation date should be None.
    MSG_VALID_MODIFICATION_DATE = "MSG_VALID_MODIFICATION_DATE"
    MSG_INVALID_MODIFICATION_DATE = "MSG_INVALID_MODIFICATION_DATE"
    MSG_MODIFICATION_DATE_FOUND = "MSG_MODIFICATION_DATE_FOUND"  # Modification date is present.
    MSG_MODIFICATION_DATE_NOT_FOUND = "MSG_MODIFICATION_DATE_NOT_FOUND"  # Modification date is not present
    MSG_MODIFICATION_DATE_SHOULD_BE_NONE = "MSG_MODIFICATION_DATE_SHOULD_BE_NONE"  # Modification date should be None
    MSG_VALID_CREATION_MODIFICATION_DATES = "MSG_VALID_CREATION_MODIFICATION_DATES"
    # Combination of creation and modification date matches validation rules.
    MSG_INVALID_CREATION_MODIFICATION_DATES = "MSG_INVALID_CREATION_MODIFICATION_DATES"
    # Combination of creation and modification date does not match validation rules.
    MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE = "MSG_CREATION_DATE_MATCHES_SPECIFIC_VALUE"
    # Creation date matches with specific value.
    MSG_CREATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE = "MSG_CREATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE"
    # Creation date does not match with specific value.
    MSG_MODIFICATION_DATE_MATCHES_SPECIFIC_VALUE = "MSG_MODIFICATION_DATE_MATCHES_SPECIFIC_VALUE"
    # Modification date matches with specific value.
    MSG_MODIFICATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE = "MSG_MODIFICATION_DATE_DOES_NOT_MATCH_SPECIFIC_VALUE"
    # Modification date does not match with specific value.
    MSG_INVALID_DATE_FORMAT = "MSG_INVALID_DATE_FORMAT"  # Date not in correct format.
    MSG_DATES_VALID_TOLERANCE = "MSG_DATES_VALID_TOLERANCE"
    # Creation date plus duration equals modification date within tolerance.
    MSG_DATES_INVALID_TOLERANCE = "MSG_DATES_INVALID_TOLERANCE"
    # Creation date plus duration does not equal modification date within tolerance.
    MSG_PRODUCER_MATCH = "MSG_PRODUCER_MATCH"  # Producer matches.
    MSG_PRODUCER_DOES_NOT_MATCH = "MSG_PRODUCER_DOES_NOT_MATCH"  # Producer not matched.
    MSG_PRODUCER_BROWSER_PRINTED = "MSG_PRODUCER_BROWSER_PRINTED"  # Producer appears browser printed.
    MSG_TEMPLATE_TYPE_MATCH = "MSG_TEMPLATE_TYPE_MATCH"  # Template type matched.
    MSG_TEMPLATE_TYPE_DOES_NOT_MATCH = "MSG_TEMPLATE_TYPE_DOES_NOT_MATCH"  # Template type not matched.
    MSG_FILE_SIZE_VALID = "MSG_FILE_SIZE_VALID"  # File size is valid.
    MSG_FILE_SIZE_INVALID = "MSG_FILE_SIZE_INVALID"  # File size is invalid.
    MSG_FILE_DOES_NOT_EXIST = "MSG_FILE_DOES_NOT_EXIST"  # File does not exist.
    MSG_VALID_FILE_SIZE_UNKNOWN = "MSG_VALID_FILE_SIZE_UNKNOWN"  # Valid file size is unknown.
    MSG_NOT_APPLICABLE = "MSG_NOT_APPLICABLE"  # NOT_APPLICABLE
    MSG_CREATOR_MATCH = "MSG_CREATOR_MATCH"  # Creator matches.
    MSG_CREATOR_DOES_NOT_MATCH = "MSG_CREATOR_DOES_NOT_MATCH"  # Creator not matched.
    MSG_CREATOR_BROWSER_PRINTED = "MSG_CREATOR_BROWSER_PRINTED"  # Creator appears browser printed.
    MSG_AUTHOR_MATCH = "MSG_AUTHOR_MATCH"  # Author matches.
    MSG_AUTHOR_DOES_NOT_MATCH = "MSG_AUTHOR_DOES_NOT_MATCH"  # Author not matched.
    MSG_FONT_MATCHED = "MSG_FONT_MATCHED"  # Font is matched.
    MSG_FONT_VALIDATION_VALID = "MSG_FONT_VALIDATION_VALID"  # Fonts present match validation rules.
    MSG_FONT_VALIDATION_INVALID = "MSG_FONT_VALIDATION_INVALID"  # Fonts present do not match validation rules.
    MSG_FRAUD_FONT_FOUND = "MSG_FRAUD_FONT_FOUND"  # Fraud font found.
    MSG_REQUIRED_FONT_NOT_MATCHED = "MSG_REQUIRED_FONT_NOT_MATCHED"  # Required font not matched.
    MSG_REQUIRED_FONT_MATCHED = "MSG_REQUIRED_FONT_MATCHED"  # Required font matched.
    MSG_OPTIONAL_FONT_NOT_MATCHED = "MSG_OPTIONAL_FONT_NOT_MATCHED"
    MSG_OPTIONAL_FONT_MATCHED = "MSG_OPTIONAL_FONT_MATCHED"
    MSG_OPTIONAL_FONT_NOT_FOUND = "MSG_OPTIONAL_FONT_NOT_FOUND"  # Optional font not found.
    MSG_OPTIONAL_FONT_FOUND = "MSG_OPTIONAL_FONT_FOUND"  # Optional font found.
    MSG_FONT_NOT_APPLICABLE = "MSG_FONT_NOT_APPLICABLE"  # Font not applicable.
    MSG_FONT_RULE_NOT_APPLICABLE = "MSG_FONT_RULE_NOT_APPLICABLE"  # Font rule not applicable.
    ERROR_INVALID_DATE_RULE = "ERROR_INVALID_DATE_RULE"  # Invalid date rule.
    ERROR_UNKNOWN_DATE_VALIDATION_RULE = "ERROR_UNKNOWN_DATE_VALIDATION_RULE"  # Unknown date validation rule.
    MSG_INVALID_IMAGE_DOCUMENT = "MSG_INVALID_IMAGE_DOCUMENT"  # Invalid image document.
    MSG_INVALID_FILE = "MSG_INVALID_FILE"  # Invalid file
    MSG_BROWSER_PRINTED_DOCUMENT = "MSG_BROWSER_PRINTED_DOCUMENT"  # Invalid file appears browser printed.
    MSG_INVALID_PDF_FILE = "MSG_INVALID_PDF_FILE"  # Invalid PDF file.
    MSG_VALID_FILE = "MSG_VALID_FILE"  # Valid file.
    MSG_UNKNOWN_TEMPLATE_TYPE = "MSG_UNKNOWN_TEMPLATE_TYPE"  # Unknown template type.
    MSG_FURTHER_VALIDATION_REQUIRED_UNKNOWN_TEMPLATE = "MSG_FURTHER_VALIDATION_REQUIRED_UNKNOWN_TEMPLATE"
    MSG_FURTHER_DOCUMENTATION_REQUIRED = "MSG_FURTHER_DOCUMENTATION_REQUIRED"  # Further documentation required.
    MSG_TEMPLATE_TYPE_DOES_NOT_EXIST = "MSG_TEMPLATE_TYPE_DOES_NOT_EXIST"  # Template type does not exist.
    MSG_FURTHER_VERIFICATION_REQUIRED_LOW_CONFIDENCE = "MSG_FURTHER_VERIFICATION_REQUIRED_LOW_CONFIDENCE"
    MSG_FURTHER_VALIDATION_REQUIRED_UNTRUSTED_TEMPLATE = "MSG_FURTHER_VALIDATION_REQUIRED_UNTRUSTED_TEMPLATE"
    MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO = "MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO"


class ValidStates:
    STATE_FDR = "FDR"
    STATE_FAIL = "Fail"
    STATE_PASS = "Pass"
