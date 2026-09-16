$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $ProjectRoot

$PythonPath = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$ManagePath = Join-Path $ProjectRoot "manage.py"

if (-not (Test-Path $PythonPath)) {
    Write-Host "ERROR: No se encontró el entorno virtual de Pronty."
    Write-Host "Ruta esperada: $PythonPath"
    exit 1
}

if (-not (Test-Path $ManagePath)) {
    Write-Host "ERROR: No se encontró manage.py."
    Write-Host "Ruta esperada: $ManagePath"
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host " PRONTY - PROCESO DE RESERVAS VENCIDAS"
Write-Host "========================================"
Write-Host ""

Write-Host "Proyecto:"
Write-Host $ProjectRoot
Write-Host ""

Write-Host "Ejecutando expire_reservations..."
Write-Host ""

& $PythonPath $ManagePath expire_reservations

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: El proceso de reservas terminó con errores."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Proceso finalizado correctamente."
Write-Host ""