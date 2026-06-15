---
name: bohrium-wiki
description: "Browse and search Bohrium SciencePedia (百科) via open.bohrium.com. Use when: user asks about finding scientific topics, reading encyclopedia-style entries, browsing by major/level/field hierarchy, or looking up a specific concept's article. NOT for: paper search (use bohrium-paper-search), knowledge base management (use bohrium-knowledge-base)."
---

# SKILL: Bohrium SciencePedia (百科)

## 概述

通过 `open.bohrium.com` 的 `/v2/literature-sage/wiki_v2/*` 端点访问 **Bohrium 百科**——一个科学主题的百科索引，按 `major` (大类) → `level` (分级) → `field` (领域) → `topic` (词条) 层级组织（一个 `topic` 即一篇文章/词条）。

> **两个 Host，各司其职**：调用 **API** 用 `open.bohrium.com`；给人看的**可点击阅读链接**用 `https://www.bohrium.com`（见[构造页面链接](#构造页面链接)）。二者是不同的 Host——不要把 API URL 直接发给用户。

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
BASE = "https://open.bohrium.com/openapi/v2/literature-sage/wiki_v2"
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

## 如何选择 Action（意图 → Action）

把用户的诉求映射到正确的调用。大多数流程都是：**先拿到 id → 再取内容**。

| 用户想要…… | 用 | 拿到 |
|-----------|----|------|
| “有哪些学科 / 大类？”（树的顶层） | `major_levels` | 大类及其 `node_id`、分级 |
| “某大类/分级下有哪些领域？” | `level_fields`（批量分页）或 `get_level_wiki_index`（按 `node_types`） | 领域行 / 节点 |
| “找关于 **X** 的词条或领域” | `search_index_name` | 含 `node_id`、`node_type`，领域节点带 `field_id` |
| “这个领域的大纲 / 有哪些词条？” | `get_wiki_index`（`field_id` 或 `node_id`） | 词条树，每个词条带 `entry_id` |
| “解释 / 给我 **X** 的正文” | `article`（`entry_id` 或 `node_id`） | `document.article_name` + `main_content` + …… |
| “服务是否可用 / 基础信息” | `info` | 服务信息 |

**经验法则**：还没有 id 就先用 `search_index_name`；用户在浏览学科则从 `major_levels` 开始。

## 工作流

### A. 解释一个概念（最常见）

1. `search_index_name`，传 `{"name": "<概念>", "node_types": ["field","topic"]}` → 取最佳命中的 `node_id`（如有 `entry_id`/`field_id` 一并记下）。
2. `article` 传该 id → 概括 `document.main_content`。
3. 返回解释 **并附上**阅读链接（见[构造页面链接](#构造页面链接)）。

### B. 浏览一个学科

1. `major_levels` → 选定大类/分级。
2. `level_fields`（传该 level 的 `node_id`）→ 列出领域。
3. `get_wiki_index` 传 `field_id` → 列出词条；为领域附 `course_url`，为每个词条附 `article_url`。

### C. 为某领域规划学习路径

1. 用 `search_index_name`（`node_types: ["field"]`）定位领域。
2. `get_wiki_index` → 按树顺序读取词条。
3. 以 基础 → 核心 → 进阶 呈现，每个词条都带链接。

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
BASE="https://open.bohrium.com/openapi/v2/literature-sage/wiki_v2"

# 按关键词搜词条
curl -s -X POST "$BASE/search_index_name" \
  -H "Authorization: Bearer $AK" -H "Content-Type: application/json" \
  -d '{"name":"graphene","node_types":["field"],"style":"Feynman"}' \
  | jq '.wiki_indices[] | {node_name, node_type, node_id}'
```

---

## 构造页面链接

每当你把词条或领域展示给人看时，都要附上 `https://www.bohrium.com` 上的可点击阅读链接（**不是** API host）。这才是让回答对人有用的关键。

- **页面 Host**：`https://www.bohrium.com`
- **风格段**：`Feynman → feynman`，`Hardcore → hardcore`
- **语言前缀**：`zh-CN` → 无前缀；`en-US` → 加前缀 `/en`
- 动态 id 需 **URL 编码**。

| 链接 | 模板 | id 来源 |
|------|------|---------|
| 文章（词条） | `{lang}/sciencepedia/{style}/{entry_id}` | `get_wiki_index` 词条节点的 `entry_id`（或你传给 `article` 的 `entry_id`） |
| 领域（课程） | `{lang}/sciencepedia/field/{style}/{field_id}` | `search_index_name` 领域结果 / `level_fields` 的 `field_id` |

```text
文章（en, Feynman）： https://www.bohrium.com/en/sciencepedia/feynman/<entry_id>
领域（zh, Feynman）： https://www.bohrium.com/sciencepedia/field/feynman/solid_state_physics
```

> 本 skill 只开放文章/领域阅读，没有关键词（keyword）页面链接。

## 回答规范

- 优先**教学式**回答：定义 → 直觉 → 要点 → 在知识树中的位置。
- 凡是提到的词条或领域，都附上阅读链接（`article_url` / `course_url`）。
- 若所请求的 `language`/`style` 无结果，按序回退：同语言换另一风格 → `zh-CN`+`Feynman` → `en-US`+`Feynman`，并告知用户已切换。
- API 失败要如实说明；无结果时给出近义词建议和一个备选语言/风格。

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `No matches for "..."` | 关键词在索引里不存在 | 换近义词；打开 `node_types` 为 `["field","topic","major","level"]` 扩大搜索 |
| `article` 返回空 | nodeId/entryId 错或该节点无正文 | 先用 `search_index_name` 拿到正确的 `node_id` |
| 结果全是英文（或全是中文） | `language` 不对 | 指定 `"language": "en-US"` 或 `"zh-CN"` |
| 阅读链接拼到了 `open.bohrium.com` 上 | 混淆了 API host 与页面 host | 页面链接用 `https://www.bohrium.com`（见“构造页面链接”） |

## 搭配使用

- **wiki** 找某个概念的基础解释 → **paper-search** 深入某个具体方向
- **wiki** 浏览学科目录（`major_levels`）→ 选定 field → **scholar** 找代表学者
