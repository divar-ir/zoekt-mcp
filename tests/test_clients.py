import pytest
import requests_mock

from zoekt_mcp.backends import ZoektClient, ZoektContentFetcher


class TestZoektClient:
    def test_client_without_auth(self):
        """Test ZoektClient initialization without auth."""
        client = ZoektClient(base_url="https://zoekt.example.com")

        assert client.base_url == "https://zoekt.example.com"
        assert client.session.auth is None

    def test_client_with_auth(self):
        """Test ZoektClient initialization with auth credentials."""
        client = ZoektClient(
            base_url="https://zoekt.example.com",
            zoekt_login="test_user",
            zoekt_password="test_pass",
        )

        assert client.base_url == "https://zoekt.example.com"
        assert client.session.auth is not None
        assert client.session.auth.username == "test_user"
        assert client.session.auth.password == "test_pass"

    def test_client_with_partial_auth(self):
        """Test ZoektClient with only login (no password)."""
        client = ZoektClient(
            base_url="https://zoekt.example.com",
            zoekt_login="test_user",
        )

        assert client.session.auth is None

    def test_search_without_auth(self, mock_zoekt_response, mock_search_params):
        """Test search without authentication."""
        client = ZoektClient(base_url="https://zoekt.example.com")

        with requests_mock.Mocker() as m:
            m.get("https://zoekt.example.com/search", json=mock_zoekt_response)
            result = client.search("test", 10)

            assert m.called
            assert m.last_request.headers.get("Authorization") is None
            assert result == mock_zoekt_response

    def test_search_with_auth(self, mock_zoekt_response, mock_search_params):
        """Test search with authentication."""
        client = ZoektClient(
            base_url="https://zoekt.example.com",
            zoekt_login="test_user",
            zoekt_password="test_pass",
        )

        with requests_mock.Mocker() as m:
            m.get("https://zoekt.example.com/search", json=mock_zoekt_response)
            result = client.search("test", 10)

            assert m.called
            auth_header = m.last_request.headers.get("Authorization")
            assert auth_header is not None
            assert "Basic" in auth_header
            assert result == mock_zoekt_response

    def test_search_http_error(self):
        """Test search with HTTP error response."""
        import requests

        client = ZoektClient(base_url="https://zoekt.example.com")

        with requests_mock.Mocker() as m:
            m.get("https://zoekt.example.com/search", status_code=401)

            with pytest.raises(requests.exceptions.HTTPError):
                client.search("test", 10)

    def test_format_results(self, mock_zoekt_response):
        """Test formatting search results."""
        client = ZoektClient(base_url="https://zoekt.example.com")
        results = client.format_results(mock_zoekt_response, 10)

        assert len(results) == 1
        assert results[0].filename == "test.py"
        assert results[0].repository == "github.com/test/repo"
        assert len(results[0].matches) == 1
        assert results[0].matches[0].line_number == 10


class TestZoektContentFetcher:
    def test_fetcher_without_auth(self):
        """Test ZoektContentFetcher initialization without auth."""
        fetcher = ZoektContentFetcher(zoekt_url="https://zoekt.example.com")

        assert fetcher.zoekt_url == "https://zoekt.example.com"
        assert fetcher.session.auth is None

    def test_fetcher_with_auth(self):
        """Test ZoektContentFetcher initialization with auth credentials."""
        fetcher = ZoektContentFetcher(
            zoekt_url="https://zoekt.example.com",
            zoekt_login="test_user",
            zoekt_password="test_pass",
        )

        assert fetcher.zoekt_url == "https://zoekt.example.com"
        assert fetcher.session.auth is not None
        assert fetcher.session.auth.username == "test_user"
        assert fetcher.session.auth.password == "test_pass"

    def test_fetcher_search_with_auth(self):
        """Test ZoektContentFetcher search with authentication."""
        fetcher = ZoektContentFetcher(
            zoekt_url="https://zoekt.example.com",
            zoekt_login="test_user",
            zoekt_password="test_pass",
        )

        mock_response = {"result": {"FileMatches": []}}

        with requests_mock.Mocker() as m:
            m.get("https://zoekt.example.com/search", json=mock_response)
            result = fetcher._fetch_zoekt_data("test/repo", ".")

            assert m.called
            auth_header = m.last_request.headers.get("Authorization")
            assert auth_header is not None
            assert "Basic" in auth_header

    def test_fetcher_file_content_with_auth(self):
        """Test ZoektContentFetcher file content fetch with authentication."""
        fetcher = ZoektContentFetcher(
            zoekt_url="https://zoekt.example.com",
            zoekt_login="test_user",
            zoekt_password="test_pass",
        )

        html_content = '<pre class="inline-pre">def hello():\n    print("world")</pre>'

        with requests_mock.Mocker() as m:
            m.get("https://zoekt.example.com/print", text=html_content)
            result = fetcher._fetch_file_content("test/repo", "test.py")

            assert m.called
            auth_header = m.last_request.headers.get("Authorization")
            assert auth_header is not None
            assert "Basic" in auth_header

    def test_clean_repository_path(self):
        """Test repository path cleaning."""
        fetcher = ZoektContentFetcher(zoekt_url="https://zoekt.example.com")

        assert fetcher._clean_repository_path("https://github.com/test/repo") == "github.com/test/repo"
        assert fetcher._clean_repository_path("http://github.com/test/repo") == "github.com/test/repo"
        assert fetcher._clean_repository_path("github.com/test/repo") == "github.com/test/repo"
