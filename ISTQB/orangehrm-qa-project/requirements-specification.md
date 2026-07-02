# Testing Requirements Specification — OrangeHRM UI Automation Suite

| | |
|---|---|
| **Identifier** | TRS-OHR-001 |
| **Suite** | `orangehrm-qa-project` |
| **Test basis** | Live OrangeHRM demo (https://opensource-demo.orangehrmlive.com), vendor-managed; demo credentials published by OrangeHRM |
| **Date** | 2026-07-01 |

Verification method for all requirements: **Test** (Playwright UI assertions) plus
**Inspection** for REQ-OHR-07 (screenshot evidence reviewed by a human). Traceability:
see TCS-OHR-001 §2.

---

## REQ-OHR-01 — Valid Authentication

**Statement.** A user presenting valid credentials *shall* be authenticated and taken
to the dashboard.

**Acceptance criteria**
- Login with the published demo credentials succeeds.
- Post-login URL/route is the dashboard and the dashboard header is visible.
- No error banner is displayed.

**Priority:** Critical · **Risk if unmet:** application unusable.
**Verified by:** TC-OHR-001.

## REQ-OHR-02 — Invalid Login Rejection

**Statement.** Every invalid username/password combination *shall* be rejected, and all
combinations *shall* be rejected identically (same error, no information disclosure).

**Rationale.** Differing error messages for "wrong user" vs. "wrong password" enable
username enumeration — a security weakness, not just a functional bug.

**Acceptance criteria**
- Wrong-password, wrong-username, and both-wrong combinations all fail
  (data-driven matrix in the parametrized test).
- The same "Invalid credentials" message is shown for every combination.
- The user remains on the login page with no session created.

**Priority:** Critical · **Risk if unmet:** unauthorized access / enumeration vector.
**Verified by:** TC-OHR-002, TC-OHR-003.

## REQ-OHR-03 — Required-Field Validation

**Statement.** Username and password *shall* be mandatory; submitting with either empty
*shall* produce inline "Required" validation without a server round-trip error.

**Acceptance criteria**
- Empty username → "Required" hint at the username field.
- Empty password → "Required" hint at the password field.
- Form is not submitted while a required field is empty.

**Priority:** High · **Risk if unmet:** malformed auth requests; poor UX.
**Verified by:** TC-OHR-004.

## REQ-OHR-04 — Dashboard Availability

**Statement.** The dashboard *shall* render its widget layout immediately after login.

**Acceptance criteria**
- Dashboard heading visible after the `logged_in_page` fixture completes.
- Widget region present (structure asserted, not widget data — the shared demo's
  contents are volatile).

**Priority:** Critical · **Risk if unmet:** post-login landing broken for all users.
**Verified by:** TC-OHR-005.

## REQ-OHR-05 — Module Navigation

**Statement.** The PIM and Admin modules *shall* be reachable from the side menu, each
rendering its module header.

**Acceptance criteria**
- Clicking **PIM** loads the employee-list view with the PIM header.
- Clicking **Admin** loads the system-users view with the Admin header.

**Priority:** High · **Risk if unmet:** core HR functions unreachable.
**Verified by:** TC-OHR-006, TC-OHR-007.

## REQ-OHR-06 — Session Termination

**Statement.** Logout *shall* end the session, return the user to the login page, and
protected pages *shall not* be accessible afterwards.

**Rationale.** Incomplete logout on shared machines leaves HR data (salaries, personal
records) exposed — checking the redirect alone is insufficient.

**Acceptance criteria**
- Logout via the user menu returns to the login page.
- Navigating directly to a protected route after logout redirects to login
  (evidenced by TC-OHR-016's restricted-access screenshot).

**Priority:** Critical · **Risk if unmet:** session fixation / data exposure on shared terminals.
**Verified by:** TC-OHR-008, TC-OHR-016.

## REQ-OHR-07 — Requirement Evidence Capture

**Statement.** Each major module and validation flow *shall* be evidenced by
screenshots archived with the test run: navigation menu, PIM, Admin, Leave,
Recruitment, My Info, form validation/usability, and post-logout restricted access.

**Rationale.** For acceptance sign-off against a third-party system, human-reviewable
evidence of the deployed UI at execution time is part of the deliverable, since the
vendor can change the site without notice.

**Acceptance criteria**
- One or more screenshots captured per listed area, saved under `artifacts/`.
- Screenshots are taken from an authenticated session (except the restricted-access shot).
- Evidence set is complete for all eight areas in every accepted run.

**Priority:** Medium · **Risk if unmet:** no audit trail for acceptance claims.
**Verified by:** TC-OHR-009 … TC-OHR-016 (Inspection of artifacts).
