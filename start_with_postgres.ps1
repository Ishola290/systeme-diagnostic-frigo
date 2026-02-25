# Script de démarrage avec PostgreSQL configuré
# Usage: .\start_with_postgres.ps1

# Définir DATABASE_URL avec SSL
$env:DATABASE_URL = "postgresql://n8ndb_440v_user:Nk1gYjZmHVpcCmFo5rGDIQnfTwJhZpu8@dpg-d6dlg4i4d50c73atk5hg-a.frankfurt-postgres.render.com/n8ndb_440v"

Write-Host "✅ DATABASE_URL configuré" -ForegroundColor Green
Write-Host "📡 Test de connexion PostgreSQL..." -ForegroundColor Yellow

# Tester la connexion
python test_postgres.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 PostgreSQL est opérationnel!" -ForegroundColor Green
    Write-Host "`n💡 Prochaines étapes:" -ForegroundColor Cyan
    Write-Host "   1. Démarrer l'app principale: python app.py"
    Write-Host "   2. Démarrer le service IA: cd gpt; python ia_service.py"
    Write-Host "   3. Tester avec le simulateur: Invoke-RestMethod -Uri 'http://localhost:5000/api/simulator/start' ..."
} else {
    Write-Host "`n❌ Échec de connexion PostgreSQL" -ForegroundColor Red
}
