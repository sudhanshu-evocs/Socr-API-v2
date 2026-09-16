import logging
import re

from docuverus.RuleEvaluators.RuleEvaluator import RuleEvaluator
from docuverus.Utils.Messages import MessageCode, ValidStates


class FontRuleEvaluator(RuleEvaluator):
    MAX_FONT_MULTIPLICITY = 9999

    def evaluate(self, rule: dict, metadata: dict) -> None:
        logging.info("Starting font rule evaluation.")
        document_font_list = self.extract_fonts(metadata["fonts"])
        logging.debug(f"Extracted document fonts: {document_font_list}")
        self.clean_rules(rule)

        # Update expected multiplicity based on number of detected paystubs
        if "paystub_count" in metadata and metadata["paystub_count"] is not None:
            logging.info(f"Paystub count detected: {metadata['paystub_count']}")
            if "paystub_count" in metadata and metadata["paystub_count"] > 0:
                self.add_multiplicity_for_paystubs(rule["fonts"], metadata["paystub_count"])

        # Validate required fonts
        for required_font in rule["fonts"]["required_fonts"]:
            logging.info(f"Validating required font: {required_font}")
            self.validate_font(document_font_list, required_font, is_required=True)

        # Validate optional fonts
        for optional_font in rule["fonts"]["optional_fonts"]:
            logging.info(f"Validating optional font: {optional_font}")
            self.validate_font(document_font_list, optional_font, is_required=False)

        self.evaluate_additional_fonts(rule["fonts"]["required_fonts"], rule["fonts"]["optional_fonts"], document_font_list, rule["fonts"])

        self.evaluate_final_status(rule["fonts"])

    def evaluate_additional_fonts(self, required_font_list, optional_font_list, document_font_list, rule):
        logging.info(f"Evaluating additional fonts in the document.")
        expected_fonts = required_font_list + optional_font_list

        def get_additional_fonts(valid_state=ValidStates.STATE_FAIL, validation_message_code=MessageCode.MSG_FRAUD_FONT_FOUND):
            list_of_fraud_fonts = []
            for doc_font in document_font_list:
                doc_font = list(doc_font)
                doc_font = [value if value else "" for value in doc_font]

                doc_font_dict = {
                    "name": doc_font[1],
                    "type": doc_font[0],
                    "encoding": doc_font[2],
                }

                if not self.is_document_font_expected(doc_font_dict, expected_fonts):
                    logging.warning(f"Fraud font detected: {doc_font_dict}")
                    list_of_fraud_fonts.append(
                        {
                            **doc_font_dict,
                            **{"actual_multiplicity": doc_font[3]},
                            **{"multiplicity": 0},
                            **{"valid": valid_state},
                            **{"validation_message_code": validation_message_code},
                        }
                    )

            return sorted(
                list_of_fraud_fonts,
                key=lambda x: (
                    x["name"],
                    x["encoding"] if x["encoding"] is not None else "",
                ),
            )

        if required_font_list or optional_font_list:
            additional_fonts_list = get_additional_fonts()
        else:
            additional_fonts_list = get_additional_fonts(ValidStates.STATE_FDR, MessageCode.MSG_FONT_NOT_APPLICABLE)

        rule["additional_fonts"] = additional_fonts_list

    def validate_font(self, page_font_set, font, is_required):
        if not self.is_font_in_document(font, page_font_set):
            font["actual_multiplicity"] = 0
            font["valid"] = ValidStates.STATE_FAIL if is_required else ValidStates.STATE_PASS
            font["validation_message_code"] = (
                MessageCode.MSG_REQUIRED_FONT_NOT_MATCHED if is_required else MessageCode.MSG_OPTIONAL_FONT_NOT_FOUND
            )
        elif font["actual_multiplicity"] <= font["multiplicity"]:
            font["valid"] = ValidStates.STATE_PASS
            font["validation_message_code"] = (
                MessageCode.MSG_REQUIRED_FONT_MATCHED if is_required else MessageCode.MSG_OPTIONAL_FONT_MATCHED
            )
        else:
            font["valid"] = ValidStates.STATE_FAIL
            font["validation_message_code"] = (
                MessageCode.MSG_REQUIRED_FONT_NOT_MATCHED if is_required else MessageCode.MSG_OPTIONAL_FONT_NOT_MATCHED
            )

    def is_font_in_document(self, font, page_font_set):
        font_name = font["name"] if font["name"] else ""
        font_type = font["type"] if font["type"] else ""
        font_encoding = font["encoding"] if font["encoding"] else ""
        normalized_font_name = normalize_font_name_for_match(font_name)

        if self.is_blank_type_and_encoding(font):
            max_multiplicity = 0
            for page_font in page_font_set:
                page_font = list(page_font)
                page_font = [value if value else "" for value in page_font]
                if normalize_font_name_for_match(page_font[1]) == normalized_font_name:
                    if page_font[3] > max_multiplicity:
                        max_multiplicity = page_font[3]
            if max_multiplicity > 0:
                font["actual_multiplicity"] = max_multiplicity
                logging.info(f"Font found in document with wildcard type and encoding: {font}")
                return True
            logging.warning(f"Font not found in document: {font}")
            return False

        for page_font in page_font_set:
            page_font = list(page_font)
            page_font = [value if value else "" for value in page_font]

            if (
                normalize_font_name_for_match(page_font[1]) == normalized_font_name
                and (page_font[0] == font_type)
                and (page_font[2] == font_encoding)
            ):
                font["actual_multiplicity"] = page_font[3]
                logging.info(f"Font found in document: {font}")
                return True
        logging.warning(f"Font not found in document: {font}")
        return False

    def is_blank_type_and_encoding(self, font):
        return (font["type"] if font["type"] else "") == "" and (font["encoding"] if font["encoding"] else "") == ""

    def is_document_font_expected(self, doc_font_dict, expected_fonts):
        doc_name = doc_font_dict["name"] if doc_font_dict["name"] else ""
        doc_type = doc_font_dict["type"] if doc_font_dict["type"] else ""
        doc_encoding = doc_font_dict["encoding"] if doc_font_dict["encoding"] else ""
        normalized_doc_name = normalize_font_name_for_match(doc_name)

        for expected_font in expected_fonts:
            expected_name = expected_font["name"] if expected_font["name"] else ""
            expected_type = expected_font["type"] if expected_font["type"] else ""
            expected_encoding = expected_font["encoding"] if expected_font["encoding"] else ""

            if normalize_font_name_for_match(expected_name) != normalized_doc_name:
                continue

            if self.is_blank_type_and_encoding(expected_font):
                return True

            if expected_type == doc_type and expected_encoding == doc_encoding:
                return True

        return False

    def extract_fonts(self, fonts_list):
        extracted_font_dict = {}
        font_dict = {}
        for doc_font in fonts_list:
            font_key = self.get_font_key(doc_font)
            if font_key in font_dict:
                font_dict[font_key] += 1
            else:
                font_dict[font_key] = 1
            for font_key, multiplicity in font_dict.items():
                if font_key not in extracted_font_dict or multiplicity > extracted_font_dict[font_key]:
                    extracted_font_dict[font_key] = multiplicity
        extracted_font_list = [(key[0], key[1], key[2], value) for key, value in extracted_font_dict.items()]
        logging.debug(f"Extracted font list: {extracted_font_list}")
        return extracted_font_list

    def get_font_key(self, doc_font):
        return (
            doc_font["subtype"],
            get_font_name(doc_font["name"]),
            doc_font["encoding"],
        )

    def clean_rules(self, rule_set) -> dict:
        logging.info("Cleaning font rules.")
        if "fonts" not in rule_set:
            rule_set["fonts"] = {"required_fonts": [], "optional_fonts": []}
        font_rules = rule_set["fonts"]
        if "required_fonts" not in font_rules:
            font_rules["required_fonts"] = []
        if "optional_fonts" not in font_rules:
            font_rules["optional_fonts"] = []
        font_rules["additional_fonts"] = []

        for font_rule in font_rules["required_fonts"]:
            if "multiplicity" not in font_rule:
                font_rule["multiplicity"] = 1
        for font_rule in font_rules["optional_fonts"]:
            if "multiplicity" not in font_rule:
                font_rule["multiplicity"] = self.MAX_FONT_MULTIPLICITY
        return font_rules

    def add_multiplicity_for_paystubs(self, rule, paystub_count):
        logging.info(f"Updating multiplicity for {paystub_count} paystubs.")
        for font_rule in rule["required_fonts"]:
            font_rule["multiplicity"] = paystub_count * font_rule["multiplicity"]

    def evaluate_final_status(self, rule):
        logging.info("Evaluating final font validation status.")
        all_required_valid = all(font["valid"] == ValidStates.STATE_PASS for font in rule["required_fonts"])
        has_fraud_fonts = False
        for font in rule["additional_fonts"]:
            if font["valid"] == ValidStates.STATE_FAIL:
                has_fraud_fonts = True

        if not rule["required_fonts"] and not rule["optional_fonts"]:
            rule["valid"] = ValidStates.STATE_FDR
            rule["validation_message_code"] = MessageCode.MSG_FONT_RULE_NOT_APPLICABLE
        elif all_required_valid and not has_fraud_fonts:
            rule["valid"] = ValidStates.STATE_PASS
            rule["validation_message_code"] = MessageCode.MSG_FONT_VALIDATION_VALID
        else:
            rule["valid"] = ValidStates.STATE_FAIL
            rule["validation_message_code"] = MessageCode.MSG_FONT_VALIDATION_INVALID


def get_font_name(font_str):
    patterns = [(r"([A-Z]{6})\+(.+)", 2), (r"(.+)(_CZEX[0-9A-F]{4})", 1)]
    for pattern in patterns:
        match = re.match(pattern[0], font_str)
        if match:
            font_str = match.group(pattern[1])
    return font_str


def normalize_font_name_for_match(font_str):
    """Match font names ignoring spaces, underscores, hyphens, and case.

    Example: "Connections Medium Bold" matches "ConnectionsMediumBold".
    """
    return re.sub(r"[^a-z0-9]", "", get_font_name(font_str or "").lower())
