import json
import logging
import re
from datetime import datetime
from pathlib import Path


class LegacyMetadataConverter:
    SENTINEL_VALUES = {"", "no", "none", "null"}
    OPTION_FONT_MULTIPLICITY = 9999
    REQUIRED_FONT_MULTIPLICITY = 1

    def __init__(
        self,
        bank_reference_dir,
        income_reference_dir,
        out_dir,
        report_path=None,
        verbose=False,
    ):
        self.bank_reference_dir = Path(bank_reference_dir)
        self.income_reference_dir = Path(income_reference_dir)
        self.out_dir = Path(out_dir)
        self.report_path = Path(report_path) if report_path else self.out_dir / "conversion_report.json"
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def convert_from_file_paths(self, bank_source, income_source):
        bank_source_path = Path(bank_source)
        income_source_path = Path(income_source)
        bank_rows = self._load_rows(bank_source_path)
        income_rows = self._load_rows(income_source_path)

        bank_report = self._convert_dataset(
            dataset_name="bank",
            rows=bank_rows,
            reference_dir=self.bank_reference_dir,
            output_dir=self.out_dir / "BankStatementsRuleJson",
        )
        income_report = self._convert_dataset(
            dataset_name="income",
            rows=income_rows,
            reference_dir=self.income_reference_dir,
            output_dir=self.out_dir / "EarningStatementsRuleJson",
        )

        report = {
            "generated_at_utc": datetime.utcnow().isoformat() + "Z",
            "settings": {
                "bank_source": str(bank_source_path),
                "income_source": str(income_source_path),
                "bank_ref_dir": str(self.bank_reference_dir),
                "income_ref_dir": str(self.income_reference_dir),
                "out_dir": str(self.out_dir),
                "report_path": str(self.report_path),
            },
            "datasets": {
                "bank": bank_report,
                "income": income_report,
            },
            "overall": {
                "rows_processed": bank_report["rows_processed"] + income_report["rows_processed"],
                "files_written": bank_report["files_written"] + income_report["files_written"],
                "present_present_rows": bank_report["present_present"]["count"] + income_report["present_present"]["count"],
            },
        }
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, indent=4) + "\n", encoding="utf-8")
        return report

    def convert_template_from_file_path(self, source, template_name, output_path):
        source_path = Path(source)
        output_path = Path(output_path)
        rows = self._load_rows(source_path)
        target_template = self._normalize(template_name)
        matched_rows = [row for row in rows if self._normalize(row.get("template")) == target_template]

        converted_rules = []
        parse_fallbacks = {
            "created_date_unparseable": 0,
            "modified_date_unparseable": 0,
            "file_size_unparseable": 0,
            "font_empty_tokens": 0,
            "font_no_valid_tokens": 0,
        }

        for row in matched_rows:
            converted_rule, row_fallbacks = self._convert_row(row, target_template)
            converted_rules.append(converted_rule)
            for key in parse_fallbacks:
                parse_fallbacks[key] += row_fallbacks[key]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(converted_rules, indent=4) + "\n", encoding="utf-8")

        return {
            "source": str(source_path),
            "template": target_template,
            "rows_matched": len(matched_rows),
            "output_path": str(output_path),
            "parse_fallbacks": parse_fallbacks,
        }

    def _convert_dataset(self, dataset_name, rows, reference_dir, output_dir):
        reference_stems = self._get_reference_stems(reference_dir)
        normalized_reference_map = self._build_normalized_reference_map(reference_stems)
        output_dir.mkdir(parents=True, exist_ok=True)
        self._clear_existing_generated_files(output_dir)

        rules_by_file = {}
        unresolved_template_to_file = {}
        reserved_file_names = set(reference_stems)
        parse_fallbacks = {
            "created_date_unparseable": 0,
            "modified_date_unparseable": 0,
            "file_size_unparseable": 0,
            "font_empty_tokens": 0,
            "font_no_valid_tokens": 0,
        }
        match_counts = {
            "exact": 0,
            "normalized": 0,
            "created_new": 0,
            "sentinel_to_unknown": 0,
        }
        present_present_templates = set()
        present_present_count = 0

        for row_index, row in enumerate(rows):
            raw_template = self._normalize(row.get("template"))
            file_stem, rule_template_name, match_type = self._resolve_output_file_stem(
                raw_template,
                reference_stems,
                normalized_reference_map,
                unresolved_template_to_file,
                reserved_file_names,
            )
            match_counts[match_type] += 1

            converted_rule, row_fallbacks = self._convert_row(row, rule_template_name)
            for key in parse_fallbacks:
                parse_fallbacks[key] += row_fallbacks[key]

            if (
                converted_rule["dates"]["created"]["state"] == "Present"
                and converted_rule["dates"]["modified"]["state"] == "Present"
            ):
                present_present_count += 1
                present_present_templates.add(converted_rule["template"]["name"])
                self.logger.warning(
                    "Detected Present/Present date rule in %s row %s for template '%s'",
                    dataset_name,
                    row_index,
                    converted_rule["template"]["name"],
                )

            if file_stem not in rules_by_file:
                rules_by_file[file_stem] = []
            rules_by_file[file_stem].append(converted_rule)

        for file_stem in sorted(rules_by_file):
            output_path = output_dir / f"{file_stem}.json"
            output_path.write_text(json.dumps(rules_by_file[file_stem], indent=4) + "\n", encoding="utf-8")

        return {
            "rows_processed": len(rows),
            "files_written": len(rules_by_file),
            "match_counts": match_counts,
            "present_present": {
                "count": present_present_count,
                "templates": sorted(present_present_templates),
            },
            "parse_fallbacks": parse_fallbacks,
            "output_files": sorted(f"{file_stem}.json" for file_stem in rules_by_file),
            "reference_dir": str(reference_dir),
            "output_dir": str(output_dir),
        }

    def _convert_row(self, row, template_name):
        created_state, created_fallback = self._normalize_created_state(row.get("created"))
        modified_state, modified_fallback = self._normalize_modified_state(row.get("modified"))
        file_size, file_size_fallback = self._parse_file_size(row.get("file_size"))
        required_fonts, optional_fonts, font_fallbacks = self._parse_fonts(row.get("font"))

        converted_rule = {
            "template": {"name": template_name},
            "producer": {"name": self._normalize_single_value_pattern(row.get("producer"))},
            "creator": {"name": self._normalize_single_value_pattern(row.get("creator"))},
            "file_size": file_size,
            "fonts": {
                "required_fonts": required_fonts,
                "optional_fonts": optional_fonts,
            },
            "dates": {
                "created": {"state": created_state},
                "modified": modified_state,
            },
        }

        return converted_rule, {
            "created_date_unparseable": 1 if created_fallback else 0,
            "modified_date_unparseable": 1 if modified_fallback else 0,
            "file_size_unparseable": 1 if file_size_fallback else 0,
            "font_empty_tokens": font_fallbacks["font_empty_tokens"],
            "font_no_valid_tokens": font_fallbacks["font_no_valid_tokens"],
        }

    def _normalize_created_state(self, value):
        raw = self._normalize(value)
        lowered = raw.lower()

        if lowered in self.SENTINEL_VALUES:
            return "None", False
        if lowered == "present":
            return "Present", False
        if raw.startswith("D:"):
            return raw, False

        normalized_date = self._try_parse_legacy_date(raw)
        if normalized_date:
            return normalized_date, False
        return raw, True

    def _normalize_modified_state(self, value):
        raw = self._normalize(value)
        lowered = raw.lower()

        if lowered in self.SENTINEL_VALUES:
            return {"state": "None"}, False
        if lowered == "present":
            return {"state": "Present"}, False
        if lowered == "equal":
            return {"state": "Equal"}, False
        if lowered == "greater":
            return {"state": "Greater"}, False
        if lowered == "lesser":
            return {"state": "Lesser"}, False
        if raw.startswith("D:"):
            return {"state": raw}, False

        hour_match = re.match(r"^\s*(\d+)\s*hrs?\s*$", raw, re.IGNORECASE)
        if hour_match:
            hour_count = int(hour_match.group(1))
            return {"state": "Equal", "duration": 0, "tolerance": hour_count * 3600}, False

        normalized_date = self._try_parse_legacy_date(raw)
        if normalized_date:
            return {"state": normalized_date}, False
        return {"state": raw}, True

    def _parse_file_size(self, value):
        raw = self._normalize(value)
        lowered = raw.lower()
        if lowered in self.SENTINEL_VALUES:
            return {"algorithm": "Unknown"}, False

        match = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", raw)
        if not match:
            return {"algorithm": "Unknown"}, True

        min_size = int(match.group(1))
        max_size = int(match.group(2))
        if min_size > max_size:
            return {"algorithm": "Unknown"}, True
        return {"algorithm": "Constant", "min": min_size, "max": max_size}, False

    def _parse_fonts(self, value):
        raw = self._normalize(value)
        lowered = raw.lower()
        if lowered in self.SENTINEL_VALUES or lowered == "allandnone":
            return [], [], {"font_empty_tokens": 0, "font_no_valid_tokens": 0}

        required_fonts = []
        optional_fonts = []
        empty_tokens = 0

        for token in [item.strip() for item in raw.split(";")]:
            if not token:
                empty_tokens += 1
                continue

            is_optional = "(o)" in token.lower()
            cleaned_font_name = re.sub(r"\(\s*[oO]\s*\)", "", token).strip()
            cleaned_font_name = self._normalize_font_name(cleaned_font_name)
            if not cleaned_font_name:
                empty_tokens += 1
                continue

            font_rule = {
                "name": cleaned_font_name,
                "type": "",
                "encoding": "",
                "multiplicity": (
                    self.OPTION_FONT_MULTIPLICITY if is_optional else self.REQUIRED_FONT_MULTIPLICITY
                ),
            }
            if is_optional:
                optional_fonts.append(font_rule)
            else:
                required_fonts.append(font_rule)

        no_valid_tokens = 0
        if not required_fonts and not optional_fonts:
            no_valid_tokens = 1

        return required_fonts, optional_fonts, {
            "font_empty_tokens": empty_tokens,
            "font_no_valid_tokens": no_valid_tokens,
        }

    def _normalize_single_value_pattern(self, value):
        raw = self._normalize(value)
        if raw.lower() in self.SENTINEL_VALUES:
            return ""
        # Single-value template rules in this repo are prefix regexes.
        return rf"^{self._escape_prefix_literal(raw)}.*"

    def _resolve_output_file_stem(
        self,
        raw_template,
        reference_stems,
        normalized_reference_map,
        unresolved_template_to_file,
        reserved_file_names,
    ):
        lowered_template = raw_template.lower()
        if lowered_template in self.SENTINEL_VALUES:
            return "Unknown", "Unknown", "sentinel_to_unknown"

        if raw_template in reference_stems:
            return raw_template, raw_template, "exact"

        normalized_template = self._normalize_for_match(raw_template)
        if normalized_template in normalized_reference_map:
            return normalized_reference_map[normalized_template], raw_template, "normalized"

        if raw_template in unresolved_template_to_file:
            return unresolved_template_to_file[raw_template], raw_template, "created_new"

        sanitized = self._sanitize_file_stem(raw_template)
        candidate = sanitized
        suffix = 1
        while candidate in reserved_file_names:
            suffix += 1
            candidate = f"{sanitized}_{suffix}"

        reserved_file_names.add(candidate)
        unresolved_template_to_file[raw_template] = candidate
        return candidate, raw_template, "created_new"

    def _get_reference_stems(self, reference_dir):
        stems = set()
        for path in Path(reference_dir).glob("*.json"):
            if path.name == "__init__.py":
                continue
            stems.add(path.stem)
        return stems

    def _clear_existing_generated_files(self, output_dir):
        for path in Path(output_dir).glob("*.json"):
            path.unlink()

    def _build_normalized_reference_map(self, reference_stems):
        normalized_map = {}
        for stem in sorted(reference_stems):
            normalized_stem = self._normalize_for_match(stem)
            if normalized_stem not in normalized_map:
                normalized_map[normalized_stem] = stem
        return normalized_map

    def _load_rows(self, source_path):
        raw_content = source_path.read_text(encoding="utf-8")
        parsed = json.loads(raw_content)
        if not isinstance(parsed, list):
            raise ValueError(f"Expected JSON array in {source_path}")
        return parsed

    def _try_parse_legacy_date(self, raw_value):
        for date_format in ("%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(raw_value, date_format)
                return f"D:{parsed.strftime('%Y%m%d')}000000"
            except ValueError:
                continue

        loose_date_match = re.match(r"^\s*(\d{1,2})[-/](\d{1,2})[-/](\d{4})\s*$", raw_value)
        if loose_date_match:
            month, day, year = [int(value) for value in loose_date_match.groups()]
            return f"D:{year:04d}{month:02d}{day:02d}000000"
        return None

    def _sanitize_file_stem(self, template_name):
        normalized_spaces = " ".join(template_name.strip().split())
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", normalized_spaces).rstrip(". ")
        return sanitized if sanitized else "Unknown"

    def _normalize_for_match(self, value):
        return re.sub(r"[^a-z0-9]", "", value.lower())

    def _normalize(self, value):
        return str(value or "").strip()

    def _normalize_font_name(self, value):
        cleaned = re.sub(r"\s*,\s*", ",", value)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _escape_prefix_literal(self, value):
        return re.escape(value).replace(r"\ ", " ")
