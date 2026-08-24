"""
Action classes for QTSMS Client.

Each action represents a specific operation that can be performed
against the SMS gateway (send SMS, check balance, get status, etc.).
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class BaseAction(ABC):
    """Base class for all SMS actions."""

    ACTION_NAME: str = ""
    DEFAULT_PARAMS: Dict[str, Any] = {}

    def __init__(self, **kwargs):
        self.params: Dict[str, Any] = dict(self.DEFAULT_PARAMS)
        if kwargs:
            self.set_params(kwargs)

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate action parameters. Override in subclasses."""
        return True

    def set_params(self, params: Dict[str, Any]) -> None:
        """Set action parameters after validation."""
        from .exceptions import QTSMSValidationError

        if not self.validate_params(params):
            raise QTSMSValidationError(f"Invalid parameters for {self.__class__.__name__}")

        for key, value in params.items():
            if key in self.params or key not in self.DEFAULT_PARAMS:
                self.params[key] = value

    def get_action_name(self) -> str:
        """Return the action name for the API request."""
        return self.ACTION_NAME

    def form_post_fields(self) -> Dict[str, Any]:
        """Format parameters for POST request."""
        fields = {"action": self.get_action_name()}
        fields.update(self.params)
        return fields


class SendSMSAction(BaseAction):
    """Action for sending SMS messages."""

    ACTION_NAME = "post_sms"
    DEFAULT_PARAMS = {
        "message": None,
        "target": None,
        "phl_codename": None,
        "sender": None,
        "post_id": None,
        "period": None,
        "time_period": None,
        "time_local": None,
        "autotrimtext": None,
        "sms_type": None,
        "wap_url": None,
        "wap_expires": None,
    }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate SMS sending parameters."""
        # phl_codename and target are mutually exclusive
        if params.get("phl_codename") and params.get("target"):
            return False
        return True


class StatusAction(BaseAction):
    """Action for checking SMS status."""

    ACTION_NAME = "status"
    DEFAULT_PARAMS = {
        "sms_id": None,
        "sms_group_id": None,
        "date_from": None,
        "date_to": None,
    }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate status check parameters."""
        # At least one of sms_id, sms_group_id, or date_from+date_to must be provided
        if (
            not params.get("sms_id")
            and not params.get("sms_group_id")
            and (not params.get("date_from") or not params.get("date_to"))
        ):
            return False
        return True


class BalanceAction(BaseAction):
    """Action for checking account balance."""

    ACTION_NAME = "balance"
    DEFAULT_PARAMS = {}

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Balance action has no parameters to validate."""
        return True


class InboxAction(BaseAction):
    """Action for retrieving incoming messages."""

    ACTION_NAME = "inbox"
    DEFAULT_PARAMS = {
        "sib_num": None,
        "new_only": None,
        "date_from": None,
        "date_to": None,
        "phone": None,
        "prefix": None,
    }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate inbox parameters."""
        # sib_num is required according to original PHP code
        # But we make it optional here to allow flexibility
        return True


class BlacklistAction(BaseAction):
    """Action for retrieving blacklist."""

    ACTION_NAME = "blacklist"
    DEFAULT_PARAMS = {
        "perp": None,
        "page": None,
        "search": None,
    }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Blacklist retrieval has no required parameters."""
        return True


class BlacklistAddAction(BaseAction):
    """Action for adding phones to blacklist."""

    ACTION_NAME = "blacklist_add"
    DEFAULT_PARAMS = {
        "phones": None,
    }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate blacklist add parameters - phones is required."""
        if not params.get("phones"):
            return False
        return True


class BlacklistDeleteAction(BaseAction):
    """Action for removing phones from blacklist."""

    ACTION_NAME = "blacklist_delete"
    DEFAULT_PARAMS = {
        "phones": None,
    }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate blacklist delete parameters - phones is required."""
        if not params.get("phones"):
            return False
        return True
