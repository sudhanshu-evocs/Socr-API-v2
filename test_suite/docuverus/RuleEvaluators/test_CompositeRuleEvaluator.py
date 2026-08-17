import fitz

from docuverus.RuleEvaluators.CompositeRuleEvaluator import *
from docuverus.RuleEvaluators.FileSizeRuleEvaluator import add_file_size_to_metadata
from docuverus.Utils.PDFUtilities import PDFUtilities
from test_suite.support.assertions import assert_dict_contains


def test_results_for_valid_bank_of_america_statement_file_size_rule_check():
    # Arrange
    input_rule = {
        "template": {"name": "Bank of America"},
        "producer": {"name": "^TargetStream.*"},
        "file_size": {
            "min": 190,
            "max": 450,
        },
        "dates": {
            "created": {"state": "None"},
            "modified": {"state": "None"},
        },
    }
    expected_rule_result = {
        "template": {
            "name": "Bank of America",
            "actual": "Bank of America",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^TargetStream.*",
            "actual": "TargetStream StreamEDS rv1.7.41 for Bank of America",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "file_size": {
            "min": 190,
            "max": 450,
            "algorithm": "Constant",
            "actual": 308.695,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        },
    }
    template_type = input_rule["template"]["name"]
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    # rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    pdf_document = fitz.open(file_path)
    metadata = pdf_document.metadata
    metadata["template"] = template_type
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(pdf_document)
    # metadata =  {"template": template_type}
    add_file_size_to_metadata(pdf_document, metadata)

    # # Act
    rule_evaluator.evaluate(input_rule, metadata)

    # Assert
    assert_dict_contains(input_rule, expected_rule_result)


def test_results_for_valid_td_bank_statement_file_size_rule_check_for_pro_ios_version():
    # Arrange
    input_rule = {
        "template": {"name": "TD Bank"},
        "producer": {"name": "^iOS Version"},
        "file_size": {
            "min": 140,
            "max": 185,
        },
        "dates": {
            "created": {"state": "None"},
            "modified": {"state": "None"},
        },
    }
    expected_rule_result = {
        "template": {
            "name": "TD Bank",
            "actual": "TD Bank",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^iOS Version",
            "actual": "iOS Version 16.3.1 (Build 20D67) Quartz PDFContext",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "fonts": {
            "additional_fonts": [
                {
                    "actual_multiplicity": 1,
                    "encoding": "MacRomanEncoding",
                    "multiplicity": 0,
                    "name": "Arial-BoldMT",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "MacRomanEncoding",
                    "multiplicity": 0,
                    "name": "ArialMT",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "MacRomanEncoding",
                    "multiplicity": 0,
                    "name": "TimesNewRomanPSMT",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
            ],
            "optional_fonts": [],
            "required_fonts": [],
            "valid": "FDR",
            "validation_message_code": "MSG_FONT_RULE_NOT_APPLICABLE",
        },
        "file_size": {
            "min": 140,
            "max": 185,
            "algorithm": "Constant",
            "actual": 158.519,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        },
    }
    template_type = input_rule["template"]["name"]
    file_path = "../test_documents/Valid_TD_Bank_Statement_ios.pdf"
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    pdf_document = fitz.open(file_path)
    metadata = pdf_document.metadata
    metadata["template"] = template_type
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(pdf_document)
    # metadata = {"template": template_type}
    add_file_size_to_metadata(pdf_document, metadata)
    #  Act
    rule_evaluator.evaluate(input_rule, metadata)

    # Assert
    assert_dict_contains(input_rule, expected_rule_result)


def test_results_for_invalid_bank_of_america_statement_file_size_rule_check():
    # Arrange
    input_rule = {
        "template": {"name": "Bank of America"},
        "producer": {"name": "^TargetStream.*"},
        "file_size": {
            "min": 190,
            "max": 450,
        },
        "dates": {
            "created": {"state": "None"},
            "modified": {"state": "None"},
        },
    }
    expected_rule_result = {
        "template": {
            "name": "Bank of America",
            "actual": "Bank of America",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^TargetStream.*",
            "actual": "Adobe PDF library 11.00",
            "valid": "Fail",
            "validation_message_code": "MSG_PRODUCER_DOES_NOT_MATCH",
        },
        "fonts": {
            "additional_fonts": [
                {
                    "actual_multiplicity": 1,
                    "encoding": "WinAnsiEncoding",
                    "multiplicity": 0,
                    "name": "Arial",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "Connections",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "ConnectionsBold",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "Connections_Medium",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "Helvetica",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "HigherStandards",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "ITC_Franklin_Gothic_Book",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "MyriadPro-Bold",
                    "type": "CIDFontType0",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 7,
                    "encoding": "Identity-H",
                    "multiplicity": 0,
                    "name": "MyriadPro-Bold",
                    "type": "Type0",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "WinAnsiEncoding",
                    "multiplicity": 0,
                    "name": "MyriadPro-Bold",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 2,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "MyriadPro-Regular",
                    "type": "CIDFontType0",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 36,
                    "encoding": "Identity-H",
                    "multiplicity": 0,
                    "name": "MyriadPro-Regular",
                    "type": "Type0",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 5,
                    "encoding": "WinAnsiEncoding",
                    "multiplicity": 0,
                    "name": "MyriadPro-Regular",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "ZapfDingbats",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
            ],
            "optional_fonts": [],
            "required_fonts": [],
            "valid": "FDR",
            "validation_message_code": "MSG_FONT_RULE_NOT_APPLICABLE",
        },
        "file_size": {
            "min": 190,
            "max": 450,
            "algorithm": "Constant",
            "actual": 2373.396,
            "valid": "Fail",
            "validation_message_code": "MSG_FILE_SIZE_INVALID",
        },
    }
    template_type = input_rule["template"]["name"]
    file_path = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf"
    # rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    # metadata = {"template": template_type}
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    pdf_document = fitz.open(file_path)
    metadata = pdf_document.metadata
    metadata["template"] = template_type
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(pdf_document)
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    # # Act
    rule_evaluator.evaluate(input_rule, metadata)

    # Assert
    assert_dict_contains(input_rule, expected_rule_result)


def test_results_for_valid_bank_of_america_statement_template_type_rule_check():
    # Arrange
    input_rule = {
        "template": {"name": "Bank of America"},
        "producer": {"name": "^TargetStream.*"},
        "file_size": {
            "min": 190,
            "max": 450,
        },
        "dates": {
            "created": {"state": "None"},
            "modified": {"state": "None"},
        },
    }
    expected_rule_result = {
        "template": {
            "name": "Bank of America",
            "actual": "Ally Bank",
            "valid": "Fail",
            "validation_message_code": "MSG_TEMPLATE_TYPE_DOES_NOT_MATCH",
        },
        "producer": {
            "name": "^TargetStream.*",
            "actual": "TargetStream StreamEDS rv1.7.41 for Bank of America",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "fonts": {
            "additional_fonts": [
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "Connections",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "ConnectionsBold",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "ConnectionsIta",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "Connections_Medium",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "HigherStandards",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "",
                    "multiplicity": 0,
                    "name": "ITC_Franklin_Gothic_Book",
                    "type": "Type1",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
            ],
            "optional_fonts": [],
            "required_fonts": [],
            "valid": "FDR",
            "validation_message_code": "MSG_FONT_RULE_NOT_APPLICABLE",
        },
        "file_size": {
            "min": 190,
            "max": 450,
            "algorithm": "Constant",
            "actual": 308.695,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        },
    }
    template_type = "Ally Bank"
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    # rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    # metadata = {"template": template_type}
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    pdf_document = fitz.open(file_path)
    metadata = pdf_document.metadata
    metadata["template"] = template_type
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(pdf_document)
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    # # Act
    rule_evaluator.evaluate(input_rule, metadata)

    # Assert
    assert_dict_contains(input_rule, expected_rule_result)


def test_results_for_valid_td_bank_statement_file_size_rule_check():
    # Arrange
    input_rule = {
        "template": {"name": "TD Bank"},
        "producer": {"name": "^iOS Version"},
        "file_size": {
            "min": 140,
            "max": 185,
        },
        "dates": {
            "created": {"state": "None"},
            "modified": {"state": "None"},
        },
    }
    expected_rule_result = {
        "template": {
            "name": "TD Bank",
            "actual": "Bank of America",
            "valid": "Fail",
            "validation_message_code": "MSG_TEMPLATE_TYPE_DOES_NOT_MATCH",
        },
        "producer": {
            "name": "^iOS Version",
            "actual": "iOS Version 16.3.1 (Build 20D67) Quartz PDFContext",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "fonts": {
            "additional_fonts": [
                {
                    "actual_multiplicity": 1,
                    "encoding": "MacRomanEncoding",
                    "multiplicity": 0,
                    "name": "Arial-BoldMT",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "MacRomanEncoding",
                    "multiplicity": 0,
                    "name": "ArialMT",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "MacRomanEncoding",
                    "multiplicity": 0,
                    "name": "TimesNewRomanPSMT",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
            ],
            "optional_fonts": [],
            "required_fonts": [],
            "valid": "FDR",
            "validation_message_code": "MSG_FONT_RULE_NOT_APPLICABLE",
        },
        "file_size": {
            "min": 140,
            "max": 185,
            "algorithm": "Constant",
            "actual": 158.519,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        },
    }
    template_type = "Bank of America"
    file_path = "../test_documents/Valid_TD_Bank_Statement_ios.pdf"
    # rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    # metadata = {"template": template_type}
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    pdf_document = fitz.open(file_path)
    metadata = pdf_document.metadata
    metadata["template"] = template_type
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(pdf_document)
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    # # Act
    rule_evaluator.evaluate(input_rule, metadata)

    # Assert
    assert_dict_contains(input_rule, expected_rule_result)


def test_rule_set_is_altered_by_evaluate():
    input_rule = {
        "template": {"name": "TD Bank"},
        "producer": {
            "name": "^iOS Version",
        },
        "file_size": {
            "min": 140,
            "max": 185,
        },
        "dates": {
            "created": {"state": "None"},
            "modified": {"state": "None"},
        },
    }

    input_rule_after_evaluation = {
        "template": {
            "name": "TD Bank",
            "actual": "TD Bank",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "producer": {
            "name": "^iOS Version",
            "actual": "iOS Version 16.3.1 (Build 20D67) Quartz PDFContext",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "fonts": {
            "additional_fonts": [
                {
                    "actual_multiplicity": 1,
                    "encoding": "MacRomanEncoding",
                    "multiplicity": 0,
                    "name": "Arial-BoldMT",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "MacRomanEncoding",
                    "multiplicity": 0,
                    "name": "ArialMT",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
                {
                    "actual_multiplicity": 1,
                    "encoding": "MacRomanEncoding",
                    "multiplicity": 0,
                    "name": "TimesNewRomanPSMT",
                    "type": "TrueType",
                    "valid": "FDR",
                    "validation_message_code": "MSG_FONT_NOT_APPLICABLE",
                },
            ],
            "optional_fonts": [],
            "required_fonts": [],
            "valid": "FDR",
            "validation_message_code": "MSG_FONT_RULE_NOT_APPLICABLE",
        },
        "file_size": {
            "min": 140,
            "max": 185,
            "algorithm": "Constant",
            "actual": 158.519,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        },
    }

    template_type = "TD Bank"
    file_path = "../test_documents/Valid_TD_Bank_Statement_ios.pdf"
    # rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    # metadata = {"template": template_type}
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    pdf_document = fitz.open(file_path)
    metadata = pdf_document.metadata
    metadata["template"] = template_type
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(pdf_document)
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    rule_evaluator.evaluate(input_rule, metadata)

    assert_dict_contains(input_rule, input_rule_after_evaluation)


def test_integration_of_date_validation():
    input_rule = {
        "template": {"name": "Bank of America"},
        "dates": {
            "created": {"state": "None"},
            "modified": {"state": "None"},
        },
        "file_size": {
            "min": 190,
            "max": 450,
        },
        "producer": {"name": "^TargetStream.*"},
        "fonts": {
            "optional_fonts": [],
            "required_fonts": [],
        },
    }
    expected_rule_result = {
        "template": {
            "name": "Bank of America",
            "actual": "Bank of America",
            "valid": "Pass",
            "validation_message_code": "MSG_TEMPLATE_TYPE_MATCH",
        },
        "dates": {
            "created": {
                "state": "None",
                "actual": "None",
                "valid": "Pass",
                "validation_message_code": "MSG_CREATION_DATE_NOT_FOUND",
            },
            "modified": {
                "state": "None",
                "actual": "None",
                "valid": "Pass",
                "validation_message_code": "MSG_MODIFICATION_DATE_NOT_FOUND",
            },
            "valid": "Pass",
            "validation_message_code": "MSG_VALID_CREATION_MODIFICATION_DATES",
        },
    }
    template_type = input_rule["template"]["name"]
    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    metadata = {"creationDate": "", "modDate": "", "template": template_type, "producer": "TargetStream", "fonts": {}}
    # Act
    rule_evaluator.evaluate(input_rule, metadata)
    # Assert
    assert_dict_contains(input_rule, expected_rule_result)


def test_integration_of_of_creator_validation():
    template_type = "template_type"
    input_rule = {
        "template": {"name": template_type},
        "creator": {"name": "^PDF.*"},
        "file_size": {"algorithm": "Unknown"},
        "dates": {
            "created": {"state": "None"},
            "modified": {"state": "None"},
        },
    }

    expected_rule_result = {
        "creator": {
            "name": "^PDF.*",
            "actual": "PDFlib Personalization Server 9.0.6p1 (PHP7/Linux)",
            "valid": "Pass",
            "validation_message_code": "MSG_CREATOR_MATCH",
        }
    }

    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    metadata = {
        "template": template_type,
        "creator": "PDFlib Personalization Server 9.0.6p1 (PHP7/Linux)",
        "fonts": {},
        "creationDate": "",
        "modDate": "",
    }

    rule_evaluator.evaluate(input_rule, metadata)

    assert_dict_contains(input_rule, expected_rule_result)


def test_integration_of_of_author_validation():
    template_type = "template_type"
    input_rule = {
        "template": {"name": template_type},
        "author": {"name": "^AdobePDFW.*"},
        "file_size": {"algorithm": "Unknown"},
        "dates": {
            "created": {"state": "None"},
            "modified": {"state": "None"},
        },
    }

    expected_rule_result = {
        "author": {
            "name": "^AdobePDFW.*",
            "actual": "AdobePDFWriter",
            "valid": "Pass",
            "validation_message_code": "MSG_AUTHOR_MATCH",
        }
    }

    rule_evaluator = CompositeRuleEvaluatorFactory.create(template_type)
    metadata = {
        "template": template_type,
        "author": "AdobePDFWriter",
        "fonts": {},
        "creationDate": "",
        "modDate": "",
    }

    rule_evaluator.evaluate(input_rule, metadata)

    assert_dict_contains(input_rule, expected_rule_result)


def test_producer_browser_printed_and_creator_match_marks_producer_unknown():
    template_type = "Any Template"
    input_rule = {
        "template": {"name": template_type},
        "producer": {"name": "^ExpectedProducer.*"},
        "creator": {"name": "^ExpectedCreator.*"},
        "file_size": {"algorithm": "Unknown"},
        "dates": {"created": {"state": "None"}, "modified": {"state": "None"}},
        "fonts": {"required_fonts": [], "optional_fonts": []},
    }

    expected = {
        "producer": {
            "name": "^ExpectedProducer.*",
            "actual": "Chrome PDF Printer",
            "valid": "FDR",
            "validation_message_code": "MSG_PRODUCER_BROWSER_PRINTED",
        },
        "creator": {
            "name": "^ExpectedCreator.*",
            "actual": "ExpectedCreator v1",
            "valid": "Pass",
            "validation_message_code": "MSG_CREATOR_MATCH",
        },
    }

    metadata = {
        "template": template_type,
        "producer": "Chrome PDF Printer",
        "creator": "ExpectedCreator v1",
        "fonts": [],
        "creationDate": "",
        "modDate": "",
    }

    CompositeRuleEvaluatorFactory.create(template_type).evaluate(input_rule, metadata)

    assert_dict_contains(input_rule, expected)


def test_creator_browser_printed_and_producer_match_marks_creator_unknown():
    template_type = "Any Template"
    input_rule = {
        "template": {"name": template_type},
        "producer": {"name": "^ExpectedProducer.*"},
        "creator": {"name": "^ExpectedCreator.*"},
        "file_size": {"algorithm": "Unknown"},
        "dates": {"created": {"state": "None"}, "modified": {"state": "None"}},
        "fonts": {"required_fonts": [], "optional_fonts": []},
    }

    expected = {
        "producer": {
            "name": "^ExpectedProducer.*",
            "actual": "ExpectedProducer 3.0",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "creator": {
            "name": "^ExpectedCreator.*",
            "actual": "Safari PDF Creator",
            "valid": "FDR",
            "validation_message_code": "MSG_CREATOR_BROWSER_PRINTED",
        },
    }

    metadata = {
        "template": template_type,
        "producer": "ExpectedProducer 3.0",
        "creator": "Safari PDF Creator",
        "fonts": [],
        "creationDate": "",
        "modDate": "",
    }

    CompositeRuleEvaluatorFactory.create(template_type).evaluate(input_rule, metadata)

    assert_dict_contains(input_rule, expected)

def test_producer_and_creator_mismatch_both_remain_fail():
    template_type = "Any Template"
    input_rule = {
        "template": {"name": template_type},
        "producer": {"name": "^ExpectedProducer.*"},
        "creator": {"name": "^ExpectedCreator.*"},
        "file_size": {"algorithm": "Unknown"},
        "dates": {"created": {"state": "None"}, "modified": {"state": "None"}},
        "fonts": {"required_fonts": [], "optional_fonts": []},
    }

    expected = {
        "producer": {
            "name": "^ExpectedProducer.*",
            "actual": "Chrome PDF Printer",
            "valid": "FDR",
            "validation_message_code": "MSG_PRODUCER_BROWSER_PRINTED",
        },
        "creator": {
            "name": "^ExpectedCreator.*",
            "actual": "Safari PDF Creator",
            "valid": "FDR",
            "validation_message_code": "MSG_CREATOR_BROWSER_PRINTED",
        },
    }

    metadata = {
        "template": template_type,
        "producer": "Chrome PDF Printer",
        "creator": "Safari PDF Creator",
        "fonts": [],
        "creationDate": "",
        "modDate": "",
    }

    CompositeRuleEvaluatorFactory.create(template_type).evaluate(input_rule, metadata)

    assert_dict_contains(input_rule, expected)


def test_producer_and_creator_match_remains_unchanged():
    template_type = "Any Template"
    input_rule = {
        "template": {"name": template_type},
        "producer": {"name": "^ExpectedProducer.*"},
        "creator": {"name": "^ExpectedCreator.*"},
        "file_size": {"algorithm": "Unknown"},
        "dates": {"created": {"state": "None"}, "modified": {"state": "None"}},
        "fonts": {"required_fonts": [], "optional_fonts": []},
    }

    expected = {
        "producer": {
            "name": "^ExpectedProducer.*",
            "actual": "ExpectedProducer 1.0",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "creator": {
            "name": "^ExpectedCreator.*",
            "actual": "ExpectedCreator 2.0",
            "valid": "Pass",
            "validation_message_code": "MSG_CREATOR_MATCH",
        },
    }

    metadata = {
        "template": template_type,
        "producer": "ExpectedProducer 1.0",
        "creator": "ExpectedCreator 2.0",
        "fonts": [],
        "creationDate": "",
        "modDate": "",
    }

    CompositeRuleEvaluatorFactory.create(template_type).evaluate(input_rule, metadata)

    assert_dict_contains(input_rule, expected)


def test_producer_and_creator_matching_browser_printed_values_remain_pass():
    template_type = "Any Template"
    input_rule = {
        "template": {"name": template_type},
        "producer": {"name": "^Chrome PDF Printer$"},
        "creator": {"name": "^Safari PDF Creator$"},
        "file_size": {"algorithm": "Unknown"},
        "dates": {"created": {"state": "None"}, "modified": {"state": "None"}},
        "fonts": {"required_fonts": [], "optional_fonts": []},
    }

    expected = {
        "producer": {
            "name": "^Chrome PDF Printer$",
            "actual": "Chrome PDF Printer",
            "valid": "Pass",
            "validation_message_code": "MSG_PRODUCER_MATCH",
        },
        "creator": {
            "name": "^Safari PDF Creator$",
            "actual": "Safari PDF Creator",
            "valid": "Pass",
            "validation_message_code": "MSG_CREATOR_MATCH",
        },
    }

    metadata = {
        "template": template_type,
        "producer": "Chrome PDF Printer",
        "creator": "Safari PDF Creator",
        "fonts": [],
        "creationDate": "",
        "modDate": "",
    }

    CompositeRuleEvaluatorFactory.create(template_type).evaluate(input_rule, metadata)

    assert_dict_contains(input_rule, expected)
