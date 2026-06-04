# POST-Rec Celery worker (Windows + RabbitMQ 4 homelab)
Set-Location $PSScriptRoot\..

Write-Host "Starting Celery worker (solo pool, retrieval + default queues)..." -ForegroundColor Cyan
py -3 -m celery -A apps.api.workers.celery_app worker `
  --loglevel=INFO `
  --pool=solo `
  --without-mingle `
  --without-gossip `
  --queues=postrec.recommendation.default,postrec.recommendation.retrieval