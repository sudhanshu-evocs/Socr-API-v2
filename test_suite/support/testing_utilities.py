import json
import re
from difflib import SequenceMatcher

from docuverus.RuleEvaluators.RuleSetFactory import RuleSetFactory


def tokenize_filename(filename):
    # Extract the basename of the file without its directory path or file extension
    basename = re.split(r"[\\/]", filename)[-1].split(".")[0]
    # Updated regex to correctly tokenize uppercase sequences and other cases
    tokens = re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", basename)
    return tokens


def load_template_names(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
        template_names = [rule["template_name"] for rule in data]
    return template_names


def calculate_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def find_most_similar_template_name(filename):
    tokens = filename.split("\\")
    template_names = RuleSetFactory(
        [
            "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
            "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
        ]
    ).get_template_names()

    # Normalize tokens and template names
    tokens = [token.lower() for token in tokens]
    template_names = [name.lower() for name in template_names]

    best_match = None
    highest_similarity = 0

    for token in tokens:
        for template_name in template_names:
            similarity = calculate_similarity(token, template_name)
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = template_name

    if highest_similarity <= 0.5:
        # print(path_tokens)
        print(tokens)
    return best_match if highest_similarity > 0.5 else ""  # Adjust threshold as needed


def generate_json_for_date_comparator(
    created_state,
    modified_state,
    created_actual,
    created_is_valid,
    created_validation_message_code,
    modified_actual,
    modified_is_valid,
    modified_validation_message_code,
    final_validation,
    final_validation_message_code,
):
    input_rule = {
        "dates": {
            "created": {"state": created_state},
            "modified": {"state": modified_state},
        }
    }
    expected_rule_result = {
        "dates": {
            "created": {
                "state": created_state,
                "actual": created_actual,
                "valid": created_is_valid,
                "validation_message_code": created_validation_message_code,
            },
            "modified": {
                "state": modified_state,
                "actual": modified_actual,
                "valid": modified_is_valid,
                "validation_message_code": modified_validation_message_code,
            },
            "valid": final_validation,
            "validation_message_code": final_validation_message_code,
        }
    }
    return input_rule, expected_rule_result
