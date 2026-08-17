from docuverus.FraudDetector.MultiTemplateFraudDetector import (
    MultiTemplateFraudDetector,
)
from docuverus.Utils.Messages import ValidStates


class UntrustedTemplateResultDetector:
    def is_result_from_untrusted_template(self, fraud_detector_result):
        pass


class CompleteMetadataWorkflow:
    def __init__(
        self,
        template_detector,
        fraud_detector=MultiTemplateFraudDetector(),
        generic_fraud_detector=MultiTemplateFraudDetector(),
    ):
        self.template_detector = template_detector
        self.fraud_detector = fraud_detector
        self.confidence_threshold = 90
        self.generic_fraud_detector = generic_fraud_detector

    def run(self, byte_stream):

        named_template_results = self.fraud_detector.run(byte_stream, self.template_detector.get_template_confidences(byte_stream))

        # First see if there is a pass, return that
        for named_result in named_template_results:
            if named_result["final_validation_results"]["valid"] == ValidStates.STATE_PASS:
                return [named_result]
        for named_result in named_template_results:
            if named_result["final_validation_results"]["valid"] == ValidStates.STATE_FDR:
                return [named_result]
        # If none have passed or hit the date override, return the first failure
        for named_result in named_template_results:
            if named_result["final_validation_results"]["valid"] == ValidStates.STATE_FAIL:
                return [named_result]

        # If no results, proceed to checking with generic_fraud_detector
        results = self.generic_fraud_detector.get_document_validations(byte_stream)
        return results
