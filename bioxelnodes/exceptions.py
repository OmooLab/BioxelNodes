class CancelledByUser(Exception):
    def __init__(self):
        message = 'Cancelled by user'
        super().__init__(message)
