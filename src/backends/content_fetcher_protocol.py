from typing import Protocol, runtime_checkable

MAX_FILE_SIZE = 100_000


@runtime_checkable
class ContentFetcherProtocol(Protocol):
    """Protocol defining the interface for content fetchers.

    This is similar to Go interfaces - any class that implements
    these methods will satisfy the protocol.
    """

    def get_content(self, repository: str, path: str = "", depth: int = 2, ref: str = "HEAD") -> str:
        """Get content from repository.

        Args:
            repository: Repository path (e.g., "github.com/example/project")
            path: File or directory path (e.g., "src/main.py")
            depth: Tree depth for directory listings
            ref: Git reference (branch, tag, or commit SHA)

        Returns:
            File content if path is a file, directory tree if path is a directory

        Raises:
            ValueError: If repository or path does not exist
        """
        ...
