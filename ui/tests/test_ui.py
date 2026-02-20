#!/usr/bin/env python3
"""
MedeX UI - Tests
================
Comprehensive tests for MedeX Reflex UI components.
"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# State Tests
# =============================================================================


class TestMedeXState:
    """Tests for MedeXState."""

    def test_initial_state(self):
        """Test initial state values."""
        from medex_ui.state import MedeXState

        state = MedeXState()

        assert state.messages == []
        assert state.current_input == ""
        assert state.is_loading is False
        assert state.user_type == "educational"
        assert state.language == "es"

    def test_has_messages_computed(self):
        """Test has_messages computed property."""
        from medex_ui.state import MedeXState, ChatMessage

        state = MedeXState()
        assert state.has_messages is False

        state.messages = [ChatMessage(content="Test")]
        assert state.has_messages is True

    def test_user_type_display(self):
        """Test user type display labels."""
        from medex_ui.state import MedeXState

        state = MedeXState()

        state.user_type = "educational"
        assert state.user_type_display == "Educativo"

        state.user_type = "professional"
        assert state.user_type_display == "Profesional"

    def test_set_input(self):
        """Test set_input method."""
        from medex_ui.state import MedeXState

        state = MedeXState()
        state.set_input("Test query")

        assert state.current_input == "Test query"

    def test_toggle_sidebar(self):
        """Test sidebar toggle."""
        from medex_ui.state import MedeXState

        state = MedeXState()
        initial = state.sidebar_open

        state.toggle_sidebar()
        assert state.sidebar_open != initial

    def test_clear_chat(self):
        """Test clear chat."""
        from medex_ui.state import MedeXState, ChatMessage

        state = MedeXState()
        state.messages = [ChatMessage(content="Test")]
        state.current_is_emergency = True

        state.clear_chat()

        assert state.messages == []
        assert state.current_is_emergency is False

    def test_export_session(self):
        """Test session export."""
        import json
        from medex_ui.state import MedeXState, ChatMessage

        state = MedeXState()
        state.session_start = "2025-01-07T10:00:00"
        state.messages = [
            ChatMessage(role="user", content="Test", timestamp="2025-01-07T10:01:00")
        ]
        state.total_queries = 5

        exported = state.export_session()
        data = json.loads(exported)

        assert data["session_start"] == "2025-01-07T10:00:00"
        assert len(data["messages"]) == 1
        assert data["stats"]["total_queries"] == 5


# =============================================================================
# ChatMessage Tests
# =============================================================================


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_default_values(self):
        """Test default values."""
        from medex_ui.state import ChatMessage

        msg = ChatMessage()

        assert msg.role == "user"
        assert msg.content == ""
        assert msg.is_emergency is False
        assert msg.is_streaming is False

    def test_custom_values(self):
        """Test custom values."""
        from medex_ui.state import ChatMessage

        msg = ChatMessage(
            id="test-1",
            role="assistant",
            content="Response text",
            is_emergency=True,
        )

        assert msg.id == "test-1"
        assert msg.role == "assistant"
        assert msg.content == "Response text"
        assert msg.is_emergency is True


# =============================================================================
# API Client Tests
# =============================================================================


class TestMedeXAPIClient:
    """Tests for API client."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        from medex_ui.api_bridge import MedeXAPIClient

        client = MedeXAPIClient()

        with patch.object(client, "client") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "healthy"}
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await client.health_check()

            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_error(self):
        """Test health check with error."""
        from medex_ui.api_bridge import MedeXAPIClient

        client = MedeXAPIClient()

        with patch.object(client, "client") as mock_client:
            mock_client.get = AsyncMock(side_effect=Exception("Connection failed"))

            result = await client.health_check()

            assert result["status"] == "error"
            assert "Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_query(self):
        """Test query endpoint."""
        from medex_ui.api_bridge import MedeXAPIClient

        client = MedeXAPIClient()

        with patch.object(client, "client") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "response": "Test response",
                "is_emergency": False,
            }
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await client.query("What is diabetes?")

            assert result["response"] == "Test response"
            mock_client.post.assert_called_once()


# =============================================================================
# Component Tests
# =============================================================================


class TestComponents:
    """Tests for UI components."""

    def test_medex_logo(self):
        """Test logo component."""
        from medex_ui.components import medex_logo

        component = medex_logo()
        assert component is not None

    def test_user_type_badge_educational(self):
        """Test educational badge."""
        from medex_ui.components import user_type_badge

        badge = user_type_badge("educational")
        assert badge is not None

    def test_user_type_badge_emergency(self):
        """Test emergency badge."""
        from medex_ui.components import user_type_badge

        badge = user_type_badge("educational", is_emergency=True)
        assert badge is not None

    def test_chat_input(self):
        """Test chat input component."""
        from medex_ui.components import chat_input

        component = chat_input()
        assert component is not None

    def test_sidebar(self):
        """Test sidebar component."""
        from medex_ui.components import sidebar

        component = sidebar()
        assert component is not None

    def test_header(self):
        """Test header component."""
        from medex_ui.components import header

        component = header()
        assert component is not None


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests."""

    def test_full_index_page(self):
        """Test full index page renders."""
        from medex_ui.medex_ui import index

        page = index()
        assert page is not None

    def test_app_configuration(self):
        """Test app is configured correctly."""
        from medex_ui.medex_ui import app

        assert app is not None


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
