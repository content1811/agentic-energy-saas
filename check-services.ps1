Write-Host "剥 Checking service health..." -ForegroundColor Cyan

$services = @(
    @{name="postgres"; port=5432},
    @{name="redis"; port=6379},
    @{name="mosquitto"; port=1883},
    @{name="nats"; port=4222},
    @{name="qdrant"; port=6333}
)

$allHealthy = $true

foreach ($service in $services) {
    $connection = Test-NetConnection -ComputerName localhost -Port $service.port -WarningAction SilentlyContinue
    
    if ($connection.TcpTestSucceeded) {
        Write-Host "笨・$($service.name) is healthy (port $($service.port))" -ForegroundColor Green
    } else {
        Write-Host "笶・$($service.name) is not responding (port $($service.port))" -ForegroundColor Red
        $allHealthy = $false
    }
}

Write-Host ""
if ($allHealthy) {
    Write-Host "脂 All services are healthy!" -ForegroundColor Green
} else {
    Write-Host "笞・・ Some services are not healthy. Check docker-compose logs." -ForegroundColor Yellow
}
