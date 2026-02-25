# Script de démarrage - Mode FICHIER (sans PostgreSQL)
# Usage: .\start_production.ps1

Write-Host "🚀 Démarrage en mode FICHIER (persistance garantie)" -ForegroundColor Green
Write-Host "📁 Les données seront sauvegardées dans: data/" -ForegroundColor Cyan
Write-Host ""

# S'assurer qu'il n'y a pas de DATABASE_URL (mode fichier)
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue

Write-Host "✅ Configuration vérifiée" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Commandes disponibles:" -ForegroundColor Yellow
Write-Host "   1. Démarrer l'app:         python app.py"
Write-Host "   2. Démarrer service IA:     cd gpt; python ia_service.py"
Write-Host "   3. Lancer simulateur:       Invoke-RestMethod -Uri 'http://localhost:5000/api/simulator/start' -Method POST -ContentType 'application/json' -Body '{\"cycles\": 5, \"interval\": 10}'"
Write-Host ""
