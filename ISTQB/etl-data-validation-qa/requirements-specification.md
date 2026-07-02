# Testing Requirements Specification — ETL Data Validation Suite

| | |
|---|---|
| **Identifier** | TRS-ETL-001 |
| **Suite** | `etl-data-validation-qa` |
| **Test basis** | Salesforce-style source extracts and warehouse target loads under `data/` (Northwind-derived, 20 accounts + 20 contacts) |
| **Date** | 2026-07-01 |

Verification method for all requirements: **Test** (pytest + pandas assertions over
source and target CSVs). Traceability: see TCS-ETL-001 §2.

---

## REQ-ETL-01 — Record Count Reconciliation (Completeness)

**Statement.** The target warehouse *shall* contain exactly one record for every source
record: row counts equal and every source primary key present in the target.

**Rationale.** Silent record loss is the highest-impact ETL failure; count + ID-set
checks catch both dropped and phantom rows.

**Acceptance criteria**
- `warehouse_accounts` row count = `salesforce_accounts` row count (20 = 20).
- `warehouse_contacts` row count = `salesforce_contacts` row count (20 = 20).
- Set of source `account_id` ⊆ set of target `account_id` (and likewise `contact_id`).
- A seeded drop (generator `DROPPED={"DRACD","EASTC"}`) must cause failure.

**Priority:** Critical · **Risk if unmet:** revenue-bearing records silently lost.
**Verified by:** TC-ETL-001, 001b, 001c, 001d.

## REQ-ETL-02 — Field Mapping Correctness (Transformation)

**Statement.** Renamed and transformed columns *shall* preserve source values exactly
per the mapping specification.

**Mapping specification**

| Source | Target | Transformation |
|---|---|---|
| `account_name` | `client_name` | rename, value-identical |
| `annual_revenue` | `annual_revenue_usd` | rename, numerically exact |
| `first_name`, `last_name` | `full_name` | concatenation `first + " " + last` |
| `phone` | `phone_number` | rename, value-identical |

**Acceptance criteria**
- For every joined key, target value equals the mapped/derived source value; revenue
  matches exactly (no rounding drift).

**Priority:** High · **Risk if unmet:** correct rows with wrong content — worse than missing rows because harder to notice.
**Verified by:** TC-ETL-002, 002b, 002c, 002d.

## REQ-ETL-03 — Mandatory Field / Null Validation (Data Quality)

**Statement.** Mandatory target columns *shall* contain no nulls, and numeric business
fields *shall* satisfy domain constraints.

**Acceptance criteria**
- Zero nulls in: `warehouse_accounts.account_id`, `warehouse_accounts.client_name`,
  `warehouse_contacts.email_address`, `warehouse_contacts.account_id` (FK).
- `annual_revenue_usd` ≥ 0 for every account.

**Priority:** Critical (keys/FKs) / Medium (revenue bound).
**Verified by:** TC-ETL-003, 003b, 003c, 003d, 003e.

## REQ-ETL-04 — Duplicate Detection (Uniqueness)

**Statement.** Primary keys *shall* be unique in the target, and contact email addresses
*shall not* be duplicated.

**Rationale.** Duplicates inflate aggregates and break downstream joins; email uniqueness
is the deduplication contract for contact records.

**Acceptance criteria**
- `account_id` unique in `warehouse_accounts`; `contact_id` unique in `warehouse_contacts`.
- `email_address` unique across all target contacts.

**Priority:** Critical (keys) / Medium (email).
**Verified by:** TC-ETL-004, 004b, 004c.

## REQ-ETL-05 — Referential Integrity

**Statement.** Every contact's `account_id` foreign key *shall* resolve to an existing
account, in both the source extract and the target load.

**Rationale.** Orphaned contacts break account-level rollups; checking the source too
distinguishes "ETL broke it" from "it arrived broken".

**Acceptance criteria**
- ∀ target contact: `account_id` ∈ target accounts.
- ∀ source contact: `account_id` ∈ source accounts.

**Priority:** Critical · **Risk if unmet:** orphaned records corrupt reporting joins.
**Verified by:** TC-ETL-005, 005b.

## REQ-ETL-06 — Business Rules & Load Metadata

**Statement.** Target records *shall* respect business-rule constraints: status values
from the approved enumeration, a load timestamp on every record, and no future-dated
creation dates.

**Acceptance criteria**
- `record_status` and `contact_status` values ∈ their allowed value sets.
- `load_timestamp` present (non-null) on every target account record.
- `created_date` ≤ execution date for every record.

**Priority:** Medium · **Risk if unmet:** invalid states enter downstream workflows; audit trail gaps.
**Verified by:** TC-ETL-006, 006b, 006c, 006d.
