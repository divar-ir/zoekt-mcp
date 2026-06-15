"""Smoke tests for ZoektMCPServer initialization."""

import pytest

from zoekt_mcp.config import ServerConfig
from zoekt_mcp.server import ZoektMCPServer


class TestZoektMCPServerInit:
    """Tests that server initializes correctly - catches API breakage."""

    def test_server_initialization(self, monkeypatch):
        """Smoke test - server should initialize without errors."""
        monkeypatch.setenv("ZOEKT_API_URL", "https://zoekt.example.com")
        monkeypatch.setenv("ZOEKT_API_LOGIN", "test_user")
        monkeypatch.setenv("ZOEKT_API_PASSWORD", "test_pass")

        config = ServerConfig()
        server = ZoektMCPServer(config)

        assert server.server is not None
        assert server.search_client is not None
        assert server.content_fetcher is not None
        assert server._shutdown_requested is False

    def test_server_initialization_without_auth(self, monkeypatch):
        """Server should initialize without auth credentials."""
        monkeypatch.setenv("ZOEKT_API_URL", "https://zoekt.example.com")
        monkeypatch.delenv("ZOEKT_API_LOGIN", raising=False)
        monkeypatch.delenv("ZOEKT_API_PASSWORD", raising=False)

        config = ServerConfig()
        server = ZoektMCPServer(config)

        assert server.server is not None

    def test_server_registers_tools(self, monkeypatch):
        """Server should register MCP tools without errors."""
        monkeypatch.setenv("ZOEKT_API_URL", "https://zoekt.example.com")

        config = ServerConfig()
        server = ZoektMCPServer(config)
        server._register_tools()

        assert server.search_tool_description is not None
        assert server.fetch_content_description is not None

    def test_server_loads_prompts(self, monkeypatch):
        """Server should load prompts during initialization."""
        monkeypatch.setenv("ZOEKT_API_URL", "https://zoekt.example.com")

        config = ServerConfig()
        server = ZoektMCPServer(config)

        assert server.codesearch_guide is not None
        assert server.search_tool_description is not None
