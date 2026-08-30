"""
Pydantic models for QTSMS Client request/response validation.

These models provide schema validation for API requests and responses,
supporting both form-urlencoded and JSON formats.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class SMSRequestBase(BaseModel):
    """Base model for SMS requests."""
    
    model_config = ConfigDict(extra='allow', populate_by_name=True)
    
    user: Optional[str] = Field(None, description="Username for authentication")
    pass_: Optional[str] = Field(None, alias="pass", description="Password for authentication")
    action: str = Field(..., description="Action type (post_sms, status, balance, etc.)")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid_actions = ['post_sms', 'status', 'balance', 'inbox', 'blacklist', 
                        'blacklist_add', 'blacklist_delete']
        if v not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of: {valid_actions}")
        return v


class SendSMSRequest(SMSRequestBase):
    """Model for sending SMS messages."""
    
    action: str = "post_sms"
    message: str = Field(..., min_length=1, description="SMS text content")
    target: Optional[str] = Field(None, description="Phone number(s) separated by commas")
    phl_codename: Optional[str] = Field(None, description="Contact list codename")
    sender: Optional[str] = Field(None, description="Sender name/number")
    post_id: Optional[str] = Field(None, description="Custom post identifier")
    period: Optional[str] = Field(None, description="Message validity period")
    time_period: Optional[str] = Field(None, description="Time period for delivery")
    time_local: Optional[str] = Field(None, description="Local time for delivery")
    autotrimtext: Optional[bool] = Field(None, description="Auto-trim long messages")
    sms_type: Optional[str] = Field(None, description="SMS type")
    wap_url: Optional[str] = Field(None, description="WAP URL")
    wap_expires: Optional[str] = Field(None, description="WAP expiration")
    shortenLinks: Optional[bool] = Field(None, description="Auto-shorten URLs in message")
    
    @model_validator(mode='after')
    def validate_target_or_phl(self):
        """Validate that either target or phl_codename is provided, but not both."""
        if not self.target and not self.phl_codename:
            raise ValueError("Either 'target' or 'phl_codename' must be specified")
        if self.target and self.phl_codename:
            raise ValueError("'target' and 'phl_codename' are mutually exclusive")
        return self
    
    @field_validator('target')
    @classmethod
    def validate_target_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v
        # Basic validation - should contain only digits, +, commas, and spaces
        import re
        if not re.match(r'^[\d\+\s,]+$', v):
            raise ValueError("Invalid phone number format")
        return v


class StatusRequest(SMSRequestBase):
    """Model for checking SMS status."""
    
    action: str = "status"
    sms_id: Optional[str] = Field(None, description="Specific SMS ID")
    sms_group_id: Optional[str] = Field(None, description="SMS group ID")
    date_from: Optional[str] = Field(None, description="Start date (dd.mm.yyyy hh:ii:ss)")
    date_to: Optional[str] = Field(None, description="End date (dd.mm.yyyy hh:ii:ss)")
    
    @model_validator(mode='after')
    def validate_status_params(self):
        """Validate that at least one search parameter is provided."""
        if not any([self.sms_id, self.sms_group_id, 
                   (self.date_from and self.date_to)]):
            raise ValueError(
                "At least one of sms_id, sms_group_id, or (date_from + date_to) "
                "must be provided"
            )
        return self


class BalanceRequest(SMSRequestBase):
    """Model for checking account balance."""
    
    action: str = "balance"


class InboxRequest(SMSRequestBase):
    """Model for retrieving incoming messages."""
    
    action: str = "inbox"
    sib_num: Optional[str] = Field(None, description="Short code number (inbox ID)")
    new_only: Optional[str] = Field(None, description="Only new messages (1 or 0)")
    date_from: Optional[str] = Field(None, description="Start date filter")
    date_to: Optional[str] = Field(None, description="End date filter")
    phone: Optional[str] = Field(None, description="Filter by phone number")
    prefix: Optional[str] = Field(None, description="Filter by prefix")


class BlacklistRequest(SMSRequestBase):
    """Model for retrieving blacklist."""
    
    action: str = "blacklist"
    perp: Optional[str] = Field(None, description="Entries per page")
    page: Optional[str] = Field(None, description="Page number")
    search: Optional[str] = Field(None, description="Search term")


class BlacklistAddRequest(SMSRequestBase):
    """Model for adding phones to blacklist."""
    
    action: str = "blacklist_add"
    phones: str = Field(..., description="Phone numbers (comma-separated or array)")


class BlacklistDeleteRequest(SMSRequestBase):
    """Model for removing phones from blacklist."""
    
    action: str = "blacklist_delete"
    phones: str = Field(..., description="Phone numbers (comma-separated or array)")


# Response Models

class SMSResponseAction(BaseModel):
    """Model for individual action result in response."""
    
    sms_group_id: Optional[str] = None
    id: Optional[str] = None
    sms_id: Optional[str] = None
    sms_type: Optional[str] = None
    phone: Optional[str] = None
    sms_res_count: Optional[str] = None
    message: Optional[str] = None
    action: Optional[str] = None
    # Status-specific fields
    created: Optional[str] = None
    aul_username: Optional[str] = None
    aul_client_addr: Optional[str] = None
    aul_proxy_addr: Optional[str] = None
    target: Optional[str] = None
    sender: Optional[str] = None
    sms_count: Optional[str] = None
    text: Optional[str] = None
    stc_code: Optional[str] = None
    sent: Optional[str] = None
    closed: Optional[str] = None
    close_time: Optional[str] = None
    status: Optional[str] = None


class SMSResponse(BaseModel):
    """Model for API response."""
    
    actions: Optional[List[SMSResponseAction]] = None
    agt_id: Optional[str] = None
    date_report: Optional[str] = None
    # For XML responses parsed to dict
    error: Optional[Dict[str, Any]] = None
    
    @property
    def has_error(self) -> bool:
        """Check if response contains an error."""
        return self.error is not None
    
    @property
    def error_code(self) -> Optional[int]:
        """Get error code if present."""
        if self.error and 'code' in self.error:
            try:
                return int(self.error['code'])
            except (ValueError, TypeError):
                return None
        return None
    
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if present."""
        if self.error and '#text' in self.error:
            return self.error['#text']
        return None


class TokenAuthConfig(BaseModel):
    """Configuration for token-based authentication."""
    
    api_key: str = Field(..., description="API token/key")
    use_json: bool = Field(True, description="Use JSON format for requests")
    rest_endpoint: bool = Field(True, description="Use /rest endpoint")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("API key cannot be empty")
        return v.strip()
