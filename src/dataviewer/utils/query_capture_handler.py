import logging


class QueryCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.queries = []

    def emit(self, record):
        self.queries.append(record.getMessage())
