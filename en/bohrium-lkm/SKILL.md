---
name: bohrium-lkm
description: "Large Knowledge Model (LKM) via open.bohrium.com (v1). Use when: user asks about searching scientific claims/questions, retrieving reasoning chains, viewing a paper's knowledge graph, tracing why a claim holds, or batch-hydrating knowledge node details. NOT for: general paper keyword search (use bohrium-paper-search), knowledge base management (use bohrium-knowledge-base), single PDF parsing (use bohrium-pdf-parser)."
---

# SKILL: Bohrium LKM (Large Knowledge Model)

## Overview

LKM (Large Knowledge Model) v1 endpoints on `open.bohrium.com` let you search and trace knowledge extracted from scientific literature: search claim/question nodes, retrieve reasoning chains, view a paper-level knowledge graph, trace the reasoning behind a single claim, and batch-hydrate node details by ID.

**Core capabilities:**

| Endpoint | Function |
|----------|----------|
| `POST /v1/lkm/search` | Node search: recall relevant claim / question nodes |
| `POST /v1/lkm/reasoning/search` | Reasoning chain search: recall whole chains by argument similarity |
| `POST /v1/lkm/papers/graph` | Paper-level knowledge graph: full graph extracted from a paper |
| `GET /v1/lkm/claims/{id}/reasoning` | Single-claim reasoning chain: why a claim holds |
| `POST /v1/lkm/variables/batch` | Batch hydration: fetch node details by an ID list |

**Choosing an entry point:**

- Find claims/questions by keyword/semantics → `/search`
- Find whole reasoning chains whose research/experimental process is similar (not just a single matching claim) → `/reasoning/search`
- Open one paper and view its full structured graph → `/papers/graph`
- Have a claim ID, want its reasoning chain → `/claims/{id}/reasoning`
- Have a set of node IDs, want to hydrate details → `/variables/batch`

**Don't use for:**

- General paper keyword search → `bohrium-paper-search`
- Knowledge base file management → `bohrium-knowledge-base`
- Single PDF parsing → `bohrium-pdf-parser`

**No CLI support** — HTTP API only.

## How the endpoints connect

The 5 endpoints fall into two groups:

- **Natural-language search entry points** (only need `query`, no ID up front): `/search`, `/reasoning/search`
- **Identifier/ID-based lookups** (need a paper identifier or node ID first): `/papers/graph` (paper `package_id`/`paper_id`/`doi`/`title`), `/claims/{id}/reasoning` (claim `gcn_` ID), `/variables/batch` (node `gcn_` ID)

> `/papers/graph` can be a standalone starting point if you already have a DOI or title; otherwise its `package_id`/`paper_id` typically comes from paper metadata returned by `/search` or `/reasoning/search`.

A search entry point's output (node IDs, paper IDs) is exactly the downstream input. Data flow:

```mermaid
flowchart TD
    search["/search node search"]
    rsearch["/reasoning/search chain search"]
    pgraph["/papers/graph paper graph"]
    creason["/claims/{id}/reasoning single chain"]
    batch["/variables/batch hydration"]

    search -->|"variables[].id (gcn_)"| creason
    search -->|"variables[].id (gcn_)"| batch
    search -->|"papers package_id / paper_id"| pgraph
    rsearch -->|"conclusion node global_id"| creason
    rsearch -->|"any node global_id (gcn_)"| batch
    rsearch -->|"paper_id (numeric)"| pgraph
    pgraph -->|"conclusion node global_id"| creason
    pgraph -->|"any node global_id (gcn_)"| batch
    creason -->|"any node global_id (gcn_)"| batch
```

**ID flow:**

| Upstream output | ID type | Usable downstream |
|------|------|------|
| `search` `variables[].id`; graph node `global_id` | global node ID `gcn_...` | `variables/batch` (any node); `claims/{id}/reasoning` (only `has_reasoning=true` conclusions) |
| `papers`/`paper` metadata; `reasoning_chains[].paper_id` | paper ID (`paper:<number>` or plain numeric) | `papers/graph` (`package_id`/`paper_id`); `reasoning/search` `filters.paper_ids` (plain numeric, no `paper:` prefix) |

**Pitfall:** do not pass a graph local node ID (e.g. `paper:...::conclusion_3`) as a global `gcn_` ID or paper ID downstream — `claims/{id}/reasoning` returns `290004`, and `variables/batch` puts it in `not_found`.

## Auth configuration

The code reads the access key from the `BOHR_ACCESS_KEY` environment variable. Provide it in one of two ways depending on the runtime:

**Option A: set the environment variable directly** (when not running under OpenClaw)

```bash
export BOHR_ACCESS_KEY=<YOUR_BOHR_ACCESS_KEY>
```

**Option B: inject via OpenClaw** (when running inside OpenClaw)

Configure `~/.openclaw/openclaw.json`; OpenClaw injects `env.BOHR_ACCESS_KEY` into the runtime environment automatically:

```json
"bohrium-lkm": {
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
BASE = "https://open.bohrium.com/openapi/v1/lkm"
H = {"Authorization": f"Bearer {AK}", "Content-Type": "application/json"}

def lkm_data(r):
    """Unwrap an LKM response: return data when code == 0, else raise with code/message."""
    body = r.json()
    if body.get("code") != 0:
        raise RuntimeError(f"LKM error {body.get('code')}: {body.get('message')}")
    return body["data"]
```

The examples below call `lkm_data(r)` so the documented `code` contract is always enforced.

**Business status:** HTTP usually returns 200; success is determined by `code` in the response body, where `code == 0` means success. See the error-code table at the end.

---

## 1. Node search — `POST /search`

Recall claim / question nodes in LKM via natural language. Returns individual nodes, not full reasoning chains.

```python
r = requests.post(f"{BASE}/search", headers=H, json={
    "query": "perovskite thermal stability",
    "keywords": ["FAPbI3", "Cs doping"],
    "retrieval_mode": "hybrid",
    "sort_by": "comprehensive",  # optional; default comprehensive; or relevance/recent/journal
    "scopes": ["claim", "question"],
    # "filters": {               # optional; ONLY when restricting recall to specific papers
    #     "paper_ids": ["811977903947382784"],  # plain numeric, no paper: prefix, ≤50
    #     "dois": ["10.1038/s41586-021-03381-x"]  # ≤50, can combine with paper_ids
    # },
    "reasoning_only": False,
    "offset": 0,
    "limit": 20
})
data = lkm_data(r)
for v in data["variables"]:
    print(v["id"], v["type"], v.get("role"), v["has_reasoning"], (v.get("content") or "")[:80])
# data["papers"]: paper metadata referenced by hits (key like paper:<id>)
# data["has_more"]: whether more pages exist
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | yes | Natural language query, ≤200 chars recommended |
| `keywords` | string[] | no | Up to 10, ≤100 chars each; put terms/materials/methods/abbreviations, not full sentences |
| `retrieval_mode` | string | no | `hybrid`(default, semantic+lexical) / `semantic`(vector only, faster) / `lexical`(keyword only) |
| `sort_by` | string | no | Sort strategy, default `comprehensive` when omitted: `relevance`(pure relevance, most on-target top hit) / `recent`(prefers newer once relevance bar is met) / `journal`(prefers high-quality journals once relevance bar is met) / `comprehensive`(relevance+recency+quality+diversity combined) |
| `scopes` | string[] | no | Restrict node type: `claim`, `question`; omit = no restriction |
| `filters.visibility` | string | no | Content visibility, usually `public` |
| `filters.role` | string | no | Restrict claim role: `conclusion`/`premise`/`highlight` |
| `filters.paper_ids` | string[] | no | Restrict recall to papers, plain numeric IDs, **no `paper:` prefix**, up to 50 |
| `filters.dois` | string[] | no | Restrict recall to papers by DOI, up to 50; server resolves each to a paper_id then merges with `paper_ids` for filtering; can be combined with `paper_ids`, omit = no paper restriction |
| `reasoning_only` | bool | no | `true` returns only conclusion claims backed by a reasoning chain (legacy alias `evidence_only`) |
| `include_paper_enrich` | bool | no | `true` returns richer paper metadata (larger response; use only when needed) |
| `offset` | int | no | Page start, max 10000 |
| `limit` | int | no | Page size, default 20, max 100 |

**Key response fields:**

| Field | Description |
|-------|-------------|
| `data.variables[].id` | Global node ID (`gcn_...`), usable in later reasoning / batch calls |
| `data.variables[].type` | `claim` or `question` |
| `data.variables[].role` | Claim role: `conclusion`/`premise`, etc. |
| `data.variables[].score` | Retrieval rank score — **not credibility/evidence strength**, do not show as confidence |
| `data.variables[].has_reasoning` | Whether the claim has a traceable reasoning chain (prefer `true` when showing reasoning) |
| `data.variables[].provenance.source_packages` | Source paper package IDs |
| `data.papers` | Paper metadata map, key like `paper:<id>` |
| `data.has_more` | Whether more pages exist (next page: same body, `offset += page count`) |

**Constraint:** when `reasoning_only=true`, `scopes` must be omitted or `["claim"]`, and `filters.role` must be omitted or `conclusion`; conflicts return `290002`.

> **Sorting note:** the recency/quality boosts in `recent`/`journal`/`comprehensive` are all relevance-gated, so they never pull in irrelevant content; existing callers that omit `sort_by` automatically get the better `comprehensive` default ordering.

---

## 2. Reasoning chain search — `POST /reasoning/search`

Recall whole reasoning chains — the research process a paper used to reach a conclusion (theoretical derivation, numerical computation, experimental procedure) — ranked by how similar that process is to your query, not by single-node text match. New callers should always pass `format: "graph"`.

```python
r = requests.post(f"{BASE}/reasoning/search", headers=H, json={
    "query": "infer phase stability from XRD evidence",
    "keywords": ["powder XRD", "Rietveld refinement", "phase transition"],
    "retrieval_mode": "hybrid",
    "sort_by": "comprehensive",  # optional; default comprehensive; or relevance/recent/journal
    "format": "graph",
    # "filters": {               # optional; ONLY when restricting recall to specific papers
    #     "paper_ids": ["811977903947382784"],  # plain numeric, no paper: prefix, ≤50
    #     "dois": ["10.1038/s41586-021-03381-x"]  # ≤50, can combine with paper_ids
    # },
    "offset": 0,
    "limit": 20
})
data = lkm_data(r)
for c in data["reasoning_chains"]:
    print(c["chain_id"], c["paper_id"], c["score"])
    print("  nodes:", len(c["graph"]["nodes"]), "edges:", len(c["graph"]["edges"]))
# data["total"]: total hits not truncated by limit
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | yes | Describe the reasoning process you want, ≤200 chars recommended |
| `keywords` | string[] | no | Up to 10; put method/material/condition/metric/abbreviation names |
| `retrieval_mode` | string | no | `hybrid`(default) / `semantic` / `lexical` |
| `sort_by` | string | no | Sort strategy, default `comprehensive` when omitted: `relevance`(pure relevance, most on-target top hit) / `recent`(prefers newer once relevance bar is met) / `journal`(prefers high-quality journals once relevance bar is met) / `comprehensive`(relevance+recency+quality+diversity combined) |
| `filters.paper_ids` | string[] | no | Restrict recall to papers, plain numeric, **no `paper:` prefix**, up to 50 |
| `filters.dois` | string[] | no | Restrict recall to papers by DOI, up to 50; server resolves each to a paper_id then merges with `paper_ids`; can be combined with `paper_ids`, omit = no paper restriction |
| `format` | string | no | Recommended `graph`, returns `graph.nodes`/`graph.edges`; omit returns legacy structure |
| `offset` | int | no | Page start, max 10000 |
| `limit` | int | no | Page size, default 20, max 100 |

**Key response fields (`format: "graph"`):**

| Field | Description |
|-------|-------------|
| `data.reasoning_chains[].chain_id` | Reasoning chain ID |
| `data.reasoning_chains[].paper_id` | Source paper ID (plain numeric) |
| `data.reasoning_chains[].score` | Retrieval rank score — **do not show as confidence** |
| `data.reasoning_chains[].graph` | Chain graph (`nodes` / `edges`, see graph section) |
| `data.reasoning_chains[].paper` | Source paper metadata |
| `data.reasoning_chains[].addressed_problems` / `open_questions` | Problems addressed / open questions |
| `data.total` | Total hits; pagination: more pages if `offset + page count < total` |

> **Sorting note:** same semantics as `/search` — the recency/quality boosts in `recent`/`journal`/`comprehensive` are relevance-gated and never introduce irrelevant content; omitting `sort_by` defaults to `comprehensive`.

---

## 3. Paper-level knowledge graph — `POST /papers/graph`

Given a paper, return the full graph LKM extracted from it (conclusions, reasoning steps, highlights, weak points, subproblems and relation edges). The main entry point for paper-level graphs.

```python
r = requests.post(f"{BASE}/papers/graph", headers=H, json={
    "package_id": "paper:1020661015349559308"   # one of four identifiers, see below
})
data = lkm_data(r)
for p in data["papers"]:
    print(p["paper"]["en_title"])
    print("  nodes:", len(p["graph"]["nodes"]), "edges:", len(p["graph"]["edges"]))
    print("  addressed_problems:", len(p["addressed_problems"]))
```

**Parameters (at least one of the four identifiers; not all empty):**

| Field | Type | Description |
|-------|------|-------------|
| `package_id` | string | LKM package ID, like `paper:<number>`; **highest priority** |
| `paper_id` | string | LKM paper ID, plain numeric, e.g. `812481689673531392` |
| `doi` | string | Paper DOI, e.g. `10.1038/s41586-021-03381-x` |
| `title` | string | Title or title keywords; may return multiple candidates |
| `title_resolve.limit` | int | When using `title`, cap candidates; default 5, max 20 |

> Priority: `package_id > paper_id > doi > title`. `package_id`/`paper_id` are LKM-internal IDs (not DOI/PMID), usually obtained from paper metadata returned by other LKM endpoints.

**Key response fields:**

| Field | Description |
|-------|-------------|
| `data.papers[].paper` | Paper metadata (`package_id`, title, authors, DOI, journal, etc.) |
| `data.papers[].graph` | Paper-level knowledge graph (`nodes` / `edges`, see graph section) |
| `data.papers[].addressed_problems` | Core problems the paper addresses |
| `data.papers[].open_questions` | Open questions / future work |

> Non-title paths usually return 1 paper; title path may return multiple candidates (each may carry `title_match_type`, e.g. `exact`/`keyword`). `include`/`hydrate_factor_refs` are legacy compatibility fields; the new default graph response does not need them.

---

## 4. Single-claim reasoning chain — `GET /claims/{id}/reasoning`

Given a global claim ID (`gcn_...`), return the reasoning steps and premises that support it. New callers should always pass `format=graph`.

```python
claim_id = "gcn_73e13bb548f847bd"
r = requests.get(f"{BASE}/claims/{claim_id}/reasoning", headers=H,
                 params={"format": "graph", "max_chains": 10, "sort_by": "comprehensive"})
data = lkm_data(r)
print(data["claim"]["id"], "total_chains:", data["total_chains"])
for c in data["reasoning_chains"]:
    print("  paper:", c["paper"]["en_title"])
    print("  nodes:", len(c["graph"]["nodes"]), "edges:", len(c["graph"]["edges"]))
```

**Parameters:**

| Field | In | Required | Description |
|-------|----|----------|-------------|
| `id` | path | yes | Global claim ID, like `gcn_...` (do NOT pass graph local node IDs like `paper:...::conclusion_3`) |
| `max_chains` | query | no | Max chains, default 10, max 100 |
| `sort_by` | query | no | `comprehensive`(default, by informativeness) / `recent`(newest first) |
| `format` | query | no | Recommended `graph`; omit or non-graph returns legacy `factors` structure |

**Key response fields (`format=graph`):**

| Field | Description |
|-------|-------------|
| `data.claim` | The queried claim itself (`id`/`type`/`content_hash`) |
| `data.reasoning_chains[].graph` | Chain graph (`nodes` / `edges`, see graph section) |
| `data.reasoning_chains[].paper` | Source paper metadata for the chain |
| `data.reasoning_chains[].addressed_problems` / `open_questions` | Problem background / open questions |
| `data.total_chains` | Total number of available chains |

> Prefer calling only on claims with `role = conclusion` and `has_reasoning = true`. Calling on premise / weak point / no-reasoning claims may return `290008`; wrong ID type often returns `290004`.

---

## 5. Batch hydration — `POST /variables/batch`

Fetch node details by ID list. Get IDs from a search endpoint first, then hydrate here. **This is not a search endpoint.**

```python
r = requests.post(f"{BASE}/variables/batch", headers=H, json={
    "ids": ["gcn_654cd35dcb814a0c", "gcn_9523aa7f1fd04d8a"]
})
data = lkm_data(r)
for v in data["variables"]:
    print(v["id"], v["type"], (v.get("content") or "")[:80])
print("not_found:", data["not_found"])
# data["papers"]: paper metadata organized by package_id
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ids` | string[] | yes | Global node IDs (`gcn_...`), 1–100, **no empty strings**; duplicates are deduped |

**Key response fields:**

| Field | Description |
|-------|-------------|
| `data.variables[]` | Matched nodes (`id`/`type`/`title`/`content`/`representative_lcn`/`local_members`/`provenance`) |
| `data.variables[].metadata` / `parameters` | **Parse defensively**: may be empty string, JSON string, or array string |
| `data.not_found` | IDs not matched (graph local IDs / paper IDs / package IDs land here) |
| `data.papers` | Paper metadata organized by `package_id` |

> Clean the list first: drop empty strings/null, dedupe, batch ≤100. Partial misses do not fail the request (still `code = 0`).

---

## Shared graph notes (endpoints 2 / 3 / 4)

`graph` consists of `nodes` and `edges`, ready for frontend graph rendering.

**Node `kind`:**

| kind | Meaning |
|------|---------|
| `conclusion` | Conclusion node (in endpoint 4, usually the passed claim) |
| `reasoning_steps` | Reasoning steps supporting a conclusion, usually with a `steps[]` array |
| `highlight` | Positive highlight / key evidence / supporting observation |
| `weak_point` | Weakness / limitation / risk / premise to treat cautiously |
| `subproblem` | Subproblem or research motivation driving the conclusion |

**Edge `type`:**

| type | Meaning |
|------|---------|
| `concludes` | reasoning_steps points to conclusion |
| `highlight_of` | highlight points to the reasoning_steps it supports (positive) |
| `weakpoint_of` | weak_point points to the reasoning_steps it weakens (limitation/risk) |
| `subproblem_of` | subproblem points to the conclusion it drives |
| `previous_conclusion_of` | Contextual/precedence relation between a prior conclusion and the current one |

**Notes:**

- `highlight_of` and `weakpoint_of` are opposites — positive vs. limitation/risk; do not treat every edge as "support".
- Do not treat `highlight` as the final conclusion, `weak_point` as positive evidence, or `subproblem` as supporting evidence.
- Edge `p1`/`p2` are model/graph internal parameters — **do not show as user-facing confidence**.
- `reasoning_steps.steps` is best shown as node detail, not expanded into multiple main-graph nodes by default.

---

## Worked example: verify and trace a scientific conclusion

> Idea: use `/search` (`reasoning_only=true`) to find a conclusion backed by a reasoning chain, then use `/claims/{id}/reasoning` to see why it holds.

```python
# 1) Search: only conclusion claims backed by a reasoning chain
res = lkm_data(requests.post(f"{BASE}/search", headers=H, json={
    "query": "perovskite thermal stability at 85 C",
    "keywords": ["FAPbI3", "thermal stability"],
    "retrieval_mode": "hybrid",
    "reasoning_only": True,
    "limit": 10,
}))

# 2) Pick the first traceable conclusion
claim = next((v for v in res["variables"] if v.get("has_reasoning")), None)
if not claim:
    print("No conclusion with a traceable reasoning chain")
else:
    print("Conclusion:", (claim.get("content") or "")[:120])
    # 3) Trace: fetch the reasoning chain for this claim
    chains = lkm_data(requests.get(f"{BASE}/claims/{claim['id']}/reasoning",
                                   headers=H, params={"format": "graph"}))
    for c in chains["reasoning_chains"]:
        print("Source paper:", c["paper"]["en_title"])
        for n in c["graph"]["nodes"]:
            print(f"  [{n['kind']}] {(n.get('title') or n['content'])[:80]}")
```

---

## curl examples

```bash
AK="$BOHR_ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v1/lkm"

# 1. Node search (sort_by optional, default comprehensive; filters.paper_ids/dois optional to restrict papers, ≤50 each)
curl -s -X POST "$BASE/search" \
  -H "Authorization: Bearer $AK" -H "Content-Type: application/json" \
  -d '{"query":"perovskite thermal stability","keywords":["FAPbI3","Cs doping"],"retrieval_mode":"hybrid","sort_by":"comprehensive","filters":{"paper_ids":["811977903947382784"],"dois":["10.1038/s41586-021-03381-x"]},"limit":20}' | jq .

# 2. Reasoning chain search (sort_by optional; filters.paper_ids/dois optional, ≤50 each)
curl -s -X POST "$BASE/reasoning/search" \
  -H "Authorization: Bearer $AK" -H "Content-Type: application/json" \
  -d '{"query":"infer phase stability from XRD","keywords":["powder XRD"],"format":"graph","sort_by":"journal","filters":{"dois":["10.1038/s41586-021-03381-x"]},"limit":20}' | jq .

# 3. Paper-level knowledge graph
curl -s -X POST "$BASE/papers/graph" \
  -H "Authorization: Bearer $AK" -H "Content-Type: application/json" \
  -d '{"package_id":"paper:1020661015349559308"}' | jq .

# 4. Single-claim reasoning chain
curl -s -X GET "$BASE/claims/gcn_73e13bb548f847bd/reasoning?format=graph&max_chains=10" \
  -H "Authorization: Bearer $AK" | jq .

# 5. Batch hydration
curl -s -X POST "$BASE/variables/batch" \
  -H "Authorization: Bearer $AK" -H "Content-Type: application/json" \
  -d '{"ids":["gcn_654cd35dcb814a0c","gcn_9523aa7f1fd04d8a"]}' | jq .
```

---

## Error codes

| code | Meaning | Fix |
|------|---------|-----|
| `2000` | Unauthorized | Check `BOHR_ACCESS_KEY` validity and that the request carries `Authorization: Bearer` |
| `290002` | Invalid params | Check `retrieval_mode`/`scopes` values, `keywords` over limit, pagination bounds, `reasoning_only` vs scopes/role conflict, empty/over-100 `ids`, `package_id` format |
| `290001` | Search/query failed | Retry once; if still failing, shorten query or lower limit |
| `290004` | Claim not found | Ensure you pass a global `gcn_...`, not a graph local node ID |
| `290008` | Claim has no reasoning chain | Only call reasoning on conclusions with `has_reasoning=true` |
| `290009` | Query timeout | Retry later, or use a more precise `paper_id`/`package_id` |
| `290011` | Paper not found | Check `paper_id`/`package_id`/`doi`/`title` |
| `290013` | Paper exists but no graph extracted | Show paper metadata and note no structured graph yet |

---

## Pairs well with

> For chaining between LKM endpoints, see "How the endpoints connect" and the "Worked example" above. This section lists cross-skill pairings only.

- **lkm** after verifying/tracing a conclusion → **bohrium-paper-search** for the original full text
- **lkm** after locating a specific paper → **bohrium-pdf-parser** to parse a single PDF
- **lkm** batch-hydration / graph results → **bohrium-knowledge-base** to archive
