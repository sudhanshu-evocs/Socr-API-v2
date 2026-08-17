import json
import os
import unittest


class TestJSONFiles(unittest.TestCase):
    def setUp(self):
        # Set up the directory containing JSON files
        self.directory = "../src/docuverus/RuleEvaluators/TemplateJson/BankStatementsRuleJson"  # Replace with the path to your directory

    def test_json_files_format(self):
        for filename in os.listdir(self.directory):
            if filename.endswith(".json"):
                with self.subTest(filename=filename):
                    filepath = os.path.join(self.directory, filename)
                    with open(filepath, "r") as file:
                        try:
                            json.load(file)
                            print(f"{filename}: True")
                        except Exception as e:
                            print(f"{filename}: False")
                            self.fail(f"JSONDecodeError in file {filename}")


if __name__ == "__main__":
    unittest.main()
