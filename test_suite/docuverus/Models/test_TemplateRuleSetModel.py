import importlib.resources
import json
import re

import pytest
from pydantic import BaseModel
from pydantic import ValidationError

from docuverus.Models.TemplateRuleSetModel import TemplateRuleSetModel


def get_file_list_from_package(package):
    file_list = []
    for file in importlib.resources.files(package).iterdir():
        if file.is_file() and file.name.endswith(".json"):
            file_list.append(file)
    return file_list


@pytest.mark.parametrize(
    "template_name, file_path",
    [
        ("1st Bank", "../src/docuverus/RuleEvaluators/TemplateJson/BankStatementsRuleJson/1stBank.json"),
        (
            "Bank of America",
            "../src/docuverus/RuleEvaluators/TemplateJson/EarningStatementsRuleJson/Bank Of America.json",
        ),
    ],
)
def test_template_rule_set_model_validates_from_given_file(template_name, file_path):
    with open(file_path, "r") as file:
        json_data = json.load(file)
        for rule_set in json_data:
            test_object = TemplateRuleSetModel(**rule_set)

    assert test_object is not None
    assert issubclass(test_object.__class__, BaseModel)
    assert test_object.template is not None
    assert test_object.template["name"] == template_name
    assert test_object.producer is not None
    assert test_object.creator is not None
    assert test_object.file_size is not None
    assert test_object.fonts is not None
    assert test_object.dates is not None
    if "created" in test_object.dates and test_object.dates["created"]["state"] == "Present":
        assert test_object.dates["modified"]["state"] != "Present"


@pytest.mark.parametrize("maximum_validation_level", ["Fail", "FDR", "Pass"])
def test_template_rule_set_model_allows_valid_maximum_validation_level(maximum_validation_level):
    test_object = TemplateRuleSetModel(
        template={"name": "Template A", "maximum_validation_level": maximum_validation_level},
        producer={"name": "^Producer.*"},
        creator={"name": "^Creator.*"},
        file_size={"algorithm": "Unknown"},
        fonts={},
        dates={"created": {"state": "None"}, "modified": {"state": "Equal"}},
    )

    assert test_object.template["maximum_validation_level"] == maximum_validation_level


def test_template_rule_set_model_rejects_invalid_maximum_validation_level():
    with pytest.raises(ValidationError):
        TemplateRuleSetModel(
            template={"name": "Template A", "maximum_validation_level": "Unknown"},
            producer={"name": "^Producer.*"},
            creator={"name": "^Creator.*"},
            file_size={"algorithm": "Unknown"},
            fonts={},
            dates={"created": {"state": "None"}, "modified": {"state": "Equal"}},
        )


@pytest.mark.skip()
@pytest.mark.parametrize(
    "template_name, file_path",
    [("Pathward", "../src/docuverus/RuleEvaluators/TemplateJson/BankStatementsRuleJson/Pathward.json")],
)
def test_intentionally_failing_test_for_a_file_without_file_size(template_name, file_path):
    with open(file_path, "r") as file:
        json_data = json.load(file)
        for rule_set in json_data:
            test_object = TemplateRuleSetModel(**rule_set)

    assert test_object is not None
    assert issubclass(test_object.__class__, BaseModel)
    assert test_object.template is not None
    assert test_object.template["name"] == template_name
    assert test_object.file_size is not None


@pytest.mark.parametrize(
    "file_path",
    get_file_list_from_package("docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson")
    + get_file_list_from_package("docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson"),
)
def test_template_rule_set_model_validates_files_in_package(file_path):
    print(file_path)
    with open(file_path, "r") as file:
        json_data = json.load(file)
        for rule_set in json_data:
            test_object = TemplateRuleSetModel(**rule_set)
    assert test_object is not None
    assert issubclass(test_object.__class__, BaseModel)
    assert test_object.template is not None
    assert test_object.dates is not None
    # state in a format of MM/DD/YY are for a very specific templates
    assert test_object.dates["created"]["state"] in ["Present", "None", "D:20040106080349-07'00'", "12/31/01", "D:20101015000000", "D:20191122000000", "D:20201203000000", "D:20140710000000", "08-31-2017"]
    assert test_object.dates["modified"]["state"] in ["Equal", "None", "Present", "Lesser", "Greater", "D:20081124110235-07'00'", "D:20181210000000"]
    if test_object.dates["created"]["state"] == "Present":
        assert test_object.dates["modified"]["state"] != "Present"
    assert test_object.file_size is not None


@pytest.mark.skip()
@pytest.mark.parametrize(
    "file_path",
    get_file_list_from_package("docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson")
    + get_file_list_from_package("docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson"),
)
def test_template_rule_set_model_validates_multiplicity_in_files_in_package(file_path):
    print(file_path)
    with open(file_path, "r") as file:
        json_data = json.load(file)
        for rule_set in json_data:
            test_object = TemplateRuleSetModel(**rule_set)
    assert test_object is not None
    assert issubclass(test_object.__class__, BaseModel)
    assert test_object.template is not None
    assert test_object.dates is not None
    if test_object.fonts["required_fonts"]:
        # Assert that multiplicity is an integer if the list is not empty
        assert isinstance(test_object.fonts["required_fonts"][0]["multiplicity"], int)
        assert test_object.fonts["required_fonts"][0]["encoding"] != "CHANGE_ME"
        assert test_object.fonts["required_fonts"][0]["type"] != "CHANGE_ME"
    if test_object.fonts["optional_fonts"]:
        # Assert that multiplicity is an integer if the list is not empty
        assert isinstance(test_object.fonts["optional_fonts"][0]["multiplicity"], int)
        assert test_object.fonts["optional_fonts"][0]["encoding"] != "CHANGE_ME"
        assert test_object.fonts["optional_fonts"][0]["type"] != "CHANGE_ME"
    assert test_object.file_size is not None


@pytest.mark.parametrize(
    "file_path",
    get_file_list_from_package("docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson")
    + get_file_list_from_package("docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson"),
)
def test_template_rule_set_model_validates_files_in_package_for_producer_and_creator(file_path):
    print(file_path)
    with open(file_path, "r") as file:
        json_data = json.load(file)
        for rule_set in json_data:
            test_object = TemplateRuleSetModel(**rule_set)
    assert test_object is not None
    assert issubclass(test_object.__class__, BaseModel)
    assert test_object.template is not None
    assert test_object.dates is not None
    assert test_object.producer["name"] != "None"
    assert test_object.creator["name"] != "None"
    assert test_object.file_size is not None


# @pytest.mark.skip()
@pytest.mark.parametrize(
    "file_path",
    get_file_list_from_package("docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson")
    + get_file_list_from_package("docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson"),
)
def test_template_rule_set_model_validates_re_in_producer_creator_name(file_path):
    print(file_path)
    with open(file_path, "r") as file:
        json_data = json.load(file)
        for rule_set in json_data:
            test_object = TemplateRuleSetModel(**rule_set)
    assert test_object is not None
    assert issubclass(test_object.__class__, BaseModel)
    assert test_object.template is not None
    assert test_object.dates is not None
    re.compile(test_object.producer["name"])
    re.compile(test_object.creator["name"])
