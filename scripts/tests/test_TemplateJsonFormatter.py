import json
import subprocess
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from src.TemplateJsonCanonicalizer import TemplateJsonCanonicalizer


def formatter_script():
    return Path(__file__).resolve().parents[2] / "scripts" / "standardize_template_json.py"


def run_formatter(tmp_path, *args):
    command = [sys.executable, str(formatter_script()), "--template-json-root", str(tmp_path), *args]
    return subprocess.run(command, capture_output=True, text=True, cwd=Path(__file__).resolve().parents[2], check=False)


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=4) + "\n", encoding="utf-8")


def rule(
    template="TemplateX",
    producer="^Producer.*",
    creator="^Creator.*",
    file_size=None,
    required_fonts=None,
    optional_fonts=None,
    created_state="Present",
    modified=None,
    author=None,
):
    payload = {
        "template": {"name": template},
        "producer": {"name": producer},
        "creator": {"name": creator},
        "file_size": file_size if file_size is not None else {"algorithm": "Unknown"},
        "fonts": {
            "required_fonts": required_fonts if required_fonts is not None else [],
            "optional_fonts": optional_fonts if optional_fonts is not None else [],
        },
        "dates": {
            "created": {"state": created_state},
            "modified": modified if modified is not None else {"state": "Equal"},
        },
    }
    if author is not None:
        payload["author"] = {"name": author}
    return payload


def font(name, type_="", encoding="", multiplicity=1):
    return {
        "name": name,
        "type": type_,
        "encoding": encoding,
        "multiplicity": multiplicity,
    }


def test_canonicalizer_orders_keys_and_fonts():
    canonicalizer = TemplateJsonCanonicalizer()
    unordered_rule = {
        "creator": {"name": "Creator"},
        "template": {"name": "T"},
        "dates": {"modified": {"tolerance": 2, "state": "Within"}, "created": {"state": "Present"}},
        "fonts": {
            "optional_fonts": [font("Zeta"), font("Alpha")],
            "required_fonts": [font("Beta"), font("Alpha")],
        },
        "producer": {"name": "Producer"},
        "file_size": {"max": 8, "min": 3, "algorithm": "Constant"},
        "author": {"name": "Author"},
    }

    canonical = canonicalizer.canonicalize_rule(unordered_rule)

    assert list(canonical.keys()) == ["template", "producer", "creator", "author", "file_size", "fonts", "dates"]
    assert [item["name"] for item in canonical["fonts"]["required_fonts"]] == ["Alpha", "Beta"]
    assert [item["name"] for item in canonical["fonts"]["optional_fonts"]] == ["Alpha", "Zeta"]
    assert list(canonical["file_size"].keys()) == ["algorithm", "min", "max"]
    assert list(canonical["dates"]["modified"].keys()) == ["state", "tolerance"]


def test_formatter_rewrites_whitespace_rule_order_and_font_order(tmp_path):
    target = tmp_path / "BankStatementsRuleJson" / "Ordered.json"
    write_text(
        target,
        '[{"template":{"name":"Ordered"},"producer":{"name":"^B.*"},"creator":{"name":"C"},"file_size":{"algorithm":"Unknown"},"fonts":{"required_fonts":[{"name":"Delta"},{"name":"Alpha"}],"optional_fonts":[]},"dates":{"created":{"state":"Present"},"modified":{"state":"Equal"}}},{"template":{"name":"Ordered"},"producer":{"name":"^A.*"},"creator":{"name":"C"},"file_size":{"algorithm":"Unknown"},"fonts":{"required_fonts":[{"name":"Gamma"},{"name":"Beta"}],"optional_fonts":[]},"dates":{"created":{"state":"Present"},"modified":{"state":"Equal"}}}]\n',
    )

    completed = run_formatter(tmp_path)

    assert completed.returncode == 0
    assert "changed_files=1" in completed.stdout

    formatted = json.loads(target.read_text(encoding="utf-8"))
    assert formatted[0]["producer"]["name"] == "^A.*"
    assert [item["name"] for item in formatted[0]["fonts"]["required_fonts"]] == ["Beta", "Gamma"]

    lines = target.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "["
    assert lines[1] == "    {"


def test_formatter_preserves_author_and_reports_dry_run_without_writing(tmp_path):
    target = tmp_path / "EarningStatementsRuleJson" / "Author.json"
    original_text = '[{"template":{"name":"Author"},"creator":{"name":"Creator"},"producer":{"name":"Producer"},"author":{"name":"Writer"},"file_size":{"max":3,"algorithm":"Constant","min":1},"fonts":{"optional_fonts":[],"required_fonts":[]},"dates":{"modified":{"state":"Equal"},"created":{"state":"Present"}}}]\n'
    write_text(target, original_text)

    completed = run_formatter(tmp_path, "--dry-run")

    assert completed.returncode == 0
    assert "would_change_files=1" in completed.stdout
    assert "WOULD_CHANGE" in completed.stdout
    assert target.read_text(encoding="utf-8") == original_text


def test_formatter_leaves_canonical_file_unchanged(tmp_path):
    target = tmp_path / "BankStatementsRuleJson" / "Canonical.json"
    canonicalizer = TemplateJsonCanonicalizer()
    canonical_text = canonicalizer.dumps_rules([rule(template="Canonical")], sort_rules=True)
    write_text(target, canonical_text)

    completed = run_formatter(tmp_path)

    assert completed.returncode == 0
    assert "changed_files=0" in completed.stdout
    assert target.read_text(encoding="utf-8") == canonical_text


def test_formatter_aborts_without_writing_if_any_file_is_invalid(tmp_path):
    valid_path = tmp_path / "BankStatementsRuleJson" / "Valid.json"
    invalid_path = tmp_path / "EarningStatementsRuleJson" / "Broken.json"
    original_valid_text = '[{"template":{"name":"Valid"},"creator":{"name":"Creator"},"producer":{"name":"Producer"},"file_size":{"max":3,"algorithm":"Constant","min":1},"fonts":{"optional_fonts":[],"required_fonts":[{"name":"Zulu"},{"name":"Alpha"}]},"dates":{"modified":{"state":"Equal"},"created":{"state":"Present"}}}]\n'
    write_text(valid_path, original_valid_text)
    write_text(invalid_path, '{"not":"a list"}\n')

    completed = run_formatter(tmp_path)

    assert completed.returncode == 1
    assert "error=Expected JSON array" in completed.stdout
    assert valid_path.read_text(encoding="utf-8") == original_valid_text


def test_formatter_scans_all_json_files_under_root(tmp_path):
    bank_target = tmp_path / "BankStatementsRuleJson" / "One.json"
    generic_target = tmp_path / "Generic" / "BankStatementsRuleJson" / "generic.json"
    write_json(bank_target, [rule(template="One", producer="^B.*"), rule(template="One", producer="^A.*")])
    write_text(generic_target, '[{"template":{"name":"Generic"},"producer":{"name":"^G.*"},"creator":{"name":"C"},"file_size":{"algorithm":"Unknown"},"fonts":{"required_fonts":[{"name":"Zed"},{"name":"Able"}],"optional_fonts":[]},"dates":{"created":{"state":"Present"},"modified":{"state":"Equal"}}}]\n')

    completed = run_formatter(tmp_path)

    assert completed.returncode == 0
    assert "files_scanned=2" in completed.stdout
    assert json.loads(bank_target.read_text(encoding="utf-8"))[0]["producer"]["name"] == "^A.*"
    assert [item["name"] for item in json.loads(generic_target.read_text(encoding="utf-8"))[0]["fonts"]["required_fonts"]] == [
        "Able",
        "Zed",
    ]
