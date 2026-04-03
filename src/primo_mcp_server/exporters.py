"""Export Primo records to BibTeX, RIS, and CSV formats."""

from __future__ import annotations

import io
import csv
import re

from primo_mcp_server.models import PrimoRecord


def _bibtex_key(record: PrimoRecord) -> str:
    """Generate a BibTeX citation key from author and year."""
    first_author = ""
    authors = record.authors_structured or record.creators
    if authors:
        # Take last name of first author
        parts = authors[0].split(",", 1)
        first_author = parts[0].strip().lower()
        # Remove non-alphanumeric
        first_author = re.sub(r"[^a-z0-9]", "", first_author)

    year = record.creation_date[:4] if record.creation_date else "nodate"

    # Add first word of title for uniqueness
    title_word = ""
    if record.title:
        words = re.findall(r"[a-zA-Z]+", record.title)
        if words:
            title_word = words[0].lower()

    return f"{first_author}{year}{title_word}" or "unknown"


def _bibtex_escape(value: str) -> str:
    """Escape special BibTeX characters."""
    return value.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")


def export_bibtex(records: list[PrimoRecord]) -> str:
    """Export records as BibTeX entries."""
    entries = []
    used_keys: set[str] = set()

    for record in records:
        # Determine entry type
        rtype = record.resource_type.lower()
        if rtype in ("article", "review"):
            entry_type = "article"
        elif rtype in ("conference_proceeding",):
            entry_type = "inproceedings"
        elif rtype in ("dissertation", "thesis"):
            entry_type = "phdthesis"
        else:
            entry_type = "book"

        # Generate unique key
        key = _bibtex_key(record)
        if key in used_keys:
            i = 2
            while f"{key}{chr(96+i)}" in used_keys:
                i += 1
            key = f"{key}{chr(96+i)}"
        used_keys.add(key)

        # Build fields
        fields = []
        authors = record.authors_structured or record.creators
        if authors:
            fields.append(f"  author = {{{_bibtex_escape(' and '.join(authors))}}}")
        fields.append(f"  title = {{{_bibtex_escape(record.title)}}}")

        year = record.creation_date[:4] if record.creation_date else ""
        if year:
            fields.append(f"  year = {{{year}}}")

        if record.journal_title and entry_type == "article":
            fields.append(f"  journal = {{{_bibtex_escape(record.journal_title)}}}")
        if record.volume:
            fields.append(f"  volume = {{{record.volume}}}")
        if record.issue:
            fields.append(f"  number = {{{record.issue}}}")
        if record.start_page:
            pages = record.start_page
            if record.end_page:
                pages += f"--{record.end_page}"
            fields.append(f"  pages = {{{pages}}}")
        if record.publisher:
            fields.append(f"  publisher = {{{_bibtex_escape(record.publisher)}}}")
        if record.doi:
            fields.append(f"  doi = {{{record.doi}}}")
        if record.isbn:
            fields.append(f"  isbn = {{{record.isbn[0]}}}")
        if record.issn:
            fields.append(f"  issn = {{{record.issn[0]}}}")

        entry = f"@{entry_type}{{{key},\n" + ",\n".join(fields) + "\n}"
        entries.append(entry)

    return "\n\n".join(entries)


def export_ris(records: list[PrimoRecord]) -> str:
    """Export records as RIS (Research Information Systems) format."""
    entries = []

    for record in records:
        lines = []

        # Type
        rtype = record.resource_type.lower()
        ris_type_map = {
            "article": "JOUR",
            "review": "JOUR",
            "book": "BOOK",
            "journal": "JFULL",
            "conference_proceeding": "CONF",
            "dissertation": "THES",
            "newspaper_article": "NEWS",
        }
        lines.append(f"TY  - {ris_type_map.get(rtype, 'GEN')}")

        # Authors
        authors = record.authors_structured or record.creators
        for author in authors:
            lines.append(f"AU  - {author}")

        lines.append(f"TI  - {record.title}")

        if record.journal_title:
            lines.append(f"JO  - {record.journal_title}")
            lines.append(f"T2  - {record.journal_title}")

        year = record.creation_date[:4] if record.creation_date else ""
        if year:
            lines.append(f"PY  - {year}")
            lines.append(f"DA  - {record.creation_date}")

        if record.volume:
            lines.append(f"VL  - {record.volume}")
        if record.issue:
            lines.append(f"IS  - {record.issue}")
        if record.start_page:
            lines.append(f"SP  - {record.start_page}")
        if record.end_page:
            lines.append(f"EP  - {record.end_page}")

        if record.publisher:
            lines.append(f"PB  - {record.publisher}")

        if record.doi:
            lines.append(f"DO  - {record.doi}")
        if record.isbn:
            lines.append(f"SN  - {record.isbn[0]}")
        elif record.issn:
            lines.append(f"SN  - {record.issn[0]}")

        if record.description:
            lines.append(f"AB  - {record.description}")

        for subject in record.subjects:
            lines.append(f"KW  - {subject}")

        if record.language:
            lines.append(f"LA  - {record.language}")

        lines.append("ER  - ")
        entries.append("\n".join(lines))

    return "\n\n".join(entries)


def export_csv(records: list[PrimoRecord]) -> str:
    """Export records as CSV with UTF-8-sig encoding (BOM for Excel)."""
    output = io.StringIO()
    # Write BOM for Excel compatibility
    output.write("\ufeff")

    writer = csv.writer(output)
    writer.writerow([
        "Record ID",
        "Title",
        "Authors",
        "Year",
        "Type",
        "Journal",
        "Volume",
        "Issue",
        "Pages",
        "DOI",
        "ISBN",
        "ISSN",
        "Publisher",
        "Subjects",
        "Peer-Reviewed",
        "Language",
    ])

    for record in records:
        authors = record.authors_structured or record.creators
        year = record.creation_date[:4] if record.creation_date else ""
        pages = record.start_page
        if pages and record.end_page:
            pages += f"-{record.end_page}"

        writer.writerow([
            record.record_id,
            record.title,
            "; ".join(authors),
            year,
            record.resource_type,
            record.journal_title,
            record.volume,
            record.issue,
            pages or "",
            record.doi,
            "; ".join(record.isbn),
            "; ".join(record.issn),
            record.publisher,
            "; ".join(record.subjects),
            "Yes" if record.peer_reviewed else "No",
            record.language,
        ])

    return output.getvalue()
