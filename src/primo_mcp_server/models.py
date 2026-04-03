"""Pydantic models for Primo PNX response data.

Primo's API returns inconsistent field shapes -- the same field may be
a string, a list of strings, or missing entirely. These models normalise
everything into predictable types.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator


def _to_list(v: str | list[str] | None) -> list[str]:
    """Normalise a field that may be str, list[str], or None into list[str]."""
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return list(v)


def _first_or_empty(v: str | list[str] | None) -> str:
    """Extract the first element, or return empty string."""
    items = _to_list(v)
    return items[0] if items else ""


class PrimoRecord(BaseModel):
    """A normalised Primo catalogue record."""

    # Identity
    record_id: str = ""
    source_id: str = ""
    source_system: str = ""

    # Display
    title: str = ""
    resource_type: str = ""
    language: str = ""
    creators: list[str] = []
    contributors: list[str] = []
    publisher: str = ""
    creation_date: str = ""
    source_label: str = ""
    description: str = ""
    snippet: str = ""
    subjects: list[str] = []
    keywords: list[str] = []
    is_part_of: str = ""

    # Identifiers
    identifiers: list[str] = []
    doi: str = ""
    isbn: list[str] = []
    issn: list[str] = []

    # Academic data
    journal_title: str = ""
    volume: str = ""
    issue: str = ""
    start_page: str = ""
    end_page: str = ""
    peer_reviewed: bool = False
    ris_type: str = ""
    authors_structured: list[str] = []

    # Availability
    fulltext_available: bool = False
    delivery_category: str = ""

    # Relevance
    score: float = 0.0
    context: str = ""

    @classmethod
    def from_api_doc(cls, doc: dict) -> PrimoRecord:
        """Parse a single document from the Primo /pnxs response."""
        pnx = doc.get("pnx", {})
        display = pnx.get("display", {})
        control = pnx.get("control", {})
        addata = pnx.get("addata", {})
        search = pnx.get("search", {})
        delivery = pnx.get("delivery", {})

        # Extract DOI from identifiers
        doi = ""
        identifiers = _to_list(display.get("identifier"))
        for ident in identifiers:
            if "DOI:" in ident.upper():
                doi = ident.split("DOI:")[-1].strip()
                break

        # Parse creators -- display.creator is often a single semicolon-separated string
        raw_creators = _to_list(display.get("creator"))
        creators = []
        for c in raw_creators:
            creators.extend(part.strip() for part in c.split(";") if part.strip())

        # Subjects -- may be semicolon-separated
        raw_subjects = _to_list(display.get("subject"))
        subjects = []
        for s in raw_subjects:
            subjects.extend(part.strip() for part in s.split(";") if part.strip())

        # Keywords
        raw_keywords = _to_list(display.get("keyword"))
        keywords = []
        for k in raw_keywords:
            keywords.extend(part.strip() for part in k.split(";") if part.strip())

        # Peer review
        lds50 = _to_list(display.get("lds50"))
        peer_reviewed = any("peer_review" in x.lower() for x in lds50)

        # Score
        score_raw = _to_list(control.get("score"))
        try:
            score = float(score_raw[0]) if score_raw else 0.0
        except (ValueError, IndexError):
            score = 0.0

        return cls(
            record_id=_first_or_empty(control.get("recordid")),
            source_id=_first_or_empty(control.get("sourceid")) or _first_or_empty(
                control.get("sourceid") if isinstance(control.get("sourceid"), str)
                else (control.get("sourceid", [None]) or [None])[0]
            ),
            source_system=_first_or_empty(control.get("sourcesystem")),
            title=_first_or_empty(display.get("title")),
            resource_type=_first_or_empty(display.get("type")),
            language=_first_or_empty(display.get("language")),
            creators=creators,
            contributors=_to_list(display.get("contributor")),
            publisher=_first_or_empty(display.get("publisher")),
            creation_date=_first_or_empty(display.get("creationdate"))
                or _first_or_empty(addata.get("date")),
            source_label=_first_or_empty(display.get("source")),
            description=_first_or_empty(display.get("description"))
                or _first_or_empty(addata.get("abstract")),
            snippet=_first_or_empty(display.get("snippet")),
            subjects=subjects,
            keywords=keywords,
            is_part_of=_first_or_empty(display.get("ispartof")),
            identifiers=identifiers,
            doi=doi,
            isbn=_to_list(addata.get("isbn")),
            issn=_to_list(addata.get("issn")),
            journal_title=_first_or_empty(addata.get("jtitle")),
            volume=_first_or_empty(addata.get("volume")),
            issue=_first_or_empty(addata.get("issue")),
            start_page=_first_or_empty(addata.get("spage")),
            end_page=_first_or_empty(addata.get("epage")),
            peer_reviewed=peer_reviewed,
            ris_type=_first_or_empty(addata.get("ristype")),
            authors_structured=_to_list(addata.get("au")),
            fulltext_available="fulltext" in str(delivery.get("fulltext", "")),
            delivery_category=_first_or_empty(delivery.get("delcategory")),
            score=score,
            context=doc.get("context", ""),
        )


class SearchInfo(BaseModel):
    """Pagination and total count info from a search response."""

    total: int = 0
    total_local: int = 0
    total_pc: int = 0
    first: int = 0
    last: int = 0


class SearchResponse(BaseModel):
    """Parsed Primo search response."""

    info: SearchInfo = SearchInfo()
    records: list[PrimoRecord] = []

    @classmethod
    def from_api_response(cls, data: dict) -> SearchResponse:
        """Parse the full /pnxs API response."""
        info_raw = data.get("info", {})
        info = SearchInfo(
            total=info_raw.get("total", 0),
            total_local=info_raw.get("totalResultsLocal", 0),
            total_pc=info_raw.get("totalResultsPC", 0),
            first=info_raw.get("first", 0),
            last=info_raw.get("last", 0),
        )
        records = [
            PrimoRecord.from_api_doc(doc)
            for doc in data.get("docs", [])
        ]
        return cls(info=info, records=records)
