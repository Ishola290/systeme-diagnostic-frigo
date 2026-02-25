# Script de lancement de tous les services
# Usage: .\start_all_services.ps1

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  LANCEMENT SYSTEME DIAGNOSTIC FRIGO" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Arrêter les services existants
Write-Host "[1/4] Arret des services existants..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
Write-Host "      ✅ Services arrêtés" -ForegroundColor Green
Write-Host ""

$basePath = "C:\Users\hp\Desktop\systeme-diagnostic-frigo"
$env:PYTHONPATH = $basePath

# Fonction pour lancer un service
function Start-ServiceProcess {
    param(
        [string]$Name,
        [string]$Script,
        [int]$Port,
        [string]$Color
    )
    
    Write-Host "[$Name] Démarrage sur port $Port..." -ForegroundColor $Color
    
    $job = Start-Job -ScriptBlock {
        param($path, $script, $port)
        $env:PYTHONPATH = $path
        & "$path\venv\Scripts\python.exe" "$path\$script" 2>&1
    } -ArgumentList $basePath, $Script, $Port
    
    Start-Sleep 3
    
    # Vérifier si le port répond
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "      ✅ $Name démarré (port $Port OK)" -ForegroundColor Green
        return $job
    } catch {
        Write-Host "      ⚠️  $Name démarré mais health check échoue" -ForegroundColor Yellow
        return $job
    }
}

# 1. Lancer app.py (port 5000)
$job1 = Start-ServiceProcess -Name "APP.PY" -Script "app.py" -Port 5000 -Color "Magenta"

# 2. Lancer gpt/app_ia.py (port 5002)  
$job2 = Start-ServiceProcess -Name "SERVICE IA" -Script "gpt\app_ia.py" -Port 5002 -Color "Blue"

# 3. Lancer chat/app_web.py (port 5001)
$job3 = Start-ServiceProcess -Name "CHAT WEB" -Script "chat\app_web.py" -Port 5001 -Color "Green"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  SERVICES LANCÉS" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  📱 Chat Web:    http://localhost:5001/dashboard" -ForegroundColor White
Write-Host "  🔧 API Principale: http://localhost:5000" -ForegroundColor White
Write-Host "  🤖 Service IA:     http://localhost:5002" -ForegroundColor White
Write-Host ""
Write-Host "  Pour lancer le simulateur:" -ForegroundColor Yellow
Write-Host "  venv\Scripts\python.exe simulateur.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Appuyez sur Ctrl+C pour arrêter tous les services" -ForegroundColor Red
Write-Host "==========================================" -ForegroundColor Cyan

# Garder le script actif pour maintenir les jobs
while ($true) {
    Start-Sleep 5
    
    # Vérifier l'état des jobs
    if ($job1.State -eq 'Failed' -or $job2.State -eq 'Failed' -or $job3.State -eq 'Failed') {
        Write-Host "⚠️  Un service a échoué!" -ForegroundColor Red
        Receive-Job $job1 -ErrorAction SilentlyContinue
        Receive-Job $job2 -ErrorAction SilentlyContinue
        Receive-Job $job3 -ErrorAction SilentlyContinue
    }
}
