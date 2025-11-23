@echo off
REM Script pour démarrer l'application avec Docker Compose
REM Windows batch file

setlocal enabledelayedexpansion

title Diagnostic Frigo - Docker Compose
color 0A
cls

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  🐳 Système Diagnostic Frigo - Docker Compose         ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Vérifier Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Docker n'est pas installé!
    echo   Télécharge Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✓ Docker trouvé

REM Vérifier docker-compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Docker Compose n'est pas installé!
    pause
    exit /b 1
)
echo ✓ Docker Compose trouvé

REM Vérifier fichier .env.docker
if not exist ".env.docker" (
    echo ✗ Fichier .env.docker absent!
    echo   Crée une copie de .env.docker.example
    pause
    exit /b 1
)
echo ✓ Configuration trouvée

echo.
echo 🔨 Construction et démarrage des conteneurs...
echo.

REM Démarrer les services
docker-compose --env-file .env.docker up -d

if errorlevel 1 (
    echo ✗ Erreur lors du démarrage
    pause
    exit /b 1
)

echo.
echo ✅ Conteneurs démarrés avec succès!
echo.
echo 🌐 URLs d'accès:
echo    • App Principale: http://localhost:5000
echo    • Chat Web: http://localhost:5001
echo.
echo 📋 Commandes utiles:
echo    Voir les logs: docker-compose logs -f chat-web
echo    Arrêter: docker-compose down
echo    Redémarrer: docker-compose restart
echo.

REM Ouvrir le navigateur
timeout /t 3 /nobreak
start http://localhost:5001

echo 💡 Connexion: admin@example.com / admin123
pause
