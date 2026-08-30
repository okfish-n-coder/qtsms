"""
QTSMS Client - Async Python library for Beeline SMS Gateway

A high-performance async Python client for the Beeline A2P SMS gateway,
rewritten from the original PHP library with optimizations for sending
thousands of SMS messages.

New in v2.0.0:
- Token-based authentication via X-ApiKey header
- JSON format for requests/responses  
- Comprehensive error handling with error code descriptions
- Pydantic schema validation
"""

__version__ = "2.0.0"
__author__ = "ISBC Group (original PHP), Python rewrite"

from .client import QTSMSClient
from .actions import (
    BaseAction,
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
    QTSMSAuthError,
    QTMSErrorCode,
    QTMSParseResponseError,
)
from .schemas import (
    TokenAuthConfig,
    SendSMSRequest,
    StatusRequest,
    BalanceRequest,
    InboxRequest,
    BlacklistRequest,
    BlacklistAddRequest,
    BlacklistDeleteRequest,
    SMSResponse,
)

__all__ = [
    "QTSMSClient",
    "BaseAction",
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
    "QTSMSAuthError",
    "QTMSErrorCode",
    "QTMSParseResponseError",
    "TokenAuthConfig",
    "SendSMSRequest",
    "StatusRequest",
    "BalanceRequest",
    "InboxRequest",
    "BlacklistRequest",
    "BlacklistAddRequest",
    "BlacklistDeleteRequest",
    "SMSResponse",
]
