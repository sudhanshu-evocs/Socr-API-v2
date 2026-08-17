import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src.TemplateJsonCanonicalizer import TemplateJsonCanonicalizer


class GeneratedRulesetComparator:
    DATASET_CONFIG = {
        "bank": "BankStatementsRuleJson",
        "income": "EarningStatementsRuleJson",
    }

    def __init__(self, generated_root, bank_reference_dir, income_reference_dir, report_path=None):
        self.generated_root = Path(generated_root)
        self.bank_reference_dir = Path(bank_reference_dir)
        self.income_reference_dir = Path(income_reference_dir)
        self.report_path = Path(report_path) if report_path else self.generated_root / "comparison_report.json"
        self._canonicalizer = TemplateJsonCanonicalizer()

    def compare(self):
        datasets = {
            "bank": self._compare_dataset(
                generated_dir=self.generated_root / self.DATASET_CONFIG["bank"],
                reference_dir=self.bank_reference_dir,
            ),
            "income": self._compare_dataset(
                generated_dir=self.generated_root / self.DATASET_CONFIG["income"],
                reference_dir=self.income_reference_dir,
            ),
        }

        overall = {
            "matched_files": sum(dataset["summary"]["matched_files"] for dataset in datasets.values()),
            "identical_files": sum(dataset["summary"]["identical_files"] for dataset in datasets.values()),
            "different_files": sum(dataset["summary"]["different_files"] for dataset in datasets.values()),
            "generated_only_files": sum(dataset["summary"]["generated_only_files"] for dataset in datasets.values()),
            "reference_only_files": sum(dataset["summary"]["reference_only_files"] for dataset in datasets.values()),
            "ambiguous_matches": sum(dataset["summary"]["ambiguous_matches"] for dataset in datasets.values()),
        }

        report = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "settings": {
                "generated_root": str(self.generated_root),
                "bank_ref_dir": str(self.bank_reference_dir),
                "income_ref_dir": str(self.income_reference_dir),
                "report_path": str(self.report_path),
            },
            "datasets": datasets,
            "overall": overall,
        }

        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, indent=4) + "\n", encoding="utf-8")
        return report

    def _compare_dataset(self, generated_dir, reference_dir):
        generated_files = {path.stem: path for path in Path(generated_dir).glob("*.json")}
        reference_files = {path.stem: path for path in Path(reference_dir).glob("*.json")}

        matched_files = []
        matched_generated = set()
        matched_reference = set()

        for stem in sorted(set(generated_files) & set(reference_files)):
            matched_generated.add(stem)
            matched_reference.add(stem)
            matched_files.append(self._compare_matched_file(generated_files[stem], reference_files[stem], "exact"))

        generated_groups = self._group_by_normalized_key(set(generated_files) - matched_generated)
        reference_groups = self._group_by_normalized_key(set(reference_files) - matched_reference)

        ambiguous_matches = []
        generated_only_files = []
        reference_only_files = []

        for normalized_key in sorted(set(generated_groups) | set(reference_groups)):
            generated_stems = generated_groups.get(normalized_key, [])
            reference_stems = reference_groups.get(normalized_key, [])

            if len(generated_stems) == 1 and len(reference_stems) == 1:
                generated_stem = generated_stems[0]
                reference_stem = reference_stems[0]
                matched_generated.add(generated_stem)
                matched_reference.add(reference_stem)
                matched_files.append(
                    self._compare_matched_file(generated_files[generated_stem], reference_files[reference_stem], "normalized")
                )
                continue

            if generated_stems and reference_stems:
                ambiguous_matches.append(
                    {
                        "normalized_key": normalized_key,
                        "generated_files": [f"{stem}.json" for stem in generated_stems],
                        "reference_files": [f"{stem}.json" for stem in reference_stems],
                    }
                )
                continue

            if generated_stems:
                generated_only_files.extend(f"{stem}.json" for stem in generated_stems)
            if reference_stems:
                reference_only_files.extend(f"{stem}.json" for stem in reference_stems)

        matched_files.sort(key=lambda item: (item["generated_file"], item["reference_file"]))
        generated_only_files.sort()
        reference_only_files.sort()
        ambiguous_matches.sort(key=lambda item: item["normalized_key"])

        summary = {
            "matched_files": len(matched_files),
            "identical_files": sum(1 for item in matched_files if item["status"] == "identical"),
            "different_files": sum(1 for item in matched_files if item["status"] == "different"),
            "generated_only_files": len(generated_only_files),
            "reference_only_files": len(reference_only_files),
            "ambiguous_matches": len(ambiguous_matches),
        }

        return {
            "generated_dir": str(generated_dir),
            "reference_dir": str(reference_dir),
            "summary": summary,
            "generated_only_files": generated_only_files,
            "reference_only_files": reference_only_files,
            "ambiguous_matches": ambiguous_matches,
            "matched_files": matched_files,
        }

    def _compare_matched_file(self, generated_path, reference_path, match_type):
        generated_rules = self._load_rules(generated_path)
        reference_rules = self._load_rules(reference_path)

        generated_sorted = self._sort_rules(generated_rules)
        reference_sorted = self._sort_rules(reference_rules)

        paired_rule_diffs = []
        changed_rules = 0
        min_length = min(len(generated_sorted), len(reference_sorted))

        for index in range(min_length):
            path_diffs = self._diff_values(generated_sorted[index], reference_sorted[index])
            if path_diffs:
                changed_rules += 1
                paired_rule_diffs.append(
                    {
                        "rule_index": index,
                        "differences": path_diffs,
                    }
                )

        generated_only_rules = [self._serialize_for_report(rule) for rule in generated_sorted[min_length:]]
        reference_only_rules = [self._serialize_for_report(rule) for rule in reference_sorted[min_length:]]

        status = "identical"
        if paired_rule_diffs or generated_only_rules or reference_only_rules:
            status = "different"

        return {
            "generated_file": generated_path.name,
            "reference_file": reference_path.name,
            "match_type": match_type,
            "status": status,
            "changed_rules": changed_rules,
            "generated_only_rules": generated_only_rules,
            "reference_only_rules": reference_only_rules,
            "rule_diffs": paired_rule_diffs,
        }

    def _load_rules(self, path):
        return self._canonicalizer.load_rules(path)

    def _normalize_rule(self, rule):
        return self._canonicalizer.canonicalize_rule(rule)

    def _sorted_fonts(self, fonts):
        return sorted((self._canonicalizer.canonicalize_rule(font) for font in fonts), key=self._font_sort_key)

    def _sort_rules(self, rules):
        return self._canonicalizer.sort_rules(rules)

    def _rule_sort_key(self, rule):
        return self._canonicalizer.rule_sort_key(rule)

    def _font_sort_key(self, font):
        return self._canonicalizer.font_sort_key(font)

    def _diff_values(self, generated_value, reference_value, path=""):
        if isinstance(generated_value, dict) and isinstance(reference_value, dict):
            diffs = []
            for key in sorted(set(generated_value) | set(reference_value)):
                child_path = f"{path}.{key}" if path else key
                if key not in generated_value:
                    diffs.append(
                        {
                            "path": child_path,
                            "generated": None,
                            "reference": self._serialize_for_report(reference_value[key]),
                        }
                    )
                    continue
                if key not in reference_value:
                    diffs.append(
                        {
                            "path": child_path,
                            "generated": self._serialize_for_report(generated_value[key]),
                            "reference": None,
                        }
                    )
                    continue
                diffs.extend(self._diff_values(generated_value[key], reference_value[key], child_path))
            return diffs

        if isinstance(generated_value, list) and isinstance(reference_value, list):
            diffs = []
            min_length = min(len(generated_value), len(reference_value))
            for index in range(min_length):
                child_path = f"{path}[{index}]"
                diffs.extend(self._diff_values(generated_value[index], reference_value[index], child_path))
            for index in range(min_length, len(generated_value)):
                diffs.append(
                    {
                        "path": f"{path}[{index}]",
                        "generated": self._serialize_for_report(generated_value[index]),
                        "reference": None,
                    }
                )
            for index in range(min_length, len(reference_value)):
                diffs.append(
                    {
                        "path": f"{path}[{index}]",
                        "generated": None,
                        "reference": self._serialize_for_report(reference_value[index]),
                    }
                )
            return diffs

        if generated_value != reference_value:
            return [
                {
                    "path": path,
                    "generated": self._serialize_for_report(generated_value),
                    "reference": self._serialize_for_report(reference_value),
                }
            ]
        return []

    def _serialize_for_report(self, value):
        return self._canonicalizer.serialize(value)

    def _group_by_normalized_key(self, stems):
        groups = {}
        for stem in sorted(stems):
            groups.setdefault(self._normalize_for_match(stem), []).append(stem)
        return groups

    def _normalize_for_match(self, value):
        return re.sub(r"[^a-z0-9]", "", value.lower())
