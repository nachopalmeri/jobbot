"""
End-to-end acceptance smoke for a new JobBot user.

This script exercises the public API only, plus a local database handoff to
simulate the Telegram link consumption path used by the bot.

Usage:
  python scripts/load/acceptance_smoke.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import os
import random
import string
import tempfile
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict
from urllib import error, parse, request

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from job_bot.database import Database


def _rand_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _rand_email(prefix: str = "acceptance") -> str:
    return f"{prefix}_{_rand_string(12)}@example.com"


def _rand_telegram_user_id() -> int:
    return random.randint(700_000_000, 799_999_999)


def _http_json(method: str, url: str, payload: Dict[str, Any] | None = None, token: str | None = None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, method=method.upper())
    if payload is not None and method.upper() != "GET":
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = raw
            return resp.status, parsed, dict(resp.headers)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return exc.code, parsed, dict(exc.headers)
    except Exception as exc:
        return -1, str(exc), {}


def _http_form(url: str, form: Dict[str, str], token: str | None = None):
    body = parse.urlencode(form).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = raw
            return resp.status, parsed, dict(resp.headers)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return exc.code, parsed, dict(exc.headers)
    except Exception as exc:
        return -1, str(exc), {}


def _http_multipart(url: str, field_name: str, filename: str, content: bytes, token: str):
    boundary = f"----JobBotBoundary{_rand_string(16)}"
    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"),
        b"Content-Type: text/plain\r\n\r\n",
        content,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    req = request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = raw
            return resp.status, parsed, dict(resp.headers)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return exc.code, parsed, dict(exc.headers)
    except Exception as exc:
        return -1, str(exc), {}


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    repro: str
    response: Any | None = None


def record(results: list[CheckResult], name: str, status: str, detail: str, repro: str, response: Any | None = None):
    results.append(CheckResult(name=name, status=status, detail=detail, repro=repro, response=response))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--password", default="Acceptance123!")
    parser.add_argument("--telegram-user-id", type=int, default=_rand_telegram_user_id())
    parser.add_argument("--db-path", default="job_bot.db")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    results: list[CheckResult] = []

    email = _rand_email()
    name = "Acceptance User"

    status, health, _ = _http_json("GET", f"{base}/health")
    record(
        results,
        "health",
        "PASS" if status == 200 else "FAIL",
        f"GET /health returned {status}",
        f"curl -i {base}/health",
        health,
    )

    register_status, register_body, _ = _http_json(
        "POST",
        f"{base}/auth/register",
        {"email": email, "password": args.password, "name": name},
    )
    token = register_body.get("access_token") if isinstance(register_body, dict) else ""
    telegram_id = register_body.get("telegram_id") if isinstance(register_body, dict) else None
    record(
        results,
        "register",
        "PASS" if register_status == 200 and token else "FAIL",
        f"register status={register_status}, token={bool(token)}",
        f'curl -i -X POST {base}/auth/register -H "Content-Type: application/json" -d "{{\\"email\\":\\"{email}\\",\\"password\\":\\"{args.password}\\",\\"name\\":\\"{name}\\"}}"',
        register_body,
    )

    login_status, login_body, _ = _http_form(
        f"{base}/auth/token",
        {"username": email, "password": args.password},
    )
    login_token = login_body.get("access_token") if isinstance(login_body, dict) else ""
    record(
        results,
        "login",
        "PASS" if login_status == 200 and login_token else "FAIL",
        f"login status={login_status}, token={bool(login_token)}",
        f'curl -i -X POST {base}/auth/token -H "Content-Type: application/x-www-form-urlencoded" -d "username={email}&password={args.password}"',
        login_body,
    )

    auth_token = login_token or token
    if not auth_token:
        print(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False))
        return

    prefs_payload = {
        "experience_level": "junior",
        "role_type": "backend developer",
        "technologies": "python, fastapi, sql",
        "job_modality": "remoto",
        "max_job_age_days": 21,
        "match_threshold": 72,
        "alert_channel": "telegram",
        "check_interval_hours": 6,
        "alert_start_hour": 8,
        "alert_end_hour": 22,
        "timezone": "America/Buenos_Aires",
        "weekly_goal": 12,
        "digest_mode": "realtime",
        "active_alerts": True,
        "blocked_companies": "Acme",
        "preferred_companies": "JobBot Labs",
    }
    pref_status, pref_body, _ = _http_json("POST", f"{base}/users/preferences", prefs_payload, auth_token)
    record(
        results,
        "config_persistence_set",
        "PASS" if pref_status == 200 else "FAIL",
        f"POST /users/preferences returned {pref_status}",
        f'curl -i -X POST {base}/users/preferences -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "...preferences..."',
        pref_body,
    )

    get_pref_status, get_pref_body, _ = _http_json("GET", f"{base}/users/preferences", token=auth_token)
    persisted = isinstance(get_pref_body, dict) and get_pref_body.get("role_type") == prefs_payload["role_type"]
    record(
        results,
        "config_persistence_get",
        "PASS" if get_pref_status == 200 and persisted else "FAIL",
        f"GET /users/preferences returned {get_pref_status}, persisted={persisted}",
        f"curl -i {base}/users/preferences -H \"Authorization: Bearer $TOKEN\"",
        get_pref_body,
    )

    dash_status, dash_body, _ = _http_json("GET", f"{base}/users/dashboard", token=auth_token)
    dash_ok = isinstance(dash_body, dict) and all(
        key in dash_body
        for key in ["daily_motivation", "application_streak", "weekly_goal", "weekly_remaining", "cv_insights", "coaching_tips"]
    )
    record(
        results,
        "dashboard_load",
        "PASS" if dash_status == 200 and dash_ok else "FAIL",
        f"GET /users/dashboard returned {dash_status}, payload_ok={dash_ok}",
        f"curl -i {base}/users/dashboard -H \"Authorization: Bearer $TOKEN\"",
        dash_body,
    )

    with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".txt") as tmp:
        tmp.write(
            b"Nombre: Acceptance User\n"
            b"Stack: Python, FastAPI, SQL, React\n"
            b"Experiencia: He trabajado con APIs, dashboards y automatizacion.\n"
        )
        tmp_path = tmp.name

    upload_status, upload_body, _ = _http_multipart(f"{base}/cv/upload", "file", Path(tmp_path).name, Path(tmp_path).read_bytes(), auth_token)
    try:
        os.remove(tmp_path)
    except Exception:
        pass
    record(
        results,
        "cv_upload",
        "PASS" if upload_status == 200 else "FAIL",
        f"POST /cv/upload returned {upload_status}",
        f'curl -i -X POST {base}/cv/upload -H "Authorization: Bearer $TOKEN" -F "file=@cv.txt"',
        upload_body,
    )

    dash2_status, dash2_body, _ = _http_json("GET", f"{base}/users/dashboard", token=auth_token)
    cv_uploaded = isinstance(dash2_body, dict) and dash2_body.get("cv_insights", {}).get("uploaded") is True
    cv_score_present = isinstance(dash2_body, dict) and dash2_body.get("cv_insights", {}).get("score") is not None
    record(
        results,
        "cv_insights_refresh",
        "PASS" if dash2_status == 200 and cv_uploaded and cv_score_present else "FAIL",
        f"dashboard after upload status={dash2_status}, uploaded={cv_uploaded}, score_present={cv_score_present}",
        f"curl -i {base}/users/dashboard -H \"Authorization: Bearer $TOKEN\"",
        dash2_body,
    )

    preview_status, preview_body, _ = _http_json("GET", f"{base}/jobs/dashboard-preview", token=auth_token)
    preview_ok = isinstance(preview_body, dict) and len(preview_body.get("jobs") or []) > 0
    record(
        results,
        "matches_preview",
        "PASS" if preview_status == 200 and preview_ok else "FAIL",
        f"GET /jobs/dashboard-preview returned {preview_status}, jobs_count={(len(preview_body.get('jobs') or []) if isinstance(preview_body, dict) else 'n/a')}",
        f"curl -i {base}/jobs/dashboard-preview -H \"Authorization: Bearer $TOKEN\"",
        preview_body,
    )

    tips_status, tips_body, _ = _http_json("GET", f"{base}/cv/tips/demo-job", token=auth_token)
    tips_ok = isinstance(tips_body, dict) and len(tips_body.get("tips") or []) > 0
    record(
        results,
        "tips",
        "PASS" if tips_status == 200 and tips_ok else "FAIL",
        f"GET /cv/tips/demo-job returned {tips_status}, tips_count={(len(tips_body.get('tips') or []) if isinstance(tips_body, dict) else 'n/a')}",
        f"curl -i {base}/cv/tips/demo-job -H \"Authorization: Bearer $TOKEN\"",
        tips_body,
    )

    status_status, status_body, _ = _http_json("GET", f"{base}/subscriptions/status", token=auth_token)
    plans_status, plans_body, _ = _http_json("GET", f"{base}/subscriptions/plans")
    record(
        results,
        "subscription_status",
        "PASS" if status_status == 200 and isinstance(status_body, dict) else "FAIL",
        f"GET /subscriptions/status returned {status_status}",
        f"curl -i {base}/subscriptions/status -H \"Authorization: Bearer $TOKEN\"",
        status_body,
    )
    record(
        results,
        "subscription_plans",
        "PASS" if plans_status == 200 and isinstance(plans_body, dict) and len(plans_body.get("plans") or []) >= 4 else "FAIL",
        f"GET /subscriptions/plans returned {plans_status}",
        f"curl -i {base}/subscriptions/plans",
        plans_body,
    )

    mock_status, mock_body, _ = _http_json(
        "POST",
        f"{base}/cv/mock-interview?job_title=Backend%20Developer",
        token=auth_token,
    )
    record(
        results,
        "subscription_gating_mock_interview",
        "PASS" if mock_status == 403 else "FAIL",
        f"POST /cv/mock-interview returned {mock_status} (expected 403 for free plan)",
        f'curl -i -X POST "{base}/cv/mock-interview?job_title=Backend%20Developer" -H "Authorization: Bearer $TOKEN"',
        mock_body,
    )

    track_status, track_body, _ = _http_json(
        "POST",
        f"{base}/jobs/track",
        {"job_title": "Backend Developer", "company": "Example Co", "url": "https://example.com/job"},
        auth_token,
    )
    record(
        results,
        "subscription_gating_track",
        "PASS" if track_status == 403 else "FAIL",
        f"POST /jobs/track returned {track_status} (expected 403 for free plan)",
        f'curl -i -X POST {base}/jobs/track -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "...job..."',
        track_body,
    )

    link_status, link_body, _ = _http_json("POST", f"{base}/auth/telegram/link-code", token=auth_token)
    link_code = link_body.get("code") if isinstance(link_body, dict) else None
    link_deep_link = link_body.get("deep_link") if isinstance(link_body, dict) else None
    record(
        results,
        "telegram_code_generation",
        "PASS" if link_status == 200 and link_code and link_deep_link else "FAIL",
        f"POST /auth/telegram/link-code returned {link_status}, code={bool(link_code)}, deeplink={bool(link_deep_link)}",
        f'curl -i -X POST {base}/auth/telegram/link-code -H "Authorization: Bearer $TOKEN"',
        link_body,
    )

    link_simulated = False
    link_status_detail = "not attempted"
    if link_code:
        db = Database(db_path=args.db_path)
        try:
            record_row = db.consume_telegram_link_code(link_code)
            if record_row:
                db.link_web_account_to_telegram(
                    int(record_row["web_telegram_id"]),
                    args.telegram_user_id,
                    "Telegram Acceptance",
                )
                link_simulated = True
                link_status_detail = f"linked web_id={record_row['web_telegram_id']} to telegram_id={args.telegram_user_id}"
        finally:
            db.close()

    if link_simulated:
        linked_status, linked_body, _ = _http_json("GET", f"{base}/users/dashboard", token=auth_token)
        linked_ok = (
            isinstance(linked_body, dict)
            and linked_body.get("has_telegram_link") is True
            and int(linked_body.get("telegram_id") or 0) > 0
        )
        record(
            results,
            "telegram_linking",
            "PASS" if linked_status == 200 and linked_ok else "FAIL",
            f"linked_status={linked_status}, detail={link_status_detail}, linked_ok={linked_ok}",
            f"curl -i {base}/users/dashboard -H \"Authorization: Bearer $TOKEN\"",
            linked_body,
        )
    else:
        record(
            results,
            "telegram_linking",
            "FAIL",
            "Could not simulate Telegram link consumption in local DB",
            f"POST {base}/auth/telegram/link-code then consume code through job_bot.database.Database(...).consume_telegram_link_code()",
            {"code": link_code, "detail": link_status_detail},
        )

    print(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
