import html
import json
import re
from typing import Dict, List, Optional, Set

import requests
from src.backends.content_fetcher_protocol import MAX_FILE_SIZE, ContentFetcherProtocol


class ZoektContentFetcher(ContentFetcherProtocol):
    def __init__(self, zoekt_url: str):
        self.zoekt_url = zoekt_url.rstrip("/")

    def _clean_repository_path(self, repository: str) -> str:
        repository = repository.replace("https://", "").replace("http://", "")
        return repository

    def get_content(self, repository: str, path: str = "", depth: int = 2, ref: str = "HEAD") -> str:
        """Get content from repository using Zoekt.

        Args:
            repository: Repository path (e.g., "github.com/example/project")
            path: File or directory path (e.g., "src/main.py")
            depth: Tree depth for directory listings
            ref: Git reference (not used in Zoekt implementation)

        Returns:
            File content if path is a file, directory tree if path is a directory

        Raises:
            ValueError: If repository or path does not exist
        """

        repository = self._clean_repository_path(repository)

        # Handle empty path as root directory
        if not path:
            path = "."

        if path != "." and not path.endswith("/"):
            file_content = self._fetch_file_content(repository, path)
            if file_content is not None:
                return file_content

        # If not a file or failed to fetch, show directory tree
        return self._get_directory_tree(repository, path, depth)

    def _fetch_file_content(self, repo: str, file_path: str) -> Optional[str]:
        """Fetch individual file content from Zoekt.

        Args:
            repo: Repository name
            file_path: Path to the file

        Returns:
            str: File content or None if error/not found
        """
        params = {"r": repo, "f": file_path}
        url = f"{self.zoekt_url}/print"

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            html_content = response.text

            lines = []
            pre_pattern = r'<pre[^>]*class="inline-pre"[^>]*>(.*?)</pre>'

            for match in re.finditer(pre_pattern, html_content, re.DOTALL):
                line_content = match.group(1)
                line_content = re.sub(r'<span[^>]*class="noselect"[^>]*>.*?</span>', "", line_content)
                line_content = re.sub(r"<[^>]+>", "", line_content)
                line_content = html.unescape(line_content)
                lines.append(line_content)

            if lines:
                content = "\n".join(lines)

                if len(content) > MAX_FILE_SIZE:
                    truncated_content = content[:MAX_FILE_SIZE]
                    last_newline = truncated_content.rfind("\n")
                    if last_newline > 0:
                        truncated_content = truncated_content[:last_newline]

                    line_count = content.count("\n") + 1
                    return (
                        f"{truncated_content}\n\n"
                        f"[FILE TRUNCATED: File too large ({len(content):,} chars, {line_count} lines). "
                        f"Showing first {len(truncated_content):,} chars]"
                    )

                return content
            return None
        except requests.exceptions.RequestException:
            return None

    def _fetch_zoekt_data(self, repo: str, path: str) -> Optional[Dict]:
        """Fetch data from Zoekt API.

        Args:
            repo: Repository name
            path: Directory path

        Returns:
            dict: JSON response data or None if error
        """
        # Handle root directory case
        if path == ".":
            query = f"r:{repo} f:\\.*"
        else:
            query = f"r:{repo} file:^{path}/"

        params = {"q": query, "format": "json", "num": "1000"}

        try:
            response = requests.get(f"{self.zoekt_url}/search", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None
        except json.JSONDecodeError:
            return None

    def _extract_files_from_response(self, data: Dict, path: str) -> List[str]:
        """Extract file paths from Zoekt API response.

        Args:
            data: Zoekt API response
            path: Base path

        Returns:
            list: Sorted list of file paths
        """
        all_files = []

        if data and "result" in data and "FileMatches" in data["result"]:
            file_matches = data["result"]["FileMatches"]

            if file_matches:  # Check if file_matches is not None
                for file_match in file_matches:
                    filename = file_match.get("FileName", "")
                    # For root directory, include all files
                    if path == ".":
                        all_files.append(filename)
                    elif filename.startswith(f"{path}/"):
                        all_files.append(filename)

        return sorted(all_files)

    def _build_directory_structure(self, all_files: List[str], path: str, max_depth: int) -> Dict[int, Set[str]]:
        """Build directory structure from file list.

        Args:
            all_files: List of file paths
            path: Base path
            max_depth: Maximum depth to include

        Returns:
            dict: Directory structure organized by depth
        """
        base_len = len(f"{path}/") if path != "." else 0
        dirs_at_depth = {}

        for f in all_files:
            rel_path = f[base_len:] if base_len > 0 else f
            parts = rel_path.split("/")

            # Process each directory level
            for depth in range(min(len(parts) - 1, max_depth)):
                dir_path = "/".join(parts[: depth + 1])

                if depth not in dirs_at_depth:
                    dirs_at_depth[depth] = set()

                dirs_at_depth[depth].add(dir_path)

            # Add files only if they're within max_depth
            if len(parts) - 1 < max_depth:
                file_depth = len(parts) - 1
                if file_depth not in dirs_at_depth:
                    dirs_at_depth[file_depth] = set()
                dirs_at_depth[file_depth].add(rel_path)

        return dirs_at_depth

    def _format_tree_structure(self, dirs_at_depth: Dict[int, Set[str]], max_depth: int) -> str:
        """Format the directory tree structure.

        Args:
            dirs_at_depth: Directory structure by depth
            max_depth: Maximum depth

        Returns:
            str: Formatted tree structure
        """
        output_lines = []
        printed_paths = set()

        def format_item(item_path: str, depth: int, is_file: bool) -> str:
            indent = "  " * depth
            name = item_path.split("/")[-1]
            if not is_file and depth < max_depth:
                name += "/"
            return f"{indent}{name}"

        all_paths = []
        for depth in range(max_depth + 1):
            if depth in dirs_at_depth:
                for item in sorted(dirs_at_depth[depth]):
                    parts = item.split("/")
                    is_file = len(parts) - 1 < max_depth and "." in parts[-1]
                    all_paths.append((item, len(parts) - 1, is_file))

        all_paths.sort(key=lambda x: x[0])
        for item_path, depth, is_file in all_paths:
            if item_path not in printed_paths:
                printed_paths.add(item_path)
                parts = item_path.split("/")
                if depth > 0:
                    parent_path = "/".join(parts[:-1])
                    if parent_path not in printed_paths and parent_path:
                        parent_parts = parent_path.split("/")
                        for i in range(1, len(parent_parts) + 1):
                            sub_parent = "/".join(parent_parts[:i])
                            if sub_parent not in printed_paths:
                                printed_paths.add(sub_parent)
                                output_lines.append(format_item(sub_parent, i - 1, False))

                output_lines.append(format_item(item_path, depth, is_file))

        return "\n".join(output_lines)

    def _get_directory_tree(self, repo: str, path: str, depth: int) -> str:
        """Get formatted directory tree listing using Zoekt.

        Args:
            repo: Repository name
            path: Directory path
            depth: Maximum depth

        Returns:
            str: Formatted directory tree

        Raises:
            ValueError: If the given path or repository does not exist
        """
        path = path.rstrip("/")

        data = self._fetch_zoekt_data(repo, path)
        if not data:
            raise ValueError("invalid arguments the given path or repository does not exist")

        all_files = self._extract_files_from_response(data, path)

        if not all_files and path != ".":
            raise ValueError("invalid arguments the given path or repository does not exist")

        dirs_at_depth = self._build_directory_structure(all_files, path, depth)
        return self._format_tree_structure(dirs_at_depth, depth)
