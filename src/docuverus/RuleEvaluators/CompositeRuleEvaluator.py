import logging

from docuverus.RuleEvaluators.BrowserPrintedSingleValueOverrideRuleEvaluator import (
    BrowserPrintedSingleValueOverrideRuleEvaluator,
)
from docuverus.RuleEvaluators.DateRuleEvaluator import DateRuleEvaluator
from docuverus.RuleEvaluators.FileSizeRuleEvaluator import FileSizeRuleEvaluator
from docuverus.RuleEvaluators.FontRuleEvaluator import FontRuleEvaluator
from docuverus.RuleEvaluators.RuleEvaluator import RuleEvaluator
from docuverus.RuleEvaluators.SingleValueRuleEvaluator import SingleValueRuleEvaluator
from docuverus.RuleEvaluators.TemplateTypeRuleEvaluator import TemplateTypeRuleEvaluator
from docuverus.Utils.Messages import MessageCode


class CompositeRuleEvaluator(RuleEvaluator):
    def __init__(self, template_type, rule_evaluators):
        self.template_type = template_type
        self.rule_evaluators = rule_evaluators

    def evaluate(self, rule: dict, metadata: dict) -> None:
        logging.info(f"Evaluating rule with metadata: {metadata}")
        for rule_evaluator in self.rule_evaluators:
            rule_evaluator.evaluate(rule, metadata)
        logging.info("Evaluation completed.")


class CompositeRuleEvaluatorFactory:
    @staticmethod
    def create(template_type):
        evaluator_list = []
        evaluator_list.append(TemplateTypeRuleEvaluator(template_type))
        evaluator_list.append(FileSizeRuleEvaluator())
        evaluator_list.append(
            SingleValueRuleEvaluator(
                template_type,
                "producer",
                MessageCode.MSG_PRODUCER_MATCH,
                MessageCode.MSG_PRODUCER_DOES_NOT_MATCH,
            )
        )
        evaluator_list.append(
            SingleValueRuleEvaluator(template_type, "creator", MessageCode.MSG_CREATOR_MATCH, MessageCode.MSG_CREATOR_DOES_NOT_MATCH)
        )
        evaluator_list.append(BrowserPrintedSingleValueOverrideRuleEvaluator())
        evaluator_list.append(
            SingleValueRuleEvaluator(template_type, "author", MessageCode.MSG_AUTHOR_MATCH, MessageCode.MSG_AUTHOR_DOES_NOT_MATCH)
        )
        evaluator_list.append(FontRuleEvaluator())
        evaluator_list.append(DateRuleEvaluator())
        return CompositeRuleEvaluator(template_type, evaluator_list)
