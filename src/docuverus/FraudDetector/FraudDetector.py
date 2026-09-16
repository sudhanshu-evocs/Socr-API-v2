import io
import logging

from docuverus.FraudDetector.DateOverrideRule import DateOverrideRule
from docuverus.FraudDetector.MetadataExtractor import MetadataExtractor
from docuverus.RuleEvaluators.RuleSetFactory import RuleSetFactory
from docuverus.Utils.BrowserPrintedDetector import BrowserPrintedDetector
from docuverus.Utils.InvalidProducerCreatorDetector import InvalidProducerCreatorDetector
from docuverus.Utils.JSONUtilities import all_valid_not_fail
from docuverus.Utils.Messages import MessageCode, ValidStates
from docuverus.Utils.TemplateNameUtilities import normalize_template_name

import logging.handlers
import os

_log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
_log_format = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_date_format = "%Y-%m-%d %H:%M:%S"

# Root logger
_logger = logging.getLogger()
_logger.setLevel(_log_level)

if not _logger.handlers:
    # Console handler — always on
    _console = logging.StreamHandler()
    _console.setFormatter(logging.Formatter(_log_format, datefmt=_date_format))
    _logger.addHandler(_console)

    # Rotating file handler — max 10 MB, keep 5 backups
    _log_dir = os.environ.get("LOG_DIR", ".")
    os.makedirs(_log_dir, exist_ok=True)
    _file = logging.handlers.RotatingFileHandler(
        os.path.join(_log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    _file.setFormatter(logging.Formatter(_log_format, datefmt=_date_format))
    _logger.addHandler(_file)


class FraudDetector:
    _na_valid_state = "NOT_APPLICABLE"
    _validation_state_order = {
        ValidStates.STATE_FAIL: 0,
        ValidStates.STATE_FDR: 1,
        ValidStates.STATE_PASS: 2,
    }
    _unknown_result_sort_fields = ("producer", "creator", "fonts", "dates", "file_size")
    _unknown_result_state_rank = {
        ValidStates.STATE_PASS: 0,
        ValidStates.STATE_FDR: 1,
        _na_valid_state: 1,
        ValidStates.STATE_FAIL: 2,
    }

    _log = logging.getLogger("FraudDetector")

    def __init__(
        self,
        template_type,
        rule_evaluator,
        rule_set_factory=RuleSetFactory(
            [
                "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
                "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
            ]
        ),
    ):
        self.template_type = template_type
        self.FILE_SIZE_LABEL = "File Size"
        self.rule_set_factory = rule_set_factory
        self.rule_evaluator = rule_evaluator
        self.date_override_rule = DateOverrideRule()

    def get_document_validations_for_metadata(self, metadata):
        self._log.info("── Validation START — template='%s'", self.template_type)

        if "exception" in metadata:
            self._log.error("Invalid or unreadable PDF — returning FAIL")
            return self.create_validation_results_dictionary()

        if metadata.get("image_file", False):
            self._log.warning("Image-only PDF detected — metadata not applicable")
            return self._build_image_result(metadata)

        self._log.debug(
            "Metadata extracted — producer='%s' creator='%s' fonts=%d filesize=%sKB",
            metadata.get("producer", ""),
            metadata.get("creator", ""),
            len(metadata.get("fonts", [])),
            metadata.get("file_size_kb", "?"),
        )

        rule_sets, unknown_template_flag = self._load_rule_sets()
        self._log.info("Loaded %d rule set(s) for template='%s'", len(rule_sets), self.template_type)
        self._evaluate_rule_sets(rule_sets, metadata)

        passing_rule_set = self._find_passing_rule_set(rule_sets)
        if passing_rule_set is not None:
            self._log.info("✅ PASS — template='%s' matched a rule set", self.template_type)
            return self._build_success_result(passing_rule_set)

        date_override_rule_set = self._find_date_override_rule_set(rule_sets, metadata)
        if date_override_rule_set is not None:
            self._log.warning("⚠️ FDR — possible Save-As / modification scenario for template='%s'", self.template_type)
            return self._build_date_override_result(date_override_rule_set)

        if unknown_template_flag:
            self._log.warning("⚠️ FDR — unknown template='%s', no rule set found", self.template_type)
            return self._build_unknown_template_result(rule_sets)

        if self._has_browser_printed_rule_set(rule_sets):
            self._log.warning("⚠️ FDR — browser-printed document detected for template='%s'", self.template_type)
            return self._build_failure_result(rule_sets)

        if InvalidProducerCreatorDetector.is_invalid_metadata(metadata):
            self._log.error("❌ FAIL — invalid producer/creator metadata for template='%s'", self.template_type)
            return self._build_invalid_result(rule_sets)

        self._log.warning("⚠️ FDR — no rule set matched for template='%s'", self.template_type)
        return self._build_unknown_result(rule_sets)

    def get_document_validations(self, file_path):
        try:
            file_content = open(file_path, "rb")
            self._log.info("Validating document from file: %s", file_path)
            metadata = MetadataExtractor().extract_metadata(io.BytesIO(file_content.read()), self.template_type)
            return self.get_document_validations_for_metadata(metadata)
        except Exception as e:
            self._log.error("Failed to validate document '%s': %s", file_path, e)
            return self.create_validation_results_dictionary()

    def create_validation_results_dictionary(self, valid_state=ValidStates.STATE_FAIL, message_code=MessageCode.MSG_INVALID_PDF_FILE):
        return {
            "final_validation_results": {
                "valid": valid_state,
                "validation_message_code": message_code,
            }
        }

    def _build_image_result(self, metadata):
        result = self.create_validation_results_dictionary(
            valid_state=ValidStates.STATE_FDR,
            message_code=MessageCode.MSG_INVALID_IMAGE_DOCUMENT,
        )
        result["template_rule_set_validation_results"] = [self._create_image_empty_rule_set_with_metadata(metadata)]
        return result

    def _load_rule_sets(self):
        rule_sets = self.rule_set_factory.get_template_rules(self.template_type)
        unknown_template_flag = False

        if not rule_sets:
            rule_sets = [self.rule_set_factory.create_empty_rule_set(self.template_type)]
            unknown_template_flag = True

        return rule_sets, unknown_template_flag

    def _evaluate_rule_sets(self, rule_sets, metadata):
        for rule_set in rule_sets:
            self.rule_evaluator.evaluate(rule_set, metadata)

    def _find_passing_rule_set(self, rule_sets):
        for rule_with_validations in rule_sets:
            is_browser_printed = BrowserPrintedDetector.is_browser_printed_metadata(rule_with_validations)
            if self._is_rule_set_valid(rule_with_validations, is_browser_printed):
                return rule_with_validations
        return None

    def _build_success_result(self, rule_with_validations):
        result = self.create_validation_results_dictionary(valid_state=ValidStates.STATE_PASS, message_code=MessageCode.MSG_VALID_FILE)
        result["template_rule_set_validation_results"] = [rule_with_validations]
        return self._finalize_result(result)

    def _find_date_override_rule_set(self, rule_sets, metadata):
        for rule_with_validations in rule_sets:
            if self.date_override_rule.apply(rule_with_validations, metadata):
                return rule_with_validations
        return None

    def _build_date_override_result(self, rule_with_validations):
        result = self.create_validation_results_dictionary(
            valid_state=ValidStates.STATE_FDR,
            message_code=MessageCode.MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO,
        )
        result["template_rule_set_validation_results"] = [rule_with_validations]
        return self._finalize_result(result)

    def _has_browser_printed_rule_set(self, rule_sets):
        return any(BrowserPrintedDetector.is_browser_printed_metadata(rule_set) for rule_set in rule_sets)

    def _build_unknown_template_result(self, rule_sets):
        result = self.create_validation_results_dictionary(
            valid_state=ValidStates.STATE_FDR,
            message_code=MessageCode.MSG_UNKNOWN_TEMPLATE_TYPE,
        )
        result["template_rule_set_validation_results"] = rule_sets
        return self._finalize_result(result)

    def _build_failure_result(self, rule_sets):
        message_code = MessageCode.MSG_INVALID_FILE
        valid_state = ValidStates.STATE_FAIL
        if self._has_browser_printed_rule_set(rule_sets):
            message_code = MessageCode.MSG_BROWSER_PRINTED_DOCUMENT
            valid_state = ValidStates.STATE_FDR

        result = self.create_validation_results_dictionary(valid_state=valid_state, message_code=message_code)
        result["template_rule_set_validation_results"] = rule_sets
        return self._finalize_result(result)

    def _build_invalid_result(self, rule_sets):
        result = self.create_validation_results_dictionary(message_code=MessageCode.MSG_INVALID_FILE)
        result["template_rule_set_validation_results"] = rule_sets
        return self._finalize_result(result)

    def _build_unknown_result(self, rule_sets):
        logging.warning(
            "FraudDetector fell through to unknown result for template '%s' with rule states: %s",
            self.template_type,
            self._summarize_rule_set_states(rule_sets),
        )
        result = self.create_validation_results_dictionary(
            valid_state=ValidStates.STATE_FDR,
            message_code=MessageCode.MSG_FURTHER_DOCUMENTATION_REQUIRED,
        )
        result["template_rule_set_validation_results"] = self._sort_unknown_result_rule_sets(rule_sets)
        return self._finalize_result(result)

    def _summarize_rule_set_states(self, rule_sets):
        summarized_rule_sets = []
        for rule_set in rule_sets:
            summarized_rule_sets.append(
                {
                    "template": rule_set.get("template", {}).get("valid"),
                    "producer": rule_set.get("producer", {}).get("valid"),
                    "creator": rule_set.get("creator", {}).get("valid"),
                    "fonts": rule_set.get("fonts", {}).get("valid"),
                    "dates": rule_set.get("dates", {}).get("valid"),
                    "file_size": rule_set.get("file_size", {}).get("valid"),
                }
            )
        return summarized_rule_sets

    def _sort_unknown_result_rule_sets(self, rule_sets):
        return sorted(rule_sets, key=self._get_unknown_result_sort_key)

    def _get_unknown_result_sort_key(self, rule_set):
        return tuple(self._get_unknown_result_field_rank(rule_set, field_name) for field_name in self._unknown_result_sort_fields)

    def _get_unknown_result_field_rank(self, rule_set, field_name):
        valid_state = rule_set.get(field_name, {}).get("valid")
        return self._unknown_result_state_rank.get(valid_state, self._unknown_result_state_rank[ValidStates.STATE_FAIL])

    def _set_not_applicable_validation(self, rule):
        rule["valid"] = self._na_valid_state
        rule["validation_message_code"] = MessageCode.MSG_NOT_APPLICABLE

    def _is_rule_set_valid(self, rule_with_validations, is_browser_printed):
        if not all_valid_not_fail(rule_with_validations):
            return False

        if not is_browser_printed:
            return True

        return self._is_browser_printed_rule_set_valid(rule_with_validations)

    def _is_browser_printed_rule_set_valid(self, rule_with_validations):
        fonts_valid = rule_with_validations.get("fonts", {}).get("valid")
        file_size_valid = rule_with_validations.get("file_size", {}).get("valid")
        return fonts_valid == ValidStates.STATE_PASS and file_size_valid == ValidStates.STATE_PASS

    def _create_image_empty_rule_set_with_metadata(self, metadata):
        image_rule_set = self.rule_set_factory.create_empty_rule_set(self.template_type)

        image_rule_set["template"].pop("name", None)
        image_rule_set["template"]["actual"] = metadata.get("template", self.template_type)
        self._set_not_applicable_validation(image_rule_set["template"])

        image_rule_set["producer"].pop("name", None)
        image_rule_set["producer"]["actual"] = metadata.get("producer", "")
        self._set_not_applicable_validation(image_rule_set["producer"])

        image_rule_set["creator"].pop("name", None)
        image_rule_set["creator"]["actual"] = metadata.get("creator", "")
        self._set_not_applicable_validation(image_rule_set["creator"])

        image_rule_set["author"].pop("name", None)
        image_rule_set["author"]["actual"] = metadata.get("author", "")
        self._set_not_applicable_validation(image_rule_set["author"])

        image_rule_set["file_size"].pop("algorithm", None)
        image_rule_set["file_size"]["actual"] = metadata.get("file_size", 0)
        self._set_not_applicable_validation(image_rule_set["file_size"])

        image_rule_set["dates"]["created"].pop("state", None)
        image_rule_set["dates"]["created"]["actual"] = metadata.get("creationDate", "None")
        self._set_not_applicable_validation(image_rule_set["dates"]["created"])

        image_rule_set["dates"]["modified"].pop("state", None)
        image_rule_set["dates"]["modified"]["actual"] = metadata.get("modDate", "None")
        self._set_not_applicable_validation(image_rule_set["dates"]["modified"])

        self._set_not_applicable_validation(image_rule_set["dates"])

        return image_rule_set

    def _apply_maximum_validation_level(self, result):
        final_validation_results = result.get("final_validation_results", {})
        current_valid_state = final_validation_results.get("valid")
        maximum_validation_level = self._get_result_maximum_validation_level(result)
        if maximum_validation_level is None:
            return result

        clamped_valid_state = self._get_lower_validation_state(current_valid_state, maximum_validation_level)
        if clamped_valid_state == current_valid_state:
            return result

        final_validation_results["valid"] = clamped_valid_state
        final_validation_results["validation_message_code"] = self._get_maximum_validation_level_message_code()
        return result

    def _get_maximum_validation_level_message_code(self):
        normalized_template_type = normalize_template_name(self.template_type or "")
        if normalized_template_type in {"no", "unknown"}:
            return MessageCode.MSG_FURTHER_VALIDATION_REQUIRED_UNKNOWN_TEMPLATE
        return MessageCode.MSG_FURTHER_VALIDATION_REQUIRED_UNTRUSTED_TEMPLATE

    def _finalize_result(self, result):
        result = self._apply_maximum_validation_level(result)
        return self._apply_font_failure_override(result)

    def _apply_font_failure_override(self, result):
        selected_rule_set = result.get("template_rule_set_validation_results", [{}])[0]
        if BrowserPrintedDetector.is_browser_printed_metadata(selected_rule_set):
            return result

        # Keep FDR/review outcomes as FDR. Font mismatch alone should not escalate
        # unknown/unverifiable documents to Fail (false positives).
        final_validation_results = result.get("final_validation_results", {})
        if final_validation_results.get("valid") == ValidStates.STATE_FDR:
            return result

        fonts_valid = selected_rule_set.get("fonts", {}).get("valid")
        if fonts_valid != ValidStates.STATE_FAIL:
            return result

        final_validation_results["valid"] = ValidStates.STATE_FAIL
        return result

    def _get_result_maximum_validation_level(self, result):
        maximum_validation_levels = []
        for rule_set in result.get("template_rule_set_validation_results", []):
            maximum_validation_level = rule_set.get("template", {}).get("maximum_validation_level")
            if maximum_validation_level is not None:
                maximum_validation_levels.append(maximum_validation_level)

        if not maximum_validation_levels:
            return None

        return min(maximum_validation_levels, key=self._validation_state_order.get)

    def _get_lower_validation_state(self, left_state, right_state):
        return min((left_state, right_state), key=self._validation_state_order.get)
