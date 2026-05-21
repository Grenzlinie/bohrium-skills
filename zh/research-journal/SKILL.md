---
name: research-journal
description: "Personal research journal with automatic knowledge linking and periodic insight generation. Use when: user wants to record daily research notes, link them to existing knowledge, and get periodic retrospective insights. NOT for: literature review (use literature-review), knowledge base file management (use bohrium-knowledge-base)."
---

# SKILL: 个人研究日志 (Research Journal)

## 概述

个人研究日志是一个**编排型 Skill**，串联知识库、论文搜索和大知识模型三个原子 Skill，帮助研究人员系统性地记录日常研究笔记，并自动完成知识关联、文献补充和周期性回顾洞察。

**组合的原子 Skill：**

| 步骤 | 原子 Skill | 端点 | 功能 |
|------|-----------|------|------|
| 1 | `knowledge-base` | POST `/v1/knowledge/file/search` + 上传流程 | 存储日志条目，自动关联已有知识 |
| 2 | `paper-search` | POST `/v1/paper/rag/pass/keyword` | 为提及的概念自动补充文献引用 |
| 3 | `lkm` | POST `/v1/lkm/search` | 分析条目之间的概念关联 |

**适用场景：**

- 记录每日研究笔记（阅读内容、想法、遇到的问题）
- 自动将新笔记与已有知识条目关联
- 为笔记中提及的概念自动补充相关文献
- 周期性生成回顾总结（反复出现的想法、未解决的问题）

**不适用：**

- 系统性文献综述 -> `literature-review`
- 知识库文件管理（上传/下载/权限） -> `bohrium-knowledge-base`
- 单次论文检索 -> `bohrium-paper-search`
- 科学论断验证 -> `bohrium-lkm`

**无 CLI 支持** -- 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"research-journal": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.ACCESS_KEY` 注入到运行环境。

---

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `entry_text` | string | 是 | -- | 日志正文：今天读了什么、有什么想法、遇到什么问题 |
| `tags` | string[] | 否 | 从正文提取 | 标签列表，如 `["molecular dynamics", "GNN"]` |
| `knowledge_base_id` | int | 是 | -- | 知识库节点 ID（存储日志的目标知识库） |
| `auto_cite` | bool | 否 | `true` | 是否自动补充文献引用 |
| `retrospective` | bool | 否 | `false` | 是否触发周期性回顾（建议每周运行一次） |
| `retrospective_days` | int | 否 | `7` | 回顾时间跨度（天） |

---

## 输出格式

### 1. 结构化日志条目

每条日志存储到知识库后包含以下结构：

| 字段 | 说明 |
|------|------|
| `date` | 日志日期 |
| `entry_text` | 日志正文 |
| `tags` | 标签列表 |
| `linked_entries` | 自动关联的已有条目列表（标题 + 相关度） |
| `auto_citations` | 自动补充的文献引用（DOI、标题、引用数） |
| `concept_connections` | LKM 分析的概念关联 |

### 2. 周期性回顾总结

| 字段 | 说明 |
|------|------|
| `period` | 回顾时间范围 |
| `entry_count` | 期间日志条数 |
| `recurring_themes` | 反复出现的主题/想法 |
| `unresolved_questions` | 仍未解决的问题 |
| `knowledge_growth` | 知识增长概要（新增关联数、新概念数） |
| `suggested_readings` | 基于未解决问题推荐的延伸阅读 |

---

## 质量控制

### 自动关联的准确性

`linked_entries` 的关联**不能仅基于关键词重叠**：
- 关联理由必须具体（如"两条日志都讨论了 X 问题的 Y 方面"）
- 排除仅标签相同但内容无实质关联的条目
- 置信度低的关联（< 0.6 相似度）应标注为"弱关联，仅供参考"

### 文献补充的相关性

`auto_citations` 补充的文献必须与日志内容**直接相关**：
- 不能仅因关键词匹配就推荐（如日志提到"transformer"不应推荐所有含该词的论文）
- 每条推荐必须附 1 句话说明为什么与该日志条目相关

### 禁止的行为

- ❌ 关联已有条目不给出理由
- ❌ 推荐文献与日志内容仅表面相关
- ❌ 周期性回顾只是条目数量统计而无 insight（如"本周记录 5 条"不是有用的回顾）

---

## 工作流程图

```
输入: entry_text, tags, knowledge_base_id
        |
        v
+--------------------------------------+
|  步骤 1: 知识库存储与关联              |
|  POST /v1/knowledge/file/search      |
|  -> 搜索已有条目，计算相关性           |
|  -> 上传新条目 (multipart + submit)   |
|  -> 返回自动关联列表                  |
+---------------+-----------------------+
                |
                v
+--------------------------------------+
|  步骤 2: 自动补充文献引用              |
|  POST /v1/paper/rag/pass/keyword     |
|  -> 提取日志中的关键概念              |
|  -> 为每个概念检索相关论文            |
|  -> 返回引用建议列表                  |
+---------------+-----------------------+
                |
                v
+--------------------------------------+
|  步骤 3: 概念关联分析                  |
|  POST /v1/lkm/search                 |
|  -> 分析日志概念在知识图谱中的位置     |
|  -> 发现跨条目的潜在关联              |
|  -> 返回概念连接图                    |
+---------------+-----------------------+
                |
                v
+--------------------------------------+
|  输出: 结构化日志条目                  |
|  -> 已存入知识库                      |
|  -> 自动关联已有条目                  |
|  -> 文献引用已补充                    |
|  -> 概念关联已标注                    |
+--------------------------------------+
                |
                v (可选: retrospective=true)
+--------------------------------------+
|  周期性回顾                            |
|  -> 汇总近 N 天的日志条目              |
|  -> 提取反复出现的主题                 |
|  -> 整理未解决的问题                   |
|  -> 推荐延伸阅读                      |
+--------------------------------------+
```

---

## 通用代码模板

```python
import os, sys, json, hashlib, tempfile, requests, urllib.parse, urllib.request, base64
from datetime import datetime, timedelta

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("ERROR: 请设置环境变量 ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET  = {"accessKey": AK}
```

---

## 步骤 1: 知识库存储与关联

将日志条目存入知识库，同时搜索已有条目找出关联内容。

### Python 示例

```python
def search_existing_entries(knowledge_base_id, query_text, top_k=5):
    """
    在知识库中搜索与当前日志相关的已有条目。

    Args:
        knowledge_base_id: 知识库节点 ID
        query_text: 搜索文本（日志正文或摘要）
        top_k: 返回最相关的条目数量

    Returns:
        关联条目列表
    """
    r = requests.post(
        f"{BASE}/v1/knowledge/file/search",
        headers=HEADERS_JSON,
        json={
            "queryContent": query_text[:500],
            "nodesId": knowledge_base_id,
            "knowledgeBaseId": knowledge_base_id
        }
    )
    r.raise_for_status()
    data = r.json()

    if data.get("code") != 0:
        print(f"  [WARN] 搜索失败: {data.get('message', 'unknown error')}")
        return []

    files = data.get("data", {}).get("Files", [])
    linked = []
    for f in files[:top_k]:
        linked.append({
            "resource_id": f.get("userResourceId"),
            "file_name": f.get("fileName", ""),
            "content_snippet": f.get("content", "")[:200],
            "knowledge_base": f.get("knowledgeBaseName", "")
        })

    print(f"[步骤1a] 找到 {len(linked)} 个相关已有条目")
    for i, entry in enumerate(linked, 1):
        print(f"  {i}. {entry['file_name']}: {entry['content_snippet'][:80]}...")

    return linked


def upload_journal_entry(knowledge_base_id, entry_text, tags, date_str=None):
    """
    将日志条目上传到知识库。

    Args:
        knowledge_base_id: 知识库节点 ID
        entry_text: 日志正文（Markdown 格式）
        tags: 标签列表
        date_str: 日期字符串，默认为今天

    Returns:
        上传结果
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 构造 Markdown 文件内容
    tag_line = ", ".join(f"`{t}`" for t in tags) if tags else "无"
    md_content = (
        f"# 研究日志 {date_str}\n\n"
        f"**日期:** {date_str}\n\n"
        f"**标签:** {tag_line}\n\n"
        f"---\n\n"
        f"{entry_text}\n"
    )

    # 写入临时文件
    file_name = f"journal_{date_str}.md"
    tmp_path = os.path.join(tempfile.gettempdir(), file_name)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    file_size = os.path.getsize(tmp_path)

    # 计算 MD5
    h = hashlib.md5()
    with open(tmp_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    file_md5 = h.hexdigest()

    # 步骤 1: 获取上传凭证
    r = requests.get(
        f"{BASE}/v1/knowledge/file/multipart",
        headers=HEADERS_GET,
        params={
            "fileName": file_name,
            "md5": file_md5,
            "parentId": knowledge_base_id,
            "size": file_size
        }
    )
    r.raise_for_status()
    multipart = r.json().get("data", {})

    if multipart.get("fileExist"):
        print(f"[步骤1b] 文件已存在，注册到知识库...")
        r_submit = requests.post(
            f"{BASE}/v1/knowledge/file/submit",
            headers=HEADERS_JSON,
            json={
                "parentId": knowledge_base_id,
                "fileName": file_name,
                "md5": file_md5,
                "size": file_size,
                "url": multipart.get("path", "")
            }
        )
        return r_submit.json()

    host = multipart["host"]
    path = multipart["path"]
    token = multipart["token"]

    # 步骤 2: 二进制上传
    content_type = "text/markdown; charset=utf-8"
    encoded_name = urllib.parse.quote(file_name, safe="-_.!~*'()")
    storage_param = base64.b64encode(json.dumps({
        "path": path,
        "option": {
            "contentDisposition": (
                f'inline; filename="{encoded_name}"; '
                f"filename*=UTF-8''{encoded_name}"
            ),
            "contentType": content_type,
        },
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).decode("utf-8")

    file_content = open(tmp_path, "rb").read()
    upload_url = host.rstrip("/") + "/api/upload/binary"

    req = urllib.request.Request(upload_url, method="POST", data=file_content)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-Storage-Param", storage_param)
    req.add_header("Content-Type", "application/octet-stream")

    with urllib.request.urlopen(req, timeout=300) as resp:
        upload_result = json.loads(resp.read().decode("utf-8"))

    # 步骤 3: 注册文件到知识库
    final_path = (upload_result.get("data") or {}).get("path") or path
    r_submit = requests.post(
        f"{BASE}/v1/knowledge/file/submit",
        headers=HEADERS_JSON,
        json={
            "parentId": knowledge_base_id,
            "fileName": file_name,
            "md5": file_md5,
            "size": file_size,
            "url": final_path
        }
    )

    result = r_submit.json()
    if result.get("code") == 0:
        print(f"[步骤1b] 日志 {file_name} 已存入知识库")
    else:
        print(f"[步骤1b] 上传结果: {result}")

    # 清理临时文件
    os.remove(tmp_path)
    return result
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 搜索已有条目（查找关联）
curl -s -X POST "https://open.bohrium.com/openapi/v1/knowledge/file/search" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "queryContent": "GNN force field training convergence issues",
    "nodesId": 456,
    "knowledgeBaseId": 456
  }'
```

---

## 步骤 2: 自动补充文献引用

提取日志中的关键概念，为每个概念检索相关论文，补充引用信息。

### Python 示例

```python
def extract_keywords(entry_text, max_keywords=5):
    """
    从日志正文中提取关键概念。

    简单实现：按行扫描，提取加粗/标记的术语和高频名词短语。
    实际使用时可结合 LLM 进行更智能的提取。

    Args:
        entry_text: 日志正文
        max_keywords: 最大关键词数量

    Returns:
        关键词列表
    """
    # 简单的关键词提取：查找反引号包裹的术语和常见学术短语
    import re

    keywords = []

    # 提取反引号包裹的术语
    backtick_terms = re.findall(r'`([^`]+)`', entry_text)
    keywords.extend(backtick_terms)

    # 提取加粗标记的术语
    bold_terms = re.findall(r'\*\*([^*]+)\*\*', entry_text)
    keywords.extend(bold_terms)

    # 去重并限制数量
    seen = set()
    unique_keywords = []
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if kw_lower not in seen and len(kw_lower) > 2:
            seen.add(kw_lower)
            unique_keywords.append(kw.strip())

    return unique_keywords[:max_keywords]


def auto_supplement_citations(entry_text, keywords=None, top_n=5):
    """
    为日志中提及的概念自动补充文献引用。

    Args:
        entry_text: 日志正文
        keywords: 关键词列表（为 None 则自动提取）
        top_n: 每个概念检索的论文数量

    Returns:
        引用建议列表
    """
    if keywords is None:
        keywords = extract_keywords(entry_text)

    if not keywords:
        print("[步骤2] 未提取到关键概念，跳过文献补充")
        return []

    print(f"[步骤2] 提取到 {len(keywords)} 个关键概念: {keywords}")

    citations = []
    for kw in keywords:
        r = requests.post(
            f"{BASE}/v1/paper/rag/pass/keyword",
            headers=HEADERS_JSON,
            json={
                "words": [kw],
                "question": f"Recent research on {kw}",
                "type": 5,
                "startTime": "",
                "endTime": "",
                "pageSize": top_n
            }
        )

        try:
            r.raise_for_status()
            text = r.text.strip()
            first_line = text.split('\n')[0]
            data = json.loads(first_line)

            if data.get("code") != 0:
                print(f"  [WARN] 检索 '{kw}' 失败: {data.get('message')}")
                continue

            papers = data.get("data", [])
            # 按引用数排序，取最相关的
            papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)

            for p in papers[:3]:
                citations.append({
                    "keyword": kw,
                    "doi": p.get("doi", ""),
                    "title": p.get("enName", ""),
                    "journal": p.get("publicationEnName", ""),
                    "year": p.get("coverDateStart", "")[:4],
                    "citations": p.get("citationNums", 0),
                    "impact_factor": p.get("impactFactor", 0),
                })

            print(f"  '{kw}': 找到 {len(papers)} 篇相关论文")

        except Exception as e:
            print(f"  [WARN] 检索 '{kw}' 异常: {e}")

    # 去重（按 DOI）
    seen_dois = set()
    unique_citations = []
    for c in citations:
        if c["doi"] and c["doi"] not in seen_dois:
            seen_dois.add(c["doi"])
            unique_citations.append(c)

    print(f"[步骤2] 共补充 {len(unique_citations)} 条文献引用")
    return unique_citations
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 为 "GNN force field" 概念搜索相关论文
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["GNN force field"],
    "question": "Recent research on GNN force field",
    "type": 5,
    "startTime": "",
    "endTime": "",
    "pageSize": 5
  }'
```

---

## 步骤 3: 概念关联分析

利用 LKM 知识图谱分析日志中概念之间的关系，发现跨条目的潜在关联。

### Python 示例

```python
def analyze_concept_connections(entry_text, keywords=None):
    """
    利用 LKM 分析日志中概念之间的关联。

    Args:
        entry_text: 日志正文
        keywords: 关键词列表

    Returns:
        概念关联列表
    """
    if keywords is None:
        keywords = extract_keywords(entry_text)

    if not keywords:
        print("[步骤3] 无关键概念，跳过关联分析")
        return []

    connections = []

    # 对每个关键概念进行知识图谱搜索
    for kw in keywords:
        try:
            r = requests.post(
                f"{BASE}/v1/lkm/search",
                headers=HEADERS_JSON,
                json={"query": kw, "limit": 5}
            )
            r.raise_for_status()
            data = r.json()

            kg_nodes = data.get("data", [])
            if not isinstance(kg_nodes, list):
                kg_nodes = [kg_nodes] if kg_nodes else []

            for node in kg_nodes:
                connections.append({
                    "keyword": kw,
                    "node": node,
                    "type": "knowledge_graph"
                })

            print(f"  '{kw}': {len(kg_nodes)} 个知识图谱节点")

        except Exception as e:
            print(f"  [WARN] LKM 搜索 '{kw}' 异常: {e}")

    # 分析关键概念之间的交叉关联
    if len(keywords) >= 2:
        combined_query = " ".join(keywords)
        try:
            r = requests.post(
                f"{BASE}/v1/lkm/search",
                headers=HEADERS_JSON,
                json={"query": combined_query, "limit": 10}
            )
            r.raise_for_status()
            data = r.json()

            cross_nodes = data.get("data", [])
            if not isinstance(cross_nodes, list):
                cross_nodes = [cross_nodes] if cross_nodes else []

            for node in cross_nodes:
                connections.append({
                    "keyword": combined_query,
                    "node": node,
                    "type": "cross_concept"
                })

            print(f"  跨概念关联: {len(cross_nodes)} 个节点")

        except Exception as e:
            print(f"  [WARN] 跨概念分析异常: {e}")

    print(f"[步骤3] 共发现 {len(connections)} 个概念关联")
    return connections
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 单概念知识图谱搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "GNN force field training convergence", "limit": 5}' | python3 -m json.tool

# 跨概念关联搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "GNN force field equivariant neural network energy conservation", "limit": 10}' | python3 -m json.tool
```

---

## 周期性回顾

汇总近 N 天的日志条目，提取反复出现的主题、整理未解决问题并推荐延伸阅读。

### Python 示例

```python
def generate_retrospective(knowledge_base_id, days=7):
    """
    生成周期性回顾总结。

    Args:
        knowledge_base_id: 知识库节点 ID
        days: 回顾天数

    Returns:
        回顾总结字典
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"\n[回顾] 时间范围: {start_date.strftime('%Y-%m-%d')} ~ "
          f"{end_date.strftime('%Y-%m-%d')}")

    # 获取知识库中的日志条目
    r = requests.get(
        f"{BASE}/v1/knowledge/folder/children",
        headers=HEADERS_GET,
        params={
            "folderId": knowledge_base_id,
            "pageNum": 1,
            "pageSize": 100
        }
    )
    r.raise_for_status()
    data = r.json().get("data", {})
    files = data.get("files", [])

    # 过滤时间范围内的日志条目
    journal_files = []
    for f in files:
        fname = f.get("fileName", "")
        if fname.startswith("journal_"):
            # 从文件名提取日期: journal_YYYY-MM-DD.md
            try:
                date_part = fname.replace("journal_", "").replace(".md", "")
                file_date = datetime.strptime(date_part, "%Y-%m-%d")
                if start_date <= file_date <= end_date:
                    journal_files.append(f)
            except ValueError:
                continue

    print(f"[回顾] 找到 {len(journal_files)} 个日志条目")

    if not journal_files:
        print("[回顾] 无日志条目，跳过回顾")
        return None

    # 收集所有日志的关键信息
    all_keywords = []
    all_questions = []
    all_entries_text = []

    for jf in journal_files:
        resource_id = jf.get("nodesId", "")
        # 获取文献详情
        try:
            r = requests.get(
                f"{BASE}/v1/knowledge/file/detail",
                headers=HEADERS_GET,
                params={"resourceId": str(resource_id)}
            )
            r.raise_for_status()
            detail = r.json().get("data", {})

            # 收集摘要和标签
            summary = detail.get("summary", [])
            for s in summary:
                content = s.get("content", "") or s.get("zhContent", "")
                if content:
                    all_entries_text.append(content)

        except Exception as e:
            print(f"  [WARN] 获取详情失败: {resource_id} -> {e}")

    # 使用 paper-search 为未解决问题推荐延伸阅读
    suggested_readings = []
    if all_entries_text:
        # 取所有日志文本的关键部分组合为查询
        combined_query = " ".join(all_entries_text)[:300]

        try:
            r = requests.post(
                f"{BASE}/v1/paper/rag/pass/keyword",
                headers=HEADERS_JSON,
                json={
                    "words": extract_keywords(combined_query, max_keywords=5),
                    "question": f"Recent advances related to: {combined_query[:200]}",
                    "type": 5,
                    "startTime": (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"),
                    "endTime": datetime.now().strftime("%Y-%m-%d"),
                    "pageSize": 5
                }
            )
            r.raise_for_status()
            text = r.text.strip()
            first_line = text.split('\n')[0]
            paper_data = json.loads(first_line)

            if paper_data.get("code") == 0:
                for p in paper_data.get("data", [])[:5]:
                    suggested_readings.append({
                        "doi": p.get("doi", ""),
                        "title": p.get("enName", ""),
                        "journal": p.get("publicationEnName", ""),
                        "reason": "基于近期日志关注方向推荐"
                    })

        except Exception as e:
            print(f"  [WARN] 推荐阅读检索异常: {e}")

    retrospective = {
        "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
        "entry_count": len(journal_files),
        "recurring_themes": [],
        "unresolved_questions": [],
        "knowledge_growth": {
            "new_entries": len(journal_files),
            "total_keywords": len(all_keywords),
        },
        "suggested_readings": suggested_readings,
    }

    print(f"[回顾] 回顾总结已生成")
    print(f"  日志条数: {retrospective['entry_count']}")
    print(f"  推荐阅读: {len(suggested_readings)} 篇")

    return retrospective


def format_retrospective_markdown(retro):
    """
    将回顾总结格式化为 Markdown。
    """
    if not retro:
        return "# 周期性回顾\n\n本周期内无日志条目。"

    lines = []
    lines.append(f"# 研究日志 -- 周期性回顾")
    lines.append(f"\n> 回顾期间: {retro['period']}")
    lines.append(f"> 日志条数: {retro['entry_count']}")

    if retro["recurring_themes"]:
        lines.append("\n## 反复出现的主题\n")
        for theme in retro["recurring_themes"]:
            lines.append(f"- {theme}")

    if retro["unresolved_questions"]:
        lines.append("\n## 未解决的问题\n")
        for q in retro["unresolved_questions"]:
            lines.append(f"- {q}")

    if retro["suggested_readings"]:
        lines.append("\n## 推荐延伸阅读\n")
        lines.append("| # | 标题 | 期刊 | DOI | 推荐理由 |")
        lines.append("|---|------|------|-----|----------|")
        for i, r in enumerate(retro["suggested_readings"], 1):
            title_short = r['title'][:50] + ("..." if len(r['title']) > 50 else "")
            lines.append(f"| {i} | {title_short} | {r['journal']} | "
                         f"`{r['doi']}` | {r['reason']} |")

    return "\n".join(lines)
```

---

## 完整编排脚本

以下是将全部步骤串联的端到端 Python 脚本：

```python
#!/usr/bin/env python3
"""
个人研究日志 (Research Journal) -- 完整编排脚本

用法:
    export ACCESS_KEY="your_access_key"
    python3 research_journal.py

可修改下方 CONFIG 区域的参数来调整日志内容和目标知识库。
"""

import os
import sys
import json
import hashlib
import tempfile
import re
import base64
import urllib.parse
import urllib.request
import requests
from datetime import datetime, timedelta

# ============================================================
# 配置
# ============================================================

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("ERROR: 请设置环境变量 ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET  = {"accessKey": AK}

# -- 用户可修改区域 --
CONFIG = {
    "knowledge_base_id": 456,           # 知识库节点 ID
    "entry_text": """
今天阅读了关于 `equivariant neural network` 在分子动力学力场中的应用。

主要收获:
- **NequIP** 框架通过 E(3)-equivariant 消息传递实现了高精度的原子间势
- 相比传统 `GNN force field`，等变网络在小数据集上表现更好
- 训练时需要注意 `energy conservation` 约束的加入方式

遇到的问题:
- NequIP 在大体系（>1000 原子）上的 scaling 如何?
- 等变性和计算效率之间的 trade-off 有没有更好的方案?
- `MACE` 模型声称解决了这个问题，需要进一步阅读
""",
    "tags": ["equivariant neural network", "GNN force field",
             "NequIP", "energy conservation", "MACE"],
    "auto_cite": True,
    "retrospective": False,             # 设为 True 执行周期性回顾
    "retrospective_days": 7,
}


# ============================================================
# 辅助函数
# ============================================================

def extract_keywords(text, max_keywords=5):
    """从文本中提取关键概念"""
    keywords = []

    # 提取反引号包裹的术语
    backtick_terms = re.findall(r'`([^`]+)`', text)
    keywords.extend(backtick_terms)

    # 提取加粗标记的术语
    bold_terms = re.findall(r'\*\*([^*]+)\*\*', text)
    keywords.extend(bold_terms)

    # 去重
    seen = set()
    unique = []
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if kw_lower not in seen and len(kw_lower) > 2:
            seen.add(kw_lower)
            unique.append(kw.strip())

    return unique[:max_keywords]


# ============================================================
# 步骤 1: 知识库存储与关联
# ============================================================

def step1_store_and_link(config):
    print(f"\n{'='*60}")
    print("步骤 1: 知识库存储与关联")
    print(f"{'='*60}\n")

    kb_id = config["knowledge_base_id"]
    entry_text = config["entry_text"]
    tags = config["tags"]

    # 1a. 搜索已有关联条目
    print("  1a. 搜索已有关联条目...")
    linked_entries = []
    try:
        r = requests.post(
            f"{BASE}/v1/knowledge/file/search",
            headers=HEADERS_JSON,
            json={
                "queryContent": entry_text[:500],
                "nodesId": kb_id,
                "knowledgeBaseId": kb_id
            }
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") == 0:
            files = data.get("data", {}).get("Files", [])
            for f in files[:5]:
                linked_entries.append({
                    "resource_id": f.get("userResourceId"),
                    "file_name": f.get("fileName", ""),
                    "content_snippet": f.get("content", "")[:200],
                })
            print(f"      找到 {len(linked_entries)} 个关联条目")
            for i, le in enumerate(linked_entries, 1):
                print(f"        {i}. {le['file_name']}")
        else:
            print(f"      搜索返回: {data.get('message', 'no data')}")
    except Exception as e:
        print(f"      [WARN] 搜索异常: {e}")

    # 1b. 上传日志条目
    print("\n  1b. 上传日志条目...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    tag_line = ", ".join(f"`{t}`" for t in tags) if tags else "无"
    md_content = (
        f"# 研究日志 {date_str}\n\n"
        f"**日期:** {date_str}\n\n"
        f"**标签:** {tag_line}\n\n"
        f"---\n\n"
        f"{entry_text.strip()}\n"
    )

    file_name = f"journal_{date_str}.md"
    tmp_path = os.path.join(tempfile.gettempdir(), file_name)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    file_size = os.path.getsize(tmp_path)
    h = hashlib.md5()
    with open(tmp_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    file_md5 = h.hexdigest()

    upload_success = False
    try:
        # 获取上传凭证
        r = requests.get(
            f"{BASE}/v1/knowledge/file/multipart",
            headers=HEADERS_GET,
            params={
                "fileName": file_name,
                "md5": file_md5,
                "parentId": kb_id,
                "size": file_size
            }
        )
        r.raise_for_status()
        multipart = r.json().get("data", {})

        if multipart.get("fileExist"):
            print(f"      文件已存在，注册到知识库...")
            r_submit = requests.post(
                f"{BASE}/v1/knowledge/file/submit",
                headers=HEADERS_JSON,
                json={
                    "parentId": kb_id, "fileName": file_name,
                    "md5": file_md5, "size": file_size,
                    "url": multipart.get("path", "")
                }
            )
            upload_success = True
        else:
            host = multipart["host"]
            path = multipart["path"]
            token = multipart["token"]

            content_type = "text/markdown; charset=utf-8"
            encoded_name = urllib.parse.quote(file_name, safe="-_.!~*'()")
            storage_param = base64.b64encode(json.dumps({
                "path": path,
                "option": {
                    "contentDisposition": (
                        f'inline; filename="{encoded_name}"; '
                        f"filename*=UTF-8''{encoded_name}"
                    ),
                    "contentType": content_type,
                },
            }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).decode("utf-8")

            file_content = open(tmp_path, "rb").read()
            upload_url = host.rstrip("/") + "/api/upload/binary"

            req = urllib.request.Request(upload_url, method="POST", data=file_content)
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("X-Storage-Param", storage_param)
            req.add_header("Content-Type", "application/octet-stream")

            with urllib.request.urlopen(req, timeout=300) as resp:
                upload_result = json.loads(resp.read().decode("utf-8"))

            final_path = (upload_result.get("data") or {}).get("path") or path
            r_submit = requests.post(
                f"{BASE}/v1/knowledge/file/submit",
                headers=HEADERS_JSON,
                json={
                    "parentId": kb_id, "fileName": file_name,
                    "md5": file_md5, "size": file_size,
                    "url": final_path
                }
            )
            upload_success = r_submit.json().get("code") == 0

        if upload_success:
            print(f"      日志 {file_name} 已存入知识库")
        else:
            print(f"      上传可能未成功，请检查知识库")

    except Exception as e:
        print(f"      [ERROR] 上传失败: {e}")

    os.remove(tmp_path)
    return linked_entries


# ============================================================
# 步骤 2: 自动补充文献引用
# ============================================================

def step2_auto_citations(config):
    print(f"\n{'='*60}")
    print("步骤 2: 自动补充文献引用")
    print(f"{'='*60}\n")

    if not config.get("auto_cite", True):
        print("  auto_cite=False，跳过文献补充")
        return []

    keywords = config.get("tags", []) or extract_keywords(config["entry_text"])
    if not keywords:
        print("  未提取到关键概念，跳过")
        return []

    print(f"  关键概念: {keywords}")
    citations = []

    for kw in keywords[:5]:
        try:
            r = requests.post(
                f"{BASE}/v1/paper/rag/pass/keyword",
                headers=HEADERS_JSON,
                json={
                    "words": [kw],
                    "question": f"Recent research on {kw}",
                    "type": 5,
                    "startTime": "",
                    "endTime": "",
                    "pageSize": 5
                }
            )
            r.raise_for_status()
            text = r.text.strip()
            first_line = text.split('\n')[0]
            data = json.loads(first_line)

            if data.get("code") != 0:
                print(f"  [WARN] '{kw}': {data.get('message')}")
                continue

            papers = data.get("data", [])
            papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)

            for p in papers[:2]:
                citations.append({
                    "keyword": kw,
                    "doi": p.get("doi", ""),
                    "title": p.get("enName", ""),
                    "journal": p.get("publicationEnName", ""),
                    "year": p.get("coverDateStart", "")[:4],
                    "citations": p.get("citationNums", 0),
                    "impact_factor": p.get("impactFactor", 0),
                })

            print(f"  '{kw}': {len(papers)} 篇相关论文")

        except Exception as e:
            print(f"  [WARN] '{kw}': {e}")

    # 去重
    seen_dois = set()
    unique = []
    for c in citations:
        if c["doi"] and c["doi"] not in seen_dois:
            seen_dois.add(c["doi"])
            unique.append(c)

    print(f"\n  共补充 {len(unique)} 条文献引用")
    for i, c in enumerate(unique, 1):
        print(f"    {i}. [{c['doi']}] {c['title'][:60]}...")
        print(f"       {c['journal']}, {c['year']}, 引用: {c['citations']}")

    return unique


# ============================================================
# 步骤 3: 概念关联分析
# ============================================================

def step3_concept_analysis(config):
    print(f"\n{'='*60}")
    print("步骤 3: 概念关联分析 (LKM)")
    print(f"{'='*60}\n")

    keywords = config.get("tags", []) or extract_keywords(config["entry_text"])
    if not keywords:
        print("  无关键概念，跳过")
        return []

    connections = []

    # 逐个概念搜索知识图谱
    for kw in keywords[:5]:
        try:
            r = requests.post(
                f"{BASE}/v1/lkm/search",
                headers=HEADERS_JSON,
                json={"query": kw, "limit": 5}
            )
            r.raise_for_status()
            data = r.json()

            kg_nodes = data.get("data", [])
            if not isinstance(kg_nodes, list):
                kg_nodes = [kg_nodes] if kg_nodes else []

            for node in kg_nodes:
                connections.append({
                    "keyword": kw,
                    "node": node,
                    "type": "knowledge_graph"
                })

            print(f"  '{kw}': {len(kg_nodes)} 个知识图谱节点")

        except Exception as e:
            print(f"  [WARN] '{kw}': {e}")

    # 跨概念关联分析
    if len(keywords) >= 2:
        combined = " ".join(keywords[:3])
        try:
            r = requests.post(
                f"{BASE}/v1/lkm/search",
                headers=HEADERS_JSON,
                json={"query": combined, "limit": 10}
            )
            r.raise_for_status()
            data = r.json()

            cross_nodes = data.get("data", [])
            if not isinstance(cross_nodes, list):
                cross_nodes = [cross_nodes] if cross_nodes else []

            for node in cross_nodes:
                connections.append({
                    "keyword": combined,
                    "node": node,
                    "type": "cross_concept"
                })

            print(f"  跨概念 '{combined[:40]}...': {len(cross_nodes)} 个节点")

        except Exception as e:
            print(f"  [WARN] 跨概念分析异常: {e}")

    print(f"\n  共发现 {len(connections)} 个概念关联")
    return connections


# ============================================================
# 周期性回顾（可选）
# ============================================================

def step_retrospective(config):
    print(f"\n{'='*60}")
    print("周期性回顾")
    print(f"{'='*60}\n")

    if not config.get("retrospective", False):
        print("  retrospective=False，跳过回顾")
        return None

    kb_id = config["knowledge_base_id"]
    days = config.get("retrospective_days", 7)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"  回顾范围: {start_date.strftime('%Y-%m-%d')} ~ "
          f"{end_date.strftime('%Y-%m-%d')}")

    # 获取日志列表
    try:
        r = requests.get(
            f"{BASE}/v1/knowledge/folder/children",
            headers=HEADERS_GET,
            params={
                "folderId": kb_id,
                "pageNum": 1,
                "pageSize": 100
            }
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        files = data.get("files", [])
    except Exception as e:
        print(f"  [ERROR] 获取日志列表失败: {e}")
        return None

    # 过滤日志条目
    journal_files = []
    for f in files:
        fname = f.get("fileName", "")
        if fname.startswith("journal_"):
            try:
                date_part = fname.replace("journal_", "").replace(".md", "")
                file_date = datetime.strptime(date_part, "%Y-%m-%d")
                if start_date <= file_date <= end_date:
                    journal_files.append(f)
            except ValueError:
                continue

    print(f"  找到 {len(journal_files)} 个日志条目")

    if not journal_files:
        print("  本周期无日志，跳过")
        return None

    # 基于日志关键词推荐延伸阅读
    all_tags = set()
    for jf in journal_files:
        fname = jf.get("fileName", "")
        all_tags.add(fname)

    suggested_readings = []
    combined_keywords = list(all_tags)[:5]
    if combined_keywords:
        try:
            r = requests.post(
                f"{BASE}/v1/paper/rag/pass/keyword",
                headers=HEADERS_JSON,
                json={
                    "words": combined_keywords,
                    "question": f"Recent advances in {' '.join(combined_keywords)}",
                    "type": 5,
                    "startTime": (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"),
                    "endTime": datetime.now().strftime("%Y-%m-%d"),
                    "pageSize": 5
                }
            )
            r.raise_for_status()
            text = r.text.strip()
            first_line = text.split('\n')[0]
            paper_data = json.loads(first_line)

            if paper_data.get("code") == 0:
                for p in paper_data.get("data", [])[:5]:
                    suggested_readings.append({
                        "doi": p.get("doi", ""),
                        "title": p.get("enName", ""),
                        "journal": p.get("publicationEnName", ""),
                        "reason": "基于近期日志关注方向推荐"
                    })
        except Exception as e:
            print(f"  [WARN] 推荐阅读检索异常: {e}")

    retro = {
        "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
        "entry_count": len(journal_files),
        "suggested_readings": suggested_readings,
    }

    print(f"\n  回顾完成: {retro['entry_count']} 条日志, "
          f"{len(suggested_readings)} 篇推荐阅读")

    return retro


# ============================================================
# 汇总输出
# ============================================================

def format_journal_output(linked, citations, connections, retro, config):
    """格式化最终输出"""
    lines = []
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"# 研究日志报告 {date_str}")
    lines.append(f"\n> 生成时间: {datetime.now().isoformat()}")

    # 关联条目
    lines.append("\n## 自动关联的已有条目\n")
    if linked:
        for i, le in enumerate(linked, 1):
            lines.append(f"{i}. **{le['file_name']}**")
            lines.append(f"   - 片段: {le['content_snippet'][:100]}...")
    else:
        lines.append("暂无关联条目（知识库中尚无历史日志，或内容不相关）。")

    # 文献引用
    lines.append("\n## 自动补充的文献引用\n")
    if citations:
        lines.append("| # | 关键词 | 标题 | 期刊 | 年份 | 引用 |")
        lines.append("|---|--------|------|------|------|------|")
        for i, c in enumerate(citations, 1):
            title_short = c['title'][:40] + ("..." if len(c['title']) > 40 else "")
            lines.append(f"| {i} | {c['keyword']} | {title_short} | "
                         f"{c['journal']} | {c['year']} | {c['citations']} |")
    else:
        lines.append("未补充文献引用。")

    # 概念关联
    lines.append("\n## 概念关联分析\n")
    if connections:
        kg_conns = [c for c in connections if c["type"] == "knowledge_graph"]
        cross_conns = [c for c in connections if c["type"] == "cross_concept"]
        lines.append(f"- 单概念知识图谱节点: {len(kg_conns)} 个")
        lines.append(f"- 跨概念关联节点: {len(cross_conns)} 个")
    else:
        lines.append("未发现显著概念关联。")

    # 周期性回顾
    if retro:
        lines.append(f"\n## 周期性回顾 ({retro['period']})\n")
        lines.append(f"- 日志条数: {retro['entry_count']}")
        if retro.get("suggested_readings"):
            lines.append("\n### 推荐延伸阅读\n")
            for i, r in enumerate(retro["suggested_readings"], 1):
                lines.append(f"{i}. [{r['title'][:60]}]"
                             f"(https://doi.org/{r['doi']}) -- {r['journal']}")

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  个人研究日志")
    print(f"  日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"  知识库: {config['knowledge_base_id']}")
    print(f"{'#'*60}")

    # 步骤 1: 存储与关联
    linked = step1_store_and_link(config)

    # 步骤 2: 自动补充文献引用
    citations = step2_auto_citations(config)

    # 步骤 3: 概念关联分析
    connections = step3_concept_analysis(config)

    # 可选: 周期性回顾
    retro = step_retrospective(config)

    # 汇总输出
    output = format_journal_output(linked, citations, connections, retro, config)
    print(f"\n{'='*60}")
    print(output)

    # 保存报告
    report_file = f"journal_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n报告已保存到: {report_file}")


if __name__ == "__main__":
    main()
```

---

## curl 示例汇总

```bash
AK="YOUR_ACCESS_KEY"

# ================================================================
# 步骤 1: 知识库存储与关联
# ================================================================

# 1a. 搜索已有关联条目
curl -s -X POST "https://open.bohrium.com/openapi/v1/knowledge/file/search" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "queryContent": "equivariant neural network force field training",
    "nodesId": 456,
    "knowledgeBaseId": 456
  }' | python3 -m json.tool

# 1b-i. 获取上传凭证
curl -s "https://open.bohrium.com/openapi/v1/knowledge/file/multipart?fileName=journal_2026-05-13.md&md5=abc123&parentId=456&size=1024" \
  -H "accessKey: $AK" | python3 -m json.tool

# 1b-iii. 注册文件到知识库
curl -s -X POST "https://open.bohrium.com/openapi/v1/knowledge/file/submit" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "parentId": 456,
    "fileName": "journal_2026-05-13.md",
    "md5": "abc123",
    "size": 1024,
    "url": "/path/from/upload"
  }'

# ================================================================
# 步骤 2: 自动补充文献引用
# ================================================================

# 为 "equivariant neural network" 搜索相关论文
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["equivariant neural network"],
    "question": "Recent research on equivariant neural network",
    "type": 5,
    "startTime": "",
    "endTime": "",
    "pageSize": 5
  }'

# 为 "NequIP" 搜索相关论文
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["NequIP"],
    "question": "NequIP equivariant interatomic potential",
    "type": 5,
    "startTime": "",
    "endTime": "",
    "pageSize": 5
  }'

# ================================================================
# 步骤 3: 概念关联分析 (LKM)
# ================================================================

# 单概念搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "equivariant neural network force field", "limit": 5}' | python3 -m json.tool

# 跨概念关联搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "equivariant neural network GNN force field energy conservation MACE", "limit": 10}' | python3 -m json.tool

# ================================================================
# 周期性回顾: 获取知识库中的日志列表
# ================================================================

curl -s "https://open.bohrium.com/openapi/v1/knowledge/folder/children?folderId=456&pageNum=1&pageSize=100" \
  -H "accessKey: $AK" | python3 -m json.tool
```

---

## 搭配使用

- **research-journal** 记录日志 -> **literature-review** 对日志中反复出现的主题做系统综述
- **research-journal** 发现未解决问题 -> **topic-scout** 将问题转化为具体研究选题
- **research-journal** 积累知识 -> **bohrium-knowledge-base** 管理和组织知识库结构
- **bohrium-paper-search** -- 本技能的文献自动引用能力来源
- **bohrium-lkm** -- 本技能的概念关联分析能力来源
- **bohrium-knowledge-base** -- 本技能的日志存储和检索能力来源

---

## 使用技巧

### 日志书写建议

```markdown
# 推荐: 用反引号标记关键术语，用加粗标记重要概念

今天阅读了关于 `equivariant neural network` 的论文。
**NequIP** 框架表现优异，但在大体系上的 scaling 存疑。

# 不推荐: 纯文字叙述，难以自动提取关键概念

今天看了一些论文，感觉等变网络很有意思。
```

### 标签策略

```python
# 推荐: 使用英文专业术语作为标签，保持一致性
tags = ["equivariant neural network", "GNN force field", "NequIP"]

# 不推荐: 混合中英文、过于笼统
tags = ["神经网络", "论文", "有趣"]
```

### 回顾频率

| 频率 | `retrospective_days` | 适用场景 |
|------|---------------------|----------|
| 每周 | 7 | 日常研究记录，追踪短期进展 |
| 每两周 | 14 | 项目阶段性回顾 |
| 每月 | 30 | 研究方向总结，准备组会报告 |

### 知识库组织

建议为研究日志创建专用知识库，按月或按项目建立子文件夹：

```
研究日志 (知识库)
  |-- 2026-05/
  |     |-- journal_2026-05-01.md
  |     |-- journal_2026-05-02.md
  |     |-- ...
  |-- 2026-04/
  |     |-- journal_2026-04-01.md
  |     |-- ...
  |-- retrospective/
        |-- retro_2026-05-week1.md
        |-- retro_2026-04-week4.md
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `ACCESS_KEY` 为空 | OpenClaw 未注入环境变量 | 检查 `~/.openclaw/openclaw.json` 中 `research-journal.env.ACCESS_KEY` 是否填入 |
| 401 Unauthorized | accessKey 无效或过期 | 更新 `~/.openclaw/openclaw.json` 中的 AccessKey 并重启会话 |
| 知识库搜索无结果 | 知识库为空或文献未完成索引 | 新上传的文件需等待后台解析和索引完成（通常几分钟） |
| 文献引用补充为空 | 关键词提取失败或概念太冷门 | 在日志中使用反引号标记关键术语，或手动指定 `tags` 参数 |
| LKM 概念关联为空 | 概念过于新颖或表述不标准 | 使用更通用的英文学术术语描述概念 |
| 上传文件报 `code=230117` | 同名文件已存在 | 正常情况，同一天重复运行会触发；系统会自动处理 |
| 回顾找不到日志条目 | 文件名格式不匹配 | 确保日志文件名为 `journal_YYYY-MM-DD.md` 格式 |
| 回顾时间范围内无日志 | `retrospective_days` 设置过小或近期未记录 | 扩大 `retrospective_days` 范围 |
| 响应含多行 JSON | paper-search 返回 streaming 格式 | 取第一行解析即可：`json.loads(r.text.split('\n')[0])` |
| 整体执行时间过长 | 概念过多导致 API 调用次数多 | 减少 `tags` 数量到 3-5 个核心概念 |
