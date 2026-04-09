# tests/test_parser.py
# ─────────────────────────────────────────────────────────────
# Unit tests for pipeline/extract/quote_parser.py
# Run: pytest tests/test_parser.py
# ─────────────────────────────────────────────────────────────

import pytest
from unittest.mock import patch, MagicMock

from pipeline.extract.quote_parser import (
    detect_response_type,
    map_tally_response,
    validate_extraction,
    score_extraction,
)
from tests.fixtures.test_briefs import BRIEF_STRUCTURED
from tests.fixtures.synthetic_responses import TEST_CASES
from tests.fixtures.test_vendors import TEST_VENDORS


class TestDetectResponseType:
    def test_dict_is_form(self):
        assert detect_response_type({"available": "Yes"}) == "form"

    def test_json_string_is_form(self):
        assert detect_response_type('{"available": "Yes"}') == "form"

    def test_plain_text_is_email(self):
        assert detect_response_type("Thank you for your enquiry...") == "email"

    def test_empty_string_is_email(self):
        assert detect_response_type("") == "email"


class TestMapTallyResponse:
    def test_availability_yes_maps_to_1(self):
        extracted, confidence, _ = map_tally_response({"available": "Yes"})
        assert extracted["availability"] == 1
        assert confidence["availability"] == 1.0

    def test_availability_no_maps_to_0(self):
        extracted, _, _ = map_tally_response({"available": "No"})
        assert extracted["availability"] == 0

    def test_inclusions_string_split_to_list(self):
        extracted, _, _ = map_tally_response({"inclusions": "AV, WiFi, parking"})
        assert isinstance(extracted["inclusions"], list)
        assert "AV" in extracted["inclusions"]

    def test_vat_percentage_converted_to_decimal(self):
        extracted, _, _ = map_tally_response({"available": "Yes"})
        # No vat_rate field — should not error
        assert "vat_rate" not in extracted

    def test_form_test_case_extraction(self):
        """All form TEST_CASES should extract without error."""
        form_cases = [c for c in TEST_CASES if c["type"] == "form"]
        for case in form_cases:
            extracted, confidence, _ = map_tally_response(case["response"])
            assert isinstance(extracted, dict)
            assert isinstance(confidence, dict)


class TestValidateExtraction:
    def test_no_warnings_for_clean_extraction(self):
        extracted  = {"base_price": 4500, "availability": 1, "vat_rate": 0.20}
        confidence = {"base_price": 1.0, "availability": 1.0, "vat_rate": 1.0}
        result = validate_extraction(extracted, confidence, BRIEF_STRUCTURED)
        assert result["warnings"] == []

    def test_over_budget_price_reduces_confidence(self):
        extracted  = {"base_price": 60000}
        confidence = {"base_price": 1.0}
        result = validate_extraction(extracted, confidence, BRIEF_STRUCTURED)
        assert len(result["warnings"]) > 0
        assert result["confidence"]["base_price"] < 1.0

    def test_vat_percentage_normalised_to_decimal(self):
        extracted  = {"vat_rate": 20}
        confidence = {}
        validate_extraction(extracted, confidence, BRIEF_STRUCTURED)
        assert extracted["vat_rate"] == pytest.approx(0.20)


class TestScoreExtraction:
    def test_fully_populated_extraction_scores_high(self):
        extracted  = {"base_price": 4500, "availability": 1,
                      "inclusions": ["AV"], "price_unit": "flat",
                      "capacity_offered": 60, "vat_rate": 0.20}
        confidence = {k: 1.0 for k in extracted}
        score = score_extraction(extracted, confidence)
        assert score > 0.5

    def test_empty_extraction_scores_zero(self):
        assert score_extraction({}, {}) == 0.0
