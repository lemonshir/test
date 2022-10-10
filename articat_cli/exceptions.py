class TaskFailed(Exception):
    ...


class TaskTimeout(Exception):
    ...


class UrlUnconverted(Exception):
    def __init__(self):
        error_msg = "The url is not converted to SRP unique ID}"
        super().__init__(error_msg)
