---
name: bohrium-matmaster
description: "MatMaster (Materials Master) integration via open.bohrium.com. Use when: user asks about querying MatMaster user skills, managing material science tools, or interacting with MatMaster via Feishu/Lark integration. NOT for: general paper search (use bohrium-paper-search)."
---

# SKILL: Bohrium MatMaster (Materials Master)

## Overview

Manage MatMaster platform user skills (tools/capabilities) and Feishu integration via `open.bohrium.com`.

**Core capabilities:**

| Endpoint pattern | Function |
|-----------------|----------|
| `/v1/matmaster/users/:userId/skills` | Query/manage user's MatMaster skills (tool list) |
| `/v1/matmaster/integrations/feishu/*` | Feishu/Lark integration (messages, callbacks) |

**Use when:**

- Querying a user's available MatMaster tools/skills
- Interacting with MatMaster via Feishu
- Managing material-science AI tool capabilities

**Don't use for:**

- Paper search → `bohrium-paper-search`
- Knowledge graph / scientific claims → `bohrium-lkm`

**No CLI support** — HTTP API only.

## Auth configuration

```json
"bohrium-matmaster": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

## Common template

```python
import os, requests

AK = os.environ["ACCESS_KEY"]
BASE = "https://open.bohrium.com/openapi/v1/matmaster"
H = {"accessKey": AK, "Content-Type": "application/json"}
H_GET = {"accessKey": AK}
```

---

## 1. Query user skills — `/matmaster/users/:userId/skills`

Get the list of available tools/skills for a specific user on MatMaster.

```python
user_id = "12345"
r = requests.get(f"{BASE}/users/{user_id}/skills", headers=H_GET)
data = r.json()
for skill in data.get("data", []):
    print(f"  {skill.get('name')}: {skill.get('description')}")
    print(f"    Status: {skill.get('status')}")
```

---

## 2. Feishu integration — `/matmaster/integrations/feishu/*`

### Send message / trigger action

```python
r = requests.post(f"{BASE}/integrations/feishu/send", headers=H, json={
    "action": "query",
    "content": "Query crystal structure of LiFePO4"
})
print(r.json())
```

### Check integration status

```python
r = requests.get(f"{BASE}/integrations/feishu/status", headers=H_GET)
print(r.json())
```

---

## Path whitelist

The open-platform strictly limits MatMaster paths to:

- `/users/*/skills` — user skill operations only
- `/integrations/feishu/*` — Feishu integration operations

Other paths return 404.

---

## curl examples

```bash
AK="YOUR_ACCESS_KEY"

# Query user skills
curl -s "https://open.bohrium.com/openapi/v1/matmaster/users/12345/skills" \
  -H "accessKey: $AK" | jq .

# Feishu integration status
curl -s "https://open.bohrium.com/openapi/v1/matmaster/integrations/feishu/status" \
  -H "accessKey: $AK" | jq .
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 404 Not found | Path not whitelisted | Only `/users/*/skills` and `/integrations/feishu/*` are allowed |
| 401 Unauthorized | Invalid or missing AccessKey | Check `accessKey` in headers |
| Empty skills list | User has no skills configured | Register skills on MatMaster platform first |

## Pairs well with

- **matmaster** query available tools → select appropriate tool for material science tasks
- **matmaster** Feishu integration → trigger material queries via Feishu → **database** for structure data
- **matmaster** skill list → understand capabilities → combine with **paper-search** for literature review
