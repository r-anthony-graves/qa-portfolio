# Test Plan — Legal AI Prompt Review Suite

| | |
|---|---|
| **Identifier** | TP-LAI-001 |
| **Suite** | `legal-ai-prompt-review-qa` |
| **Author** | R. Anthony Graves |
| **Date** | 2026-07-01 |
| **Status** | Approved |

## 1. Introduction & Objectives

Evaluate LLM answers to legal research prompts for factual accuracy, hallucination,
citation quality, and confidence calibration. The prompt catalog uses **real case law**
(Palsgraf v. Long Island R.R., Miranda v. Arizona (1966), Alice Corp v. CLS Bank (2014),
GDPR Article 17) plus one **fictitious case** used as a hallucination trap. Legal AI has a
low tolerance for fabrication, so hallucination checks are rated Critical.

## 2. Test Items

- `data/prompt_catalog.json` — 7 legal prompts (LQ-001 … LQ-007) with expected concepts,
  citation requirements, recorded responses, scores, and a defect log.
- `tests/test_legal_ai_evaluation.py` — 18 automated test cases.

## 3. Features to be Tested

| Req ID | Requirement |
|---|---|
| REQ-LAI-01 | Responses must cover all required legal concepts; ≥ 80 % of prompts pass factual accuracy |
| REQ-LAI-02 | Queries about non-existent cases must not yield fabricated rulings; hallucinations are logged as Critical defects with IDs and score 0 |
| REQ-LAI-03 | Case-law answers requiring citations must include correctly formatted citations |
| REQ-LAI-04 | Confidence must be calibrated: low for unknown/fictional queries, high for settled law; high-confidence hallucination is itself a defect |
| REQ-LAI-05 | Scoring discipline: passing responses score ≥ 80 (avg ≥ 90); every failing response appears in the defect log |

## 4. Features Not to be Tested

- Live model calls (recorded responses form the oracle).
- Jurisdictional completeness beyond the cataloged cases; legal advice quality as such.

## 5. Approach

- **Test level:** system testing of a domain-specific LLM evaluation pipeline.
- **Design techniques:** specification-based concept-coverage checks; **defect-based
  testing** via the seeded fictitious case (LQ-004 fabricated ruling) that must be caught,
  scored 0, logged with a defect ID, and flagged Critical; decision rules on
  citation-required vs. citation-optional prompts.
- **Automation:** pytest with fixtures for `prompt_catalog`, `passing_responses`,
  `failing_responses`, `hallucination_defects`.

## 6. Item Pass/Fail Criteria

Suite passes at 18/18, which necessarily includes correct detection and Critical-severity
classification of the seeded hallucination.

## 7. Entry / Exit Criteria

- **Entry:** catalog JSON parseable; defect log section present.
- **Exit:** all test cases executed; report generated; hallucination-trap outcome reviewed.

## 8. Test Environment

Windows 11 Pro, Python 3.14 (64-bit), pytest. Fully offline.

## 9. Risks & Contingencies

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Concept-keyword oracles under-count paraphrased legal reasoning | Medium | Medium | Concept lists curated per prompt; thresholded pass rate (80 %) |
| Citation format check accepts plausible-but-wrong citations | Medium | High | Paired with hallucination check TC-LAI-002e (citation presence ≠ accuracy) |
| Recorded responses age as case law evolves | Low | Low | Catalog pinned to landmark, settled cases |
