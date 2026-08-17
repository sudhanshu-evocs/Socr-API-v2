import importlib.resources
import json

from docuverus.Utils.Messages import MessageCode


class BrowserPrintedDetector:
    _browser_printed_prefixes = None

    @classmethod
    def get_browser_printed_prefixes(cls):
        if cls._browser_printed_prefixes is None:
            browser_printed_json = importlib.resources.files("docuverus.Utils").joinpath("browserprinted_list.json")
            browser_printed_data = json.loads(browser_printed_json.read_text(encoding="utf-8"))
            cls._browser_printed_prefixes = browser_printed_data.get("browser_printed_list", [])
        return cls._browser_printed_prefixes

    @classmethod
    def is_browser_printed_value(cls, value):
        normalized_value = str(value or "").strip()
        for prefix in cls.get_browser_printed_prefixes():
            if normalized_value.startswith(prefix):
                return True
        return False

    @classmethod
    def is_browser_printed_metadata(cls, metadata):
        producer_message_code = cls._get_validation_message_code(metadata, "producer")
        creator_message_code = cls._get_validation_message_code(metadata, "creator")
        return (
            producer_message_code == MessageCode.MSG_PRODUCER_BROWSER_PRINTED
            or creator_message_code == MessageCode.MSG_CREATOR_BROWSER_PRINTED
        )

    @staticmethod
    def _get_validation_message_code(metadata, field_name):
        field_metadata = metadata.get(field_name, {})
        if not isinstance(field_metadata, dict):
            return None
        return field_metadata.get("validation_message_code")
