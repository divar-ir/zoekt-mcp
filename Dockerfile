FROM python:3.10-slim

WORKDIR /app

RUN pip install uv

COPY README.md pyproject.toml ./

COPY src/ ./src/

RUN uv sync

ENV MCP_SSE_PORT=8000
ENV MCP_STREAMABLE_HTTP_PORT=8080

EXPOSE ${MCP_SSE_PORT} ${MCP_STREAMABLE_HTTP_PORT}

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "src/main.py"]
