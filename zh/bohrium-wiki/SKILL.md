---
name: bohrium-wiki
description: "Search and read Bohrium SciencePedia (科学百科) via open.bohrium.com. Use when the user wants to: look up / explain a scientific term and get a reading link (搜词条/关键词), browse what disciplines·fields·courses exist (有哪些领域和课程), get a course's chapter outline and knowledge list (课程章节与知识点), or explore the knowledge graph around a topic (主题相关的知识图谱). NOT for: paper search (use bohrium-paper-search), managing your own knowledge base (use bohrium-knowledge-base), or the LKM reasoning graph (use bohrium-lkm)."
---

# SKILL: Bohrium 科学百科（SciencePedia）

一个面向科学概念的百科。这个 skill 把它包装成 **4 件你能直接做的事**：

1. **搜一个词** → 拿到简介 + 可点击的阅读链接（自动覆盖「词条」和「关键词」，你**不用**向用户区分二者）。
2. **看百科里有哪些领域和课程**（按学科浏览）。
3. **给定一个课程** → 拿到它的章节结构和知识点列表。
4. **从一个主题出发** → 拿到它和相关概念组成的知识图谱。

> **两个 Host，别混用**：调 **API** 用 `open.bohrium.com`；给人看的**阅读链接**用 `https://www.bohrium.com`（见[拼阅读链接](#拼阅读链接)）。不要把 API 地址发给用户。

**不适用**：搜论文 → `bohrium-paper-search`；管理自己的知识库 → `bohrium-knowledge-base`；大知识模型推理图谱 → `bohrium-lkm`。

**无 CLI** — 全部通过 HTTP API。

---

## 认证配置

```json
"bohrium-wiki": {
  "enabled": true,
  "apiKey": "YOUR_BOHR_ACCESS_KEY",
  "env": { "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY" }
}
```

## 通用模板（复制即用）

```python
import os, requests
from urllib.parse import quote

AK = os.environ["BOHR_ACCESS_KEY"]
BASE = "https://open.bohrium.com/openapi/v2/literature-sage/wiki_v2"
H = {"Authorization": f"Bearer {AK}", "Content-Type": "application/json"}

# 几乎所有接口都要带这两个参数：
DEFAULTS = {"language": "en-US", "style": "Feynman"}
# language: "en-US" 或 "zh-CN"
# style:    "Feynman"（通俗易懂）或 "Hardcore"（硬核学术）

def data(resp):
    """统一解包：响应是 {"code":0,"data":{...}}，错误时 code!=0。"""
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") not in (0, None):
        raise RuntimeError(f"API error code={body.get('code')}: {body.get('message') or body}")
    return body.get("data", body)
```

## 三个最少必要的概念（其余 jargon 都可忽略）

| 概念 | 是什么 | 怎么给用户 |
|------|--------|-----------|
| **词条 / 主题（topic）** | 一篇完整的百科文章 | 用 `entry_id` 拼文章链接 |
| **关键词（keyword）** | 一个更小的概念卡片 | 用 `keyword_id` 拼关键词链接 |
| **课程 / 领域（field）** | 一组词条组成的「课」 | 用 `field_id` 拼课程链接 |

> 搜索时这三者会混在一起返回。**对用户而言它们都是「百科条目」**——直接给标题 + 简介 + 链接即可，不必解释类型差异。

---

## 任务 1：搜一个词，拿简介和阅读链接

**首选一个接口搞定**：`POST /search/universal`。它一次返回相关的「词条 + 关键词」（在 `articles` 里）和相关「课程」（在 `fields` 里），每条都带高亮简介。

```python
d = data(requests.post(f"{BASE}/search/universal", headers=H,
                       json={"text": "graphene", **DEFAULTS}))

for a in d["articles"]:                       # 词条与关键词混合，按相关度排好序
    link = build_read_url(a["type"], a["id"], **DEFAULTS)   # 见“拼阅读链接”
    snippet = a["matched_elements"][0]["content"] if a.get("matched_elements") else ""
    print(a["article_name"], "→", link)
    print("  ", snippet.replace("<em>", "").replace("</em>", ""))   # 去掉高亮标签

for f in d["fields"]:                         # 相关课程（可选展示）
    print("课程：", f["node_name"], "→", course_url(f["field_id"], **DEFAULTS))
```

`articles[]` 每项关键字段：
- `type`：`"article"`（词条/主题）或 `"keyword"`（关键词）——**决定用哪种链接**。
- `id`：词条是 `entry_id`，关键词是 `keyword_id`。
- `article_name`：标题。
- `matched_elements[].content`：命中的高亮片段，可直接当**简介**（含 `<em>` 高亮标签，展示前去掉）。

### 想要更完整的简介 / 全文

`/search/universal` 给的是检索片段。要正文，再按类型取详情：

```python
# 词条（主题文章）全文
doc = data(requests.post(f"{BASE}/article", headers=H,
                         json={"entry_id": "<entry_id>", **DEFAULTS}))["document"]

# 关键词全文
doc = data(requests.post(f"{BASE}/keyword", headers=H,
                         json={"keyword_id": "<keyword_id>", **DEFAULTS}))["document"]

# doc 常用字段：
#   article_name    标题
#   seo_description 一句话简介（最适合做摘要）
#   definition      定义
#   key_points      要点
#   main_content    正文（Markdown）
#   applications    应用
```

> ⚠️ `article` / `keyword` 偶尔返回 `code=250002`（内容按需生成、当前语言/风格下还没有）。这时**回退**用搜索结果里的 `matched_elements` 片段，或换一个 `style` / `language` 再试。

---

## 任务 2：看百科里有哪些领域和课程

**按学科浏览**：先拿大类与分级，再列某个分级下的课程。

```python
# 1) 顶层结构：大类(major) → 分级(level)
ml = data(requests.post(f"{BASE}/major_levels", headers=H, json={**DEFAULTS}))
for m in ml["majors"]:
    levels = "、".join(l["name"] for l in m["levels"])
    print(m["name"], "｜分级：", levels)

# 2) 列出某些分级下的课程(field)
level_ids = [lv["node_id"] for m in ml["majors"] for lv in m["levels"]]
lf = data(requests.post(f"{BASE}/level_fields", headers=H,
                        json={"node_ids": level_ids[:5], "page_num": 1, "page_size": 20, **DEFAULTS}))
for it in lf["items"]:
    f = it["field"]
    print(f'{it["major"]["name"]} / {it["level"]["name"]} / {f["name"]}'
          f'（{it.get("topic_count", 0)} 个知识点）→', course_url(f["field_id"], **DEFAULTS))
```

- `major_levels` 返回 `majors[]`，每个含 `name` 和 `levels[]`（`name` + `node_id`）。
- `level_fields` 返回分页 `items[]`（`total` 为总数），每项含 `major` / `level` / `field`、`topic_count`、以及若干示例 `topics`；其中 `field` 带 `node_id`、`name`、`seo_title` 和 **`field_id`**。

> 课程**阅读链接**直接用 `field.field_id` 拼（`course_url(...)`，见[拼阅读链接](#拼阅读链接)）；想要章节结构就把 `field_id`（或 `field.node_id`）传给任务 3 的 `get_wiki_index`。

---

## 任务 3：给定课程，拿章节结构和知识点列表

两步：用课程名找到课程 → 用课程取整棵章节树。

```python
# 1) 用课名定位课程（拿到 field_id）
s = data(requests.post(f"{BASE}/search/universal", headers=H,
                       json={"text": "Solid State Physics", **DEFAULTS}))
field = s["fields"][0]                 # 含 node_id、field_id、node_name

# 2) 取章节结构 + 知识点（传 field_id，或传该 field 的 node_id 也行）
tree = data(requests.post(f"{BASE}/get_wiki_index", headers=H,
                          json={"field_id": field["field_id"], **DEFAULTS}))

def walk(nodes, depth=0):
    for n in nodes:
        print("  " * depth, f'[{n["node_type"]}]', n["node_name"])
        if n["node_type"] == "entry":          # 叶子 = 一个知识点（词条）
            print("  " * (depth + 1), "→", topic_url(n["entry_id"], **DEFAULTS))
        walk(n.get("children") or [], depth + 1)

walk(tree["wiki_indices"])
print("总知识点：", tree.get("entry_count"))
```

- 树是 4 层：`field`（课程）→ `category`（大章）→ `chapter`（小节）→ `entry`（知识点/词条）。
- 每个节点：`node_id`、`node_type`、`node_name`；**叶子 `entry` 节点额外带 `entry_id`**（拼阅读链接用）、`snapshot`（AI 速览，适合当一句话摘要）、`seo_title`。
- 顶层还返回 `entry_count` 及 `foundational_entry_count` / `core_entry_count` / `advanced_entry_count`（基础 / 核心 / 进阶知识点数）。

---

## 任务 4：从一个主题出发，拿知识图谱

从某个中心节点（词条或关键词）向外扩展，得到它和相关概念组成的图。

```python
# 1) 先找到中心节点的 id（词条用 entry_id，关键词用 keyword_id）
s = data(requests.post(f"{BASE}/search/universal", headers=H,
                       json={"text": "superconductivity", **DEFAULTS}))
center_id = s["articles"][0]["id"]
# 也可以用图谱内检索直接找节点：
# gs = data(requests.post(f"{BASE}/knowledge_graph/search", headers=H, json={"text": "entropy"}))
# center_id = gs["items"][0]["id"]

# 2) 取图谱（注意：是 GET + query 参数）
g = data(requests.get(f"{BASE}/knowledge_graph", headers=H,
                      params={"id": center_id, **DEFAULTS}))

for n in g["nodes"]:                  # 节点
    link = build_read_url(n["node_type"], n["node_id"], **DEFAULTS)
    print(n["display_name"], f'({n["node_type"]}, 深度{n["depth"]})', "→", link)

for e in g["relationships"]:          # 边
    print(e["src_node_id"], "──", e["relationship"], "──>", e["desc_node_id"],
          f'(权重 {e["weight"]})')
```

- 入参：`id`（必填，中心节点的 `entry_id` 或 `keyword_id`）、`language`、`style`、可选 `skip_cross_domain`（true=只看同领域）。
- `nodes[]`：`node_id`（就是 `entry_id`/`keyword_id`，可直接拼链接）、`node_type`（`entry`/`keyword`）、`display_name`、`description`、`field_name`、`major_name`、`depth`（中心节点为 0）。
- `relationships[]`：`src_node_id` / `desc_node_id`、`relationship`（关系描述）、`relation_type`、`description`、`weight`、`evidence_count`、`is_bidirectional`、`is_cross_domain`。
- `domains[]`：图里涉及的学科（`major_node_id` + `major_name`）。

### 看某个节点 / 某条边的细节

```python
# 单个节点详情
node = data(requests.get(f"{BASE}/knowledge_graph/node", headers=H,
            params={"id": center_id, "node_type": "entry", **DEFAULTS}))

# 单条关系详情（含支撑证据 evidences）
rel = data(requests.get(f"{BASE}/knowledge_graph/relationship", headers=H,
           params={"src_node_id": "A", "desc_node_id": "B", "relation_id": "R", **DEFAULTS}))
```

---

## 动作速查表

| 任务 | 方法 + 路径 | 用途 |
|------|------------|------|
| 搜索（首选） | `POST /search/universal` | 一个词拿到词条 + 关键词 + 相关课程 |
| 词条全文 | `POST /article` | 按 `entry_id`（或 `node_id`）取主题文章正文 |
| 关键词全文 | `POST /keyword` | 按 `keyword_id` 取关键词内容 |
| 学科结构 | `POST /major_levels` | 所有大类及其分级 |
| 课程列表 | `POST /level_fields` | 某些分级下的课程（分页） |
| 课程结构 | `POST /get_wiki_index` | 课程的章节树 + 知识点（叶子带 `entry_id`） |
| 知识图谱 | `GET /knowledge_graph` | 从一个主题/关键词扩展出图谱 |
| 图谱·节点 | `GET /knowledge_graph/node` | 单个节点详情 |
| 图谱·边 | `GET /knowledge_graph/relationship` | 单条关系详情（含证据） |
| 图谱·检索 | `POST /knowledge_graph/search` | 在图谱里按词找节点 |
| （可选）基础信息 | `GET /info` | 词条 / 关键词总量 |
| （可选）名称搜索 | `POST /search_index_name` | 按名字搜节点（如只要 `field`） |

> 所有响应都包了一层 `{"code":0,"data":{...}}`，用上面的 `data()` 解包。`GET` 类用 `params=`，`POST` 类用 `json=`。

---

## 拼阅读链接

凡是展示给人的词条 / 关键词 / 课程，都附上 `https://www.bohrium.com` 上的阅读链接（**不是** API host）。

规则：
- **语言前缀**：`zh-CN` → 无前缀；`en-US` → 加 `/en`。
- **风格段**：小写，`Feynman → feynman`、`Hardcore → hardcore`。
- 动态 id 要 **URL 编码**。

| 类型 | 模板 | id 来源 |
|------|------|---------|
| 词条 / 主题 | `{前缀}/sciencepedia/{style}/{entry_id}` | 搜索结果 `type=article` 的 `id`；课程树叶子的 `entry_id`；图谱里 `node_type=entry` 的 `node_id` |
| 关键词 | `{前缀}/sciencepedia/{style}/keyword/{keyword_id}` | 搜索结果 `type=keyword` 的 `id`；图谱里 `node_type=keyword` 的 `node_id` |
| 课程 / 领域 | `{前缀}/sciencepedia/field/{style}/{field_id}` | `/search/universal` 的 `fields[].field_id`，或 `/level_fields` 的 `items[].field.field_id` |

```python
def _site(language):
    return "https://www.bohrium.com/en" if language == "en-US" else "https://www.bohrium.com"

def topic_url(entry_id, language="en-US", style="Feynman"):
    return f"{_site(language)}/sciencepedia/{style.lower()}/{quote(str(entry_id))}"

def keyword_url(keyword_id, language="en-US", style="Feynman"):
    return f"{_site(language)}/sciencepedia/{style.lower()}/keyword/{quote(str(keyword_id))}"

def course_url(field_id, language="en-US", style="Feynman"):
    return f"{_site(language)}/sciencepedia/field/{style.lower()}/{quote(str(field_id))}"

def build_read_url(node_type, node_id, language="en-US", style="Feynman"):
    # node_type: "keyword" -> 关键词页；其余（article/entry）-> 词条页
    if node_type == "keyword":
        return keyword_url(node_id, language, style)
    return topic_url(node_id, language, style)
```

示例：
```text
词条（en, Feynman）：    https://www.bohrium.com/en/sciencepedia/feynman/<entry_id>
关键词（zh, Feynman）：  https://www.bohrium.com/sciencepedia/feynman/keyword/<keyword_id>
课程（en, Hardcore）：   https://www.bohrium.com/en/sciencepedia/field/hardcore/<field_id>
```

---

## curl 示例

```bash
AK="$BOHR_ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v2/literature-sage/wiki_v2"

# 统一搜索
curl -s -X POST "$BASE/search/universal" \
  -H "Authorization: Bearer $AK" -H "Content-Type: application/json" \
  -d '{"text":"graphene","language":"en-US","style":"Feynman"}' \
  | jq '.data.articles[] | {type, id, article_name}'

# 知识图谱（GET + query）
curl -s -G "$BASE/knowledge_graph" \
  -H "Authorization: Bearer $AK" \
  --data-urlencode "id=<entry_id_or_keyword_id>" \
  --data-urlencode "language=en-US" --data-urlencode "style=Feynman" \
  | jq '.data | {nodes: (.nodes|length), edges: (.relationships|length)}'
```

---

## 回答规范

- **搜索类**：直接给「标题 + 一句话简介 + 阅读链接」的列表，不用向用户解释「词条 / 关键词」的区别。
- **解释概念**：定义 → 直觉 → 要点，并附该条目的阅读链接。
- **课程结构**：按 章 → 节 → 知识点 的层级呈现，每个知识点带链接；可按基础 / 核心 / 进阶分组（用 `*_entry_count`）。
- **知识图谱**：先讲中心节点，再列最相关的几条关系（按 `weight` 排），需要展开时再调 `node` / `relationship` 详情。
- 凡是提到的条目都附阅读链接。指定的 `language`/`style` 无结果时，按序回退：同语言换另一风格 → `zh-CN`+`Feynman` → `en-US`+`Feynman`，并告知已切换。
- API 失败要如实说明；无结果时给近义词建议和一个备选语言 / 风格。

## 常见问题

| 现象 | 原因 | 解决 |
|------|------|------|
| 搜不到 | 词不在索引里 | 换近义词；或用 `/search_index_name` 放开 `node_types` |
| `article`/`keyword` 返回 `250002` | 该语言/风格下内容尚未生成 | 回退到搜索片段，或换 `style`/`language` 重试 |
| 结果全英文（或全中文） | `language` 不对 | 指定 `"language":"en-US"` 或 `"zh-CN"` |
| 知识图谱为空 | `id` 不是有效的 `entry_id`/`keyword_id`，或该节点无邻居 | 先用 `/search/universal` 或 `/knowledge_graph/search` 拿到正确 id |
| 阅读链接拼到了 `open.bohrium.com` | 混淆了 API host 与页面 host | 页面链接用 `https://www.bohrium.com`（见[拼阅读链接](#拼阅读链接)） |

## 搭配使用

- **wiki** 拿概念的基础解释 → **bohrium-paper-search** 深入某个方向
- **wiki** 浏览学科目录（`major_levels`）→ 选定课程 → **bohrium-scholar-search** 找代表学者
