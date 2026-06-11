from __future__ import annotations

"""
Poll running jobs and print status updates.

Usage:
    python poll_jobs.py                    # poll all running jobs
    python poll_jobs.py --project_id YOUR_PROJECT_ID   # filter by project
    python poll_jobs.py --interval 30      # check every 30 seconds
"""

import json
import os
import time
from datetime import datetime

import requests

AK = os.environ.get("BOHR_ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi/v1/job"
HEADERS = {"Authorization": f"Bearer {AK}"}


def get_jobs(status: int | None = None, project_id: int | None = None) -> list[dict]:
    """Get job list through OpenAPI."""
    params = {"page": 1, "pageSize": 20}
    if status is not None:
        params["status"] = status
    if project_id is not None:
        params["projectId"] = project_id
    try:
        result = requests.get(f"{BASE}/list", headers=HEADERS, params=params, timeout=20).json()
    except (requests.RequestException, json.JSONDecodeError):
        return []
    if result.get("code") != 0:
        return []
    data = result.get("data", {})
    return data.get("items", []) if isinstance(data, dict) else []


def format_status(status: str) -> str:
    icons = {
        "Running": "RUN",
        "Finished": "OK ",
        "Failed": "ERR",
        "Pending": "...",
        "Scheduling": "...",
        1: "RUN",
        2: "OK ",
        -1: "ERR",
        0: "...",
        3: "...",
    }
    return icons.get(status, status)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Poll Bohrium job status")
    parser.add_argument("--project_id", type=int, default=None, help="Filter by project ID")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if not AK:
        print("ERROR: set BOHR_ACCESS_KEY environment variable")
        return

    while True:
        now = datetime.now().strftime("%H:%M:%S")
        all_active = []
        for status in (1, 0, 3):  # running, pending, scheduling
            all_active.extend(get_jobs(status, args.project_id))

        if not all_active:
            print(f"[{now}] No active jobs.")
            if args.once:
                break
            time.sleep(args.interval)
            continue

        print(f"\n[{now}] Active jobs: {len(all_active)}")
        print(f"  {'ID':<12} {'Status':<6} {'Name':<30}")
        print(f"  {'-'*12} {'-'*6} {'-'*30}")
        for job in all_active:
            job_id = job.get("jobId", job.get("id", "?"))
            status = format_status(job.get("status", "?"))
            name = job.get("jobName", job.get("name", "?"))[:30]
            print(f"  {job_id:<12} {status:<6} {name}")

        if args.once:
            break

        print(f"  Next check in {args.interval}s... (Ctrl+C to stop)")
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")
            break


if __name__ == "__main__":
    main()
