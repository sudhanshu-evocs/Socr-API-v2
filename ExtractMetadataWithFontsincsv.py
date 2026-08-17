import csv
import os

import fitz  # PyMuPDF


def get_pdf_files_recursive(directory_path):
    pdf_file_paths = []
    for root, _, files in os.walk(directory_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(".pdf"):
                pdf_file_paths.append(file_path)
    return pdf_file_paths


def get_pdf_metadata(file_path):
    global pdf_document
    metadata = {"Fonts": []}

    try:
        pdf_document = fitz.open(file_path)
        metadata["Number of Pages"] = pdf_document.page_count
        metadata["title"] = pdf_document.metadata.get("title", None)
        metadata["author"] = pdf_document.metadata.get("author", None)
        metadata["subject"] = pdf_document.metadata.get("subject", None)
        metadata["producer"] = pdf_document.metadata.get("producer", None)
        metadata["creator"] = pdf_document.metadata.get("creator", None)
        metadata["modDate"] = pdf_document.metadata.get("modDate", None)
        metadata["creationDate"] = pdf_document.metadata.get("creationDate", None)
        metadata["keywords"] = pdf_document.metadata.get("keywords", None)
        metadata["format"] = pdf_document.metadata.get("format", None)
        metadata["encryption"] = pdf_document.metadata.get("encryption", None)
        # metadata['size'] = pdf_document.metadata.get('size', None)
        # metadata['size'] = pdf_document.get_file_size()
        # print(metadata['size'])

        # Extract fonts used in each page
        for page_number in range(pdf_document.page_count):
            page = pdf_document[page_number]
            extracted_fonts = page.get_fonts(full=True)
            metadata["Fonts"].append(extracted_fonts)

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
    finally:
        pdf_document.close()

    return metadata


current_directory = "test_documents"
csv_output_path = "./pdf_metadata_fonts_recursive_gusto.csv"

pdf_files = get_pdf_files_recursive(current_directory)

with open(csv_output_path, "w", newline="", encoding="utf-8") as csv_file:
    fieldnames = [
        "Folder_name",
        "File",
        "Page_Number",
        "xref",
        "ext",
        "type",
        "basefont",
        "name",
        "encoding",
        "refrencer",
        "producer",
        "author",
        "creationDate",
        "modDate",
        "creator",
        "keywords",
        "title",
        "subject",
        "format",
        "encryption",
        "size",
    ]
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    for pdf_file in pdf_files:
        metadata = get_pdf_metadata(pdf_file)
        print(pdf_file)
        updated_filename = pdf_file.split("\\")
        folder_name = updated_filename[0]
        updated_filename_1 = updated_filename[1]
        file_size = os.stat(pdf_file).st_size / 1000
        for page_number, fonts_data in enumerate(metadata["Fonts"]):
            # Write filename and folder_name only once for each PDF file
            if page_number == 0:
                csv_writer.writerow(
                    {
                        "Folder_name": folder_name,
                        "File": updated_filename_1,
                    }
                )
            # print(metadata.get('creationDate', None))
            # print(metadata.get('modDate', None))

            for font_detail in fonts_data:
                xref, ext, ftype, basefont, name, encoding, refrencer = font_detail
                csv_writer.writerow(
                    {
                        #'File': updated_filename_1,
                        "producer": metadata["producer"],
                        "author": metadata["author"],
                        "creationDate": metadata["creationDate"],
                        "modDate": metadata["modDate"],
                        "creator": metadata["creator"],
                        "Page_Number": page_number + 1,
                        "xref": xref,
                        "ext": ext,
                        "type": ftype,
                        "basefont": basefont,
                        "name": name,
                        "encoding": encoding,
                        "refrencer": refrencer,
                        "keywords": metadata["keywords"],
                        "title": metadata["title"],
                        "subject": metadata["subject"],
                        "format": metadata["format"],
                        "encryption": metadata["encryption"],
                        "size": file_size,
                    }
                )

print(f"Recursive PDF metadata including fonts has been written to {csv_output_path}.")
