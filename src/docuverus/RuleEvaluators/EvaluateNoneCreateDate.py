from docuverus.RuleEvaluators.EvaluateNoneSingleDate import EvaluateNoneSingleDate
from docuverus.Utils.Messages import MessageCode

CREATED_KEY = "created"


class EvaluateNoneCreateDate(EvaluateNoneSingleDate):
    def __init__(self):
        super().__init__(
            CREATED_KEY,
            MessageCode.MSG_CREATION_DATE_NOT_FOUND,
            MessageCode.MSG_CREATION_DATE_SHOULD_BE_NONE,
            MessageCode.MSG_MODIFICATION_DATE_FOUND,
            MessageCode.MSG_MODIFICATION_DATE_NOT_FOUND,
        )
