from datetime import datetime

from docuverus.Utils.DateTimeUtilities import DateTimeUtilities


def test_valid_datetime_object_created_from_valid_pymupdf_string_seperated_by_hyphen():
    # arrange
    input_datetime_str = "D:20231023110520-04'00'"
    expected = datetime(2023, 10, 23, 11, 5, 20)
    # act
    actual = DateTimeUtilities.create(input_datetime_str)

    # assert
    assert expected == actual


def test_valid_datetime_object_created_from_valid_pymupdf_string_with_Z_char():
    # arrange
    input_datetime_str = "D:20230412160033Z00'00'"
    expected = datetime(2023, 4, 12, 16, 0, 33)
    # act
    actual = DateTimeUtilities.create(input_datetime_str)

    # assert
    assert expected == actual
