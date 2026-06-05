---
name: bohrium-mentor
description: "AI science tutor powered by Bohrium's adk_science_navigator agent. Submits a research question, subscribes to an SSE stream, and returns a structured Markdown answer. Use when: the user wants an AI-guided explanation of a scientific topic, a research progress summary, or a methodology comparison. NOT for: paper search (use bohrium-paper-search), literature review (use literature-review), or scholar lookup (use bohrium-scholar-search)."
---

# SKILL: AI Science Mentor (Science Navigator)

## Overview

**AI Science Mentor** calls Bohrium's `adk_science_navigator` agent to answer scientific questions with deep reasoning. The agent creates a session, streams intermediate and final response events over SSE, and returns a structured Markdown answer.

**Flow:**

```text
User scientific question
  |
  |-- Step 1: Create a session (POST sessions)
  |           -> get sessionId
  |
  |-- Step 2: Subscribe to the SSE stream (GET stream)
  |           -> receive streamed reasoning and answer fragments
  |
  |-- Step 3: Merge events and print the final answer
  |
  v
Output: reasoning fragments + structured Markdown answer
```

**Use cases:**

- Deep scientific Q&A, such as "recent CRISPR-Cas9 progress in gene therapy"
- Research method comparison and assessment
- Recent progress summaries for a scientific field
- Cross-disciplinary concept explanations

**Not for:**

- Specific paper search -> use `bohrium-paper-search`
- Systematic literature review -> use `literature-review`
- Scholar profile lookup -> use `bohrium-scholar-search`

**No CLI support** - use the Python script below to call the SSE APIs.

## Authentication

```json
"bohrium-mentor": {
  "enabled": true,
  "apiKey": "YOUR_BOHR_ACCESS_KEY",
  "env": {
    "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY"
  }
}
```

The script reads `BOHR_ACCESS_KEY` from the environment.

## API Endpoints

This skill uses:

| # | API | Method and Path | Purpose |
|---|-----|-----------------|---------|
| 1 | Create session | `POST /v2/sigma-search/api/v4/ai_search/sessions` | Submit the question and get `sessionId` |
| 2 | SSE stream | `GET /v2/sigma-search/api/v3/sse/ai_search/v1/{sessionId}/stream` | Receive streamed reasoning and answer events |
| 3 | Session detail | `GET /v2/sigma-search/api/v4/ai_search/sessions/{sessionId}` | Recover or replay session output |

Authentication uses the `Authorization: Bearer <BOHR_ACCESS_KEY>` header.

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Scientific question, for example "applications of quantum computing in drug discovery" |
| `discipline` | string | No | Discipline filter: `All` (default), `Physics`, `Chemistry`, `Biology`, etc. |
| `journal_type` | string | No | `foreign` (default) or `chinese` |
| `model` | string | No | `reason` (default) |

## Output

| Field | Description |
|-------|-------------|
| Reasoning | Streamed preprocessor content, when available |
| Final answer | Structured Markdown answer from the main layout |

---

## SSE Protocol

Each SSE event has the following shape:

```text
event:data
data:{"channel":{...},"system":{...},"sessionId":"..."}
```

Important fields:

| Path | Description |
|------|-------------|
| `system.event.type` | `start`, `streaming`, `end`, or `error` |
| `channel.uiInfo.layout` | `preprocessor` for reasoning, `main` for the final answer |
| `channel.uiInfo.subType` | Content component type |
| `channel.uiInfo.actionList[].action` | `append`, `delta`, or `patch` |
| `channel.uiInfo.content` | Current content fragment |
| `channel.answerId` | Message identifier. Events with the same `answerId` belong to the same answer block |

Merge rules:

1. Maintain accumulated state by `answerId` and `layout`.
2. For `action=append` or `action=delta`, append `content[key]` to the accumulated text.
3. Ignore `action=patch` for plain text extraction; it is mainly UI state.
4. On `system.event.type=end`, the `main.text` state contains the final answer if the stream completed cleanly.

---

## Complete Script

```python
import os
import sys
import json
import uuid
import requests


AK = os.environ.get("BOHR_ACCESS_KEY", "")
if not AK:
    print("ERROR: BOHR_ACCESS_KEY is not configured.")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi/v2/sigma-search"

QUERY = sys.argv[1] if len(sys.argv) > 1 else "Recent CRISPR-Cas9 progress in gene therapy"
DISCIPLINE = sys.argv[2] if len(sys.argv) > 2 else "All"
JOURNAL_TYPE = sys.argv[3] if len(sys.argv) > 3 else "foreign"
MODEL = "reason"

print("=" * 60)
print("  AI Science Mentor (Science Navigator)")
print(f"  Question: {QUERY}")
print(f"  Discipline: {DISCIPLINE}")
print(f"  Journal type: {JOURNAL_TYPE}")
print(f"  Model: {MODEL}")
print("=" * 60)


def create_session(query, discipline, journal_type, model):
    """Create an AI search session and return sessionId."""
    print("\n[Step 1/2] Creating session...")

    message_id = str(uuid.uuid4())
    answer_id = str(uuid.uuid4())

    payload = {
        "query": query,
        "model": model,
        "discipline": discipline,
        "scene": "adk_science_navigator",
        "journal_type": journal_type,
        "snp_version": "1.0.0",
        "resource_id_list": [],
        "SNPReq": {
            "sessionId": "",
            "channel": {
                "schema": "fe",
                "version": "v1",
                "role": "user",
                "auth": 1,
                "messageId": message_id,
                "answerId": answer_id,
                "uiInfo": {
                    "layout": "main",
                    "type": "ui",
                    "subType": "@bohrium-chat/common/markdown",
                    "content": {"text": query},
                    "actionList": [{"key": "text", "action": "append"}],
                },
                "entities": [],
                "state": {},
                "meta": {},
            },
            "system": {
                "payload": {
                    "model": model,
                    "agentId": "science_navigator",
                    "sessionId": "",
                    "scene": "adk_science_navigator",
                    "streaming": True,
                    "biz": {
                        "uploadList": [],
                        "sn": {
                            "discipline": discipline,
                            "journal_type": journal_type,
                            "model": model,
                        },
                    },
                },
            },
        },
    }

    url = f"{BASE}/api/v4/ai_search/sessions"
    try:
        response = requests.post(url, headers={"Authorization": f"Bearer {AK}"}, json=payload, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("  Error: create session timeout")
        return None
    except requests.exceptions.RequestException as exc:
        print(f"  Error: request failed - {exc}")
        return None

    data = response.json()
    if data.get("code") != 0:
        print(f"  Error: {data.get('message', 'unknown error')} (code={data.get('code')})")
        return None

    session_id = data["data"]["sessionId"]
    print(f"  Session created: {session_id}")
    return session_id


def subscribe_sse(session_id):
    """Subscribe to the SSE stream, merge events, and return accumulated state."""
    print("\n[Step 2/2] Subscribing to SSE stream...")

    url = f"{BASE}/api/v3/sse/ai_search/v1/{session_id}/stream"
    state = {}

    try:
        with requests.get(url, headers={"Authorization": f"Bearer {AK}"}, stream=True, timeout=180) as response:
            response.raise_for_status()
            buf = b""
            event_count = 0
            started = False

            for chunk in response.iter_content(chunk_size=4096):
                if not chunk:
                    continue
                buf += chunk

                while b"\n\n" in buf:
                    raw_bytes, buf = buf.split(b"\n\n", 1)
                    raw = raw_bytes.decode("utf-8", errors="replace")
                    lines = [line for line in raw.splitlines() if line.startswith("data:")]
                    if not lines:
                        continue

                    try:
                        evt = json.loads(lines[0][5:])
                    except json.JSONDecodeError:
                        continue

                    channel = evt.get("channel", {})
                    system = evt.get("system", {})
                    event_type = system.get("event", {}).get("type", "")

                    if event_type == "start":
                        if not started:
                            print("  Received start event.")
                            started = True
                        continue

                    if event_type == "error":
                        err_msg = system.get("event", {}).get("message", "unknown error")
                        print(f"  Error: {err_msg}")
                        return state

                    if event_type == "end":
                        print("  Received end event.")
                        return state

                    ui_info = channel.get("uiInfo") or {}
                    answer_id = channel.get("answerId", "default")
                    layout = ui_info.get("layout", "unknown")
                    action_list = ui_info.get("actionList") or []
                    content = ui_info.get("content") or {}
                    slot = state.setdefault(answer_id, {}).setdefault(layout, {})

                    for action in action_list:
                        action_type = action.get("action", "")
                        key = action.get("key", "")
                        if action_type in ("append", "delta") and key:
                            val = content.get(key, "")
                            if isinstance(val, str):
                                slot[key] = slot.get(key, "") + val

                    event_count += 1
                    if event_count % 50 == 0:
                        print(f"  Received {event_count} events...")

    except requests.exceptions.Timeout:
        print("  Warning: SSE stream timed out; returning received content")
    except requests.exceptions.RequestException as exc:
        print(f"  Error: SSE connection failed - {exc}")

    return state


def format_output(state):
    """Extract reasoning and final answer from accumulated state."""
    reasoning_parts = []
    main_parts = []

    for layouts in state.values():
        for layout, content in layouts.items():
            text = content.get("text", "")
            if not text:
                continue
            if layout == "preprocessor":
                reasoning_parts.append(text)
            elif layout == "main":
                main_parts.append(text)

    output_lines = []
    if reasoning_parts:
        output_lines.append("\n## Reasoning\n")
        output_lines.extend(part.strip() for part in reasoning_parts)
        output_lines.append("")

    if main_parts:
        output_lines.append("\n## Final Answer\n")
        output_lines.extend(part.strip() for part in main_parts)
    elif not reasoning_parts:
        output_lines.append("\n(No valid response content received.)")

    return "\n".join(output_lines)


if __name__ == "__main__":
    session_id = create_session(QUERY, DISCIPLINE, JOURNAL_TYPE, MODEL)
    if not session_id:
        print("\nFailed to create session.")
        sys.exit(1)

    result = format_output(subscribe_sse(session_id))
    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)
```

---

## Examples

```bash
export BOHR_ACCESS_KEY="your_key"

python3 science_navigator.py "Recent CRISPR-Cas9 progress in gene therapy"
python3 science_navigator.py "Latest strategies for suppressing lithium dendrites in solid-state batteries" "Chemistry" "foreign"
python3 science_navigator.py "Deep learning applications in protein structure prediction" "Biology" "chinese"
```

## Notes

1. First-token latency can be 30-60 seconds for deep reasoning.
2. Some streams may time out before an explicit `end` event; return the accumulated content in that case.
3. To recover after disconnects, call `GET /v2/sigma-search/api/v4/ai_search/sessions/{sessionId}`.
4. Use single calls or exponential backoff to avoid 429 rate limits.
