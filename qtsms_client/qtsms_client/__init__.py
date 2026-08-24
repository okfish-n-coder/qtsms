"""
QTSMS Client - Async Python library for Beeline SMS Gateway

A high-performance async Python client for the Beeline A2P SMS gateway,
rewritten from the original PHP library with optimizations for sending
thousands of SMS messages.
"""

__version__ = "1.0.0"
__author__ = "ISBC Group (original PHP), Python rewrite"

from .client import QTSMSClient
from .actions import (
    SendSMSAction,
    StatusAction,
    BalanceAction,
    InboxAction,
    BlacklistAction,
    BlacklistAddAction,
    BlacklistDeleteAction,
)
from .exceptions import (
    QTSMSException,
    QTSMSValidationError,
    QTSMSRequestError,
)

__all__ = [
    "QTSMSClient",
    "SendSMSAction",
    "StatusAction",
    "BalanceAction",
    "InboxAction",
    "BlacklistAction",
    "BlacklistAddAction",
    "BlacklistDeleteAction",
    "QTSMSException",
    "QTSMSValidationError",
    "QTSMSRequestError",
]
