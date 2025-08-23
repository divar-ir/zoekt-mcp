[![MSeeP.ai Security Assessment Badge](https://mseep.net/pr/divar-ir-zoekt-mcp-badge.png)](https://mseep.ai/app/divar-ir-zoekt-mcp)

# Zoekt MCP Server

A Model Context Protocol (MCP) server that provides code search capabilities powered by [Zoekt](https://github.com/sourcegraph/zoekt), the indexed code search engine used by Sourcegraph.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Using UV (recommended)](#using-uv-recommended)
  - [Using pip](#using-pip)
  - [Using Docker](#using-docker)
- [Configuration](#configuration)
  - [Required Environment Variables](#required-environment-variables)
  - [Optional Environment Variables](#optional-environment-variables)
- [Usage with AI Tools](#usage-with-ai-tools)
  - [Cursor](#cursor)
- [MCP Tools](#mcp-tools)
  - [search](#search)
  - [search_prompt_guide](#search_prompt_guide)
  - [fetch_content](#fetch_content)
- [Development](#development)
  - [Linting and Formatting](#linting-and-formatting)

## Overview

This MCP server integrates with Zoekt, a text search engine optimized for code repositories. Zoekt provides trigram-based indexing for searches across large codebases, making it suitable for AI assistants that need to find and understand code patterns.

## Features

- **Code Search**: Search across codebases using Zoekt's trigram indexing
- **Advanced Query Language**: Support for regex patterns, file filters, language filters, and boolean operators
- **Repository Discovery**: Find repositories by name and explore their structure
- **Content Fetching**: Browse repository files and directories
- **AI Integration**: Designed for LLM integration with guided search prompts

## Prerequisites

- **Zoekt Instance**: You need access to a running Zoekt search server. See the [Zoekt documentation](https://github.com/sourcegraph/zoekt#installation) for setup instructions.
- **Python 3.10+**: Required for running the MCP server
- **UV** (optional): Modern Python package manager for easier dependency management

## Installation

### Using UV (recommended)

```bash
# Install dependencies
uv sync

# Run the server
uv run python src/main.py
```

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Run the server
python src/main.py
```

### Using Docker

```bash
# Build the image
docker build -t zoekt-mcp .

# Run the container with default ports
docker run -p 8000:8000 -p 8080:8080 \
  -e ZOEKT_API_URL=http://your-zoekt-instance \
  zoekt-mcp

# Or run with custom ports
docker run -p 9000:9000 -p 9080:9080 \
  -e ZOEKT_API_URL=http://your-zoekt-instance \
  -e MCP_SSE_PORT=9000 \
  -e MCP_STREAMABLE_HTTP_PORT=9080 \
  zoekt-mcp
```

## Configuration

### Required Environment Variables

- `ZOEKT_API_URL`: URL of your Zoekt search instance

### Optional Environment Variables

- `MCP_SSE_PORT`: SSE server port (default: 8000)
- `MCP_STREAMABLE_HTTP_PORT`: HTTP server port (default: 8080)

## Usage with AI Tools

### Cursor

After running the MCP server, add the following to your `.cursor/mcp.json` file:

```json
{
  "mcpServers": {
    "zoekt": {
      "url": "http://localhost:8080/zoekt/mcp/"
    }
   }
}
```

## MCP Tools

This server provides three powerful tools for AI assistants:

### 🔍 search
Search across indexed codebases using Zoekt's advanced query syntax with support for regex, language filters, and boolean operators.

### 📖 search_prompt_guide
Generate a context-aware guide for constructing effective search queries based on your specific objective.

### 📂 fetch_content
Retrieve file contents or explore directory structures from indexed repositories.


## Development

### Linting and Formatting

```bash
# Check code style
uv run ruff check src/

# Format code
uv run ruff format src/
```

