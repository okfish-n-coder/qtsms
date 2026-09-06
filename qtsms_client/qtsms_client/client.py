"""
Async HTTP client for QTSMS gateway.

Optimized for high-throughput SMS sending with connection pooling,
concurrent requests, and efficient resource management.

Supports both traditional username/password authentication and
token-based authentication via X-ApiKey header.
"""

import asyncio
import json
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urlparse, urlunparse

import httpx

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
    QTSMSRequestError,
    QTSMSValidationError,
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
    # Actions
    "BaseAction",
    "SendSMSAction",
    "StatusAction",
    "BalanceAction",
    "InboxAction",
    "BlacklistAction",
    "BlacklistAddAction",
    "BlacklistDeleteAction",
    # Exceptions
    "QTSMSException",
    "QTSMSValidationError",
    "QTSMSRequestError",
    "QTSMSAuthError",
    "QTMSErrorCode",
    "QTMSParseResponseError",
    # Schemas
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


class QTSMSClient:
    """
    Async client for Beeline A2P SMS Gateway.

    Designed for high-throughput SMS sending with support for:
    - Connection pooling via httpx.AsyncClient
    - Concurrent requests using asyncio.gather
    - Batch SMS operations
    - Proxy support
    - SSL certificate validation control
    - Token-based authentication (X-ApiKey header)
    - JSON format requests/responses

    Usage with username/password:
        async with QTSMSClient(user="login", password="pass", host="sms.beeline.ru") as client:
            # Send single SMS
            result = await client.send_sms("Hello", "+79991234567", sender="MyCompany")

            # Send multiple SMS concurrently
            results = await client.send_sms_batch([
                {"message": "Hello 1", "target": "+79991234567"},
                {"message": "Hello 2", "target": "+79991234568"},
            ])

            # Check balance
            balance = await client.get_balance()

    Usage with API token:
        async with QTSMSClient.with_token_auth(
            api_key="your_api_token",
            host="sms.beeline.ru"
        ) as client:
            # Send SMS using token auth
            result = await client.send_sms_json(
                message="Hello",
                target="+79991234567",
                sender="MyCompany"
            )
    """

    DEFAULT_HOST = "https://a2p-sms.beeline.ru"
    DEFAULT_PATH = "/public/http/"
    REST_PATH = "/proto/http/rest"  # For JSON/token auth
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_MAX_CONNECTIONS = 100
    DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 50

    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        path: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
        cert_path: Optional[str] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[str] = None,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        max_keepalive_connections: int = DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
        api_key: Optional[str] = None,
        use_json: bool = False,
    ):
        """
        Initialize the QTSMS client.

        Args:
            user: Username for authentication (optional if using api_key)
            password: Password for authentication (optional if using api_key)
            host: SMS gateway hostname (with or without scheme)
            path: API endpoint path (use REST_PATH for JSON/token auth)
            timeout: Request timeout in seconds
            verify_ssl: Enable SSL certificate verification
            cert_path: Path to CA certificate file
            proxy: Proxy server address (format: "ip:port" or "http://ip:port")
            proxy_auth: Proxy authentication (format: "username:password")
            max_connections: Maximum number of connections in the pool
            max_keepalive_connections: Maximum keep-alive connections
            api_key: API token for authentication (alternative to user/password)
            use_json: Use JSON format for requests (required for token auth)
        """
        self.user = user
        self.password = password
        self.api_key = api_key
        self.use_json = use_json
        
        # Determine base URL based on auth method
        if api_key and use_json:
            # Token auth requires /rest endpoint
            default_path = self.REST_PATH
        else:
            default_path = self.DEFAULT_PATH
            
        self.base_url = self._build_base_url(host or self.DEFAULT_HOST, path or default_path)
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.cert_path = cert_path
        self.proxy = proxy
        self.proxy_auth = proxy_auth

        # Connection pool settings for high throughput
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections

        self._client: Optional[httpx.AsyncClient] = None
        self._multipost_mode = False
        self._pending_actions: List[BaseAction] = []
        
        # Validate auth configuration
        if not user and not password and not api_key:
            raise QTSMSValidationError("Either user/password or api_key must be provided")
        if api_key and (user or password):
            raise QTSMSValidationError("Cannot use both api_key and user/password authentication")

    @classmethod
    def with_token_auth(
        cls,
        api_key: str,
        host: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
        cert_path: Optional[str] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[str] = None,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        max_keepalive_connections: int = DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
    ) -> "QTSMSClient":
        """
        Create a client instance with token-based authentication.

        Token auth uses X-ApiKey header and JSON format as per Beeline API docs.
        The /rest endpoint is automatically used.

        Args:
            api_key: Your API token from Beeline A2P cabinet
            host: SMS gateway hostname
            timeout: Request timeout in seconds
            verify_ssl: Enable SSL certificate verification
            cert_path: Path to CA certificate file
            proxy: Proxy server address
            proxy_auth: Proxy authentication
            max_connections: Maximum number of connections
            max_keepalive_connections: Maximum keep-alive connections

        Returns:
            QTSMSClient instance configured for token auth

        Example:
            async with QTSMSClient.with_token_auth(
                api_key="GvEqzI1TSmw7bDn)JC4wG424u8Po5txpC7S$tiU:KJ/x4I+Udb"
            ) as client:
                result = await client.send_sms_json(
                    message="Hello",
                    target="+79991234567",
                    sender="MyCompany"
                )
        """
        config = TokenAuthConfig(api_key=api_key)
        return cls(
            api_key=config.api_key,
            host=host,
            path=cls.REST_PATH,
            timeout=timeout,
            verify_ssl=verify_ssl,
            cert_path=cert_path,
            proxy=proxy,
            proxy_auth=proxy_auth,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            use_json=True,
        )

    def _build_base_url(self, host: str, path: str) -> str:
        """Build base URL ensuring proper scheme."""
        parsed = urlparse(host)
        if not parsed.scheme:
            host = f"https://{host}"
            parsed = urlparse(host)
        return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))

    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _create_client(self):
        """Create the underlying HTTP client with optimized settings."""
        limits = httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_keepalive_connections,
        )

        transport = httpx.AsyncHTTPTransport(limits=limits)

        # Set headers based on auth method
        if self.api_key:
            # Token authentication via X-ApiKey header (as per Beeline API docs)
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": "AISMS Python Client",
                "X-ApiKey": f"ApiKey {self.api_key}",
            }
        else:
            # Traditional username/password authentication
            content_type = "application/json" if self.use_json else "application/x-www-form-urlencoded; charset=UTF-8"
            headers = {
                "Content-Type": content_type,
                "User-Agent": "AISMS Python Client",
            }

        proxies = None
        if self.proxy:
            proxy_url = self.proxy
            if "://" not in proxy_url:
                proxy_url = f"http://{proxy_url}"
            if self.proxy_auth:
                # Insert auth into proxy URL
                parsed = urlparse(proxy_url)
                proxy_url = urlunparse((
                    parsed.scheme,
                    f"{self.proxy_auth}@{parsed.netloc}",
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
            proxies = {"all://": proxy_url}

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            verify=self.cert_path if self.cert_path else self.verify_ssl,
            transport=transport,
            headers=headers,
            proxies=proxies,
        )

    async def close(self):
        """Close the HTTP client and release resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_auth_params(self) -> Dict[str, Any]:
        """Get authentication parameters for requests."""
        if self.api_key:
            # Token auth doesn't need user/pass in request body
            return {}
        return {
            "user": self.user,
            "pass": self.password,
            "gzip": "none",
            "HTTP_ACCEPT_LANGUAGE": "",
            "CLIENTADR": "",
            "comment": "",
        }

    async def execute(self, action: BaseAction) -> str:
        """
        Execute a single action.

        Args:
            action: The action to execute

        Returns:
            Server response as string
        """
        if not self._client:
            await self._create_client()

        if self.use_json or self.api_key:
            # JSON format request
            post_data = self._get_auth_params()
            post_data.update(action.form_post_fields())
            
            try:
                response = await self._client.post("", json=post_data)
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as e:
                raise QTSMSRequestError(
                    f"HTTP error: {e.response.status_code}",
                    status_code=e.response.status_code,
                    response=e.response.text,
                )
            except httpx.RequestError as e:
                raise QTSMSRequestError(f"Request failed: {str(e)}")
        else:
            # Form-urlencoded request (traditional)
            post_data = self._get_auth_params()
            post_data.update(action.form_post_fields())

            try:
                response = await self._client.post("", data=post_data)
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as e:
                raise QTSMSRequestError(
                    f"HTTP error: {e.response.status_code}",
                    status_code=e.response.status_code,
                    response=e.response.text,
                )
            except httpx.RequestError as e:
                raise QTSMSRequestError(f"Request failed: {str(e)}")

    async def execute_json(self, payload: Dict[str, Any]) -> SMSResponse:
        """
        Execute a raw JSON request with validation.

        Args:
            payload: JSON payload dictionary

        Returns:
            Parsed SMSResponse object
            
        Raises:
            QTSMSValidationError: If payload validation fails
            QTSMSRequestError: If request fails
            QTMSParseResponseError: If response parsing fails
        """
        if not self._client:
            await self._create_client()

        # Validate payload based on action type
        action = payload.get("action")
        try:
            if action == "post_sms":
                validated = SendSMSRequest(**payload)
            elif action == "status":
                validated = StatusRequest(**payload)
            elif action == "balance":
                validated = BalanceRequest(**payload)
            elif action == "inbox":
                validated = InboxRequest(**payload)
            elif action == "blacklist":
                validated = BlacklistRequest(**payload)
            elif action == "blacklist_add":
                validated = BlacklistAddRequest(**payload)
            elif action == "blacklist_delete":
                validated = BlacklistDeleteRequest(**payload)
            else:
                raise QTSMSValidationError(f"Unknown action: {action}")
        except Exception as e:
            if isinstance(e, QTSMSValidationError):
                raise
            raise QTSMSValidationError(f"Invalid request payload: {str(e)}")

        try:
            response = await self._client.post("", json=payload)
            response.raise_for_status()
            
            # Parse JSON response
            try:
                response_data = response.json()
                return SMSResponse(**response_data)
            except Exception as parse_error:
                raise QTMSParseResponseError(
                    f"Failed to parse response: {str(parse_error)}",
                    raw_response=response.text
                )
        except httpx.HTTPStatusError as e:
            # Try to parse error from response
            error_msg = f"HTTP error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_code = error_data["error"].get("code")
                    if error_code:
                        human_msg = QTMSErrorCode.get_error_message(int(error_code))
                        error_msg = f"{error_msg} - {human_msg}"
            except:
                pass
            raise QTSMSRequestError(
                error_msg,
                status_code=e.response.status_code,
                response=e.response.text,
            )
        except httpx.RequestError as e:
            raise QTSMSRequestError(f"Request failed: {str(e)}")

    async def send_sms_json(
        self,
        message: str,
        target: Union[str, List[str]],
        sender: Optional[str] = None,
        phl_codename: Optional[str] = None,
        post_id: Optional[str] = None,
        period: Optional[str] = None,
        shorten_links: bool = False,
        **kwargs,
    ) -> SMSResponse:
        """
        Send SMS using JSON format with Pydantic validation.

        Supports both traditional and token-based authentication.

        Args:
            message: SMS text content
            target: Phone number(s) - single string or list
            sender: Sender name/number
            phl_codename: Contact list codename (alternative to target)
            post_id: Custom post identifier
            period: Message validity period
            shorten_links: Auto-shorten URLs in message
            **kwargs: Additional parameters

        Returns:
            SMSResponse object with parsed response data
            
        Example:
            result = await client.send_sms_json(
                message="Hello World",
                target="+79991234567",
                sender="MyCompany",
                shorten_links=True
            )
            print(f"SMS ID: {result.actions[0].id if result.actions else 'N/A'}")
        """
        if isinstance(target, list):
            target = ",".join(str(t) for t in target)

        payload = {
            "action": "post_sms",
            "message": message,
            "target": target,
        }
        
        if sender:
            payload["sender"] = sender
        if phl_codename:
            payload["phl_codename"] = phl_codename
        if post_id:
            payload["post_id"] = post_id
        if period:
            payload["period"] = period
        if shorten_links:
            payload["shortenLinks"] = True
            
        payload.update(kwargs)
        
        # Add auth params if using user/password
        if not self.api_key:
            payload["user"] = self.user
            payload["pass"] = self.password

        return await self.execute_json(payload)

    async def execute_batch(
        self,
        actions: List[BaseAction],
        concurrency: int = 10,
    ) -> List[str]:
        """
        Execute multiple actions concurrently.

        Args:
            actions: List of actions to execute
            concurrency: Maximum concurrent requests

        Returns:
            List of server responses
        """
        if not self._client:
            await self._create_client()

        semaphore = asyncio.Semaphore(concurrency)

        async def execute_with_semaphore(action: BaseAction) -> str:
            async with semaphore:
                return await self.execute(action)

        tasks = [execute_with_semaphore(action) for action in actions]
        return await asyncio.gather(*tasks, return_exceptions=False)

    # === High-level API methods ===

    async def send_sms(
        self,
        message: str,
        target: Union[str, List[str]],
        sender: Optional[str] = None,
        phl_codename: Optional[str] = None,
        post_id: Optional[str] = None,
        period: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Send an SMS message.

        Args:
            message: SMS text content
            target: Phone number(s) - single string or list of numbers
            sender: Sender name/number
            phl_codename: Alternative to target for predefined groups
            post_id: Custom post identifier
            period: Message validity period
            **kwargs: Additional parameters (time_period, time_local, etc.)

        Returns:
            Server response
        """
        if isinstance(target, list):
            target = ",".join(str(t) for t in target)

        action = SendSMSAction(
            message=message,
            target=target,
            sender=sender,
            phl_codename=phl_codename,
            post_id=post_id,
            period=period,
            **kwargs,
        )
        return await self.execute(action)

    async def send_sms_batch(
        self,
        messages: List[Dict[str, Any]],
        concurrency: int = 20,
    ) -> List[str]:
        """
        Send multiple SMS messages concurrently.

        Optimized for high-throughput scenarios. Each message is sent
        as a separate request but executed concurrently.

        Args:
            messages: List of message dicts with keys:
                      - message (required)
                      - target (required)
                      - sender (optional)
                      - phl_codename (optional)
                      - post_id (optional)
                      - period (optional)
            concurrency: Number of concurrent requests (default: 20)

        Returns:
            List of server responses in same order as input messages

        Example:
            >>> results = await client.send_sms_batch([
            ...     {"message": "Hello", "target": "+79991234567"},
            ...     {"message": "World", "target": "+79991234568"},
            ... ], concurrency=50)
        """
        actions = []
        for msg in messages:
            action = SendSMSAction(**msg)
            actions.append(action)

        return await self.execute_batch(actions, concurrency=concurrency)

    async def get_balance(self) -> str:
        """
        Check account balance.

        Returns:
            Server response with balance information
        """
        action = BalanceAction()
        return await self.execute(action)

    async def get_status(
        self,
        sms_id: Optional[str] = None,
        sms_group_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> str:
        """
        Get SMS delivery status.

        At least one of sms_id, sms_group_id, or (date_from + date_to)
        must be provided.

        Args:
            sms_id: Specific SMS ID
            sms_group_id: SMS group ID
            date_from: Start date for range query
            date_to: End date for range query

        Returns:
            Server response with status information
        """
        action = StatusAction(
            sms_id=sms_id,
            sms_group_id=sms_group_id,
            date_from=date_from,
            date_to=date_to,
        )
        return await self.execute(action)

    async def get_inbox(
        self,
        sib_num: Optional[str] = None,
        new_only: bool = False,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        phone: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> str:
        """
        Retrieve incoming messages.

        Args:
            sib_num: Short code number
            new_only: Only new messages
            date_from: Start date filter
            date_to: End date filter
            phone: Filter by phone number
            prefix: Filter by prefix

        Returns:
            Server response with inbox messages
        """
        action = InboxAction(
            sib_num=sib_num,
            new_only="1" if new_only else None,
            date_from=date_from,
            date_to=date_to,
            phone=phone,
            prefix=prefix,
        )
        return await self.execute(action)

    async def get_blacklist(
        self,
        per_page: Optional[int] = None,
        page: Optional[int] = None,
        search: Optional[str] = None,
    ) -> str:
        """
        Retrieve blacklist entries.

        Args:
            per_page: Entries per page
            page: Page number
            search: Search term

        Returns:
            Server response with blacklist entries
        """
        action = BlacklistAction(
            perp=str(per_page) if per_page else None,
            page=str(page) if page else None,
            search=search,
        )
        return await self.execute(action)

    async def add_to_blacklist(self, phones: Union[str, List[str]]) -> str:
        """
        Add phone numbers to blacklist.

        Args:
            phones: Single phone number or list of numbers

        Returns:
            Server response
        """
        if isinstance(phones, list):
            phones = ",".join(str(p) for p in phones)

        action = BlacklistAddAction(phones=phones)
        return await self.execute(action)

    async def remove_from_blacklist(self, phones: Union[str, List[str]]) -> str:
        """
        Remove phone numbers from blacklist.

        Args:
            phones: Single phone number or list of numbers

        Returns:
            Server response
        """
        if isinstance(phones, list):
            phones = ",".join(str(p) for p in phones)

        action = BlacklistDeleteAction(phones=phones)
        return await self.execute(action)

    # === Legacy compatibility methods (matching PHP interface) ===

    def start_multipost(self):
        """Enable multipost mode for batching actions."""
        self._multipost_mode = True
        self._pending_actions = []

    async def process(self) -> List[str]:
        """Process all pending actions in multipost mode."""
        if not self._multipost_mode:
            raise QTSMSException("Call start_multipost() first")

        try:
            results = await self.execute_batch(self._pending_actions)
            return results
        finally:
            self._multipost_mode = False
            self._pending_actions = []

    def post_mes(
        self,
        mes: str,
        target: str,
        phl_codename: str,
        sender: str,
        post_id: Optional[str] = None,
        period: Optional[str] = None,
    ):
        """Legacy method for adding SMS to multipost queue."""
        action = SendSMSAction(
            message=mes,
            target=target,
            phl_codename=phl_codename,
            sender=sender,
            post_id=post_id,
            period=period,
        )
        if self._multipost_mode:
            self._pending_actions.append(action)
        else:
            return self.execute(action)

    def post_message(
        self,
        mes: str,
        target: Union[str, List[str]],
        sender: Optional[str] = None,
        post_id: Optional[str] = None,
        period: bool = False,
    ):
        """Legacy method for sending SMS."""
        if isinstance(target, list):
            target = ",".join(str(t) for t in target)
        return self.post_mes(mes, target, None, sender, post_id, str(period) if period else None)

    def post_message_phl(
        self,
        mes: str,
        phl_codename: str,
        sender: Optional[str] = None,
        post_id: Optional[str] = None,
        period: bool = False,
    ):
        """Legacy method for sending SMS to PHL codename."""
        return self.post_mes(mes, None, phl_codename, sender, post_id, str(period) if period else None)

    def status_sms(
        self,
        date_from: str,
        date_to: str,
        smstype: str,
        sms_group_id: str,
        sms_id: str,
    ):
        """Legacy method for checking status."""
        action = StatusAction(
            sms_id=sms_id or None,
            sms_group_id=sms_group_id or None,
            date_from=date_from or None,
            date_to=date_to or None,
        )
        if self._multipost_mode:
            self._pending_actions.append(action)
        else:
            return self.execute(action)

    def status_sms_id(self, sms_id: str):
        """Legacy method for checking status by SMS ID."""
        return self.status_sms(None, None, None, None, sms_id)

    def status_sms_group_id(self, sms_group_id: str):
        """Legacy method for checking status by group ID."""
        return self.status_sms(None, None, sms_group_id, None, None)

    def status_sms_date(self, date_from: str, date_to: str, smstype: str = "SENDSMS"):
        """Legacy method for checking status by date range."""
        return self.status_sms(date_from, date_to, smstype, None, None)

    def get_balance_legacy(self):
        """Legacy method for getting balance."""
        action = BalanceAction()
        if self._multipost_mode:
            self._pending_actions.append(action)
        else:
            return self.execute(action)

    def inbox_sms(
        self,
        new_only: bool = False,
        sib_num: str = None,
        date_from: str = None,
        date_to: str = None,
        phone: str = None,
        prefix: str = None,
    ):
        """Legacy method for getting inbox."""
        action = InboxAction(
            sib_num=sib_num,
            new_only="1" if new_only else None,
            date_from=date_from,
            date_to=date_to,
            phone=phone,
            prefix=prefix,
        )
        if self._multipost_mode:
            self._pending_actions.append(action)
        else:
            return self.execute(action)
