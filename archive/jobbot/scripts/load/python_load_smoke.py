"""
Lightweight concurrent load smoke for JobBot API.

Usage:
  python scripts/load/python_load_smoke.py --base-url http://127.0.0.1:8000 --users 20 --iterations 2
"""

from __future__ import annotations

import argparse
import json
import random
import string
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict
from urllib import error, parse, request


def _rand_email(prefix: str = "loadpy") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{prefix}_{suffix}@example.com"


def _http_post_json(url: str, payload: Dict, headers: Dict[str, str] | None = None):
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with request.urlopen(req, timeout=12) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, data
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        return exc.code, payload
    except Exception as exc:
        return -1, str(exc)


def _http_post_form(url: str, payload: Dict[str, str], headers: Dict[str, str] | None = None):
    body = parse.urlencode(payload).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with request.urlopen(req, timeout=12) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, data
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        return exc.code, payload
    except Exception as exc:
        return -1, str(exc)


def _http_get(url: str, headers: Dict[str, str] | None = None):
    req = request.Request(url, method="GET")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with request.urlopen(req, timeout=12) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, data
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        return exc.code, payload
    except Exception as exc:
        return -1, str(exc)


def _worker(base_url: str, token: str, counters: Dict[str, int], lock: threading.Lock):
    ok = True
    auth = {"Authorization": f"Bearer {token}"}
    dash_status, _ = _http_get(f"{base_url}/users/dashboard", headers=auth)
    jobs_status, _ = _http_get(f"{base_url}/jobs/dashboard-preview", headers=auth)
    if dash_status not in (200, 429):
        ok = False
    if jobs_status not in (200, 403, 429):
        ok = False

    with lock:
        counters["total"] += 1
        counters[f"dashboard_{dash_status}"] = counters.get(f"dashboard_{dash_status}", 0) + 1
        counters[f"jobs_{jobs_status}"] = counters.get(f"jobs_{jobs_status}", 0) + 1
        if ok:
            counters["ok"] += 1
        else:
            counters["failed"] += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--password", default="LoadTest123!")
    parser.add_argument("--seed-email", default="")
    args = parser.parse_args()

    counters = {"total": 0, "ok": 0, "failed": 0}
    lock = threading.Lock()
    started = time.time()

    seed_email = args.seed_email or "loadseed_shared@example.com"
    token = ""

    login_status, login_body = _http_post_form(
        f"{args.base_url}/auth/token",
        {"username": seed_email, "password": args.password},
    )
    if login_status == 200:
        try:
            token = json.loads(login_body).get("access_token", "")
        except Exception:
            token = ""

    if not token:
        register_status, register_body = _http_post_json(
            f"{args.base_url}/auth/register",
            {"email": seed_email, "password": args.password, "name": "Load Seed User"},
        )
        if register_status != 200:
            print(
                json.dumps(
                    {
                        "error": "seed_auth_failed",
                        "login_status": login_status,
                        "register_status": register_status,
                        "register_response": register_body,
                        "email": seed_email,
                    },
                    indent=2,
                )
            )
            return
        try:
            token = json.loads(register_body).get("access_token", "")
        except Exception:
            token = ""
    if not token:
        print(json.dumps({"error": "seed_token_missing", "email": seed_email}, indent=2))
        return

    for _ in range(args.iterations):
        with ThreadPoolExecutor(max_workers=args.users) as pool:
            futures = [
                pool.submit(_worker, args.base_url, token, counters, lock)
                for _ in range(args.users)
            ]
            for _ in as_completed(futures):
                pass

    elapsed = time.time() - started
    success_rate = (counters["ok"] / counters["total"] * 100.0) if counters["total"] else 0.0
    print(
        json.dumps(
            {
                "base_url": args.base_url,
                "users": args.users,
                "iterations": args.iterations,
                "seed_email": seed_email,
                "total_requests": counters["total"],
                "ok": counters["ok"],
                "failed": counters["failed"],
                "success_rate": round(success_rate, 2),
                "elapsed_seconds": round(elapsed, 2),
                "status_summary": {
                    key: value
                    for key, value in counters.items()
                    if key.startswith("dashboard_") or key.startswith("jobs_")
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
