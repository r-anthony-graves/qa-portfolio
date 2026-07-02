# Test Plan — OrangeHRM UI Automation Suite

| | |
|---|---|
| **Identifier** | TP-OHR-001 |
| **Suite** | `orangehrm-qa-project` |
| **Author** | R. Anthony Graves |
| **Date** | 2026-07-01 |
| **Status** | Approved |

## 1. Introduction & Objectives

End-to-end UI validation of the public OrangeHRM demo instance
(https://opensource-demo.orangehrmlive.com) using Playwright: authentication (positive
and negative), post-login dashboard availability, module navigation, session
termination, and screenshot evidence capture for each functional area.

## 2. Test Items

- System under test: live OrangeHRM demo (version as deployed by the vendor).
- `tests/test_login.py`, `tests/test_dashboard.py`, `tests/test_navigation.py`,
  `tests/test_requirement_screenshots.py` — 16 automated test functions
  (pytest-playwright; one login test is data-driven/parametrized).
- Report: `artifacts/reports/orangehrm_report.html`; screenshots under `artifacts/`.

## 3. Features to be Tested

| Req ID | Requirement |
|---|---|
| REQ-OHR-01 | Valid credentials authenticate and land on the dashboard |
| REQ-OHR-02 | Every invalid username/password combination is rejected identically |
| REQ-OHR-03 | Username and password are required fields (inline validation) |
| REQ-OHR-04 | Dashboard renders after login |
| REQ-OHR-05 | PIM and Admin modules are reachable from the side menu |
| REQ-OHR-06 | Logout terminates the session and restricts access to protected pages |
| REQ-OHR-07 | Each major module (PIM, Admin, Leave, Recruitment, My Info) and the validation/usability flows are evidenced by screenshots |

## 4. Features Not to be Tested

- Data-mutation flows (adding/deleting employees) — the demo is shared and reset by
  the vendor; destructive actions are avoided.
- Performance, accessibility, localisation, and API-level behaviour.

## 5. Approach

- **Test level:** system/acceptance testing against a live deployment.
- **Design techniques:** use-case testing (login → navigate → logout), equivalence
  partitioning + decision table on credential combinations (parametrized negative
  login test), and evidence-driven testing (screenshot capture per requirement).
- **Automation:** pytest-playwright (Playwright 1.60), `pytest-rerunfailures` for
  live-site flakiness, `pytest-xdist` capable.

## 6. Item Pass/Fail Criteria

A test passes when Playwright assertions on visible UI state hold. Suite passes when
all 16 tests pass (reruns permitted for transient network failures).

## 7. Entry / Exit Criteria

- **Entry:** demo site reachable; Playwright browsers installed (`playwright install`).
- **Exit:** all tests executed; HTML report and screenshot evidence archived.

## 8. Test Environment

Windows 11 Pro, Python 3.14 (64-bit), pytest-playwright, Chromium; network access to
the public demo instance required.

## 9. Risks & Contingencies

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Demo site down / rate-limited | Medium | High | Reruns via pytest-rerunfailures; run off-peak |
| Vendor UI changes break selectors | Medium | Medium | Role/label-based locators preferred over CSS paths |
| Shared demo data mutated by other users | High | Low | Tests assert structure/visibility, not record contents |
