<#
.SYNOPSIS
    One-shot setup + run for the QA Automation Portfolio (Windows).

.DESCRIPTION
    Creates a virtual environment, installs all dependencies (dashboard,
    data-driven suites, and the OrangeHRM Playwright suite), installs the
    Chromium browser for Playwright, then starts the dashboard at
    http://127.0.0.1:5000.

.PARAMETER SkipBrowsers
    Skip the Playwright browser download (data-driven suites and the
    dashboard still work; only the OrangeHRM suite needs the browser).

.PARAMETER NoRun
    Set up everything but do not start the dashboard.

.EXAMPLE
    .\setup.ps1
    .\setup.ps1 -SkipBrowsers -NoRun
#>
param(
    [switch]$SkipBrowsers,
    [switch]$NoRun
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

# 1. Verify Python
Step "Checking Python"
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Host "Python not found on PATH. Install Python 3.12+ from python.org." -ForegroundColor Red; exit 1 }
$ver = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
Write-Host "Found Python $ver"
if ([version]$ver -lt [version]"3.12") { Write-Host "Python 3.12+ required (found $ver)." -ForegroundColor Red; exit 1 }

# 2. Virtual environment
Step "Creating virtual environment (.venv)"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    & python -m venv (Join-Path $root ".venv")
    if ($LASTEXITCODE -ne 0) { Write-Host "venv creation failed." -ForegroundColor Red; exit 1 }
} else {
    Write-Host ".venv already exists - reusing"
}

# 3. Dependencies
Step "Installing dashboard + data-suite dependencies"
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r (Join-Path $root "requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Host "pip install failed." -ForegroundColor Red; exit 1 }

Step "Installing OrangeHRM Playwright suite dependencies"
& $venvPython -m pip install -r (Join-Path $root "orangehrm-qa-project\requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Host "pip install (OrangeHRM) failed." -ForegroundColor Red; exit 1 }

# 4. Playwright browser
if (-not $SkipBrowsers) {
    Step "Installing Playwright Chromium (skip with -SkipBrowsers)"
    & $venvPython -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { Write-Host "Playwright browser install failed (OrangeHRM suite will not run)." -ForegroundColor Yellow }
} else {
    Write-Host "Skipping Playwright browser install (-SkipBrowsers)"
}

# 5. Smoke check: collect tests without running them
Step "Smoke check - collecting data-driven suites"
$suites = @("ai-prompt-validation-qa", "etl-data-validation-qa", "legal-ai-prompt-review-qa",
            "legal-billing-qa", "workday-financial-validation-qa")
foreach ($s in $suites) {
    & $venvPython -m pytest (Join-Path $root $s) --collect-only -q | Select-Object -Last 1
    if ($LASTEXITCODE -ne 0) { Write-Host "Collection failed for $s" -ForegroundColor Red; exit 1 }
}

# 6. Run
if ($NoRun) {
    Step "Setup complete"
    Write-Host "Start the dashboard with:  .venv\Scripts\python.exe app.py"
} else {
    Step "Starting dashboard at http://127.0.0.1:5000  (Ctrl+C to stop)"
    & $venvPython (Join-Path $root "app.py")
}
