# Test Case Specification — OrangeHRM UI Automation Suite

| | |
|---|---|
| **Identifier** | TCS-OHR-001 |
| **Test basis** | Live demo at https://opensource-demo.orangehrmlive.com, TP-OHR-001 |
| **Automation** | `tests/` (pytest-playwright, 16 test functions) |

> **Note on IDs:** unlike the data-driven suites, the Playwright tests do not embed
> TC IDs in docstrings. The `TC-OHR-nnn` IDs below are assigned by this specification
> and keyed to the test function names, which remain the source of truth.

Preconditions: demo site reachable; `logged_in_page` fixture performs a valid login
where listed.

## 1. Test Cases

| TC ID | Test function (file) | Req | Expected Result | Priority |
|---|---|---|---|---|
| TC-OHR-001 | `test_valid_login` (test_login.py) | REQ-OHR-01 | Valid credentials → dashboard | Critical |
| TC-OHR-002 | `test_invalid_login` (test_login.py) | REQ-OHR-02 | Wrong credentials → "Invalid credentials" error | Critical |
| TC-OHR-003 | `test_invalid_login_credentials_rejected` (test_login.py, parametrized) | REQ-OHR-02 | Every wrong username/password combination rejected identically | High |
| TC-OHR-004 | `test_required_username_and_password` (test_login.py) | REQ-OHR-03 | Empty fields show "Required" validation | High |
| TC-OHR-005 | `test_dashboard_loads_after_login` (test_dashboard.py) | REQ-OHR-04 | Dashboard widgets render post-login | Critical |
| TC-OHR-006 | `test_pim_navigation` (test_navigation.py) | REQ-OHR-05 | PIM module loads from side menu | High |
| TC-OHR-007 | `test_admin_navigation` (test_navigation.py) | REQ-OHR-05 | Admin module loads from side menu | High |
| TC-OHR-008 | `test_logout` (test_navigation.py) | REQ-OHR-06 | Logout returns to login page | Critical |
| TC-OHR-009 | `test_navigation_menu_requirement_screenshot` (test_requirement_screenshots.py) | REQ-OHR-07 | Side-menu evidence captured | Medium |
| TC-OHR-010 | `test_pim_requirement_screenshots` (") | REQ-OHR-07 | PIM screens evidenced | Medium |
| TC-OHR-011 | `test_admin_requirement_screenshots` (") | REQ-OHR-07 | Admin screens evidenced | Medium |
| TC-OHR-012 | `test_leave_requirement_screenshots` (") | REQ-OHR-07 | Leave screens evidenced | Medium |
| TC-OHR-013 | `test_recruitment_requirement_screenshots` (") | REQ-OHR-07 | Recruitment screens evidenced | Medium |
| TC-OHR-014 | `test_my_info_requirement_screenshots` (") | REQ-OHR-07 | My Info screens evidenced | Medium |
| TC-OHR-015 | `test_validation_and_usability_requirement_screenshots` (") | REQ-OHR-07 | Form validation/usability evidenced | Medium |
| TC-OHR-016 | `test_logout_restricted_access_requirement_screenshot` (") | REQ-OHR-06, 07 | Post-logout restricted access evidenced | High |

## 2. Requirements Traceability Matrix

| Req ID | Requirement | Test Cases | Coverage |
|---|---|---|---|
| REQ-OHR-01 | Valid authentication | TC-OHR-001 | ✅ 1 TC |
| REQ-OHR-02 | Invalid login rejection | TC-OHR-002, TC-OHR-003 | ✅ 2 TCs (1 parametrized) |
| REQ-OHR-03 | Required-field validation | TC-OHR-004 | ✅ 1 TC |
| REQ-OHR-04 | Dashboard availability | TC-OHR-005 | ✅ 1 TC |
| REQ-OHR-05 | Module navigation | TC-OHR-006, TC-OHR-007 | ✅ 2 TCs |
| REQ-OHR-06 | Session termination | TC-OHR-008, TC-OHR-016 | ✅ 2 TCs |
| REQ-OHR-07 | Screenshot evidence per module | TC-OHR-009 … 016 | ✅ 8 TCs |

All 7 requirements covered; 16 test functions total; no orphan test cases.
