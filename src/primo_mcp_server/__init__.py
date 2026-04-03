"""Primo MCP Server -- search university library catalogues via MCP."""

__version__ = "0.1.0"


def main() -> None:
    """Entry point for the primo-mcp-server command."""
    from primo_mcp_server.server import mcp

    mcp.run(transport="stdio")
