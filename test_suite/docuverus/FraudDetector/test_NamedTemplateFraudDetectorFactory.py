from docuverus.FraudDetector.NamedTemplateFraudDetectorFactory import (
    NamedTemplateFraudDetectorFactory,
)


def test_create_returns_new_fraud_detector():
    template_name = "Template A"
    fraud_detector = NamedTemplateFraudDetectorFactory().create(template_name)

    assert fraud_detector.template_type == template_name
