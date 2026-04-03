"""Tests for result formatting."""

from primo_mcp_server.formatter import (
    format_record_detail,
    format_search_results,
    format_suggestions,
)
from primo_mcp_server.models import SearchResponse


class TestFormatSearchResults:
    def test_formats_results(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = format_search_results(response, "entrepreneurship innovation")
        assert "entrepreneurship innovation" in output
        assert "[1]" in output
        assert "[2]" in output
        assert "[3]" in output

    def test_empty_results_message(self, empty_results_data):
        response = SearchResponse.from_api_response(empty_results_data)
        output = format_search_results(response, "xyzzyplugh99999")
        assert "No results found" in output
        assert "Suggestions" in output

    def test_contains_record_ids(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = format_search_results(response, "test")
        assert "Record ID:" in output

    def test_contains_total_count(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = format_search_results(response, "test")
        assert "Found" in output
        assert "results" in output


class TestFormatRecordDetail:
    def test_formats_detail(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = format_record_detail(response.records[0])
        assert "Title:" in output
        assert "Author(s):" in output
        assert "Year:" in output
        assert "Type:" in output
        assert "Record ID:" in output

    def test_includes_doi(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        record = response.records[0]
        if record.doi:
            output = format_record_detail(record)
            assert "DOI:" in output


class TestFormatSuggestions:
    def test_formats_suggestions(self):
        output = format_suggestions(["machine learning", "machine vision"], "machine")
        assert "machine learning" in output
        assert "machine vision" in output

    def test_empty_suggestions(self):
        output = format_suggestions([], "xyzzy")
        assert "No suggestions" in output
