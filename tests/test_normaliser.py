# tests/test_normaliser.py
# ─────────────────────────────────────────────────────────────
# Unit tests for pipeline/normalise/normaliser.py
# Run: pytest tests/test_normaliser.py
# ─────────────────────────────────────────────────────────────

import pytest
from unittest.mock import patch, MagicMock

from pipeline.normalise.normaliser import (
    detect_components,
    normalise_price,
    score_completeness,
)
from tests.fixtures.test_briefs import BRIEF_STRUCTURED


HEADCOUNT = BRIEF_STRUCTURED["headcount"]  # 45


class TestDetectComponents:
    def test_venue_category_auto_includes_venue(self):
        components = detect_components([], [], "venue")
        assert components["venue"] == "included"

    def test_catering_category_auto_includes_catering(self):
        components = detect_components([], [], "catering")
        assert components["catering"] == "included"

    def test_inclusion_keyword_detected(self):
        components = detect_components(["AV equipment", "WiFi"], [], "venue")
        assert components["av_equipment"] == "included"

    def test_exclusion_keyword_detected(self):
        components = detect_components([], ["catering not included"], "venue")
        assert components["catering"] == "excluded"

    def test_unknown_components_default_to_unknown(self):
        components = detect_components([], [], "venue")
        assert components["transport"] == "unknown"


class TestNormalisePrice:
    def test_flat_price_normalised_correctly(self):
        quote  = {"base_price": 4500, "vat_rate": 0.20, "service_fee": 0}
        result = normalise_price(quote, HEADCOUNT)
        assert result["total_flat"]     == pytest.approx(4500)
        assert result["total_inc_vat"]  == pytest.approx(5400)
        assert result["total_per_head"] == pytest.approx(4500 / HEADCOUNT, rel=0.01)

    def test_per_head_price_scaled_by_headcount(self):
        quote  = {"price_per_head": 85, "vat_rate": 0.20, "service_fee": 0}
        result = normalise_price(quote, HEADCOUNT)
        assert result["total_flat"]    == pytest.approx(85 * HEADCOUNT)
        assert result["total_inc_vat"] == pytest.approx(85 * HEADCOUNT * 1.20)

    def test_service_charge_percentage_applied(self):
        quote  = {"price_per_head": 85, "service_fee": 12.5, "vat_rate": 0.20}
        result = normalise_price(quote, HEADCOUNT)
        expected_flat = 85 * HEADCOUNT * 1.125
        assert result["total_flat"] == pytest.approx(expected_flat, rel=0.01)

    def test_missing_price_returns_none_totals(self):
        result = normalise_price({}, HEADCOUNT)
        assert result["total_flat"]    is None
        assert result["total_inc_vat"] is None

    def test_default_vat_applied_when_missing(self):
        quote  = {"base_price": 1000}
        result = normalise_price(quote, HEADCOUNT)
        assert result["total_inc_vat"] == pytest.approx(1200)


class TestScoreCompleteness:
    def test_venue_only_scores_low(self):
        components = {c: "unknown" for c in
                      ["venue", "catering", "av_equipment",
                       "staffing", "activities", "transport", "accommodation"]}
        components["venue"] = "included"
        score = score_completeness(components)
        assert score == pytest.approx(0.30)

    def test_all_included_scores_1(self):
        components = {c: "included" for c in
                      ["venue", "catering", "av_equipment",
                       "staffing", "activities", "transport", "accommodation"]}
        score = score_completeness(components)
        assert score == pytest.approx(1.0)

    def test_excluded_components_not_counted(self):
        components = {c: "excluded" for c in
                      ["venue", "catering", "av_equipment",
                       "staffing", "activities", "transport", "accommodation"]}
        score = score_completeness(components)
        assert score == pytest.approx(0.0)
