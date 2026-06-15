import os
import pytest

from zoekt_mcp.config import ServerConfig


class TestServerConfig:
    def test_config_initialization_with_required_vars(self, monkeypatch):
        """Test ServerConfig initialization with required environment variables."""
        monkeypatch.setenv("ZOEKT_API_URL", "https://zoekt.example.com")
        monkeypatch.setenv("ZOEKT_API_LOGIN", "test_user")
        monkeypatch.setenv("ZOEKT_API_PASSWORD", "test_pass")

        config = ServerConfig()

        assert config.zoekt_api_url == "https://zoekt.example.com"
        assert config.zoekt_api_login == "test_user"
        assert config.zoekt_api_password == "test_pass"

    def test_config_without_auth_credentials(self, monkeypatch):
        """Test ServerConfig without auth credentials."""
        monkeypatch.setenv("ZOEKT_API_URL", "https://zoekt.example.com")
        monkeypatch.delenv("ZOEKT_API_LOGIN", raising=False)
        monkeypatch.delenv("ZOEKT_API_PASSWORD", raising=False)

        config = ServerConfig()

        assert config.zoekt_api_url == "https://zoekt.example.com"
        assert config.zoekt_api_login is None
        assert config.zoekt_api_password is None

    def test_config_partial_auth(self, monkeypatch):
        """Test ServerConfig with only login set (no password)."""
        monkeypatch.setenv("ZOEKT_API_URL", "https://zoekt.example.com")
        monkeypatch.setenv("ZOEKT_API_LOGIN", "test_user")
        monkeypatch.delenv("ZOEKT_API_PASSWORD", raising=False)

        config = ServerConfig()

        assert config.zoekt_api_login == "test_user"
        assert config.zoekt_api_password is None

    def test_config_default_ports(self, monkeypatch):
        """Test default port values."""
        monkeypatch.setenv("ZOEKT_API_URL", "https://zoekt.example.com")

        config = ServerConfig()

        assert config.sse_port == 8000
        assert config.streamable_http_port == 8080

    def test_config_custom_ports(self, monkeypatch):
        """Test custom port values."""
        monkeypatch.setenv("ZOEKT_API_URL", "https://zoekt.example.com")
        monkeypatch.setenv("MCP_SSE_PORT", "9000")
        monkeypatch.setenv("MCP_STREAMABLE_HTTP_PORT", "9001")

        config = ServerConfig()

        assert config.sse_port == 9000
        assert config.streamable_http_port == 9001

    def test_config_missing_required_url(self, monkeypatch):
        """Test error when required ZOEKT_API_URL is missing."""
        monkeypatch.delenv("ZOEKT_API_URL", raising=False)

        with pytest.raises(ValueError, match="Required environment variable ZOEKT_API_URL is not set"):
            ServerConfig()

    def test_get_required_env_error_message(self, monkeypatch):
        """Test descriptive error message for missing required env var."""
        monkeypatch.delenv("ZOEKT_API_URL", raising=False)

        with pytest.raises(ValueError) as exc_info:
            ServerConfig()

        assert "ZOEKT_API_URL" in str(exc_info.value)
        assert "is not set" in str(exc_info.value)
