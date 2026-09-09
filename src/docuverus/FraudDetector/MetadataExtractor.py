import logging
import fitz
from lxml import etree

from docuverus.RuleEvaluators.FileSizeRuleEvaluator import (
    add_file_size_to_metadata,
    add_paystub_count_to_metadata,
)
from docuverus.Utils.PDFUtilities import PDFUtilities


class MetadataExtractor:
    _IMAGE_ONLY_TEXT_THRESHOLD = 50

    def extract_metadata(self, file_reader, template_type):
        metadata = {}
        try:
            pdf_document = fitz.open(stream=file_reader, filetype="pdf")
        except Exception as e:
            logging.error(f"Failed to open PDF: {e}")
            metadata["exception"] = True
            return metadata
        metadata = pdf_document.metadata
        if self.is_image_only_pdf(pdf_document):
            metadata["image_file"] = True
        else:
            metadata["image_file"] = False
        metadata["template"] = template_type
        add_file_size_to_metadata(pdf_document, metadata)
        add_paystub_count_to_metadata(file_reader, metadata)
        metadata["fonts"] = PDFUtilities.extract_xref_fonts(pdf_document)
        return metadata

    @staticmethod
    def is_image_only_pdf(pdf_document):
        extracted_text_length = 0

        for page in pdf_document:
            extracted_text_length += len(page.get_text().strip())
            if extracted_text_length >= MetadataExtractor._IMAGE_ONLY_TEXT_THRESHOLD:
                return False

        return True

    def extract_xml_metadata(self, file_stream):
        namespaces = {"pdf": "http://ns.adobe.com/pdf/1.3/", "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}
        pdf_document = fitz.open(stream=file_stream, filetype="pdf")
        xml_metadata = pdf_document.get_xml_metadata()

        return self.parse_xml_metadata(xml_metadata, namespaces)

    def parse_xml_metadata(self, xml_metadata, namespaces):
        logging.debug(f"XML metadata: {xml_metadata}")
        xml_tree = etree.fromstring(xml_metadata)
        xml_element = xml_tree.xpath("//pdf:Producer", namespaces=namespaces)
        if xml_element:
            return {"producer-xml": xml_element[0].text}
        else:
            xml_attribute = xml_tree.xpath("//rdf:Description/@pdf:Producer", namespaces=namespaces)
            if xml_attribute:
                return {"producer-xml": xml_attribute[0]}
            return {"producer-xml": ""}
