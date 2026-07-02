# QA Automation Portfolio

Six automated test suites — spanning AI/LLM evaluation, ETL data validation, legal-domain
business rules, financial reconciliation, and live-site UI automation — run and monitored
from a single Flask dashboard with live streaming test output. Each suite ships with
formal ISTQB-aligned documentation (test plan, requirements specification, test case
specification with traceability matrix, and test summary report).

**Author:** R. Anthony Graves

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14 (3.12+ supported) |
| Test framework | pytest 9 · pytest-html reports · pytest-xdist (parallel) · pytest-rerunfailures |
| UI automation | Playwright 1.60 (Chromium) via pytest-playwright |
| Data validation | pandas · deterministic JSON/CSV fixtures |
| Dashboard backend | Flask 3.1 · Server-Sent Events (live pytest streaming) · subprocess runner |
| Dashboard frontend | Tailwind CSS · Lucide icons · vanilla JS (no build step) |
| QA documentation | ISTQB / ISO-IEC-IEEE 29119-3 templates (Markdown) |

## Start the App

```bash
python app.py        # → http://127.0.0.1:5000
```

That's it if dependencies are already installed. First time here? Use the
[one-shot setup script](#quick-start) below, which ends by starting the app for you.

## Test Suites

| Suite | Type | Tests | Highlights |
|---|---|---|---|
| [ai-prompt-validation-qa](ai-prompt-validation-qa/) | LLM response validation | 18 | Factual accuracy, refusals, JSON/format compliance, hallucination, PII safety, bias, latency — against recorded `gpt-4o` responses |
| [etl-data-validation-qa](etl-data-validation-qa/) | Data migration validation | 22 | Source→target reconciliation (counts, mapping, nulls, duplicates, referential integrity) on a Northwind-derived dataset, with defect-injection tooling |
| [legal-ai-prompt-review-qa](legal-ai-prompt-review-qa/) | Domain LLM evaluation | 18 | Real case law (Palsgraf, Miranda, Alice Corp, GDPR Art. 17) plus a seeded fictitious case proving hallucination containment |
| [legal-billing-qa](legal-billing-qa/) | Business rule validation | 19 | UTBMS codes, 2024 ABA rates, daily-hours limits, closed-matter enforcement, invoice reconciliation — 4 seeded defects, all detected |
| [workday-financial-validation-qa](workday-financial-validation-qa/) | Financial reconciliation | 16 | Three-way payroll ⇄ HR ⇄ GL reconciliation with IRS 2024 rates; balanced ledger; terminated-employee control probe |
| [orangehrm-qa-project](orangehrm-qa-project/) | E2E UI automation (Playwright) | 16 | Live OrangeHRM demo: auth (positive/negative/parametrized), navigation, logout, screenshot evidence capture |

A deliberate theme across the suites: **seeded defects**. Test checks are only
trustworthy if they can fail, so several datasets contain known bad records (a 25-hour
time entry, a fabricated court case, a PII-echoing response, a terminated employee still
in payroll) that the suites must positively detect.

## ISTQB Documentation

The [ISTQB/](ISTQB/) folder contains, per suite:

- **Requirements specification** — shall-statements, rationale, measurable acceptance criteria
- **Test plan** — scope, approach, entry/exit criteria, risks (ISO/IEC/IEEE 29119-3)
- **Test case specification** — every test case tabulated + requirements traceability matrix
- **Test summary report** — results, seeded-defect outcomes, exit-criteria evaluation

The `TC-*`/`REQ-*` IDs in the documents mirror the IDs embedded in the pytest docstrings,
so the code is the source of truth.

## Quick Start

Requires **Python 3.12+** (developed on 3.14). Clone with the submodule so the OrangeHRM
suite comes along:

```bash
git clone --recurse-submodules https://github.com/r-anthony-graves/qa-portfolio.git
cd qa-portfolio
# already cloned without it? run: git submodule update --init
```

Then one command sets everything up — virtual environment, all dependencies, Playwright
browser — and starts the dashboard:

**Windows (PowerShell)**

```powershell
.\setup.ps1
```

**macOS / Linux / Git Bash**

```bash
./setup.sh
```

Then open **http://127.0.0.1:5000**.

Script options (both platforms):

| Option | Effect |
|---|---|
| `-SkipBrowsers` / `--skip-browsers` | Skip the Playwright Chromium download (everything except the OrangeHRM suite still works) |
| `-NoRun` / `--no-run` | Set up only; don't start the dashboard |

<details>
<summary>Manual setup (if you prefer)</summary>

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -r orangehrm-qa-project/requirements.txt
playwright install chromium
python app.py
```
</details>

## The Dashboard

`app.py` serves a single-page dashboard (Tailwind, follows your OS light/dark theme) that:

- runs any suite via **Run Tests** and streams pytest output live (Server-Sent Events)
  into an embedded terminal panel
- runs everything sequentially via **Run All** with a progress bar
- tracks per-suite pass/fail counts, pass-rate bars, durations, and global counters
- links each suite's **pytest-html report** and, for OrangeHRM, the **live site**
- explains each suite's rationale and coverage via the ⓘ hover tooltip on every card

## Running Suites from the CLI

Every suite is a standalone pytest project:

```bash
cd etl-data-validation-qa
python -m pytest -v                  # report lands in artifacts/report.html
```

The OrangeHRM suite tests the public demo at
https://opensource-demo.orangehrmlive.com (network required):

```bash
cd orangehrm-qa-project
python -m pytest                     # report: artifacts/reports/orangehrm_report.html
python -m pytest -n auto             # parallel via pytest-xdist
```

## Project Structure

```
qa-portfolio/
├── app.py                           # Flask backend: PROJECTS registry, SSE streaming, report serving
├── templates/index.html             # Dashboard UI (Tailwind, Lucide, vanilla JS)
├── requirements.txt                 # Dashboard + data-driven suite dependencies
├── setup.ps1 / setup.sh             # One-shot setup & run scripts
├── ISTQB/                           # Formal QA documentation (4 docs × 6 suites)
├── ai-prompt-validation-qa/         # ── each suite: ──
├── etl-data-validation-qa/          #   data/       test data (JSON/CSV)
├── legal-ai-prompt-review-qa/       #   tests/      pytest test cases
├── legal-billing-qa/                #   artifacts/  pytest-html reports
├── workday-financial-validation-qa/ #   scripts/    (where applicable) data generators
└── orangehrm-qa-project/            # Playwright E2E suite (own pinned requirements.txt)
```

## Repository Notes

- **Submodule:** [orangehrm-qa-project](https://github.com/r-anthony-graves/orangehrm-qa-project)
  is maintained as its own repository and included here as a git submodule, pinned to a
  verified commit — one source of truth, no duplicated code. If its folder is empty after
  cloning, run `git submodule update --init`.
- **Generated output is not committed:** `.gitignore` excludes `.venv/`, `artifacts/`
  (pytest-html reports), `__pycache__/`, `.pytest_cache/`, and `.env`. Reports regenerate
  on every test run, locally or from the dashboard.

## Test Status

| Suite | Last result |
|---|---|
| ai-prompt-validation-qa | ✅ 18/18 |
| etl-data-validation-qa | ✅ 22/22 |
| legal-ai-prompt-review-qa | ✅ 18/18 |
| legal-billing-qa | ✅ 19/19 |
| workday-financial-validation-qa | ✅ 16/16 |
| orangehrm-qa-project | 🌐 run on demand against the live demo |
