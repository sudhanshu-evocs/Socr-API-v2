import importlib.resources
import json


class InvalidProducerCreatorDetector:
    _invalid_prefixes = None

    @classmethod
    def get_invalid_prefixes(cls):
        if cls._invalid_prefixes is None:
            invalid_json = importlib.resources.files("docuverus.Utils").joinpath("invalidproducercreator_list.json")
            invalid_data = json.loads(invalid_json.read_text(encoding="utf-8"))
            cls._invalid_prefixes = invalid_data.get("invalid_list", [])
        return cls._invalid_prefixes

    @classmethod
    def is_invalid_value(cls, value):
        normalized_value = str(value or "").strip()
        for prefix in cls.get_invalid_prefixes():
            if normalized_value.startswith(prefix):
                return True
        return False

    @classmethod
    def is_invalid_metadata(cls, metadata):
        return cls.is_invalid_value(metadata.get("producer")) or cls.is_invalid_value(metadata.get("creator"))
