$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Ambiente não preparado. Execute .\setup.ps1 primeiro."
}

& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

