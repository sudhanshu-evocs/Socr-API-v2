import fitz
import pytest

from docuverus.RuleEvaluators.FontRuleEvaluator import FontRuleEvaluator, normalize_font_name_for_match
from docuverus.RuleEvaluators.RuleSetFactory import RuleSetFactory
from docuverus.Utils.FileUtilities import FileUtilities
from docuverus.Utils.PDFUtilities import PDFUtilities
from test_suite.support.assertions import assert_dict_contains


def test_normalize_font_name_for_match_ignores_spaces_underscores_and_case():
    assert normalize_font_name_for_match("Connections Medium Bold") == "connectionsmediumbold"
    assert normalize_font_name_for_match("ConnectionsMediumBold") == "connectionsmediumbold"
    assert normalize_font_name_for_match("Connections_Medium_Bold") == "connectionsmediumbold"
    assert normalize_font_name_for_match("ABCDEF+Connections Medium Bold") == "connectionsmediumbold"


def test_connections_medium_bold_variant_matches_ruleset_font():
    evaluator = FontRuleEvaluator()
    expected_fonts = [{"name": "ConnectionsMediumBold", "type": "", "encoding": ""}]
    document_font = {"name": "Connections Medium Bold", "type": "Type0", "encoding": "Identity-H"}

    assert evaluator.is_document_font_expected(document_font, expected_fonts)


def retrieve_font_rules_by_name(template_name, rule_set_index=0):
    rules = RuleSetFactory(
        [
            "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
            "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
        ]
    ).get_template_rules(template_name)
    return {"fonts": rules[rule_set_index].get("fonts")} if rules else None


def retrieve_font_rule_count(template_name):
    rules = RuleSetFactory(
        [
            "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
            "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
        ]
    ).get_template_rules(template_name)
    return len(rules) if rules else 0


class SimpleFont:
    def __init__(self, name, font_type, encoding, multiplicity=1):
        self.name = name
        self.font_type = font_type
        self.encoding = encoding
        self.multiplicity = multiplicity


class SimpleOptionalFont(SimpleFont):
    def __init__(
        self,
        name,
        font_type,
        encoding,
        multiplicity=FontRuleEvaluator.MAX_FONT_MULTIPLICITY,
    ):
        super().__init__(name, font_type, encoding, multiplicity)


class DocumentFont(SimpleFont):
    def __init__(
        self,
        name,
        font_type,
        encoding,
        multiplicity=1,
        actual_multiplicity=0,
        valid="Fail",
        validation_message_code="",
    ):
        super().__init__(name, font_type, encoding, multiplicity)
        self.actual_multiplicity = actual_multiplicity
        self.valid = valid
        self.validation_message_code = validation_message_code


class DocumentFraudFont(DocumentFont):
    def __init__(
        self,
        name,
        font_type,
        encoding,
        multiplicity=0,
        actual_multiplicity=1,
        valid="Fail",
        validation_message_code="MSG_FRAUD_FONT_FOUND",
    ):
        super().__init__(
            name,
            font_type,
            encoding,
            multiplicity,
            actual_multiplicity,
            valid,
            validation_message_code,
        )


def create_input_rule(fonts, optional_fonts=None):
    if optional_fonts is None:
        optional_fonts = {}
    font_rule_json = {
        "fonts": {
            "required_fonts": [
                {
                    **{
                        "name": font.name,
                        "type": font.font_type,
                        "encoding": font.encoding,
                    },
                    **({"multiplicity": font.multiplicity} if font.multiplicity != 1 else {}),
                }
                for font in fonts
            ]
        }
    }
    if optional_fonts:
        font_rule_json["fonts"]["optional_fonts"] = [
            {
                **{
                    "name": font.name,
                    "type": font.font_type,
                    "encoding": font.encoding,
                },
                **({"multiplicity": font.multiplicity} if font.multiplicity != FontRuleEvaluator.MAX_FONT_MULTIPLICITY else {}),
            }
            for font in optional_fonts
        ]
    return font_rule_json


def create_expected_document_fonts(
    required_fonts,
    additional_fonts=[],
    optional_fonts=[],
    final_valid="foo",
    final_validation_message_code="foo",
):
    required_fonts_dict = [
        {
            "name": font.name,
            "type": font.font_type,
            "encoding": font.encoding,
            "multiplicity": font.multiplicity,
            "actual_multiplicity": font.actual_multiplicity,
            "valid": font.valid,
            "validation_message_code": font.validation_message_code,
        }
        for font in required_fonts
    ]

    additional_fonts_dict = [
        {
            "name": font.name,
            "type": font.font_type,
            "encoding": font.encoding,
            "multiplicity": font.multiplicity,
            "actual_multiplicity": font.actual_multiplicity,
            "valid": font.valid,
            "validation_message_code": font.validation_message_code,
        }
        for font in additional_fonts
    ]

    optional_fonts_dict = [
        {
            "name": font.name,
            "type": font.font_type,
            "encoding": font.encoding,
            "multiplicity": font.multiplicity,
            "actual_multiplicity": font.actual_multiplicity,
            "valid": font.valid,
            "validation_message_code": font.validation_message_code,
        }
        for font in optional_fonts
    ]
    return {
        "fonts": {
            "required_fonts": required_fonts_dict,
            "additional_fonts": additional_fonts_dict,
            "optional_fonts": optional_fonts_dict,
            "valid": final_valid,
            "validation_message_code": final_validation_message_code,
        }
    }


def test_valid_fonts_for_valid_bank_statement_with_no_optional_fonts():
    # arrange
    input_rule = retrieve_font_rules_by_name("pnc bank")
    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "MicrosoftSansSerif",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_PNC_Bank_Statement_with_single_font.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_validate_if_multiplicity_is_not_present_by_default_its_1():
    # arrange
    input_rule = create_input_rule(
        [
            SimpleFont("MicrosoftSansSerif", "TrueType", "WinAnsiEncoding"),
            SimpleFont("Times-Roman", "Type1", "WinAnsiEncoding"),
        ]
    )
    # # act
    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "TrueType", "MicrosoftSansSerif", "WinAnsiEncoding"))]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule["fonts"]["required_fonts"][0]["multiplicity"] == 1


def test_when_required_fonts_is_not_known():
    input_rule = {
        "fonts": {
            "required_fonts": [],
            "optional_fonts": [],
        }
    }
    expected_result = create_expected_document_fonts(
        [],
        [
            DocumentFont("Arial", "Type1", "WinAnsiEncoding", 0, 1, "FDR", "MSG_FONT_NOT_APPLICABLE"),
            DocumentFont("Times-Roman", "TrueType", "WinAnsiEncoding", 0, 1, "FDR", "MSG_FONT_NOT_APPLICABLE"),
        ],
        [],
        "FDR",
        "MSG_FONT_RULE_NOT_APPLICABLE",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Type1", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((3, "TrueType", "Times-Roman", "WinAnsiEncoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_when_font_rule_is_missing():
    input_rule = {}
    expected_result = create_expected_document_fonts(
        [],
        [
            DocumentFont("Arial", "Type1", "WinAnsiEncoding", 0, 1, "FDR", "MSG_FONT_NOT_APPLICABLE"),
            DocumentFont("Times-Roman", "TrueType", "WinAnsiEncoding", 0, 1, "FDR", "MSG_FONT_NOT_APPLICABLE"),
        ],
        [],
        "FDR",
        "MSG_FONT_RULE_NOT_APPLICABLE",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Type1", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((3, "TrueType", "Times-Roman", "WinAnsiEncoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_for_when_only_optional_fonts_are_present():
    # arrange
    input_rule = create_input_rule([], [SimpleOptionalFont("Arial", "Type1", "WinAnsiEncoding")])

    expected_result = create_expected_document_fonts(
        [],
        [
            DocumentFont("Times-Roman", "TrueType", "WinAnsiEncoding", 0, 1, "Fail", "MSG_FRAUD_FONT_FOUND"),
        ],
        [DocumentFont("Arial", "Type1", "WinAnsiEncoding", 9999, 1, "Pass", "MSG_OPTIONAL_FONT_MATCHED")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Type1", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((3, "TrueType", "Times-Roman", "WinAnsiEncoding")),
    ]

    FontRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule == expected_result


def test_valid_fonts_multiplicity_for_valid_PNC_bank_statement():
    # arrange
    input_rule = retrieve_font_rules_by_name("pnc bank")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "MicrosoftSansSerif",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_PNC_Bank_for_font_multiplicity.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_peoples_united_bank_statement_with_no_optional_fonts():
    # arrange
    input_rule = retrieve_font_rules_by_name("People's United")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Courier",
                "",
                "",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_People_United_Bank_Statement_with_single_font.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_TD_Bank_with_multiple_fonts():
    # arrange
    input_rule = create_input_rule(
        [
            SimpleFont("Arial", "TrueType", "WinAnsiEncoding"),
            SimpleFont("Times-Roman", "Type1", "WinAnsiEncoding"),
            SimpleFont("Arial Bold", "TrueType", "WinAnsiEncoding"),
        ]
    )

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "Times-Roman",
                "Type1",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "Arial Bold",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
        ],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_TD_Bank_Statement_opentext.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)

    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_invalid_bank_with_1st_invalid_font_and_others_valid_font():
    # arrange
    input_rule = create_input_rule([SimpleFont("Arial", "Type1", "WinAnsiEncoding")])

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "Type1",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [
            DocumentFont(
                "Fraud Font",
                "Fraud Font Type",
                "Fraud Encoding",
                0,
                1,
                "Fail",
                "MSG_FRAUD_FONT_FOUND",
            )
        ],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Type1", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((3, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_invalid_bank_with_multiple_invalid_fonts():
    # arrange
    input_rule = create_input_rule(
        [
            SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding"),
            SimpleFont("Courier", "Type1", "AnsiEncoding"),
        ]
    )

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "Courier",
                "Type1",
                "AnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
        ],
        [
            DocumentFont(
                "Fraud Font",
                "Fraud Font Type",
                "Fraud Encoding",
                0,
                1,
                "Fail",
                "MSG_FRAUD_FONT_FOUND",
            ),
            DocumentFont(
                "Fraud Font 2",
                "Fraud Font Type 2",
                "Fraud Encoding 2",
                0,
                1,
                "Fail",
                "MSG_FRAUD_FONT_FOUND",
            ),
        ],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Type1", "Courier", "AnsiEncoding")),
        font_dict_for_tuple((2, "TrueType", "Times-Roman", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((2, "Fraud Font Type 2", "Fraud Font 2", "Fraud Encoding 2")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_invalid_bank_when_type_is_different():
    # arrange
    input_rule = create_input_rule([SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")])
    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            )
        ],
        [
            DocumentFont(
                "Times-Roman",
                "Different Type",
                "WinAnsiEncoding",
                0,
                1,
                "Fail",
                "MSG_FRAUD_FONT_FOUND",
            )
        ],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "Different Type", "Times-Roman", "WinAnsiEncoding"))]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_invalid_bank_when_encoding_is_different():
    # arrange
    input_rule = create_input_rule([SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")])

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            )
        ],
        [DocumentFraudFont("Times-Roman", "TrueType", "Different Encoding")],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "TrueType", "Times-Roman", "Different Encoding"))]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_when_required_font_is_not_present():
    # arrange
    input_rule = create_input_rule([SimpleFont("Arial", "TrueType", "WinAnsiEncoding")])

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "TrueType",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            )
        ],
        [DocumentFraudFont("Fraud Font", "Fraud Type", "Fraud Encoding")],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    # act
    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "Fraud Type", "Fraud Font", "Fraud Encoding"))]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_multiple_fonts_when_one_required_fonts_is_not_present():
    # arrange
    input_rule = create_input_rule(
        [
            SimpleFont("Arial", "TrueType", "WinAnsiEncoding"),
            SimpleFont("Courier", "Type1", "WinAnsiEncoding"),
        ]
    )

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "Courier",
                "Type1",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            ),
        ],
        [DocumentFraudFont("Fraud Font", "Fraud Type", "Fraud Encoding")],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Fraud Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_when_multiple_fonts_are_there_and_one_required_fonts_is_not_present():
    # arrange
    input_rule = create_input_rule(
        [
            SimpleFont("Arial", "TrueType", "WinAnsiEncoding"),
            SimpleFont("Courier", "Type1", "WinAnsiEncoding"),
            SimpleFont("Arial-Bold", "Type2", "AnsiEncoding"),
        ]
    )

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "Courier",
                "Type1",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            ),
            DocumentFont(
                "Arial-Bold",
                "Type2",
                "AnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
        ],
        [DocumentFraudFont("Fraud Font", "Fraud Type", "Fraud Encoding")],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Fraud Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Type2", "Arial-Bold", "AnsiEncoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_multiple_fonts_when_all_fonts_are_present_except_one_font():
    # arrange
    input_rule = create_input_rule(
        [
            SimpleFont("Arial", "TrueType", "WinAnsiEncoding"),
            SimpleFont("Courier", "Type1", "WinAnsiEncoding"),
            SimpleFont("Arial-Bold", "Type2", "AnsiEncoding"),
        ]
    )

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "Courier",
                "Type1",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            ),
            DocumentFont(
                "Arial-Bold",
                "Type2",
                "AnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
        ],
        [DocumentFraudFont("Fraud Font", "Fraud Type", "Fraud Encoding")],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Fraud Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Type2", "Arial-Bold", "AnsiEncoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_multiple_fonts_to_detect_invalid_fonts_present():
    # arrange
    input_rule = create_input_rule(
        [
            SimpleFont("Arial", "TrueType", "WinAnsiEncoding"),
            SimpleFont("Courier", "Type1", "WinAnsiEncoding"),
            SimpleFont("Arial-Bold", "Type2", "AnsiEncoding"),
        ]
    )

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "TrueType",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            ),
            DocumentFont(
                "Courier",
                "Type1",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            ),
            DocumentFont(
                "Arial-Bold",
                "Type2",
                "AnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
        ],
        [
            DocumentFraudFont("Arial", "TrueType", "FakeEncoding"),
            DocumentFraudFont("Courier", "FakeType", "FakeEncoding"),
            DocumentFraudFont("Fraud Font", "Fraud Type", "Fraud Encoding"),
        ],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Fraud Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((2, "TrueType", "Arial", "FakeEncoding")),
        font_dict_for_tuple((2, "FakeType", "Courier", "FakeEncoding")),
        font_dict_for_tuple((2, "Type2", "Arial-Bold", "AnsiEncoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_font_when_font_name_is_different_with_same_type_and_encoding():
    # arrange
    input_rule = create_input_rule([SimpleFont("Arial", "TrueType", "WinAnsiEncoding")])

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "TrueType",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            )
        ],
        [DocumentFraudFont("Courier", "TrueType", "WinAnsiEncoding")],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "TrueType", "Courier", "WinAnsiEncoding"))]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_for_font_with_none_font_type():
    # arrange
    input_rule = create_input_rule([SimpleFont("Arial", "", "WinAnsiEncoding")])

    expected_result = create_expected_document_fonts(
        [DocumentFont("Arial", "", "WinAnsiEncoding", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED")],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )

    # act
    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "", "Arial", "WinAnsiEncoding"))]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_for_font_with_none_font_encoding():
    # arrange
    input_rule = create_input_rule([SimpleFont("Arial", "Type1", "")])

    expected_result = create_expected_document_fonts(
        [DocumentFont("Arial", "Type1", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED")],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "Type1", "Arial", ""))]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_multiple_fonts_with_font_with_none_font_encoding():
    # arrange
    input_rule = create_input_rule(
        [
            SimpleFont("Arial", "Type1", "WinAnsiEncoding"),
            SimpleFont("Arial-Bold", "Type1", ""),
        ]
    )

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "Type1",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont("Arial-Bold", "Type1", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Type1", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Type1", "Arial-Bold", "")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_required_font_with_blank_type_and_encoding_matches_name_any_variant():
    input_rule = create_input_rule([SimpleFont("Arial", "", "")])

    expected_result = create_expected_document_fonts(
        [DocumentFont("Arial", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED")],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )

    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding"))]

    FontRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule == expected_result


def test_optional_font_with_blank_type_and_encoding_matches_name_any_variant():
    input_rule = create_input_rule([], [SimpleOptionalFont("Arial", "", "", 1)])

    expected_result = create_expected_document_fonts(
        [],
        [],
        [DocumentFont("Arial", "", "", 1, 1, "Pass", "MSG_OPTIONAL_FONT_MATCHED")],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )

    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding"))]

    FontRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule == expected_result


def test_blank_type_and_encoding_uses_best_single_variant_for_multiplicity():
    input_rule = create_input_rule([SimpleFont("Arial", "", "", 3)])

    expected_result = create_expected_document_fonts(
        [DocumentFont("Arial", "", "", 3, 2, "Pass", "MSG_REQUIRED_FONT_MATCHED")],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((1, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((3, "Type1", "Arial", "MacRomanEncoding")),
    ]

    FontRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule == expected_result


def test_valid_duplicate_fonts_when_xref_number_is_different():
    # arrange
    input_rule = create_input_rule([SimpleFont("Arial", "Type1", "WinAnsiEncoding", 2)])

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "Type1",
                "WinAnsiEncoding",
                2,
                2,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Type1", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((3, "Type1", "Arial", "WinAnsiEncoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_multiple_duplicate_fonts_when_xref_number_is_different():
    # arrange
    input_rule = create_input_rule(
        [
            SimpleFont("Arial", "Type1", "WinAnsiEncoding"),
            SimpleFont("Courier", "TrueType", "AnsiEncoding"),
        ]
    )

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial",
                "Type1",
                "WinAnsiEncoding",
                1,
                2,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            ),
            DocumentFont(
                "Courier",
                "TrueType",
                "AnsiEncoding",
                1,
                3,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            ),
        ],
        [],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "Type1", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((10, "Type1", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((13, "TrueType", "Courier", "AnsiEncoding")),
        font_dict_for_tuple((16, "TrueType", "Courier", "AnsiEncoding")),
        font_dict_for_tuple((18, "TrueType", "Courier", "AnsiEncoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_paycor_paystub():
    input_rule = retrieve_font_rules_by_name("paycor")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Helvetica", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("MICR", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [DocumentFont("ArialMT", "", "", 9999, 1, "Pass", "MSG_OPTIONAL_FONT_MATCHED")],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_Paycor_Paystub_for_fonts.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_paycom_paystub_with_producer_as_pdfium():
    input_rule = retrieve_font_rules_by_name("paycom")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Helvetica", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Times-Roman", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [DocumentFont("Times-Italic", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_Paycom_Paystub_with_pdfium_pro.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_justworks_paystub():
    input_rule = retrieve_font_rules_by_name("justworks")
    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Oately-Bold", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Oately-Regular", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_Justworks_Paystub_for_fonts.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_accenture_paystub():
    input_rule = retrieve_font_rules_by_name("accenture")
    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Helvetica", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [
            DocumentFraudFont("Roboto-Bold", "Type0", "Identity-H"),
            DocumentFraudFont("Roboto-Regular", "Type0", "Identity-H"),
        ],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Invalid_accenture_paystub.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_paycor_image_pdf_paystub():
    input_rule = retrieve_font_rules_by_name("paycor")
    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Helvetica", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("MICR", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [],
        [DocumentFont("ArialMT", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Invalid_paycor_image_pdf.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_invalid_paycor_paystub():
    input_rule = retrieve_font_rules_by_name("paycor")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Helvetica", "", "", 1, 5, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 2, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("MICR", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [
            DocumentFraudFont("Arial", "Type0", "Identity-H"),
            DocumentFraudFont("Arial-BoldMT", "Type0", "Identity-H", 0, 6, "Fail"),
            DocumentFraudFont("ZapfDingbats", "Type1", "", 0, 1),
        ],
        [DocumentFont("ArialMT", "", "", 9999, 6, "Pass", "MSG_OPTIONAL_FONT_MATCHED")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    file_path = "../test_documents/Invalid_Paycor_Paystub.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_paycor_paystub():
    input_rule = retrieve_font_rules_by_name("paycor")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Helvetica", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("MICR", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [
            DocumentFraudFont(".SFNS-Regular_wdth_opsz110000_GRAD_wght", "TrueType", ""),
            DocumentFraudFont(
                ".SFNS-Regular_wdth_opsz110000_GRAD_wght",
                "TrueType",
                "MacRomanEncoding",
            ),
            DocumentFraudFont("font000000002bdaa251", "TrueType", "MacRomanEncoding"),
            DocumentFraudFont("font000000002bdaa252", "TrueType", "MacRomanEncoding", 0, 2),
        ],
        [DocumentFont("ArialMT", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    file_path = "../test_documents/Invalid_paycor.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_validate_specified_optional_font_but_not_present():
    input_rule = create_input_rule(
        [SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")],
        [SimpleOptionalFont("Courier", "Type1", "AnsiEncoding")],
    )
    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [DocumentFraudFont("Fraud Font", "Fraud Font Type", "Fraud Encoding")],
        [
            DocumentFont(
                "Courier",
                "Type1",
                "AnsiEncoding",
                FontRuleEvaluator.MAX_FONT_MULTIPLICITY,
                0,
                "Pass",
                "MSG_OPTIONAL_FONT_NOT_FOUND",
            )
        ],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    # act
    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "TrueType", "Times-Roman", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)

    # assert
    assert input_rule == expected_result


def test_validate_specified_optional_font_is_present():
    input_rule = create_input_rule(
        [SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")],
        [SimpleFont("Optional Font", "Optional Font Type", "Optional Font Encoding")],
    )

    # act
    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [DocumentFraudFont("Fraud Font", "Fraud Font Type", "Fraud Encoding")],
        [
            DocumentFont(
                "Optional Font",
                "Optional Font Type",
                "Optional Font Encoding",
                1,
                1,
                "Pass",
                "MSG_OPTIONAL_FONT_MATCHED",
            )
        ],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "TrueType", "Times-Roman", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((2, "Optional Font Type", "Optional Font", "Optional Font Encoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)

    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_charles_schwab_Bank_with_more_fonts_on_2nd_page_than_1st_page():
    input_rule = retrieve_font_rules_by_name("charles schwab")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Helvetica",
                "Type1",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "Helvetica-Bold",
                "Type1",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "Helvetica-Oblique",
                "Type1",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
        ],
        [],
        [
            DocumentFont("Symbol", "Type1", "", 1, 1, "Pass", "MSG_OPTIONAL_FONT_MATCHED"),
            DocumentFont("Times-Roman", "Type1", "WinAnsiEncoding", 1, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
        ],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_Charles_Schwab_Bank_with_more_fonts_on_2nd_page.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_paycom_paystub():
    input_rule = retrieve_font_rules_by_name("paycom")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Helvetica", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Times-Roman", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [
            DocumentFont("Times-Italic", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
        ],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_paycom_paystub_for_fonts.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_chase_bank_statement_with_prefix_before_font_names():
    input_rule = retrieve_font_rules_by_name("chase bank", rule_set_index=2)

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Helvetica", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Times-Roman", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("F20 (O", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [
            DocumentFraudFont("Arial", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Arial Bold", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Arial Italic", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Symbol MT", "TrueType", ""),
            DocumentFraudFont("Times New Roman", "TrueType", "WinAnsiEncoding"),
        ],
        [
            DocumentFont("F1", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F2", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F3", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F4", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F5", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F6", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F7", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F8", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F9", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F10", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F11", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F12", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F13", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F14", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F15", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F16", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F17", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F18", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("F19", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("Helvetica-Bold", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("Symbol", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
        ],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Valid_Chase_Bank_with_prefix_in_fonts.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_bank_of_america_bank_statement():
    input_rule = retrieve_font_rules_by_name("bank of america", rule_set_index=1)

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Connections", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Connections_Medium", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("ConnectionsBold", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("ConnectionsIta", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("CourierSWM", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("HigherStandards", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("ITC_Franklin_Gothic_Book", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [DocumentFont("Swiss721SWM", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_fonts_with_suffix_for_valid_bank_of_america_bank_statement():
    input_rule = retrieve_font_rules_by_name("bank of america", rule_set_index=1)
    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Connections", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Connections_Medium", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("ConnectionsBold", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("ConnectionsIta", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("CourierSWM", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("HigherStandards", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("ITC_Franklin_Gothic_Book", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [DocumentFont("Swiss721SWM", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Valid_boa_fonts_with_suffix.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_fonts_with_suffix_for_valid_citizens_bank():
    input_rule = retrieve_font_rules_by_name("citizens bank")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("C00", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C01", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C02", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C03", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C04", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C05", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C07", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C08", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C09", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C010", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C011", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C012", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C013", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C014", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C015", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [
            DocumentFraudFont("C00_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C010_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C011_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C012_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C013_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C014_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C015_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C016_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C017_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C018_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C01_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C02_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C03_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C04_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C05_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C06_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C07_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C08_T100FULE_0", "Type3", ""),
            DocumentFraudFont("C09_T100FULE_0", "Type3", ""),
        ],
        [
            DocumentFont("C06", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("C016", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("C017", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("C018", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("C019", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
        ],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    file_path = "../test_documents/Valid_Citizens_Bank_Statement.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_fonts_with_suffix_for_invalid_navy_fcu_bank():
    input_rule = retrieve_font_rules_by_name("navy fcu", rule_set_index=2)
    expected_result = create_expected_document_fonts(
        [
            DocumentFont("C0A05570", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0D0GT10", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0D0GT12", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0D0GT15", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H20070", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H20090", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H40070", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H40090", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H400A0", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H400B0", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0L00G15", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0XQUC23", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("spaceFont", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [
            DocumentFraudFont("Arial Narrow", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Arial Narrow,Bold", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Arial,Bold", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Book Antiqua,Bold", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Courier New,Bold", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Times New Roman", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Times New Roman,Bold", "Type0", "Identity-H"),
            DocumentFraudFont("Times New Roman,Bold", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("Verdana,Bold", "TrueType", "WinAnsiEncoding"),
        ],
        [DocumentFont("C0H40080", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    file_path = "../test_documents/Invalid_navy_fcu_bank_statement.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_when_required_font_is_not_present():
    input_rule = create_input_rule([SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")])

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                0,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            )
        ],
        [DocumentFraudFont("Not Times-Roman", "Not TrueType", "Not WinAnsiEncoding")],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    # act
    metadata = {}
    metadata["fonts"] = [font_dict_for_tuple((2, "Not TrueType", "Not Times-Roman", "Not WinAnsiEncoding"))]
    FontRuleEvaluator().evaluate(input_rule, metadata)

    # assert
    assert input_rule == expected_result


def test_extract_fonts_creates_list_of_fonts_with_multiplicities():
    fonts_list = FontRuleEvaluator().extract_fonts(
        PDFUtilities.extract_xref_fonts(fitz.open("../test_documents/Valid_Charles_Schwab_Bank_with_more_fonts_on_2nd_page.pdf"))
    )

    assert fonts_list[0][3] == 1
    assert fonts_list[1][3] == 1
    assert fonts_list[2][3] == 1
    assert fonts_list[3][3] == 1


def test_validate_multiplicity_of_optional_font():
    input_rule = create_input_rule(
        [SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")],
        [SimpleOptionalFont("Optional Font", "Optional Font Type", "Optional Font Encoding")],
    )

    # act
    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [DocumentFraudFont("Fraud Font", "Fraud Font Type", "Fraud Encoding")],
        [
            DocumentFont(
                "Optional Font",
                "Optional Font Type",
                "Optional Font Encoding",
                9999,
                1,
                "Pass",
                "MSG_OPTIONAL_FONT_MATCHED",
            )
        ],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((1, "TrueType", "Times-Roman", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((3, "Optional Font Type", "Optional Font", "Optional Font Encoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)

    # assert
    assert input_rule == expected_result


def test_valid_multiplicity_of_duplicate_optional_font():
    input_rule = create_input_rule(
        [SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")],
        [SimpleOptionalFont("Optional Font", "Optional Font Type", "Optional Font Encoding")],
    )

    # act
    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [DocumentFraudFont("Fraud Font", "Fraud Font Type", "Fraud Encoding")],
        [
            DocumentFont(
                "Optional Font",
                "Optional Font Type",
                "Optional Font Encoding",
                9999,
                2,
                "Pass",
                "MSG_OPTIONAL_FONT_MATCHED",
            )
        ],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((1, "TrueType", "Times-Roman", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((3, "Optional Font Type", "Optional Font", "Optional Font Encoding")),
        font_dict_for_tuple((4, "Optional Font Type", "Optional Font", "Optional Font Encoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)

    # assert
    assert input_rule == expected_result


def test_valid_multiplicity_when_more_than_one_optional_font_is_present():
    input_rule = create_input_rule(
        [SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")],
        [
            SimpleOptionalFont("Optional Font", "Optional Font Type", "Optional Font Encoding"),
            SimpleOptionalFont("Optional Font 2", "Optional Font Type 2", "Optional Font Encoding 2"),
        ],
    )

    # act
    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [DocumentFraudFont("Fraud Font", "Fraud Font Type", "Fraud Encoding")],
        [
            DocumentFont(
                "Optional Font",
                "Optional Font Type",
                "Optional Font Encoding",
                9999,
                1,
                "Pass",
                "MSG_OPTIONAL_FONT_MATCHED",
            ),
            DocumentFont(
                "Optional Font 2",
                "Optional Font Type 2",
                "Optional Font Encoding 2",
                9999,
                1,
                "Pass",
                "MSG_OPTIONAL_FONT_MATCHED",
            ),
        ],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "TrueType", "Times-Roman", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((2, "Optional Font Type", "Optional Font", "Optional Font Encoding")),
        font_dict_for_tuple((2, "Optional Font Type 2", "Optional Font 2", "Optional Font Encoding 2")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_multiplicity_for_fraud_fonts_present():
    input_rule = create_input_rule([SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")])

    # act
    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [
            DocumentFraudFont(
                "Fraud Font",
                "Fraud Font Type",
                "Fraud Encoding",
                0,
                1,
                "Fail",
                "MSG_FRAUD_FONT_FOUND",
            )
        ],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((2, "TrueType", "Times-Roman", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_multiplicity_for_same_fraud_font_present_on_different_pages():
    input_rule = create_input_rule([SimpleFont("Times-Roman", "TrueType", "WinAnsiEncoding")])

    # act
    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Times-Roman",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            )
        ],
        [
            DocumentFraudFont(
                "Fraud Font",
                "Fraud Font Type",
                "Fraud Encoding",
                0,
                3,
                "Fail",
                "MSG_FRAUD_FONT_FOUND",
            )
        ],
        [],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((4, "TrueType", "Times-Roman", "WinAnsiEncoding")),
        font_dict_for_tuple((21, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((13, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
        font_dict_for_tuple((26, "Fraud Font Type", "Fraud Font", "Fraud Encoding")),
    ]
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_rippling_paystub():
    input_rule = retrieve_font_rules_by_name("rippling", 1)

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("BentonSans", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("DejaVu-Sans", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("DejaVu-Sans-Bold", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Nimbus-Sans", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Nimbus-Sans-Bold", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [
            DocumentFraudFont("BentonSans-Book", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("DejaVuSans", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("DejaVuSans-Bold", "TrueType", "WinAnsiEncoding"),
            DocumentFraudFont("NimbusSans-Bold", "Type1", "WinAnsiEncoding"),
            DocumentFraudFont("NimbusSans-Regular", "Type1", "WinAnsiEncoding"),
        ],
        [DocumentFont("Nimbus-Bold", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Valid_rippling_paystub_for_fonts_check.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_chime_bank_statement():
    input_rule = retrieve_font_rules_by_name("chime bank")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "SourceSansPro-Bold",
                "Type0",
                "Identity-H",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "SourceSansPro-Light",
                "Type0",
                "Identity-H",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "SourceSansPro-Regular",
                "Type0",
                "Identity-H",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
        ],
        [],
        [
            DocumentFont(
                "DejaVuSans",
                "Type0",
                "Identity-H",
                FontRuleEvaluator.MAX_FONT_MULTIPLICITY,
                1,
                "Pass",
                "MSG_OPTIONAL_FONT_MATCHED",
            ),
            DocumentFont(
                "NimbusSanL-Regu",
                "Type0",
                "Identity-H",
                FontRuleEvaluator.MAX_FONT_MULTIPLICITY,
                0,
                "Pass",
                "MSG_OPTIONAL_FONT_NOT_FOUND",
            ),
        ],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_Chime_bank_statement.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_invalid_paychex_paystub():
    input_rule = retrieve_font_rules_by_name("paychex")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Arial-Black", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Helvetica", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Helvetica-Oblique", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [
            DocumentFraudFont("NimbusSans-Bold", "Type0", "Identity-H", 0, 1, "Fail", "MSG_FRAUD_FONT_FOUND"),
            DocumentFraudFont("NimbusSans-Regular", "Type0", "Identity-H", 0, 1, "Fail", "MSG_FRAUD_FONT_FOUND"),
        ],
        [DocumentFont("Arial-Black,Bold", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Invalid_paychex_paystub.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_TD_Bank_Statement():
    # arrange
    input_rule = retrieve_font_rules_by_name("td bank", rule_set_index=0)

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Arial", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Arial Bold", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Times-Roman", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [
            DocumentFont("Helvetica", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("Helvetica-Bold", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
        ],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_TD_Bank_Statement.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)

    # assert
    assert input_rule == expected_result


def test_evaluate_fonts_when_retrieved_from_xref():
    file_path = "../test_documents/Invalid_chime_bank_statment.pdf"
    metadata = {"fonts": PDFUtilities.extract_xref_fonts(fitz.open(file_path))}

    input_rule = {"fonts": {}}
    FontRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule


def test_fonts_with_suffix_for_valid_navy_fcu_bank():
    # fonts always found with suffix
    input_rule = retrieve_font_rules_by_name("navy fcu", rule_set_index=2)
    expected_result = create_expected_document_fonts(
        [
            DocumentFont("C0A05570", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0D0GT10", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0D0GT12", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0D0GT15", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H20070", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H20090", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H40070", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H40090", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H400A0", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0H400B0", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0L00G15", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("C0XQUC23", "", "", 1, 0, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("spaceFont", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [
            DocumentFraudFont("C0A05570_T1DCDCFS_0", "Type3", ""),
            DocumentFraudFont("C0D0GT12_T1D0BASE_0", "Type3", ""),
            DocumentFraudFont("C0D0GT24_T1D0BASE_0", "Type3", ""),
            DocumentFraudFont("C0H20000_T1V10500_0", "Type3", "", 0, 3),
            DocumentFraudFont("C0H20060_T1V10500_0", "Type3", "", 0, 2),
            DocumentFraudFont("C0H20070_T1V10500_0", "Type3", "", 0, 3),
            DocumentFraudFont("C0H20080_T1V10500_0", "Type3", "", 0, 2),
            DocumentFraudFont("C0H20090_T1V10500_0", "Type3", "", 0, 2),
            DocumentFraudFont("C0H30080_T1V10500_0", "Type3", ""),
            DocumentFraudFont("C0H40000_T1V10500_0", "Type3", "", 0, 3),
            DocumentFraudFont("C0H40060_T1V10500_0", "Type3", ""),
            DocumentFraudFont("C0H40070_T1V10500_0", "Type3", "", 0, 3),
            DocumentFraudFont("C0H40080_T1V10500_0", "Type3", "", 0, 2),
            DocumentFraudFont("C0H40090_T1V10500_0", "Type3", "", 0, 3),
            DocumentFraudFont("C0H400B0_T1V10500_0", "Type3", ""),
            DocumentFraudFont("C0L00AON_T1L0OCR1_0", "Type3", ""),
        ],
        [DocumentFont("C0H40080", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Valid_Navy_FCU_Bank_fonts_with_suffix.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_invalid_truist_Bank_Statement():
    # arrange
    input_rule = retrieve_font_rules_by_name("truist")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Helvetica", "", "", 1, 23, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 5, "Fail", "MSG_REQUIRED_FONT_NOT_MATCHED"),
        ],
        [DocumentFont("ZapfDingbats", "Type1", "", 0, 1, "Fail", "MSG_FRAUD_FONT_FOUND")],
        [
            DocumentFont("Helvetica-Oblique", "", "", 9999, 1, "Pass", "MSG_OPTIONAL_FONT_MATCHED"),
        ],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Invalid_truist_bank_statement.pdf"

    # act
    metadata = {"fonts": PDFUtilities.extract_xref_fonts(fitz.open(file_path))}
    FontRuleEvaluator().evaluate(input_rule, metadata)

    # assert
    assert input_rule == expected_result


def test_invalid_fonts_for_invalid_chime_bank_statement():
    input_rule = retrieve_font_rules_by_name("chime bank")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "SourceSansPro-Bold",
                "Type0",
                "Identity-H",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "SourceSansPro-Light",
                "Type0",
                "Identity-H",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "SourceSansPro-Regular",
                "Type0",
                "Identity-H",
                1,
                6,
                "Fail",
                "MSG_REQUIRED_FONT_NOT_MATCHED",
            ),
        ],
        [
            DocumentFraudFont("Helvetica", "Type1", "", 0, 1, "Fail", "MSG_FRAUD_FONT_FOUND"),
            DocumentFraudFont(
                "SourceSansPro-Regular",
                "CIDFontType0",
                "",
                0,
                5,
                "Fail",
                "MSG_FRAUD_FONT_FOUND",
            ),
            DocumentFraudFont("ZapfDingbats", "Type1", "", 0, 1, "Fail", "MSG_FRAUD_FONT_FOUND"),
        ],
        [
            DocumentFont(
                "DejaVuSans",
                "Type0",
                "Identity-H",
                FontRuleEvaluator.MAX_FONT_MULTIPLICITY,
                1,
                "Pass",
                "MSG_OPTIONAL_FONT_MATCHED",
            ),
            DocumentFont(
                "NimbusSanL-Regu",
                "Type0",
                "Identity-H",
                FontRuleEvaluator.MAX_FONT_MULTIPLICITY,
                0,
                "Pass",
                "MSG_OPTIONAL_FONT_NOT_FOUND",
            ),
        ],
        "Fail",
        "MSG_FONT_VALIDATION_INVALID",
    )
    file_path = "../test_documents/Invalid_chime_bank_statment.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_paychex_paystub():
    input_rule = retrieve_font_rules_by_name("paychex")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Arial-Black", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica-Oblique", "", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [DocumentFont("Arial-Black,Bold", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_single-paystub_paychex_paystub.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_valid_fonts_for_valid_multipage_paychex_paystub():
    input_rule = retrieve_font_rules_by_name("paychex")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont("Arial-Black", "", "", 4, 4, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica", "", "", 4, 4, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica-Bold", "", "", 4, 4, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica-Oblique", "", "", 4, 4, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [DocumentFont("Arial-Black,Bold", "", "", 9999, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND")],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_multi-paystub_paychex_paystub.pdf"
    # act
    metadata = {}
    metadata["paystub_count"] = PDFUtilities.retrieve_paystub_count_by_pdf(fitz.open(file_path))
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_ally_bank_valid_bank_statement():
    input_rule = retrieve_font_rules_by_name("ally")

    expected_result = create_expected_document_fonts(
        [
            DocumentFont(
                "Arial-BoldMT",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont(
                "ArialMT",
                "TrueType",
                "WinAnsiEncoding",
                1,
                1,
                "Pass",
                "MSG_REQUIRED_FONT_MATCHED",
            ),
            DocumentFont("Helvetica", "Type1", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Helvetica-Bold", "Type1", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
            DocumentFont("Times-Roman", "Type1", "", 1, 1, "Pass", "MSG_REQUIRED_FONT_MATCHED"),
        ],
        [],
        [
            DocumentFont("SymbolMT", "Type0", "Identity-H", 1, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("Times-RomanPSMT", "TrueType", "WinAnsiEncoding", 1, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
            DocumentFont("TimesNewRomanPSMT", "TrueType", "WinAnsiEncoding", 1, 0, "Pass", "MSG_OPTIONAL_FONT_NOT_FOUND"),
        ],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )
    file_path = "../test_documents/Valid_Ally_Bank_Statement.pdf"
    # act
    metadata = {}
    metadata["fonts"] = PDFUtilities.extract_xref_fonts(fitz.open(file_path))
    metadata["paystub_count"] = PDFUtilities.retrieve_paystub_count(file_path)
    FontRuleEvaluator().evaluate(input_rule, metadata)
    # assert
    assert input_rule == expected_result


def test_evaluate_with_single_paystub_count_and_multplicity_greater_than_1():
    input_rule = create_input_rule([SimpleFont("Arial", "TrueType", "WinAnsiEncoding", 2)])

    expected_result = create_expected_document_fonts(
        [DocumentFont("Arial", "TrueType", "WinAnsiEncoding", 2, 2, "Pass", "MSG_REQUIRED_FONT_MATCHED")],
        [],
        [],
        "Pass",
        "MSG_FONT_VALIDATION_VALID",
    )

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((1, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding")),
    ]
    metadata["paystub_count"] = 1
    FontRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule == expected_result


def test_evaluate_handles_paystub_count_if_missing():
    input_rule = {}
    FontRuleEvaluator().evaluate(input_rule, {"fonts": [], "paystub_count": None})

    assert input_rule["fonts"] is not None


def test_evaluate_puts_correct_message_code_on_optional_fonts():
    input_rule = create_input_rule([], [SimpleOptionalFont("Arial", "TrueType", "WinAnsiEncoding", 1)])

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((1, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((3, "type", "font", "encoding")),
    ]

    FontRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule["fonts"]["optional_fonts"][0]["validation_message_code"] == "MSG_OPTIONAL_FONT_NOT_MATCHED"
    assert input_rule["fonts"]["optional_fonts"][0]["valid"] == "Fail"


def test_evaluate_successful_optional_font_with_multiplicity_2():
    input_rule = create_input_rule([], [SimpleOptionalFont("Arial", "TrueType", "WinAnsiEncoding", 2)])

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((1, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding")),
    ]

    FontRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule["fonts"]["optional_fonts"][0]["validation_message_code"] == "MSG_OPTIONAL_FONT_MATCHED"
    assert input_rule["fonts"]["optional_fonts"][0]["valid"] == "Pass"


def test_evaluate_failure_optional_font_with_multiplicity_2():
    input_rule = create_input_rule([], [SimpleOptionalFont("Arial", "TrueType", "WinAnsiEncoding", 2)])

    metadata = {}
    metadata["fonts"] = [
        font_dict_for_tuple((1, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((2, "TrueType", "Arial", "WinAnsiEncoding")),
        font_dict_for_tuple((3, "TrueType", "Arial", "WinAnsiEncoding")),
    ]

    FontRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule["fonts"]["optional_fonts"][0]["validation_message_code"] == "MSG_OPTIONAL_FONT_NOT_MATCHED"
    assert input_rule["fonts"]["optional_fonts"][0]["valid"] == "Fail"


@pytest.mark.skip()
@pytest.mark.parametrize("file", FileUtilities.get_all_files_recursively("../test_documents/"))
def test_evaluate_fonts_for_all_files_in_directory(file):
    template_names = [
        "Bank of america",
        "chase bank",
        "accenture",
        "charles schwab bank",
        "chime bank",
        "people's united",
        "capital one bank",
        "navy fcu",
        "citizens bank",
        "gusto",
        "intuit",
        "insperity",
        "justworks",
        "rippling",
        "td bank",
        "paychex",
        "paycor",
        "pnc bank",
        "truist",
        "usaa",
        "wells fargo",
        "ceridian",
        "adp2",
        "ally bank",
        "ADPNA",
    ]

    print(file)
    metadata = {
        "fonts": PDFUtilities.extract_xref_fonts(file),
        "paystub_count": PDFUtilities.retrieve_paystub_count(file),
    }
    metadata_validated_against_font_rule = False
    for template_name in template_names:
        print(template_name)
        for i in list(range(retrieve_font_rule_count(template_name))):
            font_rule = retrieve_font_rules_by_name(template_name, i)
            FontRuleEvaluator().evaluate(font_rule, metadata)
            paths = find_key_value_pairs(font_rule, "valid", "Pass")
            if paths:
                print(f"Fonts evaluated successfully for file: {file} against font_rule template: {template_name}")
                print(font_rule)
                metadata_validated_against_font_rule = True
    if not metadata_validated_against_font_rule:
        print("Fonts not evaluated successfully for file: " + file)
        print(metadata["fonts"])
        assert not "Valid" in file


def find_key_value_pairs(dictionary, target_key, target_value, path=None, found=None):
    if found is None:
        found = []
    if path is None:
        path = []

    for key, value in dictionary.items():
        current_path = path + [key]
        if isinstance(value, dict):
            # Recursive call for nested dictionaries
            find_key_value_pairs(value, target_key, target_value, current_path, found)
        elif key == target_key and value == target_value:
            found.append(current_path)

    return found


def font_dict_for_tuple(tp):
    return {"xref": tp[0], "subtype": tp[1], "name": tp[2], "encoding": tp[3]}
