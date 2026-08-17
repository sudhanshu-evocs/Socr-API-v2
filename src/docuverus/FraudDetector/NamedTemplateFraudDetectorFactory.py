from docuverus.FraudDetector.FraudDetector import FraudDetector


class NamedTemplateFraudDetectorFactory:

    def create(self, template_name):
        return FraudDetector(template_name, None, None)
