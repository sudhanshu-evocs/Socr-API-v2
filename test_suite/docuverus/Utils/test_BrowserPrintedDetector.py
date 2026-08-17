from docuverus.Utils.BrowserPrintedDetector import BrowserPrintedDetector


def test_is_browser_printed_metadata_when_producer_message_code_matches():
    metadata = {
        "producer": {"validation_message_code": "MSG_PRODUCER_BROWSER_PRINTED"},
        "creator": {"validation_message_code": "MSG_CREATOR_MATCH"},
    }

    assert BrowserPrintedDetector.is_browser_printed_metadata(metadata) is True


def test_is_browser_printed_metadata_when_creator_message_code_matches():
    metadata = {
        "producer": {"validation_message_code": "MSG_PRODUCER_MATCH"},
        "creator": {"validation_message_code": "MSG_CREATOR_BROWSER_PRINTED"},
    }

    assert BrowserPrintedDetector.is_browser_printed_metadata(metadata) is True


def test_is_browser_printed_metadata_when_no_message_code_matches():
    metadata = {
        "producer": {"validation_message_code": "MSG_PRODUCER_MATCH"},
        "creator": {"validation_message_code": "MSG_CREATOR_MATCH"},
    }

    assert BrowserPrintedDetector.is_browser_printed_metadata(metadata) is False


def test_is_browser_printed_metadata_when_fields_are_missing():
    assert BrowserPrintedDetector.is_browser_printed_metadata({}) is False
