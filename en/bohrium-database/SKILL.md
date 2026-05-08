---
name: bohrium-database
description: "Query scientific databases (materials structures, polymers, common data, molecular properties) via open.bohrium.com. Use when: user asks about querying material structures, phase diagrams, polymer data, common scientific datasets, or molecular property lookup. NOT for: molecule-in-paper search (use bohrium-mol-search), paper search (use bohrium-paper-search), knowledge base (use bohrium-knowledge-base)."
---

# SKILL: Bohrium Scientific Database

## Overview

Query scientific databases via multiple `open.bohrium.com` endpoints, covering material structures, polymers, common scientific datasets, and molecular properties.

**Supported data sources:**

| Endpoint prefix | Data type | Description |
|-----------------|-----------|-------------|
| `/v1/structures/` | Material structures | Crystal structure query, iteration, phase diagram convex hull |
| `/v1/database/` | Common data | Public datasets, polymer data |
| `/v1/molecular/` | Molecular properties | Lookup by name/SMILES/InChI/formula |

**Use when:**

- Querying crystal structures by formula
- Getting phase diagram convex hull data for a composition
- Browsing public material datasets
- Querying polymer material lists
- Looking up molecular property/structure data

**Don't use for:**

- Searching papers mentioning a molecule → `bohrium-mol-search`
- Paper/patent search → `bohrium-paper-search`
- Knowledge base file management → `bohrium-knowledge-base`

**No CLI support** — HTTP API only.

## Auth configuration

```json
"bohrium-database": {
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
BASE = "https://open.bohrium.com/openapi/v1"
H = {"accessKey": AK, "Content-Type": "application/json"}
H_GET = {"accessKey": AK}
```

---

## 1. Material structure query — `/structures/query`

Query material structures by formula (returns structure, energy, descriptor).

```python
r = requests.get(f"{BASE}/structures/query", headers=H_GET, params={
    "formula": "Li2O",
    "page": 1,
    "pageSize": 20
})
data = r.json()
for s in data.get("data", {}).get("items", []):
    print(f"  Formula: {s['formula']}, Energy: {s['energy']}")
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `formula` | string | yes | Chemical formula (e.g., `Li2O`, `Fe2O3`) |
| `page` | int | no | Page number, default 1 |
| `pageSize` | int | no | Items per page, default 20 |

**Response fields:**

| Field | Description |
|-------|-------------|
| `formula` | Chemical formula |
| `structure` | Structure data (typically JSON or POSCAR format) |
| `energy` | Energy value (eV) |
| `descriptor` | Structure descriptor |
| `submissionTime` | Submission time |

---

## 2. Structure iteration — `/structures/iterate`

Cursor-based iteration over all structures (for bulk export).

```python
start_id = 0
while True:
    r = requests.get(f"{BASE}/structures/iterate", headers=H_GET, params={
        "startId": start_id,
        "limit": 100
    })
    data = r.json().get("data", {})
    items = data.get("items", [])
    if not items:
        break
    for s in items:
        print(f"  [{s['id']}] {s['formula']} E={s['energy']}")
    start_id = data.get("nextStartId", 0)
    if start_id == 0:
        break
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `startId` | int | no | Start ID (pass 0 for first call) |
| `limit` | int | no | Batch size |

---

## 3. Phase diagram convex hull — `/structures/query_hull_by_composition/:composition`

Get phase diagram convex hull data for a composition (returns OSS link to hull plot).

```python
composition = "Li-Fe-O"
r = requests.get(f"{BASE}/structures/query_hull_by_composition/{composition}", headers=H_GET)
data = r.json()
print(f"  Hull URL: {data.get('data', {}).get('hull')}")
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `composition` (path) | string | yes | Chemical composition, elements joined by `-` (e.g., `Li-Fe-O`) |

---

## 4. Common data list — `/database/common_data/list`

Query public scientific datasets.

```python
r = requests.post(f"{BASE}/database/common_data/list", headers=H, json={
    "page": 1,
    "pageSize": 20
})
data = r.json()
for item in data.get("data", {}).get("items", []):
    print(f"  {item.get('name')}: {item.get('description')}")
```

---

## 5. Polymer data list — `/database/polymer/list`

Query polymer material data.

```python
r = requests.post(f"{BASE}/database/polymer/list", headers=H, json={
    "page": 1,
    "pageSize": 20
})
data = r.json()
for item in data.get("data", {}).get("items", []):
    print(f"  {item.get('name')}: {item.get('properties')}")
```

---

## 6. Molecular property lookup — `/molecular/search`

Look up molecular property data by name, SMILES, InChI, or formula.

```python
r = requests.post(f"{BASE}/molecular/search", headers=H, json={
    "query": "aspirin",
    "page": 1,
    "pageSize": 10
})
data = r.json()
print(data)
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | yes | Name / SMILES / InChI / formula |
| `page` | int | no | Page, default 1 |
| `pageSize` | int | no | Page size, default 10 |

> **Note**: To search for papers mentioning a specific molecule (similarity/substructure match), use `bohrium-mol-search` instead.

---

## curl examples

```bash
AK="YOUR_ACCESS_KEY"

# Query structures by formula
curl -s "https://open.bohrium.com/openapi/v1/structures/query?formula=Li2O&page=1&pageSize=10" \
  -H "accessKey: $AK" | jq .

# Phase diagram convex hull
curl -s "https://open.bohrium.com/openapi/v1/structures/query_hull_by_composition/Li-Fe-O" \
  -H "accessKey: $AK" | jq .

# Iterate structures
curl -s "https://open.bohrium.com/openapi/v1/structures/iterate?startId=0&limit=10" \
  -H "accessKey: $AK" | jq .

# Common data list
curl -s -X POST "https://open.bohrium.com/openapi/v1/database/common_data/list" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"page":1,"pageSize":10}' | jq .

# Polymer data
curl -s -X POST "https://open.bohrium.com/openapi/v1/database/polymer/list" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"page":1,"pageSize":10}' | jq .

# Molecular property lookup
curl -s -X POST "https://open.bohrium.com/openapi/v1/molecular/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"query":"aspirin","page":1,"pageSize":10}' | jq .
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| structures/query no results | Formula not in DB | Check spelling, try more common formulas |
| Hull link 404 | OSS file expired or missing | Composition may not have hull data yet |
| molecular/search timeout | Slow backend | Use SMILES instead of name (more precise) |
| database endpoint 404 | Path not whitelisted | Only `common_data/list` and `polymer/list` supported |

## Pairs well with

- **database** find material structures → **paper-search** for related synthesis/characterization papers
- **database** get molecular properties → **mol-search** to find papers discussing the molecule
- **database** export structure data → **sandbox** for computational analysis
