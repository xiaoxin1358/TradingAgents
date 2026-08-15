# frontend.ps1 — one-command launcher for the TradingAgents web UI.
# Starts the FastAPI backend (:8000) and Vite dev server (:5173) if they are
# not already running, then opens the dashboard in the default browser.
# Safe to run repeatedly — already-running services are left untouched.
#
# ponytail: assumes default ports 8000/5173; if either port is taken by
# something else the browser may show the wrong app (upgrade path: check the
# served content or read a pid file).

$ErrorActionPreference = "SilentlyContinue"

$Root = $PSScriptRoot
$Python = "D:\anaconda3\envs\TradingAgent\python.exe"
$env:PATH = "D:\anaconda3\envs\TradingAgent;" + $env:PATH  # node lives in conda env

function Test-Port($Port) {
    (Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue).TcpTestSucceeded
}

# 1. backend (FastAPI, port 8000)
if (-not (Test-Port 8000)) {
    Start-Process $Python -ArgumentList "-m", "uvicorn", "webapi.main:app", "--port", "8000" `
        -WorkingDirectory $Root -WindowStyle Hidden
    Write-Host "backend started (http://127.0.0.1:8000)"
    Start-Sleep -Seconds 2
} else {
    Write-Host "backend already running"
}

# 2. frontend (Vite dev, port 5173)
if (-not (Test-Port 5173)) {
    Start-Process "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory "$Root\frontend" `
        -WindowStyle Hidden
    Write-Host "frontend started (http://localhost:5173)"
    Start-Sleep -Seconds 2
} else {
    Write-Host "frontend already running"
}

# 3. open the dashboard
Start-Process "http://localhost:5173/"
Write-Host "opened the dashboard in your browser"
