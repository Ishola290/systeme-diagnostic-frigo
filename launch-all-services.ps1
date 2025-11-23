# Launch All Services for Local Testing
# Démarre: App, Chat, IA Service, Simulateur

param(
    [switch]$Docker,
    [switch]$Python,
    [switch]$Simulator,
    [int]$SimulatorInterval = 30,
    [float]$PanneProb = 0.1,
    [switch]$NoSimulator,
    [switch]$ShowLogs
)

if (-not $Docker -and -not $Python) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║     🚀 Lanceur Services Local - Frigo Diagnostic              ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\launch-all-services.ps1 -Docker              # Via Docker Compose" -ForegroundColor Green
    Write-Host "  .\launch-all-services.ps1 -Python             # Via Python Scripts" -ForegroundColor Green
    Write-Host "  .\launch-all-services.ps1 -Python -Simulator  # + Simulateur" -ForegroundColor Green
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -NoSimulator          Lancer sans le simulateur"
    Write-Host "  -SimulatorInterval    Intervalle en secondes (default: 30)"
    Write-Host "  -PanneProb            Probabilité panne 0.0-1.0 (default: 0.1)"
    Write-Host "  -ShowLogs             Afficher logs détaillés"
    Write-Host ""
    exit 1
}

# ============================================================
# MODE 1: DOCKER COMPOSE
# ============================================================

if ($Docker) {
    Write-Host ""
    Write-Host "🐳 Lancement via Docker Compose..." -ForegroundColor Cyan
    Write-Host ""
    
    # Vérifier docker-compose
    if (-not (Test-Path "docker-compose.yml")) {
        Write-Host "❌ Erreur: docker-compose.yml non trouvé" -ForegroundColor Red
        exit 1
    }
    
    # Lancer Docker
    Write-Host "▶️  Démarrage services..." -ForegroundColor Green
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erreur Docker" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "⏳ Attendez 10 secondes pour le démarrage..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Afficher statut
    Write-Host ""
    Write-Host "📊 Statut Services:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "🌐 URLs Locales:" -ForegroundColor Cyan
    Write-Host "   App  → http://localhost:5000" -ForegroundColor Green
    Write-Host "   Chat → http://localhost:5001" -ForegroundColor Green
    Write-Host "   IA   → http://localhost:5002" -ForegroundColor Green
    
    # Lancer simulateur si demandé
    if ($Simulator -and -not $NoSimulator) {
        Write-Host ""
        Write-Host "⏳ Attendez 5 secondes avant simulateur..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        Write-Host "▶️  Démarrage simulateur..." -ForegroundColor Green
        $pythonArgs = @(
            "simulateur_production.py"
            "--interval", $SimulatorInterval
            "--prob-panne", $PanneProb
        )
        
        & python @pythonArgs
    } else {
        Write-Host ""
        Write-Host "✅ Services lancés!" -ForegroundColor Green
        Write-Host "   Lancez le simulateur: python simulateur_production.py" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Pour arrêter: docker-compose down" -ForegroundColor Gray
        Write-Host ""
        
        # Garder la fenêtre ouverte
        Read-Host "Appuyez sur Entrée pour arrêter les services"
        docker-compose down
    }
}

# ============================================================
# MODE 2: PYTHON SCRIPTS
# ============================================================

elseif ($Python) {
    Write-Host ""
    Write-Host "🐍 Lancement via Python Scripts..." -ForegroundColor Cyan
    Write-Host ""
    
    # Vérifier les fichiers
    $required_files = @("app.py", "chat/app_web.py", "gpt/app_ia.py")
    foreach ($file in $required_files) {
        if (-not (Test-Path $file)) {
            Write-Host "❌ Erreur: $file non trouvé" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "⚠️  ATTENTION: Ce mode nécessite 4 terminaux" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ouvrez 4 terminaux PowerShell et exécutez:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Terminal 1 (App Service):"
    Write-Host "  cd '$($PWD.Path)'" -ForegroundColor Cyan
    Write-Host "  python app.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Terminal 2 (Chat Service):"
    Write-Host "  cd '$($PWD.Path)'" -ForegroundColor Cyan
    Write-Host "  cd chat" -ForegroundColor Cyan
    Write-Host "  python app_web.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Terminal 3 (IA Service):"
    Write-Host "  cd '$($PWD.Path)'" -ForegroundColor Cyan
    Write-Host "  cd gpt" -ForegroundColor Cyan
    Write-Host "  python app_ia.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Terminal 4 (Simulateur):"
    Write-Host "  cd '$($PWD.Path)'" -ForegroundColor Cyan
    Write-Host "  python simulateur_production.py" -ForegroundColor Cyan
    Write-Host ""
    
    # Option: lancer App automatiquement
    if ([System.Environment]::OSVersion.Platform -eq "Win32NT") {
        Write-Host "💡 Alternative: Voulez-vous que je lance les services automatiquement?" -ForegroundColor Magenta
        Write-Host "   (Cette option créera 4 fenêtres PowerShell)" -ForegroundColor Gray
        $choice = Read-Host "Lancer automatiquement? (o/n)"
        
        if ($choice -eq 'o' -or $choice -eq 'O' -or $choice -eq 'oui') {
            Write-Host ""
            Write-Host "▶️  Lancement automatique..." -ForegroundColor Green
            
            # Terminal 1: App
            $scriptDir = $PSScriptRoot
            Start-Process powershell -ArgumentList "cd '$scriptDir'; python app.py" -WindowStyle Normal
            Write-Host "   ✅ Terminal 1: App lancé" -ForegroundColor Green
            
            Start-Sleep -Seconds 2
            
            # Terminal 2: Chat
            Start-Process powershell -ArgumentList "cd '$scriptDir'; cd chat; python app_web.py" -WindowStyle Normal
            Write-Host "   ✅ Terminal 2: Chat lancé" -ForegroundColor Green
            
            Start-Sleep -Seconds 2
            
            # Terminal 3: IA
            Start-Process powershell -ArgumentList "cd '$scriptDir'; cd gpt; python app_ia.py" -WindowStyle Normal
            Write-Host "   ✅ Terminal 3: IA lancé" -ForegroundColor Green
            
            Start-Sleep -Seconds 3
            
            # Terminal 4: Simulateur (optionnel)
            if (-not $NoSimulator) {
                $simArgs = "cd '$scriptDir'; python simulateur_production.py --interval $SimulatorInterval --prob-panne $PanneProb"
                if ($Simulator) {
                    Start-Process powershell -ArgumentList $simArgs -WindowStyle Normal
                    Write-Host "   ✅ Terminal 4: Simulateur lancé" -ForegroundColor Green
                }
            }
            
            Write-Host ""
            Write-Host "✅ Tous les services lancés!" -ForegroundColor Green
            Write-Host ""
            Write-Host "🌐 URLs Locales:" -ForegroundColor Cyan
            Write-Host "   App  → http://localhost:5000" -ForegroundColor Green
            Write-Host "   Chat → http://localhost:5001" -ForegroundColor Green
            Write-Host "   IA   → http://localhost:5002" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│                                                                │" -ForegroundColor Cyan
Write-Host "│  ✅ Configuration Complète                                    │" -ForegroundColor Cyan
Write-Host "│                                                                │" -ForegroundColor Cyan
Write-Host "│  Pour tester la communication:                                │" -ForegroundColor Cyan
Write-Host "│  python test_service_communication.py                         │" -ForegroundColor Cyan
Write-Host "│                                                                │" -ForegroundColor Cyan
Write-Host "│  Pour voir les logs:                                          │" -ForegroundColor Cyan
Write-Host "│  docker-compose logs -f  (Mode Docker)                        │" -ForegroundColor Cyan
Write-Host "│                                                                │" -ForegroundColor Cyan
Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
