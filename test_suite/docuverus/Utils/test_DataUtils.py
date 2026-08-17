import csv
import json

import pytest


def remove_known_characters(input_string, characters_to_remove):
    return "".join([char for char in input_string if char not in characters_to_remove])


def parse_csv_to_json(csv_file_path):
    with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        banking_jsons = []
        earnings_jsons = []
        for row in reader:
            new_json = {"template": {"name": row["Template"]}}
            if row["Valid or Fraud?"] != "Valid":
                continue
            new_json["producer"] = {"name": "None" if row["PDF Producer"] == "Null" else row["PDF Producer"]}
            new_json["creator"] = {"name": "None" if row["Application"] == "Null" else row["Application"]}
            file_size_row = remove_known_characters(row["File Size"], {"K", "B", "k", "b"})
            if len(file_size_row.split("-")) == 2:
                new_json["file_size"] = {
                    "min": file_size_row.split("-")[0].strip(),
                    "max": file_size_row.split("-")[1].strip(),
                }
            new_json["fonts"] = dict(
                required_fonts=(
                    [
                        {"name": font.strip(), "type": "CHANGE_ME", "encoding": "CHANGE_ME", "multiplicity": 1}
                        for font in row["Standard Fonts"].split(";")
                    ]
                    if row["Standard Fonts"]
                    else []
                ),
                optional_fonts=(
                    [
                        {"name": font.strip(), "type": "CHANGE_ME", "encoding": "CHANGE_ME", "multiplicity": 1}
                        for font in row["Optional Fonts"].split(";")
                    ]
                    if row["Optional Fonts"]
                    else []
                ),
            )
            new_json["dates"] = {
                "created": {"state": "None" if row["Create Date"] == "Null" else row["Create Date"]},
                "modified": {"state": "None" if row["Modified Date"] == "Null" else row["Modified Date"]},
            }

            print(row)
            if row["Type"] == "Earning Statement":
                earnings_jsons.append([new_json])
            else:
                banking_jsons.append([new_json])
        return (banking_jsons, earnings_jsons)


@pytest.mark.skip()
def test_create_base_json_files_from_csv():
    csv_file_path = "../ats.csv"
    banking_jsons, earning_jsons = parse_csv_to_json(csv_file_path)

    for json_obj in banking_jsons:
        print(json_obj[0]["template"]["name"].strip("/ "))
        with open(
            f"output_files/Banking/{remove_known_characters(json_obj[0]['template']['name'], {'/', ' ', '?'})}.json",
            "w",
        ) as json_file:
            json.dump(json_obj, json_file, indent=4)
        # print(json.dumps(json_obj, indent=4))

    for json_obj in earning_jsons:
        print(json_obj[0]["template"]["name"].strip("/ "))
        with open(
            f"output_files/Earning/{remove_known_characters(json_obj[0]['template']['name'], {'/', ' ', '?'})}.json",
            "w",
        ) as json_file:
            json.dump(json_obj, json_file, indent=4)
