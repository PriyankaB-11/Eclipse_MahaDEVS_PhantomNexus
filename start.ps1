$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$backendCmd = "Set-Location '$root\backend'; & '$root\.venv\Scripts\python.exe' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
$frontendCmd = "Set-Location '$root\frontend'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "Starting Phantom Nexus..."
Write-Host "  Backend  -> http://127.0.0.1:8000"
Write-Host "  Frontend -> http://localhost:5173"
