# tests/test_router.py
# ─────────────────────────────────────────────────────────────
# Unit tests for pipeline/match/llm_router.py
# Run: pytest tests/test_router.py
# ─────────────────────────────────────────────────────────────

import pytest
from unittest.mock import patch, MagicMock

from pipeline.match.llm_router import parse_brief, _validate_brief, prefilter
from tests.fixtures.test_briefs import BRIEF_STRUCTURED, BRIEF_TEXT_LONDON


class TestValidateBrief:
    def test_defaults_applied_to_empty_dict(self):
        brief = _validate_brief({})
        assert brief["city"]       == "London"
        assert brief["event_type"] == "offsite"
        assert "venue" in brief["categories"]

    def test_existing_values_preserved(self):
        brief = _validate_brief({"city": "Manchester", "headcount": 30})
        assert brief["city"]      == "Manchester"
        assert brief["headcount"] == 30

    def test_structured_brief_passes_through(self):
        brief = parse_brief(BRIEF_STRUCTURED)
        assert brief["city"]         == BRIEF_STRUCTURED["city"]
        assert brief["headcount"]    == BRIEF_STRUCTURED["headcount"]
        assert brief["budget_total"] == BRIEF_STRUCTURED["budget_total"]


class TestParseBrief:
    @patch("pipeline.match.llm_router.client")
    def test_free_text_calls_llm(self, mock_client):
        """parse_brief should call the LLM for free-text input."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"city":"London","headcount":45,'
                                            '"budget_total":15000,"budget_currency":"GBP",'
                                            '"event_type":"offsite","date_start":null,'
                                            '"date_end":null,"categories":["venue","catering"],'
                                            '"requirements":"outdoor space","brief_text":"test"}')]
        mock_client.messages.create.return_value = mock_response

        brief = parse_brief("test brief")
        assert mock_client.messages.create.called
        assert brief["city"] == "London"

    @patch("pipeline.match.llm_router.client")
    def test_llm_json_error_raises_value_error(self, mock_client):
        """Invalid JSON from LLM should raise ValueError."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not json")]
        mock_client.messages.create.return_value = mock_response

        with pytest.raises(ValueError):
            parse_brief("some brief text")


class TestPrefilter:
    def test_returns_list(self):
        """prefilter always returns a list, even on empty DB."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = []
        result = prefilter(mock_conn, BRIEF_STRUCTURED, "venue")
        assert isinstance(result, list)
