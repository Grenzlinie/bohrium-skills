---
name: bohrium-wiki
description: "Browse and search Bohrium SciencePedia (encyclopedia) via open.bohrium.com. Use when: user asks about finding scientific topics, reading encyclopedia-style entries, browsing by major/level/field hierarchy, or looking up a specific concept's article. NOT for: paper search (use bohrium-paper-search), knowledge base management (use bohrium-knowledge-base)."
---

# SKILL: Bohrium SciencePedia

## Overview

Access **Bohrium SciencePedia** through the `/v2/literature-sage/wiki_v2/*` endpoints on `open.bohrium.com` — a hierarchical encyclopedia of scientific topics organized as `major` → `level` → `field` → `topic` (a `topic` is one article/entry).

> **Two hosts, two jobs**: call the **API** on `open.bohrium.com`; build the **clickable reader link** you show to a human on `https://www.bohrium.com` (see [Building page links](#building-page-links)). They are different hosts — don't paste the API URL to a user.

**Use when**:

- Getting a quick definition of a scientific term (more focused than web-search — encyclopedia-style entries)
- Browsing by discipline (e.g., all subfields under materials science)
- Retrieving the full article of a topic (intro / applications / background sections)

**Don't use for**:

- Paper search → `bohrium-paper-search`
- Managing your own knowledge base → `bohrium-knowledge-base`

**No CLI support** — HTTP API only.

## Auth configuration

```json
"bohrium-wiki": {
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
BASE = "https://open.bohrium.com/openapi/v2/literature-sage/wiki_v2"
H = {"Authorization": f"Bearer {AK}", "Content-Type": "application/json"}

# Optional global defaults
DEFAULTS = {"language": "en-US", "style": "Feynman"}
# language: "en-US" / "zh-CN"
# style: "Feynman" for accessible tone, or others
```

---

## Actions overview

| Action | Method | Purpose |
|--------|--------|---------|
| `info` | GET | Basic SciencePedia info |
| `major_levels` | POST | List all majors and their levels |
| `get_wiki_index` | POST | Fetch index for a given nodeId / fieldId |
| `get_level_wiki_index` | POST | List nodes filtered by `node_types` |
| `search_index_name` | POST | Keyword search of index entries |
| `level_fields` | POST | List fields under a set of level nodes |
| `article` | POST | Fetch the article body of a node / entry |

---

## Choosing an action (intent → action)

Map what the user is asking for to the right call. Most flows are: **find an id → fetch content**.

| The user wants… | Use | You get back |
|-----------------|-----|--------------|
| "What disciplines / majors exist?" (top of the tree) | `major_levels` | majors + their `node_id` and levels |
| "What fields are under this major/level?" | `level_fields` (bulk, paged) or `get_level_wiki_index` (by `node_types`) | field rows / nodes |
| "Find the entry or field about **X**" | `search_index_name` | nodes with `node_id`, `node_type`, and `field_id` (for fields) |
| "Show the outline / topics of this field" | `get_wiki_index` (`field_id` or `node_id`) | topic tree, each topic carries an `entry_id` |
| "Explain / give me the article on **X**" | `article` (`entry_id` or `node_id`) | `document.article_name` + `main_content` + … |
| "Is the service up? basic metadata" | `info` | service info |

**Rule of thumb**: if you don't have an id yet, start with `search_index_name`; if the user is browsing a discipline, start with `major_levels`.

## Workflows

### A. Explain a concept (most common)

1. `search_index_name` with `{"name": "<concept>", "node_types": ["field","topic"]}` → take the best match's `node_id` (and `entry_id`/`field_id` if present).
2. `article` with that id → summarize `document.main_content`.
3. Return the explanation **plus** the reader link (see [Building page links](#building-page-links)).

### B. Browse a discipline

1. `major_levels` → pick a major/level.
2. `level_fields` (pass that level's `node_id`) → list fields.
3. `get_wiki_index` on a `field_id` → list the topics; attach a `course_url` for the field and `article_url` per topic.

### C. Build a learning path for a field

1. Resolve the field via `search_index_name` (`node_types: ["field"]`).
2. `get_wiki_index` → read topics in tree order.
3. Present as fundamentals → core → advanced, each topic linked.

---

## 1. Info — `info`

```python
r = requests.get(f"{BASE}/info", headers={"Authorization": f"Bearer {AK}"})
print(r.json())
```

---

## 2. Majors & levels — `major_levels`

```python
r = requests.post(f"{BASE}/major_levels", headers=H, json={**DEFAULTS})
for m in r.json().get("majors", []):
    levels = ", ".join(l["name"] for l in m.get("levels", []))
    print(f"- {m['name']} [{m['node_id']}]  levels: {levels}")
```

---

## 3. Search entries — `search_index_name`

```python
r = requests.post(f"{BASE}/search_index_name", headers=H, json={
    "name": "graphene",
    "node_types": ["field"],   # Filter: major / level / field / topic
    "style": "Feynman",
})
for i, n in enumerate(r.json().get("wiki_indices", []), 1):
    print(f"[{i}] [{n['node_type']}] {n['node_name']}  id={n['node_id']}")
```

---

## 4. All nodes under a level — `get_level_wiki_index`

```python
r = requests.post(f"{BASE}/get_level_wiki_index", headers=H, json={
    "node_types": ["major", "level"],
    **DEFAULTS,
})
for n in r.json().get("wiki_indices", [])[:50]:
    print(f"[{n['node_type']}] {n['node_name']}  ({n['node_id']})")
```

---

## 5. Index for a given node — `get_wiki_index`

```python
r = requests.post(f"{BASE}/get_wiki_index", headers=H, json={
    "node_id": "NODE_ID_HERE",
    # or "field_id": "FIELD_ID_HERE"
    **DEFAULTS,
})
print(r.json())
```

---

## 6. Bulk list fields under level — `level_fields`

```python
r = requests.post(f"{BASE}/level_fields", headers=H, json={
    "node_ids": ["LEVEL_NODE_ID1", "LEVEL_NODE_ID2"],
    "page_num": 1, "page_size": 10,
    **DEFAULTS,
})
for row in r.json().get("items", []):
    major = row.get("major", {}).get("name")
    level = row.get("level", {}).get("name")
    field = row.get("field", {}).get("name")
    print(f"- {major}/{level}/{field}  topics={row.get('topic_count')}")
```

---

## 7. Article body — `article`

```python
r = requests.post(f"{BASE}/article", headers=H, json={
    "node_id": "NODE_ID",         # or "entry_id": "ENTRY_ID"
    **DEFAULTS,
})
doc = r.json().get("document", {})
print(f"# {doc.get('article_name')}")
print(doc.get("main_content", "")[:2000])
```

**Common fields**: `document.article_name` / `document.main_content` / `document.applications` / `document.seo_title`.

---

## curl example

```bash
AK="$BOHR_ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v2/literature-sage/wiki_v2"

# Search entries by keyword
curl -s -X POST "$BASE/search_index_name" \
  -H "Authorization: Bearer $AK" -H "Content-Type: application/json" \
  -d '{"name":"graphene","node_types":["field"],"style":"Feynman"}' \
  | jq '.wiki_indices[] | {node_name, node_type, node_id}'
```

---

## Building page links

Whenever you show an entry or field to a human, attach the clickable reader link on `https://www.bohrium.com` (NOT the API host). This is what makes the answer useful to a person.

- **Page host**: `https://www.bohrium.com`
- **Style segment**: `Feynman → feynman`, `Hardcore → hardcore`
- **Language prefix**: `zh-CN` → no prefix; `en-US` → prefix with `/en`
- **URL-encode** dynamic ids.

| Link | Pattern | id source |
|------|---------|-----------|
| Article (topic) | `{lang}/sciencepedia/{style}/{entry_id}` | `entry_id` from `get_wiki_index` topic nodes (or the `entry_id` you pass to `article`) |
| Field (course) | `{lang}/sciencepedia/field/{style}/{field_id}` | `field_id` from `search_index_name` field results / `level_fields` |

```text
Article (en, Feynman):  https://www.bohrium.com/en/sciencepedia/feynman/<entry_id>
Field   (zh, Feynman):  https://www.bohrium.com/sciencepedia/field/feynman/solid_state_physics
```

> This skill exposes only article/field reading — there are no keyword page links here.

## Response standards

- Prefer a **teaching-style** answer: definition → intuition → key points → where it sits in the tree.
- Always include the reader link (`article_url` / `course_url`) for any entry or field you mention.
- If the requested `language`/`style` returns nothing, fall back in order: same language with the other style → `zh-CN`+`Feynman` → `en-US`+`Feynman`, and tell the user you switched.
- Keep API failures transparent; on empty results, suggest synonyms and one alternate language/style.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `No matches for "..."` | Keyword not in index | Try synonyms; expand `node_types` to `["field","topic","major","level"]` |
| Empty `article` | Wrong nodeId/entryId or no body | First call `search_index_name` to obtain the correct `node_id` |
| All-English (or all-Chinese) results | Wrong `language` | Set `"language": "en-US"` or `"zh-CN"` |
| Built a reader link on `open.bohrium.com` | Mixed up API host and page host | Page links use `https://www.bohrium.com` (see *Building page links*) |

## Pairs well with

- **wiki** for a baseline explanation of a concept → **paper-search** to go deep
- **wiki** to browse the discipline tree (`major_levels`) → pick a field → **scholar** to find leading researchers
