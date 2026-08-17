# SOCR API v2 Business Rules

## Purpose and source of truth

This document summarizes the business rules implemented by FraudDetector and CompositeRuleEvaluator as of 2026-07-29. The source code and tests are authoritative; rule JSON supplies template-specific thresholds, values, fonts, and date states.

Primary implementation sources:

- src/docuverus/FraudDetector/FraudDetector.py
- src/docuverus/FraudDetector/DateOverrideRule.py
- src/docuverus/RuleEvaluators/CompositeRuleEvaluator.py
- src/docuverus/RuleEvaluators/TemplateTypeRuleEvaluator.py
- src/docuverus/RuleEvaluators/SingleValueRuleEvaluator.py
- src/docuverus/RuleEvaluators/FileSizeRuleEvaluator.py
- src/docuverus/RuleEvaluators/FontRuleEvaluator.py
- src/docuverus/RuleEvaluators/DateRuleEvaluator.py and its comparator classes
- src/docuverus/Utils/BrowserPrintedDetector.py
- src/docuverus/Utils/InvalidProducerCreatorDetector.py
- src/docuverus/Utils/JSONUtilities.py

## Rule vocabulary

### Validation states

| State | Meaning in the implementation |
|---|---|
| Pass | The rule or final document result is accepted by that validation layer. |
| Fail | A rule or document condition is explicitly invalid. |
| FDR | Further documentation/review is required, or the condition is treated as fraud/document-review risk rather than a hard rejection. |
| NOT_APPLICABLE | A rule does not apply, such as an unavailable font rule; it is not treated as Fail by recursive pass selection. |

all_valid_not_fail recursively searches a rule-set dictionary and returns false only when a nested valid value is exactly Fail. Therefore, an ordinary non-browser-printed rule set may still be selected as passing when one or more nested rules are FDR or NOT_APPLICABLE.

### Rule-set fields

The evaluator expects a rule set containing, at minimum, template, file_size, fonts, dates, producer, and creator. author is optional and is synthesized as a passing rule when absent. Rules are evaluated in-place; the expected rule object is enriched with actual values, states, and message codes.

## CompositeRuleEvaluator rules

CompositeRuleEvaluatorFactory.create(template_type) always constructs the following ordered pipeline:

~~~text
Template type
  -> file size
  -> producer
  -> creator
  -> browser-printed producer/creator override
  -> author
  -> fonts
  -> dates
~~~

The composite evaluator does not short-circuit the pipeline. Each evaluator receives the same mutable rule-set dictionary. The template evaluator has one internal exception: if the template rule is already Fail, it leaves it failed instead of overwriting it.

### 1. Template type

- Compare rule template.name with the requested template using strip, case-folding, and whitespace removal.
- Matching names receive Pass / MSG_TEMPLATE_TYPE_MATCH.
- Non-matching names receive Fail / MSG_TEMPLATE_TYPE_DOES_NOT_MATCH.
- The requested template is recorded as template.actual.
- An empty rule set created for an unknown template already has a failed template rule and remains failed.

### 2. Producer, creator, and author values

SingleValueRuleEvaluator applies the configured name as a Python regular expression against the extracted metadata value.

- A match produces Pass and the field-specific match message.
- No match produces Fail and the field-specific non-match message.
- A blank configured name matches only an empty actual value.
- If a field is absent from the rule, the evaluator creates a passing field rule with an empty expected name.
- Actual values are recorded in the rule-set field.

The business effect is that producer and creator rules normally act as template fingerprints. Author rules are optional and are less restrictive when omitted from a template rule set.

### 3. Browser-printed producer/creator override

After producer and creator evaluation, BrowserPrintedSingleValueOverrideRuleEvaluator checks only fields that:

1. Exist in the rule set.
2. Currently have valid == Fail.
3. Have actual metadata beginning with a configured browser-printed prefix.

Matching values are rewritten to valid == FDR with MSG_PRODUCER_BROWSER_PRINTED or MSG_CREATOR_BROWSER_PRINTED.

The detector uses prefix matching after trimming surrounding whitespace. It does not treat an arbitrary occurrence of a browser token as a match; the configured token must be at the beginning of the value. If the producer/creator rule already passes, the override does not replace that pass.

### 4. File size

FileSizeRuleEvaluator uses file_size metadata and the rule algorithm.

#### Constant algorithm

- Convert actual, minimum, and maximum values to floating-point numbers.
- Accept when min <= actual <= max.
- Reject when actual size is outside the inclusive range.

#### Linear algorithm

For paystub-based rules, calculate:

~~~text
calculated_min = min_slope * paystub_count + min_size - min_slope
calculated_max = max_slope * paystub_count + max_size - max_slope
~~~

Accept when calculated_min <= actual <= calculated_max.

#### Unknown or unsupported algorithm

- Unknown produces NOT_APPLICABLE and an unknown-file-size message.
- An unrecognized algorithm also produces NOT_APPLICABLE.
- If algorithm is absent, the evaluator defaults it to Constant.
- A zero file size uses the “file does not exist” message when the strategy generates a file-size message.

## Font rules

FontRuleEvaluator validates extracted PDF font tuples by subtype, normalized font name, encoding, and multiplicity.

### Font identity

- The document font key is (subtype, normalized_name, encoding).
- Six-character PDF subset prefixes such as ABCDEF+FontName are reduced to FontName.
- Certain _CZEX#### suffix patterns are normalized.
- A rule with blank type and blank encoding treats those attributes as wildcards and matches by name alone.
- Otherwise name, type, and encoding must all match.

### Required fonts

- Missing required font: Fail / MSG_REQUIRED_FONT_NOT_MATCHED.
- Required font present within its allowed multiplicity: Pass / MSG_REQUIRED_FONT_MATCHED.
- Required font over multiplicity: Fail / MSG_REQUIRED_FONT_NOT_MATCHED.
- Missing required multiplicity defaults to 1.

### Optional fonts

- Missing optional font: field-level Pass / MSG_OPTIONAL_FONT_NOT_FOUND.
- Present within multiplicity: Pass / MSG_OPTIONAL_FONT_MATCHED.
- Present over multiplicity: field-level Fail / MSG_OPTIONAL_FONT_NOT_MATCHED.
- Missing optional multiplicity defaults to 9999.
- Although aggregate font status primarily checks required fonts and additional fonts, the recursive FraudDetector pass check still rejects any nested optional-font Fail.

### Paystub multiplicity

When paystub_count > 0, every required font multiplicity is multiplied by the paystub count. This models repeated font usage across multiple paystubs. The rule object is mutated in place, so repeated evaluation of the same rule object can compound this multiplication; callers should provide fresh rule objects for independent evaluations.

### Additional fonts

- Fonts not represented in either required or optional expected lists are collected as additional_fonts.
- When any font rules exist, an additional font is marked Fail / MSG_FRAUD_FONT_FOUND and contributes to aggregate font failure.
- When no required or optional font rules exist, additional fonts are marked FDR / MSG_FONT_NOT_APPLICABLE; the aggregate font rule is FDR / MSG_FONT_RULE_NOT_APPLICABLE.
- Aggregate fonts are Pass only when all required fonts pass and no additional font is failed.
- Aggregate fonts are Fail if required fonts fail or additional fonts are failed.

## Date rules

Date rules are selected by expected creation state, expected modification state, whether tolerance is positive, and whether duration is positive.

### Date parsing

The evaluator records the raw metadata value in the date rule’s actual field and accepts these effective formats:

- D:YYYYMMDDHHMMSS
- MM/DD/YYYY HH:MM:SS
- D:YYYYMMDD

Timezone suffixes split at -, +, Z, or UTC, and CR/LF characters are removed. An empty metadata value is treated as the sentinel None.

If a date cannot be parsed, the corresponding date field is failed with MSG_INVALID_DATE_FORMAT and the combined date rule is failed with MSG_INVALID_CREATION_MODIFICATION_DATES before the mapped comparison is applied.

### Supported date states

| Expected creation | Expected modification | Business rule |
|---|---|---|
| None | None | Both metadata dates must be absent. |
| None | Present | Creation must be absent and modification must be present. |
| Present | None | Creation must be present and modification must be absent. |
| Present | Equal | Modification must equal creation plus expected duration within tolerance. With no configured tolerance, the default tolerance is one second. |
| Present | Greater | Modification must be strictly later than creation, or satisfy duration/tolerance when a duration is configured. |
| Present | Lesser | Modification must be strictly earlier than creation. |
| Specific date | Specific date or Equal | Actual creation/modification values must equal the configured specific values. |
| Specific date | Greater | Creation must equal the configured specific date and modification must be later than creation. |
| Specific date | Present | Creation must equal the configured specific date and modification must be present. |
| Specific date | None | Creation must equal the configured specific date and modification must be absent. |

For duration/tolerance comparisons:

~~~text
actual_duration = modification - creation
actual_variance = actual_duration - expected_duration
valid when 0 <= actual_variance <= expected_tolerance
~~~

An unsupported state combination falls through to NoDateRuleComparator, which marks the date fields and aggregate date rule as FDR with the configured error message constants.

## FraudDetector decision policy

FraudDetector evaluates all matching rule sets for one requested template, then chooses a document-level result. This is the central business decision layer.

### Pre-evaluation gates

1. If metadata contains exception, return Fail / MSG_INVALID_PDF_FILE.
2. If image_file is true, skip the composite evaluator and return Fail / MSG_INVALID_IMAGE_DOCUMENT.
3. Otherwise load every matching rule set and evaluate each one.
4. If no rule set matches, create one empty rule set and set unknown_template_flag=True.

The image result includes a not-applicable copy of common metadata fields. It does not run producer, creator, font, file-size, or date business rules.

### Rule-set selection

For each evaluated rule set:

- A non-browser-printed rule set is considered valid if no nested valid value is Fail.
- A browser-printed rule set must also have aggregate fonts.valid == Pass and file_size.valid == Pass.
- The first passing rule set in factory order is selected.

If a passing rule set is selected, the document result is Pass / MSG_VALID_FILE, subject to final clamping and font overrides.

### Date override / save-as scenario

The date override is evaluated only after no rule set passed.

A rule set qualifies when:

- template, producer, creator, author, and file_size are Pass.
- fonts is Pass, or is specifically FDR / MSG_FONT_RULE_NOT_APPLICABLE.
- Both metadata dates parse successfully and are present.
- 0 < modification - creation < 5 hours.

The five-hour upper bound is exclusive. A zero or negative interval does not qualify. A five-hour-or-longer interval does not qualify. A different failed validator prevents the override.

When selected, the date field and aggregate date rule are rewritten to FDR / MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO, and the final document result is FDR with the same message code.

### Unknown template

If no rule set exists and the date override did not apply, return:

~~~text
FDR / MSG_UNKNOWN_TEMPLATE_TYPE
~~~

This branch takes precedence over browser-printed and invalid-producer classification for the empty unknown-template rule set.

### Browser-printed failure

For known templates, if any evaluated rule set has producer or creator marked with a browser-printed message code and no passing/date-override result was selected, return:

~~~text
FDR / MSG_BROWSER_PRINTED_DOCUMENT
~~~

This includes browser-printed cases with failed or not-applicable fonts/file size. A browser-printed rule set can still return Pass when its aggregate fonts and file size pass.

### Invalid producer/creator metadata

If no earlier result applies and the raw producer or creator begins with a configured invalid prefix, return:

~~~text
Fail / MSG_INVALID_FILE
~~~

This check uses raw metadata and the invalid-prefix list, not the evaluated rule’s message code.

### Fallback / further documentation

If no prior result applies, return:

~~~text
FDR / MSG_FURTHER_DOCUMENTATION_REQUIRED
~~~

The returned rule sets are sorted by the following field priority:

1. producer
2. creator
3. fonts
4. dates
5. file_size

For each field, Pass ranks best, FDR and NOT_APPLICABLE tie in the middle, and Fail ranks worst. Missing or unknown states rank as worst. Python’s stable sort preserves input order for ties.

## Final-result modifiers

Every selected result except the initial exception/image result is passed through _finalize_result.

### Maximum validation level

If one or more selected rule sets define template.maximum_validation_level, the most restrictive value is selected using:

~~~text
Fail < FDR < Pass
~~~

The final result is clamped down to that state if necessary. A clamped result receives:

- MSG_FURTHER_VALIDATION_REQUIRED_UNKNOWN_TEMPLATE when the requested template normalizes to no or unknown.
- MSG_FURTHER_VALIDATION_REQUIRED_UNTRUSTED_TEMPLATE otherwise.

The rule-set-level validation states remain unchanged; only final_validation_results is clamped.

### Font failure override

After maximum-level clamping, the first selected rule set is inspected:

- Browser-printed rule sets are excluded from this override.
- If the selected aggregate font rule is Fail, final validity is forced to Fail.
- The existing final message code is preserved.
- Font failures in non-selected rule sets do not trigger this override.

## Document-level outcome matrix

| Evaluation condition | Final state | Message code |
|---|---:|---|
| Metadata extraction exception | Fail | MSG_INVALID_PDF_FILE |
| Image-only PDF | Fail | MSG_INVALID_IMAGE_DOCUMENT |
| First acceptable ordinary rule set | Pass | MSG_VALID_FILE |
| First acceptable browser-printed rule set with fonts and size passing | Pass | MSG_VALID_FILE |
| Date override qualifies | FDR | MSG_POSSIBLE_MODIFICATION_SAVE_AS_SCENARIO |
| No matching template rule set | FDR | MSG_UNKNOWN_TEMPLATE_TYPE |
| Known template, browser-printed rule set remains unresolved | FDR | MSG_BROWSER_PRINTED_DOCUMENT |
| Raw producer/creator has invalid prefix and no earlier branch applies | Fail | MSG_INVALID_FILE |
| Remaining unresolved validation | FDR | MSG_FURTHER_DOCUMENTATION_REQUIRED |
| Any result clamped by maximum validation level | Lower of current/max | MSG_FURTHER_VALIDATION_REQUIRED_* |

The matrix is ordered: earlier branches win. In particular, a pass wins over date override, date override wins over unknown/browser/invalid/fallback branches, and unknown-template handling wins over browser/invalid fallback handling.

## Important implementation caveats

These are current behaviors that should be considered when changing rules or interpreting results:

- CompositeRuleEvaluator mutates rule dictionaries and never resets them between evaluations.
- Required font multiplicity is multiplied in-place for paystub counts, so reusing a rule object can compound the expected count.
- Ordinary pass selection rejects only explicit Fail; FDR and NOT_APPLICABLE are otherwise tolerated unless a special detector branch adds stricter requirements.
- Browser-printed selection is stricter than ordinary selection: aggregate fonts and file size must both be Pass.
- Date override has its own five-hour rule and is not the same as a template’s configured date comparator.
- Maximum validation level changes only the final result, not nested rule results.
- Font failure override examines only the first selected rule set.
- The broad file-path exception handler returns invalid-PDF output for any exception, not only malformed PDFs.
- The public route currently receives a template from the caller; the repository’s template-confidence workflow is not connected to this policy.

## Test coverage map

The business rules are exercised primarily by:

- test_suite/docuverus/FraudDetector/test_FraudDetector.py — document-level precedence, browser-printed branches, date override, unknown sorting, maximum validation levels, invalid PDFs, image PDFs, and real fixtures.
- test_suite/docuverus/RuleEvaluators/test_CompositeRuleEvaluator.py — ordered rule mutation and representative complete evaluations.
- test_suite/docuverus/RuleEvaluators/test_FontRuleEvaluator.py — font identity, required/optional multiplicity, additional fonts, and paystub scaling.
- test_suite/docuverus/RuleEvaluators/test_DateRuleEvaluator.py — date formats, absence/presence, exact dates, ordering, durations, and tolerances.
- Individual evaluator tests for file size, producer/creator values, template names, and browser-printed behavior.

