from docuverus.FraudDetector.FraudDetector import FraudDetector
from docuverus.FraudDetector.MetadataExtractor import MetadataExtractor
from docuverus.RuleEvaluators.CompositeRuleEvaluator import (
    CompositeRuleEvaluatorFactory,
)


class MultiTemplateFraudDetector:
    def run(self, byte_stream, template_confidence_tuples):
        results = []
        for template_confidence_dict in template_confidence_tuples:
            fraud_detector = FraudDetector(
                template_confidence_dict["name"],
                rule_evaluator=CompositeRuleEvaluatorFactory.create(template_confidence_dict["name"]),
            )
            metadata = MetadataExtractor().extract_metadata(byte_stream, template_confidence_tuples)
            result = fraud_detector.get_document_validations_for_metadata(metadata)
            result["template_rule_set_validation_results"][0]["template"]["actual_confidence"] = template_confidence_dict[
                "actual_confidence"
            ]
            results.append(result)
        return results
