import importlib.resources
import json

from docuverus.Utils.Messages import MessageCode
from docuverus.Utils.TemplateNameUtilities import normalize_template_name


class RuleSetFactory:

    def __init__(self, rule_set_packages):
        self.raw_rules_files = []
        self.rule_sources = []
        for rule_set_package in rule_set_packages:
            category = "Paystubs & Earnings" if "EarningStatements" in rule_set_package else "Bank Statements"
            for file in importlib.resources.files(rule_set_package).iterdir():
                if file.is_file() and file.name.endswith(".json"):
                    self.raw_rules_files.append(file)
                    self.rule_sources.append((file, category))

    def get_template_rules(self, template_name):
        rules = []
        normalized_template_name = normalize_template_name(template_name)
        for rule_file in self.raw_rules_files:
            json_list = json.load(rule_file.open())
            for rule_json in json_list:
                if normalize_template_name(rule_json["template"]["name"]) == normalized_template_name:
                    rules.append(rule_json)
        return rules

    def get_template_names(self):
        template_names_by_normalized_name = {}
        for rule_file in self.raw_rules_files:
            rule_json_list = json.load(rule_file.open())
            for rule_json in rule_json_list:
                template_name = rule_json["template"]["name"]
                normalized_template_name = normalize_template_name(template_name)
                if normalized_template_name not in template_names_by_normalized_name:
                    template_names_by_normalized_name[normalized_template_name] = template_name
        return set(template_names_by_normalized_name.values())

    def get_template_categories(self):
        categories = {
            "Bank Statements": set(),
            "Paystubs & Earnings": set()
        }
        for rule_file in self.raw_rules_files:
            is_earning = "EarningStatements" in str(rule_file)
            category_key = "Paystubs & Earnings" if is_earning else "Bank Statements"
            rule_json_list = json.load(rule_file.open())
            for rule_json in rule_json_list:
                t_name = rule_json["template"]["name"]
                categories[category_key].add(t_name)
        return {
            "Bank Statements": sorted(list(categories["Bank Statements"])),
            "Paystubs & Earnings": sorted(list(categories["Paystubs & Earnings"]))
        }

    def get_all_template_rules_with_categories(self):
        rules_with_categories = []
        for rule_file, category in self.rule_sources:
            for rule in json.load(rule_file.open()):
                rules_with_categories.append({"rule": rule, "category": category})
        return rules_with_categories

    def create_empty_rule_set(self, template_name):
        return {
            "template": {
                "name": "",
                "actual": template_name,
                "valid": "Fail",
                "validation_message_code": MessageCode.MSG_TEMPLATE_TYPE_DOES_NOT_EXIST,
            },
            "file_size": {"algorithm": "Unknown"},
            "dates": {"created": {"state": "Unknown"}, "modified": {"state": "Unknown"}},
            "fonts": {},
            "producer": {"name": "Unknown"},
            "creator": {"name": "Unknown"},
            "author": {"name": "Unknown"},
        }
