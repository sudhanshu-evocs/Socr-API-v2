import csv
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import fitz
import pytest

from docuverus.Utils.FileUtilities import FileUtilities
from docuverus.Utils.PDFUtilities import PDFUtilities


def test_extract_xref_fonts_works_for_citizens_bank_pdf():
    file_path = "../test_documents/Valid_Citizens_Bank_Statement.pdf"

    fonts = PDFUtilities.extract_xref_fonts(fitz.open(file_path))

    assert len(fonts) == 19


def test_extract_xref_fonts_works_for_odd_insperity_pdf():
    file_path = "../test_documents/Valid_Odd_Insperity_Paystub.pdf"
    expected_fonts = [
        {"subtype": "Type1", "encoding": "WinAnsiEncoding", "name": "Helvetica-Bold", "xref": 9},
        {"subtype": "Type0", "name": "SUBSET+TimesNewRomanPSItalicMT", "encoding": "Identity-H", "xref": 10},
        {"subtype": "Type0", "name": "SUBSET+TimesNewRomanPSMT", "encoding": "Identity-H", "xref": 11},
        {"subtype": "Type0", "name": "SUBSET+ArialBoldItalicMT", "encoding": "Identity-H", "xref": 12},
        {"subtype": "Type1", "encoding": "WinAnsiEncoding", "name": "Helvetica", "xref": 13},
    ]

    fonts = PDFUtilities.extract_xref_fonts(fitz.open(file_path))

    print(fonts)
    assert fonts == expected_fonts


def test_xml_metadata_and_normal_metadata():
    file_path = "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf"

    pdf_document = fitz.open(file_path)
    print("Normal dictionary metadata")
    print(pdf_document.metadata)
    print("XML metadata")
    print(pdf_document.get_xml_metadata())
    print("END")


def test_xml_metadata_but_not_in_normal_metadata():
    file_path = "../test_documents/Valid_ADP_Paystub_Not_Getting_Metadata_Read.pdf"

    pdf_document = fitz.open(file_path)
    print("Normal dictionary metadata")
    print(pdf_document.metadata)
    print("XML metadata")
    print(pdf_document.get_xml_metadata())
    print("END")


def test_command_line_utility_creates_output_file():
    test_documents_path = Path(__file__).resolve().parents[3] / "test_documents"
    utilities_path = Path(__file__).resolve().parents[3] / "src" / "docuverus" / "Utils"
    # Arrange
    test_file_extension = ".pdf"
    test_file_name = "Invalid_truist_bank_statement"
    file_path = test_documents_path / f"{test_file_name}{test_file_extension}"
    font_name = "Times-Roman"
    output_file_path = test_documents_path / f"{test_file_name}_out{test_file_extension}"

    # Act
    result = subprocess.run(
        [sys.executable, utilities_path / "PDFUtilities.py", file_path, font_name, output_file_path],
        capture_output=True,
        text=True,
    )

    # Assert
    assert result.returncode == 0
    assert os.path.exists(output_file_path)

    # Clean up
    os.remove(output_file_path)


# TODO: Need to move these longer running tests somewhere
@pytest.mark.skip()
def test_command_line_utility_takes_a_color_to_highlight_font_as():
    test_documents_path = Path(__file__).resolve().parents[3] / "test_documents"
    utilities_path = Path(__file__).resolve().parents[3] / "src" / "docuverus" / "Utils"
    # Arrange
    test_file_extension = ".pdf"
    test_file_name = "Invalid_truist_bank_statement"
    file_path = test_documents_path / f"{test_file_name}{test_file_extension}"
    font_name = "Helvetica"
    output_file_path = test_documents_path / f"{test_file_name}_out{test_file_extension}"
    color = "1,0,0"
    # Act
    result = subprocess.run(
        [sys.executable, utilities_path / "PDFUtilities.py", file_path, font_name, output_file_path, color],
        capture_output=True,
        text=True,
    )

    # Assert
    assert result.returncode == 0
    assert os.path.exists(output_file_path)

    # Clean up
    os.remove(output_file_path)


@pytest.mark.skip()
def test_highlight_fonts_with_bytes_from_file():
    test_documents_path = Path(__file__).resolve().parents[3] / "test_documents"
    test_file_extension = ".pdf"
    test_file_name = "Invalid_truist_bank_statement"
    file_path = test_documents_path / f"{test_file_name}{test_file_extension}"
    font_name = "Helvetica"
    color_str = (1, 0, 0)

    output_bytes = []
    with open(file_path, "rb") as byte_reader:
        byte_str = byte_reader.read()
        output_bytes = PDFUtilities.highlight_usages_of_fonts_in_byte_representation_of_pdf(byte_str, font_name, color_str)

    assert len(output_bytes) > 0
    pdf_document = fitz.open(stream=output_bytes)
    assert pdf_document.xref_length() > 0
    print(pdf_document)
    annot_list = []
    for page in pdf_document:
        for annot in page.annots():
            annot_list.append(annot)
            assert annot.colors["stroke"] == list(color_str)
    assert len(annot_list) > 0


@pytest.mark.skip()
def test_highlight_multiple_fonts_with_bytes_from_file():
    test_documents_path = Path(__file__).resolve().parents[3] / "test_documents"
    test_file_extension = ".pdf"
    test_file_name = "Invalid_truist_bank_statement"
    file_path = test_documents_path / f"{test_file_name}{test_file_extension}"
    font_name = "Helvetica"
    color_str_red = (1, 0, 0)
    color_str_green = (0, 1, 0)
    color_list = [list(color_str_red), list(color_str_green)]

    output_bytes = []
    with open(file_path, "rb") as byte_reader:
        byte_str = byte_reader.read()
        output_bytes = PDFUtilities.highlight_usages_of_fonts_in_byte_representation_of_pdf(byte_str, font_name, color_str_red)

    assert len(output_bytes) > 0

    final_output_bytes = PDFUtilities.highlight_usages_of_fonts_in_byte_representation_of_pdf(
        output_bytes, "Helvetica-Oblique", color_str_green
    )
    pdf_document = fitz.open(stream=final_output_bytes)
    assert pdf_document.xref_length() > 0
    print(pdf_document)
    annot_list = []
    for page in pdf_document:
        for annot in page.annots():
            annot_list.append(annot)
            assert annot.colors["stroke"] in color_list
    assert len(annot_list) > 0


@pytest.mark.skip()
def test_create_csv_of_pdf_metrics():
    all_files = FileUtilities.get_all_files_recursively(
        "C:\Workspace\docuverus\dv-automation\RestassuredAPITesting\curated_list_jamie1\Income\Valid Income"
    )

    file_details = []
    for file in all_files:
        pdf_dict = {"name": os.path.basename(file), "size": os.path.getsize(file)}

        pdf_document = fitz.open(file)
        pdf_dict["num_pages"] = pdf_document.page_count
        pdf_dict["metadata"] = pdf_document.metadata
        pdf_dict["fonts"] = PDFUtilities.extract_unique_fonts(file)

        file_details.append(pdf_dict)

    # Act
    output_filename = "pdf_metrics.csv"
    with open(output_filename, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(
            [
                "name",
                "size",
                "num_pages",
                "fonts (xref, ext, type, basefont, name, encoding, referencer(optional))",
            ]
            + list(file_details[0]["metadata"].keys())
        )
        for file in file_details:
            csvwriter.writerow([file["name"], file["size"], file["num_pages"], file["fonts"]] + list(file["metadata"].values()))

    # Assert
    assert False


@pytest.mark.skip()
@pytest.mark.parametrize("file_path", FileUtilities.get_all_files_recursively("../test_documents"))
def test_valid_adp_pdf_that_does_not_have_metadata(file_path):
    if not file_path.endswith(".pdf"):
        return
    pdf_document = fitz.open(file_path)
    metadata = pdf_document.get_xml_metadata()
    print(metadata)
    if metadata:
        root = ET.fromstring(metadata)

        # Define namespaces
        namespaces = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "pdf": "http://ns.adobe.com/pdf/1.3/"}

        description_element = root.find(".//rdf:Description", namespaces)
        print(description_element)
        print(description_element.attrib)
        if description_element and "{http://ns.adobe.com/pdf/1.3/}Producer" in description_element.attrib:
            print("good")
        # Find the pdf:Producer element
        producer_element = root.find(".//pdf:Producer", namespaces)

        # Extract and print the text content of the pdf:Producer element
        if producer_element is not None:
            print(producer_element.text.strip())
            producer_element = producer_element.text.strip()
            assert producer_element == pdf_document.metadata["producer"].strip()
        else:
            print("pdf:Producer element not found")
            producer_element = ""


@pytest.mark.skip()
@pytest.mark.parametrize("file_path", ["../test_documents/Valid_ADP_Paystub_Not_Getting_Metadata_Read.pdf"])
def test_write_new_pdf(file_path):
    pdf_document = fitz.open(file_path)

    pdf_document.metadata["producer"] = "TEST NEW PRODUCER"
    pdf_document.set_metadata(pdf_document.metadata)

    pdf_document.save("../test_documents/Valid_ADP_New.pdf")


@pytest.mark.skip()
@pytest.mark.parametrize(
    "pdf_file, font_name, out_file",
    [
        (
            "D:/Projects/socrdata/ML Model/BankStatments/1st Bank/1691172530452_1st bank feb.pdf",
            "Courier",
            "invalid.pdf",
        )
    ],
)
def test_highlight_usages_of_font_in_pdf(pdf_file, font_name, out_file):
    PDFUtilities.highlight_usages_of_fonts_in_pdf(pdf_file, out_file, font_name)
