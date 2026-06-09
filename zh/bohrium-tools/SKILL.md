---
name: bohrium-tools
description: "浏览与检索 Bohrium 科学工具库（Tools），通过 open.bohrium.com 访问。Use when: 用户需要按领域/子领域浏览科学计算工具、按关键词混合检索工具、查看某个工具的详情（GitHub 指标、教程、关联词条等）。NOT for: 论文检索（用 bohrium-paper-search）、百科词条（用 bohrium-wiki）、知识库管理（用 bohrium-knowledge-base）。"
---

# SKILL: Bohrium 科学工具库（Tools）

## 概述

通过 `open.bohrium.com` 的 `/v2/literature-sage/tool/*` 端点访问 **Bohrium 科学工具库**——一个按 `domain`(领域) → `subdomain`(子领域) → `tool`(工具) 层级组织的科学计算软件/工具目录，并提供混合检索（BM25 + 向量召回）能力。

**典型场景**：

- 浏览某个领域下的工具（如分子动力学领域下的所有工具）
- 用自然语言 + 关键词混合检索最匹配的工具
- 查看某个工具的详细信息（简介、GitHub star/fork、教程、关联词条、Docker 镜像、MCP 地址等）

**不适用**：

- 搜论文 → `bohrium-paper-search`
- 查百科词条 → `bohrium-wiki`
- 管理自己的知识库 → `bohrium-knowledge-base`

**无 CLI 支持** — 通过 HTTP API 操作。

## 认证配置

```json
"bohrium-tools": {
  "enabled": true,
  "apiKey": "YOUR_BOHR_ACCESS_KEY",
  "env": {
    "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY"
  }
}
```

## 通用代码模板

```python
import os, requests

AK = os.environ["BOHR_ACCESS_KEY"]
BASE = "https://open.bohrium.com/openapi/v2/literature-sage/tool"

# 语言通过 Content-Language 头控制：en-us / zh-cn
H = {
    "Authorization": f"Bearer {AK}",
    "Content-Type": "application/json",
    "Content-Language": "en-us",   # 或 "zh-cn"
}

# 所有响应都包了一层信封：{"code": 0, "data": {...}, "trace_id": "..."}。
# 真正的数据（items / tools / total_num / ...）都在 "data" 里，务必先解包。
def data(r):
    r.raise_for_status()
    body = r.json()
    if isinstance(body, dict) and body.get("code") not in (0, None) and "data" not in body:
        raise RuntimeError(f"API error code={body.get('code')} msg={body.get('message')}")
    return body.get("data", body) if isinstance(body, dict) else body
```

> **语言说明**：绝大多数接口的展示语言由 HTTP 头 `Content-Language`(`en-us`/`zh-cn`) 决定，缺省时回退为英文 `en-US`。但 `search/hybrid` 与 `search/subdomain` 这两个检索接口**必须**指定语言——请求体里传 `language`(`en-US`/`zh-CN`) 或带上 `Content-Language` 头，二者至少其一；都不传会报 `language is required`，不会回退。

---

## Action 概览

| Action | 方法 | 路径 | 用途 |
|--------|------|------|------|
| `domain` | GET | `/domain` | 列出所有工具领域 |
| `domain/summary` | GET | `/domain/summary` | 工具总数统计 |
| `subdomain` | POST | `/subdomain` | 列出领域下的子领域（分页） |
| `subdomain/detail` | POST | `/subdomain/detail` | 获取子领域详情 |
| `list` | POST | `/list` | 列出子领域下的工具（标签筛选/排序/分页） |
| `detail` | GET | `/detail` | 按 `tool_unique_key` 获取工具详情 |
| `tags` | POST | `/tags` | 获取一组子领域下的标签 |
| `search/hybrid` | POST | `/search/hybrid` | 工具混合检索（文本 + 关键词权重） |
| `search/subdomain` | POST | `/search/subdomain` | 子领域检索 |

---

## 1. 列出领域 — `domain`

```python
r = requests.get(f"{BASE}/domain", headers=H)
for it in data(r).get("items", []):
    print(f"- {it['node_name']}  [{it['node_id']}]  tools={it['tool_num']}")
```

返回字段：`data.items[].node_id` / `node_name` / `tool_num`。

---

## 2. 工具总数 — `domain/summary`

```python
r = requests.get(f"{BASE}/domain/summary", headers=H)
print(data(r).get("total_num"))   # data: {"total_num": 1234}
```

---

## 3. 列出子领域 — `subdomain`

```python
r = requests.post(f"{BASE}/subdomain", headers=H, json={
    "domain_node_ids": ["DOMAIN_NODE_ID"],   # 领域 node_id 列表，可为空表示全部
    "page": 1,
    "page_size": 20,
})
body = data(r)
print("total:", body.get("total"))
for it in body.get("items", []):
    print(f"- {it['node_name']}  [{it['node_id']}]  tools={it['tool_num']}  tags={it.get('tags')}")
```

返回字段：`data.items[].node_id` / `node_name` / `tool_num` / `tags` / `tools[]`(轻量工具：`tool_unique_key`/`tool_name`/`avatar_url`)；分页 `data.total` / `page` / `pageSize`。

---

## 4. 子领域详情 — `subdomain/detail`

```python
r = requests.post(f"{BASE}/subdomain/detail", headers=H, json={
    "subdomain_node_id": "SUBDOMAIN_NODE_ID",
})
print(data(r))   # data: {"node_id": "...", "node_name": "..."}
```

---

## 5. 子领域下的工具列表 — `list`

```python
r = requests.post(f"{BASE}/list", headers=H, json={
    "subdomain_node_id": "SUBDOMAIN_NODE_ID",   # 必填
    "tag_ids": [],            # 可选：按标签 id 过滤
    "sort_by": "star_count",  # 可选排序字段，如 star_count / last_commit_time
    "sort_type": "desc",      # asc / desc
    "page": 1,
    "page_size": 10,
})
body = data(r)
print("total:", body.get("total"))
for it in body.get("items", []):
    print(f"- {it['name']}  ★{it['star_count']}  key={it['tool_unique_key']}")
    print(f"    {it.get('profile','')[:120]}")
```

返回 `data.items[]` 关键字段：`id` / `name` / `profile` / `tags` / `star_count` / `related_entry_count` / `last_commit_time` / `avatar_url` / `tool_unique_key`。

---

## 6. 工具详情 — `detail`

```python
r = requests.get(f"{BASE}/detail", headers=H, params={
    "tool_unique_key": "TOOL_UNIQUE_KEY",   # 必填
})
d = data(r)
print(f"# {d['name']}  ★{d['star_count']} / fork {d['fork_count']}")
print("repo:", d.get("repo_url"))
print(d.get("overview", "")[:2000])
```

返回 `GetToolDetailResponse` 关键字段：`name` / `profile` / `version` / `star_count` / `fork_count` / `watch_count` / `key_points` / `overview` / `tutorial` / `related_entry_list` / `primary_language` / `license` / `mcp_url` / `docker_image_uri` / `repo_url` / `help_urls` / `sub_domains` / `tags`。

---

## 7. 子领域标签 — `tags`

```python
r = requests.post(f"{BASE}/tags", headers=H, json={
    "subdomain_node_ids": ["SUBDOMAIN_NODE_ID1", "SUBDOMAIN_NODE_ID2"],   # 必填
})
for it in data(r).get("items", []):
    print(f"- {it['tag_name']}  [{it['tag_id']}]")
```

---

## 8. 工具混合检索 — `search/hybrid`

用自然语言 `text` + 关键词权重 `keywords`(关键词→权重) 做 BM25 + 向量的混合召回。

```python
r = requests.post(f"{BASE}/search/hybrid", headers=H, json={
    "text": "molecular dynamics simulation engine with GPU support",
    "keywords": {"molecular dynamics": 1.0, "GPU": 0.6},  # 必填：关键词→权重
    "language": "en-US",      # 必须：与 Content-Language 头二选一，都不传会报 language is required
    "k": 50,                  # 可选；默认 100，最大 500
    "return_level": "",       # 可选：控制返回粒度
})
body = data(r)
print("total:", body.get("total"))
for t in body.get("tools", []):
    score = t.get("score")
    score_str = f"{score:.3f}" if isinstance(score, (int, float)) else "-"   # score 可能为 null
    print(f"- {t['tool_name']}  score={score_str}  key={t.get('tool_unique_key')}")
```

返回 `data.tools[]` 关键字段：`tool_id` / `tool_name` / `tool_unique_key` / `domains` / `subdomains` / `tags` / `profile` / `repo_url` / `score` / `matched_chunks`。

---

## 9. 子领域检索 — `search/subdomain`

```python
r = requests.post(f"{BASE}/search/subdomain", headers=H, json={
    "text": "protein structure prediction",
    "language": "en-US",   # 必须：与 Content-Language 头二选一，都不传会报 language is required
})
for s in data(r).get("subdomains", []):
    print(f"- {s['node_display_name']}  [{s['node_id']}]")
```

---

## curl 示例

```bash
AK="$BOHR_ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v2/literature-sage/tool"

# 工具混合检索（数据在 .data 下）
curl -s -X POST "$BASE/search/hybrid" \
  -H "Authorization: Bearer $AK" \
  -H "Content-Type: application/json" \
  -H "Content-Language: en-us" \
  -d '{"text":"molecular dynamics simulation","keywords":{"molecular dynamics":1.0},"k":20}' \
  | jq '.data.tools[] | {tool_name, score, tool_unique_key}'

# 列出领域
curl -s "$BASE/domain" \
  -H "Authorization: Bearer $AK" -H "Content-Language: en-us" \
  | jq '.data.items[] | {node_name, node_id, tool_num}'
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 检索结果全英文（或全中文） | `Content-Language` / `language` 不对 | 设置头 `Content-Language: zh-cn` 或在检索体内传 `"language":"zh-CN"` |
| `search/hybrid` 报 `text is required` | 缺少 `text` | `text` 与 `keywords` 均为必填 |
| `search/hybrid` / `search/subdomain` 报 `language is required` | 既没传请求体 `language`，也没带 `Content-Language` 头 | 请求体加 `"language":"en-US"`（或 `zh-CN`），或带上 `Content-Language: en-us` 头 |
| `k` 过大被截断 | `search/hybrid` 的 `k` 上限 500 | 控制在 500 以内 |
| `list` 报 `subdomain_node_id` 错 | 缺少必填的子领域 id | 先用 `subdomain` 或 `search/subdomain` 拿到 `node_id` |

## 搭配使用

- **tools** 检索/浏览工具（`domain` → `subdomain` → `list` → `detail`）
- 先用 **wiki** / **paper-search** 了解某个方向，再用 **tools** 找对应的实现工具
- 用 `search/hybrid` 做自然语言找工具，用 `search/subdomain` 定位最匹配的子领域
