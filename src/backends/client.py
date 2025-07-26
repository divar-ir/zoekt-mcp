from typing import List

import requests
from src.backends.models import FormattedResult, Match
from src.backends.search_protocol import SearchClientProtocol


class ZoektClient(SearchClientProtocol):
    def __init__(
        self,
        base_url: str,
        max_line_length: int = 300,
        max_output_length: int = 100000,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_line_length = max_line_length
        self.max_output_length = max_output_length

    def search(self, query: str, num: int) -> dict:
        params = {
            "q": query,
            "num": num,
            "format": "json",
            "ctx": 5,
        }

        url = f"{self.base_url}/search"
        response = requests.get(url, params=params)

        if response.status_code != 200:
            raise requests.exceptions.HTTPError(
                f"Search failed with status code: {response.status_code}. Response: {response.text}"
            )
        return response.json()

    def _truncate_line(self, line: str) -> str:
        if len(line) > self.max_line_length:
            return line[: self.max_line_length - 3] + "..."
        return line

    def format_results(self, results: dict, num: int) -> List[FormattedResult]:
        formatted = []

        # Handle repository results (when using r: queries)
        if "repos" in results and "Repos" in results["repos"]:
            for repo in results["repos"]["Repos"][:num]:
                repo_name = repo.get("Name", "")
                repo_url = repo.get("URL", f"https://{repo_name}")

                formatted.append(
                    FormattedResult(
                        filename="",
                        repository=repo_name,
                        matches=[
                            Match(
                                line_number=0,
                                text=f"Repository: {repo_name}",
                            )
                        ],
                        url=repo_url,
                    )
                )
            return formatted

        # Handle file match results
        if not results or "result" not in results or "FileMatches" not in results["result"]:
            return formatted

        if results["result"]["FileMatches"] is None:
            return formatted

        # Track total matches processed across all files
        total_matches_processed = 0

        for file_match in results["result"]["FileMatches"]:
            if total_matches_processed >= num:
                break

            matches = []

            # Calculate how many matches we can process from this file
            remaining_matches = num - total_matches_processed
            matches_to_process = min(remaining_matches, len(file_match["Matches"]))

            for match in file_match["Matches"][:matches_to_process]:
                # Combine fragments to get the full line
                full_line = ""
                for fragment in match["Fragments"]:
                    full_line += fragment["Pre"] + fragment["Match"] + fragment["Post"]

                # Create match with the full context
                full_text = []
                if match.get("Before"):
                    full_text.extend(match["Before"].strip().splitlines())
                full_text.append(full_line.strip())
                if match.get("After"):
                    full_text.extend(match["After"].strip().splitlines())

                # Truncate each line in the text for readability
                truncated_text = [self._truncate_line(line) for line in full_text]

                matches.append(
                    Match(
                        line_number=match["LineNum"],
                        text="\n".join(truncated_text),
                    )
                )

            if matches:  # Only add file to results if it has matches
                formatted.append(
                    FormattedResult(
                        filename=file_match["FileName"],
                        repository=file_match["Repo"],
                        matches=matches,
                        url=(
                            file_match["Matches"][0]["URL"].split("#L")[0]
                            if file_match["Matches"] and "URL" in file_match["Matches"][0]
                            else None
                        ),
                    )
                )
                total_matches_processed += len(matches)

        return formatted
