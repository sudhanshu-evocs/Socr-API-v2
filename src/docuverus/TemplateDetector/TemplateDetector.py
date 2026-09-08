import re
from pathlib import Path

from docuverus.FraudDetector.MetadataExtractor import MetadataExtractor
from docuverus.RuleEvaluators.FontRuleEvaluator import get_font_name


class TemplateDetector:
    AUTO_SELECT_THRESHOLD = 60
    AUTO_SELECT_MARGIN = 6
    MAX_CANDIDATES = 3
    SIGNAL_WEIGHTS = {
        "producer": 35,
        "creator": 30,
        "fonts": 25,
        "file_size": 10,
    }
    FILENAME_HINT_WEIGHT = 8

    def __init__(self, rule_set_factory=None, metadata_extractor=None):
        self.rule_set_factory = rule_set_factory
        self.metadata_extractor = metadata_extractor or MetadataExtractor()

    def detect(self, pdf_bytes, filename=""):
        if self.rule_set_factory is None:
            raise ValueError("TemplateDetector requires a rule-set factory")

        metadata = self.metadata_extractor.extract_metadata(pdf_bytes, "")
        if metadata.get("exception"):
            return self._empty_result("The PDF metadata could not be extracted.")
        if metadata.get("image_file"):
            return self._empty_result("Image-only PDFs do not contain enough metadata for reliable template detection.")

        best_variants = {}
        for entry in self.rule_set_factory.get_all_template_rules_with_categories():
            candidate = self._score_rule(entry["rule"], entry["category"], metadata, filename)
            key = (candidate["name"], candidate["category"])
            current = best_variants.get(key)
            if current is None or candidate["confidence"] > current["confidence"]:
                best_variants[key] = candidate

        ranked_candidates = sorted(
            best_variants.values(),
            key=lambda candidate: (-candidate["confidence"], -len(candidate["name"]), candidate["name"]),
        )[: self.MAX_CANDIDATES]
        if not ranked_candidates:
            return self._empty_result("No template rules are available for detection.")

        best_candidate = ranked_candidates[0]
        second_score = ranked_candidates[1]["confidence"] if len(ranked_candidates) > 1 else 0
        margin = best_candidate["confidence"] - second_score
        auto_select = best_candidate["confidence"] >= self.AUTO_SELECT_THRESHOLD and margin >= self.AUTO_SELECT_MARGIN

        return {
            "detected": auto_select,
            "auto_select": auto_select,
            "template_name": best_candidate["name"],
            "category": best_candidate["category"],
            "document_class": self._document_class(best_candidate["category"]),
            "confidence": best_candidate["confidence"],
            "confidence_margin": margin,
            "reason": (
                "A strong, distinct metadata fingerprint matched this template."
                if auto_select
                else "The closest metadata fingerprint is not distinct enough for safe automatic selection."
            ),
            "matched_signals": best_candidate["matched_signals"],
            "candidates": ranked_candidates,
        }

    def get_template_confidences(self, file_path):
        path = Path(file_path) if isinstance(file_path, (str, Path)) else None
        pdf_bytes = path.read_bytes() if path else file_path
        result = self.detect(pdf_bytes, path.name if path else "")
        return [
            {"name": candidate["name"], "actual_confidence": candidate["confidence"]}
            for candidate in result.get("candidates", [])
        ]

    def _score_rule(self, rule, category, metadata, filename):
        score = 0.0
        matched_signals = []

        for field_name in ("producer", "creator"):
            pattern = rule.get(field_name, {}).get("name", "")
            if self._regex_matches(pattern, metadata.get(field_name, "")):
                score += self.SIGNAL_WEIGHTS[field_name]
                matched_signals.append(field_name)

        font_similarity = self._font_similarity(rule, metadata)
        if font_similarity:
            score += self.SIGNAL_WEIGHTS["fonts"] * font_similarity
            matched_signals.append("fonts")

        if self._file_size_matches(rule, metadata):
            score += self.SIGNAL_WEIGHTS["file_size"]
            matched_signals.append("file_size")

        template_name = rule.get("template", {}).get("name", "Unknown")
        if filename and self._filename_contains_template(filename, template_name):
            score += self.FILENAME_HINT_WEIGHT
            matched_signals.append("filename_hint")

        return {
            "name": template_name,
            "category": category,
            "document_class": self._document_class(category),
            "confidence": round(min(100, score)),
            "matched_signals": matched_signals,
        }

    @staticmethod
    def _regex_matches(pattern, actual):
        if not pattern or pattern in {"*", "Unknown"}:
            return False
        try:
            return re.search(pattern, actual or "") is not None
        except (re.error, TypeError):
            return False

    @staticmethod
    def _font_similarity(rule, metadata):
        font_rules = rule.get("fonts", {})
        expected_rules = font_rules.get("required_fonts", []) or font_rules.get("optional_fonts", [])
        expected_names = {get_font_name(font.get("name", "")) for font in expected_rules if font.get("name")}
        if not expected_names:
            return 0.0

        actual_names = {
            get_font_name(font.get("name", ""))
            for font in metadata.get("fonts", [])
            if font.get("name")
        }
        return len(expected_names.intersection(actual_names)) / len(expected_names)

    @staticmethod
    def _file_size_matches(rule, metadata):
        file_size_rule = rule.get("file_size", {})
        algorithm = file_size_rule.get("algorithm", "Constant")
        try:
            actual_size = float(metadata.get("file_size", 0))
            if algorithm == "Constant":
                return float(file_size_rule["min"]) <= actual_size <= float(file_size_rule["max"])
            if algorithm == "Linear":
                paystub_count = float(metadata.get("paystub_count", 0))
                minimum = (
                    float(file_size_rule["min_slope"]) * paystub_count
                    + float(file_size_rule["min"])
                    - float(file_size_rule["min_slope"])
                )
                maximum = (
                    float(file_size_rule["max_slope"]) * paystub_count
                    + float(file_size_rule["max"])
                    - float(file_size_rule["max_slope"])
                )
                return minimum <= actual_size <= maximum
        except (KeyError, TypeError, ValueError):
            return False
        return False

    @staticmethod
    def _filename_contains_template(filename, template_name):
        filename_words = re.sub(r"[^a-z0-9]+", " ", Path(filename).stem.casefold()).strip()
        template_words = re.sub(r"[^a-z0-9]+", " ", template_name.casefold()).strip()
        if len(template_words) < 3:
            return False
        pattern = r"\b" + r"\s+".join(re.escape(word) for word in template_words.split()) + r"\b"
        return re.search(pattern, filename_words) is not None

    @staticmethod
    def _document_class(category):
        return "Paystub / Earning Statement" if category == "Paystubs & Earnings" else "Bank Statement"

    @staticmethod
    def _empty_result(reason):
        return {
            "detected": False,
            "auto_select": False,
            "template_name": None,
            "category": None,
            "document_class": None,
            "confidence": 0,
            "confidence_margin": 0,
            "reason": reason,
            "matched_signals": [],
            "candidates": [],
        }
