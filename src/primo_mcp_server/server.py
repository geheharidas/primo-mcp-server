"""FastMCP server exposing Primo library search tools."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from mcp.server.fastmcp import Context, FastMCP

from primo_mcp_server.client import PrimoAPIError, PrimoClient
from primo_mcp_server.config import PrimoConfig
from primo_mcp_server.formatter import (
    format_record_detail,
    format_search_results,
    format_suggestions,
)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Create a shared httpx client for the server lifetime."""
    config = PrimoConfig()
    async with httpx.AsyncClient(
        base_url=config.base_url,
        timeout=config.request_timeout,
        headers={"User-Agent": config.user_agent},
    ) as http_client:
        client = PrimoClient(http_client, config)
        yield {"client": client, "config": config}


mcp = FastMCP(
    "primo",
    instructions=(
        "Search university library catalogues and subscribed databases "
        "(ProQuest, Elsevier, Crossref, Gale, Springer, IEEE, etc.) "
        "via the Ex Libris Primo discovery API. "
        "Use primo_search for queries, primo_get_record for full details, "
        "primo_suggest for autocomplete, primo_cite for citations, "
        "and primo_export for BibTeX/RIS/CSV export."
    ),
    lifespan=app_lifespan,
)


def _get_client(ctx: Context) -> PrimoClient:
    """Extract the PrimoClient from the lifespan context."""
    return ctx.request_context.lifespan_context["client"]


# ---------------------------------------------------------------------------
# Tool 1: primo_search
# ---------------------------------------------------------------------------

@mcp.tool()
async def primo_search(
    ctx: Context,
    query: str,
    field: str = "any",
    scope: str = "everything",
    sort_by: str = "rank",
    limit: int = 10,
    offset: int = 0,
    resource_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    peer_reviewed: bool | None = None,
) -> str:
    """Search the university library catalogue and subscribed databases.

    Args:
        query: Search terms (e.g. "machine learning entrepreneurship").
        field: Search field -- "any" (default), "title", "creator", "sub" (subject), "isbn", "oclcnum".
        scope: "everything" for local catalogue + subscribed databases, "catalogue" for local only.
        sort_by: "rank" (relevance, default), "date" (newest first), "title" (alphabetical).
        limit: Number of results to return (1-50, default 10).
        offset: Pagination offset (default 0). Use to get the next page of results.
        resource_type: Filter by type -- "books", "articles", "journals", "dissertations", "conference_proceedings".
        date_from: Start year filter (YYYY format, e.g. "2020").
        date_to: End year filter (YYYY format, e.g. "2025").
        peer_reviewed: Set to true to show only peer-reviewed items.

    Returns:
        Formatted search results with title, authors, year, identifiers, and availability.
    """
    try:
        client = _get_client(ctx)
        response = await client.search(
            query=query,
            field=field,
            scope=scope,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
            resource_type=resource_type,
            date_from=date_from,
            date_to=date_to,
            peer_reviewed=peer_reviewed,
        )
        return format_search_results(response, query, offset)
    except PrimoAPIError as e:
        return f"Error searching Primo: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Tool 2: primo_get_record
# ---------------------------------------------------------------------------

@mcp.tool()
async def primo_get_record(ctx: Context, record_id: str) -> str:
    """Get full details for a single library record.

    Use the record ID from primo_search results to fetch complete metadata
    including abstract, all authors, subjects, identifiers, and availability.

    Args:
        record_id: The Primo record ID (from search results, e.g. "alma991234567890" or "cdi_crossref_primary_10_1234").

    Returns:
        Full record details including title, authors, abstract, identifiers, and availability.
    """
    try:
        client = _get_client(ctx)
        record = await client.get_record(record_id)
        if record is None:
            return (
                f'Record "{record_id}" not found. '
                "It may have been removed, or the ID may be incorrect. "
                "Try searching again with primo_search."
            )
        return format_record_detail(record)
    except PrimoAPIError as e:
        return f"Error fetching record: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Tool 3: primo_suggest
# ---------------------------------------------------------------------------

@mcp.tool()
async def primo_suggest(ctx: Context, query: str) -> str:
    """Get autocomplete suggestions for a search term.

    Useful for refining searches, checking subject headings, or exploring
    related terms before running a full search.

    Args:
        query: Partial search term (e.g. "entrepre" or "machine lear").

    Returns:
        List of suggested search terms.
    """
    try:
        client = _get_client(ctx)
        suggestions = await client.suggest(query)
        return format_suggestions(suggestions, query)
    except PrimoAPIError as e:
        return f"Error getting suggestions: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Tool 4: primo_cite
# ---------------------------------------------------------------------------

@mcp.tool()
async def primo_cite(
    ctx: Context,
    record_ids: list[str],
    style: str = "apa7",
) -> str:
    """Generate formatted citations for library records.

    Args:
        record_ids: List of Primo record IDs to cite.
        style: Citation style -- "apa7" (default), "harvard", "chicago", "ieee", "vancouver".

    Returns:
        Formatted citations. Note: always verify generated citations before submission.
    """
    try:
        from primo_mcp_server.citations import format_citation

        valid_styles = {"apa7", "harvard", "chicago", "ieee", "vancouver"}
        if style not in valid_styles:
            return f'Invalid citation style "{style}". Use one of: {", ".join(sorted(valid_styles))}'

        client = _get_client(ctx)
        records = await client.get_records(record_ids)

        if not records:
            return "No records found for the provided IDs."

        citations = []
        for record in records:
            citations.append(format_citation(record, style))

        result = "\n\n".join(citations)
        result += "\n\n-- Note: verify citations before submission. Automated formatting may not cover all edge cases."
        return result
    except PrimoAPIError as e:
        return f"Error fetching records for citation: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Tool 5: primo_export
# ---------------------------------------------------------------------------

@mcp.tool()
async def primo_export(
    ctx: Context,
    record_ids: list[str],
    format: str = "bibtex",
) -> str:
    """Export library records to reference manager formats.

    Args:
        record_ids: List of Primo record IDs to export.
        format: Export format -- "bibtex" (default), "ris", "csv".

    Returns:
        Formatted export data ready for import into reference managers (Zotero, Mendeley, EndNote).
    """
    try:
        from primo_mcp_server.exporters import export_bibtex, export_csv, export_ris

        valid_formats = {"bibtex", "ris", "csv"}
        if format not in valid_formats:
            return f'Invalid format "{format}". Use one of: {", ".join(sorted(valid_formats))}'

        client = _get_client(ctx)
        records = await client.get_records(record_ids)

        if not records:
            return "No records found for the provided IDs."

        if format == "bibtex":
            return export_bibtex(records)
        elif format == "ris":
            return export_ris(records)
        else:
            return export_csv(records)
    except PrimoAPIError as e:
        return f"Error fetching records for export: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"
