from datetime import datetime


class DateTimeUtilities:
    @staticmethod
    def create(input_datetime_str):
        split_input_datetime_str = input_datetime_str.split("-")[0].split("Z")[0]
        try:
            if split_input_datetime_str == "None":
                actual_datetime = "None"
            else:
                actual_datetime = datetime.strptime(split_input_datetime_str, "D:%Y%m%d%H%M%S")
            return actual_datetime
        except ValueError:
            return "Error parsing input datetime string"


# Handle the exception such that it returns the boolean value and don't consider handling code using error message.
