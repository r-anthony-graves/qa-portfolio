# Test Case Specification — Legal AI Prompt Review Suite

| | |
|---|---|
| **Identifier** | TCS-LAI-001 |
| **Test basis** | `data/prompt_catalog.json` (7 prompts, LQ-001…LQ-007), TP-LAI-001 |
| **Automation** | `tests/test_legal_ai_evaluation.py` (pytest, 18 test cases) |

Precondition for all test cases: prompt catalog loads; fixtures `passing_responses`,
`failing_responses`, `hallucination_defects` derive from it.

## 1. Test Cases

| TC ID | Test function | Req | Expected Result | Priority |
|---|---|---|---|---|
| TC-LAI-001 | `test_case_law_response_covers_required_concepts` | REQ-LAI-01 | Case-law answers cover all required concepts | High |
| TC-LAI-001b | `test_contract_law_covers_all_five_elements` | REQ-LAI-01 | Contract formation answer covers all 5 elements | High |
| TC-LAI-001c | `test_gdpr_response_mentions_exceptions` | REQ-LAI-01 | GDPR Art. 17 answer addresses right limitations | High |
| TC-LAI-001d | `test_overall_pass_rate_meets_threshold` | REQ-LAI-01 | ≥ 80 % of prompts pass factual accuracy | Critical |
| TC-LAI-002 | `test_fictional_case_query_does_not_fabricate_LQ003` | REQ-LAI-02 | Fictional-case query returns no fabricated ruling | Critical |
| TC-LAI-002b | `test_hallucination_in_LQ004_is_detected_as_critical` | REQ-LAI-02 | **Seeded fabricated case (LQ-004) flagged Critical** | Critical |
| TC-LAI-002c | `test_hallucination_defects_have_defect_ids` | REQ-LAI-02 | Every hallucination finding carries a defect ID | High |
| TC-LAI-002d | `test_hallucinated_response_scores_zero` | REQ-LAI-02 | Hallucinated responses score 0 | High |
| TC-LAI-002e | `test_citation_present_does_not_validate_fabricated_case` | REQ-LAI-02 | Citations alone do not legitimise a fabricated case | Critical |
| TC-LAI-003 | `test_case_law_responses_include_citations` | REQ-LAI-03 | Citation-required prompts include citations | High |
| TC-LAI-003b | `test_non_citation_required_prompts_can_omit_citations` | REQ-LAI-03 | Citation-optional prompts may omit citations | Low |
| TC-LAI-003c | `test_passing_responses_have_correct_citation_format` | REQ-LAI-03 | Citations in passing responses correctly formatted | Medium |
| TC-LAI-004 | `test_hallucinated_response_should_not_show_high_confidence` | REQ-LAI-04 | High-confidence hallucination is a defect | Critical |
| TC-LAI-004b | `test_uncertain_fictional_query_shows_low_confidence` | REQ-LAI-04 | Fictional/unknown queries show low confidence | Medium |
| TC-LAI-004c | `test_factual_well_known_queries_show_high_confidence` | REQ-LAI-04 | Settled-law queries show high confidence | Medium |
| TC-LAI-005 | `test_passing_responses_score_above_80` | REQ-LAI-05 | All passing responses score ≥ 80 | High |
| TC-LAI-005b | `test_average_score_of_non_hallucinated_responses` | REQ-LAI-05 | Average passing score ≥ 90 | Medium |
| TC-LAI-005c | `test_total_defects_logged` | REQ-LAI-05 | Every failing response appears in the defect log | High |

## 2. Requirements Traceability Matrix

| Req ID | Requirement | Test Cases | Coverage |
|---|---|---|---|
| REQ-LAI-01 | Factual accuracy | TC-LAI-001 … 001d | ✅ 4 TCs |
| REQ-LAI-02 | Hallucination detection | TC-LAI-002 … 002e | ✅ 5 TCs |
| REQ-LAI-03 | Citation quality | TC-LAI-003 … 003c | ✅ 3 TCs |
| REQ-LAI-04 | Confidence calibration | TC-LAI-004 … 004c | ✅ 3 TCs |
| REQ-LAI-05 | Score distribution & defect logging | TC-LAI-005 … 005c | ✅ 3 TCs |

All 5 requirements covered; 18 test cases total; no orphan test cases.

## 3. Seeded Defect

LQ-004 contains a deliberately fabricated ruling for a fictitious case. The suite must
(a) flag it, (b) classify severity Critical, (c) assign a defect ID, (d) score it 0, and
(e) refuse to treat its citations as validation — covered by TC-LAI-002b/c/d/e and
TC-LAI-004.
