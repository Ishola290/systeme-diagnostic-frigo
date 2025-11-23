# Script de démarrage - Système Diagnostic Frigo
# Exécute les deux applications en parallèle

param(
    [string]$Mode = "dev",  # dev ou prod
    [switch]$Docker = $false,
    [switch]$OpenBrowser = $true
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Get-Location

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🔧 Système de Diagnostic Frigorifique - Démarrage    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Fonction pour vérifier Python
function Test-PythonInstalled {
    try {
        $version = python --version 2>&1
        Write-Host "✓ Python trouvé: $version" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Python n'est pas installé!" -ForegroundColor Red
        return $false
    }
}

# Fonction pour installer les dépendances
function Install-Dependencies {
    param([string]$Path, [string]$Name)
    
    Write-Host "`n📦 Installation des dépendances pour $Name..." -ForegroundColor Yellow
    
    if (Test-Path "$Path\requirements.txt") {
        Set-Location $Path
        pip install -r requirements.txt
        Set-Location $WorkspaceRoot
        Write-Host "✓ $Name dépendances installées" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Fichier requirements.txt non trouvé dans $Path" -ForegroundColor Red
    }
}

# Fonction pour initialiser la BD
function Initialize-Database {
    param([string]$Path, [string]$Name)
    
    Write-Host "`n🗄️  Initialisation de la base de données $Name..." -ForegroundColor Yellow
    
    if (Test-Path "$Path\init_db.py") {
        Set-Location $Path
        python init_db.py
        Set-Location $WorkspaceRoot
        Write-Host "✓ Base de données $Name initialisée" -ForegroundColor Green
    }
}

# Vérifier Python
if (-not (Test-PythonInstalled)) {
    exit 1
}

# Mode Docker
if ($Docker) {
    Write-Host "`n🐳 Démarrage avec Docker Compose..." -ForegroundColor Cyan
    docker-compose up
    exit
}

# Mode Développement
Write-Host "`n📋 Mode: $($Mode.ToUpper())" -ForegroundColor Cyan

# Vérifier les fichiers .env
Write-Host "`n🔐 Vérification des fichiers .env..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "ℹ Création .env depuis .env.example (racine)" -ForegroundColor Gray
        Copy-Item ".env.example" ".env"
        Write-Host "⚠️  IMPORTANT: Édite .env avec tes clés API" -ForegroundColor Yellow
    }
}

if (-not (Test-Path "chat\.env")) {
    if (Test-Path "chat\.env.example") {
        Write-Host "ℹ Création chat\.env depuis .env.example" -ForegroundColor Gray
        Copy-Item "chat\.env.example" "chat\.env"
        Write-Host "⚠️  IMPORTANT: Édite chat\.env avec ta configuration" -ForegroundColor Yellow
    }
}

# Installation des dépendances
Write-Host "`n📦 Installation des dépendances..." -ForegroundColor Cyan
Install-Dependencies $WorkspaceRoot "Application Principale"
Install-Dependencies "$WorkspaceRoot\chat" "Chat Web"

# Initialisation des bases de données
Write-Host "`n🗄️  Initialisation des bases de données..." -ForegroundColor Cyan
if (Test-Path "init_data.py") {
    Write-Host "Initialisation app principale..." -ForegroundColor Yellow
    python init_data.py
}
Initialize-Database "$WorkspaceRoot\chat" "Chat Web"

# Démarrage des applications
Write-Host "`n🚀 Démarrage des applications..." -ForegroundColor Cyan
Write-Host "   • App Principale: http://localhost:5000" -ForegroundColor Blue
Write-Host "   • Chat Web: http://localhost:5001" -ForegroundColor Blue
Write-Host "`n" -ForegroundColor Cyan

# Ouvrir les navigateurs
if ($OpenBrowser) {
    Start-Sleep -Seconds 2
    Write-Host "🌐 Ouverture des applications dans le navigateur..." -ForegroundColor Cyan
    Start-Process "http://localhost:5001"
}

# Démarrer les applications dans des nouvelles fenêtres
Write-Host "`n📌 Application Principale en cours de démarrage..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot'; python app.py" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "📌 Chat Web en cours de démarrage..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot\chat'; python app_web.py" -WindowStyle Normal

Write-Host "`n✓ Les deux applications démarrent dans des fenêtres séparées" -ForegroundColor Green
Write-Host "`n💡 Conseil: Pour arrêter les applications, ferme les fenêtres ou utilise Ctrl+C`n" -ForegroundColor Gray
