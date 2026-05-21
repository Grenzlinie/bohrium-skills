---
name: related-work-writer
description: "Related work section generator combining paper search, PDF parsing, and knowledge base. Use when: user is writing the Related Work section of a paper and needs to find, categorize, and summarize relevant prior work. NOT for: general literature review (use literature-review), finding a specific paper (use bohrium-paper-search)."
---

# SKILL: 相关工作生成器 (Related Work Writer)

## 概述

编排 `paper-search`、`pdf-parser`、`knowledge-base` 三个原子技能，为用户撰写论文的 Related Work（相关工作）章节提供一站式辅助。从文献检索、关键论文全文解析到用户积累笔记检索，最终输出分类组织的相关工作段落、BibTeX 引用列表和自身工作定位分析。

**编排的原子技能：**

| 步骤 | 原子 Skill | 端点 | 功能 |
|------|-----------|------|------|
| 1 | `paper-search` | `/v1/paper/rag/pass/keyword` | 语义检索相关论文 |
| 2 | `pdf-parser` | `/v1/parse/trigger-url-async` + `/v1/parse/get-result` | 解析关键论文的方法和贡献 |
| 3 | `knowledge-base` | `/v1/knowledge/file/search` | 检索用户积累的文献笔记 |

**适用场景：**

- 撰写论文的 Related Work 章节
- 按方法/时间/问题维度对已有工作进行分类梳理
- 生成分类段落草稿和过渡句
- 输出 BibTeX 格式引用列表
- 分析自身工作与已有工作的定位关系

**不适用：**

- 通用文献综述（无特定论文写作需求）→ `literature-review`
- 单纯搜索某篇论文 → `bohrium-paper-search`
- 深度拆解一篇论文 → `paper-dissector`
- 选题探索 → `topic-scout`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"related-work-writer": {
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
| `topic` | string | 是 | — | 自身研究主题描述（如"基于图神经网络的分子力场预测"） |
| `method_description` | string | 是 | — | 自身方法的简要描述（1-3 句话） |
| `organization_mode` | string | 否 | `"by-method"` | 组织模式：`"by-method"`（按方法）/ `"by-chronological"`（按时间）/ `"by-problem"`（按问题） |
| `must_cite_papers` | list | 否 | `[]` | 必须引用的论文列表（DOI 或标题） |
| `keywords` | string[] | 否 | 从 topic 提取 | 检索关键词（3-8 个英文术语） |
| `top_n_parse` | int | 否 | 5 | 需要全文解析的关键论文数量 |
| `knowledge_base_id` | int | 否 | 0 | 用户知识库 ID，0 表示不检索知识库 |

---

## 输出格式

### 1. 分类相关工作段落（草稿）

按用户选择的组织模式（方法/时间/问题）生成结构化的 Related Work 段落，每个分类包含：
- 分类标题
- 综述段落（含引用标记）
- 类别间过渡句

### 2. 引用列表（BibTeX 格式）

从 `paper-search` 结果自动生成标准 BibTeX 条目。

### 3. LaTeX 可编译段落（默认同时输出）

除 Markdown 版本外，**必须同时输出 LaTeX 格式**：
- 正文段落使用 `\cite{}` 引用标记（替换 Markdown 中的 [Author Year] 标记）
- 各分类使用 `\subsection{}` 分节
- 附带完整 `.bib` 文件，BibTeX key 格式统一为 `author_year_venue`

用户可直接将输出的 LaTeX 段落 `\input{}` 到主文件中编译，无需手动转换格式。

### 4. 定位关系分析

分析自身工作与各类已有方法的关系：
- 继承了哪些方法的思路
- 解决了哪些方法的不足
- 在哪些维度上有差异化贡献

---

## 数据质量控制（关键步骤）

API 返回的论文列表可能包含不相关的结果，**必须在生成 Related Work 段落前进行相关性过滤和内容验证**。

### 过滤规则

```python
def filter_relevant_papers(papers, topic_keywords, min_hits=2):
    """
    只保留标题+摘要中至少命中 min_hits 个主题核心术语的论文。

    topic_keywords: 研究主题的核心术语
    例如主题 "equivariant GNN for molecular force field"
    topic_keywords = ["graph neural", "force field", "equivariant", "molecular dynamics", "interatomic potential"]
    """
    filtered = []
    for p in papers:
        text = (p.get("enName", "") + " " + p.get("enAbstract", "")).lower()
        hits = sum(1 for k in topic_keywords if k.lower() in text)
        if hits >= min_hits:
            filtered.append(p)
    return filtered
```

### 引用内容真实性验证（最高优先级）

**生成的 Related Work 文本绝对不能捏造论文内容。** 每条引用必须遵循以下规则：

1. **有摘要时**：只能基于摘要中的实际内容进行总结和引用
2. **无摘要时**：只能引用论文标题，**严禁**根据标题推测论文"表明了"、"证明了"、"提出了"什么
3. **有全文解析时**：可以引用全文解析中提取的方法和贡献描述

```python
def generate_citation_text(paper, parsed_content=None):
    """
    生成单篇论文的引用描述文本。严格基于实际可用信息。
    """
    abstract = paper.get("enAbstract", "").strip()
    title = paper.get("enName", "")
    contribution = ""
    if parsed_content:
        contribution = parsed_content.get("contribution", "").strip()

    if contribution:
        # 有全文解析：使用提取的贡献描述
        return contribution[:200]
    elif abstract:
        # 有摘要：从摘要提取关键句
        return _extract_key_sentence(abstract)
    else:
        # 无摘要：只引用标题，不做任何内容推断
        return f'(titled "{title}")'  # 不使用 "demonstrated", "showed" 等动词
```

### 禁止的行为

- **捏造论文内容**：基于标题猜测论文"提出了X方法"或"证明了Y结论"
- 将 A 论文的结论错误归因到 B 论文
- 编造不存在的实验结果或性能数据
- 引用时省略不利信息只保留有利结论

### 推荐的做法

- 无摘要时诚实标注：`Smith et al. [3] (titled "A Novel Approach to X") 也与本方向相关。`
- 有摘要时基于摘要引用：`Chen et al. [5] proposed a message-passing scheme that achieves 0.5 kcal/mol MAE on MD17.`
- 对不确定的内容加限定词：`Based on the abstract, this work appears to focus on...`
- 明确标注信息来源深度：`以下引用基于论文摘要，未经全文验证`

---

## 报告分析深度要求

**Related Work 不是论文列表的格式化转储**。你是一个专业学术写作者，必须在段落中提供：

1. **分类综述而非罗列**：按方法/问题/时间线组织论文，每个类别给出概括性总结
2. **跨论文对比**：不同方法在同一指标上的比较、不同工作的思路差异
3. **与自身工作的定位关系**：明确说明本文继承了什么、改进了什么、与什么不同
4. **类别间的逻辑过渡**：段落之间用过渡句连接，形成连贯叙述

### 奠基性文献补充（关键步骤）

**确保技术主线完整**：API 检索结果可能偏向近期高被引工作，需主动补充奠基性文献：

**必须确认包含的引用类型**：
1. **领域奠基论文**：如果写 GNN 分子预测的 Related Work，必须包含 Gilmer (MPNN, ICML 2017)、Schütt (SchNet, NeurIPS 2017/2018)、Gasteiger (DimeNet, ICLR 2020) 等
2. **方法主线论文**：每个分类下的技术主线必须完整（如等变 GNN: TFN → SE(3)-Transformer → PaiNN → NequIP → Equiformer → MACE），不能跳过关键节点
3. **当前 SOTA**：每个分类下必须引用当前最好的方法（可引用 leaderboard 结果）

**如何判断是否遗漏了奠基性工作**：
- 你的分类中每条技术主线是否有"起点"论文？如果最早的引用是 2021 年的，而该方向实际起源于 2017 年，说明你遗漏了——通过扩展时间范围的关键词检索补充
- 领域内 h-index 最高的 3-5 位学者，是否至少被引用了一次？
- 如果去掉所有 2022 年之后的引用，你的 Related Work 是否仍有骨架？

### 禁止的行为

- 逐篇列出论文标题和摘要，不做归纳
- 用模板化语言描述每篇论文（如每篇都是"提出了一种方法"）
- 忽略与自身工作的关系
- 截断论文标题或作者名
- 遗漏领域奠基性工作（即使 API 没有返回，你作为领域专家也应知道它们的存在）
- 只引用"被引数高的近期论文"，忽略被引数可能不高但方法论意义重大的早期工作

---

## 工作流程图

```
输入: topic, method_description, organization_mode, must_cite_papers
        |
        v
+--------------------------------------+
|  步骤 1: 论文语义检索                  |
|  POST /v1/paper/rag/pass/keyword     |
|  -> 检索 30 篇相关论文                |
|  -> 合并 must_cite_papers             |
|  -> 按引用数和相关性排序               |
+---------------+----------------------+
                |
                v
+--------------------------------------+
|  步骤 2: 关键论文全文解析              |
|  POST /v1/parse/trigger-url-async    |
|  POST /v1/parse/get-result (轮询)     |
|  -> 解析 Top-N 论文的方法和贡献        |
|  -> 提取 Related Work 和 Method 段落  |
+---------------+----------------------+
                |
                v
+--------------------------------------+
|  步骤 3: 知识库笔记检索               |
|  POST /v1/knowledge/file/search      |
|  -> 检索用户积累的文献笔记             |
|  -> 补充分类信息和个人理解             |
+---------------+----------------------+
                |
                v
+--------------------------------------+
|  步骤 4: 分类组织与生成               |
|  -> 按 organization_mode 分类论文     |
|  -> 生成各分类段落草稿                |
|  -> 生成类别间过渡句                  |
|  -> 生成 BibTeX 引用列表              |
|  -> 分析自身工作定位关系               |
+--------------------------------------+
```

---

## 通用代码模板

```python
import os, time, requests, json

AK = os.environ.get("ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
```

---

## 步骤 1: 论文语义检索

使用 `paper-search` 进行语义检索，获取相关论文候选列表。

### Python 示例

```python
def search_related_papers(keywords, question, must_cite_dois=None, page_size=30):
    """
    语义检索相关论文。

    Args:
        keywords: 关键词列表，3-8 个英文术语
        question: 研究问题的自然语言描述
        must_cite_dois: 必须引用的论文 DOI 列表
        page_size: 返回论文数量

    Returns:
        论文列表，按引用数降序排列
    """
    payload = {
        "words": keywords,
        "question": question,
        "type": 5,
        "pageSize": page_size
    }

    r = requests.post(
        f"{BASE}/v1/paper/rag/pass/keyword",
        headers=HEADERS_JSON,
        json=payload
    )
    r.raise_for_status()

    # API 可能返回多行 JSON（streaming），取第一行
    text = r.text.strip()
    first_line = text.split('\n')[0]
    data = json.loads(first_line)

    if data.get("code") != 0:
        raise RuntimeError(f"论文检索失败: {data.get('message', 'unknown error')}")

    papers = data["data"]

    # 按引用数降序排列
    papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)

    # 合并必须引用的论文（如果不在检索结果中，单独搜索补充）
    if must_cite_dois:
        existing_dois = {p.get("doi", "") for p in papers}
        for doi in must_cite_dois:
            if doi not in existing_dois:
                extra = _search_paper_by_doi(doi)
                if extra:
                    papers.append(extra)

    print(f"[步骤1] 检索到 {len(papers)} 篇相关论文")
    for i, p in enumerate(papers[:10]):
        print(f"  {i+1}. [{p.get('doi', 'N/A')}] {p['enName'][:70]}")
        print(f"     引用: {p.get('citationNums', 0)}, "
              f"期刊: {p.get('publicationEnName', 'N/A')}, "
              f"日期: {p.get('coverDateStart', 'N/A')}")

    return papers


def _search_paper_by_doi(doi):
    """通过 DOI 搜索单篇论文。"""
    payload = {
        "words": [doi],
        "question": doi,
        "type": 5,
        "pageSize": 1
    }
    try:
        r = requests.post(
            f"{BASE}/v1/paper/rag/pass/keyword",
            headers=HEADERS_JSON,
            json=payload
        )
        r.raise_for_status()
        text = r.text.strip().split('\n')[0]
        data = json.loads(text)
        if data.get("code") == 0 and data.get("data"):
            return data["data"][0]
    except Exception as e:
        print(f"  [警告] 无法检索 DOI={doi}: {e}")
    return None
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["graph neural network", "molecular dynamics", "force field"],
    "question": "graph neural network methods for molecular force field prediction",
    "type": 5,
    "pageSize": 30
  }'
```

---

## 步骤 2: 关键论文全文解析

对高引用论文进行全文解析，重点提取 Method 和 Related Work 段落，用于理解各方法的核心贡献。

### Python 示例

```python
def parse_key_papers(papers, top_n=5):
    """
    解析关键论文全文，提取方法和贡献。

    Args:
        papers: 论文列表（来自步骤1）
        top_n: 解析数量

    Returns:
        dict: {doi: {"content": 全文, "method": 方法段落, "contribution": 贡献摘要}}
    """
    selected = papers[:top_n]
    tokens = {}
    results = {}

    print(f"\n[步骤2] 提交 {len(selected)} 篇论文解析任务...")

    # 1. 提交所有解析任务
    for p in selected:
        doi = p.get("doi", "")
        if not doi:
            continue

        pdf_url = f"https://doi.org/{doi}"
        payload = {
            "url": pdf_url,
            "sync": False,
            "textual": True,
            "table": True,
            "expression": True,
            "equation": True,
            "pages": [0, 1, 2],   # 只解析前3页（摘要+方法概述）
            "timeout": 1800
        }

        try:
            r = requests.post(
                f"{BASE}/v1/parse/trigger-url-async",
                headers=HEADERS_JSON,
                json=payload
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("code"):
                tokens[doi] = data["token"]
                print(f"  提交: {doi} -> token={data['token'][:16]}...")
            else:
                print(f"  跳过: {doi} -> {data.get('message', 'error')}")
        except Exception as e:
            print(f"  失败: {doi} -> {e}")

    if not tokens:
        print("  警告: 无法提交任何解析任务，跳过全文解析")
        return results

    # 2. 轮询解析结果
    print(f"\n  等待 {len(tokens)} 个解析任务完成...")
    pending = dict(tokens)
    max_wait = 180
    start = time.time()

    while pending and (time.time() - start) < max_wait:
        time.sleep(3)
        done_keys = []
        for doi, token in pending.items():
            try:
                r = requests.post(
                    f"{BASE}/v1/parse/get-result",
                    headers=HEADERS_JSON,
                    json={
                        "token": token,
                        "content": True,
                        "objects": False,
                        "pages_dict": False
                    }
                )
                r.raise_for_status()
                result = r.json()
                status = result.get("status", "")

                if status == "success":
                    content = result.get("content", "")
                    method_section = _extract_section(content, "method")
                    contribution = _extract_contribution(content)
                    results[doi] = {
                        "content": content,
                        "method": method_section,
                        "contribution": contribution
                    }
                    print(f"  完成: {doi} ({len(content)} 字符)")
                    done_keys.append(doi)
                elif status == "failed":
                    print(f"  失败: {doi}")
                    done_keys.append(doi)
            except Exception as e:
                print(f"  错误: {doi} -> {e}")

        for k in done_keys:
            del pending[k]

    if pending:
        print(f"  超时: {len(pending)} 个任务未完成")

    print(f"  解析完成: {len(results)}/{len(tokens)} 篇")
    return results


import re

def _extract_section(text, section_name):
    """从解析文本中提取指定章节内容。"""
    patterns = {
        "method": r'(?i)(method|approach|methodology|proposed\s+method)',
        "related": r'(?i)(related\s+work|background|literature\s+review|prior\s+work)',
        "conclusion": r'(?i)(conclusion|summary|concluding)',
    }
    pattern = patterns.get(section_name, section_name)

    # 尝试按 LaTeX 风格标记定位
    sections = re.split(r'\\begin\{(?:section|subsection)\}', text)
    for sec in sections:
        first_line = sec.strip()[:200]
        if re.search(pattern, first_line, re.IGNORECASE):
            return sec[:3000]  # 截取前 3000 字符

    return ""


def _extract_contribution(text):
    """从摘要中提取论文核心贡献。"""
    # 匹配贡献性语句
    contribution_patterns = [
        r'[^.]*(?:we\s+propose|we\s+present|we\s+introduce|we\s+develop)[^.]+\.',
        r'[^.]*(?:this\s+paper\s+presents?|this\s+work\s+proposes?)[^.]+\.',
        r'[^.]*(?:our\s+(?:main\s+)?contribution)[^.]+\.',
    ]

    contributions = []
    for pattern in contribution_patterns:
        matches = re.findall(pattern, text[:5000], re.IGNORECASE)
        contributions.extend(matches)

    return " ".join(contributions[:3]) if contributions else ""
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 提交解析任务
TOKEN=$(curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/trigger-url-async" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "url": "https://doi.org/10.1038/s41586-021-03819-2",
    "sync": false,
    "textual": true,
    "table": true,
    "expression": true,
    "equation": true,
    "pages": [0, 1, 2],
    "timeout": 1800
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "Token: $TOKEN"

# 轮询结果
sleep 5
curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/get-result" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d "{\"token\": \"$TOKEN\", \"content\": true}"
```

---

## 步骤 3: 知识库笔记检索

检索用户在 Bohrium 知识库中积累的文献笔记，补充分类信息和个人理解。

### Python 示例

```python
def search_user_notes(topic, knowledge_base_id=0):
    """
    检索用户知识库中的文献笔记。

    Args:
        topic: 研究主题
        knowledge_base_id: 知识库 ID，0 表示搜索所有知识库

    Returns:
        list: 匹配的笔记列表 [{fileName, content, userResourceId}]
    """
    if knowledge_base_id == 0:
        print("[步骤3] 未指定知识库 ID，跳过笔记检索")
        return []

    payload = {
        "queryContent": topic,
        "nodesId": 0,
        "knowledgeBaseId": knowledge_base_id
    }

    try:
        r = requests.post(
            f"{BASE}/v1/knowledge/file/search",
            headers=HEADERS_JSON,
            json=payload
        )
        r.raise_for_status()
        data = r.json()

        if data.get("code") != 0:
            print(f"[步骤3] 知识库搜索失败: {data.get('message')}")
            return []

        files = data.get("data", {}).get("Files", [])
        total = data.get("data", {}).get("total", 0)

        print(f"[步骤3] 知识库中找到 {total} 条相关笔记")
        for f in files[:5]:
            print(f"  - {f.get('fileName', '未命名')}: "
                  f"{f.get('content', '')[:100]}...")

        return files

    except Exception as e:
        print(f"[步骤3] 知识库检索异常: {e}")
        return []
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

curl -s -X POST "https://open.bohrium.com/openapi/v1/knowledge/file/search" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "queryContent": "graph neural network force field",
    "nodesId": 0,
    "knowledgeBaseId": 12345
  }'
```

---

## 步骤 4: 分类组织与生成

核心步骤：将检索和解析的结果按用户选择的组织模式进行分类，生成 Related Work 段落草稿、BibTeX 引用和定位分析。

### 三种组织模式

#### 模式一：按方法分类 (by-method)

将论文按核心方法/技术路线分组，适合方法驱动型研究。

```python
def organize_by_method(papers, parsed_contents):
    """
    按方法分类组织论文。

    策略：
    1. 从论文标题和摘要中提取方法关键词
    2. 基于方法关键词聚类
    3. 每个类别生成一个综述段落

    Returns:
        dict: {category_name: [paper_list]}
    """
    categories = {}

    # 方法关键词模式（根据领域调整）
    method_keywords = {
        "基于图神经网络的方法": [
            "graph neural network", "GNN", "message passing",
            "graph convolutional", "graph attention"
        ],
        "基于 Transformer 的方法": [
            "transformer", "attention mechanism", "self-attention",
            "multi-head attention"
        ],
        "基于传统机器学习的方法": [
            "random forest", "support vector", "kernel method",
            "gaussian process", "descriptor"
        ],
        "基于物理信息的方法": [
            "physics-informed", "physics-based", "equivariant",
            "invariant", "symmetry"
        ],
        "其他方法": []
    }

    for p in papers:
        title = p.get("enName", "").lower()
        abstract = p.get("enAbstract", "").lower()
        text = f"{title} {abstract}"

        assigned = False
        for category, keywords in method_keywords.items():
            if category == "其他方法":
                continue
            for kw in keywords:
                if kw.lower() in text:
                    categories.setdefault(category, []).append(p)
                    assigned = True
                    break
            if assigned:
                break

        if not assigned:
            categories.setdefault("其他方法", []).append(p)

    return categories
```

#### 模式二：按时间分类 (by-chronological)

将论文按时间阶段分组，适合展示领域发展脉络。

```python
def organize_by_chronological(papers):
    """
    按时间阶段分类组织论文。

    策略：
    1. 按发表年份分组
    2. 合并相近年份为阶段
    3. 每个阶段生成一个综述段落

    Returns:
        dict: {stage_name: [paper_list]}
    """
    from collections import defaultdict

    papers_by_year = defaultdict(list)
    for p in papers:
        year = p.get("coverDateStart", "")[:4]
        if year:
            papers_by_year[int(year)].append(p)

    if not papers_by_year:
        return {"全部论文": papers}

    min_year = min(papers_by_year.keys())
    max_year = max(papers_by_year.keys())

    # 根据时间跨度决定分组策略
    span = max_year - min_year
    if span <= 3:
        # 跨度小，按年分组
        stages = {}
        for year in sorted(papers_by_year.keys()):
            stages[f"{year} 年"] = papers_by_year[year]
    elif span <= 8:
        # 中等跨度，2-3 年一组
        stages = {}
        years = sorted(papers_by_year.keys())
        i = 0
        while i < len(years):
            start = years[i]
            end = min(start + 2, years[-1])
            stage_name = f"{start}-{end} 年" if start != end else f"{start} 年"
            stage_papers = []
            for y in range(start, end + 1):
                stage_papers.extend(papers_by_year.get(y, []))
            if stage_papers:
                stages[stage_name] = stage_papers
            i += (end - start + 1)
    else:
        # 大跨度，分为早期/中期/近期
        mid_year = min_year + span // 3
        late_year = min_year + 2 * span // 3
        stages = {
            f"早期工作 ({min_year}-{mid_year})": [],
            f"发展阶段 ({mid_year+1}-{late_year})": [],
            f"近期进展 ({late_year+1}-{max_year})": [],
        }
        for year, ps in papers_by_year.items():
            if year <= mid_year:
                stages[f"早期工作 ({min_year}-{mid_year})"].extend(ps)
            elif year <= late_year:
                stages[f"发展阶段 ({mid_year+1}-{late_year})"].extend(ps)
            else:
                stages[f"近期进展 ({late_year+1}-{max_year})"].extend(ps)

        # 移除空阶段
        stages = {k: v for k, v in stages.items() if v}

    return stages
```

#### 模式三：按问题分类 (by-problem)

将论文按解决的核心问题分组，适合问题导向型研究。

```python
def organize_by_problem(papers, parsed_contents):
    """
    按问题分类组织论文。

    策略：
    1. 从论文摘要中提取核心问题关键词
    2. 按问题类型聚类
    3. 每个问题生成一个综述段落

    Returns:
        dict: {problem_name: [paper_list]}
    """
    categories = {}

    # 问题关键词模式（根据领域调整）
    problem_keywords = {
        "数据效率问题": [
            "data efficiency", "small sample", "few-shot",
            "data scarcity", "limited data", "label efficiency"
        ],
        "可解释性问题": [
            "interpretability", "explainability", "interpretable",
            "explainable", "black box", "transparency"
        ],
        "泛化能力问题": [
            "generalization", "transferability", "domain adaptation",
            "out-of-distribution", "robustness"
        ],
        "计算效率问题": [
            "computational efficiency", "scalability", "large-scale",
            "acceleration", "speed up", "real-time"
        ],
        "精度问题": [
            "accuracy", "precision", "chemical accuracy",
            "benchmark", "state-of-the-art"
        ],
    }

    for p in papers:
        title = p.get("enName", "").lower()
        abstract = p.get("enAbstract", "").lower()
        text = f"{title} {abstract}"

        assigned = False
        for category, keywords in problem_keywords.items():
            for kw in keywords:
                if kw.lower() in text:
                    categories.setdefault(category, []).append(p)
                    assigned = True
                    break
            if assigned:
                break

        if not assigned:
            categories.setdefault("其他相关工作", []).append(p)

    return categories
```

### 段落生成与过渡句

```python
def generate_related_work_paragraphs(categories, papers, parsed_contents,
                                     method_description, organization_mode):
    """
    为每个分类生成 Related Work 段落草稿和过渡句。

    Args:
        categories: {category_name: [paper_list]} 分类结果
        papers: 完整论文列表（用于引用编号）
        parsed_contents: {doi: {...}} 解析内容
        method_description: 自身方法描述
        organization_mode: 组织模式

    Returns:
        str: Related Work 段落草稿（Markdown 格式）
    """
    # 构建引用编号映射
    cite_map = {}
    for i, p in enumerate(papers, 1):
        doi = p.get("doi", "")
        if doi:
            cite_map[doi] = i

    paragraphs = []
    category_names = list(categories.keys())

    for idx, (category, cat_papers) in enumerate(categories.items()):
        # ── 分类标题 ──
        paragraphs.append(f"### {category}\n")

        # ── 按引用数排序，提取代表性论文 ──
        sorted_cat = sorted(cat_papers,
                            key=lambda p: p.get("citationNums", 0),
                            reverse=True)

        # ── 生成综述段落 ──
        lines = []
        for p in sorted_cat[:5]:  # 每类最多引用 5 篇
            doi = p.get("doi", "")
            cite_num = cite_map.get(doi, "?")
            title = p.get("enName", "")
            abstract = p.get("enAbstract", "")

            # 如果有解析内容，使用更详细的方法描述
            parsed = parsed_contents.get(doi, {})
            contribution = parsed.get("contribution", "")

            if contribution:
                lines.append(
                    f"{_get_first_author(p)} et al. [{cite_num}] "
                    f"{contribution[:200]}"
                )
            elif abstract:
                # 提取摘要中的关键句
                key_sentence = _extract_key_sentence(abstract)
                lines.append(
                    f"{_get_first_author(p)} et al. [{cite_num}] "
                    f"{key_sentence}"
                )

        paragraph_text = " ".join(lines)
        paragraphs.append(paragraph_text + "\n")

        # ── 生成过渡句 ──
        if idx < len(category_names) - 1:
            next_category = category_names[idx + 1]
            transition = _generate_transition(
                category, next_category, organization_mode
            )
            paragraphs.append(f"_{transition}_\n")

    return "\n".join(paragraphs)


def _get_first_author(paper):
    """提取第一作者姓氏。"""
    authors = paper.get("authors", "Unknown")
    if isinstance(authors, list):
        first = str(authors[0]) if authors else "Unknown"
    else:
        first = str(authors).split(",")[0]
    # 提取姓氏（取最后一个词）
    parts = first.strip().split()
    return parts[-1] if parts else "Unknown"


def _extract_key_sentence(abstract):
    """从摘要中提取关键句（通常是方法描述或核心结论）。"""
    sentences = abstract.replace(". ", ".\n").split("\n")
    # 优先选择包含方法描述的句子
    for s in sentences:
        s_lower = s.lower().strip()
        if any(kw in s_lower for kw in ["propose", "present", "introduce",
                                         "develop", "demonstrate", "show that"]):
            return s.strip()
    # fallback 到第二句（通常比第一句信息密度更高）
    if len(sentences) > 1:
        return sentences[1].strip()
    return sentences[0].strip() if sentences else ""


def _generate_transition(current_category, next_category, mode):
    """生成类别间的过渡句。"""
    transitions = {
        "by-method": {
            "default": (
                f"除了上述 {current_category} 的工作之外，"
                f"另一类重要的研究方向是 {next_category}。"
            ),
        },
        "by-chronological": {
            "default": (
                f"在 {current_category} 的基础上，"
                f"{next_category} 的研究在方法和性能上取得了进一步突破。"
            ),
        },
        "by-problem": {
            "default": (
                f"与解决 {current_category} 的工作不同，"
                f"另一组研究重点关注 {next_category}。"
            ),
        },
    }
    mode_transitions = transitions.get(mode, transitions["by-method"])
    return mode_transitions.get("default", f"此外，{next_category} 也是相关的研究方向。")
```

---

## BibTeX 生成

从 `paper-search` 返回的元数据自动生成 BibTeX 条目。

```python
def generate_bibtex(papers):
    """
    从论文元数据生成 BibTeX 条目列表。

    Args:
        papers: paper-search 返回的论文列表

    Returns:
        str: BibTeX 格式的完整引用列表
    """
    entries = []

    for p in papers:
        doi = p.get("doi", "")
        title = p.get("enName", "Untitled")
        authors_raw = p.get("authors", "Unknown")
        journal = p.get("publicationEnName", "")
        year = p.get("coverDateStart", "")[:4]
        volume = p.get("volume", "")
        pages = p.get("pages", "")
        citation_nums = p.get("citationNums", 0)

        # 格式化作者
        if isinstance(authors_raw, list):
            authors = " and ".join(str(a) for a in authors_raw)
        else:
            authors = str(authors_raw)

        # 生成 cite key: 第一作者姓 + 年份 + 标题首词
        first_author = _get_first_author(p).lower()
        title_first_word = re.sub(r'[^a-zA-Z]', '',
                                   title.split()[0]).lower() if title else "paper"
        cite_key = f"{first_author}{year}{title_first_word}"

        entry = f"""@article{{{cite_key},
  title     = {{{title}}},
  author    = {{{authors}}},
  journal   = {{{journal}}},
  year      = {{{year}}},"""

        if volume:
            entry += f"\n  volume    = {{{volume}}},"
        if pages:
            entry += f"\n  pages     = {{{pages}}},"
        if doi:
            entry += f"\n  doi       = {{{doi}}},"

        entry += f"\n  note      = {{Cited by {citation_nums}}}"
        entry += "\n}"

        entries.append(entry)

    bibtex_output = "\n\n".join(entries)
    print(f"\n[BibTeX] 生成 {len(entries)} 条引用")
    return bibtex_output
```

### 输出示例

```bibtex
@article{smith2022graph,
  title     = {Graph Neural Networks for Molecular Property Prediction},
  author    = {John Smith and Jane Doe and Bob Lee},
  journal   = {Nature Machine Intelligence},
  year      = {2022},
  volume    = {4},
  pages     = {123-135},
  doi       = {10.1038/s42256-022-00001-1},
  note      = {Cited by 256}
}

@article{chen2023equivariant,
  title     = {Equivariant Transformers for Molecular Dynamics},
  author    = {Wei Chen and Li Zhang},
  journal   = {Physical Review Letters},
  year      = {2023},
  doi       = {10.1103/PhysRevLett.130.012345},
  note      = {Cited by 89}
}
```

---

## 定位关系分析

分析自身工作与各类已有方法的关系，辅助撰写 Related Work 结尾的定位段落。

```python
def analyze_positioning(categories, method_description, parsed_contents):
    """
    分析自身工作与已有方法的定位关系。

    Args:
        categories: 分类结果
        method_description: 自身方法描述
        parsed_contents: 解析的论文内容

    Returns:
        str: 定位关系分析文本
    """
    positioning = []
    positioning.append("## 自身工作定位分析\n")

    method_lower = method_description.lower()

    for category, cat_papers in categories.items():
        # 分析与该类方法的关系
        relations = []

        # 检测继承关系
        for p in cat_papers[:3]:
            abstract = p.get("enAbstract", "").lower()
            parsed = parsed_contents.get(p.get("doi", ""), {})
            method_text = parsed.get("method", "").lower()

            # 简单的共词分析判断关系
            common_terms = _find_common_terms(method_lower,
                                               f"{abstract} {method_text}")
            if len(common_terms) > 3:
                relations.append(("继承", p, common_terms))
            elif len(common_terms) > 0:
                relations.append(("相关", p, common_terms))

        if relations:
            positioning.append(f"### 与「{category}」的关系\n")
            for relation_type, paper, terms in relations:
                first_author = _get_first_author(paper)
                doi = paper.get("doi", "N/A")
                if relation_type == "继承":
                    positioning.append(
                        f"- **继承**: 本工作借鉴了 {first_author} et al. "
                        f"[{doi}] 中 {', '.join(terms[:3])} 的思路，"
                        f"但在 [具体差异] 方面做出了改进。"
                    )
                else:
                    positioning.append(
                        f"- **区别**: 与 {first_author} et al. [{doi}] 不同，"
                        f"本工作聚焦于 [自身独特视角]，"
                        f"而非 [该工作的关注点]。"
                    )
            positioning.append("")

    positioning.append("### 总结定位\n")
    positioning.append(
        "本工作 [继承/区别于] 上述各类方法，核心贡献在于 "
        "[填写自身核心贡献]。与已有工作相比，本方法的独特优势在于 "
        "[填写差异化优势]。\n"
    )

    return "\n".join(positioning)


def _find_common_terms(text1, text2):
    """找出两段文本中的共有专业术语。"""
    # 简单实现：提取多词短语的交集
    terms1 = set(re.findall(r'\b[a-z]+(?:\s+[a-z]+){1,2}\b', text1))
    terms2 = set(re.findall(r'\b[a-z]+(?:\s+[a-z]+){1,2}\b', text2))

    # 过滤掉常见的停用词组合
    stop_phrases = {"of the", "in the", "for the", "on the", "with the",
                    "and the", "to the", "from the", "by the", "at the",
                    "this paper", "we propose", "et al"}
    common = terms1 & terms2 - stop_phrases

    return list(common)[:10]
```

---

## 完整编排脚本

以下是将全部步骤串联的端到端 Python 脚本：

```python
#!/usr/bin/env python3
"""
相关工作生成器 (Related Work Writer) — 完整编排脚本

用法:
    export ACCESS_KEY="your_access_key"
    python3 related_work_writer.py

可修改下方 CONFIG 区域的参数来调整输入。
"""

import os
import re
import sys
import time
import json
import requests
from datetime import datetime
from collections import defaultdict

# ============================================================
# 配置
# ============================================================

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误: 请设置环境变量 ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}

# -- 用户可修改区域 --
CONFIG = {
    # 自身研究信息
    "topic": "equivariant graph neural network for molecular force field",
    "method_description": (
        "We propose an equivariant graph neural network that incorporates "
        "geometric symmetry constraints for predicting molecular force fields, "
        "achieving chemical accuracy with improved data efficiency."
    ),

    # 检索参数
    "keywords": [
        "graph neural network", "molecular force field",
        "equivariant neural network", "machine learning potential",
        "neural network interatomic potential"
    ],

    # 组织模式: "by-method", "by-chronological", "by-problem"
    "organization_mode": "by-method",

    # 必须引用的论文 DOI 列表
    "must_cite_papers": [
        "10.1038/s41586-021-03819-2",   # AlphaFold2
    ],

    # 解析参数
    "top_n_parse": 5,

    # 知识库 ID（0 = 不使用知识库）
    "knowledge_base_id": 0,
}


# ============================================================
# 步骤 1: 论文语义检索
# ============================================================

def step1_search(config):
    print(f"\n{'='*60}")
    print(f"步骤 1: 论文语义检索")
    print(f"  主题: {config['topic']}")
    print(f"  关键词: {config['keywords']}")
    print(f"{'='*60}\n")

    payload = {
        "words": config["keywords"],
        "question": config["topic"],
        "type": 5,
        "pageSize": 30
    }

    r = requests.post(
        f"{BASE}/v1/paper/rag/pass/keyword",
        headers=HEADERS_JSON,
        json=payload
    )
    r.raise_for_status()

    text = r.text.strip()
    first_line = text.split('\n')[0]
    data = json.loads(first_line)

    if data.get("code") != 0:
        print(f"检索失败: {data.get('message')}")
        sys.exit(1)

    papers = data["data"]
    papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)

    # 合并必须引用的论文
    existing_dois = {p.get("doi", "") for p in papers}
    for doi in config.get("must_cite_papers", []):
        if doi not in existing_dois:
            extra_payload = {
                "words": [doi],
                "question": doi,
                "type": 5,
                "pageSize": 1
            }
            try:
                r2 = requests.post(
                    f"{BASE}/v1/paper/rag/pass/keyword",
                    headers=HEADERS_JSON,
                    json=extra_payload
                )
                r2.raise_for_status()
                extra_data = json.loads(r2.text.strip().split('\n')[0])
                if extra_data.get("code") == 0 and extra_data.get("data"):
                    papers.append(extra_data["data"][0])
                    print(f"  补充必引论文: {doi}")
            except Exception as e:
                print(f"  [警告] 无法检索必引论文 {doi}: {e}")

    print(f"检索到 {len(papers)} 篇论文，按引用数排序:\n")
    for i, p in enumerate(papers[:10]):
        print(f"  {i+1:2d}. {p['enName'][:70]}")
        print(f"      DOI: {p.get('doi', 'N/A')} | "
              f"引用: {p.get('citationNums', 0)} | "
              f"日期: {p.get('coverDateStart', 'N/A')}")

    return papers


# ============================================================
# 步骤 2: 关键论文全文解析
# ============================================================

def step2_parse(papers, top_n):
    print(f"\n{'='*60}")
    print(f"步骤 2: 关键论文全文解析 (Top-{top_n})")
    print(f"{'='*60}\n")

    selected = papers[:top_n]
    tokens = {}
    parsed_contents = {}

    # 提交解析任务
    for p in selected:
        doi = p.get("doi", "")
        if not doi:
            continue

        pdf_url = f"https://doi.org/{doi}"
        try:
            r = requests.post(
                f"{BASE}/v1/parse/trigger-url-async",
                headers=HEADERS_JSON,
                json={
                    "url": pdf_url,
                    "sync": False,
                    "textual": True,
                    "table": True,
                    "expression": True,
                    "equation": True,
                    "pages": [0, 1, 2],
                    "timeout": 1800
                }
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("code"):
                tokens[doi] = data["token"]
                print(f"  提交: {doi} -> token={data['token'][:16]}...")
            else:
                print(f"  跳过: {doi} -> {data.get('message', 'error')}")
        except Exception as e:
            print(f"  失败: {doi} -> {e}")

    if not tokens:
        print("  警告: 无法提交任何解析任务，继续使用摘要信息")
        return parsed_contents

    # 轮询结果
    print(f"\n  等待 {len(tokens)} 个解析任务完成...")
    pending = dict(tokens)
    max_wait = 180
    start = time.time()

    while pending and (time.time() - start) < max_wait:
        time.sleep(3)
        done_keys = []
        for doi, token in pending.items():
            try:
                r = requests.post(
                    f"{BASE}/v1/parse/get-result",
                    headers=HEADERS_JSON,
                    json={
                        "token": token,
                        "content": True,
                        "objects": False,
                        "pages_dict": False
                    }
                )
                r.raise_for_status()
                result = r.json()
                status = result.get("status", "")

                if status == "success":
                    content = result.get("content", "")
                    # 提取方法段落和贡献摘要
                    method_section = _extract_section_text(content, "method")
                    contribution = _extract_contribution_text(content)
                    parsed_contents[doi] = {
                        "content": content,
                        "method": method_section,
                        "contribution": contribution
                    }
                    print(f"  完成: {doi} ({len(content)} 字符)")
                    done_keys.append(doi)
                elif status == "failed":
                    print(f"  失败: {doi}")
                    done_keys.append(doi)
            except Exception as e:
                print(f"  错误: {doi} -> {e}")

        for k in done_keys:
            del pending[k]

    if pending:
        print(f"  超时: {len(pending)} 个任务未完成")

    print(f"  解析完成: {len(parsed_contents)}/{len(tokens)} 篇")
    return parsed_contents


def _extract_section_text(text, section_name):
    """从解析文本中提取指定章节。"""
    patterns = {
        "method": r'(?i)(method|approach|methodology|proposed\s+method)',
        "related": r'(?i)(related\s+work|background|literature\s+review)',
    }
    pattern = patterns.get(section_name, section_name)
    sections = re.split(r'\\begin\{(?:section|subsection)\}', text)
    for sec in sections:
        first_line = sec.strip()[:200]
        if re.search(pattern, first_line, re.IGNORECASE):
            return sec[:3000]
    return ""


def _extract_contribution_text(text):
    """从全文中提取核心贡献句。"""
    patterns = [
        r'[^.]*(?:we\s+propose|we\s+present|we\s+introduce|we\s+develop)[^.]+\.',
        r'[^.]*(?:this\s+paper\s+presents?|this\s+work\s+proposes?)[^.]+\.',
        r'[^.]*(?:our\s+(?:main\s+)?contribution)[^.]+\.',
    ]
    contributions = []
    for pat in patterns:
        matches = re.findall(pat, text[:5000], re.IGNORECASE)
        contributions.extend(matches)
    return " ".join(contributions[:3]) if contributions else ""


# ============================================================
# 步骤 3: 知识库笔记检索
# ============================================================

def step3_knowledge_base(config):
    kb_id = config.get("knowledge_base_id", 0)
    if kb_id == 0:
        print(f"\n{'='*60}")
        print(f"步骤 3: 知识库笔记检索 (跳过 — 未指定知识库 ID)")
        print(f"{'='*60}")
        return []

    print(f"\n{'='*60}")
    print(f"步骤 3: 知识库笔记检索 (ID={kb_id})")
    print(f"{'='*60}\n")

    payload = {
        "queryContent": config["topic"],
        "nodesId": 0,
        "knowledgeBaseId": kb_id
    }

    try:
        r = requests.post(
            f"{BASE}/v1/knowledge/file/search",
            headers=HEADERS_JSON,
            json=payload
        )
        r.raise_for_status()
        data = r.json()

        if data.get("code") != 0:
            print(f"  搜索失败: {data.get('message')}")
            return []

        files = data.get("data", {}).get("Files", [])
        total = data.get("data", {}).get("total", 0)
        print(f"  找到 {total} 条相关笔记")
        for f in files[:5]:
            print(f"  - {f.get('fileName', '未命名')}: "
                  f"{f.get('content', '')[:80]}...")
        return files

    except Exception as e:
        print(f"  检索异常: {e}")
        return []


# ============================================================
# 步骤 4: 分类组织与生成
# ============================================================

def step4_generate(config, papers, parsed_contents, notes):
    mode = config["organization_mode"]
    method_desc = config["method_description"]

    print(f"\n{'='*60}")
    print(f"步骤 4: 分类组织与生成")
    print(f"  组织模式: {mode}")
    print(f"{'='*60}\n")

    # 4a. 分类论文
    if mode == "by-method":
        categories = _organize_by_method(papers, parsed_contents)
    elif mode == "by-chronological":
        categories = _organize_by_chronological(papers)
    elif mode == "by-problem":
        categories = _organize_by_problem(papers, parsed_contents)
    else:
        print(f"  未知模式: {mode}，使用默认 by-method")
        categories = _organize_by_method(papers, parsed_contents)

    print(f"  分为 {len(categories)} 个类别:")
    for name, cat_papers in categories.items():
        print(f"    - {name}: {len(cat_papers)} 篇")

    # 4b. 生成段落草稿
    print("\n  生成 Related Work 段落草稿...\n")
    paragraphs = _generate_paragraphs(categories, papers, parsed_contents, mode)

    # 4c. 生成 BibTeX
    print("  生成 BibTeX 引用列表...")
    bibtex = _generate_bibtex_entries(papers)

    # 4d. 定位分析
    print("  生成定位关系分析...")
    positioning = _generate_positioning(categories, method_desc, parsed_contents)

    # 组装完整输出
    output = []
    output.append("# Related Work 草稿\n")
    output.append(f"> 生成时间: {datetime.now().isoformat()}")
    output.append(f"> 组织模式: {mode}")
    output.append(f"> 检索论文数: {len(papers)}")
    output.append(f"> 全文解析数: {len(parsed_contents)}")
    if notes:
        output.append(f"> 知识库笔记数: {len(notes)}")
    output.append("")

    output.append("## 相关工作段落\n")
    output.append(paragraphs)

    output.append("\n---\n")
    output.append(positioning)

    fence = chr(96) * 3
    output.append("\n---\n")
    output.append("## BibTeX 引用列表\n")
    output.append(f"{fence}bibtex")
    output.append(bibtex)
    output.append(fence)

    full_output = "\n".join(output)
    print("\n" + full_output)
    return full_output


def _organize_by_method(papers, parsed_contents):
    """按方法分类。"""
    method_keywords = {
        "基于图神经网络的方法": [
            "graph neural network", "GNN", "message passing",
            "graph convolutional", "graph attention"
        ],
        "基于 Transformer 的方法": [
            "transformer", "attention mechanism", "self-attention"
        ],
        "基于传统机器学习的方法": [
            "random forest", "support vector", "kernel method",
            "gaussian process", "descriptor"
        ],
        "基于物理信息的方法": [
            "physics-informed", "physics-based", "equivariant",
            "invariant", "symmetry"
        ],
        "其他方法": []
    }
    return _classify_papers(papers, method_keywords)


def _organize_by_chronological(papers):
    """按时间分类。"""
    papers_by_year = defaultdict(list)
    for p in papers:
        year = p.get("coverDateStart", "")[:4]
        if year:
            papers_by_year[int(year)].append(p)

    if not papers_by_year:
        return {"全部论文": papers}

    min_year = min(papers_by_year.keys())
    max_year = max(papers_by_year.keys())
    span = max_year - min_year

    if span <= 3:
        return {f"{y} 年": papers_by_year[y]
                for y in sorted(papers_by_year.keys())}

    if span <= 8:
        stages = {}
        years = sorted(papers_by_year.keys())
        i = 0
        while i < len(years):
            s = years[i]
            e = min(s + 2, years[-1])
            name = f"{s}-{e} 年" if s != e else f"{s} 年"
            stage_papers = []
            for y in range(s, e + 1):
                stage_papers.extend(papers_by_year.get(y, []))
            if stage_papers:
                stages[name] = stage_papers
            i += (e - s + 1)
        return stages

    mid = min_year + span // 3
    late = min_year + 2 * span // 3
    stages = {}
    early_key = f"早期工作 ({min_year}-{mid})"
    mid_key = f"发展阶段 ({mid+1}-{late})"
    late_key = f"近期进展 ({late+1}-{max_year})"
    stages[early_key] = []
    stages[mid_key] = []
    stages[late_key] = []
    for year, ps in papers_by_year.items():
        if year <= mid:
            stages[early_key].extend(ps)
        elif year <= late:
            stages[mid_key].extend(ps)
        else:
            stages[late_key].extend(ps)
    return {k: v for k, v in stages.items() if v}


def _organize_by_problem(papers, parsed_contents):
    """按问题分类。"""
    problem_keywords = {
        "数据效率问题": [
            "data efficiency", "small sample", "few-shot",
            "data scarcity", "limited data"
        ],
        "可解释性问题": [
            "interpretability", "explainability", "interpretable",
            "explainable", "black box"
        ],
        "泛化能力问题": [
            "generalization", "transferability", "domain adaptation",
            "out-of-distribution"
        ],
        "计算效率问题": [
            "computational efficiency", "scalability", "large-scale",
            "acceleration"
        ],
        "精度问题": [
            "accuracy", "precision", "chemical accuracy",
            "state-of-the-art"
        ],
        "其他相关工作": []
    }
    return _classify_papers(papers, problem_keywords)


def _classify_papers(papers, keyword_map):
    """通用分类函数。"""
    categories = {}
    fallback_key = list(keyword_map.keys())[-1]  # 最后一个为兜底类别

    for p in papers:
        title = p.get("enName", "").lower()
        abstract = p.get("enAbstract", "").lower()
        text = f"{title} {abstract}"

        assigned = False
        for category, keywords in keyword_map.items():
            if category == fallback_key and not keywords:
                continue
            for kw in keywords:
                if kw.lower() in text:
                    categories.setdefault(category, []).append(p)
                    assigned = True
                    break
            if assigned:
                break

        if not assigned:
            categories.setdefault(fallback_key, []).append(p)

    return categories


def _generate_paragraphs(categories, papers, parsed_contents, mode):
    """生成各分类的综述段落和过渡句。"""
    # 引用编号映射
    cite_map = {}
    for i, p in enumerate(papers, 1):
        doi = p.get("doi", "")
        if doi:
            cite_map[doi] = i

    paragraphs = []
    cat_names = list(categories.keys())

    for idx, (category, cat_papers) in enumerate(categories.items()):
        paragraphs.append(f"### {category}\n")

        sorted_cat = sorted(cat_papers,
                            key=lambda p: p.get("citationNums", 0),
                            reverse=True)

        lines = []
        for p in sorted_cat[:5]:
            doi = p.get("doi", "")
            cite_num = cite_map.get(doi, "?")
            abstract = p.get("enAbstract", "")
            parsed = parsed_contents.get(doi, {})
            contribution = parsed.get("contribution", "")

            # 提取第一作者
            authors = p.get("authors", "Unknown")
            if isinstance(authors, list):
                first = str(authors[0]).split()[-1] if authors else "Unknown"
            else:
                first = str(authors).split(",")[0].split()[-1]

            if contribution:
                lines.append(
                    f"{first} et al. [{cite_num}] {contribution[:200].strip()}"
                )
            elif abstract:
                sentences = abstract.replace(". ", ".\n").split("\n")
                key = None
                for s in sentences:
                    sl = s.lower().strip()
                    if any(kw in sl for kw in ["propose", "present",
                                                "introduce", "show that"]):
                        key = s.strip()
                        break
                if not key and len(sentences) > 1:
                    key = sentences[1].strip()
                elif not key:
                    key = sentences[0].strip()
                lines.append(f"{first} et al. [{cite_num}] {key[:200]}")

        paragraphs.append(" ".join(lines) + "\n")

        # 过渡句
        if idx < len(cat_names) - 1:
            next_cat = cat_names[idx + 1]
            if mode == "by-method":
                transition = (
                    f"除了上述{category}的工作之外，"
                    f"另一类重要的研究方向是{next_cat}。"
                )
            elif mode == "by-chronological":
                transition = (
                    f"在{category}的基础上，"
                    f"{next_cat}的研究在方法和性能上取得了进一步突破。"
                )
            elif mode == "by-problem":
                transition = (
                    f"与解决{category}的工作不同，"
                    f"另一组研究重点关注{next_cat}。"
                )
            else:
                transition = f"此外，{next_cat}也是相关的研究方向。"
            paragraphs.append(f"_{transition}_\n")

    return "\n".join(paragraphs)


def _generate_bibtex_entries(papers):
    """生成 BibTeX 条目。"""
    entries = []
    for p in papers:
        doi = p.get("doi", "")
        title = p.get("enName", "Untitled")
        authors_raw = p.get("authors", "Unknown")
        journal = p.get("publicationEnName", "")
        year = p.get("coverDateStart", "")[:4]
        volume = p.get("volume", "")
        pages = p.get("pages", "")
        citations = p.get("citationNums", 0)

        if isinstance(authors_raw, list):
            authors = " and ".join(str(a) for a in authors_raw)
        else:
            authors = str(authors_raw)

        # cite key
        if isinstance(authors_raw, list) and authors_raw:
            first_last = str(authors_raw[0]).split()[-1].lower()
        else:
            first_last = str(authors_raw).split(",")[0].split()[-1].lower()
        first_last = re.sub(r'[^a-z]', '', first_last)
        title_word = re.sub(r'[^a-zA-Z]', '',
                             title.split()[0]).lower() if title else "paper"
        cite_key = f"{first_last}{year}{title_word}"

        entry = f"@article{{{cite_key},\n"
        entry += f"  title     = {{{title}}},\n"
        entry += f"  author    = {{{authors}}},\n"
        entry += f"  journal   = {{{journal}}},\n"
        entry += f"  year      = {{{year}}},"
        if volume:
            entry += f"\n  volume    = {{{volume}}},"
        if pages:
            entry += f"\n  pages     = {{{pages}}},"
        if doi:
            entry += f"\n  doi       = {{{doi}}},"
        entry += f"\n  note      = {{Cited by {citations}}}\n}}"

        entries.append(entry)

    return "\n\n".join(entries)


def _generate_positioning(categories, method_desc, parsed_contents):
    """生成自身工作定位分析。"""
    lines = []
    lines.append("## 自身工作定位分析\n")

    method_lower = method_desc.lower()

    for category, cat_papers in categories.items():
        has_relation = False
        relation_lines = []

        for p in cat_papers[:3]:
            abstract = p.get("enAbstract", "").lower()
            parsed = parsed_contents.get(p.get("doi", ""), {})
            method_text = parsed.get("method", "").lower()
            combined = f"{abstract} {method_text}"

            # 共词分析
            terms1 = set(re.findall(r'\b[a-z]+(?:\s+[a-z]+){1,2}\b',
                                     method_lower))
            terms2 = set(re.findall(r'\b[a-z]+(?:\s+[a-z]+){1,2}\b',
                                     combined))
            stop = {"of the", "in the", "for the", "on the", "with the",
                    "and the", "to the", "from the", "by the", "this paper"}
            common = list((terms1 & terms2) - stop)[:5]

            if not common:
                continue

            authors = p.get("authors", "Unknown")
            if isinstance(authors, list):
                first = str(authors[0]).split()[-1] if authors else "Unknown"
            else:
                first = str(authors).split(",")[0].split()[-1]
            doi = p.get("doi", "N/A")

            if len(common) > 3:
                relation_lines.append(
                    f"- **继承**: 本工作借鉴了 {first} et al. [{doi}] "
                    f"中 {', '.join(common[:3])} 的思路，"
                    f"但在 [具体差异] 方面做出了改进。"
                )
            else:
                relation_lines.append(
                    f"- **区别**: 与 {first} et al. [{doi}] 不同，"
                    f"本工作聚焦于 [自身独特视角]。"
                )
            has_relation = True

        if has_relation:
            lines.append(f"### 与「{category}」的关系\n")
            lines.extend(relation_lines)
            lines.append("")

    lines.append("### 总结定位\n")
    lines.append(
        "本工作 [继承/区别于] 上述各类方法，核心贡献在于 "
        "[填写自身核心贡献]。与已有工作相比，本方法的独特优势在于 "
        "[填写差异化优势]。"
    )

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  相关工作生成器 (Related Work Writer)")
    print(f"  主题: {config['topic']}")
    print(f"  组织模式: {config['organization_mode']}")
    print(f"{'#'*60}")

    # 步骤 1: 论文检索
    papers = step1_search(config)
    if not papers:
        print("未检索到论文，退出")
        sys.exit(1)

    # 步骤 2: 关键论文解析
    parsed_contents = step2_parse(papers, config["top_n_parse"])

    # 步骤 3: 知识库笔记检索
    notes = step3_knowledge_base(config)

    # 步骤 4: 分类组织与生成
    output = step4_generate(config, papers, parsed_contents, notes)

    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"related_work_{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\nRelated Work 草稿已保存到: {output_file}")

    bibtex_file = f"references_{timestamp}.bib"
    bibtex_text = _generate_bibtex_entries(papers)
    with open(bibtex_file, "w", encoding="utf-8") as f:
        f.write(bibtex_text)
    print(f"BibTeX 引用列表已保存到: {bibtex_file}")


if __name__ == "__main__":
    main()
```

---

## 使用示例

### 示例 1: 按方法分类（默认）

```python
CONFIG = {
    "topic": "equivariant graph neural network for molecular force field",
    "method_description": "We propose an equivariant GNN with geometric constraints...",
    "keywords": ["graph neural network", "molecular force field", "equivariant"],
    "organization_mode": "by-method",
    "must_cite_papers": [],
    "top_n_parse": 5,
    "knowledge_base_id": 0,
}
```

输出结构：
```
### 基于图神经网络的方法
Smith et al. [1] ... Chen et al. [3] ...

_除了上述基于图神经网络的方法的工作之外，另一类重要的研究方向是基于 Transformer 的方法。_

### 基于 Transformer 的方法
Wang et al. [5] ... Li et al. [8] ...
```

### 示例 2: 按时间线组织

```python
CONFIG["organization_mode"] = "by-chronological"
```

输出结构：
```
### 早期工作 (2018-2020)
...
_在早期工作的基础上，发展阶段的研究在方法和性能上取得了进一步突破。_

### 发展阶段 (2021-2022)
...

### 近期进展 (2023-2025)
...
```

### 示例 3: 按问题组织

```python
CONFIG["organization_mode"] = "by-problem"
```

输出结构：
```
### 精度问题
...
_与解决精度问题的工作不同，另一组研究重点关注数据效率问题。_

### 数据效率问题
...

### 泛化能力问题
...
```

---

## 使用技巧

### 关键词选择

```python
# 推荐: 3-8 个专业英文术语，覆盖核心概念和相关领域
keywords = ["graph neural network", "molecular force field",
            "equivariant neural network", "machine learning potential",
            "neural network interatomic potential"]

# 不推荐: 太笼统
keywords = ["deep learning", "chemistry"]
```

### 必须引用的论文

在 `must_cite_papers` 中列出导师/审稿人期望引用的论文 DOI，脚本会确保这些论文出现在结果中：

```python
must_cite_papers = [
    "10.1038/s41586-021-03819-2",  # AlphaFold2
    "10.1103/PhysRevLett.120.143001",  # SchNet
]
```

### 知识库集成

如果在 Bohrium 知识库中有积累的文献笔记，指定 `knowledge_base_id` 可以让生成器参考个人理解：

```python
CONFIG["knowledge_base_id"] = 12345  # 你的知识库 ID
```

### 分类关键词自定义

不同研究领域需要调整分类关键词。修改 `_organize_by_method` 或 `_organize_by_problem` 中的 `keyword_map` 字典即可适配新领域。

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 检索结果太少 | 关键词太窄 | 增加关键词，使用更通用的术语 |
| 分类不均匀 | 分类关键词不匹配目标领域 | 根据领域特点自定义 `keyword_map` |
| 全文解析失败 | DOI 对应的 PDF 不可直接下载 | 改用 arXiv PDF 链接或减少 `top_n_parse` |
| BibTeX 格式不标准 | 论文元数据不完整 | 手动补充缺失字段（volume、pages 等） |
| 过渡句生硬 | 自动生成模板化 | 以生成的过渡句为基础，手动润色 |
| 定位分析模板化 | 共词分析能力有限 | 替换 `[具体差异]` 等占位符为实际内容 |
| 知识库搜索无结果 | knowledge_base_id 为 0 或笔记不匹配 | 确认知识库 ID 正确且包含相关笔记 |
| 响应含多行 JSON | paper-search 返回 streaming 格式 | 脚本已处理：取第一行 `text.split('\n')[0]` |
| 401 Unauthorized | accessKey 无效 | 确认 ACCESS_KEY 正确 |

---

## 搭配使用

- **related-work-writer** 生成草稿 → 人工润色为正式段落
- **paper-dissector** 深度拆解关键论文 → 补充到 Related Work 细节
- **literature-review** 全面综述 → **related-work-writer** 聚焦写作
- **knowledge-base** 管理文献笔记 → 为 Related Work 提供个人积累
- **grant-helper** 基金申请 → 复用 Related Work 中的研究现状分析
