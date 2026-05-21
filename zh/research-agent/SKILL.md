---
name: research-agent
description: "Autonomous research agent that iteratively explores a research question using multiple skills until forming a reliable conclusion with evidence chain. Use when: user has an open research question that requires multi-step investigation with iterative reasoning. NOT for: simple paper search (use bohrium-paper-search), structured workflows with known steps (use other specific skills)."
---

# SKILL: 自主研究代理 (Research Agent)

## 概述

自主研究代理是一个**迭代推理型编排 Skill**，围绕一个开放式研究问题，自主规划搜索策略、调用多个原子 Skill、分析中间结果、判断是否需要进一步查询，循环迭代直到形成可靠结论并构建完整证据链。

**与其他 Skill 的区别：**

| Skill | 定位 | 适用场景 |
|-------|------|----------|
| `bohrium-paper-search` | 单次论文检索 | 已知要找什么关键词 |
| `literature-review` | 固定四步流水线 | 已知研究主题，需要结构化综述 |
| **`research-agent`** | **自主迭代探索** | **开放式问题，不确定需要查什么、查多少轮** |

**核心能力：**

- 自主分解研究问题为可搜索的子问题
- 动态选择最合适的搜索工具（论文、学者、知识图谱、网页）
- 分析中间结果，判断证据是否充分
- 迭代深入，直到形成可靠结论
- 构建完整的证据链，评估结论置信度

**调用的原子 Skill：**

| 原子 Skill | 端点 | 用途 |
|-----------|------|------|
| `bohrium-paper-search` | `POST /v1/paper/rag/pass/keyword` | 语义检索学术论文 |
| `bohrium-scholar-search` | `POST /v1/paper-server/scholar/search` | 搜索相关学者及其研究方向 |
| `bohrium-lkm` | `POST /v1/lkm/search` + `POST /v1/lkm/claims/match` | 知识图谱搜索 + 论断验证 |
| `bohrium-web-search` | `GET /v1/search/web` | 开放互联网搜索 |
| `bohrium-pdf-parser` | `POST /v1/parse/trigger-url-async` + `POST /v1/parse/get-result` | 论文全文解析 |

**适用场景：**

- "X 材料是否适合做 Y 应用？文献中有什么证据？"
- "A 方法和 B 方法在 C 任务上的对比，哪个更优？为什么？"
- "某个新发现的机制是否已被独立验证？"
- "某领域的最新突破是什么？与之前的工作有何不同？"

**不适用：**

- 简单论文检索（已知关键词）→ `bohrium-paper-search`
- 固定步骤的文献综述 → `literature-review`
- 单篇论文解析 → `bohrium-pdf-parser`
- 学者信息查询 → `bohrium-scholar-search`

**无 CLI 支持** — 通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"research-agent": {
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
| `question` | string | 是 | — | 研究问题（自然语言描述） |
| `max_iterations` | int | 否 | 5 | 最大迭代轮次 |
| `confidence_threshold` | float | 否 | 0.7 | 结论置信度阈值（0-1），达到后停止迭代 |
| `time_range_years` | int | 否 | 5 | 论文检索时间范围（年） |
| `scope` | string | 否 | `"balanced"` | 搜索范围：`"narrow"`（精确）/ `"balanced"`（均衡）/ `"broad"`（广泛） |
| `depth` | string | 否 | `"standard"` | 探索深度：`"quick"`（快速）/ `"standard"`（标准）/ `"deep"`（深入） |

---

## 输出格式

### 研究备忘录 (Research Memo)

```
# 研究备忘录: {question}

## 1. 结论摘要
- 核心结论（1-3 句话）
- 置信度评估: HIGH / MEDIUM / LOW
- 置信度依据

## 2. 证据链
- 证据 1: [来源] → [发现] → [与结论的关系]
- 证据 2: ...
- （按证据强度排序）

## 3. 研究过程
- 迭代 1: 搜索了什么 → 发现了什么 → 下一步决策
- 迭代 2: ...

## 4. 矛盾与争议
- 支持的证据 vs 反对的证据
- 未解决的分歧

## 5. 进一步研究建议
- 可以深入的方向
- 推荐的关键论文
- 建议验证的假设
```

---

## 数据质量控制（关键步骤）

研究代理在多轮迭代中会积累来自不同来源的证据，**必须在综合结论前验证数据可靠性并明确区分数据来源**。

### 多源交叉验证

```python
def cross_validate_finding(finding, all_evidence, min_sources=2):
    """
    对关键发现进行多源交叉验证。
    只有被至少 min_sources 个独立来源支持的发现才能作为可靠结论。

    finding: 待验证的发现描述
    all_evidence: 所有已收集的证据列表
    """
    supporting_sources = set()
    for ev in all_evidence:
        # 检查该证据是否支持此发现（简化版：关键词匹配）
        finding_terms = [w.lower() for w in finding.split() if len(w) > 4]
        ev_text = (ev.source_title + " " + ev.content).lower()
        overlap = sum(1 for t in finding_terms if t in ev_text)
        if overlap >= len(finding_terms) * 0.3:
            supporting_sources.add(ev.source_type)  # 按来源类型去重

    return {
        "finding": finding,
        "source_count": len(supporting_sources),
        "sources": list(supporting_sources),
        "validated": len(supporting_sources) >= min_sources
    }
```

### 数据来源标注（最高优先级）

**研究备忘录中必须明确区分"来自 API 的数据"和"LLM 的推理/推断"。** 具体规则：

1. **来自 API 的数据**：论文标题、引用数、期刊名、摘要内容、LKM 匹配结果、学者 h-index 等 --> 标注为事实
2. **LLM 的推理**：从数据中归纳的趋势、因果推断、假设生成、对比分析 --> 标注为推断
3. **混合内容**：基于 API 数据做出的判断 --> 标注数据基础和推理过程

```python
def format_evidence_with_source(content, source_type):
    """在输出中明确标注信息来源类型。"""
    if source_type == "api_data":
        return f"[数据] {content}"      # 直接来自 API 返回
    elif source_type == "llm_inference":
        return f"[推断] {content}"      # LLM 基于数据的分析
    elif source_type == "cross_validated":
        return f"[已验证] {content}"    # 经多源交叉验证
    else:
        return f"[未验证] {content}"    # 单一来源，未经验证
```

### 过滤后检查

- 如果某个关键结论仅由单一来源支持：在备忘录中明确标注「此结论仅基于单一来源（paper/lkm/web），置信度有限」
- 如果不同来源的结论相互矛盾：在"矛盾与争议"部分详细列出，不要强行统一
- **永远不要**将 LLM 的推测呈现为已验证的事实

---

## 报告分析深度要求

**研究备忘录不是 API 数据的格式化转储**。你是一个严谨的研究者，必须在备忘录中提供：

1. **区分事实与推断**：每条关键结论标注是来自数据还是推理
2. **多源交叉验证**：关键发现必须被至少两个独立来源支持才能标记为可靠
3. **置信度层次化**：区分"有强证据支持的结论"、"有初步证据的假设"、"纯推测"
4. **证据链完整性**：从数据到结论的推理链条必须清晰可追溯
5. **技术表述精确性**：涉及硬件规格、物理量级、算法复杂度等技术细节时，必须使用精确的表述

### 技术精确性要求

**涉及前沿技术（量子计算、AI 硬件等）的报告，必须注意**：
- 区分**物理比特数**和**有效逻辑比特数**（如量子计算中"1000 物理比特 ≠ 1000 可用比特，考虑纠错开销后有效逻辑比特 <20"）
- 区分**"当前硬件上无优势"**和**"理论上无优势"**（如 QML 可能有理论优势但当前无法实现）
- 技术能力的限制因素要准确（如量子计算瓶颈不仅是比特数，还有相干时间和门保真度）
- **追踪最新硬件里程碑**：如 Microsoft 逻辑量子比特 (2024)、Google Willow 纠错突破 (2024) 等，这些直接影响时间线预估
- 涉及成本分析时，给出具体参考点（如 "IBM 量子云 $X/量子比特时" vs "同等精度经典计算 $Y/CPU时"）

### 禁止的行为

- 将 LLM 的推测呈现为来自文献的事实
- 将单一论文的结论泛化为领域共识
- 在结论中引入搜索结果中没有出现的信息
- 忽略矛盾证据只报告支持结论的证据
- 使用过时的技术参数（如引用 2022 年的量子计算能力来预判 2025 年的时间线）
- 忽略经济成本维度只讨论技术可行性

### 推荐的做法

- 明确标注来源："[数据] 3 篇论文报道 GO 掺量 0.03% 时抗压强度提升 15-30%"
- 标注推断："[推断] 基于上述 3 篇论文的一致结论，0.03% 可能是最优掺量范围"
- 报告矛盾："Wang et al. 报道最优掺量为 0.05%（[数据]），与上述 0.03% 结论存在分歧，可能因水泥类型不同"
- 量化置信度："该结论有 4 条论文证据 + 1 条 LKM 验证支持，置信度评为 HIGH"
- 精确表述硬件限制："当前 NISQ 设备的瓶颈不是物理比特数（IBM Eagle 已有 1121），而是有效相干时间内可执行的门深度（约 100-300 双量子比特门）"

---

## 工作流程图

```
输入: question, constraints
        │
        ▼
┌──────────────────────────────────────┐
│  阶段 1: 问题分解                      │
│  → 将开放问题拆解为可搜索的子问题       │
│  → 确定初始搜索策略                    │
│  → 选择首轮使用的工具                  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  阶段 2: 迭代搜索与分析 (循环)         │
│                                      │
│  ┌─ 2a. 执行搜索 ──────────────────┐ │
│  │  paper-search / scholar-search  │ │
│  │  lkm / web-search / pdf-parser  │ │
│  └──────────────┬──────────────────┘ │
│                 │                    │
│  ┌─ 2b. 分析结果 ──────────────────┐ │
│  │  提取关键发现                    │ │
│  │  更新证据链                     │ │
│  │  评估当前置信度                  │ │
│  └──────────────┬──────────────────┘ │
│                 │                    │
│  ┌─ 2c. 决策: 是否继续 ────────────┐ │
│  │  置信度 >= 阈值? → 退出循环     │ │
│  │  达到最大轮次? → 退出循环       │ │
│  │  否则 → 生成新的搜索查询        │ │
│  └──────────────┬──────────────────┘ │
│                 │                    │
│         循环回到 2a                   │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  阶段 3: 综合与输出                    │
│  → 构建证据链                        │
│  → 评估结论置信度                     │
│  → 生成研究备忘录                     │
│  → 提出进一步研究建议                  │
└──────────────────────────────────────┘
```

---

## 通用代码模板

```python
import os, sys, time, json, requests
from datetime import datetime, timedelta

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误: 请设置环境变量 ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
H = {"accessKey": AK, "Content-Type": "application/json"}
H_GET = {"accessKey": AK}
```

---

## 完整 Python 脚本

以下是完整的自主研究代理脚本，展示迭代循环逻辑：

```python
#!/usr/bin/env python3
"""
自主研究代理 (Research Agent)

围绕一个开放式研究问题，自主迭代搜索、分析、推理，
直到形成可靠结论并构建完整证据链。

用法:
    export ACCESS_KEY="your_access_key"
    python3 research_agent.py
"""

import os, sys, time, json, re, requests
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# 配置
# ============================================================

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误: 请设置环境变量 ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
H = {"accessKey": AK, "Content-Type": "application/json"}
H_GET = {"accessKey": AK}

# -- 用户可修改区域 --
CONFIG = {
    "question": "Is graphene oxide effective for improving concrete mechanical properties? What is the optimal dosage?",
    "max_iterations": 5,
    "confidence_threshold": 0.7,
    "time_range_years": 5,
    "scope": "balanced",      # narrow / balanced / broad
    "depth": "standard",      # quick / standard / deep
}

SCOPE_PAPER_SIZE = {"narrow": 10, "balanced": 20, "broad": 50}
DEPTH_PARSE_N = {"quick": 0, "standard": 3, "deep": 5}


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Evidence:
    """单条证据"""
    source_type: str          # paper / lkm / web / scholar
    source_id: str            # DOI, URL, claim ID 等
    source_title: str
    content: str              # 证据内容摘要
    relevance: float          # 与问题的相关度 (0-1)
    supports_conclusion: Optional[bool] = None  # True=支持, False=反对, None=中立

@dataclass
class Iteration:
    """单轮迭代记录"""
    round_num: int
    query: str                # 本轮搜索查询
    tool_used: str            # 使用的工具
    findings: list = field(default_factory=list)      # 本轮发现
    evidence: list = field(default_factory=list)       # 本轮收集的证据
    decision: str = ""        # 下一步决策

@dataclass
class ResearchState:
    """研究状态"""
    question: str
    sub_questions: list = field(default_factory=list)
    iterations: list = field(default_factory=list)
    all_evidence: list = field(default_factory=list)
    current_hypothesis: str = ""
    confidence: float = 0.0
    explored_queries: set = field(default_factory=set)


# ============================================================
# 工具函数: 调用各原子 Skill
# ============================================================

def search_papers(keywords, question, page_size=20, start_time="", end_time=""):
    """调用 paper-search: POST /v1/paper/rag/pass/keyword"""
    r = requests.post(f"{BASE}/v1/paper/rag/pass/keyword", headers=H, json={
        "words": keywords,
        "question": question,
        "type": 5,
        "startTime": start_time,
        "endTime": end_time,
        "pageSize": page_size
    })
    r.raise_for_status()
    text = r.text.strip()
    first_line = text.split('\n')[0]
    data = json.loads(first_line)
    if data.get("code") != 0:
        print(f"    [paper-search] 失败: {data.get('message')}")
        return []
    papers = data.get("data", [])
    papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
    return papers


def search_scholars(name, tags="", page_size=5):
    """调用 scholar-search: POST /v1/paper-server/scholar/search"""
    r = requests.post(f"{BASE}/v1/paper-server/scholar/search", headers=H, json={
        "name": name,
        "tags": tags,
        "page": 1,
        "pageSize": page_size
    })
    r.raise_for_status()
    data = r.json()
    return data.get("data", {}).get("items", [])


def lkm_search(query, limit=10):
    """调用 lkm: POST /v1/lkm/search"""
    r = requests.post(f"{BASE}/v1/lkm/search", headers=H, json={
        "query": query,
        "limit": limit
    })
    r.raise_for_status()
    return r.json().get("data", [])


def lkm_claims_match(text, limit=5):
    """调用 lkm: POST /v1/lkm/claims/match"""
    r = requests.post(f"{BASE}/v1/lkm/claims/match", headers=H, json={
        "text": text,
        "limit": limit
    })
    r.raise_for_status()
    data = r.json().get("data", {})
    return {
        "variables": data.get("variables", []),
        "papers": data.get("papers", {}),
        "new_claim_likely": data.get("new_claim_likely", False)
    }


def web_search(query, num=5):
    """调用 web-search: GET /v1/search/web"""
    r = requests.get(f"{BASE}/v1/search/web", headers=H_GET, params={
        "q": query,
        "num": min(num, 10)
    })
    r.raise_for_status()
    return r.json().get("organic_results", [])


def parse_pdf_async(url, pages=None):
    """调用 pdf-parser: POST /v1/parse/trigger-url-async"""
    r = requests.post(f"{BASE}/v1/parse/trigger-url-async", headers=H, json={
        "url": url,
        "sync": False,
        "textual": True,
        "table": True,
        "expression": True,
        "equation": True,
        "pages": pages or [],
        "timeout": 1800
    })
    r.raise_for_status()
    data = r.json()
    if data.get("code"):
        return None
    return data.get("token")


def poll_parse_result(token, max_attempts=30, interval=3):
    """轮询 pdf-parser 结果: POST /v1/parse/get-result"""
    for _ in range(max_attempts):
        time.sleep(interval)
        r = requests.post(f"{BASE}/v1/parse/get-result", headers=H, json={
            "token": token,
            "content": True,
            "objects": False,
            "pages_dict": False
        })
        r.raise_for_status()
        result = r.json()
        if result.get("status") == "success":
            return result.get("content", "")
        elif result.get("status") == "failed":
            return None
    return None


# ============================================================
# 核心逻辑: 问题分解
# ============================================================

def decompose_question(question):
    """
    将开放式问题分解为可搜索的子问题。

    策略:
    - 提取核心实体和关系
    - 生成针对不同方面的子问题
    - 确定每个子问题最适合的工具
    """
    # 提取关键词（简化版：按名词短语拆分）
    # 实际使用中可接入 LLM 做更智能的分解
    words = question.split()
    # 去除常见停用词
    stop_words = {"is", "are", "the", "a", "an", "for", "of", "in", "on",
                  "to", "and", "or", "what", "how", "why", "which", "does",
                  "do", "can", "could", "would", "should", "has", "have",
                  "been", "be", "was", "were", "it", "its", "this", "that",
                  "with", "from", "by", "at", "as", "into", "about"}
    keywords = [w.strip("?.,!") for w in words if w.lower().strip("?.,!") not in stop_words and len(w) > 2]

    sub_questions = [
        {
            "query": question,
            "keywords": keywords,
            "tool": "paper-search",
            "purpose": "查找直接相关的学术论文"
        },
        {
            "query": question,
            "keywords": keywords[:5],
            "tool": "lkm-search",
            "purpose": "从知识图谱中搜索相关知识节点"
        },
        {
            "query": " ".join(keywords[:4]) + " review",
            "keywords": keywords[:4] + ["review"],
            "tool": "web-search",
            "purpose": "从网络获取综述或最新报道"
        }
    ]

    return keywords, sub_questions


# ============================================================
# 核心逻辑: 单轮迭代
# ============================================================

def execute_iteration(state, sub_q, config):
    """
    执行一轮搜索迭代。

    Args:
        state: 当前研究状态
        sub_q: 子问题描述 dict
        config: 运行配置

    Returns:
        Iteration: 本轮迭代结果
    """
    iteration = Iteration(
        round_num=len(state.iterations) + 1,
        query=sub_q["query"],
        tool_used=sub_q["tool"]
    )

    scope = config.get("scope", "balanced")
    end_time = datetime.now().strftime("%Y-%m-%d")
    start_time = (datetime.now() - timedelta(days=365 * config.get("time_range_years", 5))).strftime("%Y-%m-%d")

    print(f"\n  --- 迭代 {iteration.round_num}: {sub_q['tool']} ---")
    print(f"  查询: {sub_q['query'][:80]}")
    print(f"  目的: {sub_q['purpose']}")

    try:
        if sub_q["tool"] == "paper-search":
            papers = search_papers(
                keywords=sub_q["keywords"],
                question=sub_q["query"],
                page_size=SCOPE_PAPER_SIZE.get(scope, 20),
                start_time=start_time,
                end_time=end_time
            )
            print(f"  结果: 找到 {len(papers)} 篇论文")

            for p in papers[:10]:
                ev = Evidence(
                    source_type="paper",
                    source_id=p.get("doi", ""),
                    source_title=p.get("enName", ""),
                    content=p.get("enAbstract", "")[:300],
                    relevance=min(1.0, p.get("citationNums", 0) / 100)
                )
                iteration.evidence.append(ev)
                iteration.findings.append(
                    f"[论文] {p.get('enName', '')[:60]} "
                    f"(引用:{p.get('citationNums', 0)}, IF:{p.get('impactFactor', 0)})"
                )

        elif sub_q["tool"] == "lkm-search":
            nodes = lkm_search(sub_q["query"], limit=10)
            print(f"  结果: 找到 {len(nodes)} 个知识节点")

            for node in nodes:
                content = node.get("content", "") if isinstance(node, dict) else str(node)
                ev = Evidence(
                    source_type="lkm",
                    source_id=node.get("id", "") if isinstance(node, dict) else "",
                    source_title="知识图谱节点",
                    content=content[:300],
                    relevance=node.get("score", 0.5) if isinstance(node, dict) else 0.5
                )
                iteration.evidence.append(ev)
                iteration.findings.append(f"[知识图谱] {content[:80]}")

        elif sub_q["tool"] == "lkm-claims":
            result = lkm_claims_match(sub_q["query"], limit=5)
            variables = result.get("variables", [])
            print(f"  结果: 匹配到 {len(variables)} 条论断")

            for var in variables:
                ev = Evidence(
                    source_type="lkm",
                    source_id=var.get("id", ""),
                    source_title="论断匹配",
                    content=var.get("content", "")[:300],
                    relevance=var.get("score", 0.5),
                    supports_conclusion=(var.get("role") == "conclusion")
                )
                iteration.evidence.append(ev)
                iteration.findings.append(
                    f"[论断] {var.get('content', '')[:80]} "
                    f"(角色:{var.get('role', 'N/A')}, 分数:{var.get('score', 0):.2f})"
                )

            if result.get("new_claim_likely"):
                iteration.findings.append("[注意] 该论断可能是新发现，文献支持有限")

        elif sub_q["tool"] == "web-search":
            results = web_search(sub_q["query"], num=5)
            print(f"  结果: 找到 {len(results)} 条网页结果")

            for hit in results:
                ev = Evidence(
                    source_type="web",
                    source_id=hit.get("link", ""),
                    source_title=hit.get("title", ""),
                    content=hit.get("snippet", "")[:300],
                    relevance=0.5
                )
                iteration.evidence.append(ev)
                iteration.findings.append(f"[网页] {hit.get('title', '')[:60]}")

        elif sub_q["tool"] == "scholar-search":
            scholars = search_scholars(
                name=sub_q.get("scholar_name", ""),
                tags=sub_q.get("tags", ""),
                page_size=5
            )
            print(f"  结果: 找到 {len(scholars)} 位学者")

            for s in scholars:
                ev = Evidence(
                    source_type="scholar",
                    source_id=s.get("scholarId", ""),
                    source_title=f"{s.get('nameEn', '')} ({s.get('scholarOrgNameEn', '')})",
                    content=f"h-index:{s.get('hIndex', 0)}, 发文:{s.get('paperNums', 0)}, 引用:{s.get('citationNums', 0)}",
                    relevance=0.4
                )
                iteration.evidence.append(ev)
                iteration.findings.append(
                    f"[学者] {s.get('nameEn', '')} @ {s.get('scholarOrgNameEn', '')} "
                    f"(h-index:{s.get('hIndex', 0)})"
                )

        elif sub_q["tool"] == "pdf-parse":
            pdf_url = sub_q.get("pdf_url", "")
            if pdf_url:
                token = parse_pdf_async(pdf_url, pages=[0, 1, 2])
                if token:
                    content = poll_parse_result(token)
                    if content:
                        ev = Evidence(
                            source_type="paper",
                            source_id=pdf_url,
                            source_title="PDF 全文解析",
                            content=content[:500],
                            relevance=0.8
                        )
                        iteration.evidence.append(ev)
                        iteration.findings.append(f"[PDF] 解析完成, {len(content)} 字符")
                        print(f"  结果: PDF 解析完成, {len(content)} 字符")
                    else:
                        print(f"  结果: PDF 解析失败或超时")
                else:
                    print(f"  结果: PDF 提交解析失败")

    except Exception as e:
        print(f"  错误: {e}")
        iteration.findings.append(f"[错误] {sub_q['tool']}: {e}")

    state.explored_queries.add(sub_q["query"])
    return iteration


# ============================================================
# 核心逻辑: 评估置信度
# ============================================================

def evaluate_confidence(state):
    """
    根据当前收集的证据评估结论置信度。

    评估维度:
    - 证据数量: 是否有足够多的证据
    - 证据多样性: 是否来自不同来源
    - 证据一致性: 支持/反对比例
    - 证据质量: 高引用、高影响因子的占比
    """
    if not state.all_evidence:
        return 0.0

    total = len(state.all_evidence)

    # 1. 数量分 (0-0.3): 至少需要 5 条证据才有基础置信度
    quantity_score = min(0.3, total * 0.06)

    # 2. 多样性分 (0-0.2): 来源类型越多越好
    source_types = set(e.source_type for e in state.all_evidence)
    diversity_score = min(0.2, len(source_types) * 0.05)

    # 3. 一致性分 (0-0.3): 支持证据占比
    supporting = sum(1 for e in state.all_evidence if e.supports_conclusion is True)
    opposing = sum(1 for e in state.all_evidence if e.supports_conclusion is False)
    if supporting + opposing > 0:
        consistency_score = 0.3 * (supporting / (supporting + opposing))
    else:
        # 无明确支持/反对标记时给中等分
        consistency_score = 0.15

    # 4. 质量分 (0-0.2): 平均相关度
    avg_relevance = sum(e.relevance for e in state.all_evidence) / total
    quality_score = 0.2 * avg_relevance

    confidence = quantity_score + diversity_score + consistency_score + quality_score
    return min(1.0, confidence)


# ============================================================
# 核心逻辑: 生成下一轮查询
# ============================================================

def plan_next_iteration(state, config):
    """
    根据当前研究状态，决定下一轮搜索什么。

    策略:
    - 如果论文证据不足 → 换关键词再搜论文
    - 如果有核心论断但未验证 → 用 LKM claims/match 验证
    - 如果缺少最新进展 → 用 web-search 补充
    - 如果发现重要学者 → 搜索该学者的更多工作
    - 如果有重要论文但未解析全文 → 用 pdf-parser 解析
    """
    used_tools = [it.tool_used for it in state.iterations]
    evidence_types = set(e.source_type for e in state.all_evidence)

    # 策略 1: 如果还没做论断验证，且已有初步假设 → 验证论断
    if "lkm-claims" not in used_tools and state.current_hypothesis:
        return {
            "query": state.current_hypothesis,
            "keywords": [],
            "tool": "lkm-claims",
            "purpose": "验证当前假设是否有文献支持"
        }

    # 策略 2: 如果只搜了论文没搜知识图谱 → 搜知识图谱
    if "lkm" not in evidence_types and "lkm-search" not in used_tools:
        return {
            "query": state.question,
            "keywords": [],
            "tool": "lkm-search",
            "purpose": "从知识图谱获取结构化知识"
        }

    # 策略 3: 如果只搜了学术来源没搜网页 → 搜网页补充最新信息
    if "web" not in evidence_types:
        return {
            "query": state.question + " latest research",
            "keywords": [],
            "tool": "web-search",
            "purpose": "搜索最新的网络信息和报道"
        }

    # 策略 4: 从已有证据中提取新关键词，做进一步论文搜索
    existing_keywords = set()
    for it in state.iterations:
        if it.tool_used == "paper-search":
            existing_keywords.update(
                sub_q.get("keywords", [])
                for sub_q in state.sub_questions
            )

    # 从最新证据中提取可能的新搜索方向
    new_terms = []
    for ev in state.all_evidence[-5:]:
        # 简化: 取标题中的关键词作为新搜索方向
        words = ev.source_title.split()
        for w in words:
            w_clean = w.strip(".,;:()[]").lower()
            if len(w_clean) > 4 and w_clean not in existing_keywords:
                new_terms.append(w_clean)

    if new_terms:
        refined_query = state.question + " " + " ".join(new_terms[:3])
        if refined_query not in state.explored_queries:
            return {
                "query": refined_query,
                "keywords": new_terms[:5],
                "tool": "paper-search",
                "purpose": "基于已有发现，用新关键词深入搜索"
            }

    # 策略 5: 如果有重要论文 DOI，尝试解析全文
    depth = config.get("depth", "standard")
    parse_n = DEPTH_PARSE_N.get(depth, 3)
    if parse_n > 0:
        for ev in state.all_evidence:
            if ev.source_type == "paper" and ev.source_id and ev.relevance > 0.5:
                pdf_url = f"https://doi.org/{ev.source_id}"
                if pdf_url not in state.explored_queries:
                    return {
                        "query": pdf_url,
                        "keywords": [],
                        "tool": "pdf-parse",
                        "pdf_url": pdf_url,
                        "purpose": f"解析高相关度论文全文: {ev.source_title[:50]}"
                    }

    # 无更多策略，返回 None 终止迭代
    return None


# ============================================================
# 核心逻辑: 综合生成研究备忘录
# ============================================================

def synthesize_memo(state):
    """生成最终的研究备忘录。"""

    # 置信度评级
    if state.confidence >= 0.7:
        confidence_label = "HIGH"
    elif state.confidence >= 0.4:
        confidence_label = "MEDIUM"
    else:
        confidence_label = "LOW"

    lines = []
    lines.append(f"# 研究备忘录: {state.question}")
    lines.append(f"\n> 生成时间: {datetime.now().isoformat()}")
    lines.append(f"> 迭代轮次: {len(state.iterations)}")
    lines.append(f"> 收集证据: {len(state.all_evidence)} 条")

    # 1. 结论摘要
    lines.append("\n## 1. 结论摘要\n")
    if state.current_hypothesis:
        lines.append(f"**核心结论:** {state.current_hypothesis}")
    else:
        lines.append("**核心结论:** 尚未形成明确结论，需要进一步研究。")
    lines.append(f"\n**置信度:** {confidence_label} ({state.confidence:.0%})")

    supporting = [e for e in state.all_evidence if e.supports_conclusion is True]
    opposing = [e for e in state.all_evidence if e.supports_conclusion is False]
    lines.append(f"\n**置信度依据:** 共 {len(state.all_evidence)} 条证据，"
                 f"其中 {len(supporting)} 条支持、{len(opposing)} 条反对、"
                 f"{len(state.all_evidence) - len(supporting) - len(opposing)} 条中立。")

    # 2. 证据链
    lines.append("\n## 2. 证据链\n")
    sorted_evidence = sorted(state.all_evidence, key=lambda e: e.relevance, reverse=True)
    for i, ev in enumerate(sorted_evidence[:15], 1):
        support_tag = ""
        if ev.supports_conclusion is True:
            support_tag = " [支持]"
        elif ev.supports_conclusion is False:
            support_tag = " [反对]"

        lines.append(f"{i}. **[{ev.source_type}]** {ev.source_title[:60]}{support_tag}")
        lines.append(f"   - 来源: `{ev.source_id[:60]}`")
        lines.append(f"   - 内容: {ev.content[:150]}...")
        lines.append(f"   - 相关度: {ev.relevance:.2f}")

    # 3. 研究过程
    lines.append("\n## 3. 研究过程\n")
    for it in state.iterations:
        lines.append(f"### 迭代 {it.round_num}: {it.tool_used}\n")
        lines.append(f"- **查询:** {it.query[:80]}")
        lines.append(f"- **发现数:** {len(it.findings)}")
        for finding in it.findings[:5]:
            lines.append(f"  - {finding[:100]}")
        if len(it.findings) > 5:
            lines.append(f"  - ...及另外 {len(it.findings) - 5} 条发现")
        if it.decision:
            lines.append(f"- **决策:** {it.decision}")
        lines.append("")

    # 4. 矛盾与争议
    lines.append("\n## 4. 矛盾与争议\n")
    if opposing:
        lines.append("以下证据与当前结论存在矛盾:\n")
        for ev in opposing:
            lines.append(f"- **{ev.source_title[:60]}** (`{ev.source_id[:40]}`)")
            lines.append(f"  {ev.content[:150]}")
    else:
        lines.append("本次研究未发现与结论直接矛盾的证据。")

    # 5. 进一步研究建议
    lines.append("\n## 5. 进一步研究建议\n")
    if state.confidence < 0.7:
        lines.append("- 当前置信度不足，建议扩大搜索范围或增加迭代轮次")
    if "scholar" not in set(e.source_type for e in state.all_evidence):
        lines.append("- 建议搜索该领域的核心学者，了解其最新研究动态")
    if len([e for e in state.all_evidence if e.source_type == "paper"]) < 5:
        lines.append("- 论文证据较少，建议使用不同关键词组合进行更多轮检索")

    # 推荐关键论文
    top_papers = [e for e in sorted_evidence if e.source_type == "paper"][:5]
    if top_papers:
        lines.append("\n**推荐精读论文:**\n")
        for i, p in enumerate(top_papers, 1):
            lines.append(f"{i}. {p.source_title[:70]} (`{p.source_id}`)")

    return "\n".join(lines)


# ============================================================
# 主流程: 迭代循环
# ============================================================

def run_research_agent(config):
    """
    运行自主研究代理的主循环。

    流程:
    1. 分解问题
    2. 循环: 执行搜索 → 分析结果 → 评估置信度 → 决策是否继续
    3. 综合生成研究备忘录
    """
    question = config["question"]
    max_iter = config.get("max_iterations", 5)
    threshold = config.get("confidence_threshold", 0.7)

    print(f"\n{'#'*60}")
    print(f"  自主研究代理")
    print(f"  问题: {question}")
    print(f"  最大迭代: {max_iter}, 置信度阈值: {threshold}")
    print(f"{'#'*60}")

    # --- 阶段 1: 问题分解 ---
    print(f"\n{'='*60}")
    print("阶段 1: 问题分解")
    print(f"{'='*60}")

    keywords, sub_questions = decompose_question(question)
    print(f"  提取关键词: {keywords}")
    print(f"  生成 {len(sub_questions)} 个子问题:")
    for sq in sub_questions:
        print(f"    - [{sq['tool']}] {sq['purpose']}")

    state = ResearchState(
        question=question,
        sub_questions=sub_questions
    )

    # --- 阶段 2: 迭代搜索与分析 ---
    print(f"\n{'='*60}")
    print("阶段 2: 迭代搜索与分析")
    print(f"{'='*60}")

    # 先执行初始子问题
    pending_queries = list(sub_questions)

    for i in range(max_iter):
        print(f"\n  ======== 第 {i+1}/{max_iter} 轮 ========")

        # 2a. 选择查询
        if pending_queries:
            sub_q = pending_queries.pop(0)
        else:
            sub_q = plan_next_iteration(state, config)
            if sub_q is None:
                print("  [决策] 无更多可探索的方向，提前终止。")
                break

        # 2b. 执行搜索
        iteration = execute_iteration(state, sub_q, config)

        # 2c. 更新状态
        state.iterations.append(iteration)
        state.all_evidence.extend(iteration.evidence)

        # 2d. 从第一轮论文搜索结果构建初步假设
        if i == 0 and iteration.evidence:
            # 取第一篇高引论文的摘要作为初步假设方向
            top_ev = max(iteration.evidence, key=lambda e: e.relevance)
            state.current_hypothesis = (
                f"基于初步检索，关于「{question}」的研究表明: "
                f"{top_ev.content[:200]}"
            )

        # 2e. 评估置信度
        state.confidence = evaluate_confidence(state)
        print(f"\n  [状态] 证据总数: {len(state.all_evidence)}, "
              f"置信度: {state.confidence:.0%}")

        # 2f. 决策
        if state.confidence >= threshold:
            iteration.decision = f"置信度 ({state.confidence:.0%}) 已达阈值 ({threshold:.0%})，停止迭代。"
            print(f"  [决策] {iteration.decision}")
            break
        elif i == max_iter - 1:
            iteration.decision = "已达最大迭代次数，停止。"
            print(f"  [决策] {iteration.decision}")
        else:
            iteration.decision = f"置信度 ({state.confidence:.0%}) 不足，继续搜索。"
            print(f"  [决策] {iteration.decision}")

    # --- 阶段 3: 综合与输出 ---
    print(f"\n{'='*60}")
    print("阶段 3: 综合与输出")
    print(f"{'='*60}\n")

    memo = synthesize_memo(state)
    print(memo)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    memo_file = f"research_memo_{timestamp}.md"
    with open(memo_file, "w", encoding="utf-8") as f:
        f.write(memo)
    print(f"\n研究备忘录已保存到: {memo_file}")

    # 保存原始数据
    data_file = f"research_data_{timestamp}.json"
    raw_data = {
        "question": state.question,
        "confidence": state.confidence,
        "hypothesis": state.current_hypothesis,
        "iterations": len(state.iterations),
        "evidence_count": len(state.all_evidence),
        "evidence": [
            {
                "source_type": e.source_type,
                "source_id": e.source_id,
                "source_title": e.source_title,
                "content": e.content[:200],
                "relevance": e.relevance,
                "supports_conclusion": e.supports_conclusion
            }
            for e in state.all_evidence
        ]
    }
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"原始数据已保存到: {data_file}")

    return state, memo


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    run_research_agent(CONFIG)
```

---

## 各步骤的 curl 示例

以下展示了研究代理在一轮迭代中可能依次调用的接口：

### 1. 论文搜索

```bash
AK="YOUR_ACCESS_KEY"

curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["graphene oxide", "concrete", "mechanical properties"],
    "question": "Is graphene oxide effective for improving concrete mechanical properties?",
    "type": 5,
    "startTime": "2021-01-01",
    "endTime": "2026-01-01",
    "pageSize": 20
  }'
```

### 2. 知识图谱搜索

```bash
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "graphene oxide effect on concrete compressive strength",
    "limit": 10
  }' | jq .
```

### 3. 论断验证

```bash
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/claims/match" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Graphene oxide at 0.03% dosage improves concrete compressive strength by 15-30%",
    "limit": 5
  }' | jq .
```

### 4. 网页搜索

```bash
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=graphene+oxide+concrete+latest+research&num=5" \
  -H "accessKey: $AK" | jq '.organic_results[] | {title, link, snippet}'
```

### 5. 学者搜索

```bash
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper-server/scholar/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"name": "graphene concrete", "tags": "graphene oxide concrete", "page": 1, "pageSize": 5}'
```

### 6. PDF 全文解析

```bash
# 提交解析
TOKEN=$(curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/trigger-url-async" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "url": "https://doi.org/10.1016/j.conbuildmat.2023.xxxxx",
    "sync": false,
    "textual": true,
    "table": true,
    "expression": true,
    "equation": true,
    "pages": [0, 1, 2],
    "timeout": 1800
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 轮询结果
sleep 5
curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/get-result" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d "{\"token\": \"$TOKEN\", \"content\": true, \"objects\": false, \"pages_dict\": false}"
```

---

## 迭代策略详解

### 何时选择哪个工具

| 情况 | 选择工具 | 原因 |
|------|---------|------|
| 初始探索，不确定方向 | `paper-search` | 论文是最结构化的学术信息来源 |
| 需要验证一个具体结论 | `lkm claims/match` | 直接匹配支持/反对的证据 |
| 需要理解概念关系 | `lkm search` | 知识图谱提供结构化的概念网络 |
| 论文搜索结果不足 | `web-search` | 补充非学术来源的最新信息 |
| 发现关键学者 | `scholar-search` | 了解该学者的其他工作 |
| 需要论文全文细节 | `pdf-parser` | 摘要信息不够，需要全文 |

### 何时停止迭代

- **置信度达标:** 收集到足够多、足够一致的证据
- **达到最大轮次:** 防止无限循环
- **无新方向:** 所有合理的搜索策略都已尝试
- **证据饱和:** 新的搜索不再带来新发现

### 搜索范围与深度配置

| 参数组合 | 论文数 | 解析数 | 预计时间 | 适合场景 |
|---------|--------|--------|----------|----------|
| `narrow` + `quick` | 10 | 0 | 1-2 分钟 | 快速验证一个假设 |
| `balanced` + `standard` | 20 | 3 | 3-5 分钟 | 一般研究问题 |
| `broad` + `deep` | 50 | 5 | 10-15 分钟 | 深入调研 |

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 置信度一直很低 | 问题太宽泛或领域太新 | 缩小问题范围，增加 `max_iterations`，或降低 `confidence_threshold` |
| 迭代重复搜索相同内容 | 关键词提取不够智能 | 手动提供更精确的关键词，或在问题描述中加入具体术语 |
| 某个工具调用失败 | 网络问题或参数错误 | 代理会自动跳过失败的工具，继续使用其他工具 |
| 证据链中有矛盾 | 领域存在争议 | 正常现象，备忘录的"矛盾与争议"部分会标注 |
| 结论过于笼统 | 初始问题不够具体 | 提供更具体的研究问题，如加入材料名称、具体参数等 |
| 401 Unauthorized | accessKey 无效 | 确认 ACCESS_KEY 正确，检查 `~/.openclaw/openclaw.json` 配置 |
| 论文搜索返回多行 JSON | paper-search 的 streaming 格式 | 脚本已处理：取第一行解析 `json.loads(r.text.split('\n')[0])` |
| PDF 解析超时 | 论文太长或服务繁忙 | 使用 `pages` 参数只解析前几页，或切换为 `quick` 深度跳过全文解析 |

---

## 搭配使用

- **research-agent** 形成初步结论 → **literature-review** 对该方向做完整综述
- **research-agent** 发现关键学者 → **scholar-profiler** 生成学者画像
- **research-agent** 验证一个论断 → **pre-review** 评审相关论文的可靠性
- **research-agent** 发现技术路线 → **tech-compare** 做系统化技术对比
