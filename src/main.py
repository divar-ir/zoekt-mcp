#!/usr/bin/env python3
"""Main entry point for Zoekt MCP server."""

import logging
import sys

logger = logging.getLogger(__name__)


def print_help():
    print("Usage: python main.py <command> [options]")
    print("\nAvailable commands:")
    print("  search     - Start the search server (default)")
    print("\nEnvironment variables:")
    print("  MCP_TRANSPORT=stdio  - Start server with stdio transport")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "search"

    match command:
        case "search" | "--stdio":
            from .server import main as search_main
            search_main()
        case "help" | "--help" | "-h":
            print_help()
        case _:
            print(f"Unknown command: {command}")
            print_help()
            sys.exit(1)
