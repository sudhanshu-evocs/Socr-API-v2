import pytest

from docuverus.RuleEvaluators.FileSizeRuleEvaluator import (
    FileSizeRuleEvaluator,
    add_file_size_to_metadata,
    add_paystub_count_to_metadata,
)


def test_add_file_size_in_metadata_after():
    # arrange
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    metadata = {}
    actual_file_size = 308.695

    # act
    add_file_size_to_metadata(open(file_path, "rb"), metadata)

    # assert
    assert metadata["file_size"] == actual_file_size


def test_invalid_file_when_file_size_is_too_big_file1():
    # Arrange
    file_path = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf"
    input_rule = {"file_size": {"min": 190, "max": 450}}
    expected_result = {
        "file_size": {
            "min": 190,
            "max": 450,
            "algorithm": "Constant",
            "actual": 2373.396,
            "valid": "Fail",
            "validation_message_code": "MSG_FILE_SIZE_INVALID",
        }
    }

    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_invalid_file_when_file_size_is_too_big_file2():
    # Arrange
    file_path = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big_2.pdf"
    input_rule = {
        "file_size": {
            "min": 190,
            "max": 450,
        }
    }
    expected_result = {
        "file_size": {
            "min": 190,
            "max": 450,
            "algorithm": "Constant",
            "actual": 3045.462,
            "valid": "Fail",
            "validation_message_code": "MSG_FILE_SIZE_INVALID",
        },
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_another_valid_bank_of_america_statement():
    # Arrange
    file_path = "../test_documents/Valid_Bank_of_America_Statement.pdf"
    input_rule = {
        "file_size": {
            "min": 190,
            "max": 450,
        }
    }
    expected_result = {
        "file_size": {
            "min": 190,
            "max": 450,
            "algorithm": "Constant",
            "actual": 308.695,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_td_bank_statement_to_validate_document():
    # Arrange
    file_path = "../test_documents/Valid_TD_Bank_Statement_ios.pdf"
    input_rule = {
        "file_size": {
            "min": 140,
            "max": 185,
        }
    }
    expected_result = {
        "file_size": {
            "min": 140,
            "max": 185,
            "algorithm": "Constant",
            "actual": 158.519,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_td_bank_statement_with_different_file_size_range_to_validate_document():
    # Arrange
    file_path = "../test_documents/Valid_TD_Bank_Statement_opentext.pdf"

    input_rule = {
        "file_size": {
            "min": 910,
            "max": 990,
        }
    }
    expected_result = {
        "file_size": {
            "min": 910,
            "max": 990,
            "algorithm": "Constant",
            "actual": 956.42,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_invalid_paychex_paystub():
    # Arrange

    file_path = "../test_documents/Invalid_paychex_for_file_size.pdf"
    input_rule = {
        "file_size": {
            "min": 6,
            "max": 13,
        }
    }
    expected_result = {
        "file_size": {
            "min": 6,
            "max": 13,
            "algorithm": "Constant",
            "actual": 806.833,
            "valid": "Fail",
            "validation_message_code": "MSG_FILE_SIZE_INVALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_paycor_single_page_paystub():
    # Arrange
    file_path = "../test_documents/Valid_paycor_1_page_paystub.pdf"
    input_rule = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
        }
    }
    expected_result = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
            "actual": 40.574,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(open(file_path, "rb").read(), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_paycor_2_page_paystub():
    # Arrange

    file_path = "../test_documents/Valid_paycor_2_pages_paystub.pdf"
    input_rule = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
        }
    }
    expected_result = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
            "actual": 56.112,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(open(file_path, "rb").read(), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_paycor_with_producer_ABCpdf_2_page_paystub():
    # Arrange

    file_path = "../test_documents/Valid_paycor_with_pro_ABC_2_pages_paystub.pdf"
    input_rule = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
        }
    }
    expected_result = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
            "actual": 44.615,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(open(file_path, "rb").read(), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_paycor_with_producer_ABCpdf_5_page_paystub():
    # Arrange

    file_path = "../test_documents/Valid_paycor_with_pro_ABC_5_pages_paystub.pdf"
    input_rule = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
        }
    }
    expected_result = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
            "actual": 82.702,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(open(file_path, "rb").read(), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_paycor_with_producer_ABCpdf_10_page_paystub():
    # Arrange

    file_path = "../test_documents/Valid_paycor_with_pro_ABC_10_pages_paystub.pdf"
    input_rule = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
        }
    }
    expected_result = {
        "file_size": {
            "min": 35,
            "max": 45,
            "algorithm": "Linear",
            "min_slope": 8,
            "max_slope": 20,
            "actual": 171.459,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(open(file_path, "rb").read(), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_paycom_2_page_paystub():
    # Arrange

    file_path = "../test_documents/Valid_Paycom_2_page_paystub.pdf"
    input_rule = {
        "file_size": {
            "min": 44,
            "max": 50,
            "algorithm": "Linear",
            "min_slope": 44,
            "max_slope": 50,
        }
    }
    expected_result = {
        "file_size": {
            "min": 44,
            "max": 50,
            "algorithm": "Linear",
            "min_slope": 44,
            "max_slope": 50,
            "actual": 91.071,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(open(file_path, "rb").read(), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_paycom_6_page_paystub():
    # Arrange

    file_path = "../test_documents/Valid_Paycom_6_page_paystub.pdf"
    input_rule = {
        "file_size": {
            "min": 44,
            "max": 50,
            "algorithm": "Linear",
            "min_slope": 44,
            "max_slope": 50,
        }
    }
    expected_result = {
        "file_size": {
            "min": 44,
            "max": 50,
            "algorithm": "Linear",
            "min_slope": 44,
            "max_slope": 50,
            "actual": 271.077,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(open(file_path, "rb").read(), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_paycom_3_page_paystub():
    # Arrange

    file_path = "../test_documents/Valid_Paycom_Paystub_2024.pdf"
    input_rule = {
        "file_size": {
            "min": 44,
            "max": 50,
            "algorithm": "Linear",
            "min_slope": 44,
            "max_slope": 50,
        }
    }
    expected_result = {
        "file_size": {
            "min": 44,
            "max": 50,
            "algorithm": "Linear",
            "min_slope": 44,
            "max_slope": 50,
            "actual": 91.828,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(open(file_path, "rb").read(), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_valid_results_for_valid_paycom_1_page_paystub():
    # Arrange

    file_path = "../test_documents/Valid_Paycom_Paystub_2024_1.pdf"
    input_rule = {
        "file_size": {
            "min": 44,
            "max": 50,
            "algorithm": "Linear",
            "min_slope": 44,
            "max_slope": 50,
        }
    }
    expected_result = {
        "file_size": {
            "min": 44,
            "max": 50,
            "algorithm": "Linear",
            "min_slope": 44,
            "max_slope": 50,
            "actual": 45.965,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(open(file_path, "rb").read(), metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


@pytest.mark.parametrize(
    "min,max,min_slope,max_slope,file_size,paystub_count",
    [
        (35, 45, 35, 45, 41, 1),
        (10, 20, 5, 10, 22, 2),
        (44, 50, 44, 50, 135, 3),
        (44, 50, 44, 50, 177, 4),
        (44, 50, 44, 50, 220, 5),
        (44, 50, 44, 50, 270, 6),
    ],
)
def test_valid_file_size_range_for_linear_algorithm(min, max, min_slope, max_slope, file_size, paystub_count):
    input_rule = {
        "file_size": {
            "min": min,
            "max": max,
            "algorithm": "Linear",
            "min_slope": min_slope,
            "max_slope": max_slope,
        }
    }

    metadata = {"file_size": file_size, "paystub_count": paystub_count}

    expected_result = {
        "file_size": {
            "min": min,
            "max": max,
            "algorithm": "Linear",
            "min_slope": min_slope,
            "max_slope": max_slope,
            "actual": file_size,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }

    FileSizeRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule == expected_result


@pytest.mark.parametrize(
    "min,max,min_slope,max_slope,file_size,paystub_count",
    [
        (35, 45, 8, 20, 321, 1),
        (10, 20, 5, 10, 176, 2),
        (44, 50, 44, 50, 200, 3),
        (44, 50, 44, 50, 276, 4),
        (44, 50, 44, 50, 300, 5),
        (44, 50, 44, 50, 436, 6),
    ],
)
def test_invalid_file_size_range_for_linear_algorithm(min, max, min_slope, max_slope, file_size, paystub_count):
    input_rule = {
        "file_size": {
            "min": min,
            "max": max,
            "algorithm": "Linear",
            "min_slope": min_slope,
            "max_slope": max_slope,
        }
    }

    metadata = {"file_size": file_size, "paystub_count": paystub_count}

    expected_result = {
        "file_size": {
            "min": min,
            "max": max,
            "algorithm": "Linear",
            "min_slope": min_slope,
            "max_slope": max_slope,
            "actual": file_size,
            "valid": "Fail",
            "validation_message_code": "MSG_FILE_SIZE_INVALID",
        }
    }

    FileSizeRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule == expected_result


@pytest.mark.parametrize(
    "min,max,min_slope,max_slope,file_size,paystub_count",
    [
        (18, 74, 5, 8, 42, 1),
        (18, 74, 5, 8, 72, 1),
        (18, 74, 5, 8, 77, 6),
        (18, 74, 5, 8, 102, 9),
        (18, 74, 5, 8, 232, 23),
        (18, 74, 5, 8, 102, 12),
        (18, 74, 5, 8, 82.3, 6),
    ],
)
def test_valid_file_size_range_for_gusto_paystubs(min, max, min_slope, max_slope, file_size, paystub_count):
    input_rule = {
        "file_size": {
            "min": min,
            "max": max,
            "algorithm": "Linear",
            "min_slope": min_slope,
            "max_slope": max_slope,
        }
    }

    metadata = {"file_size": file_size, "paystub_count": paystub_count}

    expected_result = {
        "file_size": {
            "min": min,
            "max": max,
            "algorithm": "Linear",
            "min_slope": min_slope,
            "max_slope": max_slope,
            "actual": file_size,
            "valid": "Pass",
            "validation_message_code": "MSG_FILE_SIZE_VALID",
        }
    }

    FileSizeRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule == expected_result


@pytest.mark.parametrize(
    "min,max,min_slope,max_slope,file_size,paystub_count",
    [
        (18, 74, 5, 8, 83, 1),
        (18, 74, 5, 8, 92, 1),
        (18, 74, 5, 8, 160, 6),
        (18, 74, 5, 8, 157, 9),
        (18, 74, 5, 8, 334, 23),
        (18, 74, 5, 8, 211, 12),
        (18, 74, 5, 8, 184, 6),
    ],
)
def test_invalid_file_size_range_for_gusto_paystubs(min, max, min_slope, max_slope, file_size, paystub_count):
    input_rule = {
        "file_size": {
            "min": min,
            "max": max,
            "algorithm": "Linear",
            "min_slope": min_slope,
            "max_slope": max_slope,
        }
    }

    metadata = {"file_size": file_size, "paystub_count": paystub_count}

    expected_result = {
        "file_size": {
            "min": min,
            "max": max,
            "algorithm": "Linear",
            "min_slope": min_slope,
            "max_slope": max_slope,
            "actual": file_size,
            "valid": "Fail",
            "validation_message_code": "MSG_FILE_SIZE_INVALID",
        }
    }

    FileSizeRuleEvaluator().evaluate(input_rule, metadata)

    assert input_rule == expected_result


def test_validate_when_file_size_is_unknown():
    # Arrange

    file_path = "../test_documents/Valid_Paycom_Paystub_2024_1.pdf"
    input_rule = {
        "file_size": {
            "algorithm": "Unknown",
        }
    }
    expected_result = {
        "file_size": {
            "algorithm": "Unknown",
            "actual": 45.965,
            "valid": "NOT_APPLICABLE",
            "validation_message_code": "MSG_VALID_FILE_SIZE_UNKNOWN",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(file_path, metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result


def test_validate_failing_case_when_algorithm_is_not_present():
    # Arrange

    file_path = "../test_documents/Valid_Paycom_Paystub_2024_1.pdf"
    input_rule = {
        "file_size": {
            "algorithm": "None",
        }
    }
    expected_result = {
        "file_size": {
            "algorithm": "None",
            "actual": 45.965,
            "valid": "NOT_APPLICABLE",
            "validation_message_code": "MSG_NOT_APPLICABLE",
        }
    }
    # Act
    metadata = {}
    add_file_size_to_metadata(open(file_path, "rb"), metadata)
    add_paystub_count_to_metadata(file_path, metadata)
    FileSizeRuleEvaluator().evaluate(input_rule, metadata)
    # Assert
    assert input_rule == expected_result
