from pydantic import BaseModel, field_validator

from docuverus.Utils.Messages import ValidStates


class TemplateRuleSetModel(BaseModel):
    template: dict
    producer: dict
    creator: dict
    file_size: dict
    fonts: dict
    dates: dict

    @field_validator("template")
    def check_template(cls, values) -> dict:
        maximum_validation_level = values.get("maximum_validation_level")
        valid_states = {
            ValidStates.STATE_FAIL,
            ValidStates.STATE_FDR,
            ValidStates.STATE_PASS,
        }
        if maximum_validation_level is not None and maximum_validation_level not in valid_states:
            raise ValueError("maximum_validation_level must be one of Fail, FDR, or Pass")
        return values

    @field_validator("dates")
    def check_dates(cls, values) -> dict:
        if "created" in values and values["created"]["state"] == "Present":
            if values["modified"]["state"] == "Present":
                raise ValueError("Created and modified dates cannot both be present")
        return values
