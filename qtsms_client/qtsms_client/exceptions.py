"""
Custom exceptions for QTSMS Client.
"""


class QTSMSException(Exception):
    """Base exception for QTSMS client."""

    pass


class QTSMSValidationError(QTSMSException):
    """Raised when action parameters fail validation."""

    pass


class QTSMSRequestError(QTSMSException):
    """Raised when a request to the SMS gateway fails."""

    def __init__(self, message: str, status_code: int = None, response: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
