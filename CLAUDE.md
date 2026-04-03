# Primo MCP Server

MCP server for searching university library catalogues via the Ex Libris Primo discovery API.

## Architecture

- **Framework:** FastMCP (mcp.server.fastmcp)
- **Transport:** stdio
- **HTTP client:** httpx (async, connection-pooled)
- **Config:** pydantic-settings with PRIMO_ env prefix

## Key Files

- `src/primo_mcp_server/server.py` -- MCP tool definitions and lifespan
- `src/primo_mcp_server/client.py` -- Primo API HTTP client
- `src/primo_mcp_server/models.py` -- Pydantic models for PNX response normalisation
- `src/primo_mcp_server/formatter.py` -- Compact text output for LLM context
- `src/primo_mcp_server/citations.py` -- Citation formatting (APA7, Harvard, Chicago, IEEE, Vancouver)
- `src/primo_mcp_server/exporters.py` -- BibTeX, RIS, CSV export

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Configuration

Defaults are UWA. Override via environment variables:
- PRIMO_BASE_URL -- Primo API base URL
- PRIMO_VID -- View ID for the institution
- PRIMO_INSTITUTION_NAME -- Display name

## Conventions

- Australian English (en-AU)
- UTF-8-sig for CSV exports
- No contractions in prose
- ASCII-only in generated content
