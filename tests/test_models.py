"""Tests for Primo PNX model parsing."""

from primo_mcp_server.models import PrimoRecord, SearchResponse


class TestSearchResponse:
    def test_parse_search_results(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        assert response.info.total > 0
        assert len(response.records) == 3

    def test_parse_empty_results(self, empty_results_data):
        response = SearchResponse.from_api_response(empty_results_data)
        assert response.info.total == 0
        assert len(response.records) == 0

    def test_record_has_title(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        for record in response.records:
            assert record.title != ""

    def test_record_has_creators(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        for record in response.records:
            assert len(record.creators) > 0

    def test_record_has_type(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        for record in response.records:
            assert record.resource_type == "article"

    def test_record_has_record_id(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        for record in response.records:
            assert record.record_id != ""

    def test_peer_reviewed_detected(self, search_results_data):
        response = SearchResponse.from_api_response(search_results_data)
        # At least one record should be peer-reviewed
        assert any(r.peer_reviewed for r in response.records)


class TestPrimoRecord:
    def test_from_minimal_doc(self):
        """Test parsing with minimal/missing fields."""
        doc = {
            "pnx": {
                "display": {"title": ["Test Title"]},
                "control": {"recordid": ["test123"]},
            }
        }
        record = PrimoRecord.from_api_doc(doc)
        assert record.title == "Test Title"
        assert record.record_id == "test123"
        assert record.creators == []
        assert record.doi == ""

    def test_doi_extraction(self):
        doc = {
            "pnx": {
                "display": {
                    "title": ["Test"],
                    "identifier": ["ISSN: 1234-5678", "DOI: 10.1234/test"],
                },
                "control": {"recordid": ["test"]},
            }
        }
        record = PrimoRecord.from_api_doc(doc)
        assert record.doi == "10.1234/test"
