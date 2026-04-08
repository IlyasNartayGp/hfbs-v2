param(
    [int]$Count = 500,
    [int]$Concurrency = 50,
    [double]$RampSeconds = 20,
    [string]$BaseUrl = "http://host.docker.internal:8880/api"
)

$ErrorActionPreference = "Stop"

$runner = Join-Path $PSScriptRoot "run_mass_reserve_demo.ps1"

Write-Host "Heavy mass reserve demo"
Write-Host "Frontend: http://localhost:3737/events"
Write-Host "Mode:     random seats across all events"
Write-Host "Count:    $Count"
Write-Host "Workers:  $Concurrency"
Write-Host "Ramp:     $RampSeconds sec"
Write-Host ""

& $runner `
  -AllEvents `
  -Count $Count `
  -Concurrency $Concurrency `
  -RampSeconds $RampSeconds `
  -BaseUrl $BaseUrl
