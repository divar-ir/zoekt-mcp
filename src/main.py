#!/usr/bin/env python3
"""Main entry point for Zoekt MCP server."""

import logging
import sys

logger = logging.getLogger(__name__)


def print_help():
    print("Usage: python main.py <command> [options]")
    print("\nAvailable commands:")
    print("  search     - Start the search server (default)")


if __name__ == "__main__":
    # Default to search command if no argument provided
    if len(sys.argv) < 2:
        command = "search"
    else:
        command = sys.argv[1]

    match command:
        case "search":
            from .server import main as search_main
            search_main()
        case "help" | "--help" | "-h":
            print_help()
        case _:
            print(f"Unknown command: {command}")
            print_help()
            sys.exit(1)
