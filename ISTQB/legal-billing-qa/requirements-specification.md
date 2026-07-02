# Testing Requirements Specification — Legal Billing Validation Suite

| | |
|---|---|
| **Identifier** | TRS-LB-001 |
| **Suite** | `legal-billing-qa` |
| **Test basis** | `data/billing_data.json` — 7 timekeepers (2024 ABA-benchmark rates), 6 matters, 16 time entries incl. 4 seeded defects (TE-006, TE-007, TE-010, TE-016); UTBMS code set |
| **Date** | 2026-07-01 |

Verification method for all requirements: **Test** (pytest assertions over the billing
dataset; the `valid_entries` fixture is the defect-free partition). Traceability:
see TCS-LB-001 §2.

---

## REQ-LB-01 — Time Entry Hours Validation

**Statement.** Every billable time entry *shall* satisfy 0 < hours ≤ 24 for a single
day, recorded in increments of 0.1 hour; violations *shall* be flagged and excluded
from billing.

**Rationale.** Entries above 24 h/day are physically impossible and a classic
fee-padding red flag in fee audits; zero-hour entries pollute invoices; off-increment
values indicate manual entry errors.

**Acceptance criteria**
- No unflagged entry exceeds 24.0 hours (seeded TE-006 at 25.0 h **must** be flagged
  `EXCEEDS_DAILY_MAX`).
- All valid entries have hours > 0 (seeded TE-010 at 0.0 h flagged `ZERO_HOURS`).
- All valid entries are multiples of 0.1 h (seeded TE-016 at 0.05 h flagged
  `BELOW_MIN_INCREMENT`).

**Priority:** Critical · **Risk if unmet:** unbillable/fraud-flagged entries reach client invoices.
**Verified by:** TC-LB-001, 001b, 001c, 001d, 001e.

## REQ-LB-02 — Matter Status Enforcement

**Statement.** Time *shall not* be recorded against a matter whose status is Closed;
valid entries *shall* target Active matters only.

**Rationale.** Billing to closed matters is unbillable work at best and an ethics
violation at worst; it also corrupts matter-level profitability reporting.

**Acceptance criteria**
- No unflagged entry references a Closed matter (seeded TE-007 → MAT-004 (Closed)
  **must** be flagged `CLOSED_MATTER`).
- Every entry in the valid partition references a matter with status Active.

**Priority:** Critical · **Risk if unmet:** ethics exposure; write-offs.
**Verified by:** TC-LB-002, 002b, 002c.

## REQ-LB-03 — Billing Rate Calculation

**Statement.** The billed amount for each entry *shall* equal hours × the timekeeper's
contracted hourly rate, and every timekeeper rate *shall* be positive.

**Rate table (2024 ABA benchmarks, as configured)**

| Timekeeper | Role | Rate |
|---|---|---|
| TK-002 | Senior Associate | $425/hr |
| TK-004 | Paralegal | $185/hr |
| TK-006 | Counsel | $550/hr |
| TK-007 | Summer Associate | $225/hr |

**Acceptance criteria**
- Spot recomputations hold exactly: TE-002 = 1.0 h × $425 = $425.00;
  TE-004 = 4.0 h × $185 = $740.00; TE-001 per its timekeeper's rate.
- Every valid entry produces a billed amount > $0.
- Every configured rate > $0.

**Priority:** High · **Risk if unmet:** systematic over/under-billing.
**Verified by:** TC-LB-003, 003b, 003c, 003d, 003e.

## REQ-LB-04 — UTBMS Code Compliance

**Statement.** Every time entry *shall* carry a valid UTBMS task code (L-series) and
activity code (A-series); partner-level work *shall* use the task-code tier appropriate
to partner activities (L160+).

**Rationale.** Corporate clients enforce UTBMS coding in e-billing systems; invalid
codes cause automatic invoice rejection, and partners billing junior-tier task codes
triggers guideline audits.

**Acceptance criteria**
- All `utbms_task_code` values ∈ the valid L-code set (e.g., L110–L250).
- All `utbms_activity_code` values ∈ the valid A-code set (e.g., A101–A106).
- Entries by Partner-role timekeepers use task codes at or above the L160 tier.

**Priority:** High · **Risk if unmet:** e-billing rejections; payment delays.
**Verified by:** TC-LB-004, 004b, 004c.

## REQ-LB-05 — Invoice Total Reconciliation

**Statement.** Each matter's invoice total *shall* equal the sum of its **valid** line
items (hours × rate), computed only over entries that pass REQ-LB-01/02; the minimum
billable unit of 0.1 h (6 minutes) *shall* be enforced at invoicing.

**Rationale.** The invoice is the financial contract with the client; defective entries
must be excluded before summation or every upstream control is moot.

**Acceptance criteria**
- MAT-001 invoice total = Σ(valid entries on MAT-001), to the cent — noting TE-006 is excluded.
- MAT-002 invoice total = Σ(valid entries on MAT-002) — noting TE-010 is excluded.
- No line item below 0.1 h is billed (TE-016 excluded).

**Priority:** Critical · **Risk if unmet:** client disputes; revenue leakage or overcharge.
**Verified by:** TC-LB-005, 005b, 005c.
