import datetime

from docuverus.RuleEvaluators.GreaterModDateComparator import GreaterModDateComparator
from test_suite.support.testing_utilities import generate_json_for_date_comparator


def test_invalid_but_doesnt_crash_when_no_mod_date():
    input_rule, expected_rule_result = generate_json_for_date_comparator(
        "Present",
        "Greater",
        "10/30/2023 08:02:15",
        "Pass",
        "MSG_CREATION_DATE_FOUND",
        "None",
        "Fail",
        "MSG_INVALID_MODIFICATION_DATE",
        "Fail",
        "MSG_INVALID_CREATION_MODIFICATION_DATES",
    )
    metadata = {"created": datetime.datetime(2023, 10, 30, 8, 2, 15), "modified": "None"}

    GreaterModDateComparator().compare(input_rule, metadata["created"], metadata["modified"], 0, 0)

    # The DateRuleEvaluator class fills in the actual datetimes, and these need to be removed for this verification
    del expected_rule_result["dates"]["created"]["actual"]
    del expected_rule_result["dates"]["modified"]["actual"]
    assert input_rule == expected_rule_result
