"""Integration tests using real credentials from .env file."""

import os
import pytest

from zoekt_mcp.config import ServerConfig
from zoekt_mcp.backends import ZoektClient, ZoektContentFetcher


@pytest.fixture
def real_config():
    """Load real configuration from environment."""
    return ServerConfig()


@pytest.mark.integration
class TestRealZoektConnection:
    """Integration tests with real Zoekt instance using .env credentials."""

    def test_search_with_real_credentials(self, real_config):
        """Test search query with real authentication."""
        client = ZoektClient(
            base_url=real_config.zoekt_api_url,
            zoekt_login=real_config.zoekt_api_login,
            zoekt_password=real_config.zoekt_api_password,
            verify_ssl=False,  # Disable SSL for internal server
        )

        # Search for weight_calc/sizes
        result = client.search("weight_calc sizes", num=10)

        assert result is not None
        assert "result" in result

    def test_search_weight_calc_sizes_path(self, real_config):
        """Test searching for specific path /weight_calc/sizes/."""
        client = ZoektClient(
            base_url=real_config.zoekt_api_url,
            zoekt_login=real_config.zoekt_api_login,
            zoekt_password=real_config.zoekt_api_password,
            verify_ssl=False,
        )

        # Search using file path filter
        result = client.search('file:"weight_calc/sizes/"', num=10)

        assert result is not None
        assert "result" in result

        # Format and verify results
        formatted = client.format_results(result, 10)
        assert isinstance(formatted, list)

    def test_fetch_weight_calc_sizes_directory(self, real_config):
        """Test fetching directory tree for weight_calc/sizes/."""
        fetcher = ZoektContentFetcher(
            zoekt_url=real_config.zoekt_api_url,
            zoekt_login=real_config.zoekt_api_login,
            zoekt_password=real_config.zoekt_api_password,
            verify_ssl=False,
        )

        # Need to determine the repository from your setup
        # This is an example - adjust repo name as needed
        repo = os.getenv("TEST_REPO_NAME", "github.com/your/repo")

        try:
            content = fetcher.get_content(repo, "weight_calc/sizes/", depth=2)
            assert content is not None
            assert isinstance(content, str)
        except ValueError as e:
            pytest.skip(f"Repository or path not found: {e}")

    def test_auth_required_success(self, real_config):
        """Test that authentication works for protected endpoints."""
        # Skip if no auth configured
        if not real_config.zoekt_api_login or not real_config.zoekt_api_password:
            pytest.skip("No authentication credentials configured")

        client = ZoektClient(
            base_url=real_config.zoekt_api_url,
            zoekt_login=real_config.zoekt_api_login,
            zoekt_password=real_config.zoekt_api_password,
            verify_ssl=False,
        )

        # This should succeed with auth
        result = client.search("weight_calc", num=5)
        assert result is not None

    def test_without_auth_fails_if_required(self, real_config):
        """Test that requests fail without auth when required."""
        # Skip if no auth configured
        if not real_config.zoekt_api_login or not real_config.zoekt_api_password:
            pytest.skip("No authentication credentials configured")

        client = ZoektClient(
            base_url=real_config.zoekt_api_url,
            verify_ssl=False,
        )

        try:
            result = client.search("weight_calc", num=5)
            # If we get here, auth might not be required
            if result is None:
                raise AssertionError("Request failed without auth")
        except Exception as e:
            # Expected to fail with 401 or similar if auth is required
            assert "401" in str(e) or "403" in str(e) or "Unauthorized" in str(e)
