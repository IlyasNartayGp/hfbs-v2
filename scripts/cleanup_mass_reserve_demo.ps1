param(
    [Parameter(Mandatory = $true)]
    [string]$Report,
    [string]$BaseUrl = "http://host.docker.internal:8880/api"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

docker run --rm `
  -v "${root}:/mnt/hfbs-v2" `
  -w /mnt/hfbs-v2 `
  python:3.11-slim `
  python scripts/cleanup_mass_reserved_seats.py `
    --base-url $BaseUrl `
    --report $Report
