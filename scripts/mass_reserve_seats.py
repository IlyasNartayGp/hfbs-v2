import argparse
import concurrent.futures
import json
import pathlib
import random
import sys
import time
import urllib.error
import urllib.request


BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def fetch_json(url: str) -> list[dict]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": BROWSER_USER_AGENT,
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def build_ip(user_index: int) -> str:
    third = ((user_index - 1) // 250) % 250
    fourth = ((user_index - 1) % 250) + 1
    return f"10.42.{third}.{fourth}"


def collect_available_seats(base_url: str, event_ids: list[int]) -> list[dict]:
    seats: list[dict] = []
    for event_id in event_ids:
        event_seats = fetch_json(f"{base_url}/events/{event_id}/seats")
        for seat in event_seats:
            if seat.get("status") != "available":
                continue
            enriched_seat = dict(seat)
            enriched_seat["event_id"] = event_id
            seats.append(enriched_seat)
    return seats


def reserve_one(
    *,
    base_url: str,
    seat: dict,
    user_index: int,
    start_time: float,
    ramp_seconds: float,
    total_count: int,
) -> dict:
    if ramp_seconds > 0 and total_count > 1:
        target_offset = ramp_seconds * ((user_index - 1) / (total_count - 1))
        sleep_for = (start_time + target_offset) - time.time()
        if sleep_for > 0:
            time.sleep(sleep_for)

    payload = {
        "event_id": seat["event_id"],
        "seat_id": seat["id"],
        "user_id": f"mass-user-{user_index:04d}",
        "user_email": f"mass-user-{user_index:04d}@hfbs.local",
    }
    request = urllib.request.Request(
        f"{base_url}/bookings/",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": BROWSER_USER_AGENT,
            "X-Forwarded-For": build_ip(user_index),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
            return {
                "user_index": user_index,
                "event_id": seat["event_id"],
                "seat_id": seat["id"],
                "seat_label": f"{seat['row']}{seat['number']}",
                "status": "reserved",
                "http_status": response.status,
                "booking_id": body.get("booking_id"),
                "message": body.get("message"),
            }
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = exc.reason
        return {
            "user_index": user_index,
            "event_id": seat["event_id"],
            "seat_id": seat["id"],
            "seat_label": f"{seat['row']}{seat['number']}",
            "status": "failed",
            "http_status": exc.code,
            "error": detail,
        }
    except Exception as exc:
        return {
            "user_index": user_index,
            "event_id": seat["event_id"],
            "seat_id": seat["id"],
            "seat_label": f"{seat['row']}{seat['number']}",
            "status": "failed",
            "http_status": None,
            "error": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reserve many seats in v2 so you can manually test booking from the frontend.",
    )
    parser.add_argument("--base-url", default="http://localhost:8880/api")
    parser.add_argument("--event-id", type=int, default=1)
    parser.add_argument("--all-events", action="store_true")
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--ramp-seconds", type=float, default=40.0)
    parser.add_argument("--report", default="")
    args = parser.parse_args()

    events = fetch_json(f"{args.base_url}/events/")
    event_ids = [int(event["id"]) for event in events]
    use_all_events = args.all_events or args.event_id <= 0
    selection_mode = "single_event"

    if use_all_events:
        target_event_ids = event_ids
        selection_mode = "all_events_random"
    else:
        target_event_ids = [args.event_id]

    available_seats = collect_available_seats(args.base_url, target_event_ids)

    if len(available_seats) < args.count:
        fallback_seats = collect_available_seats(args.base_url, event_ids)
        if len(fallback_seats) >= args.count:
            available_seats = fallback_seats
            target_event_ids = event_ids
            selection_mode = "all_events_random"
        else:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": f"Only {len(fallback_seats)} seats are available across all events, but {args.count} were requested.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1

    random.shuffle(available_seats)
    chosen_seats = available_seats[: args.count]
    start_time = time.time()

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(
                reserve_one,
                base_url=args.base_url,
                seat=seat,
                user_index=index,
                start_time=start_time,
                ramp_seconds=args.ramp_seconds,
                total_count=args.count,
            )
            for index, seat in enumerate(chosen_seats, start=1)
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda item: item["user_index"])
    reserved = [item for item in results if item["status"] == "reserved"]
    failed = [item for item in results if item["status"] != "reserved"]

    event_distribution: dict[str, int] = {}
    for item in reserved:
        key = str(item["event_id"])
        event_distribution[key] = event_distribution.get(key, 0) + 1

    report = {
        "base_url": args.base_url,
        "event_id": args.event_id,
        "event_ids_used": target_event_ids,
        "selection_mode": selection_mode,
        "requested_count": args.count,
        "concurrency": args.concurrency,
        "ramp_seconds": args.ramp_seconds,
        "reserved_count": len(reserved),
        "failed_count": len(failed),
        "event_distribution": event_distribution,
        "reserved_seats": reserved,
        "failed_seats": failed,
    }

    if args.report:
        report_path = pathlib.Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
