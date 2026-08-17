import logging
import os
from abc import abstractmethod

from docuverus.RuleEvaluators.get_count_of_paystubs import count_paystubs
from docuverus.RuleEvaluators.RuleEvaluator import RuleEvaluator
from docuverus.Utils.Messages import MessageCode

UNKNOWN = "Unknown"
NOT_APPLICABLE = "NOT_APPLICABLE"
LINEAR_ALGORITHM = "Linear"
FAIL = "Fail"
PASS = "Pass"
DEFAULT_ALGORITHM = "Constant"


class ValidationStrategy:
    @abstractmethod
    def validate(self, rule, metadata):
        pass

    def get_validation_message_code(self, file_size, valid):
        logging.info(f"Updating validation messages for file size rule.")
        if file_size == 0:
            return MessageCode.MSG_FILE_DOES_NOT_EXIST
        elif valid == PASS:
            return MessageCode.MSG_FILE_SIZE_VALID
        elif valid == FAIL:
            return MessageCode.MSG_FILE_SIZE_INVALID
        else:
            return MessageCode.MSG_VALID_FILE_SIZE_UNKNOWN

    def update_rule_validation(self, rule, file_size, valid, validation_message_code):
        rule["file_size"]["actual"] = file_size
        rule["file_size"]["valid"] = valid
        rule["file_size"]["validation_message_code"] = validation_message_code


class ConstantValidationStrategy(ValidationStrategy):
    def validate(self, rule, metadata):
        logging.info(f"Evaluating the file size against constant validation strategy")
        file_size = float(metadata.get("file_size", 0))

        min_size = float(rule["file_size"]["min"])
        max_size = float(rule["file_size"]["max"])

        valid = PASS if min_size <= file_size <= max_size else FAIL
        validation_message_code = self.get_validation_message_code(file_size, valid)
        self.update_rule_validation(rule, file_size, valid, validation_message_code)


class LinearValidationStrategy(ValidationStrategy):
    def validate(self, rule, metadata):
        logging.info(f"Evaluating the file size against linear validation strategy")
        file_size = metadata.get("file_size", 0)
        min_size = rule["file_size"]["min"]
        max_size = rule["file_size"]["max"]
        min_slope = rule["file_size"]["min_slope"]
        max_slope = rule["file_size"]["max_slope"]
        paystub_count = metadata.get("paystub_count", 0)

        calculated_min = min_slope * paystub_count + min_size - min_slope
        calculated_max = max_slope * paystub_count + max_size - max_slope

        valid = PASS if calculated_min <= file_size <= calculated_max else FAIL
        validation_message_code = self.get_validation_message_code(file_size, valid)
        self.update_rule_validation(rule, file_size, valid, validation_message_code)


class UnknownValidationStrategy(ValidationStrategy):
    def validate(self, rule, metadata):
        logging.info(f"Evaluating the file size against unknown validation strategy")
        file_size = metadata.get("file_size", 0)
        valid = NOT_APPLICABLE
        validation_message_code = self.get_validation_message_code(file_size, valid)
        self.update_rule_validation(rule, file_size, valid, validation_message_code)


class FileSizeRuleEvaluator(RuleEvaluator):

    def __init__(self):
        self.strategies = {
            DEFAULT_ALGORITHM: ConstantValidationStrategy(),
            LINEAR_ALGORITHM: LinearValidationStrategy(),
            UNKNOWN: UnknownValidationStrategy(),
        }

    def evaluate(self, rule: dict, metadata: dict) -> None:
        file_size = metadata.get("file_size", 0)

        if "algorithm" not in rule["file_size"]:
            rule["file_size"]["algorithm"] = DEFAULT_ALGORITHM

        algorithm = rule["file_size"].get("algorithm", DEFAULT_ALGORITHM)

        strategy = self.strategies.get(algorithm, None)

        if strategy:
            strategy.validate(rule, metadata)
        else:
            rule["file_size"]["actual"] = file_size
            rule["file_size"]["valid"] = NOT_APPLICABLE
            rule["file_size"]["validation_message_code"] = MessageCode.MSG_NOT_APPLICABLE


def get_file_size(pdf_document):
    if not hasattr(pdf_document, "stream") or pdf_document.stream is None:
        try:
            file_size = os.stat(pdf_document.name).st_size / 1000
            logging.info(f"Extracted file size of file - {pdf_document.name} is {file_size}")
            return file_size
        except Exception:
            return 0
    return len(pdf_document.stream) / 1000


def add_file_size_to_metadata(pdf_document, metadata):
    logging.info(f"Adding file size to metadata dictionary")
    metadata["file_size"] = get_file_size(pdf_document)


def add_paystub_count_to_metadata(reader, metadata):
    logging.info(f"Adding paystub count to metadata dictionary")
    metadata["paystub_count"] = count_paystubs(reader)


# Add this linear algorithm as a strategy by doing either using construction algorithm or some injection framework
# Instead of json file i can create a python file and import the class.
