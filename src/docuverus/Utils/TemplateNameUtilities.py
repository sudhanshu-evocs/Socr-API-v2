import re


def normalize_template_name(template_name: str) -> str:
    normalized_name = template_name.strip().casefold()
    return re.sub(r"\s+", "", normalized_name)
