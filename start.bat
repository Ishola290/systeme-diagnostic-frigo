@echo off
REM Script de démarrage - Système Diagnostic Frigo
REM Démarre les deux applications en parallèle

title Diagnostic Frigo - Startup
color 0A
cls

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  🔧 Système de Diagnostic Frigorifique - Démarrage    ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python n'est pas installé!
    pause
    exit /b 1
)
echo ✓ Python trouvé

REM Vérifier fichiers .env
if not exist ".env" (
    echo ℹ Création .env depuis .env.example
    copy .env.example .env
    echo ⚠️  IMPORTANT: Édite .env avec tes clés API
)

if not exist "chat\.env" (
    echo ℹ Création chat\.env depuis .env.example
    copy chat\.env.example chat\.env
    echo ⚠️  IMPORTANT: Édite chat\.env avec ta configuration
)

echo.
echo 📦 Installation des dépendances...
pip install -r requirements.txt >nul 2>&1
cd chat
pip install -r requirements.txt >nul 2>&1
cd ..

echo.
echo 🗄️  Initialisation des bases de données...
if exist "init_data.py" python init_data.py
cd chat
if exist "init_db.py" python init_db.py
cd ..

echo.
echo 🚀 Démarrage des applications...
echo    • App Principale: http://localhost:5000
echo    • Chat Web: http://localhost:5001
echo.

REM Démarrer les applications
start "App Principale" cmd /k "cd /d %CD% && python app.py"
timeout /t 3 /nobreak
start "Chat Web" cmd /k "cd /d %CD%\chat && python app_web.py"

echo.
echo ✓ Les applications démarrent dans des fenêtres séparées
echo 💡 Pour arrêter: fermez les fenêtres ou utilisez Ctrl+C
echo.

REM Ouvrir navigateur
timeout /t 2 /nobreak
start http://localhost:5001

pause
