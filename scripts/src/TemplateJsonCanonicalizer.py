import json
from pathlib import Path


class TemplateJsonCanonicalizer:
    TOP_LEVEL_KEY_ORDER = ("template", "producer", "creator", "author", "file_size", "fonts", "dates")
    NESTED_KEY_ORDER = {
        ("template",): ("name",),
        ("producer",): ("name",),
        ("creator",): ("name",),
        ("author",): ("name",),
        ("file_size",): ("algorithm", "min", "max"),
        ("fonts",): ("required_fonts", "optional_fonts"),
        ("fonts", "required_fonts", "*"): ("name", "type", "encoding", "multiplicity"),
        ("fonts", "optional_fonts", "*"): ("name", "type", "encoding", "multiplicity"),
        ("dates",): ("created", "modified"),
        ("dates", "created"): ("state", "duration", "tolerance"),
        ("dates", "modified"): ("state", "duration", "tolerance"),
    }

    def load_rules(self, path):
        parsed = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(parsed, list):
            raise ValueError(f"Expected JSON array in {path}")
        return [self.canonicalize_rule(rule) for rule in parsed]

    def canonicalize_rule(self, rule):
        if not isinstance(rule, dict):
            return self._deep_clone(rule)
        return self._canonicalize_value(rule, path=())

    def sort_rules(self, rules):
        return sorted((self.canonicalize_rule(rule) for rule in rules), key=self.rule_sort_key)

    def dumps_rules(self, rules, sort_rules=False):
        normalized_rules = [self.canonicalize_rule(rule) for rule in rules]
        if sort_rules:
            normalized_rules = sorted(normalized_rules, key=self.rule_sort_key)
        return json.dumps(normalized_rules, indent=4, ensure_ascii=True) + "\n"

    def rule_sort_key(self, rule):
        file_size = rule.get("file_size", {})
        dates = rule.get("dates", {})
        modified = dates.get("modified", {})
        return (
            rule.get("template", {}).get("name", ""),
            rule.get("producer", {}).get("name", ""),
            rule.get("creator", {}).get("name", ""),
            dates.get("created", {}).get("state", ""),
            modified.get("state", ""),
            modified.get("duration", ""),
            modified.get("tolerance", ""),
            file_size.get("algorithm", ""),
            file_size.get("min", ""),
            file_size.get("max", ""),
            tuple(self.font_sort_key(font) for font in rule.get("fonts", {}).get("required_fonts", [])),
            tuple(self.font_sort_key(font) for font in rule.get("fonts", {}).get("optional_fonts", [])),
        )

    def font_sort_key(self, font):
        return (
            font.get("name", ""),
            font.get("type", ""),
            font.get("encoding", ""),
            font.get("multiplicity", ""),
        )

    def serialize(self, value):
        return json.loads(json.dumps(value))

    def _canonicalize_value(self, value, path):
        if isinstance(value, dict):
            return self._canonicalize_dict(value, path)
        if isinstance(value, list):
            return self._canonicalize_list(value, path)
        return self._deep_clone(value)

    def _canonicalize_dict(self, value, path):
        canonical_items = {}
        preferred_order = self._preferred_keys_for_path(path)
        seen_keys = set()

        for key in preferred_order:
            if key in value:
                seen_keys.add(key)
                canonical_items[key] = self._canonicalize_value(value[key], path + (key,))

        for key in sorted(k for k in value.keys() if k not in seen_keys):
            canonical_items[key] = self._canonicalize_value(value[key], path + (key,))

        return canonical_items

    def _canonicalize_list(self, value, path):
        canonical_items = [self._canonicalize_value(item, path + ("*",)) for item in value]
        if path in (("fonts", "required_fonts"), ("fonts", "optional_fonts")):
            return sorted(canonical_items, key=self.font_sort_key)
        return canonical_items

    def _preferred_keys_for_path(self, path):
        if path == ():
            return self.TOP_LEVEL_KEY_ORDER
        return self.NESTED_KEY_ORDER.get(path, ())

    def _deep_clone(self, value):
        return json.loads(json.dumps(value))
