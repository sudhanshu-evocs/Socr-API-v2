import re

import fitz  # PyMuPDF


def count_paystubs(file_content):
    try:
        # Open the PDF file
        pdf_document = fitz.open(stream=file_content)
        return count_paystubs_by_pdf_document(pdf_document)
    except Exception as error:
        print(error)


def count_paystubs_by_pdf_document(pdf_document):
    num_paystubs = check_image_pdf(pdf_document)

    if num_paystubs is not False:
        # It's an image PDF, return the number of pages
        pdf_document.close()
        return num_paystubs

    num_paystubs = 0
    keywords = [
        "pay date",
        "pay day",
        "check date",
        "paid on",
        "payment date",
        "date payable",
        "date paid",
        "pay period",
        "advice date",
        "paydate",
        "weekly summary",
        "statement effective date",
        "printed on",
    ]
    # Iterate through each page in the PDF
    for page_num in range(pdf_document.page_count):
        # Get the page
        page = pdf_document.load_page(page_num)

        # Extract text from the page
        text = page.get_text()
        clean_text = re.sub(r"\s+", " ", text.lower())
        # Count occurrences of the keyword

        for keyword in keywords:
            if keyword in clean_text:
                num_paystubs += clean_text.count(keyword)
                break
    # Close the PDF document
    pdf_document.close()

    return num_paystubs


def check_image_pdf(pdf_document):
    try:
        all_text = ""
        for page_num in range(pdf_document.page_count):
            # Get the page
            page = pdf_document.load_page(page_num)
            # Extract text from the page
            text = page.get_text()
            all_text += text
        regex_pattern = re.compile(r"^\s*$")
        if regex_pattern.match(all_text):
            num_paystubs = pdf_document.page_count
            return num_paystubs
        else:
            return False
    except Exception as error:
        print(error)
