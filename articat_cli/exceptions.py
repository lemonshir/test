class TaskFailed(Exception):
    ...


class TaskTimeout(Exception):
    ...


class UrlUnconverted(Exception):
    def __init__(self, url):
        error_msg = f"The url is not converted to SRP unique ID: {url}"
        super().__init__(error_msg)
