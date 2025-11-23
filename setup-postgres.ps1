param(
    [string]$Action = "setup",
    [string]$DbPassword = "frigo_secure_pass_change_me",
    [string]$DbUser = "frigo_user",
    [string]$DbName = "chat_app"
)

function Setup-Postgres {
    Write-Host "Starting PostgreSQL Docker container..."
    
    # Stop existing container
    docker stop frigo-postgres 2>$null | Out-Null
    docker rm frigo-postgres 2>$null | Out-Null
    
    # Create volume
    docker volume create frigo-postgres-data 2>$null | Out-Null
    
    # Run PostgreSQL
    Write-Host "Launching PostgreSQL 16..."
    docker run --name frigo-postgres `
        -e POSTGRES_USER=$DbUser `
        -e POSTGRES_PASSWORD=$DbPassword `
        -e POSTGRES_DB=$DbName `
        -p 5432:5432 `
        -v frigo-postgres-data:/var/lib/postgresql/data `
        -d postgres:16-alpine
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to start container" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Green
    Start-Sleep -Seconds 5
    
    # Wait for database to be ready
    $attempts = 0
    while ($attempts -lt 12) {
        docker exec frigo-postgres pg_isready -U $DbUser > $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "PostgreSQL is ready!" -ForegroundColor Green
            break
        }
        $attempts++
        Start-Sleep -Seconds 5
    }
    
    Write-Host ""
    Write-Host "Database URL: postgresql://$DbUser`:$DbPassword@localhost:5432/$DbName" -ForegroundColor Cyan
    Write-Host ""
}

function Migrate-Database {
    Write-Host "Checking PostgreSQL status..."
    
    # Check if PostgreSQL is running
    docker ps --filter "name=frigo-postgres" --filter "status=running" -q >$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: PostgreSQL not running. Run setup first." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "PostgreSQL is running" -ForegroundColor Green
    
    # Set environment variables
    $env:DATABASE_URL = "postgresql://$DbUser`:$DbPassword@localhost:5432/$DbName"
    $env:FLASK_ENV = "development"
    
    Write-Host "Running database migration..."
    cd chat
    python migrate_to_postgres.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Migration failed" -ForegroundColor Red
        cd ..
        exit 1
    }
    
    Write-Host "Migration completed!" -ForegroundColor Green
    cd ..
}

function Check-Connection {
    Write-Host "Checking PostgreSQL connection..."
    
    $output = docker exec frigo-postgres psql -U $DbUser -d $DbName -c "SELECT 1;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Connection successful!" -ForegroundColor Green
        Write-Host $output
    } else {
        Write-Host "Connection failed!" -ForegroundColor Red
        exit 1
    }
}

function Start-PostgresContainer {
    Write-Host "Starting PostgreSQL..."
    docker start frigo-postgres
    Write-Host "PostgreSQL started" -ForegroundColor Green
}

function Stop-PostgresContainer {
    Write-Host "Stopping PostgreSQL..."
    docker stop frigo-postgres
    Write-Host "PostgreSQL stopped" -ForegroundColor Green
}

function Restart-PostgresContainer {
    Write-Host "Restarting PostgreSQL..."
    docker restart frigo-postgres
    Start-Sleep -Seconds 3
    Write-Host "PostgreSQL restarted" -ForegroundColor Green
}

# Main
switch ($Action.ToLower()) {
    "setup" { Setup-Postgres }
    "migrate" { Migrate-Database }
    "check" { Check-Connection }
    "start" { Start-PostgresContainer }
    "stop" { Stop-PostgresContainer }
    "restart" { Restart-PostgresContainer }
    default {
        Write-Host "PostgreSQL Setup Script"
        Write-Host ""
        Write-Host "Usage: .\setup-postgres.ps1 -Action <action>"
        Write-Host ""
        Write-Host "Actions:"
        Write-Host "  setup    - Create and start PostgreSQL container"
        Write-Host "  migrate  - Run database migrations"
        Write-Host "  check    - Check database connection"
        Write-Host "  start    - Start PostgreSQL container"
        Write-Host "  stop     - Stop PostgreSQL container"
        Write-Host "  restart  - Restart PostgreSQL container"
    }
}
