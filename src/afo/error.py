
class AlertsGeneratedError(Exception):
    """Exception raised for alerts generated"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
