from docuverus.RuleEvaluators.RuleEvaluator import RuleEvaluator


class EvaluateTemplateConfidence(RuleEvaluator):
    def __init__(self, templates):
        self.templates = templates

    def evaluate(self):
        results = []
        default_confidence_threshold = 95
        for template in self.templates:
            template["name"]
            actual_confidence = template["actual_confidence"]

            if actual_confidence >= default_confidence_threshold:
                results.append({"status": "valid"})
            else:
                results.append({"status": "invalid"})

        return results
