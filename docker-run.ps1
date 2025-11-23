# Script PowerShell pour démarrer Docker Compose
# Système Diagnostic Frigo

param(
    [switch]$Build = $false,
    [switch]$Down = $false,
    [switch]$Logs = $false,
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🐳 Système Diagnostic Frigo - Docker Compose         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Vérifier Docker
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker trouvé: $dockerVersion" -ForegroundColor Green
}
catch {
    Write-Host "✗ Docker n'est pas installé!" -ForegroundColor Red
    Write-Host "  Télécharge: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Vérifier docker-compose
try {
    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose trouvé: $composeVersion" -ForegroundColor Green
}
catch {
    Write-Host "✗ Docker Compose n'est pas installé!" -ForegroundColor Red
    exit 1
}

# Vérifier .env.docker
if (-not (Test-Path ".env.docker")) {
    Write-Host "✗ Fichier .env.docker absent!" -ForegroundColor Red
    if (Test-Path ".env.docker.example") {
        Copy-Item ".env.docker.example" ".env.docker"
        Write-Host "ℹ Fichier .env.docker créé - Édite-le avec tes données" -ForegroundColor Yellow
    }
}
else {
    Write-Host "✓ Configuration trouvée" -ForegroundColor Green
}

# Afficher les options
if ($Down) {
    Write-Host "`n🛑 Arrêt des conteneurs..." -ForegroundColor Yellow
    docker-compose --env-file .env.docker down
    Write-Host "✓ Conteneurs arrêtés" -ForegroundColor Green
    exit 0
}

if ($Logs) {
    Write-Host "`n📋 Affichage des logs..." -ForegroundColor Yellow
    docker-compose --env-file .env.docker logs -f chat-web
    exit 0
}

if ($Clean) {
    Write-Host "`n🧹 Nettoyage complet..." -ForegroundColor Yellow
    docker-compose --env-file .env.docker down -v
    Write-Host "✓ Nettoyage complet terminé" -ForegroundColor Green
    exit 0
}

# Démarrage normal
Write-Host "`n🔨 Construction et démarrage des conteneurs..." -ForegroundColor Yellow

if ($Build) {
    Write-Host "  (Reconstruction des images...)" -ForegroundColor Gray
    docker-compose --env-file .env.docker up -d --build
}
else {
    docker-compose --env-file .env.docker up -d
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Conteneurs démarrés avec succès!" -ForegroundColor Green
    
    Write-Host "`n🌐 URLs d'accès:" -ForegroundColor Cyan
    Write-Host "   • App Principale: http://localhost:5000" -ForegroundColor Blue
    Write-Host "   • Chat Web: http://localhost:5001" -ForegroundColor Blue
    
    Write-Host "`n📋 Commandes utiles:" -ForegroundColor Cyan
    Write-Host "   Voir les logs: .\docker-run.ps1 -Logs"
    Write-Host "   Arrêter: .\docker-run.ps1 -Down"
    Write-Host "   Nettoyer: .\docker-run.ps1 -Clean"
    Write-Host "   Reconstruire: .\docker-run.ps1 -Build"
    
    Write-Host "`n💡 Connexion:" -ForegroundColor Cyan
    Write-Host "   Email: admin@example.com" -ForegroundColor Yellow
    Write-Host "   Mot de passe: admin123" -ForegroundColor Yellow
    
    Start-Sleep -Seconds 3
    Write-Host "`n🌐 Ouverture du navigateur..." -ForegroundColor Yellow
    Start-Process "http://localhost:5001"
}
else {
    Write-Host "`n✗ Erreur lors du démarrage" -ForegroundColor Red
    exit 1
}

Write-Host "`n"
