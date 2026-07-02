# Testing Requirements Specification — Legal AI Prompt Review Suite

| | |
|---|---|
| **Identifier** | TRS-LAI-001 |
| **Suite** | `legal-ai-prompt-review-qa` |
| **Test basis** | `data/prompt_catalog.json` — 7 legal prompts (LQ-001…LQ-007) built on real authority: Palsgraf v. Long Island R.R., Miranda v. Arizona (1966), Alice Corp v. CLS Bank (2014), GDPR Art. 17; LQ-004 references a fictitious case as a hallucination trap |
| **Date** | 2026-07-01 |

Verification method for all requirements: **Test** (pytest assertions over the evaluated
response catalog and its defect log). Traceability: see TCS-LAI-001 §2.

---

## REQ-LAI-01 — Legal Factual Accuracy

**Statement.** Responses to legal research prompts *shall* cover all required legal
concepts defined for the prompt, and the catalog as a whole *shall* achieve at least an
80 % factual-accuracy pass rate.

**Rationale.** A legal answer that omits a controlling concept (e.g., an element of
contract formation) is materially wrong even if everything it says is true.

**Acceptance criteria**
- Case-law responses mention every concept in the prompt's required-concepts list
  (e.g., Palsgraf → duty, foreseeability, proximate cause).
- The contract-formation response covers all five elements (offer, acceptance,
  consideration, capacity, legality).
- The GDPR Article 17 response addresses the limitations/exceptions to the right to
  erasure, not just the right itself.
- (# prompts passing factual accuracy) / (total prompts) ≥ 0.80.

**Priority:** High (threshold Critical) · **Risk if unmet:** incomplete legal analysis relied upon by users.
**Verified by:** TC-LAI-001, 001b, 001c, 001d.

## REQ-LAI-02 — Hallucination Detection & Containment

**Statement.** A query about a case that does not exist *shall not* produce a fabricated
ruling; any hallucinated response *shall* be logged as a defect with an ID, scored 0,
and classified **Critical** severity; the presence of citations *shall not* be treated
as evidence of accuracy.

**Rationale.** Fabricated case law has produced real-world sanctions against attorneys.
This is the highest-stakes failure mode of legal AI, hence five distinct controls.

**Acceptance criteria**
- The fictional-case query (LQ-003 path) returns uncertainty, not an invented ruling.
- The seeded fabricated ruling in LQ-004 is present in the defect log.
- Every hallucination defect record carries a non-empty defect ID.
- Every hallucinated response has `score == 0`.
- A fabricated case accompanied by well-formed citations still fails (citation ≠ validation).

**Priority:** Critical · **Risk if unmet:** fabricated authority cited in real proceedings.
**Verified by:** TC-LAI-002, 002b, 002c, 002d, 002e.

## REQ-LAI-03 — Citation Quality

**Statement.** Responses to prompts flagged citation-required *shall* include citations
in correct format; prompts not requiring citations *may* omit them.

**Rationale.** Legal answers are only verifiable through their citations; format
correctness (e.g., `Miranda v. Arizona, 384 U.S. 436 (1966)`) is what makes them
resolvable.

**Acceptance criteria**
- Every citation-required prompt's response has a non-empty citation list.
- Citation-optional prompts pass with an empty citation list.
- Citations in passing responses match the expected reporter-citation format.

**Priority:** High · **Risk if unmet:** unverifiable legal claims.
**Verified by:** TC-LAI-003, 003b, 003c.

## REQ-LAI-04 — Confidence Calibration

**Statement.** Reported confidence *shall* track epistemic reality: low for fictional or
unknown matters, high for settled law; a high-confidence hallucination *shall* itself be
recorded as a defect.

**Rationale.** Users triage answers by stated confidence. Overconfident fabrication is
strictly worse than either honest uncertainty or a flagged error.

**Acceptance criteria**
- No response in the hallucination defect set carries high confidence without that
  overconfidence being flagged as a defect.
- Responses to fictional/unknown queries report low confidence.
- Responses on settled doctrine (e.g., Miranda) report high confidence.

**Priority:** Critical (overconfidence) / Medium (calibration direction).
**Verified by:** TC-LAI-004, 004b, 004c.

## REQ-LAI-05 — Scoring Discipline & Defect Logging

**Statement.** The evaluation scoring *shall* be internally consistent: passing
responses score ≥ 80 with a passing-set average ≥ 90, and every failing response
*shall* appear in the defect log.

**Rationale.** The score is the suite's summary statistic; if failures can escape the
defect log, the pipeline's headline numbers cannot be trusted.

**Acceptance criteria**
- ∀ response marked passing: `score ≥ 80`.
- mean(score of passing responses) ≥ 90.
- |defect log| = |failing responses| with matching IDs.

**Priority:** High · **Risk if unmet:** evaluation dashboard overstates quality.
**Verified by:** TC-LAI-005, 005b, 005c.
