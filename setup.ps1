$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    throw "O comando 'uv' não foi encontrado. Instale-o em https://docs.astral.sh/uv/getting-started/installation/"
}

$env:UV_CACHE_DIR = Join-Path $PSScriptRoot "work\uv-cache"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    uv venv .venv
} else {
    Write-Host "Ambiente virtual existente será reutilizado." -ForegroundColor Cyan
}
uv pip install --python ".venv\Scripts\python.exe" -r requirements.txt

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
}

Write-Host "Ambiente preparado. Execute: .\start.ps1" -ForegroundColor Green
