"""Tests for export formats."""

from primo_mcp_server.exporters import export_bibtex, export_csv, export_ris
from primo_mcp_server.models import PrimoRecord, SearchResponse


class TestBibTeX:
    def test_article_export(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = export_bibtex(response.records)
        assert "@article{" in output
        assert "author = {" in output
        assert "title = {" in output
        assert "doi = {" in output

    def test_unique_keys(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = export_bibtex(response.records)
        # Extract all citation keys
        import re
        keys = re.findall(r"@\w+\{(\w+),", output)
        assert len(keys) == len(set(keys)), "BibTeX keys should be unique"


class TestRIS:
    def test_article_export(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = export_ris(response.records)
        assert "TY  - JOUR" in output
        assert "AU  - " in output
        assert "TI  - " in output
        assert "ER  - " in output

    def test_has_doi(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = export_ris(response.records[:1])
        if response.records[0].doi:
            assert "DO  - " in output


class TestCSV:
    def test_csv_has_header(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = export_csv(response.records)
        assert "Record ID" in output
        assert "Title" in output
        assert "Authors" in output

    def test_csv_has_bom(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = export_csv(response.records)
        assert output.startswith("\ufeff")

    def test_csv_row_count(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        output = export_csv(response.records)
        lines = output.strip().split("\n")
        # Header + data rows
        assert len(lines) == 1 + len(response.records)
