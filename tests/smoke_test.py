#!/usr/bin/env python3
"""
Smoke-test every Bohrium skill's primary endpoint against open.bohrium.com.

Usage:
    export BOHR_ACCESS_KEY="..."
    python3 tests/smoke_test.py

Exits with non-zero if any required-endpoint test fails.
Skills that depend on external services (sandbox/E2B, viking) are skipped with
an explanation; they are documented but not part of the open.bohrium.com surface.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import urllib.request
import urllib.parse
import urllib.error


BASE = os.environ.get("BOHR_API_BASE_URL", "https://open.bohrium.com/openapi")
AK = os.environ.get("BOHR_ACCESS_KEY", "")
TIMEOUT = 60


if not AK:
    print("ERROR: set BOHR_ACCESS_KEY in env", file=sys.stderr)
    sys.exit(2)


@dataclass
class Result:
    skill: str
    endpoint: str
    status: str     # PASS / FAIL / SKIP
    code: int | None
    note: str = ""


def http(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    body: dict | None = None,
) -> tuple[int, dict]:
    url = BASE + path
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    data: bytes | None = None
    headers = {"accessKey": AK}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, {"_raw": raw[:200]}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            body_json = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body_json = {"_raw": raw[:200]}
        return e.code, body_json
    except urllib.error.URLError as e:
        return 0, {"_err": str(e.reason)}
    except Exception as e:  # noqa: BLE001
        return 0, {"_err": repr(e)}


def _msg(data: dict) -> str:
    for k in ("message", "error", "_raw"):
        v = data.get(k) if isinstance(data, dict) else None
        if v:
            return str(v)[:80]
    return ""


def classify(code: int, data: dict) -> tuple[str, str]:
    """Decide PASS/FAIL and build a note.

    Any 2xx counts as pass. 401/403 counts as FAIL (auth broken). 404 / 400
    usually means wrong endpoint / wrong params. 5xx = server side.
    """
    api_code = data.get("code") if isinstance(data, dict) else None
    if 200 <= code < 300:
        # Some endpoints return {"code": <non-zero>} on error inside a 200 body
        if api_code not in (None, 0, 200, "0"):
            return "FAIL", f"HTTP 200 but body code={api_code} msg={_msg(data)}"
        return "PASS", ""
    if code == 0:
        return "FAIL", data.get("_err", "network error") if isinstance(data, dict) else "network error"
    return "FAIL", f"msg={_msg(data)}"


results: list[Result] = []


def record(
    skill: str,
    endpoint: str,
    method: str,
    *,
    params: dict | None = None,
    body: dict | None = None,
    note_on_pass: str = "",
) -> None:
    code, data = http(method, endpoint, params=params, body=body)
    status, note = classify(code, data)
    if status == "PASS" and note_on_pass:
        note = note_on_pass
    results.append(Result(skill, endpoint, status, code, note))
    print(f"  [{status}] {method:<4} {endpoint}  HTTP={code}  {note}")


def skip(skill: str, endpoint: str, reason: str) -> None:
    results.append(Result(skill, endpoint, "SKIP", None, reason))
    print(f"  [SKIP] {endpoint}  {reason}")


# ---------------------------------------------------------------------------

print("=" * 72)
print(f"Bohrium skill smoke test")
print(f"BASE = {BASE}")
print(f"AK   = {AK[:6]}...{AK[-4:]} (len={len(AK)})")
print("=" * 72)


# ---------------------------------------------------------------------------
# bohrium-job
# ---------------------------------------------------------------------------
print("\n[bohrium-job]")
record("job", "/v1/job/list", "GET", params={"page": 1, "pageSize": 1})

# ---------------------------------------------------------------------------
# bohrium-node
# ---------------------------------------------------------------------------
print("\n[bohrium-node]")
record("node", "/v1/node/list", "GET", params={"page": 1, "pageSize": 1})

# ---------------------------------------------------------------------------
# bohrium-dataset
# ---------------------------------------------------------------------------
print("\n[bohrium-dataset]")
record("dataset", "/v1/ds/", "GET", params={"page": 1, "pageSize": 1})

# ---------------------------------------------------------------------------
# bohrium-image  — image v2 endpoints live on the LEGACY gateway
# ---------------------------------------------------------------------------
print("\n[bohrium-image]")
IMAGE_BASE = "https://openapi.dp.tech/openapi"


def record_image() -> None:
    url = IMAGE_BASE + "/v2/image/public?page=1&pageSize=1"
    req = urllib.request.Request(url, headers={"accessKey": AK})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = resp.status
            data = json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
    except urllib.error.HTTPError as e:
        code = e.code
        try:
            data = json.loads(e.read().decode("utf-8", errors="replace") or "{}")
        except json.JSONDecodeError:
            data = {}
    except Exception as e:  # noqa: BLE001
        code = 0
        data = {"_err": repr(e)}
    status, note = classify(code, data)
    note = (note + " (via openapi.dp.tech)").strip()
    results.append(Result("image", "/v2/image/public", status, code, note))
    print(f"  [{status}] GET  /v2/image/public  HTTP={code}  {note}")


record_image()

# ---------------------------------------------------------------------------
# bohrium-project
# ---------------------------------------------------------------------------
print("\n[bohrium-project]")
record("project", "/v1/project/lite_list", "GET")

# ---------------------------------------------------------------------------
# bohrium-knowledge-base
# ---------------------------------------------------------------------------
print("\n[bohrium-knowledge-base]")
record(
    "knowledge-base",
    "/v1/knowledge/knowledge_base/list",
    "GET",
    params={"page": 1, "pageSize": 1},
)

# ---------------------------------------------------------------------------
# bohrium-paper-search
# ---------------------------------------------------------------------------
print("\n[bohrium-paper-search]")
record(
    "paper-search",
    "/v2/paper/rag/pass/keyword",
    "POST",
    body={"words": ["graphene"], "question": "graphene synthesis", "type": 0, "pageSize": 2},
)
record(
    "paper-search",
    "/v2/paper/rag/pass/patent",
    "POST",
    body={"type": 3, "words": ["neural network"], "question": "neural network", "pageSize": 2},
)

# ---------------------------------------------------------------------------
# bohrium-pdf-parser
# ---------------------------------------------------------------------------
print("\n[bohrium-pdf-parser]")
# Trigger a cheap single-page parse and check we at least got a token back.
code, data = http(
    "POST",
    "/v1/parse/trigger-url-async",
    body={
        "url": "https://arxiv.org/pdf/2107.06922",
        "sync": False,
        "textual": True,
        "table": False,
        "molecule": False,
        "chart": False,
        "figure": False,
        "expression": False,
        "equation": False,
        "pages": [0],
        "timeout": 300,
    },
)
if 200 <= code < 300 and isinstance(data, dict):
    inner = data.get("data") if isinstance(data.get("data"), dict) else {}
    token = data.get("token") or inner.get("token")
    if token:
        status = "PASS"
        note = f"token={token[:8]}...  status={inner.get('status') or data.get('status')}"
    else:
        status = "FAIL"
        note = f"no token; body={json.dumps(data)[:160]}"
else:
    status = "FAIL"
    note = f"no token; body={json.dumps(data)[:160]}"
results.append(Result("pdf-parser", "/v1/parse/trigger-url-async", status, code, note))
print(f"  [{status}] POST /v1/parse/trigger-url-async  HTTP={code}  {note}")

# ---------------------------------------------------------------------------
# bohrium-web-search
# ---------------------------------------------------------------------------
print("\n[bohrium-web-search]")
record(
    "web-search",
    "/v1/search/web",
    "GET",
    params={"q": "deepmd-kit", "num": 3},
)

# ---------------------------------------------------------------------------
# bohrium-scholar
# ---------------------------------------------------------------------------
print("\n[bohrium-scholar]")
record(
    "scholar",
    "/v1/paper-server/scholar/search",
    "POST",
    body={"name": "Yann LeCun", "page": 1, "pageSize": 3},
)

# ---------------------------------------------------------------------------
# bohrium-wiki
# ---------------------------------------------------------------------------
print("\n[bohrium-wiki]")
record(
    "wiki",
    "/v1/literature-sage/wiki_v2/search_index_name",
    "POST",
    body={"name": "graphene", "node_types": ["field"], "style": "Feynman"},
)

# ---------------------------------------------------------------------------
# bohrium-sandbox (external, skipped)
# ---------------------------------------------------------------------------
print("\n[bohrium-sandbox]")
skip("sandbox", "api.e2b.dev/v1/*", "External service (E2B); not via open.bohrium.com")

# ---------------------------------------------------------------------------
# bohrium-viking-memory (external, skipped)
# ---------------------------------------------------------------------------
print("\n[bohrium-viking-memory]")
skip("viking-memory", "openviking.test.dp.tech/*", "External service (OpenViking); not via open.bohrium.com")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("SUMMARY")
print("=" * 72)
print(f"{'Skill':<22} {'Endpoint':<50} {'Status':<6} {'HTTP':<5} Note")
print("-" * 100)
for r in results:
    ep = r.endpoint if len(r.endpoint) <= 49 else r.endpoint[:46] + "..."
    code = "-" if r.code is None else str(r.code)
    note = r.note if len(r.note) <= 40 else r.note[:37] + "..."
    print(f"{r.skill:<22} {ep:<50} {r.status:<6} {code:<5} {note}")

passes = sum(r.status == "PASS" for r in results)
fails = sum(r.status == "FAIL" for r in results)
skips = sum(r.status == "SKIP" for r in results)
total = len(results)
print("-" * 100)
print(f"PASS={passes}  FAIL={fails}  SKIP={skips}  TOTAL={total}")

sys.exit(1 if fails else 0)
