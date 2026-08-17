import pytest

from docuverus.RuleEvaluators.get_count_of_paystubs import count_paystubs


@pytest.mark.parametrize(
    "expected_count, file",
    [
        (6, "../test_documents/Valid_paycom_6_page_paystub.pdf"),
        (1, "../test_documents/Valid_paycor_1_page_paystub.pdf"),
        (2, "../test_documents/Valid_paycor_2_pages_paystub.pdf"),
        (9, "../test_documents/Valid_Gusto_13_paystubs.pdf"),
        (5, "../test_documents/Valid_paycor_with_pro_ABC_5_pages_paystub.pdf"),
        (10, "../test_documents/Valid_paycor_with_pro_ABC_10_pages_paystub.pdf"),
    ],
)
def test_validate_count_of_paystub_for_paycom(expected_count, file):
    # Arrange
    # Act
    num_of_paystubs = count_paystubs(open(file, "rb").read())
    # Assert
    assert num_of_paystubs == expected_count


# def store_contents_in_tuples(file_path):
#     with open(file_path, 'r') as file:
#         contents = file.read()
#     contents_array = eval(contents)
#     return contents_array
#
# @pytest.mark.parametrize("expected_count, file", store_contents_in_tuples("files.txt"))
# def test_validate_count_of_paystub_for_all_files(expected_count,file):
#     #Arrange
#     #Act
#     num_of_paystubs = count_paystubs(file)
#     #Assert
#     assert  num_of_paystubs == expected_count
#
# def get_all_files_recursively(root_dir):
#     all_files = []
#     for root, dirs, files in os.walk(root_dir):
#         for file in files:
#             all_files.append(os.path.join(root, file))
#     return all_files
#
#
# def create_paystub_count_file_array(root_dir):
#     all_files = []
#     for root, dirs, files in os.walk(root_dir):
#         for file in files:
#             all_files.append((count_paystubs(os.path.join(root, file)),os.path.join(root, file)))
#     return all_files
#
#
#
# # @pytest.mark.parametrize("file", get_all_files_recursively("directory_of_files"))
# # def test_validate_count_paystubs_for_files_in_directory(file):
# #     num_of_paystubs = count_paystubs(file)
# #
# #     assert num_of_paystubs == 1
# #
# #
# def test_other_files():
#     print(create_paystub_count_file_array("../proof_of_income"))
# #
# #
# @pytest.mark.parametrize("expected_count, file", store_contents_in_tuples("files.txt"))
