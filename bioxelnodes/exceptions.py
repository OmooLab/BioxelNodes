class CancelledByUser(Exception):
    def __init__(self):
        message = 'Cancelled by user'
        super().__init__(message)


class NoContent(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class NoFound(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class Incompatible(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
