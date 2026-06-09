---
name: bohrium-tools
description: "Browse and search the Bohrium scientific Tools library via open.bohrium.com. Use when: user wants to browse scientific computing tools by domain/subdomain, hybrid-search tools by keywords, or view a tool's details (GitHub metrics, tutorial, related entries). NOT for: paper search (use bohrium-paper-search), encyclopedia entries (use bohrium-wiki), knowledge base management (use bohrium-knowledge-base)."
---

# SKILL: Bohrium Scientific Tools Library

## Overview

Access the **Bohrium Tools library** through the `/v2/literature-sage/tool/*` endpoints on `open.bohrium.com` — a directory of scientific computing software/tools organized as `domain` → `subdomain` → `tool`, with hybrid retrieval (BM25 + vector recall).

**Use when**:

- Browsing tools under a domain (e.g., all tools under molecular dynamics)
- Hybrid-searching the best-matching tools with natural language + keyword weights
- Viewing a tool's details (profile, GitHub star/fork, tutorial, related entries, Docker image, MCP URL, etc.)

**Don't use for**:

- Paper search → `bohrium-paper-search`
- Encyclopedia entries → `bohrium-wiki`
- Managing your own knowledge base → `bohrium-knowledge-base`

**No CLI support** — HTTP API only.

## Auth configuration

```json
"bohrium-tools": {
  "enabled": true,
  "apiKey": "YOUR_BOHR_ACCESS_KEY",
  "env": {
    "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY"
  }
}
```

## Common template

```python
import os, requests

AK = os.environ["BOHR_ACCESS_KEY"]
BASE = "https://open.bohrium.com/openapi/v2/literature-sage/tool"

# Language is controlled by the Content-Language header: en-us / zh-cn
H = {
    "Authorization": f"Bearer {AK}",
    "Content-Type": "application/json",
    "Content-Language": "en-us",   # or "zh-cn"
}

# All responses are wrapped in an envelope: {"code": 0, "data": {...}, "trace_id": "..."}.
# The real payload (items / tools / total_num / ...) lives under "data". Always unwrap it.
def data(r):
    r.raise_for_status()
    body = r.json()
    if isinstance(body, dict) and body.get("code") not in (0, None) and "data" not in body:
        raise RuntimeError(f"API error code={body.get('code')} msg={body.get('message')}")
    return body.get("data", body) if isinstance(body, dict) else body
```

> **Language note**: Most endpoints determine display language from the `Content-Language` header (`en-us`/`zh-cn`), defaulting to English `en-US` when absent. However, `search/hybrid` and `search/subdomain` **require** a language: pass `language` (`en-US`/`zh-CN`) in the body or send a `Content-Language` header — at least one. Omitting both returns `language is required` (no fallback).

---

## Actions overview

| Action | Method | Path | Purpose |
|--------|--------|------|---------|
| `domain` | GET | `/domain` | List all tool domains |
| `domain/summary` | GET | `/domain/summary` | Total tool count |
| `subdomain` | POST | `/subdomain` | List subdomains under domains (paged) |
| `subdomain/detail` | POST | `/subdomain/detail` | Get subdomain detail |
| `list` | POST | `/list` | List tools under a subdomain (tag filter / sort / page) |
| `detail` | GET | `/detail` | Get tool detail by `tool_unique_key` |
| `tags` | POST | `/tags` | Get tags under a set of subdomains |
| `search/hybrid` | POST | `/search/hybrid` | Tool hybrid search (text + keyword weights) |
| `search/subdomain` | POST | `/search/subdomain` | Subdomain search |

---

## 1. List domains — `domain`

```python
r = requests.get(f"{BASE}/domain", headers=H)
for it in data(r).get("items", []):
    print(f"- {it['node_name']}  [{it['node_id']}]  tools={it['tool_num']}")
```

Response fields: `data.items[].node_id` / `node_name` / `tool_num`.

---

## 2. Tool count — `domain/summary`

```python
r = requests.get(f"{BASE}/domain/summary", headers=H)
print(data(r).get("total_num"))   # data: {"total_num": 1234}
```

---

## 3. List subdomains — `subdomain`

```python
r = requests.post(f"{BASE}/subdomain", headers=H, json={
    "domain_node_ids": ["DOMAIN_NODE_ID"],   # list of domain node_ids; empty = all
    "page": 1,
    "page_size": 20,
})
body = data(r)
print("total:", body.get("total"))
for it in body.get("items", []):
    print(f"- {it['node_name']}  [{it['node_id']}]  tools={it['tool_num']}  tags={it.get('tags')}")
```

Response: `data.items[].node_id` / `node_name` / `tool_num` / `tags` / `tools[]` (lite: `tool_unique_key`/`tool_name`/`avatar_url`); paging `data.total` / `page` / `pageSize`.

---

## 4. Subdomain detail — `subdomain/detail`

```python
r = requests.post(f"{BASE}/subdomain/detail", headers=H, json={
    "subdomain_node_id": "SUBDOMAIN_NODE_ID",
})
print(data(r))   # data: {"node_id": "...", "node_name": "..."}
```

---

## 5. Tools under a subdomain — `list`

```python
r = requests.post(f"{BASE}/list", headers=H, json={
    "subdomain_node_id": "SUBDOMAIN_NODE_ID",   # required
    "tag_ids": [],            # optional: filter by tag ids
    "sort_by": "star_count",  # optional sort field, e.g. star_count / last_commit_time
    "sort_type": "desc",      # asc / desc
    "page": 1,
    "page_size": 10,
})
body = data(r)
print("total:", body.get("total"))
for it in body.get("items", []):
    print(f"- {it['name']}  star {it['star_count']}  key={it['tool_unique_key']}")
    print(f"    {it.get('profile','')[:120]}")
```

Key `data.items[]` fields: `id` / `name` / `profile` / `tags` / `star_count` / `related_entry_count` / `last_commit_time` / `avatar_url` / `tool_unique_key`.

---

## 6. Tool detail — `detail`

```python
r = requests.get(f"{BASE}/detail", headers=H, params={
    "tool_unique_key": "TOOL_UNIQUE_KEY",   # required
})
d = data(r)
print(f"# {d['name']}  star {d['star_count']} / fork {d['fork_count']}")
print("repo:", d.get("repo_url"))
print(d.get("overview", "")[:2000])
```

Key fields of `GetToolDetailResponse`: `name` / `profile` / `version` / `star_count` / `fork_count` / `watch_count` / `key_points` / `overview` / `tutorial` / `related_entry_list` / `primary_language` / `license` / `mcp_url` / `docker_image_uri` / `repo_url` / `help_urls` / `sub_domains` / `tags`.

---

## 7. Subdomain tags — `tags`

```python
r = requests.post(f"{BASE}/tags", headers=H, json={
    "subdomain_node_ids": ["SUBDOMAIN_NODE_ID1", "SUBDOMAIN_NODE_ID2"],   # required
})
for it in data(r).get("items", []):
    print(f"- {it['tag_name']}  [{it['tag_id']}]")
```

---

## 8. Tool hybrid search — `search/hybrid`

Hybrid (BM25 + vector) recall using natural-language `text` + keyword weights `keywords` (keyword → weight).

```python
r = requests.post(f"{BASE}/search/hybrid", headers=H, json={
    "text": "molecular dynamics simulation engine with GPU support",
    "keywords": {"molecular dynamics": 1.0, "GPU": 0.6},  # required: keyword -> weight
    "language": "en-US",      # required: either this or the Content-Language header; omitting both returns "language is required"
    "k": 50,                  # optional; default 100, max 500
    "return_level": "",       # optional: control return granularity
})
body = data(r)
print("total:", body.get("total"))
for t in body.get("tools", []):
    score = t.get("score")
    score_str = f"{score:.3f}" if isinstance(score, (int, float)) else "-"   # score may be null
    print(f"- {t['tool_name']}  score={score_str}  key={t.get('tool_unique_key')}")
```

Key `data.tools[]` fields: `tool_id` / `tool_name` / `tool_unique_key` / `domains` / `subdomains` / `tags` / `profile` / `repo_url` / `score` / `matched_chunks`.

---

## 9. Subdomain search — `search/subdomain`

```python
r = requests.post(f"{BASE}/search/subdomain", headers=H, json={
    "text": "protein structure prediction",
    "language": "en-US",   # required: either this or the Content-Language header; omitting both returns "language is required"
})
for s in data(r).get("subdomains", []):
    print(f"- {s['node_display_name']}  [{s['node_id']}]")
```

---

## curl examples

```bash
AK="$BOHR_ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v2/literature-sage/tool"

# Tool hybrid search (payload lives under .data)
curl -s -X POST "$BASE/search/hybrid" \
  -H "Authorization: Bearer $AK" \
  -H "Content-Type: application/json" \
  -H "Content-Language: en-us" \
  -d '{"text":"molecular dynamics simulation","keywords":{"molecular dynamics":1.0},"k":20}' \
  | jq '.data.tools[] | {tool_name, score, tool_unique_key}'

# List domains
curl -s "$BASE/domain" \
  -H "Authorization: Bearer $AK" -H "Content-Language: en-us" \
  | jq '.data.items[] | {node_name, node_id, tool_num}'
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| All-English (or all-Chinese) results | Wrong `Content-Language` / `language` | Set header `Content-Language: zh-cn` or pass `"language":"zh-CN"` in the search body |
| `search/hybrid` returns `text is required` | Missing `text` | Both `text` and `keywords` are required |
| `search/hybrid` / `search/subdomain` returns `language is required` | Neither body `language` nor `Content-Language` header was provided | Add `"language":"en-US"` (or `zh-CN`) to the body, or send a `Content-Language: en-us` header |
| `k` truncated | `search/hybrid` caps `k` at 500 | Keep `k` ≤ 500 |
| `list` reports `subdomain_node_id` error | Missing required subdomain id | First obtain `node_id` via `subdomain` or `search/subdomain` |

## Pairs well with

- **tools** to search/browse tools (`domain` → `subdomain` → `list` → `detail`)
- Use **wiki** / **paper-search** to understand a direction first, then **tools** to find implementations
- Use `search/hybrid` for natural-language tool discovery, and `search/subdomain` to locate the best-matching subdomain
