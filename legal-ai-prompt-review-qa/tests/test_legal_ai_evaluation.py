"""
Legal AI Prompt Review — Test Suite
Project: legal-ai-prompt-review-qa
Tests evaluate AI responses on legal queries for factual accuracy, citation quality,
hallucination detection, scope compliance, and hedging language appropriateness.
Domain: DeepJudge-style legal AI evaluation.
"""

import json
import pytest
from pathlib import Path


CATALOG_PATH = Path(__file__).parent.parent / "data" / "prompt_catalog.json"

HALLUCINATION_SEVERITY = {
    "fabricated_case": "Critical",
    "wrong_jurisdiction": "High",
    "incorrect_statute": "High",
    "wrong_date": "Medium",
    "wrong_party_name": "Medium"
}


@pytest.fixture(scope="session")
def prompt_catalog():
    with open(CATALOG_PATH) as f:
        return json.load(f)

@pytest.fixture(scope="session")
def passing_responses(prompt_catalog):
    return [p for p in prompt_catalog if p["evaluation"]["factual_accuracy"] == "pass"]

@pytest.fixture(scope="session")
def failing_responses(prompt_catalog):
    return [p for p in prompt_catalog if p["evaluation"]["factual_accuracy"] == "fail"]

@pytest.fixture(scope="session")
def hallucination_defects(prompt_catalog):
    return [p for p in prompt_catalog if p["evaluation"].get("hallucination_detected")]


# ─────────────────────────────────────────────────────────────────────────────
# TC-LAI-001  Factual Accuracy Evaluation
# ─────────────────────────────────────────────────────────────────────────────
class TestFactualAccuracy:

    def test_case_law_response_covers_required_concepts(self, prompt_catalog):
        """TC-LAI-001 — REQ-LAI-01: Case law responses must cover all required legal concepts."""
        case_law = [p for p in prompt_catalog if p["category"] == "case_law"]
        for prompt in case_law:
            response_text = prompt["mock_response"]["text"].lower()
            evaluation    = prompt["evaluation"]
            covered       = evaluation.get("concepts_covered", [])
            expected      = prompt["expected_concepts"]
            missing       = [c for c in expected if c.lower() not in response_text and c not in covered]
            assert not missing, (
                f"Prompt {prompt['id']}: Missing required concepts: {missing}\n"
                f"Prompt: {prompt['prompt'][:80]}..."
            )

    def test_contract_law_covers_all_five_elements(self, prompt_catalog):
        """TC-LAI-001b — REQ-LAI-01: Contract formation response must cover all 5 elements."""
        contract = next((p for p in prompt_catalog if p["id"] == "LQ-002"), None)
        assert contract is not None, "LQ-002 not found in catalog."
        covered = contract["evaluation"]["concepts_covered"]
        required = ["offer", "acceptance", "consideration", "capacity", "legality"]
        missing  = [r for r in required if r not in covered]
        assert not missing, f"Contract law missing elements: {missing}"

    def test_gdpr_response_mentions_exceptions(self, prompt_catalog):
        """TC-LAI-001c — REQ-LAI-01: GDPR Article 17 response must address right limitations."""
        gdpr = next((p for p in prompt_catalog if p["id"] == "LQ-005"), None)
        assert gdpr is not None, "LQ-005 not found."
        response_text = gdpr["mock_response"]["text"].lower()
        assert "exception" in response_text or "limitation" in response_text or "however" in response_text, (
            "GDPR response does not address limitations to the right of erasure."
        )

    def test_overall_pass_rate_meets_threshold(self, passing_responses, prompt_catalog):
        """TC-LAI-001d — REQ-LAI-01: At least 80% of prompts must achieve factual accuracy pass."""
        total       = len(prompt_catalog)
        pass_count  = len(passing_responses)
        pass_rate   = pass_count / total if total else 0
        assert pass_rate >= 0.80, (
            f"Factual accuracy pass rate {pass_rate:.0%} below 80% threshold.\n"
            f"Pass: {pass_count}/{total}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-LAI-002  Hallucination Detection
# ─────────────────────────────────────────────────────────────────────────────
class TestHallucinationDetection:

    def test_fictional_case_query_does_not_fabricate_LQ003(self, prompt_catalog):
        """TC-LAI-002 — REQ-LAI-02: Query for fictional case must not return fabricated ruling."""
        lq003 = next((p for p in prompt_catalog if p["id"] == "LQ-003"), None)
        assert lq003 is not None, "LQ-003 not found."
        assert not lq003["evaluation"]["hallucination_detected"], (
            f"LQ-003 incorrectly flagged as hallucination.\n"
            f"Response: {lq003['mock_response']['text'][:200]}..."
        )
        response = lq003["mock_response"]["text"].lower()
        uncertainty_words = ["unable", "not find", "cannot verify", "no record", "does not appear"]
        has_uncertainty = any(w in response for w in uncertainty_words)
        assert has_uncertainty, (
            "LQ-003 response should express uncertainty about the fictional case."
        )

    def test_hallucination_in_LQ004_is_detected_as_critical(self, prompt_catalog):
        """TC-LAI-002b — REQ-LAI-02: Fabricated case (LQ-004) must be flagged as Critical severity."""
        lq004 = next((p for p in prompt_catalog if p["id"] == "LQ-004"), None)
        assert lq004 is not None, "LQ-004 not found."
        assert lq004["evaluation"]["hallucination_detected"], (
            "LQ-004 hallucination (fabricated case) not detected."
        )
        assert lq004["evaluation"].get("hallucination_type") == "fabricated_case", (
            f"Hallucination type should be 'fabricated_case'. "
            f"Got: {lq004['evaluation'].get('hallucination_type')}"
        )
        assert lq004["evaluation"].get("severity") == "Critical", (
            "Fabricated case hallucination must be rated Critical severity."
        )

    def test_hallucination_defects_have_defect_ids(self, hallucination_defects):
        """TC-LAI-002c — REQ-LAI-02: All hallucination findings must have a defect ID."""
        without_id = [p for p in hallucination_defects if not p["evaluation"].get("defect_id")]
        assert not without_id, (
            f"Hallucination defects without defect IDs: "
            f"{[p['id'] for p in without_id]}"
        )

    def test_hallucinated_response_scores_zero(self, hallucination_defects):
        """TC-LAI-002d — REQ-LAI-02: Responses with hallucinations must receive score of 0."""
        non_zero = [p for p in hallucination_defects if p["evaluation"].get("score", 0) > 0]
        assert not non_zero, (
            f"Hallucinated responses with non-zero scores: "
            f"{[(p['id'], p['evaluation']['score']) for p in non_zero]}"
        )

    def test_citation_present_does_not_validate_fabricated_case(self, prompt_catalog):
        """TC-LAI-002e — REQ-LAI-02: Presence of citations does not imply accuracy."""
        lq004 = next(p for p in prompt_catalog if p["id"] == "LQ-004")
        # LQ-004 has a citation AND is a hallucination — citations must be verified
        has_citation    = len(lq004["mock_response"]["citations"]) > 0
        is_hallucination = lq004["evaluation"]["hallucination_detected"]
        assert has_citation and is_hallucination, (
            "Test setup: LQ-004 should have a citation AND be a hallucination to validate "
            "that citations alone cannot confirm accuracy."
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-LAI-003  Citation Quality
# ─────────────────────────────────────────────────────────────────────────────
class TestCitationQuality:

    def test_case_law_responses_include_citations(self, prompt_catalog):
        """TC-LAI-003 — REQ-LAI-03: Case law queries requiring citations must include them."""
        citation_required = [p for p in prompt_catalog if p["citation_required"]]
        missing_citations = []
        for p in citation_required:
            if not p["evaluation"]["hallucination_detected"]:
                citations = p["mock_response"].get("citations", [])
                if not citations:
                    missing_citations.append(p["id"])
        assert not missing_citations, (
            f"Prompts requiring citations with none provided: {missing_citations}"
        )

    def test_non_citation_required_prompts_can_omit_citations(self, prompt_catalog):
        """TC-LAI-003b — REQ-LAI-03: Prompts not requiring citations may have empty citation list."""
        no_citation_required = [p for p in prompt_catalog if not p["citation_required"]]
        # This is a validation — it should always pass
        assert len(no_citation_required) >= 1, "Expected at least one non-citation prompt."

    def test_passing_responses_have_correct_citation_format(self, passing_responses):
        """TC-LAI-003c — REQ-LAI-03: Passing responses with citations must have correct format."""
        for p in passing_responses:
            assert p["evaluation"]["citation_format_correct"], (
                f"Prompt {p['id']}: Citation format marked incorrect in a passing response."
            )


# ─────────────────────────────────────────────────────────────────────────────
# TC-LAI-004  Confidence Calibration
# ─────────────────────────────────────────────────────────────────────────────
class TestConfidenceCalibration:

    def test_hallucinated_response_should_not_show_high_confidence(self, hallucination_defects):
        """TC-LAI-004 — REQ-LAI-04: Hallucinated responses that show high confidence are defects."""
        high_confidence_hallucinations = [
            p for p in hallucination_defects
            if p["mock_response"].get("confidence") == "high"
        ]
        # LQ-004 demonstrates this failure pattern — document it
        assert len(high_confidence_hallucinations) >= 1, (
            "Expected at least one high-confidence hallucination (LQ-004) in test data."
        )
        for p in high_confidence_hallucinations:
            assert p["evaluation"]["score"] == 0, (
                f"High-confidence hallucination {p['id']} must score 0."
            )

    def test_uncertain_fictional_query_shows_low_confidence(self, prompt_catalog):
        """TC-LAI-004b — REQ-LAI-04: Responses to fictional/unknown queries should show low confidence."""
        lq003 = next(p for p in prompt_catalog if p["id"] == "LQ-003")
        confidence = lq003["mock_response"].get("confidence")
        assert confidence == "low", (
            f"LQ-003 (fictional case) should return low confidence. Got: '{confidence}'"
        )

    def test_factual_well_known_queries_show_high_confidence(self, prompt_catalog):
        """TC-LAI-004c — REQ-LAI-04: Well-established legal concepts should return high confidence."""
        well_known = [p for p in prompt_catalog if p["id"] in ("LQ-001", "LQ-002", "LQ-005")]
        for p in well_known:
            if not p["evaluation"]["hallucination_detected"]:
                confidence = p["mock_response"].get("confidence")
                assert confidence == "high", (
                    f"Prompt {p['id']} (well-known legal concept) returned '{confidence}' confidence."
                )


# ─────────────────────────────────────────────────────────────────────────────
# TC-LAI-005  Evaluation Score Distribution
# ─────────────────────────────────────────────────────────────────────────────
class TestEvaluationScoreDistribution:

    def test_passing_responses_score_above_80(self, passing_responses):
        """TC-LAI-005 — REQ-LAI-05: All passing responses must score >= 80."""
        low_scores = [
            p for p in passing_responses
            if p["evaluation"].get("score", 0) < 80
        ]
        assert not low_scores, (
            f"Passing responses with score < 80:\n"
            + "\n".join(f"  {p['id']}: {p['evaluation']['score']}" for p in low_scores)
        )

    def test_average_score_of_non_hallucinated_responses(self, passing_responses):
        """TC-LAI-005b — REQ-LAI-05: Average score of passing responses must be >= 90."""
        scores = [p["evaluation"].get("score", 0) for p in passing_responses]
        avg    = sum(scores) / len(scores) if scores else 0
        assert avg >= 90, (
            f"Average passing response score {avg:.1f} is below 90 threshold."
        )

    def test_total_defects_logged(self, hallucination_defects, failing_responses):
        """TC-LAI-005c — REQ-LAI-05: All failing responses must be in defect log."""
        for failing in failing_responses:
            assert failing["evaluation"].get("defect_id"), (
                f"Failing response {failing['id']} has no defect ID assigned."
            )
