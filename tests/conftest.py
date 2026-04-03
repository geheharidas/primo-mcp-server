"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def search_results_data() -> dict:
    """Load the search results fixture."""
    with open(FIXTURES_DIR / "search_results.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def empty_results_data() -> dict:
    """Load the empty results fixture."""
    with open(FIXTURES_DIR / "empty_results.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def suggest_results_data() -> dict:
    """Load the suggest results fixture."""
    with open(FIXTURES_DIR / "suggest_results.json", encoding="utf-8") as f:
        return json.load(f)
