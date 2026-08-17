import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from src.GeneratedRulesetComparator import GeneratedRulesetComparator
from src.LegacyMetadataConverter import LegacyMetadataConverter
from src.TemplateJsonCanonicalizer import TemplateJsonCanonicalizer


class TemplateJsonUpdaterFromReport:
    DATASET_DIRS = GeneratedRulesetComparator.DATASET_CONFIG

    def __init__(
        self,
        comparison_report_path,
        bank_reference_dir=None,
        income_reference_dir=None,
        generated_root=None,
        out_report=None,
        dry_run=False,
    ):
        self.comparison_report_path = Path(comparison_report_path)
        self.dry_run = dry_run
        self._canonicalizer = TemplateJsonCanonicalizer()
        self._comparison_report = self._load_json(self.comparison_report_path)
        settings = self._comparison_report.get("settings", {})
        self.generated_root = Path(generated_root or settings.get("generated_root", self.comparison_report_path.parent))
        self.bank_reference_dir = Path(bank_reference_dir or settings["bank_ref_dir"])
        self.income_reference_dir = Path(income_reference_dir or settings["income_ref_dir"])
        self.out_report = Path(out_report) if out_report else self.generated_root / "template_update_report.json"
        self._comparator = GeneratedRulesetComparator(
            generated_root=self.generated_root,
            bank_reference_dir=self.bank_reference_dir,
            income_reference_dir=self.income_reference_dir,
        )
        self._sanitizer = LegacyMetadataConverter(
            bank_reference_dir=self.bank_reference_dir,
            income_reference_dir=self.income_reference_dir,
            out_dir=self.generated_root,
        )

    def apply(self):
        datasets = {
            "bank": self._apply_dataset("bank", self.bank_reference_dir),
            "income": self._apply_dataset("income", self.income_reference_dir),
        }

        report = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "comparison_report_path": str(self.comparison_report_path),
            "dry_run": self.dry_run,
            "settings": {
                "generated_root": str(self.generated_root),
                "bank_ref_dir": str(self.bank_reference_dir),
                "income_ref_dir": str(self.income_reference_dir),
                "out_report": str(self.out_report),
            },
            "datasets": datasets,
            "overall": {
                "updated_existing_files": sum(data["summary"]["updated_existing_files"] for data in datasets.values()),
                "created_new_files": sum(data["summary"]["created_new_files"] for data in datasets.values()),
                "flagged_reference_only_rules": sum(data["summary"]["flagged_reference_only_rules"] for data in datasets.values()),
                "appended_rules": sum(data["summary"]["appended_rules"] for data in datasets.values()),
                "filled_scalar_gaps": sum(data["summary"]["filled_scalar_gaps"] for data in datasets.values()),
                "files_written": sum(data["summary"]["files_written"] for data in datasets.values()),
            },
        }

        self.out_report.parent.mkdir(parents=True, exist_ok=True)
        self.out_report.write_text(json.dumps(report, indent=4) + "\n", encoding="utf-8")
        return report

    def _apply_dataset(self, dataset_name, reference_dir):
        generated_dir = Path(self._comparison_report["datasets"][dataset_name]["generated_dir"])
        reference_files = {path.name: self._load_rules(path) for path in Path(reference_dir).glob("*.json")}
        generated_files = {path.name: self._load_rules(path) for path in Path(generated_dir).glob("*.json")}

        reference_template_to_file = self._build_template_to_file_index(reference_files)
        normalized_reference_template_to_file = self._build_normalized_template_to_file_index(reference_template_to_file)
        generated_template_to_rules = self._build_generated_template_index(generated_files)
        pending_templates = []

        for template_name, generated_info in sorted(generated_template_to_rules.items()):
            target_reference_file = reference_template_to_file.get(template_name)
            if not target_reference_file:
                target_reference_file = normalized_reference_template_to_file.get(
                    self._comparator._normalize_for_match(template_name)
                )
            pending_templates.append(
                {
                    "template_name": template_name,
                    "generated_file": generated_info["source_file"],
                    "target_reference_file": target_reference_file,
                    "generated_rules": generated_info["rules"],
                }
            )

        changed_files = {}
        file_actions = []
        existing_file_flags = self._build_reference_only_flags(dataset_name, generated_template_to_rules, reference_files)

        for template_info in pending_templates:
            action = self._apply_template_update(
                reference_dir=reference_dir,
                reference_files=reference_files,
                template_info=template_info,
                changed_files=changed_files,
            )
            file_actions.append(action)

        files_written = 0
        if not self.dry_run:
            for file_name, rules in changed_files.items():
                output_path = Path(reference_dir) / file_name
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(self._canonicalizer.dumps_rules(rules, sort_rules=True), encoding="utf-8")
                files_written += 1
        else:
            files_written = len(changed_files)

        summary = {
            "updated_existing_files": sum(1 for item in file_actions if item["action"] == "updated_existing_file"),
            "created_new_files": sum(1 for item in file_actions if item["action"] == "created_new_file"),
            "flagged_reference_only_rules": sum(len(item["flagged_reference_only_rules"]) for item in file_actions)
            + sum(len(item["flagged_reference_only_rules"]) for item in existing_file_flags),
            "appended_rules": sum(item["appended_rules"] for item in file_actions),
            "filled_scalar_gaps": sum(item["filled_scalar_gaps"] for item in file_actions),
            "files_written": files_written,
        }

        return {
            "reference_dir": str(reference_dir),
            "generated_dir": str(generated_dir),
            "summary": summary,
            "file_actions": file_actions,
            "reference_only_flags": existing_file_flags,
        }

    def _apply_template_update(self, reference_dir, reference_files, template_info, changed_files):
        template_name = template_info["template_name"]
        generated_rules = [self._normalize_generated_rule(rule) for rule in template_info["generated_rules"]]
        target_reference_file = template_info["target_reference_file"]

        if target_reference_file:
            current_rules = deepcopy(changed_files.get(target_reference_file, reference_files[target_reference_file]))
            reference_rules_for_template = [deepcopy(rule) for rule in current_rules if rule.get("template", {}).get("name") == template_name]
            other_rules = [deepcopy(rule) for rule in current_rules if rule.get("template", {}).get("name") != template_name]

            merged_rules, action_details = self._merge_template_rules(
                template_name=template_name,
                generated_rules=generated_rules,
                reference_rules=reference_rules_for_template,
                file_rule_pool=current_rules,
            )
            changed_files[target_reference_file] = other_rules + merged_rules
            changed_files[target_reference_file] = self._comparator._sort_rules(
                [self._comparator._normalize_rule(rule) for rule in changed_files[target_reference_file]]
            )

            return {
                "template_name": template_name,
                "action": "updated_existing_file",
                "generated_file": template_info["generated_file"],
                "reference_file": target_reference_file,
                **action_details,
            }

        new_file_name = self._allocate_new_file_name(reference_dir, reference_files, changed_files, template_name)
        created_rules = self._build_new_template_rules(generated_rules, existing_rules_in_file=[])
        changed_files[new_file_name] = self._comparator._sort_rules([self._comparator._normalize_rule(rule) for rule in created_rules])

        return {
            "template_name": template_name,
            "action": "created_new_file",
            "generated_file": template_info["generated_file"],
            "reference_file": new_file_name,
            "appended_rules": len(created_rules),
            "filled_scalar_gaps": 0,
            "kept_reference_fonts": 0,
            "flagged_reference_only_rules": [],
        }

    def _merge_template_rules(self, template_name, generated_rules, reference_rules, file_rule_pool):
        generated_sorted = self._comparator._sort_rules([self._comparator._normalize_rule(rule) for rule in generated_rules])
        reference_sorted = self._comparator._sort_rules([self._comparator._normalize_rule(rule) for rule in reference_rules])

        merged_rules = []
        filled_scalar_gaps = 0
        kept_reference_fonts = 0
        min_length = min(len(generated_sorted), len(reference_sorted))

        for index in range(min_length):
            merged_rule, merge_stats = self._merge_paired_rule(reference_sorted[index], generated_sorted[index])
            merged_rules.append(merged_rule)
            filled_scalar_gaps += merge_stats["filled_scalar_gaps"]
            kept_reference_fonts += 1 if merge_stats["kept_reference_fonts"] else 0

        appended_rules = []
        if len(generated_sorted) > min_length:
            appended_rules = self._build_new_template_rules(generated_sorted[min_length:], existing_rules_in_file=file_rule_pool)
            merged_rules.extend(appended_rules)

        flagged_reference_only_rules = [self._serialize(rule) for rule in reference_sorted[min_length:]]
        merged_rules.extend(reference_sorted[min_length:])
        merged_rules = self._comparator._sort_rules([self._comparator._normalize_rule(rule) for rule in merged_rules])

        return merged_rules, {
            "appended_rules": len(appended_rules),
            "filled_scalar_gaps": filled_scalar_gaps,
            "kept_reference_fonts": kept_reference_fonts,
            "flagged_reference_only_rules": flagged_reference_only_rules,
        }

    def _merge_paired_rule(self, reference_rule, generated_rule):
        merged = deepcopy(reference_rule)
        filled_scalar_gaps = 0

        generated_rule = self._normalize_generated_rule(generated_rule)
        merged, file_size_gap_fills = self._merge_file_size(merged, generated_rule)
        filled_scalar_gaps += file_size_gap_fills

        scalar_paths = [
            ("producer", "name"),
            ("creator", "name"),
            ("dates", "created", "state"),
            ("dates", "modified", "state"),
            ("dates", "modified", "duration"),
            ("dates", "modified", "tolerance"),
        ]
        for path in scalar_paths:
            filled_scalar_gaps += self._fill_missing_scalar(merged, generated_rule, path)

        keep_reference_fonts = self._reference_has_font_metadata(reference_rule)
        if not keep_reference_fonts and self._fonts_block_is_empty(reference_rule.get("fonts")):
            generated_fonts = deepcopy(generated_rule.get("fonts", {"required_fonts": [], "optional_fonts": []}))
            merged["fonts"] = self._comparator._normalize_rule({"fonts": generated_fonts}).get("fonts", generated_fonts)

        return self._comparator._normalize_rule(merged), {
            "filled_scalar_gaps": filled_scalar_gaps,
            "kept_reference_fonts": keep_reference_fonts,
        }

    def _build_new_template_rules(self, generated_rules, existing_rules_in_file):
        reference_font_index = self._build_exact_font_index(existing_rules_in_file)
        created_rules = []
        for rule in generated_rules:
            new_rule = deepcopy(self._normalize_generated_rule(rule))
            new_rule["fonts"] = self._backfill_font_metadata(new_rule.get("fonts", {}), reference_font_index)
            created_rules.append(self._comparator._normalize_rule(new_rule))
        return created_rules

    def _build_reference_only_flags(self, dataset_name, generated_template_to_rules, reference_files):
        flags = []
        for file_name, rules in sorted(reference_files.items()):
            template_names = sorted({rule.get("template", {}).get("name", "") for rule in rules})
            unmatched_templates = [name for name in template_names if name and name not in generated_template_to_rules]
            if unmatched_templates:
                flags.append(
                    {
                        "reference_file": file_name,
                        "dataset": dataset_name,
                        "flagged_reference_only_rules": unmatched_templates,
                    }
                )
        return flags

    def _merge_file_size(self, merged_rule, generated_rule):
        filled = 0
        merged_file_size = merged_rule.setdefault("file_size", {})
        generated_file_size = generated_rule.get("file_size", {})

        if self._is_missing(merged_file_size.get("algorithm")) and not self._is_missing(generated_file_size.get("algorithm")):
            if not self._is_missing(merged_file_size.get("min")) or not self._is_missing(merged_file_size.get("max")):
                merged_file_size["algorithm"] = generated_file_size.get("algorithm")
                filled += 1

        for key in ("min", "max"):
            if self._is_missing(merged_file_size.get(key)) and not self._is_missing(generated_file_size.get(key)):
                merged_file_size[key] = generated_file_size.get(key)
                filled += 1

        return merged_rule, filled

    def _fill_missing_scalar(self, merged_rule, generated_rule, path):
        merged_value = self._get_nested(merged_rule, path)
        generated_value = self._get_nested(generated_rule, path)
        if self._is_missing(merged_value) and not self._is_missing(generated_value):
            self._set_nested(merged_rule, path, deepcopy(generated_value))
            return 1
        return 0

    def _normalize_generated_rule(self, rule):
        normalized_rule = deepcopy(rule)
        modified = normalized_rule.setdefault("dates", {}).setdefault("modified", {})
        created = normalized_rule.setdefault("dates", {}).setdefault("created", {})
        if created.get("state") == "Present" and modified.get("state") == "Present":
            modified["state"] = "Equal"
            modified.pop("duration", None)
            modified.pop("tolerance", None)
        return self._comparator._normalize_rule(normalized_rule)

    def _reference_has_font_metadata(self, rule):
        fonts = rule.get("fonts", {})
        for section in ("required_fonts", "optional_fonts"):
            for font in fonts.get(section, []):
                if font.get("type") or font.get("encoding"):
                    return True
        return False

    def _fonts_block_is_empty(self, fonts):
        if not fonts:
            return True
        return not fonts.get("required_fonts") and not fonts.get("optional_fonts")

    def _build_exact_font_index(self, rules):
        font_index = {}
        for rule in rules:
            for section in ("required_fonts", "optional_fonts"):
                for font in rule.get("fonts", {}).get(section, []):
                    name = font.get("name")
                    if name and name not in font_index:
                        font_index[name] = {
                            "type": font.get("type", ""),
                            "encoding": font.get("encoding", ""),
                        }
        return font_index

    def _backfill_font_metadata(self, fonts, reference_font_index):
        updated_fonts = deepcopy(fonts or {"required_fonts": [], "optional_fonts": []})
        for section in ("required_fonts", "optional_fonts"):
            updated_fonts.setdefault(section, [])
            for font in updated_fonts[section]:
                match = reference_font_index.get(font.get("name"))
                if not match:
                    continue
                if self._is_missing(font.get("type")) and match.get("type"):
                    font["type"] = match["type"]
                if self._is_missing(font.get("encoding")) and match.get("encoding"):
                    font["encoding"] = match["encoding"]
        return updated_fonts

    def _build_template_to_file_index(self, files):
        index = {}
        for file_name, rules in sorted(files.items()):
            for rule in rules:
                template_name = rule.get("template", {}).get("name", "")
                if template_name and template_name not in index:
                    index[template_name] = file_name
        return index

    def _build_normalized_template_to_file_index(self, template_to_file):
        groups = {}
        for template_name, file_name in sorted(template_to_file.items()):
            normalized = self._comparator._normalize_for_match(template_name)
            groups.setdefault(normalized, set()).add(file_name)

        normalized_index = {}
        for normalized, file_names in groups.items():
            if len(file_names) == 1:
                normalized_index[normalized] = sorted(file_names)[0]
        return normalized_index

    def _build_generated_template_index(self, files):
        index = {}
        for file_name, rules in sorted(files.items()):
            for rule in rules:
                template_name = rule.get("template", {}).get("name", "")
                if not template_name:
                    continue
                index.setdefault(template_name, {"source_file": file_name, "rules": []})
                index[template_name]["rules"].append(deepcopy(rule))
        return index

    def _allocate_new_file_name(self, reference_dir, reference_files, changed_files, template_name):
        existing_names = set(reference_files) | set(changed_files)
        sanitized = self._sanitizer._sanitize_file_stem(template_name)
        candidate = f"{sanitized}.json"
        suffix = 2
        while candidate in existing_names or (Path(reference_dir) / candidate).exists():
            candidate = f"{sanitized}_{suffix}.json"
            suffix += 1
        return candidate

    def _load_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def _load_rules(self, path):
        return self._canonicalizer.load_rules(path)

    def _get_nested(self, payload, path):
        current = payload
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def _set_nested(self, payload, path, value):
        current = payload
        for key in path[:-1]:
            current = current.setdefault(key, {})
        current[path[-1]] = value

    def _is_missing(self, value):
        if value is None:
            return True
        if value == "":
            return True
        if isinstance(value, (list, dict)) and not value:
            return True
        return False

    def _serialize(self, value):
        return self._canonicalizer.serialize(value)
