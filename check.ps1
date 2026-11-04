<#
.SYNOPSIS
  Windows PowerShell equivalent of `make check`.
  Runs ruff, mypy, import-linter, and pytest — same checks as CI.

.EXAMPLE
  .\check.ps1
  .\check.ps1 -SkipTests
#>

param(
    [switch]$SkipTests,
    [switch]$SkipLint
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PythonExe = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } elseif (Test-Path ".venv/bin/python") { ".venv/bin/python" } else { "python" }

function Invoke-Step {
    param([string]$Label, [scriptblock]$Block)
    Write-Host "`n==> $Label" -ForegroundColor Cyan
    & $Block
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED: $Label" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# ── Format ───────────────────────────────────────────────────────────────────
Invoke-Step "ruff format" {
    & $PythonExe -m ruff format .
}

Invoke-Step "ruff check (auto-fix)" {
    & $PythonExe -m ruff check --fix .
}

if (-not $SkipLint) {
    # ── Type-check ───────────────────────────────────────────────────────────────
    Invoke-Step "mypy (libs/)" {
        & $PythonExe -m mypy libs/
    }

    # ── Import-linter ────────────────────────────────────────────────────────────
    $LintImportsExe = if (Test-Path ".\.venv\Scripts\lint-imports.exe") { ".\.venv\Scripts\lint-imports.exe" } elseif (Test-Path ".venv/bin/lint-imports") { ".venv/bin/lint-imports" } else { "lint-imports" }
    Invoke-Step "import-linter" {
        & $LintImportsExe
    }
}

if (-not $SkipTests) {
    # ── Unit + leakage tests ─────────────────────────────────────────────────────
    Invoke-Step "pytest (unit + leakage)" {
        & $PythonExe -m pytest tests/unit tests/leakage --tb=short -v
    }
}

Write-Host "`nAll checks passed!" -ForegroundColor Green

