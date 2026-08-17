import fitz
import pytest

from docuverus.FraudDetector.MetadataExtractor import MetadataExtractor


def _build_pdf_with_text(*page_texts):
    pdf_document = fitz.open()
    for text in page_texts:
        page = pdf_document.new_page()
        if text:
            page.insert_text((72, 72), text)
    return pdf_document


@pytest.mark.parametrize(
    "page_texts, expected_output",
    [
        (("",), True),
        (("x" * 49,), True),
        (("x" * 25, "y" * 24), True),
        (("x" * 50,), False),
        (("x" * 30, "y" * 21), False),
    ],
)
def test_is_image_only_pdf_uses_50_character_buffer(page_texts, expected_output):
    pdf_document = _build_pdf_with_text(*page_texts)

    try:
        assert MetadataExtractor.is_image_only_pdf(pdf_document) is expected_output
    finally:
        pdf_document.close()


def test_xml_metadata_extraction():
    test_results = MetadataExtractor().extract_xml_metadata(
        open("../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf", "rb").read()
    )

    assert test_results["producer-xml"] == "Adobe PDF library 11.00"


def test_xml_metadata_extraction_on_other_file():
    test_results = MetadataExtractor().extract_xml_metadata(
        open("../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big_2.pdf", "rb").read()
    )

    assert test_results["producer-xml"] == "TargetStream StreamEDS rv1.7.41 for Bank of America"


@pytest.mark.parametrize(
    "file_path, expected_output",
    [
        ("../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big.pdf", "Adobe PDF library 11.00"),
        (
            "../test_documents/Invalid_Bank_of_America_Statement_with_file_size_too_big_2.pdf",
            "TargetStream StreamEDS rv1.7.41 for Bank of America",
        ),
        (
            "../test_documents/Invalid_Capital_One_Bank_Statement.pdf",
            "iText® 7.1.5 ©2000-2019 iText Group NV (CAPITAL ONE SERVICES, LLC; licensed version)",
        ),
        ("../test_documents/Invalid_paychex_for_file_size.pdf", ""),
        (
            "../test_documents/Invalid_PNC_Bank_Statement_with_unequal_dates.pdf",
            "Adobe Photoshop for Macintosh -- Image Conversion Plug-in",
        ),
        (
            "../test_documents/Invalid_USAA_bank_statement_for_multiplicity_of_font_check.pdf",
            "iText® 5.5.12 ©2000-2017 iText Group NV (United Services Automobile Association; licensed version)",
        ),
    ],
)
def test_xml_metadata_extraction_for_multiple_files(file_path, expected_output):
    test_results = MetadataExtractor().extract_xml_metadata(open(file_path, "rb").read())

    assert test_results["producer-xml"] == expected_output


@pytest.mark.parametrize(
    "file_path, template, expected_output",
    [
        (
            "../test_documents/fail_pdf_extraction.pdf",
            "ADP1",
            "PDFOUT v3.8v by Xenos, inc.",
        )
    ],
)
def test_metadata_extraction_for_multiple_files(file_path, template, expected_output):
    test_results = MetadataExtractor().extract_metadata(open(file_path, "rb").read(), template)

    assert test_results["producer"] == expected_output
