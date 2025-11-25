"""Custom exceptions for the Zoekt MCP server."""


class ServerShutdownError(Exception):
    """Raised when server is shutting down and cannot process requests."""
    pass


class SearchError(Exception):
    """Raised when search operation fails."""
    pass


class ContentFetchError(Exception):
    """Raised when content fetching fails."""
    pass
