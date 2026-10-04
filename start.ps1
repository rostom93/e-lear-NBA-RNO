<#
.SYNOPSIS
  Lance EduLearn : API Django sur 8000 + front Angular sur 4200.

.DESCRIPTION
  Libère d'abord les deux ports (un ancien `ng serve` qui traîne fait échouer le
  démarrage avec « Port 4200 is already in use »), puis ouvre un terminal par
  serveur. Ctrl+C dans une fenêtre arrête le serveur correspondant.

.EXAMPLE
  .\start.ps1
#>

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = Join-Path $root 'backend\.venv\Scripts\python.exe'

function Stop-Port {
    param([int]$Port)

    $owners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($owner in $owners) {
        try {
            $proc = [System.Diagnostics.Process]::GetProcessById($owner)
            $proc.Kill()
            $proc.WaitForExit(10000) | Out-Null
            Write-Host "  port $Port : processus $owner arrete" -ForegroundColor Yellow
        } catch {
            Write-Host "  port $Port : impossible d'arreter $owner ($($_.Exception.GetBaseException().Message))" -ForegroundColor Red
        }
    }
    if (-not $owners) {
        Write-Host "  port $Port : libre" -ForegroundColor DarkGray
    }
}

function Wait-Url {
    param([string]$Url, [int]$TimeoutSeconds = 90)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $null = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            return $true
        } catch {
            if ($_.Exception.Response) { return $true }   # repond, meme en 4xx/5xx
            Start-Sleep -Seconds 2
        }
    }
    return $false
}

if (-not (Test-Path $python)) {
    throw "Environnement Python introuvable : $python`nCreez-le avec : cd backend; python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
}

Write-Host "`n[1/3] Liberation des ports" -ForegroundColor Cyan
Stop-Port -Port 4200
Stop-Port -Port 8000

Write-Host "`n[2/3] Demarrage des serveurs" -ForegroundColor Cyan
Start-Process -FilePath 'powershell.exe' `
    -ArgumentList '-NoExit', '-Command', "Set-Location '$root\backend'; & '$python' manage.py runserver 127.0.0.1:8000" `
    -WorkingDirectory "$root\backend"
Write-Host '  API Django    -> http://127.0.0.1:8000/' -ForegroundColor Green

Start-Process -FilePath 'powershell.exe' `
    -ArgumentList '-NoExit', '-Command', "Set-Location '$root\frontend'; npm start" `
    -WorkingDirectory "$root\frontend"
Write-Host '  Front Angular -> http://127.0.0.1:4200/' -ForegroundColor Green

Write-Host "`n[3/3] Verification" -ForegroundColor Cyan
if (Wait-Url -Url 'http://127.0.0.1:8000/api/courses/') {
    Write-Host '  API prete' -ForegroundColor Green
} else {
    Write-Host '  API injoignable : voir la fenetre Django' -ForegroundColor Red
}
if (Wait-Url -Url 'http://127.0.0.1:4200/') {
    Write-Host '  Front pret' -ForegroundColor Green
    Write-Host "`nOuvrez http://127.0.0.1:4200/`n" -ForegroundColor Cyan
} else {
    Write-Host '  Front injoignable : voir la fenetre Angular' -ForegroundColor Red
}
