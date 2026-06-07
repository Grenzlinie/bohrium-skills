---
name: bohrium-wiki
description: "Browse and search Bohrium SciencePedia (百科) via open.bohrium.com. Use when: user asks about finding scientific topics, reading encyclopedia-style entries, browsing by major/level/field hierarchy, or looking up a specific concept's article. NOT for: paper search (use bohrium-paper-search), knowledge base management (use bohrium-knowledge-base)."
---

# SKILL: Bohrium SciencePedia (百科)

## 概述

通过 `open.bohrium.com` 的 `/v1/literature-sage/wiki_v2/*` 端点访问 **Bohrium 百科**——一个科学主题的百科索引，按 `major` (大类) → `level` (分级) → `field` (领域) → `topic` (词条) 层级组织。

**典型场景**：

- 快速了解某个科学名词的定义（比 web-search 更聚焦于"百科条目"）
- 按学科分类浏览（如材料科学下面的所有子领域）
- 查询词条的正文（简介 / 应用 / 背景等段落）

**不适用**：

- 搜论文 → `bohrium-paper-search`
- 管理自己的知识库 → `bohrium-knowledge-base`

**无 CLI 支持** — 通过 HTTP API 操作。

## 认证配置

```json
"bohrium-wiki": {
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
BASE = "https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2"
H = {"Authorization": f"Bearer {AK}", "Content-Type": "application/json"}

# 可选的全局默认参数
DEFAULTS = {"language": "en-US", "style": "Feynman"}
# language: "en-US" / "zh-CN"
# style: "Feynman" 风格通俗，或其他风格
```

---

## Action 概览

| Action | 方法 | 用途 |
|--------|------|------|
| `info` | GET | 获取 SciencePedia 基础信息 |
| `major_levels` | POST | 列出所有大类及其分级 |
| `get_wiki_index` | POST | 给定 nodeId 或 fieldId，获取索引 |
| `get_level_wiki_index` | POST | 列出指定 `node_types` 下的所有节点 |
| `search_index_name` | POST | 按关键词搜索词条索引 |
| `level_fields` | POST | 在一组 level 节点下列出领域 |
| `article` | POST | 获取某个节点/词条的正文 |

---

## 1. 基础信息 — `info`

```python
r = requests.get(f"{BASE}/info", headers={"Authorization": f"Bearer {AK}"})
print(r.json())
```

---

## 2. 大类与分级 — `major_levels`

```python
r = requests.post(f"{BASE}/major_levels", headers=H, json={**DEFAULTS})
for m in r.json().get("majors", []):
    levels = ", ".join(l["name"] for l in m.get("levels", []))
    print(f"- {m['name']} [{m['node_id']}]  levels: {levels}")
```

---

## 3. 搜索词条 — `search_index_name`

```python
r = requests.post(f"{BASE}/search_index_name", headers=H, json={
    "name": "graphene",
    "node_types": ["field"],   # 过滤节点类型：major / level / field / topic
    "style": "Feynman",
})
for i, n in enumerate(r.json().get("wiki_indices", []), 1):
    print(f"[{i}] [{n['node_type']}] {n['node_name']}  id={n['node_id']}")
```

---

## 4. 某一分级下的所有节点 — `get_level_wiki_index`

```python
r = requests.post(f"{BASE}/get_level_wiki_index", headers=H, json={
    "node_types": ["major", "level"],
    **DEFAULTS,
})
for n in r.json().get("wiki_indices", [])[:50]:
    print(f"[{n['node_type']}] {n['node_name']}  ({n['node_id']})")
```

---

## 5. 获取词条索引 — `get_wiki_index`

```python
r = requests.post(f"{BASE}/get_wiki_index", headers=H, json={
    "node_id": "NODE_ID_HERE",
    # 或 "field_id": "FIELD_ID_HERE"
    **DEFAULTS,
})
print(r.json())
```

---

## 6. 批量列出 level 下的领域 — `level_fields`

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

## 7. 获取词条正文 — `article`

```python
r = requests.post(f"{BASE}/article", headers=H, json={
    "node_id": "NODE_ID",         # 或 "entry_id": "ENTRY_ID"
    **DEFAULTS,
})
doc = r.json().get("document", {})
print(f"# {doc.get('article_name')}")
print(doc.get("main_content", "")[:2000])
```

**常用字段**：`document.article_name` / `document.main_content` / `document.applications` / `document.seo_title`。

---

## curl 示例

```bash
AK="$BOHR_ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2"

# 按关键词搜词条
curl -s -X POST "$BASE/search_index_name" \
  -H "Authorization: Bearer $AK" -H "Content-Type: application/json" \
  -d '{"name":"graphene","node_types":["field"],"style":"Feynman"}' \
  | jq '.wiki_indices[] | {node_name, node_type, node_id}'
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `No matches for "..."` | 关键词在索引里不存在 | 换近义词；打开 `node_types` 为 `["field","topic","major","level"]` 扩大搜索 |
| `article` 返回空 | nodeId/entryId 错或该节点无正文 | 先用 `search_index_name` 拿到正确的 `node_id` |
| 结果全是英文（或全是中文） | `language` 不对 | 指定 `"language": "en-US"` 或 `"zh-CN"` |

## 搭配使用

- **wiki** 找某个概念的基础解释 → **paper-search** 深入某个具体方向
- **wiki** 浏览学科目录（`major_levels`）→ 选定 field → **scholar** 找代表学者
