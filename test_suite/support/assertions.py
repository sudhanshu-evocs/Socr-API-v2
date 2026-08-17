def assert_dict_contains(larger_dict, smaller_dict):
    for key, value in smaller_dict.items():
        assert (
            key in larger_dict and larger_dict[key] == value
        ), f"Key {key} with value {value} not found in larger JSON"
