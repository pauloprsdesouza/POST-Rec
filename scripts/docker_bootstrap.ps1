# Bootstrap local Docker infrastructure for POST-Rec (Windows PowerShell).
# Usage:
#   .\scripts\docker_bootstrap.ps1              # infra only
#   .\scripts\docker_bootstrap.ps1 -FullStack   # infra + api + worker + web

param(
    [switch]$FullStack
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".env")) {
    if ($FullStack -and (Test-Path ".env.docker.example")) {
        Copy-Item ".env.docker.example" ".env"
        Write-Host "Created .env from .env.docker.example — add GEMINI_API_KEY before production runs."
    } elseif (Test-Path ".env.local.infra.example") {
        Copy-Item ".env.local.infra.example" ".env"
        Write-Host "Created .env from .env.local.infra.example — add GEMINI_API_KEY as needed."
    }
}

Write-Host "Starting POST-Rec Docker infrastructure..."
docker compose up -d postgres redis rabbitmq minio minio-init evolution-postgres evolution-redis evolution-api evolution-manager

Write-Host "Waiting for PostgreSQL..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    docker compose exec -T postgres pg_isready -U postrec -d postrec 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    Write-Error "PostgreSQL did not become ready in time."
}

Write-Host "Running database migrations..."
docker compose run --rm migrate

Write-Host "Ensuring Evolution WhatsApp instance..."
docker compose run --rm evolution-init

Write-Host ""
Write-Host "Infrastructure ready:"
Write-Host "  PostgreSQL (pgvector)  localhost:5432  postrec / postrec"
Write-Host "  Redis                  localhost:6379"
Write-Host "  RabbitMQ               localhost:5672  postrec / postrec"
Write-Host "  RabbitMQ management    http://localhost:15672"
Write-Host "  MinIO API              localhost:9000  minioadmin / minioadmin"
Write-Host "  MinIO console          http://localhost:9001"
Write-Host "  Evolution API          http://localhost:8080  (apikey: dev-evolution-api-key)"
Write-Host "  Evolution Manager      http://localhost:3000  (scan QR for instance postrec)"

if ($FullStack) {
    Write-Host ""
    Write-Host "Starting application services..."
    docker compose up --build -d api worker web
    Write-Host "  API       http://localhost:8000"
    Write-Host "  Web UI    http://localhost:5173"
    Write-Host "  API docs  http://localhost:8000/docs"
    Write-Host ""
    Write-Host "Verifying stack..."
    docker compose exec -T api python scripts/verify_stack.py
    docker compose exec -T worker celery -A apps.api.workers.celery_app inspect ping
} else {
    Write-Host ""
    Write-Host "Run the app on the host:"
    Write-Host "  uvicorn apps.api.main:app --reload --port 8000"
    Write-Host "  celery -A apps.api.workers.celery_app worker --loglevel=INFO"
    Write-Host "  cd apps/web; npm run dev"
}
