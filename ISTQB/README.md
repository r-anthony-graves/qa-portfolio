# ISTQB-Aligned QA Documentation

Formal test documentation for the seven automated test suites in this portfolio, structured
according to **ISTQB** terminology and the document templates of **ISO/IEC/IEEE 29119-3**
(successor to IEEE 829).

## Document Set (per suite)

| Document | Purpose | ISTQB / 29119-3 basis |
|---|---|---|
| `requirements-specification.md` | Detailed testing requirements: shall-statements, rationale, measurable acceptance criteria, priority, risk | Test basis / requirements specification |
| `test-plan.md` | Scope, objectives, approach, entry/exit criteria, environment, risks | Test Plan (29119-3 §8) |
| `test-case-specification.md` | Test conditions, test cases, and the Requirements Traceability Matrix (RTM) | Test Case Specification + Traceability (29119-3 §10) |
| `test-summary-report.md` | Execution results, defects found, evaluation against exit criteria | Test Completion / Summary Report (29119-3 §14) |

## Suites Covered

| Suite | Test Level / Type | Tests | Doc Folder |
|---|---|---|---|
| AI Prompt Validation | System testing — functional + non-functional (AI quality characteristics) | 18 | [ai-prompt-validation-qa/](ai-prompt-validation-qa/) |
| ETL Data Validation | Integration testing — data migration validation | 22 | [etl-data-validation-qa/](etl-data-validation-qa/) |
| Legal AI Prompt Review | System testing — domain-specific AI evaluation | 18 | [legal-ai-prompt-review-qa/](legal-ai-prompt-review-qa/) |
| Legal Billing Validation | System testing — business rule validation | 19 | [legal-billing-qa/](legal-billing-qa/) |
| Workday Financial Validation | Integration testing — financial reconciliation | 16 | [workday-financial-validation-qa/](workday-financial-validation-qa/) |
| REST API Contract Testing | Integration testing — API contract, negative, auth, idempotency (offline + live tiers) | 37 | [rest-api-contract-qa/](rest-api-contract-qa/) |
| OrangeHRM UI Automation | System / acceptance testing — E2E UI (live site) | 16 | [orangehrm-qa-project/](orangehrm-qa-project/) |

## Conventions

- **Requirement IDs** — `REQ-<SUITE>-nn` (e.g. `REQ-ETL-03`). These mirror the IDs embedded in
  the pytest docstrings of each suite, so the code itself is the source of truth.
- **Test case IDs** — `TC-<SUITE>-nnn[x]` (e.g. `TC-LB-002b`). Sub-letters denote test cases
  derived from the same test condition.
- **Test basis** — the data files under each suite's `data/` directory (for the API suite,
  the `schemas/` contract files and the API implementation) plus the stated business
  rules (IRS 2024 rates, UTBMS codes, GDPR Art. 17, RFC 9110 method semantics, etc.).
- **Test design techniques** — primarily specification-based: equivalence partitioning,
  boundary value analysis, decision table testing, and use case testing (UI suite).
  Several suites also use **defect-based** testing via deliberately seeded defects
  (error seeding / fault injection) to prove the checks can fail.

## Execution

All suites run via pytest from the dashboard (`python app.py` → http://127.0.0.1:5000) or
directly, e.g.:

```bash
cd etl-data-validation-qa && python -m pytest -v
```

The OrangeHRM suite additionally requires Playwright and network access to the public demo
instance at https://opensource-demo.orangehrmlive.com.
