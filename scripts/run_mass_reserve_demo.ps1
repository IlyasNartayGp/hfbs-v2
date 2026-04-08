param(
    [int]$EventId = 1,
    [int]$Count = 200,
    [int]$Concurrency = 20,
    [double]$RampSeconds = 40,
    [switch]$AllEvents,
    [string]$BaseUrl = "http://host.docker.internal:8880/api"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$reportDir = Join-Path $PSScriptRoot "reports"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportPath = Join-Path $reportDir "mass_reserve_${timestamp}.json"

New-Item -ItemType Directory -Force -Path $reportDir | Out-Null

Write-Host "Mass reserve demo"
if ($AllEvents -or $EventId -le 0) {
  Write-Host "Frontend: http://localhost:3737/events"
  Write-Host "Mode:     random seats across all events"
} else {
  Write-Host "Frontend: http://localhost:3737/events/$EventId"
  Write-Host "Mode:     target event $EventId, fallback to all events if needed"
}
Write-Host "API:      $BaseUrl"
Write-Host "Report:   $reportPath"
Write-Host ""
Write-Host "Tip: open the event page now and try to book manually while the script is running."
Write-Host ""

docker run --rm `
  -v "${root}:/mnt/hfbs-v2" `
  -w /mnt/hfbs-v2 `
  python:3.11-slim `
  python scripts/mass_reserve_seats.py `
    --base-url $BaseUrl `
    --count $Count `
    --concurrency $Concurrency `
    --ramp-seconds $RampSeconds `
    --report "scripts/reports/mass_reserve_${timestamp}.json" `
    --event-id $EventId `
    $(if ($AllEvents) { "--all-events" })

Write-Host ""
Write-Host "Mass reserve report:"
Write-Host $reportPath
