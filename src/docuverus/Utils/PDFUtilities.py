import argparse
import logging
import sys
import tempfile
from pathlib import Path

import fitz

# Support direct execution via `python src/docuverus/Utils/PDFUtilities.py ...`.
if __package__ in (None, ""):
    src_root = Path(__file__).resolve().parents[2]
    src_root_str = str(src_root)
    if src_root_str not in sys.path:
        sys.path.insert(0, src_root_str)

from docuverus.RuleEvaluators.get_count_of_paystubs import (
    count_paystubs,
    count_paystubs_by_pdf_document,
)


class PDFUtilities:

    @staticmethod
    def retrieve_paystub_count(file_path):
        return count_paystubs(file_path)

    @staticmethod
    def retrieve_paystub_count_by_pdf(pdf_document):
        return count_paystubs_by_pdf_document(pdf_document)

    @staticmethod
    def extract_unique_fonts(file_path):
        pdf_document = fitz.open(file_path)
        fonts_list = []
        for page in pdf_document:
            fonts_list += page.get_fonts()
        return list(set(fonts_list))

    @staticmethod
    def extract_xref_fonts(pdf_document):
        def parse_font_info(font_string):
            lines = font_string.split("\n")
            font_info = {}
            looking_for_special_font = False
            for line in lines:
                if "/Type /Font" in line:
                    looking_for_special_font = True
                if "/BaseFont" in line:
                    font_info["name"] = line.split("/BaseFont /")[1].strip()
                    if "#20" in font_info["name"]:
                        font_info["name"] = font_info["name"].replace("#20", " ")
                if "/Name" in line and looking_for_special_font and not "name" in font_info:
                    font_info["name"] = line.split("/Name /")[1].strip()
                elif "/Encoding" in line:
                    temp_encoding = line.split("/Encoding")[1].strip()
                    if temp_encoding.startswith("/"):
                        font_info["encoding"] = temp_encoding.strip("/")
                elif "/Subtype" in line:
                    font_info["subtype"] = line.split("/Subtype /")[1].strip()
            if "encoding" not in font_info:
                font_info["encoding"] = ""
            return font_info

        def is_cid_type_2(font_string):
            lines = font_string.split("\n")
            for line in lines:
                if "/CIDFontType2" in line:
                    return True
            return False

        xref_fonts = []
        for xref in range(1, pdf_document.xref_length()):
            try:
                xref_object = pdf_document.xref_object(xref, compressed=False)
            except Exception:
                pdf_document.update_object(xref, "<<>>")
                xref_object = pdf_document.xref_object(xref, compressed=False)
            if "/BaseFont /" in xref_object or "/Type /Font" in [line.strip() for line in xref_object.splitlines()]:
                if not is_cid_type_2(xref_object):
                    xref_font = parse_font_info(xref_object)
                    if "name" in xref_font:
                        xref_font["xref"] = xref
                        xref_fonts.append(xref_font)
        return xref_fonts

    @staticmethod
    def highlight_usages_of_fonts_in_pdf(input_pdf_path, output_pdf_path, font_name, color_str="1,1,0"):
        doc = fitz.open(input_pdf_path)
        color = tuple(map(float, color_str.split(",")))
        for page in doc:
            text_instances = page.get_text("dict")["blocks"]

            for instance in text_instances:
                if instance["type"] == 0:
                    for line in instance["lines"]:
                        for span in line["spans"]:
                            if span["font"].lower() == font_name.lower():
                                rect = fitz.Rect(span["bbox"])
                                highlight = page.add_highlight_annot(rect)
                                highlight.set_colors(stroke=color)
                                highlight.update()

        logging.debug(f"Saved highlighted PDF to: {output_pdf_path}")
        doc.save(output_pdf_path)

    @staticmethod
    def highlight_usages_of_fonts_in_byte_representation_of_pdf(byte_str, font_name, color):
        doc = fitz.open(stream=byte_str)
        for page in doc:
            text_instances = page.get_text("dict")["blocks"]

            for instance in text_instances:
                if instance["type"] == 0:
                    for line in instance["lines"]:
                        for span in line["spans"]:
                            if span["font"].lower() == font_name.lower():
                                rect = fitz.Rect(span["bbox"])
                                highlight = page.add_highlight_annot(rect)
                                highlight.set_colors(stroke=color)
                                highlight.update()

        with tempfile.NamedTemporaryFile(delete=False) as named_temp_file:
            temp_file_name = named_temp_file.name

        doc.save(named_temp_file.name)

        with open(temp_file_name, "rb") as byte_reader:
            return byte_reader.read()


def main():
    parser = argparse.ArgumentParser(description="A simple command line utility")
    parser.add_argument("input_file", type=str, help="The file to process")
    parser.add_argument("font", type=str, help="The font")
    parser.add_argument("output_file", type=str, help="The output file")
    parser.add_argument("color", nargs="?", default="1,1,0", type=str, help="string representation of a color e.g. '1,0,0' for red")

    args = parser.parse_args()

    PDFUtilities.highlight_usages_of_fonts_in_pdf(args.input_file, args.output_file, args.font, args.color)


if __name__ == "__main__":
    main()
