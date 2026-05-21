---
name: literature-review
description: "Automated literature review workflow combining paper search, PDF parsing, and knowledge graph analysis. Use when: user asks for a literature review, research summary, or state-of-the-art analysis on a topic. NOT for: single paper search (use bohrium-paper-search), single paper parsing (use bohrium-pdf-parser)."
---

# SKILL: 文献综述助手 (Literature Review Assistant)

## 概述

文献综述助手是一个**编排型 Skill**，串联多个 Bohrium 原子 Skill，自动完成从论文检索、全文解析、知识图谱分析到结构化综述生成的完整流程。

**组合的原子 Skill：**

| 步骤 | 原子 Skill | 端点 | 功能 |
|------|-----------|------|------|
| 1 | `bohrium-paper-search` | `/v1/paper/rag/pass/keyword` | 语义检索相关论文 |
| 2 | `bohrium-pdf-parser` | `/v1/parse/trigger-url-async` + `/v1/parse/get-result` | 解析 Top-N 论文全文 |
| 3 | `bohrium-lkm` | `/v1/lkm/claims/match` + `/v1/lkm/search` | 提取概念关系，构建子领域知识图谱 |
| 4 | 综合分析 | — | 组织为结构化综述 |

**适用场景：**

- 针对某一研究主题生成完整文献综述
- 研究领域现状分析（state-of-the-art）
- 方法对比与技术路线梳理
- 研究趋势与前沿热点分析

**不适用：**

- 单篇论文检索 → `bohrium-paper-search`
- 单篇 PDF 解析 → `bohrium-pdf-parser`
- 知识库文件管理 → `bohrium-knowledge-base`
- 科学论断验证 → `bohrium-lkm`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"literature-review": {
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
| `topic` | string | 是 | — | 研究主题/关键词 |
| `keywords` | string[] | 否 | 从 topic 提取 | 检索关键词列表（3-8 个英文术语） |
| `time_range` | int | 否 | 5 | 检索时间范围（年），从当前向前推算 |
| `start_time` | string | 否 | 自动计算 | 起始日期 `YYYY-MM-DD` |
| `end_time` | string | 否 | 今天 | 截止日期 `YYYY-MM-DD` |
| `jcr_zones` | string[] | 否 | [] | JCR 分区筛选，如 `["Q1", "Q2"]` |
| `top_n` | int | 否 | 10 | 全文解析的论文数量 |
| `depth` | string | 否 | `"quick"` | 综述深度：`"quick"`（快速概览）/ `"deep"`（深度分析） |

---

## 输出格式

综述结果包含以下结构化部分：

### 1. 研究时间线

按时间排列的关键里程碑，标注代表性论文和突破性进展。

### 2. 方法对比矩阵

| 方法 | 优势 | 局限性 | 适用场景 | 代表论文 |
|------|------|--------|----------|----------|
| 方法 A | ... | ... | ... | DOI |
| 方法 B | ... | ... | ... | DOI |

### 3. 核心发现列表

按主题聚类的关键研究发现，附文献来源。

### 4. 争议与未解决问题

当前领域中存在的争议性观点和开放性问题。

### 5. 推荐阅读清单

精选论文列表，每篇附推荐理由（如：奠基性工作、方法创新、最新进展等）。

---

## 数据质量控制（关键步骤）

API 返回的论文列表可能包含大量不相关结果（关键词语义泛化导致），**必须在生成报告前进行相关性过滤**。

### 过滤规则

```python
def filter_relevant_papers(papers, core_keywords, min_hits=2):
    """
    只保留标题+摘要中至少命中 min_hits 个核心关键词的论文。
    
    core_keywords: 用户主题的核心术语（不是搜索关键词，而是判断相关性的术语）
    例如用户搜索 "solid-state electrolyte for lithium battery"
    core_keywords = ["solid", "electrolyte", "lithium", "ionic", "garnet", "sulfide", "polymer"]
    """
    filtered = []
    for p in papers:
        text = (p.get("enName", "") + " " + p.get("enAbstract", "")).lower()
        hits = sum(1 for k in core_keywords if k.lower() in text)
        if hits >= min_hits:
            filtered.append(p)
    return filtered
```

### 过滤后检查

- 如果过滤后 <5 篇：放宽 `min_hits=1` 或扩展关键词
- 如果过滤后仍大量不相关：在报告中明确说明「检索精度有限，以下结果经过人工标注的关键词过滤」
- **永远不要**在报告中展示明显不相关的论文（如搜固态电解质却出现"MoS₂阴极"相关论文）

---

## 报告分析深度要求

**报告不是 API 数据的格式化转储**。你是一个专业研究者，必须在报告中提供：

1. **有数据支撑的分析判断**：从论文分布、引用趋势、期刊分布中得出结论
2. **从摘要中提取定量结果**：电导率数值、循环次数、效率指标等具体数字
3. **跨论文的对比和综合**：不同方法的优劣、不同材料的性能比较
4. **基于数据的空白识别**：哪个方向论文少但重要性高？哪些问题反复被提到但未解决？
5. **"So what?" 分析层**：每个发现后必须跟一句 "这意味着什么" 的判断。将挑战**归纳为 2-4 个结构性矛盾**（如 trade-off），解释为什么难，而非只列举 "however" 句

### 文献时效性与覆盖范围

**必须区分两类文献，在报告中分别标注**：
- **奠基性工作（Foundational）**：经典引用，不受时间限制（如 Goodenough 1980, Kamaya 2011）
- **前沿进展（Frontier）**：最近 1-2 年的突破性工作，应占推荐精读列表的 ≥50%

**覆盖范围声明**（报告必须包含）：
> 本报告基于 Bohrium 学术搜索（覆盖期刊论文、顶会论文、arXiv 预印本）。如发现特定子方向检索结果偏少，已通过多轮关键词扩展补充。

**时效性要求**：
- 如果是快速迭代领域（AI4Science、电池、生物医药），最近 2 年的论文在正文讨论中应占 ≥40%
- "推荐精读"列表中 2020 年之前的论文占比不超过 30%（除非该领域非常经典/缓慢）
- 如果检索结果偏旧（多为 2020-2022），必须通过扩展关键词或缩小时间窗口二次检索，补充 2023-2025 的最新工作

**检索排序策略（避免引用时效偏差）**：
- 不能仅按引用数降序选择论文——这会系统性偏向老论文
- 必须分两路取论文：
  - 经典高引（按总引用数 Top-N）：覆盖奠基性工作
  - 前沿高速（按"月均引用数"Top-N，12 个月内论文额外加权）：覆盖最新突破
- 推荐精读列表合并两组后去重，确保新老兼顾

### 定量声明溯源规则

**所有定量 claim 必须有来源标注**，违反即为报告质量不合格：
- ✅ "Li₆PS₅Cl 室温离子电导率 3.2 mS/cm [Zhang et al., CEJ 2024]"
- ✅ "接受率约 10-15%（估计值，基于该刊 2023 年公开数据）"
- ✅ "MAE = 0.02 eV（来源：OC20 Leaderboard, 2024-03 快照）"
- ❌ "降低 90% 计算量"（无来源）
- ❌ "接受率 <5%"（无来源）
- ❌ "MAE = 0.0044 eV"（未注明来自哪篇论文/哪个基准测试）

### 禁止的行为

- ❌ 只列标题不分析内容
- ❌ 用星级评分代替具体数据（如 "精度: ⭐⭐⭐⭐"）
- ❌ 写所有研究生都知道的常识（如 "固态电解质比液态安全"）
- ❌ 从标题猜测论文内容（如果没有摘要，就不要总结该论文）
- ❌ 截断标题或期刊名（必须完整展示）
- ❌ "关键挑战"章节只贴论文原文的 "however" 句子（这是引文堆砌，不是分析）
- ❌ 只讨论一个主要体系而遗漏该领域的近亲体系（如只讨论 Li-ion SSE 而完全不提 Na-ion SSE）

### 推荐的做法

- ✅ 引用具体数值："Li₆PS₅Cl 的室温离子电导率达到 3.2 mS/cm [Zhang 2024, CEJ]"
- ✅ 对比不同论文的结论差异："A组报道 Cu(111) 选择性最高 [ref1]，而 B组发现 Cu(100) 对 C₂ 产物更优 [ref2]，差异可能源于电位窗口不同"
- ✅ 从发表趋势推断："界面工程方向论文从 2022 年的 3 篇增至 2024 年的 15 篇，表明该方向正从基础研究进入实用阶段"
- ✅ 明确标注数据来源不足："由于 API 未返回全文，以下对比基于摘要信息，深度有限"
- ✅ 将挑战归纳为结构性矛盾："固态电解质面临 '导电率-稳定性 trade-off'：硫化物导电率高但空气稳定性差，氧化物稳定但导电率低且加工困难。这个矛盾的本质是..."
- ✅ 在报告末尾给出 "本报告未覆盖的重要方向" 清单（如近亲体系、交叉领域的最新工作）

---

## 工作流程图

```
输入: topic, keywords, time_range, depth
        │
        ▼
┌──────────────────────────────────────┐
│  步骤 1: 多轮渐进式论文检索            │
│  Round 1: 用户关键词 → 获取高引论文   │
│  Round 2: 从 Round 1 摘要中提取新术语 │
│           → 补充检索遗漏子方向         │
│  Round 3: LKM 知识图谱相邻概念        │
│           → 发现盲区子方向             │
│  → 合并去重、分两路排序（高引+高速）  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 2: Top-N 论文全文解析            │
│  POST /v1/parse/trigger-url-async    │
│  POST /v1/parse/get-result (轮询)     │
│  → 获取全文文本、表格、公式            │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 3: 知识图谱分析                  │
│  POST /v1/lkm/claims/match          │
│  POST /v1/lkm/search                │
│  → 提取概念关系                      │
│  → 验证核心论断                      │
│  → 发现潜在新论断                    │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 4: 综合分析与生成               │
│  → 研究时间线                        │
│  → 方法对比矩阵                      │
│  → 核心发现列表                      │
│  → 争议与未解决问题                   │
│  → 推荐阅读清单                      │
└──────────────┬───────────────────────┘
               │
               ▼ (可选)
┌──────────────────────────────────────┐
│  扩展: 存入知识库 / 推送飞书文档       │
│  POST /v1/knowledge/knowledge_base/  │
│       create                         │
└──────────────────────────────────────┘
```

---

## 通用代码模板

```python
import os, time, requests, json
from datetime import datetime, timedelta

AK = os.environ.get("ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
```

---

## 步骤 1: 论文语义检索

使用 `paper-search` 进行语义检索，按引用数和相关性排序，获取候选论文列表。

### Python 示例

```python
def search_papers(keywords, question, top_n=20, start_time="", end_time="",
                  jcr_zones=None):
    """
    语义检索相关论文。

    Args:
        keywords: 关键词列表，建议 3-8 个英文术语
        question: 研究问题的自然语言描述
        top_n: 返回论文数量
        start_time: 起始日期 YYYY-MM-DD，空字符串不限
        end_time: 截止日期 YYYY-MM-DD，空字符串不限
        jcr_zones: JCR 分区筛选，如 ["Q1", "Q2"]

    Returns:
        论文列表，按引用数降序排列
    """
    payload = {
        "words": keywords,
        "question": question,
        "type": 5,               # 题目+摘要+语料+图片+靶点 全方位检索
        "startTime": start_time,
        "endTime": end_time,
        "jcrZones": jcr_zones or [],
        "pageSize": top_n
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

    print(f"[步骤1] 检索到 {len(papers)} 篇论文")
    for i, p in enumerate(papers):
        print(f"  {i+1}. [{p.get('doi', 'N/A')}] {p['enName']}")
        print(f"     期刊: {p.get('publicationEnName', 'N/A')}, "
              f"IF: {p.get('impactFactor', 0)}, "
              f"引用: {p.get('citationNums', 0)}, "
              f"日期: {p.get('coverDateStart', 'N/A')}")

    return papers
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["deep learning", "molecular dynamics", "force field"],
    "question": "How to use deep learning for molecular dynamics force field development?",
    "type": 5,
    "startTime": "2021-01-01",
    "endTime": "2026-01-01",
    "jcrZones": ["Q1"],
    "pageSize": 20
  }'
```

---

## 步骤 2: Top-N 论文全文解析

对步骤 1 中引用数最高的 Top-N 论文进行全文解析，提取文本、表格和公式。

### Python 示例

```python
def parse_paper_async(paper_url, pages=None):
    """
    提交单篇论文解析任务。

    Args:
        paper_url: 论文 PDF 的 URL
        pages: 解析页码列表（0-indexed），None 则解析全部

    Returns:
        解析任务 token
    """
    payload = {
        "url": paper_url,
        "sync": False,
        "textual": True,
        "table": True,
        "expression": True,
        "equation": True,
        "pages": pages or [],
        "timeout": 1800
    }

    r = requests.post(
        f"{BASE}/v1/parse/trigger-url-async",
        headers=HEADERS_JSON,
        json=payload
    )
    r.raise_for_status()
    data = r.json()

    if data.get("code"):
        raise RuntimeError(f"提交解析失败: {data.get('message')}")

    return data["token"]


def poll_parse_result(token, max_attempts=60, interval=3):
    """
    轮询解析结果，直到成功或失败。

    Args:
        token: 解析任务 token
        max_attempts: 最大轮询次数
        interval: 轮询间隔（秒）

    Returns:
        解析出的全文内容字符串
    """
    for attempt in range(max_attempts):
        time.sleep(interval)
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
            return result.get("content", "")
        elif status == "failed":
            raise RuntimeError(f"解析失败: {result.get('description', 'unknown')}")

    raise TimeoutError(f"解析超时: token={token}, 已等待 {max_attempts * interval} 秒")


def parse_top_papers(papers, top_n=10):
    """
    批量解析 Top-N 论文全文。

    Args:
        papers: search_papers 返回的论文列表
        top_n: 解析数量

    Returns:
        dict: {doi: full_text_content}
    """
    selected = papers[:top_n]
    results = {}

    # 1. 提交所有解析任务
    tokens = {}
    for p in selected:
        doi = p.get("doi", "")
        if not doi:
            continue

        # 通过 DOI 构造常用 PDF URL（以 arXiv 和 Sci-Hub 为例）
        # 实际使用时需根据论文来源确定 PDF URL
        pdf_url = f"https://doi.org/{doi}"

        try:
            token = parse_paper_async(pdf_url)
            tokens[doi] = token
            print(f"  提交解析: {doi} -> token={token}")
        except Exception as e:
            print(f"  提交失败: {doi} -> {e}")

    # 2. 轮询所有解析结果
    print(f"\n[步骤2] 等待 {len(tokens)} 篇论文解析完成...")
    for doi, token in tokens.items():
        try:
            content = poll_parse_result(token)
            results[doi] = content
            print(f"  解析完成: {doi} ({len(content)} 字符)")
        except Exception as e:
            print(f"  解析失败: {doi} -> {e}")

    print(f"[步骤2] 成功解析 {len(results)}/{len(tokens)} 篇论文")
    return results
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 提交解析任务
TOKEN=$(curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/trigger-url-async" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "url": "https://arxiv.org/pdf/2107.06922",
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
  -d "{\"token\": \"$TOKEN\", \"content\": true, \"objects\": false, \"pages_dict\": false}"
```

---

## 步骤 3: 知识图谱分析

使用 LKM 的论断匹配和知识图谱搜索，提取核心概念之间的关系，验证关键结论。

### Python 示例

```python
def analyze_with_lkm(topic, papers, parsed_contents):
    """
    利用 LKM 进行知识图谱分析。

    Args:
        topic: 研究主题
        papers: 论文元数据列表
        parsed_contents: {doi: full_text} 解析结果

    Returns:
        dict: {
            "knowledge_graph": [...],   # 知识图谱搜索结果
            "claims": [...],            # 论断匹配结果
            "new_claims": [...]         # 潜在新论断
        }
    """
    analysis = {
        "knowledge_graph": [],
        "claims": [],
        "new_claims": []
    }

    # 3a. 知识图谱搜索 — 获取领域概念网络
    print(f"\n[步骤3a] 知识图谱搜索: {topic}")
    r = requests.post(
        f"{BASE}/v1/lkm/search",
        headers=HEADERS_JSON,
        json={"query": topic, "limit": 10}
    )
    r.raise_for_status()
    kg_data = r.json()
    analysis["knowledge_graph"] = kg_data.get("data", [])
    print(f"  找到 {len(analysis['knowledge_graph'])} 个知识节点")

    # 3b. 论断匹配 — 从论文摘要中提取核心论断并验证
    print(f"\n[步骤3b] 论断验证...")
    for p in papers[:10]:
        abstract = p.get("enAbstract", "")
        if not abstract or len(abstract) < 50:
            continue

        # 将摘要中的核心结论作为待验证论断
        # 取摘要的最后 1-2 句（通常是结论）
        sentences = abstract.replace(". ", ".\n").split("\n")
        conclusion = ". ".join(sentences[-2:]) if len(sentences) > 1 else abstract

        try:
            r = requests.post(
                f"{BASE}/v1/lkm/claims/match",
                headers=HEADERS_JSON,
                json={"text": conclusion[:500], "limit": 5}
            )
            r.raise_for_status()
            match_data = r.json()

            claim_result = {
                "paper_doi": p.get("doi", ""),
                "paper_title": p.get("enName", ""),
                "claim_text": conclusion[:200],
                "matches": match_data.get("data", {}).get("variables", []),
                "new_claim_likely": match_data.get("data", {}).get("new_claim_likely", False)
            }

            analysis["claims"].append(claim_result)

            if claim_result["new_claim_likely"]:
                analysis["new_claims"].append(claim_result)
                print(f"  [NEW] {p.get('enName', '')[:60]}...")
            else:
                match_count = len(claim_result["matches"])
                print(f"  [OK]  {p.get('enName', '')[:60]}... ({match_count} 条证据)")

        except Exception as e:
            print(f"  [ERR] {p.get('doi', '')}: {e}")

    print(f"\n[步骤3] 分析完成: {len(analysis['claims'])} 个论断, "
          f"{len(analysis['new_claims'])} 个潜在新发现")
    return analysis
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 知识图谱搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "deep learning molecular dynamics force field", "limit": 10}' | python3 -m json.tool

# 论断匹配
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/claims/match" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Graph neural networks can accurately predict molecular potential energy surfaces with chemical accuracy",
    "limit": 5
  }' | python3 -m json.tool
```

---

## 步骤 4: 综合分析与生成

将前三步的结果组织为结构化综述。

### Python 示例

```python
def synthesize_review(topic, papers, parsed_contents, lkm_analysis):
    """
    综合分析，生成结构化综述。

    Args:
        topic: 研究主题
        papers: 论文元数据列表
        parsed_contents: {doi: full_text} 解析结果
        lkm_analysis: LKM 分析结果

    Returns:
        dict: 结构化综述
    """
    review = {
        "topic": topic,
        "generated_at": datetime.now().isoformat(),
        "paper_count": len(papers),
        "parsed_count": len(parsed_contents),
        "timeline": [],
        "method_comparison": [],
        "core_findings": [],
        "controversies": [],
        "recommended_reading": []
    }

    # 4a. 研究时间线 — 按年份聚合论文
    papers_by_year = {}
    for p in papers:
        year = p.get("coverDateStart", "")[:4]
        if year:
            papers_by_year.setdefault(year, []).append(p)

    for year in sorted(papers_by_year.keys()):
        year_papers = papers_by_year[year]
        top_paper = max(year_papers, key=lambda x: x.get("citationNums", 0))
        review["timeline"].append({
            "year": year,
            "paper_count": len(year_papers),
            "milestone": top_paper.get("enName", ""),
            "milestone_doi": top_paper.get("doi", ""),
            "citations": top_paper.get("citationNums", 0)
        })

    # 4b. 核心发现列表 — 基于 LKM 论断分析
    for claim in lkm_analysis.get("claims", []):
        review["core_findings"].append({
            "finding": claim["claim_text"],
            "source_doi": claim["paper_doi"],
            "source_title": claim["paper_title"],
            "evidence_count": len(claim.get("matches", [])),
            "is_novel": claim.get("new_claim_likely", False)
        })

    # 4c. 争议与未解决问题 — 潜在新论断
    for new_claim in lkm_analysis.get("new_claims", []):
        review["controversies"].append({
            "question": new_claim["claim_text"],
            "source_doi": new_claim["paper_doi"],
            "reason": "LKM 标记为潜在新发现，文献支持较少"
        })

    # 4d. 推荐阅读清单 — 综合引用数、影响因子、新颖性
    for p in papers[:5]:
        reason = []
        if p.get("citationNums", 0) > 100:
            reason.append("高引用（奠基性工作）")
        if p.get("impactFactor", 0) > 10:
            reason.append(f"高影响因子期刊 (IF={p['impactFactor']})")
        if p.get("coverDateStart", "") >= (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"):
            reason.append("近一年最新进展")
        if not reason:
            reason.append("领域相关高质量论文")

        review["recommended_reading"].append({
            "doi": p.get("doi", ""),
            "title": p.get("enName", ""),
            "journal": p.get("publicationEnName", ""),
            "year": p.get("coverDateStart", "")[:4],
            "citations": p.get("citationNums", 0),
            "reason": "；".join(reason)
        })

    return review


def format_review_markdown(review):
    """
    将结构化综述格式化为 Markdown。
    """
    lines = []
    lines.append(f"# 文献综述: {review['topic']}")
    lines.append(f"\n> 生成时间: {review['generated_at']}")
    lines.append(f"> 检索论文数: {review['paper_count']}, "
                 f"全文解析数: {review['parsed_count']}")

    # 时间线
    lines.append("\n## 1. 研究时间线\n")
    for t in review["timeline"]:
        lines.append(f"- **{t['year']}** ({t['paper_count']} 篇) "
                     f"— {t['milestone']} (引用: {t['citations']})")

    # 核心发现
    lines.append("\n## 2. 核心发现\n")
    for i, f in enumerate(review["core_findings"], 1):
        novel_tag = " [NEW]" if f["is_novel"] else ""
        lines.append(f"{i}. {f['finding'][:150]}...{novel_tag}")
        lines.append(f"   - 来源: {f['source_title'][:80]} ({f['source_doi']})")
        lines.append(f"   - 证据数: {f['evidence_count']}")

    # 争议
    if review["controversies"]:
        lines.append("\n## 3. 争议与未解决问题\n")
        for c in review["controversies"]:
            lines.append(f"- **{c['question'][:150]}...**")
            lines.append(f"  - 来源: {c['source_doi']}")
            lines.append(f"  - 原因: {c['reason']}")

    # 推荐阅读
    lines.append("\n## 4. 推荐阅读清单\n")
    lines.append("| # | 标题 | 期刊 | 年份 | 引用 | 推荐理由 |")
    lines.append("|---|------|------|------|------|----------|")
    for i, r in enumerate(review["recommended_reading"], 1):
        lines.append(f"| {i} | {r['title'][:50]}... | {r['journal']} | "
                     f"{r['year']} | {r['citations']} | {r['reason']} |")

    return "\n".join(lines)
```

---

## 完整编排示例

以下是将全部步骤串联的端到端 Python 脚本：

```python
#!/usr/bin/env python3
"""
文献综述助手 — 完整编排脚本

用法:
    export ACCESS_KEY="your_access_key"
    python3 literature_review.py

可修改下方 CONFIG 区域的参数来调整检索范围和深度。
"""

import os
import sys
import time
import json
import requests
from datetime import datetime, timedelta

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
    "topic": "deep learning for molecular dynamics force field",
    "keywords": ["deep learning", "molecular dynamics", "force field",
                 "neural network potential", "machine learning interatomic potential"],
    "time_range_years": 5,
    "jcr_zones": ["Q1", "Q2"],
    "top_n_parse": 5,         # 全文解析 Top-N 篇（quick=5, deep=10）
    "depth": "quick",         # "quick" 或 "deep"
}


# ============================================================
# 步骤 1: 论文语义检索
# ============================================================

def step1_search_papers(config):
    end_time = datetime.now().strftime("%Y-%m-%d")
    start_time = (datetime.now() - timedelta(days=365 * config["time_range_years"])).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"步骤 1: 论文语义检索")
    print(f"  主题: {config['topic']}")
    print(f"  关键词: {config['keywords']}")
    print(f"  时间范围: {start_time} ~ {end_time}")
    print(f"  JCR 分区: {config['jcr_zones'] or '不限'}")
    print(f"{'='*60}\n")

    page_size = 20 if config["depth"] == "quick" else 50

    r = requests.post(f"{BASE}/v1/paper/rag/pass/keyword", headers=HEADERS_JSON, json={
        "words": config["keywords"],
        "question": config["topic"],
        "type": 5,
        "startTime": start_time,
        "endTime": end_time,
        "jcrZones": config["jcr_zones"],
        "pageSize": page_size
    })
    r.raise_for_status()

    text = r.text.strip()
    first_line = text.split('\n')[0]
    data = json.loads(first_line)

    if data.get("code") != 0:
        print(f"检索失败: {data.get('message')}")
        sys.exit(1)

    papers = data["data"]
    papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)

    print(f"检索到 {len(papers)} 篇论文，按引用数排序:\n")
    for i, p in enumerate(papers[:10]):
        print(f"  {i+1:2d}. {p['enName'][:70]}")
        print(f"      DOI: {p.get('doi', 'N/A')} | "
              f"IF: {p.get('impactFactor', 0)} | "
              f"引用: {p.get('citationNums', 0)} | "
              f"日期: {p.get('coverDateStart', 'N/A')}")

    return papers


# ============================================================
# 步骤 2: Top-N 论文全文解析
# ============================================================

def step2_parse_papers(papers, top_n):
    print(f"\n{'='*60}")
    print(f"步骤 2: 全文解析 Top-{top_n} 论文")
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
            r = requests.post(f"{BASE}/v1/parse/trigger-url-async", headers=HEADERS_JSON, json={
                "url": pdf_url,
                "sync": False,
                "textual": True,
                "table": True,
                "expression": True,
                "equation": True,
                "pages": [],    # 全部页
                "timeout": 1800
            })
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
        print("  警告: 无法提交任何解析任务，跳过全文解析步骤")
        return parsed_contents

    # 轮询结果
    print(f"\n  等待 {len(tokens)} 个解析任务完成...\n")
    pending = dict(tokens)
    max_wait = 180  # 最长等待 3 分钟
    start = time.time()

    while pending and (time.time() - start) < max_wait:
        time.sleep(3)
        done_keys = []
        for doi, token in pending.items():
            try:
                r = requests.post(f"{BASE}/v1/parse/get-result", headers=HEADERS_JSON, json={
                    "token": token,
                    "content": True,
                    "objects": False,
                    "pages_dict": False
                })
                r.raise_for_status()
                result = r.json()
                status = result.get("status", "")

                if status == "success":
                    content = result.get("content", "")
                    parsed_contents[doi] = content
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
        print(f"\n  超时: {len(pending)} 个任务未完成")

    print(f"\n  解析完成: {len(parsed_contents)}/{len(tokens)} 篇")
    return parsed_contents


# ============================================================
# 步骤 3: 知识图谱分析
# ============================================================

def step3_lkm_analysis(topic, papers):
    print(f"\n{'='*60}")
    print(f"步骤 3: 知识图谱分析")
    print(f"{'='*60}\n")

    analysis = {
        "knowledge_graph": [],
        "claims": [],
        "new_claims": []
    }

    # 3a. 知识图谱搜索
    print("  3a. 知识图谱搜索...")
    try:
        r = requests.post(f"{BASE}/v1/lkm/search", headers=HEADERS_JSON, json={
            "query": topic,
            "limit": 10
        })
        r.raise_for_status()
        kg_data = r.json()
        analysis["knowledge_graph"] = kg_data.get("data", [])
        print(f"      找到 {len(analysis['knowledge_graph'])} 个知识节点")
    except Exception as e:
        print(f"      知识图谱搜索失败: {e}")

    # 3b. 论断匹配
    print("\n  3b. 核心论断验证...")
    for p in papers[:10]:
        abstract = p.get("enAbstract", "")
        if not abstract or len(abstract) < 50:
            continue

        # 提取摘要末尾的结论
        sentences = abstract.replace(". ", ".\n").split("\n")
        conclusion = ". ".join(s.strip() for s in sentences[-2:] if s.strip())

        if len(conclusion) < 30:
            continue

        try:
            r = requests.post(f"{BASE}/v1/lkm/claims/match", headers=HEADERS_JSON, json={
                "text": conclusion[:500],
                "limit": 5
            })
            r.raise_for_status()
            match_data = r.json()

            claim_result = {
                "paper_doi": p.get("doi", ""),
                "paper_title": p.get("enName", ""),
                "claim_text": conclusion[:300],
                "matches": match_data.get("data", {}).get("variables", []),
                "new_claim_likely": match_data.get("data", {}).get("new_claim_likely", False)
            }
            analysis["claims"].append(claim_result)

            if claim_result["new_claim_likely"]:
                analysis["new_claims"].append(claim_result)
                print(f"      [NEW] {p['enName'][:60]}...")
            else:
                print(f"      [OK]  {p['enName'][:60]}... "
                      f"({len(claim_result['matches'])} 条证据)")
        except Exception as e:
            print(f"      [ERR] {p.get('doi', '')}: {e}")

    print(f"\n  分析完成: {len(analysis['claims'])} 个论断, "
          f"{len(analysis['new_claims'])} 个潜在新发现")
    return analysis


# ============================================================
# 步骤 4: 综合生成
# ============================================================

def step4_synthesize(topic, papers, parsed_contents, lkm_analysis):
    print(f"\n{'='*60}")
    print(f"步骤 4: 综合分析与生成")
    print(f"{'='*60}\n")

    review = {
        "topic": topic,
        "generated_at": datetime.now().isoformat(),
        "paper_count": len(papers),
        "parsed_count": len(parsed_contents),
        "timeline": [],
        "method_comparison": [],
        "core_findings": [],
        "controversies": [],
        "recommended_reading": []
    }

    # 时间线
    papers_by_year = {}
    for p in papers:
        year = p.get("coverDateStart", "")[:4]
        if year:
            papers_by_year.setdefault(year, []).append(p)

    for year in sorted(papers_by_year.keys()):
        year_papers = papers_by_year[year]
        top_paper = max(year_papers, key=lambda x: x.get("citationNums", 0))
        review["timeline"].append({
            "year": year,
            "paper_count": len(year_papers),
            "milestone": top_paper.get("enName", ""),
            "milestone_doi": top_paper.get("doi", ""),
            "citations": top_paper.get("citationNums", 0)
        })

    # 核心发现
    for claim in lkm_analysis.get("claims", []):
        review["core_findings"].append({
            "finding": claim["claim_text"],
            "source_doi": claim["paper_doi"],
            "source_title": claim["paper_title"],
            "evidence_count": len(claim.get("matches", [])),
            "is_novel": claim.get("new_claim_likely", False)
        })

    # 争议
    for nc in lkm_analysis.get("new_claims", []):
        review["controversies"].append({
            "question": nc["claim_text"],
            "source_doi": nc["paper_doi"],
            "reason": "LKM 标记为潜在新发现，文献支持较少"
        })

    # 推荐阅读
    for p in papers[:5]:
        reason_parts = []
        if p.get("citationNums", 0) > 100:
            reason_parts.append("高引用（奠基性工作）")
        if p.get("impactFactor", 0) > 10:
            reason_parts.append(f"高影响因子期刊 (IF={p['impactFactor']})")
        if p.get("coverDateStart", "") >= (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"):
            reason_parts.append("近一年最新进展")
        if not reason_parts:
            reason_parts.append("领域相关高质量论文")

        review["recommended_reading"].append({
            "doi": p.get("doi", ""),
            "title": p.get("enName", ""),
            "journal": p.get("publicationEnName", ""),
            "year": p.get("coverDateStart", "")[:4],
            "citations": p.get("citationNums", 0),
            "reason": "；".join(reason_parts)
        })

    # 格式化输出
    output = format_review(review)
    print(output)
    return review, output


def format_review(review):
    lines = []
    lines.append(f"# 文献综述: {review['topic']}")
    lines.append(f"\n> 生成时间: {review['generated_at']}")
    lines.append(f"> 检索论文数: {review['paper_count']}, "
                 f"全文解析数: {review['parsed_count']}")

    # 时间线
    lines.append("\n## 1. 研究时间线\n")
    for t in review["timeline"]:
        lines.append(f"- **{t['year']}** ({t['paper_count']} 篇) "
                     f"— {t['milestone']} (引用: {t['citations']})")

    # 核心发现
    lines.append("\n## 2. 核心发现\n")
    for i, f in enumerate(review["core_findings"], 1):
        novel_tag = " **[NEW]**" if f["is_novel"] else ""
        lines.append(f"{i}. {f['finding'][:200]}{novel_tag}")
        lines.append(f"   - 来源: {f['source_title'][:80]} (`{f['source_doi']}`)")
        lines.append(f"   - 证据数: {f['evidence_count']}")

    # 争议
    if review["controversies"]:
        lines.append("\n## 3. 争议与未解决问题\n")
        for c in review["controversies"]:
            lines.append(f"- {c['question'][:200]}")
            lines.append(f"  - 来源: `{c['source_doi']}`")
            lines.append(f"  - 原因: {c['reason']}")
    else:
        lines.append("\n## 3. 争议与未解决问题\n")
        lines.append("本次分析未发现显著争议性论断。")

    # 推荐阅读
    lines.append("\n## 4. 推荐阅读清单\n")
    lines.append("| # | 标题 | 期刊 | 年份 | 引用 | 推荐理由 |")
    lines.append("|---|------|------|------|------|----------|")
    for i, r in enumerate(review["recommended_reading"], 1):
        title_short = r['title'][:50] + ("..." if len(r['title']) > 50 else "")
        lines.append(f"| {i} | {title_short} | {r['journal']} | "
                     f"{r['year']} | {r['citations']} | {r['reason']} |")

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  文献综述助手 — {config['topic']}")
    print(f"  深度: {config['depth']}")
    print(f"{'#'*60}")

    # 步骤 1
    papers = step1_search_papers(config)
    if not papers:
        print("未检索到论文，退出")
        sys.exit(1)

    # 步骤 2
    parsed_contents = step2_parse_papers(papers, config["top_n_parse"])

    # 步骤 3
    lkm_analysis = step3_lkm_analysis(config["topic"], papers)

    # 步骤 4
    review, output = step4_synthesize(
        config["topic"], papers, parsed_contents, lkm_analysis
    )

    # 保存结果
    output_file = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n综述已保存到: {output_file}")

    # 保存原始数据
    data_file = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}_data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)
    print(f"原始数据已保存到: {data_file}")


if __name__ == "__main__":
    main()
```

---

## 可选扩展: 存入知识库

综述完成后，可将论文和综述结果存入 Bohrium 知识库以便后续管理和搜索。

```python
def save_to_knowledge_base(topic, review_markdown):
    """
    创建知识库并保存综述结果。

    Args:
        topic: 研究主题（用作知识库名称）
        review_markdown: 综述 Markdown 内容

    Returns:
        知识库 ID
    """
    # 创建知识库
    r = requests.post(
        f"{BASE}/v1/knowledge/knowledge_base/create",
        headers=HEADERS_JSON,
        json={
            "knowledgeBaseName": f"文献综述 — {topic}",
            "cover": "",
            "introduction": f"自动生成的文献综述: {topic}",
            "privilege": 1  # 1=私有
        }
    )
    r.raise_for_status()
    data = r.json()

    if data.get("code") != 0:
        print(f"创建知识库失败: {data.get('message')}")
        return None

    kb_id = data["data"]["id"]
    print(f"知识库已创建: ID={kb_id}")
    return kb_id
```

---

## 深度模式与快速模式对比

| 维度 | 快速模式 (`quick`) | 深度模式 (`deep`) |
|------|-------------------|-------------------|
| 检索论文数 | 20 篇 | 50 篇 |
| 全文解析数 | 5 篇 | 10 篇 |
| LKM 论断验证 | 前 5 篇 | 前 10 篇 |
| 预计耗时 | 2-5 分钟 | 10-20 分钟 |
| 适合场景 | 快速了解领域概况 | 撰写综述论文、深入调研 |

---

## 使用技巧

### 关键词选择

```python
# 推荐: 3-8 个专业英文术语，覆盖核心概念
keywords = ["deep learning", "molecular dynamics", "force field",
            "neural network potential", "machine learning"]

# 不推荐: 太笼统或太少
keywords = ["AI", "science"]
```

### 分区与时间范围配合

```python
# 综述近 5 年 Q1 论文 — 适合了解最新高质量研究
config = {"time_range_years": 5, "jcr_zones": ["Q1"]}

# 综述近 10 年全部论文 — 适合全面调研
config = {"time_range_years": 10, "jcr_zones": []}
```

### 解析失败处理

PDF 全文解析可能因 URL 无法访问而失败，这不影响整体流程。综述助手会自动跳过解析失败的论文，使用已有的元数据（标题、摘要、语料片段）继续生成综述。

### 分段执行

对于网络不稳定的环境，可以将四个步骤拆开单独执行，每步将中间结果保存为 JSON 文件：

```python
# 步骤 1 结果保存
import json
papers = step1_search_papers(config)
with open("step1_papers.json", "w") as f:
    json.dump(papers, f, ensure_ascii=False)

# 后续步骤从文件加载
with open("step1_papers.json") as f:
    papers = json.load(f)
parsed_contents = step2_parse_papers(papers, top_n=5)
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 检索结果为空 | 关键词太窄或时间范围太小 | 扩大关键词范围，放宽时间限制，移除 JCR 分区筛选 |
| PDF 解析全部失败 | DOI 对应的 PDF 不可直接下载 | 改用 arXiv 链接或其他可直接访问的 PDF URL |
| LKM 论断匹配无结果 | 摘要内容太短或不含明确论断 | 正常现象，部分论文摘要不含可验证的结论 |
| 响应含多行 JSON | paper-search 返回 streaming 格式 | 取第一行解析即可：`json.loads(r.text.split('\n')[0])` |
| 解析轮询超时 | PDF 页数多或服务繁忙 | 增大 `max_wait` 时间，或使用 `pages` 参数限定解析范围 |
| 401 Unauthorized | accessKey 无效 | 确认 ACCESS_KEY 正确，检查 `~/.openclaw/openclaw.json` 配置 |
| 整体执行时间过长 | 深度模式解析论文多 | 使用 `quick` 模式，减少 `top_n_parse` 数量 |
