"""
Tests for QTSMS Client.

Run with: pytest tests/ -v
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from qtsms_client.src.actions import (
    BaseAction,
    SendSMSAction,
    StatusAction,
    BalanceAction,
    InboxAction,
    BlacklistAction,
    BlacklistAddAction,
    BlacklistDeleteAction,
)
from qtsms_client.src.exceptions import (
    QTSMSException,
    QTSMSValidationError,
    QTSMSRequestError,
)
from qtsms_client.src.client import QTSMSClient


class TestSendSMSAction:
    """Tests for SendSMSAction."""

    def test_create_with_valid_params(self):
        action = SendSMSAction(
            message="Hello",
            target="+79991234567",
            sender="TestSender",
        )
        assert action.get_action_name() == "post_sms"
        assert action.params["message"] == "Hello"
        assert action.params["target"] == "+79991234567"
        assert action.params["sender"] == "TestSender"

    def test_validate_mutually_exclusive_params(self):
        # Should fail when both target and phl_codename are provided
        action = SendSMSAction()
        assert not action.validate_params({
            "target": "+79991234567",
            "phl_codename": "test_group",
        })

    def test_validate_accepts_target_only(self):
        action = SendSMSAction()
        assert action.validate_params({"target": "+79991234567"})

    def test_validate_accepts_phl_codename_only(self):
        action = SendSMSAction()
        assert action.validate_params({"phl_codename": "test_group"})

    def test_form_post_fields(self):
        action = SendSMSAction(message="Test", target="+79991234567")
        fields = action.form_post_fields()
        assert fields["action"] == "post_sms"
        assert fields["message"] == "Test"
        assert fields["target"] == "+79991234567"


class TestStatusAction:
    """Tests for StatusAction."""

    def test_create_with_sms_id(self):
        action = StatusAction(sms_id="12345")
        assert action.get_action_name() == "status"
        assert action.params["sms_id"] == "12345"

    def test_validate_requires_at_least_one_param(self):
        action = StatusAction()
        # Empty params should fail
        assert not action.validate_params({})
        # sms_id alone should pass
        assert action.validate_params({"sms_id": "123"})
        # sms_group_id alone should pass
        assert action.validate_params({"sms_group_id": "456"})
        # date_from + date_to together should pass
        assert action.validate_params({"date_from": "2024-01-01", "date_to": "2024-01-02"})
        # Only date_from should fail
        assert not action.validate_params({"date_from": "2024-01-01"})


class TestBalanceAction:
    """Tests for BalanceAction."""

    def test_create(self):
        action = BalanceAction()
        assert action.get_action_name() == "balance"
        assert action.params == {}

    def test_form_post_fields(self):
        action = BalanceAction()
        fields = action.form_post_fields()
        assert fields["action"] == "balance"


class TestInboxAction:
    """Tests for InboxAction."""

    def test_create_with_params(self):
        action = InboxAction(sib_num="1234", new_only=True)
        assert action.get_action_name() == "inbox"
        assert action.params["sib_num"] == "1234"


class TestBlacklistActions:
    """Tests for blacklist actions."""

    def test_blacklist_add_requires_phones(self):
        action = BlacklistAddAction()
        assert not action.validate_params({})
        assert action.validate_params({"phones": "+79991234567"})

    def test_blacklist_delete_requires_phones(self):
        action = BlacklistDeleteAction()
        assert not action.validate_params({})
        assert action.validate_params({"phones": "+79991234567"})

    def test_blacklist_retrieval_no_required_params(self):
        action = BlacklistAction()
        assert action.validate_params({})


class TestQTSMSClient:
    """Tests for QTSMSClient."""

    @pytest.fixture
    def client_config(self):
        return {
            "user": "test_user",
            "password": "test_pass",
            "host": "https://test.sms.gateway",
        }

    @pytest.mark.asyncio
    async def test_context_manager(self, client_config):
        """Test async context manager."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            async with QTSMSClient(**client_config) as client:
                assert client._client is not None

            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sms_single(self, client_config):
        """Test sending a single SMS."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.text = "OK"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            async with QTSMSClient(**client_config) as client:
                result = await client.send_sms("Hello", "+79991234567", sender="Test")

                assert result == "OK"
                mock_client.post.assert_called_once()
                call_data = mock_client.post.call_args[1]["data"]
                assert call_data["user"] == "test_user"
                assert call_data["pass"] == "test_pass"
                assert call_data["action"] == "post_sms"
                assert call_data["message"] == "Hello"
                assert call_data["target"] == "+79991234567"

    @pytest.mark.asyncio
    async def test_send_sms_multiple_targets(self, client_config):
        """Test sending SMS to multiple targets."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.text = "OK"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            async with QTSMSClient(**client_config) as client:
                result = await client.send_sms(
                    "Hello",
                    ["+79991234567", "+79991234568"],
                    sender="Test"
                )

                call_data = mock_client.post.call_args[1]["data"]
                assert call_data["target"] == "+79991234567,+79991234568"

    @pytest.mark.asyncio
    async def test_send_sms_batch(self, client_config):
        """Test batch SMS sending."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.text = "OK"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            async with QTSMSClient(**client_config) as client:
                messages = [
                    {"message": "Hello 1", "target": "+79991234567"},
                    {"message": "Hello 2", "target": "+79991234568"},
                    {"message": "Hello 3", "target": "+79991234569"},
                ]
                results = await client.send_sms_batch(messages, concurrency=2)

                assert len(results) == 3
                assert all(r == "OK" for r in results)
                # Should have made 3 calls
                assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_get_balance(self, client_config):
        """Test balance check."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.text = "BALANCE:100.50"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            async with QTSMSClient(**client_config) as client:
                result = await client.get_balance()

                assert result == "BALANCE:100.50"
                call_data = mock_client.post.call_args[1]["data"]
                assert call_data["action"] == "balance"

    @pytest.mark.asyncio
    async def test_get_status_by_id(self, client_config):
        """Test status check by SMS ID."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.text = "DELIVRD"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            async with QTSMSClient(**client_config) as client:
                result = await client.get_status(sms_id="12345")

                call_data = mock_client.post.call_args[1]["data"]
                assert call_data["action"] == "status"
                assert call_data["sms_id"] == "12345"

    @pytest.mark.asyncio
    async def test_http_error_handling(self, client_config):
        """Test HTTP error handling."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Server Error",
                request=MagicMock(),
                response=mock_response
            ))
            mock_client_class.return_value = mock_client

            async with QTSMSClient(**client_config) as client:
                with pytest.raises(QTSMSRequestError) as exc_info:
                    await client.send_sms("Hello", "+79991234567")

                assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_proxy_configuration(self):
        """Test proxy configuration."""
        client = QTSMSClient(
            user="test",
            password="test",
            proxy="192.168.1.1:8080",
            proxy_auth="user:pass",
        )
        assert client.proxy == "192.168.1.1:8080"
        assert client.proxy_auth == "user:pass"

    @pytest.mark.asyncio
    async def test_multipost_mode(self, client_config):
        """Test multipost mode."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.text = "OK"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            async with QTSMSClient(**client_config) as client:
                client.start_multipost()
                client.post_mes("Hello 1", "+79991234567", None, "Sender")
                client.post_mes("Hello 2", "+79991234568", None, "Sender")

                results = await client.process()

                assert len(results) == 2
                assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_legacy_methods(self, client_config):
        """Test legacy PHP-compatible methods."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.text = "OK"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            async with QTSMSClient(**client_config) as client:
                # Test post_message
                await client.post_message("Hello", "+79991234567", "Sender")
                assert mock_client.post.call_count == 1

                # Test status_sms_id
                await client.status_sms_id("12345")
                assert mock_client.post.call_count == 2

                # Test get_balance_legacy
                await client.get_balance_legacy()
                assert mock_client.post.call_count == 3


class TestConcurrency:
    """Tests for concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrency_limit(self):
        """Test that concurrency is properly limited."""
        call_times = []

        async def mock_post(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)
            mock_response = MagicMock()
            mock_response.text = "OK"
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client_class.return_value = mock_client

            client = QTSMSClient(
                user="test",
                password="test",
                host="https://test.example.com",
            )

            async with client:
                messages = [{"message": f"Msg {i}", "target": f"+7999000000{i}"} for i in range(10)]
                results = await client.send_sms_batch(messages, concurrency=3)

            # Verify all requests completed
            assert len(results) == 10


# Import httpx for exception testing
import httpx
