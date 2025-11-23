# Production Simulator Launcher
# Lance le simulateur avec configuration automatique des URLs

param(
    [Parameter(Position=0)]
    [string]$AppUrl = "http://localhost:5000",
    
    [Parameter(Position=1)]
    [int]$Interval = 30,
    
    [Parameter(Position=2)]
    [float]$PanneProb = 0.1,
    
    [switch]$Production,
    [switch]$NoAutoDetect,
    [int]$Cycles,
    [switch]$Verbose
)

# Bannière
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         🚀 Simulateur Frigorifique - Production Ready         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Configuration Production
if ($Production) {
    Write-Host "🌐 MODE PRODUCTION" -ForegroundColor Yellow
    $AppUrl = "https://frigo-app.onrender.com"
    $env:MAIN_APP_URL = "https://frigo-app.onrender.com"
    $env:CHAT_API_URL = "https://frigo-chat.onrender.com"
    $env:IA_SERVICE_URL = "https://frigo-gpt.onrender.com"
    Write-Host "   URLs Render configurées" -ForegroundColor Green
} else {
    Write-Host "🏠 MODE LOCAL (Docker/Localhost)" -ForegroundColor Green
}

Write-Host ""
Write-Host "⚙️  Configuration:" -ForegroundColor Cyan
Write-Host "   App URL:        $AppUrl"
Write-Host "   Intervalle:     $Interval secondes"
Write-Host "   Prob. panne:    $($PanneProb * 100)%"

if ($Cycles -gt 0) {
    Write-Host "   Cycles:         $Cycles"
} else {
    Write-Host "   Cycles:         ∞ (Ctrl+C pour arrêter)"
}

Write-Host ""

# Construire la commande
$pythonArgs = @(
    "simulateur_production.py"
    "--app-url", $AppUrl
    "--interval", $Interval
    "--prob-panne", $PanneProb
)

if ($NoAutoDetect) {
    $pythonArgs += "--no-auto-detect"
}

if ($Cycles -gt 0) {
    $pythonArgs += "--cycles", $Cycles
}

if ($Verbose) {
    Write-Host "🔧 Commande: python $($pythonArgs -join ' ')" -ForegroundColor Gray
    Write-Host ""
}

# Vérifier que le fichier existe
if (-not (Test-Path "simulateur_production.py")) {
    Write-Host "❌ Erreur: simulateur_production.py non trouvé" -ForegroundColor Red
    exit 1
}

# Lancer le simulateur
Write-Host "▶️  Démarrage du simulateur..." -ForegroundColor Green
Write-Host ""

python @pythonArgs

Write-Host ""
Write-Host "⏹️  Simulateur arrêté" -ForegroundColor Yellow
