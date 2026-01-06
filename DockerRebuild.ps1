Write-Host ''
$dateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "=[ START $dateTime ]===========================[ DockerRebuild.ps1 ]=" -ForegroundColor Blue
Write-Host "Executing $PSCommandPath..." -ForegroundColor Yellow

& ./CreateDbSqlScript.ps1
docker compose down
#docker rm --force resultcollector
#docker rmi --force resultcollector-db
docker volume prune -f
docker compose create
docker compose start

Write-Host '-[ END DockerRebuild ]----------------------------------------------------------' -ForegroundColor Cyan
Write-Host ''
