param(
    [string]$ComposeFile = "C:\Iliyas\diploma\hfbs-v2\docker-compose.yml",
    [switch]$RestartServices = $true
)

$ErrorActionPreference = "Stop"

$preservedBookingIds = @(
    "20000000-0000-0000-0000-000000000001",
    "20000000-0000-0000-0000-000000000002",
    "20000000-0000-0000-0000-000000000003",
    "20000000-0000-0000-0000-000000000011",
    "20000000-0000-0000-0000-000000000012",
    "20000000-0000-0000-0000-000000000013"
)

$preservedUsers = @(
    "demo@hfbs.kz",
    "loadtest@hfbs.local",
    "loadtest_fastapi@hfbs.local"
)

$quotedBookingIds = ($preservedBookingIds | ForEach-Object { "'$_'" }) -join ", "
$quotedUsers = ($preservedUsers | ForEach-Object { "'$_'" }) -join ", "

$sql = @"
DELETE FROM bookings
WHERE id::text NOT IN ($quotedBookingIds);

DELETE FROM users
WHERE email LIKE '%@hfbs.local'
  AND email NOT IN ($quotedUsers);

UPDATE events e
SET available_seats = e.total_seats - COALESCE(active_bookings.count, 0)
FROM (
    SELECT event_id, COUNT(*)::int AS count
    FROM bookings
    WHERE LOWER(status) <> 'cancelled'
    GROUP BY event_id
) AS active_bookings
WHERE e.id = active_bookings.event_id;

UPDATE events
SET available_seats = total_seats
WHERE id NOT IN (
    SELECT DISTINCT event_id
    FROM bookings
    WHERE LOWER(status) <> 'cancelled'
);
"@

$ticketSql = @"
DELETE FROM tickets_ticket
WHERE booking_id::text NOT IN ($quotedBookingIds);
"@

Write-Host "Resetting HFBS v2 test state..."

docker compose -f $ComposeFile exec -T postgres `
  psql -U hfbs -d hfbs -v ON_ERROR_STOP=1 -c $sql

docker compose -f $ComposeFile exec -T postgres `
  psql -U hfbs -d hfbs -v ON_ERROR_STOP=1 -c $ticketSql

docker compose -f $ComposeFile exec -T redis redis-cli FLUSHDB

docker compose -f $ComposeFile exec -T django `
  sh -lc "find /app/media/tickets -type f -name '*.pdf' -delete"

if ($RestartServices) {
  docker compose -f $ComposeFile restart fastapi django ticket-consumer antifrod-consumer nginx | Out-Null

  $ready = $false
  for ($attempt = 1; $attempt -le 20; $attempt++) {
    try {
      Invoke-WebRequest -Uri "http://localhost:8880/api/events/" -UseBasicParsing -TimeoutSec 5 | Out-Null
      $ready = $true
      break
    } catch {
      Start-Sleep -Seconds 2
    }
  }

  if (-not $ready) {
    throw "v2 gateway did not become ready after reset."
  }
}

Write-Host ""
Write-Host "HFBS v2 test state has been reset."
Write-Host "Preserved baseline load-test bookings: $($preservedBookingIds.Count)"
Write-Host "Preserved baseline users: $($preservedUsers -join ', ')"
Write-Host "Redis locks and anti-fraud counters: cleared"
Write-Host "Ticket PDFs: deleted"
if ($RestartServices) {
  Write-Host "Services restarted: fastapi, django, ticket-consumer, antifrod-consumer, nginx"
}
