from docuverus.RuleEvaluators.RuleSetFactory import RuleSetFactory


def test_get_template_rules_returns_single_template():
    rule_set_factory = RuleSetFactory(["docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson"])

    template_rules = rule_set_factory.get_template_rules("Bank of America")

    assert len(template_rules) == 2
    assert template_rules[0]["producer"]["name"] == "^TargetStream.*"


def test_get_template_rules_returns_multiple_templates_from_file():
    rule_set_factory = RuleSetFactory(["docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson"])

    template_rules = rule_set_factory.get_template_rules("TD Bank")

    assert len(template_rules) == 3
    assert template_rules[0]["producer"]["name"] == "^OpenText Output Transformation Engine.*"
    assert template_rules[1]["producer"]["name"] == "^iOS Version.*"
    assert template_rules[2]["producer"]["name"] == "^macOS Version.*"


def test_get_template_rules_returns_template_from_multiple_packages():
    rule_set_factory = RuleSetFactory(
        [
            "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
            "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
        ]
    )

    template_rules = rule_set_factory.get_template_rules("Paycor")

    assert len(template_rules) == 1
    assert template_rules[0]["producer"]["name"] == "^DynamicPDF Core Suite.*"


def test_get_available_templates_returns_list_of_template_names_from_rule_sets():
    rule_set_factory = RuleSetFactory(
        [
            "docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson",
            "docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson",
        ]
    )
    list_known_templates = [
        "BB&T",
        "Bank of America",
        "Chase Bank",
        "Citizens Bank",
        "Discover Bank",
        "Paycor",
        "TD Bank",
    ]

    templates = rule_set_factory.get_template_names()

    assert len(templates) == 417
    for known_template in list_known_templates:
        assert known_template in templates


def test_get_template_rules_uses_template_name_field_in_json():

    rule_set_factory = RuleSetFactory(["docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson"])

    template_rules = rule_set_factory.get_template_rules("Discover Bank")

    assert template_rules[0]["template"]["name"] == "Discover Bank"
    assert template_rules[0]["producer"]["name"] == "^Rendering Engine.*"
    assert template_rules[0]["file_size"]["min"] == 200
    assert template_rules[0]["file_size"]["max"] == 300


def test_rule_set_factory_is_not_case_sensitive():

    rule_set_factory = RuleSetFactory(["docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson"])

    template_rules = rule_set_factory.get_template_rules("discover bank")

    assert template_rules[0]["template"]["name"] == "Discover Bank"
    assert template_rules[0]["producer"]["name"] == "^Rendering Engine.*"
    assert template_rules[0]["file_size"]["min"] == 200
    assert template_rules[0]["file_size"]["max"] == 300


def test_rule_set_factory_ignores_inner_whitespace_for_template_matching():
    rule_set_factory = RuleSetFactory(["docuverus.RuleEvaluators.TemplateJson.EarningStatementsRuleJson"])

    template_rules = rule_set_factory.get_template_rules("JP   Morgan   Chase")

    assert len(template_rules) == 2
    assert [rule["template"]["name"] for rule in template_rules].count("JP Morgan Chase") == 0
    assert [rule["template"]["name"] for rule in template_rules].count("JPMorgan Chase") == 2


def test_get_template_names_dedupes_by_normalized_template_name():
    rule_set_factory = RuleSetFactory(["docuverus.RuleEvaluators.TemplateJson.BankStatementsRuleJson"])

    templates = rule_set_factory.get_template_names()

    police_fire_variants = {"Police _ Fire", "Police_Fire"} & templates
    assert len(police_fire_variants) == 1
