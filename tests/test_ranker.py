# tests/test_ranker.py
# ─────────────────────────────────────────────────────────────
# Unit tests for pipeline/normalise/ranker.py
# Run: pytest tests/test_ranker.py
# ─────────────────────────────────────────────────────────────

import pytest
from unittest.mock import patch, MagicMock

from pipeline.normalise.ranker import (
    passes_availability_gate,
    score_budget_fit,
    score_completeness,
    compute_score,
)
from tests.fixtures.test_briefs import BRIEF_STRUCTURED


class TestAvailabilityGate:
    def test_explicitly_unavailable_fails(self):
        assert passes_availability_gate({"availability": 0}) is False

    def test_available_passes(self):
        assert passes_availability_gate({"availability": 1}) is True

    def test_unknown_availability_passes(self):
        assert passes_availability_gate({}) is True
        assert passes_availability_gate({"availability": None}) is True


class TestScoreBudgetFit:
    BUDGET = BRIEF_STRUCTURED["budget_total"]  # 15000

    def test_exact_venue_allocation_scores_highest(self):
        # Venue gets 50% = £7500
        score = score_budget_fit(7500, self.BUDGET, "venue")
        assert score >= 0.95

    def test_over_budget_by_more_than_20pct_scores_low(self):
        # 50% of £15k = £7500 budget. £10k = 133% of allocation
        score = score_budget_fit(10000, self.BUDGET, "venue")
        assert score < 0.4

    def test_missing_price_returns_neutral(self):
        assert score_budget_fit(None, self.BUDGET, "venue") == 0.5

    def test_missing_budget_returns_neutral(self):
        assert score_budget_fit(5000, None, "venue") == 0.5

    def test_unknown_category_uses_default_allocation(self):
        score = score_budget_fit(4500, self.BUDGET, "unknown_cat")
        assert 0.0 <= score <= 1.0


class TestScoreCompleteness:
    def test_missing_catering_on_venue_reduces_score(self):
        score_with    = score_completeness(0.55, [],             "venue")
        score_without = score_completeness(0.55, ["catering"],   "venue")
        assert score_with > score_without

    def test_capped_at_1(self):
        score = score_completeness(0.95, [], "venue")
        assert score <= 1.0

    def test_none_completeness_returns_neutral(self):
        assert score_completeness(None, [], "venue") == 0.5


class TestComputeScore:
    def _make_quote(self, total_inc_vat, completeness, confidence, category="venue"):
        return {
            "category":          category,
            "availability":      1,
            "confidence_score":  confidence,
            "missing_components": [],
            "normalised": {
                "total_inc_vat":      total_inc_vat,
                "total_per_head":     total_inc_vat / 45,
                "completeness_score": completeness,
            }
        }

    def test_scores_between_0_and_1(self):
        quote  = self._make_quote(7500, 0.70, 0.80)
        scores = compute_score(quote, BRIEF_STRUCTURED, [quote])
        assert 0.0 <= scores["total"] <= 1.0

    def test_better_budget_fit_scores_higher(self):
        good = self._make_quote(7500,  0.70, 0.80)  # on target for venue
        bad  = self._make_quote(15000, 0.70, 0.80)  # 2x over venue allocation
        peers = [good, bad]
        assert compute_score(good, BRIEF_STRUCTURED, peers)["total"] > \
               compute_score(bad,  BRIEF_STRUCTURED, peers)["total"]

    def test_all_score_dimensions_present(self):
        quote  = self._make_quote(7500, 0.70, 0.80)
        scores = compute_score(quote, BRIEF_STRUCTURED, [quote])
        assert all(k in scores for k in
                   ["total", "budget_fit", "completeness", "confidence", "value"])
