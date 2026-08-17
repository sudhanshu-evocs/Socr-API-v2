def all_valid_not_fail(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "valid" and value == "Fail":
                return False
            if not all_valid_not_fail(value):
                return False
    elif isinstance(data, list):
        for item in data:
            if not all_valid_not_fail(item):
                return False
    return True
