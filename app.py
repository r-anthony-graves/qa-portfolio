"""
QA Portfolio Dashboard — Main Application
Run: python app.py   →   http://127.0.0.1:5000
"""

import json
import subprocess
import time
from pathlib import Path
from flask import Flask, render_template, Response, stream_with_context, jsonify, send_file

BASE_DIR = Path(__file__).parent

PROJECTS: dict = {
    "ai-prompt-validation-qa": {
        "name": "AI Prompt Validation",
        "description": "Validates LLM responses for factual accuracy, safety, format compliance, and refusal behavior using mock responses.",
        "icon": "cpu",
        "tags": ["AI/ML", "LLM", "Prompt Engineering"],
        "tech": ["pytest", "openai", "pydantic", "python-dotenv"],
        "accent": "#6366f1",
        "tooltip": {
            "rationale": "LLM outputs are non-deterministic — the same prompt can return different results across runs, model versions, and temperature settings. Systematic response validation is essential before any AI feature ships to production.",
            "validates": [
                "Factual accuracy via expected keyword matching",
                "Refusal behavior on harmful or off-topic prompts",
                "Response format and structural compliance",
                "PII leakage and sensitive data in outputs",
                "Bias detection across demographic groups",
            ],
        },
    },
    "etl-data-validation-qa": {
        "name": "ETL Data Validation",
        "description": "End-to-end Salesforce → Data Warehouse migration validation covering record counts, field mappings, nulls, and duplicates.",
        "icon": "git-merge",
        "tags": ["ETL", "Data Quality", "Salesforce"],
        "tech": ["pytest", "pandas"],
        "accent": "#0ea5e9",
        "tooltip": {
            "rationale": "Silent data loss or corruption during ETL pipelines is a critical enterprise risk. Decisions made on incomplete warehouse data cascade into reporting errors, compliance failures, and lost business insight.",
            "validates": [
                "Source-to-target record count reconciliation",
                "Field mapping accuracy (Salesforce → warehouse schema)",
                "Null and empty field enforcement on required columns",
                "Duplicate primary key and email detection",
                "Foreign key and referential integrity constraints",
                "Business rule and status value enforcement",
            ],
        },
    },
    "legal-ai-prompt-review-qa": {
        "name": "Legal AI Prompt Review",
        "description": "DeepJudge-style evaluation of AI legal query responses for hallucination detection, citation quality, and scope compliance.",
        "icon": "scale-3d",
        "tags": ["Legal", "AI/ML", "Hallucination"],
        "tech": ["pytest", "pydantic"],
        "accent": "#f59e0b",
        "tooltip": {
            "rationale": "AI-generated legal responses with hallucinated case citations, incorrect statutes, or wrong jurisdictions can expose law firms to professional liability and cause direct client harm. Every response must be evaluated for factual and citation integrity.",
            "validates": [
                "Hallucination detection: fabricated cases, statutes, dates",
                "Citation quality and jurisdiction accuracy",
                "Hedging language appropriateness",
                "Out-of-scope and speculative response flagging",
                "Factual accuracy on legal questions",
            ],
        },
    },
    "legal-billing-qa": {
        "name": "Legal Billing Validation",
        "description": "Validates Aderant-style time entry rules, UTBMS codes, billing rate calculations, and invoice accuracy.",
        "icon": "briefcase",
        "tags": ["Legal", "Billing", "UTBMS"],
        "tech": ["pytest"],
        "accent": "#10b981",
        "tooltip": {
            "rationale": "Incorrect UTBMS codes, time rounding violations, or billing against closed matters create audit risks, client disputes, and direct revenue leakage in legal practice management systems.",
            "validates": [
                "UTBMS task and activity code compliance",
                "Daily billing hour cap enforcement (24h max)",
                "Billing rate accuracy per timekeeper grade",
                "Matter status enforcement (no billing on closed matters)",
                "Invoice total arithmetic and rounding accuracy",
            ],
        },
    },
    "workday-financial-validation-qa": {
        "name": "Workday Financial Validation",
        "description": "Payroll reconciliation, gross-to-net accuracy, GL code mapping, and headcount validation against HR roster.",
        "icon": "dollar-sign",
        "tags": ["Finance", "Payroll", "Workday"],
        "tech": ["pytest", "pandas"],
        "accent": "#f43f5e",
        "tooltip": {
            "rationale": "Payroll calculation errors directly impact employee compensation and can trigger regulatory penalties. GL mapping errors distort financial reporting and create reconciliation failures at period close.",
            "validates": [
                "Gross-to-net accuracy against federal, state, SS, and Medicare rates",
                "GL code mapping from payroll to general ledger",
                "Headcount reconciliation against HR roster",
                "Terminated employee payroll flag enforcement",
                "Deduction totals and net pay arithmetic",
            ],
        },
    },
    "orangehrm-qa-project": {
        "name": "OrangeHRM E2E",
        "description": "Playwright end-to-end suite against the OrangeHRM live demo — login, PIM, leave, recruitment, and admin flows with screenshot evidence.",
        "icon": "monitor-check",
        "tags": ["E2E", "Playwright", "HRMS", "OrangeHRM"],
        "tech": ["pytest", "playwright", "pytest-html"],
        "accent": "#f97316",
        "report_path": "artifacts/reports/orangehrm_report.html",
        "site_url": "https://opensource-demo.orangehrmlive.com",
        "tooltip": {
            "rationale": "Unit and API tests cannot catch UI regressions that block critical HR workflows. Playwright-driven end-to-end tests verify the full application stack — browser to backend — against the live OrangeHRM demo site exactly as a real user would experience it.",
            "validates": [
                "Login authentication and session management",
                "PIM employee create, edit, and search flows",
                "Leave application, approval, and balance display",
                "Recruitment pipeline and vacancy management",
                "Admin module configuration and role assignment",
            ],
        },
    },
}

app = Flask(__name__)

# In-memory result store (reset on server restart)
results: dict = {
    pid: {"status": "idle", "passed": 0, "failed": 0, "total": 0, "duration": 0.0}
    for pid in PROJECTS
}


@app.route("/")
def index():
    report_exists = {
        pid: (BASE_DIR / pid / PROJECTS[pid].get("report_path", "artifacts/report.html")).exists()
        for pid in PROJECTS
    }
    return render_template("index.html", projects=PROJECTS, results=results, report_exists=report_exists)


@app.route("/run/<project_id>")
def run_tests(project_id: str):
    if project_id not in PROJECTS:
        return jsonify({"error": "Unknown project"}), 404

    project_dir = BASE_DIR / project_id

    def generate():
        results[project_id].update({"status": "running", "passed": 0, "failed": 0, "total": 0})
        yield f"data: {json.dumps({'type': 'status', 'status': 'running'})}\n\n"

        start = time.monotonic()
        process = subprocess.Popen(
            ["python", "-m", "pytest"],
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        passed = failed = 0
        for raw_line in process.stdout:
            line = raw_line.rstrip()
            if " PASSED" in line:
                passed += 1
            elif " FAILED" in line or " ERROR" in line:
                failed += 1
            yield f"data: {json.dumps({'type': 'line', 'text': line})}\n\n"

        process.wait()
        duration = round(time.monotonic() - start, 2)
        total = passed + failed
        status = "passed" if process.returncode == 0 else "failed"

        results[project_id].update(
            {"status": status, "passed": passed, "failed": failed, "total": total, "duration": duration}
        )
        yield f"data: {json.dumps({'type': 'done', 'status': status, 'passed': passed, 'failed': failed, 'total': total, 'duration': duration})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/report/<project_id>")
def view_report(project_id: str):
    if project_id not in PROJECTS:
        return jsonify({"error": "Unknown project"}), 404
    rel = PROJECTS[project_id].get("report_path", "artifacts/report.html")
    report_path = BASE_DIR / project_id / rel
    if not report_path.exists():
        return "Report not generated yet. Run tests first.", 404
    return send_file(str(report_path))


@app.route("/status")
def get_status():
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000, threaded=True)
