---
name: tech-compare
description: "Technology route comparison combining literature analysis, PDF parsing, and knowledge graph. Use when: user needs to compare two or more technical approaches, methods, or frameworks to make a decision. NOT for: single technology deep-dive (use literature-review), tracking competitor moves (use tech-radar)."
---

# SKILL: 技术路线对比 (Tech Compare)

## 概述

技术路线对比是一个**编排型 Skill**，串联 `paper-search`、`pdf-parser`、`lkm` 三个原子 Skill，自动完成从多路线论文检索、实验数据解析、理论基础分析到结构化决策矩阵生成的完整流程。

**组合的原子 Skill：**

| 步骤 | 原子 Skill | 端点 | 功能 |
|------|-----------|------|------|
| 1 | `paper-search` | `/v1/paper/rag/pass/keyword` | 为每条技术路线检索代表性论文 |
| 2 | `pdf-parser` | `/v1/parse/trigger-url-async` + `/v1/parse/get-result` | 解析比较实验数据（表格、指标） |
| 3 | `lkm` | `/v1/lkm/search` | 分析各路线的理论基础与适用条件 |
| 4 | 综合分析 | — | 构建决策矩阵，输出对比报告 |

**适用场景：**

- 对比两种或多种技术方案，辅助技术选型决策
- 评估不同方法在精度、效率、可扩展性等维度的优劣
- 分析各技术路线的发展趋势，判断哪条路线处于上升期
- 识别各路线的代表性团队和核心工作

**不适用：**

- 单一技术深入调研 → `literature-review`
- 竞品技术动态监控 → `tech-radar`
- 单篇论文精读 → `paper-dissector`
- 单纯论文检索 → `bohrium-paper-search`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"tech-compare": {
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
| `routes` | string[] | 是 | — | 技术路线名称列表（至少 2 个），如 `["DFT", "ML force fields"]` |
| `dimensions` | string[] | 否 | `["accuracy", "efficiency", "scalability"]` | 评估维度列表 |
| `time_range` | int | 否 | 5 | 检索时间范围（年） |
| `top_n` | int | 否 | 10 | 每条路线检索的论文数量 |
| `parse_top` | int | 否 | 3 | 每条路线全文解析的论文数量 |
| `jcr_zones` | string[] | 否 | [] | JCR 分区筛选，如 `["Q1", "Q2"]` |

---

## 输出格式

对比结果包含以下结构化部分：

### 1. 决策矩阵

| 维度 | 路线 A | 路线 B | 路线 C |
|------|--------|--------|--------|
| 精度 | 高 | 中 | 低 |
| 效率 | 低 | 高 | 高 |
| 可扩展性 | 低 | 中 | 高 |

### 2. 各路线优劣势总结

每条路线的核心优势、主要局限、最佳适用场景。

### 3. 适用场景推荐

根据使用场景（如：高精度需求、大规模计算、快速原型等）推荐最优路线。

### 4. 发展趋势判断

基于论文发表年份分布，判断各路线的发展势头（上升/平稳/下降）。

### 5. 代表性团队与作品

各路线的高产作者、核心团队和里程碑论文。

### 6. 定量 Benchmark 对比表（核心交付物）

**对比报告必须包含至少一张定量 benchmark 表**，格式如下：

| 方法 | 数据集 | 指标 | 数值 | 来源论文 | 备注 |
|------|--------|------|------|---------|------|
| Method A | Dataset X | MAE | 0.014 eV | [Author 2023, Journal] | 官方实现 |
| Method B | Dataset X | MAE | 0.006 eV | [Author 2024, Journal] | 复现结果 |

**数据质量要求**：
- 所有数值必须标注来源论文（作者、年份、期刊/会议）
- 对比数值必须来自**相同数据集、相同划分、相同评估协议**
- 如数据来自不同论文的自报告结果，需标注"非公平对比，仅供参考"
- 如果无法获得可比数据，**必须明确说明**而非编造或使用不可比数据

---

## 报告分析深度要求

**对比报告不是信息堆砌**。在决策矩阵和优劣势之上，必须回答：

1. **"什么时候该用什么"决策指南**：给出具体的使用场景→推荐路线映射，如"数据量 <1000 条时用传统描述符，>10000 条时用 GNN"
2. **路线间的互补可能性**：是否存在组合使用的可能（如"DFT 生成训练数据 → ML 做快速筛选 → DFT 验证"）
3. **迁移代价分析**：从路线 A 切换到路线 B 的成本（需要的额外数据/算力/人员技能）
4. **定量 claim 溯源**：所有对比中的定量数据必须标注来源，禁止使用无来源的精度/效率数字

### 禁止的行为

- ❌ 决策矩阵只给"高/中/低"定性评估而无定量支撑
- ❌ 使用不同数据集/不同设置下的数字进行直接对比
- ❌ "路线 A 精度高但速度慢，路线 B 速度快但精度低"的套话结论（这是输入不是分析）
- ❌ 遗漏近 2 年的关键新路线或新方法

### 引用时效性与排序

检索结果需使用"引用速度"加权排序而非纯引用数排序：
- **经典高引**：按总引用数取 Top-N（保证覆盖奠基性工作）
- **前沿高速**：按"月均引用数"取 Top-N（保证覆盖最新突破）
- 最终结果合并两组去重，确保既有 2018 年的奠基工作也有 2024 年的最新 SOTA

---

## 工作流程图

```
输入: routes[], dimensions[], time_range
        │
        ▼
┌──────────────────────────────────────┐
│  步骤 1: 多路线论文检索               │
│  对每条路线:                          │
│  POST /v1/paper/rag/pass/keyword     │
│  → 检索代表性论文                    │
│  → 按引用数排序                      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 2: 对比实验数据解析             │
│  选取含跨路线对比的论文:              │
│  POST /v1/parse/trigger-url-async    │
│  POST /v1/parse/get-result (轮询)     │
│  → 提取 benchmark 表格、指标数据      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 3: 理论基础与适用性分析         │
│  对每条路线:                          │
│  POST /v1/lkm/search                │
│  → 查询理论基础                      │
│  → 分析适用条件与约束                │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 4: 综合分析与报告生成           │
│  → 构建决策矩阵                      │
│  → 优劣势总结                        │
│  → 适用场景推荐                      │
│  → 发展趋势判断                      │
│  → 代表性团队识别                    │
└──────────────────────────────────────┘
```

---

## 通用代码模板

```python
import os, sys, time, json, requests
from datetime import datetime, timedelta
from collections import Counter, defaultdict

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误: 请设置环境变量 ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
```

---

## 步骤 1: 多路线论文检索

为每条技术路线分别检索代表性论文，同时检索包含跨路线对比的综述/benchmark 论文。

### Python 示例

```python
def search_route_papers(route_name, question, top_n=15,
                        start_time="", end_time="", jcr_zones=None):
    """
    为单条技术路线检索代表性论文。

    Args:
        route_name: 技术路线名称
        question: 检索问题描述
        top_n: 返回论文数量
        start_time: 起始日期 YYYY-MM-DD
        end_time: 截止日期 YYYY-MM-DD
        jcr_zones: JCR 分区筛选

    Returns:
        论文列表，按引用数降序排列
    """
    payload = {
        "words": [route_name, "comparison"],
        "question": question,
        "type": 5,
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

    text = r.text.strip()
    first_line = text.split('\n')[0]
    data = json.loads(first_line)

    if data.get("code") != 0:
        raise RuntimeError(f"论文检索失败: {data.get('message', 'unknown error')}")

    papers = data["data"]
    papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
    return papers


def search_comparison_papers(routes, top_n=15, start_time="", end_time="",
                             jcr_zones=None):
    """
    检索包含多路线对比的综述或 benchmark 论文。

    Args:
        routes: 技术路线名称列表
        top_n: 返回论文数量

    Returns:
        包含跨路线对比的论文列表
    """
    # 构造对比检索词
    comparison_words = routes + ["comparison", "benchmark", "review"]
    question = f"compare {' vs '.join(routes)}: accuracy, efficiency, scalability"

    payload = {
        "words": comparison_words,
        "question": question,
        "type": 5,
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

    text = r.text.strip()
    first_line = text.split('\n')[0]
    data = json.loads(first_line)

    if data.get("code") != 0:
        return []

    papers = data["data"]
    papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
    return papers
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 检索单条路线论文
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["DFT", "comparison"],
    "question": "compare DFT vs ML force fields for molecular dynamics",
    "type": 5,
    "startTime": "2021-01-01",
    "endTime": "2026-01-01",
    "jcrZones": ["Q1"],
    "pageSize": 15
  }'

# 检索跨路线对比论文
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["DFT", "ML force fields", "comparison", "benchmark", "review"],
    "question": "compare DFT vs ML force fields: accuracy, efficiency, scalability",
    "type": 5,
    "pageSize": 15
  }'
```

---

## 步骤 2: 对比实验数据解析

对步骤 1 中选出的含跨路线对比的论文进行全文解析，重点提取 benchmark 表格和指标数据。

### Python 示例

```python
def parse_paper_async(paper_url, pages=None):
    """
    提交单篇论文 PDF 解析任务。

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
            raise RuntimeError(
                f"解析失败: {result.get('description', 'unknown')}"
            )

    raise TimeoutError(f"解析超时: token={token}")


def parse_comparison_papers(papers, parse_top=3):
    """
    批量解析含对比数据的论文。

    Args:
        papers: 论文列表
        parse_top: 解析数量

    Returns:
        dict: {doi: full_text_content}
    """
    selected = papers[:parse_top]
    tokens = {}
    parsed_contents = {}

    # 提交所有解析任务
    for p in selected:
        doi = p.get("doi", "")
        if not doi:
            continue
        pdf_url = f"https://doi.org/{doi}"
        try:
            token = parse_paper_async(pdf_url)
            tokens[doi] = token
            print(f"  提交解析: {doi} -> token={token[:16]}...")
        except Exception as e:
            print(f"  提交失败: {doi} -> {e}")

    if not tokens:
        return parsed_contents

    # 轮询所有解析结果
    print(f"\n  等待 {len(tokens)} 篇论文解析完成...")
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
                    json={"token": token, "content": True,
                          "objects": False, "pages_dict": False}
                )
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

    return parsed_contents
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 提交解析任务
TOKEN=$(curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/trigger-url-async" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "url": "https://arxiv.org/pdf/2302.14231",
    "sync": false,
    "textual": true,
    "table": true,
    "expression": true,
    "equation": true,
    "pages": [0, 1, 2, 3],
    "timeout": 1800
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "Token: $TOKEN"

# 轮询结果
sleep 5
curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/get-result" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d "{\"token\": \"$TOKEN\", \"content\": true, \"objects\": false}"
```

---

## 步骤 3: 理论基础与适用性分析

使用 LKM 知识图谱搜索，分析每条技术路线的理论基础、适用条件和约束。

### Python 示例

```python
def analyze_route_theory(route_name):
    """
    利用 LKM 知识图谱查询技术路线的理论基础。

    Args:
        route_name: 技术路线名称

    Returns:
        dict: 包含理论基础、适用条件等信息
    """
    analysis = {
        "route": route_name,
        "theoretical_basis": [],
        "applicability": [],
        "constraints": []
    }

    # 查询理论基础
    queries = [
        f"theoretical basis of {route_name}",
        f"{route_name} applicability conditions",
        f"{route_name} limitations and constraints"
    ]

    for query in queries:
        try:
            r = requests.post(
                f"{BASE}/v1/lkm/search",
                headers=HEADERS_JSON,
                json={"query": query, "limit": 10}
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("data", [])

            if "theoretical" in query:
                analysis["theoretical_basis"].extend(results)
            elif "applicability" in query:
                analysis["applicability"].extend(results)
            elif "limitation" in query:
                analysis["constraints"].extend(results)

            print(f"  {route_name} - {query[:40]}... -> {len(results)} 条结果")

        except Exception as e:
            print(f"  {route_name} - 查询失败: {e}")

    return analysis
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 查询 DFT 的理论基础
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "theoretical basis of DFT density functional theory", "limit": 10}' \
  | python3 -m json.tool

# 查询 ML force fields 的适用条件
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "ML force fields applicability conditions", "limit": 10}' \
  | python3 -m json.tool
```

---

## 步骤 4: 综合分析与报告生成

将前三步结果汇总，构建决策矩阵、分析发展趋势、识别代表性团队。

### Python 示例

```python
def analyze_publication_trend(route_papers):
    """
    基于论文发表年份分布分析技术路线的发展趋势。

    Args:
        route_papers: dict, {route_name: [papers]}

    Returns:
        dict: {route_name: {"trend": "上升/平稳/下降", "yearly_counts": {...},
               "recent_ratio": float}}
    """
    trends = {}

    for route_name, papers in route_papers.items():
        yearly_counts = Counter()
        for p in papers:
            year = p.get("coverDateStart", "")[:4]
            if year and year.isdigit():
                yearly_counts[int(year)] += 1

        if not yearly_counts:
            trends[route_name] = {
                "trend": "数据不足",
                "yearly_counts": {},
                "recent_ratio": 0.0
            }
            continue

        sorted_years = sorted(yearly_counts.keys())
        total = sum(yearly_counts.values())

        # 计算近 2 年论文占总数的比例
        current_year = datetime.now().year
        recent_count = sum(
            yearly_counts[y] for y in sorted_years
            if y >= current_year - 2
        )
        recent_ratio = recent_count / total if total > 0 else 0

        # 判断趋势：对比前半段和后半段的论文数量
        mid_year = sorted_years[len(sorted_years) // 2]
        first_half = sum(
            yearly_counts[y] for y in sorted_years if y <= mid_year
        )
        second_half = sum(
            yearly_counts[y] for y in sorted_years if y > mid_year
        )

        if second_half > first_half * 1.5:
            trend = "上升"
        elif second_half < first_half * 0.6:
            trend = "下降"
        else:
            trend = "平稳"

        trends[route_name] = {
            "trend": trend,
            "yearly_counts": dict(yearly_counts),
            "recent_ratio": round(recent_ratio, 2)
        }

    return trends


def identify_representative_teams(route_papers):
    """
    从作者出现频率中识别各路线的代表性团队。

    Args:
        route_papers: dict, {route_name: [papers]}

    Returns:
        dict: {route_name: [{"author": str, "count": int,
               "top_paper": str, "citations": int}]}
    """
    teams = {}

    for route_name, papers in route_papers.items():
        author_stats = defaultdict(lambda: {
            "count": 0, "total_citations": 0,
            "top_paper": "", "top_citations": 0
        })

        for p in papers:
            authors = p.get("authors", [])
            citations = p.get("citationNums", 0)
            title = p.get("enName", "")

            for author in authors:
                # authors 可能是字符串或字典
                if isinstance(author, dict):
                    name = author.get("name", author.get("nameEn", ""))
                else:
                    name = str(author)

                if not name:
                    continue

                stats = author_stats[name]
                stats["count"] += 1
                stats["total_citations"] += citations
                if citations > stats["top_citations"]:
                    stats["top_citations"] = citations
                    stats["top_paper"] = title

        # 按论文数和总引用数排序，取前 5
        sorted_authors = sorted(
            author_stats.items(),
            key=lambda x: (x[1]["count"], x[1]["total_citations"]),
            reverse=True
        )

        teams[route_name] = [
            {
                "author": name,
                "paper_count": stats["count"],
                "total_citations": stats["total_citations"],
                "top_paper": stats["top_paper"],
                "top_citations": stats["top_citations"]
            }
            for name, stats in sorted_authors[:5]
        ]

    return teams


def build_decision_matrix(routes, dimensions, route_papers,
                          parsed_contents, lkm_analyses):
    """
    构建决策矩阵。

    根据检索到的论文数据、解析内容和 LKM 分析，
    对各路线在各维度上进行定性评估。

    Args:
        routes: 技术路线名称列表
        dimensions: 评估维度列表
        route_papers: {route_name: [papers]}
        parsed_contents: {doi: full_text}
        lkm_analyses: {route_name: lkm_analysis_result}

    Returns:
        dict: {dimension: {route: rating}}
        rating 为 "高/中/低" 的定性评估
    """
    matrix = {}

    for dim in dimensions:
        matrix[dim] = {}
        for route in routes:
            papers = route_papers.get(route, [])
            lkm = lkm_analyses.get(route, {})

            # 基于论文指标的启发式评估
            avg_citations = 0
            if papers:
                avg_citations = sum(
                    p.get("citationNums", 0) for p in papers
                ) / len(papers)

            # 基于 LKM 知识图谱的理论支撑度
            theory_count = len(lkm.get("theoretical_basis", []))

            # 综合评分（简化启发式）
            if dim.lower() in ("accuracy", "精度", "准确性"):
                # 高引用通常意味着方法成熟可靠
                if avg_citations > 100:
                    rating = "高"
                elif avg_citations > 30:
                    rating = "中"
                else:
                    rating = "低"
            elif dim.lower() in ("efficiency", "效率", "速度"):
                # 需要从解析内容中推断（简化处理）
                rating = "中"
                for doi, content in parsed_contents.items():
                    content_lower = content.lower()
                    if route.lower() in content_lower:
                        if any(w in content_lower for w in
                               ["fast", "efficient", "speedup",
                                "real-time", "rapid"]):
                            rating = "高"
                        elif any(w in content_lower for w in
                                 ["slow", "expensive", "computational cost"]):
                            rating = "低"
            elif dim.lower() in ("scalability", "可扩展性"):
                if theory_count > 5:
                    rating = "高"
                elif theory_count > 2:
                    rating = "中"
                else:
                    rating = "低"
            else:
                # 默认：基于论文数量的粗略评估
                paper_count = len(papers)
                if paper_count > 10:
                    rating = "高"
                elif paper_count > 5:
                    rating = "中"
                else:
                    rating = "低"

            matrix[dim][route] = rating

    return matrix


def summarize_pros_cons(route_name, papers, lkm_analysis, trend_info):
    """
    总结单条技术路线的优劣势。

    Args:
        route_name: 路线名称
        papers: 该路线的论文列表
        lkm_analysis: LKM 分析结果
        trend_info: 发展趋势信息

    Returns:
        dict: {"pros": [...], "cons": [...], "best_for": str}
    """
    pros = []
    cons = []
    best_for = ""

    # 基于论文指标分析
    if papers:
        avg_if = sum(
            p.get("impactFactor", 0) for p in papers
        ) / len(papers)
        max_citations = max(
            p.get("citationNums", 0) for p in papers
        )

        if avg_if > 5:
            pros.append("研究发表在高影响因子期刊，方法受到广泛认可")
        if max_citations > 200:
            pros.append(f"拥有高引用代表作（最高 {max_citations} 次引用），领域影响力大")
        if len(papers) < 5:
            cons.append("相关研究论文较少，成熟度待验证")

    # 基于 LKM 分析
    theory = lkm_analysis.get("theoretical_basis", [])
    constraints = lkm_analysis.get("constraints", [])

    if len(theory) > 5:
        pros.append("理论基础扎实，知识图谱中有丰富的支撑文献")
    elif len(theory) < 2:
        cons.append("理论基础文献较少，可能处于早期探索阶段")

    if constraints:
        for c in constraints[:2]:
            if isinstance(c, dict):
                text = c.get("text", c.get("content", str(c)))
            else:
                text = str(c)
            cons.append(f"已知约束: {text[:100]}")

    # 基于趋势分析
    trend = trend_info.get("trend", "")
    if trend == "上升":
        pros.append("论文发表量呈上升趋势，是当前研究热点")
    elif trend == "下降":
        cons.append("论文发表量呈下降趋势，关注度可能减弱")

    return {"pros": pros, "cons": cons, "best_for": best_for}
```

---

## 完整编排示例

以下是将全部步骤串联的端到端 Python 脚本：

```python
#!/usr/bin/env python3
"""
技术路线对比 (Tech Compare) — 完整编排脚本

用法:
    export ACCESS_KEY="your_access_key"
    python3 tech_compare.py

可修改下方 CONFIG 区域的参数来调整对比范围。
"""

import os
import sys
import time
import json
import requests
from datetime import datetime, timedelta
from collections import Counter, defaultdict

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
    "routes": ["DFT", "ML force fields"],
    "dimensions": ["accuracy", "efficiency", "scalability"],
    "time_range_years": 5,
    "jcr_zones": ["Q1", "Q2"],
    "top_n": 15,          # 每条路线检索论文数
    "parse_top": 3,       # 每条路线全文解析数
}


# ============================================================
# 步骤 1: 多路线论文检索
# ============================================================

def step1_search(config):
    end_time = datetime.now().strftime("%Y-%m-%d")
    start_time = (
        datetime.now() - timedelta(days=365 * config["time_range_years"])
    ).strftime("%Y-%m-%d")

    routes = config["routes"]
    route_papers = {}
    comparison_question = f"compare {' vs '.join(routes)}"

    print(f"\n{'='*60}")
    print(f"步骤 1: 多路线论文检索")
    print(f"  路线: {routes}")
    print(f"  时间范围: {start_time} ~ {end_time}")
    print(f"{'='*60}\n")

    # 1a. 为每条路线单独检索
    for route in routes:
        question = f"{route} method for {comparison_question}"
        payload = {
            "words": [route, "comparison"],
            "question": question,
            "type": 5,
            "startTime": start_time,
            "endTime": end_time,
            "jcrZones": config["jcr_zones"],
            "pageSize": config["top_n"]
        }

        try:
            r = requests.post(
                f"{BASE}/v1/paper/rag/pass/keyword",
                headers=HEADERS_JSON,
                json=payload
            )
            r.raise_for_status()
            text = r.text.strip()
            first_line = text.split('\n')[0]
            data = json.loads(first_line)

            if data.get("code") == 0:
                papers = data["data"]
                papers.sort(
                    key=lambda p: p.get("citationNums", 0), reverse=True
                )
                route_papers[route] = papers
                print(f"  [{route}] 检索到 {len(papers)} 篇论文")
                for i, p in enumerate(papers[:3]):
                    print(f"    {i+1}. {p['enName'][:60]}... "
                          f"(引用: {p.get('citationNums', 0)})")
            else:
                route_papers[route] = []
                print(f"  [{route}] 检索失败: {data.get('message')}")
        except Exception as e:
            route_papers[route] = []
            print(f"  [{route}] 检索异常: {e}")

    # 1b. 检索跨路线对比论文
    print(f"\n  检索跨路线对比论文...")
    comparison_words = routes + ["comparison", "benchmark"]
    try:
        r = requests.post(
            f"{BASE}/v1/paper/rag/pass/keyword",
            headers=HEADERS_JSON,
            json={
                "words": comparison_words,
                "question": comparison_question,
                "type": 5,
                "startTime": start_time,
                "endTime": end_time,
                "jcrZones": config["jcr_zones"],
                "pageSize": config["top_n"]
            }
        )
        r.raise_for_status()
        text = r.text.strip()
        first_line = text.split('\n')[0]
        data = json.loads(first_line)

        if data.get("code") == 0:
            comparison_papers = data["data"]
            comparison_papers.sort(
                key=lambda p: p.get("citationNums", 0), reverse=True
            )
            route_papers["_comparison"] = comparison_papers
            print(f"  [跨路线对比] 检索到 {len(comparison_papers)} 篇论文")
        else:
            route_papers["_comparison"] = []
    except Exception as e:
        route_papers["_comparison"] = []
        print(f"  [跨路线对比] 检索异常: {e}")

    return route_papers


# ============================================================
# 步骤 2: 对比实验数据解析
# ============================================================

def step2_parse(route_papers, parse_top):
    print(f"\n{'='*60}")
    print(f"步骤 2: 对比实验数据解析")
    print(f"{'='*60}\n")

    # 优先解析跨路线对比论文
    comparison_papers = route_papers.get("_comparison", [])
    all_to_parse = comparison_papers[:parse_top]

    # 补充各路线的高引论文
    for route, papers in route_papers.items():
        if route == "_comparison":
            continue
        for p in papers[:2]:
            if len(all_to_parse) < parse_top * 2:
                all_to_parse.append(p)

    tokens = {}
    parsed_contents = {}

    # 提交解析任务
    for p in all_to_parse:
        doi = p.get("doi", "")
        if not doi or doi in tokens:
            continue
        pdf_url = f"https://doi.org/{doi}"
        try:
            payload = {
                "url": pdf_url,
                "sync": False,
                "textual": True,
                "table": True,
                "expression": True,
                "equation": True,
                "pages": [],
                "timeout": 1800
            }
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
        except Exception as e:
            print(f"  失败: {doi} -> {e}")

    if not tokens:
        print("  警告: 无法提交任何解析任务")
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
                    json={"token": token, "content": True,
                          "objects": False, "pages_dict": False}
                )
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

    print(f"\n  解析完成: {len(parsed_contents)}/{len(tokens)} 篇")
    return parsed_contents


# ============================================================
# 步骤 3: 理论基础与适用性分析
# ============================================================

def step3_lkm_analysis(routes):
    print(f"\n{'='*60}")
    print(f"步骤 3: 理论基础与适用性分析")
    print(f"{'='*60}\n")

    lkm_analyses = {}

    for route in routes:
        print(f"  分析路线: {route}")
        analysis = {
            "route": route,
            "theoretical_basis": [],
            "applicability": [],
            "constraints": []
        }

        queries = {
            "theoretical_basis": f"theoretical basis of {route} method",
            "applicability": f"{route} applicability conditions and scenarios",
            "constraints": f"{route} limitations and constraints"
        }

        for field, query in queries.items():
            try:
                r = requests.post(
                    f"{BASE}/v1/lkm/search",
                    headers=HEADERS_JSON,
                    json={"query": query, "limit": 10}
                )
                r.raise_for_status()
                data = r.json()
                results = data.get("data", [])
                analysis[field] = results
                print(f"    {field}: {len(results)} 条结果")
            except Exception as e:
                print(f"    {field}: 查询失败 - {e}")

        lkm_analyses[route] = analysis

    return lkm_analyses


# ============================================================
# 步骤 4: 综合分析与报告生成
# ============================================================

def step4_synthesize(config, route_papers, parsed_contents, lkm_analyses):
    print(f"\n{'='*60}")
    print(f"步骤 4: 综合分析与报告生成")
    print(f"{'='*60}\n")

    routes = config["routes"]
    dimensions = config["dimensions"]

    # 4a. 发展趋势分析
    print("  4a. 发展趋势分析...")
    trends = {}
    for route in routes:
        papers = route_papers.get(route, [])
        yearly_counts = Counter()
        for p in papers:
            year = p.get("coverDateStart", "")[:4]
            if year and year.isdigit():
                yearly_counts[int(year)] += 1

        if not yearly_counts:
            trends[route] = {
                "trend": "数据不足",
                "yearly_counts": {},
                "recent_ratio": 0.0
            }
            continue

        sorted_years = sorted(yearly_counts.keys())
        total = sum(yearly_counts.values())
        current_year = datetime.now().year
        recent_count = sum(
            yearly_counts[y] for y in sorted_years if y >= current_year - 2
        )
        recent_ratio = recent_count / total if total > 0 else 0

        mid_year = sorted_years[len(sorted_years) // 2]
        first_half = sum(
            yearly_counts[y] for y in sorted_years if y <= mid_year
        )
        second_half = sum(
            yearly_counts[y] for y in sorted_years if y > mid_year
        )

        if second_half > first_half * 1.5:
            trend = "上升"
        elif second_half < first_half * 0.6:
            trend = "下降"
        else:
            trend = "平稳"

        trends[route] = {
            "trend": trend,
            "yearly_counts": dict(yearly_counts),
            "recent_ratio": round(recent_ratio, 2)
        }

        print(f"    {route}: {trend} "
              f"(近两年占比 {recent_ratio:.0%})")

    # 4b. 代表性团队识别
    print("\n  4b. 代表性团队识别...")
    teams = {}
    for route in routes:
        papers = route_papers.get(route, [])
        author_stats = defaultdict(lambda: {
            "count": 0, "total_citations": 0,
            "top_paper": "", "top_citations": 0
        })

        for p in papers:
            authors = p.get("authors", [])
            citations = p.get("citationNums", 0)
            title = p.get("enName", "")

            for author in authors:
                if isinstance(author, dict):
                    name = author.get("name",
                                      author.get("nameEn", ""))
                else:
                    name = str(author)
                if not name:
                    continue

                stats = author_stats[name]
                stats["count"] += 1
                stats["total_citations"] += citations
                if citations > stats["top_citations"]:
                    stats["top_citations"] = citations
                    stats["top_paper"] = title

        sorted_authors = sorted(
            author_stats.items(),
            key=lambda x: (x[1]["count"], x[1]["total_citations"]),
            reverse=True
        )

        teams[route] = [
            {
                "author": name,
                "paper_count": stats["count"],
                "total_citations": stats["total_citations"],
                "top_paper": stats["top_paper"]
            }
            for name, stats in sorted_authors[:5]
        ]

        if teams[route]:
            top = teams[route][0]
            print(f"    {route} 代表人物: {top['author']} "
                  f"({top['paper_count']} 篇, "
                  f"总引用 {top['total_citations']})")

    # 4c. 构建决策矩阵
    print("\n  4c. 构建决策矩阵...")
    matrix = {}
    for dim in dimensions:
        matrix[dim] = {}
        for route in routes:
            papers = route_papers.get(route, [])
            lkm = lkm_analyses.get(route, {})

            avg_citations = 0
            if papers:
                avg_citations = sum(
                    p.get("citationNums", 0) for p in papers
                ) / len(papers)

            theory_count = len(lkm.get("theoretical_basis", []))

            if dim.lower() in ("accuracy", "精度", "准确性"):
                if avg_citations > 100:
                    rating = "高"
                elif avg_citations > 30:
                    rating = "中"
                else:
                    rating = "低"
            elif dim.lower() in ("efficiency", "效率", "速度"):
                rating = "中"
                for doi, content in parsed_contents.items():
                    cl = content.lower()
                    if route.lower() in cl:
                        if any(w in cl for w in
                               ["fast", "efficient", "speedup"]):
                            rating = "高"
                        elif any(w in cl for w in
                                 ["slow", "expensive", "cost"]):
                            rating = "低"
            elif dim.lower() in ("scalability", "可扩展性"):
                if theory_count > 5:
                    rating = "高"
                elif theory_count > 2:
                    rating = "中"
                else:
                    rating = "低"
            else:
                paper_count = len(papers)
                if paper_count > 10:
                    rating = "高"
                elif paper_count > 5:
                    rating = "中"
                else:
                    rating = "低"

            matrix[dim][route] = rating

    # 4d. 优劣势总结
    print("\n  4d. 优劣势总结...")
    pros_cons = {}
    for route in routes:
        papers = route_papers.get(route, [])
        lkm = lkm_analyses.get(route, {})
        trend_info = trends.get(route, {})

        pros = []
        cons = []

        if papers:
            avg_if = sum(
                p.get("impactFactor", 0) for p in papers
            ) / len(papers)
            max_citations = max(
                p.get("citationNums", 0) for p in papers
            )

            if avg_if > 5:
                pros.append(
                    "研究发表在高影响因子期刊，方法受到广泛认可"
                )
            if max_citations > 200:
                pros.append(
                    f"拥有高引用代表作（最高 {max_citations} 次引用）"
                )
            if len(papers) < 5:
                cons.append("相关研究论文较少，成熟度待验证")

        theory = lkm.get("theoretical_basis", [])
        if len(theory) > 5:
            pros.append("理论基础扎实，知识图谱中有丰富支撑")
        elif len(theory) < 2:
            cons.append("理论基础文献较少，可能处于早期探索阶段")

        if trend_info.get("trend") == "上升":
            pros.append("论文发表量呈上升趋势，是当前研究热点")
        elif trend_info.get("trend") == "下降":
            cons.append("论文发表量呈下降趋势，关注度可能减弱")

        pros_cons[route] = {"pros": pros, "cons": cons}

    # 生成报告
    report = format_comparison_report(
        config, route_papers, matrix, trends, teams, pros_cons
    )
    return report


def format_comparison_report(config, route_papers, matrix, trends,
                             teams, pros_cons):
    """
    格式化输出技术路线对比报告（Markdown）。
    """
    routes = config["routes"]
    dimensions = config["dimensions"]
    lines = []

    lines.append(f"# 技术路线对比报告: {' vs '.join(routes)}")
    lines.append(f"\n> 生成时间: {datetime.now().isoformat()}")
    total_papers = sum(
        len(route_papers.get(r, [])) for r in routes
    )
    lines.append(f"> 检索论文总数: {total_papers}")
    lines.append(f"> 评估维度: {', '.join(dimensions)}")

    # 1. 决策矩阵
    lines.append("\n## 1. 决策矩阵\n")
    header = "| 维度 | " + " | ".join(routes) + " |"
    separator = "|------|" + "|".join(["------"] * len(routes)) + "|"
    lines.append(header)
    lines.append(separator)
    for dim in dimensions:
        row = f"| {dim} |"
        for route in routes:
            rating = matrix.get(dim, {}).get(route, "—")
            row += f" {rating} |"
        lines.append(row)

    # 2. 各路线优劣势
    lines.append("\n## 2. 各路线优劣势总结\n")
    for route in routes:
        pc = pros_cons.get(route, {})
        lines.append(f"### {route}\n")
        lines.append("**优势：**\n")
        for pro in pc.get("pros", []):
            lines.append(f"- {pro}")
        if not pc.get("pros"):
            lines.append("- 暂无明显优势（数据不足）")
        lines.append("\n**劣势：**\n")
        for con in pc.get("cons", []):
            lines.append(f"- {con}")
        if not pc.get("cons"):
            lines.append("- 暂无明显劣势（数据不足）")
        lines.append("")

    # 3. 适用场景推荐
    lines.append("## 3. 适用场景推荐\n")
    for route in routes:
        trend = trends.get(route, {}).get("trend", "未知")
        paper_count = len(route_papers.get(route, []))
        if trend == "上升" and paper_count > 5:
            lines.append(
                f"- **{route}**：处于上升期，"
                f"适合关注前沿进展、开展新课题"
            )
        elif paper_count > 10:
            lines.append(
                f"- **{route}**：成熟路线，"
                f"适合工程应用和需要稳定性的场景"
            )
        else:
            lines.append(
                f"- **{route}**：数据量有限，"
                f"建议进一步调研后决策"
            )

    # 4. 发展趋势
    lines.append("\n## 4. 发展趋势判断\n")
    lines.append("| 路线 | 趋势 | 近两年占比 | 年度论文分布 |")
    lines.append("|------|------|-----------|-------------|")
    for route in routes:
        t = trends.get(route, {})
        trend_label = t.get("trend", "未知")
        ratio = t.get("recent_ratio", 0)
        yearly = t.get("yearly_counts", {})
        yearly_str = ", ".join(
            f"{y}:{c}" for y, c in sorted(yearly.items())
        )
        lines.append(
            f"| {route} | {trend_label} | "
            f"{ratio:.0%} | {yearly_str} |"
        )

    # 5. 代表性团队
    lines.append("\n## 5. 代表性团队与作品\n")
    for route in routes:
        lines.append(f"### {route}\n")
        route_teams = teams.get(route, [])
        if route_teams:
            lines.append(
                "| # | 研究者 | 论文数 | 总引用 | 代表作 |"
            )
            lines.append(
                "|---|--------|--------|--------|--------|"
            )
            for i, t in enumerate(route_teams, 1):
                title_short = (t['top_paper'][:40] + "..."
                               if len(t['top_paper']) > 40
                               else t['top_paper'])
                lines.append(
                    f"| {i} | {t['author']} | "
                    f"{t['paper_count']} | "
                    f"{t['total_citations']} | "
                    f"{title_short} |"
                )
        else:
            lines.append("暂无数据。")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  技术路线对比 — {' vs '.join(config['routes'])}")
    print(f"  评估维度: {', '.join(config['dimensions'])}")
    print(f"{'#'*60}")

    # 校验输入
    if len(config["routes"]) < 2:
        print("错误: 至少需要 2 条技术路线进行对比")
        sys.exit(1)

    # 步骤 1: 论文检索
    route_papers = step1_search(config)
    total = sum(
        len(v) for k, v in route_papers.items() if k != "_comparison"
    )
    if total == 0:
        print("未检索到任何论文，退出")
        sys.exit(1)

    # 步骤 2: PDF 解析
    parsed_contents = step2_parse(route_papers, config["parse_top"])

    # 步骤 3: LKM 分析
    lkm_analyses = step3_lkm_analysis(config["routes"])

    # 步骤 4: 综合分析
    report = step4_synthesize(
        config, route_papers, parsed_contents, lkm_analyses
    )

    # 输出报告
    print("\n" + report)

    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    routes_tag = "_vs_".join(
        r.replace(" ", "-") for r in config["routes"]
    )
    output_file = f"compare_{routes_tag}_{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存到: {output_file}")


if __name__ == "__main__":
    main()
```

---

## 使用技巧

### 路线命名

```python
# 推荐: 使用领域内通用的英文缩写或术语
routes = ["DFT", "ML force fields"]
routes = ["GNN", "Transformer", "CNN"]
routes = ["Monte Carlo", "Molecular Dynamics"]

# 不推荐: 太笼统或缩写不标准
routes = ["method A", "method B"]
```

### 评估维度定制

```python
# 通用科学计算场景
dimensions = ["accuracy", "efficiency", "scalability"]

# 材料科学场景
dimensions = ["精度", "计算成本", "可迁移性", "数据需求量"]

# 机器学习场景
dimensions = ["模型精度", "训练效率", "推理速度", "数据依赖", "可解释性"]
```

### 解析失败处理

PDF 全文解析可能因 URL 无法访问而失败，这不影响整体流程。对比分析会自动降级，使用已有的元数据（标题、摘要、引用数）继续生成决策矩阵。解析成功的论文会提供更精细的指标对比。

### 分段执行

对于网络不稳定的环境，可以将四个步骤拆开单独执行，每步将中间结果保存为 JSON 文件：

```python
# 步骤 1 结果保存
route_papers = step1_search(config)
with open("step1_route_papers.json", "w") as f:
    json.dump(route_papers, f, ensure_ascii=False)

# 后续步骤从文件加载
with open("step1_route_papers.json") as f:
    route_papers = json.load(f)
parsed_contents = step2_parse(route_papers, parse_top=3)
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 检索结果为空 | 路线名称太窄或时间范围太小 | 使用更通用的英文术语，放宽时间限制 |
| 两条路线结果高度重叠 | 路线区分度不够 | 使用更具体的术语区分，如 "ab initio MD" vs "MLFF MD" |
| PDF 解析全部失败 | DOI 对应的 PDF 不可直接下载 | 改用 arXiv 链接或其他可直接访问的 PDF URL |
| LKM 查询无结果 | 知识图谱不覆盖该领域 | 正常现象，对比分析会降级使用论文元数据 |
| 决策矩阵评级不准确 | 启发式规则的局限 | 将矩阵作为参考起点，结合领域知识人工修正 |
| 响应含多行 JSON | paper-search 返回 streaming 格式 | 取第一行解析：`json.loads(r.text.split('\n')[0])` |
| 401 Unauthorized | accessKey 无效 | 确认 ACCESS_KEY 正确，检查 `~/.openclaw/openclaw.json` 配置 |
| 趋势判断不准确 | 样本量太少（< 10 篇论文） | 增大 `top_n` 或扩大时间范围以获取更多数据点 |
| 代表团队识别有误 | 同名作者干扰 | 结合机构信息人工确认，后续版本将引入机构去重 |

---

## 搭配使用

- **bohrium-paper-search** — 本技能的论文检索能力来源
- **bohrium-pdf-parser** — 本技能的全文解析能力来源
- **bohrium-lkm** — 本技能的知识图谱分析能力来源
- **literature-review** — 对选定路线做更深入的文献综述
- **paper-dissector** — 精读对比论文中的关键单篇论文
- **tech-radar** — 持续跟踪已选定路线的最新动态
