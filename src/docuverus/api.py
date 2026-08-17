from collections.abc import Iterable

from docuverus.FraudDetector.FraudDetector import FraudDetector
from docuverus.FraudDetector.MetadataExtractor import MetadataExtractor
from docuverus.RuleEvaluators.CompositeRuleEvaluator import CompositeRuleEvaluatorFactory
from docuverus.RuleEvaluators.RuleSetFactory import RuleSetFactory

RULE_PACKAGES = [
    "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
    "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
]

def create_rule_set_factory(rule_packages: Iterable[str] | None = None) -> RuleSetFactory:
    return RuleSetFactory(RULE_PACKAGES if rule_packages is None else rule_packages)


def validate_metadata(pdf_bytes: bytes, template_name: str, rule_packages: Iterable[str] | None = None) -> dict:
    rule_set_factory = create_rule_set_factory(rule_packages)
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_name)
    fraud_detector = FraudDetector(template_name, rule_evaluator, rule_set_factory)
    metadata = MetadataExtractor().extract_metadata(pdf_bytes, template_name)
    return fraud_detector.get_document_validations_for_metadata(metadata)


def get_template_names(rule_packages: Iterable[str] | None = None) -> list[str]:
    rule_set_factory = create_rule_set_factory(rule_packages)
    return sorted(rule_set_factory.get_template_names())


def get_template_categories(rule_packages: Iterable[str] | None = None) -> dict[str, list[str]]:
    rule_set_factory = create_rule_set_factory(rule_packages)
    return rule_set_factory.get_template_categories()

