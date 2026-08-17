from docuverus.RuleEvaluators.EvaluateNoneSingleDate import EvaluateNoneSingleDate
from docuverus.Utils.Messages import MessageCode

MODIFIED_KEY = "modified"


class EvaluateNoneModDate(EvaluateNoneSingleDate):

    def __init__(self):
        super().__init__(
            MODIFIED_KEY,
            MessageCode.MSG_CREATION_DATE_FOUND,
            MessageCode.MSG_CREATION_DATE_NOT_FOUND,
            MessageCode.MSG_MODIFICATION_DATE_NOT_FOUND,
            MessageCode.MSG_MODIFICATION_DATE_SHOULD_BE_NONE,
        )
