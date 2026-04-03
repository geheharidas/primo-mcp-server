"""Format Primo records into compact, LLM-friendly text output."""

from __future__ import annotations

from primo_mcp_server.models import PrimoRecord, SearchResponse


def _format_authors(creators: list[str], max_authors: int = 3) -> str:
    """Format an author list, truncating with 'et al.' if needed."""
    if not creators:
        return "Unknown author"
    if len(creators) <= max_authors:
        return "; ".join(creators)
    return "; ".join(creators[:max_authors]) + " et al."


def _format_identifiers(record: PrimoRecord) -> str:
    """Format the most useful identifier for a record."""
    parts = []
    if record.doi:
        parts.append(f"DOI: {record.doi}")
    if record.isbn:
        parts.append(f"ISBN: {record.isbn[0]}")
    if record.issn:
        parts.append(f"ISSN: {record.issn[0]}")
    return " | ".join(parts) if parts else ""


def _format_availability(record: PrimoRecord) -> str:
    """Format availability information."""
    parts = []
    if record.fulltext_available:
        parts.append("Full text available")
    if record.delivery_category:
        parts.append(record.delivery_category)
    return " | ".join(parts) if parts else "Check availability in OneSearch"


def format_search_results(response: SearchResponse, query: str, offset: int = 0) -> str:
    """Format search results as a compact numbered list.

    Each result is 3-5 lines: title, authors, metadata, identifiers, availability.
    """
    if not response.records:
        return (
            f'No results found for "{query}".\n\n'
            "Suggestions:\n"
            "- Broaden your search terms\n"
            "- Check spelling\n"
            "- Try a different search field (title, creator, subject)\n"
            "- Remove filters (resource type, date range)"
        )

    total = f"{response.info.total:,}"
    showing_start = offset + 1
    showing_end = offset + len(response.records)

    lines = [
        f'Found {total} results for "{query}" (showing {showing_start}-{showing_end})',
        "",
    ]

    for i, record in enumerate(response.records, start=showing_start):
        # Line 1: number, title, year, type
        type_badge = record.resource_type.replace("_", " ").title() if record.resource_type else "Unknown"
        year = record.creation_date[:4] if record.creation_date else "n.d."

        lines.append(f"[{i}] {record.title}")
        lines.append(f"    {_format_authors(record.creators)} | {year} | {type_badge}")

        # Line 3: journal/source + identifiers
        source_parts = []
        if record.journal_title:
            journal_info = record.journal_title
            if record.volume:
                journal_info += f", {record.volume}"
            if record.issue:
                journal_info += f"({record.issue})"
            if record.start_page:
                journal_info += f", pp. {record.start_page}"
                if record.end_page:
                    journal_info += f"-{record.end_page}"
            source_parts.append(journal_info)
        elif record.publisher:
            source_parts.append(record.publisher)

        ident = _format_identifiers(record)
        if ident:
            source_parts.append(ident)
        if source_parts:
            lines.append(f"    {' | '.join(source_parts)}")

        # Line 4: availability + peer review + record ID
        status_parts = []
        if record.peer_reviewed:
            status_parts.append("Peer-reviewed")
        status_parts.append(_format_availability(record))
        lines.append(f"    {' | '.join(status_parts)}")
        lines.append(f"    Record ID: {record.record_id}")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_record_detail(record: PrimoRecord) -> str:
    """Format a single record with full details."""
    lines = []

    lines.append(f"Title: {record.title}")
    lines.append(f"Author(s): {_format_authors(record.creators, max_authors=10)}")

    if record.contributors:
        lines.append(f"Contributor(s): {'; '.join(record.contributors)}")

    year = record.creation_date[:4] if record.creation_date else "n.d."
    lines.append(f"Year: {year}")
    lines.append(f"Type: {record.resource_type.replace('_', ' ').title() if record.resource_type else 'Unknown'}")

    if record.publisher:
        lines.append(f"Publisher: {record.publisher}")

    if record.journal_title:
        journal = record.journal_title
        if record.volume:
            journal += f", vol. {record.volume}"
        if record.issue:
            journal += f", no. {record.issue}"
        if record.start_page:
            journal += f", pp. {record.start_page}"
            if record.end_page:
                journal += f"-{record.end_page}"
        lines.append(f"Journal: {journal}")

    if record.language:
        lines.append(f"Language: {record.language}")

    # Identifiers
    if record.doi:
        lines.append(f"DOI: {record.doi}")
    if record.isbn:
        lines.append(f"ISBN: {', '.join(record.isbn)}")
    if record.issn:
        lines.append(f"ISSN: {', '.join(record.issn)}")

    if record.subjects:
        lines.append(f"Subjects: {'; '.join(record.subjects)}")
    if record.keywords:
        lines.append(f"Keywords: {'; '.join(record.keywords)}")

    lines.append(f"Peer-reviewed: {'Yes' if record.peer_reviewed else 'No'}")

    if record.description:
        # Truncate long descriptions
        desc = record.description
        if len(desc) > 500:
            desc = desc[:497] + "..."
        lines.append(f"\nDescription:\n{desc}")

    # Availability
    lines.append(f"\nAvailability: {_format_availability(record)}")
    if record.source_label:
        lines.append(f"Source: {record.source_label}")

    lines.append(f"Record ID: {record.record_id}")

    return "\n".join(lines)


def format_suggestions(suggestions: list[str], query: str) -> str:
    """Format autocomplete suggestions."""
    if not suggestions:
        return f'No suggestions found for "{query}".'

    lines = [f'Suggestions for "{query}":', ""]
    for s in suggestions:
        lines.append(f"  - {s}")
    return "\n".join(lines)
