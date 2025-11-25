import asyncio
import logging
import pathlib
import signal
from typing import Any, List

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .backends import FormattedResult, ZoektClient, ZoektContentFetcher
from .config import ServerConfig
from .core import PromptManager
from .exceptions import ContentFetchError, SearchError, ServerShutdownError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class ZoektMCPServer:
    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.server = FastMCP(sse_path="/zoekt/sse", message_path="/zoekt/messages/")
        self._shutdown_requested = False

        self._setup_clients()
        self._load_prompts()

    def _setup_clients(self) -> None:
        self.search_client = ZoektClient(base_url=self.config.zoekt_api_url)
        self.content_fetcher = ZoektContentFetcher(zoekt_url=self.config.zoekt_api_url)
        logger.info("Using Zoekt backend")

    def _load_prompts(self) -> None:
        prompt_manager = PromptManager(file_path=pathlib.Path(__file__).parent / "prompts" / "prompts.yaml")

        self.codesearch_guide = prompt_manager._load_prompt("guides.codesearch_guide")
        self.search_tool_description = prompt_manager._load_prompt("tools.search")
        self.search_prompt_guide_description = prompt_manager._load_prompt("tools.search_prompt_guide")
        self.fetch_content_description = prompt_manager._load_prompt("tools.fetch_content")

        try:
            self.org_guide = prompt_manager._load_prompt("guides.org_guide")
        except Exception:
            self.org_guide = ""

    def signal_handler(self, sig: int, frame: Any = None) -> None:
        """Handle termination signals for graceful shutdown."""
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        self._shutdown_requested = True

    async def fetch_content(self, repo: str, path: str) -> str:
        if self._shutdown_requested:
            logger.info("Shutdown in progress, declining new requests")
            raise ServerShutdownError("Server is shutting down")

        try:
            result = await asyncio.to_thread(self.content_fetcher.get_content, repo, path)
            return result
        except ValueError as e:
            logger.warning(f"Error fetching content from {repo}: {str(e)}")
            raise ContentFetchError("Invalid arguments: path or repository does not exist") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching content: {e}")
            raise ContentFetchError("Error fetching content") from e

    async def search(self, query: str, limit: int = 30) -> List[FormattedResult]:
        if self._shutdown_requested:
            logger.info("Shutdown in progress, declining new requests")
            raise ServerShutdownError("Server is shutting down")

        num_results = min(max(1, limit), 100)
        logger.info(f"Search query: {query}, limit: {num_results}")

        try:
            results = await asyncio.to_thread(self.search_client.search, query, num_results)
            formatted_results = await asyncio.to_thread(self.search_client.format_results, results, num_results)
            return formatted_results
        except requests.exceptions.HTTPError as exc:
            logger.error(f"Search HTTP error: {exc}")
            raise SearchError(f"HTTP error during search: {exc}") from exc
        except Exception as exc:
            logger.error(f"Unexpected error during search: {exc}")
            raise SearchError(f"Unexpected error during search: {exc}") from exc

    async def search_prompt_guide(self, objective: str) -> str:
        if self._shutdown_requested:
            logger.info("Shutdown in progress, declining new prompt guide requests")
            raise ServerShutdownError("Server is shutting down")

        prompt_parts = []

        if self.org_guide:
            prompt_parts.append(self.org_guide)
            prompt_parts.append("\n\n")

        prompt_parts.append(self.codesearch_guide)
        prompt_parts.append(
            f"\nGiven this guide create a Zoekt query for {objective} and call the search tool accordingly."
        )

        return "".join(prompt_parts)

    async def _safe_fetch_content(self, repo: str, path: str) -> str:
        """Safe wrapper for fetch_content that handles exceptions."""
        try:
            return await self.fetch_content(repo, path)
        except ServerShutdownError:
            return ""
        except ContentFetchError as e:
            return str(e)
        except Exception as e:
            logger.error(f"Unexpected error in fetch_content: {e}")
            return "error fetching content"

    async def _safe_search(self, query: str, limit: int = 30) -> List[FormattedResult]:
        """Safe wrapper for search that handles exceptions."""
        try:
            return await self.search(query, limit)
        except ServerShutdownError:
            return []
        except SearchError as e:
            logger.error(f"Search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in search: {e}")
            return []

    async def _safe_search_prompt_guide(self, objective: str) -> str:
        """Safe wrapper for search_prompt_guide that handles exceptions."""
        try:
            return await self.search_prompt_guide(objective)
        except ServerShutdownError:
            return "Server is shutting down"
        except Exception as e:
            logger.error(f"Unexpected error in search_prompt_guide: {e}")
            return "Error generating search guide"

    def _register_tools(self) -> None:
        """Register MCP tools with the server."""
        tools = [
            (self._safe_search, "search", self.search_tool_description),
            (self._safe_search_prompt_guide, "search_prompt_guide", self.search_prompt_guide_description),
            (self._safe_fetch_content, "fetch_content", self.fetch_content_description),
        ]

        for tool_func, tool_name, description in tools:
            self.server.tool(tool_func, name=tool_name, description=description)
            logger.info(f"Registered tool: {tool_name}")

    def _register_health_endpoints(self) -> None:
        """Register health check endpoints."""

        @self.server.custom_route("/health", methods=["GET"])
        async def health_check(request: Request) -> Response:
            """Simple health check endpoint for liveness probe."""
            return JSONResponse({"status": "ok", "service": "zoekt-mcp"})

        @self.server.custom_route("/ready", methods=["GET"])
        async def readiness_check(request: Request) -> Response:
            """Readiness check endpoint that verifies the service is ready."""
            try:
                # Check if search client is available
                if not hasattr(self, "search_client") or self.search_client is None:
                    return JSONResponse({"status": "not_ready", "reason": "search_client_unavailable"}, status_code=503)

                # Check if content fetcher is available
                if not hasattr(self, "content_fetcher") or self.content_fetcher is None:
                    return JSONResponse(
                        {"status": "not_ready", "reason": "content_fetcher_unavailable"}, status_code=503
                    )

                return JSONResponse({"status": "ready", "service": "zoekt-mcp", "backend": "zoekt"})
            except Exception as e:
                logger.error(f"Readiness check failed: {e}")
                return JSONResponse({"status": "error", "reason": str(e)}, status_code=503)

    async def _run_server(self) -> None:
        """Run the FastMCP server with both HTTP and SSE transports."""

        tasks = [
            self.server.run_http_async(
                transport="streamable-http",
                host="0.0.0.0",
                path="/zoekt/mcp",
                port=self.config.streamable_http_port,
            ),
            self.server.run_http_async(transport="sse", host="0.0.0.0", port=self.config.sse_port),
        ]
        await asyncio.gather(*tasks)

    async def run(self) -> None:
        """Start the search server."""
        signal.signal(signal.SIGINT, lambda sig, frame: self.signal_handler(sig, frame))
        signal.signal(signal.SIGTERM, lambda sig, frame: self.signal_handler(sig, frame))

        self._register_tools()
        self._register_health_endpoints()

        try:
            logger.info("Starting Zoekt MCP server...")
            await self._run_server()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt (CTRL+C)")
        except Exception as exc:
            logger.error(f"Server error: {exc}")
            raise
        finally:
            logger.info("Server has shut down.")


def main() -> None:
    config = ServerConfig()
    server = ZoektMCPServer(config)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
