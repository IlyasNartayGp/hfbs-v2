import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request


def cancel_booking(base_url: str, booking_id: str) -> dict:
    request = urllib.request.Request(
        f"{base_url}/bookings/{booking_id}",
        headers={"Accept": "application/json"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            return {
                "booking_id": booking_id,
                "status": "cancelled",
                "http_status": response.status,
                "body": body,
            }
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = exc.reason
        return {
            "booking_id": booking_id,
            "status": "failed",
            "http_status": exc.code,
            "error": detail,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cancel mass reserved seats using a JSON report.")
    parser.add_argument("--base-url", default="http://localhost:8880/api")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    report_path = pathlib.Path(args.report)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    reserved = report.get("reserved_seats", [])

    results = []
    for item in reserved:
        booking_id = item.get("booking_id")
        if booking_id:
            results.append(cancel_booking(args.base_url, booking_id))

    summary = {
        "requested": len(reserved),
        "cancelled": len([item for item in results if item["status"] == "cancelled"]),
        "failed": len([item for item in results if item["status"] != "cancelled"]),
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
