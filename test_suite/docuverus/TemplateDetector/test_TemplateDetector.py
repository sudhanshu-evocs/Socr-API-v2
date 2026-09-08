from unittest.mock import MagicMock

from docuverus.TemplateDetector.TemplateDetector import TemplateDetector


def test_detector_selects_distinct_metadata_fingerprint_and_category():
    metadata = {
        "image_file": False,
        "producer": "",
        "creator": "OpenText Exstream Version 16.4.11 64-bit",
        "file_size": 72.8,
        "paystub_count": 0,
        "fonts": [
            {"name": "ABCDEF+ArialMT", "subtype": "TrueType", "encoding": "WinAnsiEncoding"},
            {"name": "ABCDEF+Arial-BoldMT", "subtype": "TrueType", "encoding": "WinAnsiEncoding"},
        ],
    }
    ally_rule = {
        "template": {"name": "Ally"},
        "producer": {"name": "^FailProducer.*"},
        "creator": {"name": "^OpenText Exstream.*"},
        "file_size": {"algorithm": "Constant", "min": 10, "max": 50},
        "fonts": {
            "required_fonts": [{"name": "ArialMT"}, {"name": "Arial-BoldMT"}],
            "optional_fonts": [],
        },
    }
    other_rule = {
        "template": {"name": "Other Bank"},
        "producer": {"name": "^Different Producer.*"},
        "creator": {"name": "^Different Creator.*"},
        "file_size": {"algorithm": "Constant", "min": 1, "max": 10},
        "fonts": {"required_fonts": [{"name": "Courier"}], "optional_fonts": []},
    }
    rule_set_factory = MagicMock()
    rule_set_factory.get_all_template_rules_with_categories.return_value = [
        {"rule": ally_rule, "category": "Bank Statements"},
        {"rule": other_rule, "category": "Bank Statements"},
    ]
    metadata_extractor = MagicMock()
    metadata_extractor.extract_metadata.return_value = metadata

    result = TemplateDetector(rule_set_factory, metadata_extractor).detect(b"pdf", "Valid_Ally_Bank_Statement.pdf")

    assert result["auto_select"] is True
    assert result["template_name"] == "Ally"
    assert result["category"] == "Bank Statements"
    assert result["document_class"] == "Bank Statement"
    assert result["confidence"] == 63
    assert set(result["matched_signals"]) == {"creator", "fonts", "filename_hint"}


def test_detector_does_not_auto_select_an_ambiguous_match():
    rule_set_factory = MagicMock()
    shared_rule = {
        "producer": {"name": "^Shared.*"},
        "creator": {"name": "^Creator.*"},
        "file_size": {"algorithm": "Unknown"},
        "fonts": {"required_fonts": [], "optional_fonts": []},
    }
    rule_set_factory.get_all_template_rules_with_categories.return_value = [
        {"rule": {**shared_rule, "template": {"name": "Template A"}}, "category": "Bank Statements"},
        {"rule": {**shared_rule, "template": {"name": "Template B"}}, "category": "Bank Statements"},
    ]
    metadata_extractor = MagicMock()
    metadata_extractor.extract_metadata.return_value = {
        "image_file": False,
        "producer": "Shared Producer",
        "creator": "Creator App",
        "file_size": 20,
        "fonts": [],
    }

    result = TemplateDetector(rule_set_factory, metadata_extractor).detect(b"pdf")

    assert result["confidence"] == 65
    assert result["confidence_margin"] == 0
    assert result["auto_select"] is False
    assert "not distinct enough" in result["reason"]
