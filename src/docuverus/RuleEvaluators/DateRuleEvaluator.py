import logging
from datetime import datetime, timedelta

from docuverus.RuleEvaluators.EvaluateDatesWithSpecificCreationDateAndGreaterModDate import (
    EvaluateDatesWithSpecificCreationDateAndGreaterModDate,
)
from docuverus.RuleEvaluators.EvaluateDatesWithSpecificValue import (
    EvaluateDatesWithSpecificValue,
)
from docuverus.RuleEvaluators.EvaluateNoneCreateDate import EvaluateNoneCreateDate
from docuverus.RuleEvaluators.EvaluateNoneDates import EvaluateNoneDates
from docuverus.RuleEvaluators.EvaluateNoneModDate import EvaluateNoneModDate
from docuverus.RuleEvaluators.EvaluateSpecificValueWithNoneModDate import (
    EvaluateSpecificValueWithNoneModDate,
)
from docuverus.RuleEvaluators.EvaluateSpecificValueWithPresentModDate import (
    EvaluateSpecificValueWithPresentModDate,
)
from docuverus.RuleEvaluators.EvaluateUnparseableDates import EvaluateUnparseableDates
from docuverus.RuleEvaluators.GreaterModDateComparator import GreaterModDateComparator
from docuverus.RuleEvaluators.LesserModDateComparator import LesserModDateComparator
from docuverus.RuleEvaluators.NoDateRuleEvaluator import NoDateRuleComparator
from docuverus.RuleEvaluators.RuleEvaluator import RuleEvaluator
from docuverus.RuleEvaluators.ToleranceDurationDateComparator import (
    ToleranceDurationDateComparator,
)
from docuverus.Utils.Messages import MessageCode


class DateInfo:
    def __init__(
        self,
        creation_date,
        expected_creation_state,
        expected_duration,
        expected_mod_state,
        expected_tolerance,
        modification_date,
    ):
        self.creation_date = creation_date
        self.expected_creation_state = expected_creation_state
        self.expected_duration = expected_duration
        self.expected_mod_state = expected_mod_state
        self.expected_tolerance = expected_tolerance
        self.modification_date = modification_date


class DateRuleEvaluator(RuleEvaluator):
    DEFAULT_EQUAL_TOLERANCE_SECONDS = 1

    def __init__(self, evaluation_mapping=None):
        if evaluation_mapping is None:
            evaluation_mapping = {
                ("Unparseable", "Present", False, False): EvaluateUnparseableDates(True, False),
                ("Unparseable", "Unparseable", False, False): EvaluateUnparseableDates(True, True),
                ("Present", "Unparseable", False, False): EvaluateUnparseableDates(False, True),
                ("None", "None", False, False): EvaluateNoneDates(),
                ("None", "Present", False, False): EvaluateNoneCreateDate(),
                ("Present", "Equal", True, False): ToleranceDurationDateComparator(),
                ("Present", "Equal", False, False): ToleranceDurationDateComparator(),
                ("Present", "None", False, False): EvaluateNoneModDate(),
                ("Present", "Greater", False, True): ToleranceDurationDateComparator(),
                ("Present", "Greater", False, False): GreaterModDateComparator(),
                ("Present", "Lesser", False, False): LesserModDateComparator(),
                ("Specific", "Specific", False, False): EvaluateDatesWithSpecificValue(),
                ("Specific", "Greater", False, False): EvaluateDatesWithSpecificCreationDateAndGreaterModDate(),
                (
                    "Specific",
                    "Present",
                    False,
                    False,
                ): EvaluateSpecificValueWithPresentModDate(),
                ("Specific", "None", False, False): EvaluateSpecificValueWithNoneModDate(),
                ("Specific", "Equal", False, False): EvaluateDatesWithSpecificValue(),
            }
        self.evaluation_mapping = evaluation_mapping

    def evaluate(self, input_rule, metadata):
        logging.info(f"Starting Date Rule Evaluator")
        date_info = self.get_date_info(input_rule, metadata)

        # Parsing of the creation and modification dates
        creation_datetime = self.parse_date_string_into_datetime(date_info.creation_date, input_rule, "created")
        modification_datetime = self.parse_date_string_into_datetime(
            date_info.modification_date, input_rule, "modified"
        )

        if not creation_datetime or not modification_datetime:
            self.update_rule_for_unparseable_dates(creation_datetime, modification_datetime, date_info, input_rule)

        self.date_evaluation(
            creation_datetime,
            date_info.expected_creation_state,
            date_info.expected_duration,
            date_info.expected_mod_state,
            date_info.expected_tolerance,
            input_rule,
            modification_datetime,
        )

    def update_rule_for_unparseable_dates(self, creation_datetime, modification_datetime, date_info, input_rule):
        date_info.expected_mod_state = "Present"
        date_info.expected_creation_state = "Present"
        if not creation_datetime:
            date_info.expected_creation_state = "Unparseable"
            input_rule["dates"]["created"]["valid"] = "Fail"
            input_rule["dates"]["created"]["validation_message_code"] = MessageCode.MSG_INVALID_DATE_FORMAT
        if not modification_datetime:
            date_info.expected_mod_state = "Unparseable"
            input_rule["dates"]["modified"]["valid"] = "Fail"
            input_rule["dates"]["modified"]["validation_message_code"] = MessageCode.MSG_INVALID_DATE_FORMAT
        input_rule["dates"]["valid"] = "Fail"
        input_rule["dates"]["validation_message_code"] = MessageCode.MSG_INVALID_CREATION_MODIFICATION_DATES

    def parse_date_string_into_datetime(self, date_string, input_rule, date_type):
        if date_string == "":
            date_string = "None"
        input_rule["dates"][date_type]["actual"] = date_string
        date_string = date_string.split("-")[0]
        date_string = date_string.split("+")[0]
        date_string = date_string.split("Z")[0]
        date_string = date_string.split("UTC")[0]
        date_string = date_string.replace("\r", "").replace("\n", "")
        try:
            parsed_datetime = datetime.strptime(date_string, "D:%Y%m%d%H%M%S") if date_string != "None" else "None"
        except ValueError:
            logging.warning(f"Error converting the date in format: D:%Y%m%d%H%M%S ")
            try:
                parsed_datetime = (
                    datetime.strptime(date_string, "%m/%d/%Y %H:%M:%S") if date_string != "None" else "None"
                )
            except ValueError:
                logging.warning(f"Error converting the date in format: %m/%d/%Y %H:%M:%S")
                try:
                    parsed_datetime = datetime.strptime(date_string, "D:%Y%m%d") if date_string != "None" else "None"
                except ValueError:
                    parsed_datetime = None

        return parsed_datetime

    def get_date_info(self, input_rule, metadata):
        logging.info(f"Extracting creation and modification dates")
        expected_creation_state = input_rule["dates"]["created"]["state"]
        if expected_creation_state.startswith("D:"):
            expected_creation_state = "Specific"
        expected_mod_state = input_rule["dates"]["modified"]["state"]
        if expected_mod_state.startswith("D:"):
            expected_mod_state = "Specific"
        modified_rule = input_rule["dates"]["modified"]
        expected_tolerance_int = modified_rule.get("tolerance")
        if expected_tolerance_int is None and expected_creation_state == "Present" and expected_mod_state == "Equal":
            expected_tolerance_int = self.DEFAULT_EQUAL_TOLERANCE_SECONDS
        elif expected_tolerance_int is None:
            expected_tolerance_int = 0
        expected_tolerance = timedelta(seconds=expected_tolerance_int)
        expected_duration_int = modified_rule.get("duration", 0)
        expected_duration = timedelta(seconds=expected_duration_int)
        creation_date = metadata["creationDate"]
        modification_date = metadata["modDate"]

        return DateInfo(
            creation_date,
            expected_creation_state,
            expected_duration,
            expected_mod_state,
            expected_tolerance,
            modification_date,
        )

    def date_evaluation(
        self,
        creation_datetime,
        expected_creation_state,
        expected_duration,
        expected_mod_state,
        expected_tolerance,
        input_rule,
        modification_datetime,
    ):
        evaluation_key = (
            expected_creation_state,
            expected_mod_state,
            expected_tolerance.seconds > 0,
            expected_duration.seconds > 0,
        )
        evaluation_instance = self.evaluation_mapping.get(evaluation_key)
        logging.info(f"Date Evaluation Mapping : {evaluation_instance}")
        if evaluation_instance:
            evaluation_instance.compare(
                input_rule,
                creation_datetime,
                modification_datetime,
                expected_tolerance,
                expected_duration,
            )
        else:
            NoDateRuleComparator().compare(
                input_rule, creation_datetime, modification_datetime, expected_tolerance, expected_duration
            )
