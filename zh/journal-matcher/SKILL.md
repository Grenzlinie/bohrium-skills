---
name: journal-matcher
description: "Journal recommendation for manuscript submission by analyzing topic-journal fit and publication patterns. Use when: user has a paper ready and needs to choose which journal to submit to. NOT for: paper search (use bohrium-paper-search), literature review (use literature-review)."
---

# SKILL: 期刊匹配推荐 (Journal Matcher)

## 概述

编排 `paper-search` 和 `web-search` 两个原子技能，根据用户的论文摘要/关键词和偏好约束，分析同主题论文的发表去向与期刊特征，输出 5-10 个推荐期刊及详细投稿参考信息。

**编排的原子技能：**

| 步骤 | 原子 Skill | 端点 | 功能 |
|------|-----------|------|------|
| 1 | `paper-search` | `POST /v1/paper/rag/pass/keyword` | 语义检索同主题论文，提取发表期刊分布与影响因子 |
| 2 | `web-search` | `GET /v1/search/web?q=...&num=5` | 补充期刊最新信息（IF 变化、审稿周期、版面费等） |

**适用场景：**

- 论文初稿已完成，需要选择投稿期刊
- 对比多个候选期刊的匹配度和投稿难度
- 了解特定方向论文的发表去向分布
- 根据影响因子、审稿速度、OA 等约束筛选期刊

**不适用：**

- 搜索论文 → `bohrium-paper-search`
- 多篇论文综述 → `literature-review`
- 论文精读拆解 → `paper-dissector`
- 选题探索 → `topic-scout`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"journal-matcher": {
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
| `abstract` | string | 是 | — | 论文摘要（英文，建议 150-300 词） |
| `keywords` | string[] | 是 | — | 论文关键词列表（3-8 个英文术语） |
| `if_min` | float | 否 | 0 | 最低影响因子要求 |
| `if_max` | float | 否 | 无上限 | 最高影响因子（用于避开顶刊降低拒稿风险） |
| `open_access` | bool | 否 | `false` | 是否仅推荐 OA 期刊 |
| `review_speed` | string | 否 | `""` | 审稿速度偏好：`"fast"`（< 2 月）/ `"normal"` / `""` 不限 |
| `jcr_zones` | string[] | 否 | `[]` | JCR 分区筛选，如 `["Q1", "Q2"]` |
| `exclude_journals` | string[] | 否 | `[]` | 排除的期刊名称列表（如已被拒稿的期刊） |
| `top_n` | int | 否 | 10 | 推荐期刊数量 |

---

## 输出格式

推荐结果包含 5-10 个期刊，每个期刊包含以下信息：

| 字段 | 说明 |
|------|------|
| 期刊名称 | 英文全称 |
| 匹配理由 | 为什么该期刊适合投稿（基于主题匹配度和发表历史） |
| Impact Factor | 最新影响因子 |
| JCR 分区 | Q1 / Q2 / Q3 / Q4 |
| 预估审稿周期 | 从投稿到首次决定的典型时长 |
| 预估接收率 | 基于公开数据的大致接收率 |
| 投稿须知 | OA 选项、版面费、稿件格式等关键信息 |

---

## 工作流程图

```
输入: abstract, keywords, 偏好约束
        │
        ▼
┌──────────────────────────────────────┐
│  步骤 1: 同主题论文检索               │
│  POST /v1/paper/rag/pass/keyword     │
│  → 检索同主题已发表论文               │
│  → 提取 publicationEnName 分布       │
│  → 统计各期刊的论文数量与平均 IF      │
│  → 分析主题-期刊匹配度               │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 2: 期刊信息补充                 │
│  GET /v1/search/web?q=...&num=5      │
│  → 查询各候选期刊最新 IF             │
│  → 查询审稿周期、版面费              │
│  → 查询接收率和 OA 政策              │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 3: 综合排序与推荐               │
│  → 按主题匹配度 + 用户偏好打分        │
│  → 应用 IF / OA / 审稿速度约束过滤    │
│  → 排除用户指定的期刊                 │
│  → 输出 Top-N 推荐列表               │
└──────────────────────────────────────┘
```

---

## 报告质量控制

### 数据溯源要求

**所有定量数据必须标注来源**，以下为典型场景：

- ✅ "Impact Factor: 12.3（来源：2025 JCR 报告）"
- ✅ "预估接收率: 15-20%（来源：期刊官网 2024 年公开数据）"
- ✅ "平均审稿周期: 45 天（来源：web-search 检索到的 ScholarOne 统计）"
- ❌ "接收率 <5%"（无来源）
- ❌ "审稿很快"（无具体数据）

如果某项数据**无法从可靠来源获取**，必须标注"估计值"并说明估算依据：
> 预估接收率: ~10%（估计值，基于该刊 2024 年发文量与投稿量级推断，非官方数据）

### 投稿梯度策略（必须输出）

推荐结果**必须**按梯度组织为三层：

| 层级 | 说明 | 数量 |
|------|------|------|
| **Tier-1 冲刺** | 影响力最高但风险大，匹配度需精准 | 2-3 刊 |
| **Tier-2 稳健** | 主题高度匹配，接收概率合理 | 3-4 刊 |
| **Tier-3 保底** | 审稿快、接收率高，适合赶时间发表 | 2-3 刊 |

每一层级需说明：为什么归入该级别、与用户论文的具体匹配点、相比其他层级的 trade-off。

### 审稿人画像分析

对每个推荐期刊，应给出审稿人画像的粗略判断：
- 该刊近期接收的论文偏向什么类型？（实验/理论/计算/方法学）
- 如果用户论文是纯计算/ML 工作，指出哪些期刊的审稿人对此类论文更友好
- 如果用户论文跨学科，指出哪些期刊更欢迎交叉研究

### 禁止的行为

- ❌ 接收率、审稿周期等数据不标注来源
- ❌ 推荐理由仅为"影响因子高"或"主题相关"（太泛，每个推荐都如此）
- ❌ 不区分 regular article / short communication / letter 的接收标准差异
- ❌ 不考虑用户论文的创新性水平——如果创新不够强，不应推荐 Nature/Science 子刊

---

## 通用代码模板

```python
import os, requests, json

AK = os.environ.get("ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET  = {"accessKey": AK}
```

---

## 步骤 1: 同主题论文检索

使用 `paper-search` 检索与用户论文主题相似的已发表论文，统计各期刊的发表频次和影响因子。

### Python 示例

```python
def search_similar_papers(keywords, abstract, jcr_zones=None, page_size=50):
    """
    检索同主题论文，用于分析发表去向。

    Args:
        keywords: 论文关键词列表
        abstract: 论文摘要（作为 question 传入）
        jcr_zones: JCR 分区筛选
        page_size: 检索数量，建议 30-50 以获得充分的期刊分布样本

    Returns:
        论文列表
    """
    payload = {
        "words": keywords,
        "question": abstract[:500],  # question 字段用于语义匹配
        "type": 5,                   # 题目+摘要+语料+图片+靶点 全方位检索
        "startTime": "",             # 不限起始时间
        "endTime": "",               # 不限截止时间
        "jcrZones": jcr_zones or [],
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
    print(f"[步骤1] 检索到 {len(papers)} 篇同主题论文")
    return papers


def analyze_journal_distribution(papers):
    """
    统计检索结果中各期刊的论文数量和平均影响因子。

    Args:
        papers: search_similar_papers 返回的论文列表

    Returns:
        按论文数量降序排列的期刊统计列表:
        [{"journal": str, "count": int, "avg_if": float,
          "max_if": float, "sample_dois": list, "sample_titles": list}, ...]
    """
    journal_stats = {}

    for p in papers:
        journal = p.get("publicationEnName", "").strip()
        if not journal:
            continue

        if journal not in journal_stats:
            journal_stats[journal] = {
                "journal": journal,
                "count": 0,
                "if_values": [],
                "sample_dois": [],
                "sample_titles": [],
            }

        stats = journal_stats[journal]
        stats["count"] += 1

        impact_factor = p.get("impactFactor", 0)
        if impact_factor and impact_factor > 0:
            stats["if_values"].append(impact_factor)

        if len(stats["sample_dois"]) < 3:
            stats["sample_dois"].append(p.get("doi", ""))
            stats["sample_titles"].append(p.get("enName", ""))

    # 计算平均和最大 IF
    result = []
    for stats in journal_stats.values():
        if_values = stats["if_values"]
        result.append({
            "journal": stats["journal"],
            "count": stats["count"],
            "avg_if": round(sum(if_values) / len(if_values), 2) if if_values else 0,
            "max_if": round(max(if_values), 2) if if_values else 0,
            "sample_dois": stats["sample_dois"],
            "sample_titles": stats["sample_titles"],
        })

    # 按论文数量降序排列
    result.sort(key=lambda x: x["count"], reverse=True)

    print(f"[步骤1] 识别出 {len(result)} 个候选期刊")
    for i, j in enumerate(result[:10]):
        print(f"  {i+1:2d}. {j['journal']} "
              f"(论文数: {j['count']}, 平均IF: {j['avg_if']}, 最高IF: {j['max_if']})")

    return result
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["perovskite", "solar cell", "efficiency", "stability"],
    "question": "We report a novel passivation strategy for perovskite solar cells that achieves power conversion efficiency exceeding 25% with improved long-term stability under ambient conditions.",
    "type": 5,
    "startTime": "",
    "endTime": "",
    "jcrZones": ["Q1"],
    "pageSize": 50
  }'
```

---

## 步骤 2: 期刊信息补充

使用 `web-search` 查询每个候选期刊的最新信息，包括影响因子变化趋势、审稿周期、版面费和 OA 政策。

### Python 示例

```python
def fetch_journal_details(journal_name):
    """
    通过 web-search 补充单个期刊的详细信息。

    Args:
        journal_name: 期刊英文名称

    Returns:
        dict: 期刊详细信息（从搜索结果中提取）
    """
    queries = [
        f"{journal_name} impact factor 2025 review time acceptance rate",
        f"{journal_name} submission guidelines author fees open access",
    ]

    all_snippets = []
    for q in queries:
        try:
            r = requests.get(
                f"{BASE}/v1/search/web",
                headers=HEADERS_GET,
                params={"q": q, "num": 5}
            )
            r.raise_for_status()
            data = r.json()

            for hit in data.get("organic_results", []):
                all_snippets.append({
                    "title": hit.get("title", ""),
                    "link": hit.get("link", ""),
                    "snippet": hit.get("snippet", ""),
                })
        except Exception as e:
            print(f"  [警告] 搜索 '{journal_name}' 信息失败: {e}")

    return {
        "journal": journal_name,
        "web_results": all_snippets,
    }


def enrich_journal_candidates(journal_stats, top_n=10):
    """
    对 Top-N 候选期刊批量补充详细信息。

    Args:
        journal_stats: analyze_journal_distribution 返回的统计列表
        top_n: 补充信息的期刊数量

    Returns:
        enriched_journals: 附加了 web 搜索结果的期刊列表
    """
    candidates = journal_stats[:top_n]
    enriched = []

    print(f"\n[步骤2] 补充 {len(candidates)} 个期刊的详细信息...")

    for j in candidates:
        journal_name = j["journal"]
        print(f"  查询: {journal_name}")
        details = fetch_journal_details(journal_name)

        enriched.append({
            **j,
            "web_results": details["web_results"],
        })

    print(f"[步骤2] 信息补充完成")
    return enriched
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 查询期刊影响因子和审稿周期
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=Nature+Energy+impact+factor+2025+review+time+acceptance+rate&num=5" \
  -H "accessKey: $AK"

# 查询投稿要求和费用
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=Nature+Energy+submission+guidelines+author+fees+open+access&num=5" \
  -H "accessKey: $AK"
```

---

## 步骤 3: 综合排序与推荐

根据主题匹配度和用户偏好约束对候选期刊进行综合打分和排序。

### Python 示例

```python
def score_and_rank(enriched_journals, preferences):
    """
    综合打分与排序。

    打分规则（满分 100）：
    - 主题匹配度（40分）：基于同主题论文在该期刊的发表数量
    - 影响因子匹配（30分）：IF 在用户偏好范围内得满分
    - 审稿速度（15分）：用户偏好 fast 时，已知审稿快的期刊加分
    - OA 匹配（15分）：用户要求 OA 时，OA 期刊加分

    Args:
        enriched_journals: enrich_journal_candidates 返回的列表
        preferences: 用户偏好 dict

    Returns:
        排序后的推荐列表
    """
    if_min = preferences.get("if_min", 0)
    if_max = preferences.get("if_max", float("inf"))
    require_oa = preferences.get("open_access", False)
    review_speed = preferences.get("review_speed", "")
    exclude = set(j.lower() for j in preferences.get("exclude_journals", []))

    max_count = max(j["count"] for j in enriched_journals) if enriched_journals else 1

    scored = []
    for j in enriched_journals:
        journal_lower = j["journal"].lower()

        # 排除用户指定的期刊
        if journal_lower in exclude:
            continue

        # IF 范围过滤
        avg_if = j["avg_if"]
        if avg_if > 0 and (avg_if < if_min or avg_if > if_max):
            continue

        score = 0.0

        # 主题匹配度（40分）：发表数量越多，匹配度越高
        score += 40 * (j["count"] / max_count)

        # 影响因子匹配（30分）
        if avg_if > 0:
            if if_min <= avg_if <= if_max:
                score += 30
            elif avg_if > if_max:
                # 超过上限，按比例扣分
                score += max(0, 30 - (avg_if - if_max) * 5)
            else:
                # 低于下限，按比例扣分
                score += max(0, 30 - (if_min - avg_if) * 5)
        else:
            score += 15  # IF 未知，给中间分

        # 审稿速度（15分） — 基于 web 搜索结果中的关键词判断
        web_text = " ".join(
            r["snippet"].lower() for r in j.get("web_results", [])
        )
        if review_speed == "fast":
            fast_indicators = ["fast review", "rapid", "2 weeks", "3 weeks",
                               "1 month", "quick decision", "expedited"]
            if any(ind in web_text for ind in fast_indicators):
                score += 15
            else:
                score += 5
        else:
            score += 10  # 不关心速度，给中间分

        # OA 匹配（15分）
        oa_indicators = ["open access", "gold oa", "fully open", "cc-by"]
        is_oa = any(ind in web_text for ind in oa_indicators)
        if require_oa:
            if is_oa:
                score += 15
            else:
                score += 0  # 要求 OA 但不是 OA
        else:
            score += 10  # 不关心 OA，给中间分

        scored.append({
            **j,
            "score": round(score, 1),
            "is_oa_likely": is_oa,
        })

    # 按得分降序排列
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
```

---

## 完整编排脚本

以下 Python 脚本实现端到端的期刊匹配推荐流程。

```python
#!/usr/bin/env python3
"""
期刊匹配推荐 (Journal Matcher)

根据论文摘要和关键词，分析同主题论文的发表去向，
结合用户偏好，推荐 5-10 个适合投稿的期刊。

用法:
    export ACCESS_KEY="your_access_key"
    python journal_matcher.py

可修改下方 CONFIG 区域的参数。
"""

import os
import sys
import json
import requests

# ============================================================
# 配置
# ============================================================

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误: 请设置环境变量 ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET  = {"accessKey": AK}

# -- 用户可修改区域 --
CONFIG = {
    # 论文信息
    "abstract": (
        "We present a novel graph neural network architecture for predicting "
        "molecular properties with chemical accuracy. By incorporating 3D "
        "geometric information and multi-scale attention mechanisms, our model "
        "achieves state-of-the-art performance on QM9 and OC20 benchmarks. "
        "The proposed method reduces prediction error by 15% compared to "
        "existing approaches while maintaining computational efficiency."
    ),
    "keywords": [
        "graph neural network",
        "molecular property prediction",
        "geometric deep learning",
        "quantum chemistry",
        "machine learning potential",
    ],

    # 偏好约束
    "if_min": 5.0,           # 最低 IF
    "if_max": 30.0,          # 最高 IF（避开 Nature/Science 等顶刊）
    "open_access": False,    # 是否仅推荐 OA 期刊
    "review_speed": "",      # "fast" / "normal" / "" 不限
    "jcr_zones": ["Q1"],     # JCR 分区筛选
    "exclude_journals": [],  # 排除的期刊
    "top_n": 10,             # 推荐数量
}


# ============================================================
# 步骤 1: 同主题论文检索与期刊分布分析
# ============================================================

def step1_analyze_publication_landscape(config):
    """检索同主题论文，分析期刊发表分布。"""
    print(f"\n{'='*60}")
    print(f"步骤 1: 同主题论文检索与期刊分布分析")
    print(f"  关键词: {config['keywords']}")
    print(f"  JCR 分区: {config['jcr_zones'] or '不限'}")
    print(f"{'='*60}\n")

    # 1a. 检索同主题论文
    payload = {
        "words": config["keywords"],
        "question": config["abstract"][:500],
        "type": 5,
        "startTime": "",
        "endTime": "",
        "jcrZones": config["jcr_zones"],
        "pageSize": 50,
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
    print(f"检索到 {len(papers)} 篇同主题论文\n")

    # 1b. 统计期刊分布
    journal_stats = {}
    for p in papers:
        journal = p.get("publicationEnName", "").strip()
        if not journal:
            continue

        if journal not in journal_stats:
            journal_stats[journal] = {
                "journal": journal,
                "count": 0,
                "if_values": [],
                "sample_dois": [],
                "sample_titles": [],
            }

        stats = journal_stats[journal]
        stats["count"] += 1

        impact_factor = p.get("impactFactor", 0)
        if impact_factor and impact_factor > 0:
            stats["if_values"].append(impact_factor)

        if len(stats["sample_dois"]) < 3:
            stats["sample_dois"].append(p.get("doi", ""))
            stats["sample_titles"].append(p.get("enName", ""))

    result = []
    for stats in journal_stats.values():
        if_values = stats["if_values"]
        result.append({
            "journal": stats["journal"],
            "count": stats["count"],
            "avg_if": round(sum(if_values) / len(if_values), 2) if if_values else 0,
            "max_if": round(max(if_values), 2) if if_values else 0,
            "sample_dois": stats["sample_dois"],
            "sample_titles": stats["sample_titles"],
        })

    result.sort(key=lambda x: x["count"], reverse=True)

    print(f"识别出 {len(result)} 个候选期刊:")
    for i, j in enumerate(result[:15]):
        print(f"  {i+1:2d}. {j['journal']}")
        print(f"      论文数: {j['count']}, 平均IF: {j['avg_if']}, 最高IF: {j['max_if']}")

    return result


# ============================================================
# 步骤 2: 期刊信息补充
# ============================================================

def step2_enrich_journal_info(journal_stats, top_n=10):
    """通过 web-search 补充候选期刊的详细信息。"""
    candidates = journal_stats[:top_n]

    print(f"\n{'='*60}")
    print(f"步骤 2: 期刊信息补充（{len(candidates)} 个候选期刊）")
    print(f"{'='*60}\n")

    enriched = []
    for j in candidates:
        journal_name = j["journal"]
        print(f"  查询: {journal_name}")

        web_results = []
        queries = [
            f"{journal_name} impact factor 2025 review time acceptance rate",
            f"{journal_name} submission guidelines open access APC fees",
        ]

        for q in queries:
            try:
                r = requests.get(
                    f"{BASE}/v1/search/web",
                    headers=HEADERS_GET,
                    params={"q": q, "num": 5}
                )
                r.raise_for_status()
                data = r.json()
                for hit in data.get("organic_results", []):
                    web_results.append({
                        "title": hit.get("title", ""),
                        "link": hit.get("link", ""),
                        "snippet": hit.get("snippet", ""),
                    })
            except Exception as e:
                print(f"    [警告] 搜索失败: {e}")

        enriched.append({**j, "web_results": web_results})
        print(f"    获取到 {len(web_results)} 条参考信息")

    return enriched


# ============================================================
# 步骤 3: 综合评分与推荐
# ============================================================

def step3_score_and_recommend(enriched_journals, config):
    """综合打分、过滤和排序，生成推荐列表。"""
    print(f"\n{'='*60}")
    print(f"步骤 3: 综合评分与推荐")
    print(f"  IF 范围: {config['if_min']} ~ {config['if_max']}")
    print(f"  要求 OA: {'是' if config['open_access'] else '否'}")
    print(f"  审稿速度偏好: {config['review_speed'] or '不限'}")
    print(f"  排除期刊: {config['exclude_journals'] or '无'}")
    print(f"{'='*60}\n")

    if_min = config.get("if_min", 0)
    if_max = config.get("if_max", float("inf"))
    require_oa = config.get("open_access", False)
    review_speed = config.get("review_speed", "")
    exclude = set(j.lower() for j in config.get("exclude_journals", []))

    max_count = max(j["count"] for j in enriched_journals) if enriched_journals else 1

    scored = []
    for j in enriched_journals:
        journal_lower = j["journal"].lower()

        # 排除用户指定的期刊
        if journal_lower in exclude:
            print(f"  [排除] {j['journal']}")
            continue

        # IF 范围过滤（硬过滤）
        avg_if = j["avg_if"]
        if avg_if > 0 and (avg_if < if_min or avg_if > if_max):
            print(f"  [IF不符] {j['journal']} (IF={avg_if})")
            continue

        score = 0.0

        # 主题匹配度（40分）
        score += 40 * (j["count"] / max_count)

        # 影响因子匹配（30分）
        if avg_if > 0:
            if if_min <= avg_if <= if_max:
                score += 30
        else:
            score += 15

        # 审稿速度（15分）
        web_text = " ".join(
            r["snippet"].lower() for r in j.get("web_results", [])
        )
        if review_speed == "fast":
            fast_indicators = ["fast review", "rapid", "2 weeks", "3 weeks",
                               "1 month", "quick decision", "expedited"]
            if any(ind in web_text for ind in fast_indicators):
                score += 15
            else:
                score += 5
        else:
            score += 10

        # OA 匹配（15分）
        oa_indicators = ["open access", "gold oa", "fully open", "cc-by"]
        is_oa = any(ind in web_text for ind in oa_indicators)
        if require_oa:
            if is_oa:
                score += 15
            else:
                score += 0
        else:
            score += 10

        scored.append({
            **j,
            "score": round(score, 1),
            "is_oa_likely": is_oa,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:config.get("top_n", 10)]


# ============================================================
# 报告生成
# ============================================================

def generate_report(recommendations, config):
    """生成结构化推荐报告。"""
    lines = []
    lines.append("# 期刊匹配推荐报告\n")
    lines.append(f"> 关键词: {', '.join(config['keywords'])}")
    lines.append(f"> IF 范围: {config['if_min']} ~ {config['if_max']}")
    lines.append(f"> JCR 分区: {config['jcr_zones'] or '不限'}")
    lines.append(f"> 要求 OA: {'是' if config['open_access'] else '否'}")
    lines.append(f"> 审稿速度: {config['review_speed'] or '不限'}\n")

    lines.append("## 推荐期刊列表\n")

    for i, j in enumerate(recommendations, 1):
        lines.append(f"### {i}. {j['journal']}\n")
        lines.append(f"| 指标 | 信息 |")
        lines.append(f"|------|------|")
        lines.append(f"| **综合评分** | {j['score']}/100 |")
        lines.append(f"| **平均 IF** | {j['avg_if']} |")
        lines.append(f"| **同主题论文数** | {j['count']} 篇 |")
        lines.append(f"| **OA 期刊** | {'可能是' if j.get('is_oa_likely') else '可能不是（请核实）'} |")

        # 匹配理由
        lines.append(f"\n**匹配理由**: 在检索到的同主题论文中，该期刊收录了 "
                     f"{j['count']} 篇相关论文，平均影响因子 {j['avg_if']}，"
                     f"表明该期刊对本研究方向有持续关注和发表历史。")

        # 代表性论文
        if j["sample_titles"]:
            lines.append(f"\n**同主题代表论文**:")
            for title, doi in zip(j["sample_titles"], j["sample_dois"]):
                lines.append(f"- {title} (DOI: {doi})")

        # Web 搜索摘要
        if j.get("web_results"):
            lines.append(f"\n**参考信息（来自 web 搜索）**:")
            for wr in j["web_results"][:3]:
                snippet = wr["snippet"][:200] if wr["snippet"] else ""
                if snippet:
                    lines.append(f"- {snippet}")

        lines.append("")

    # 投稿建议
    lines.append("## 投稿策略建议\n")
    if len(recommendations) >= 3:
        lines.append(f"1. **首选**: {recommendations[0]['journal']} "
                     f"（综合评分 {recommendations[0]['score']}，匹配度最高）")
        lines.append(f"2. **备选**: {recommendations[1]['journal']} "
                     f"（综合评分 {recommendations[1]['score']}）")
        lines.append(f"3. **保底**: {recommendations[2]['journal']} "
                     f"（综合评分 {recommendations[2]['score']}）")
    elif recommendations:
        for i, j in enumerate(recommendations, 1):
            lines.append(f"{i}. {j['journal']} （综合评分 {j['score']}）")
    else:
        lines.append("未找到符合条件的推荐期刊，请尝试放宽约束条件。")

    lines.append("\n> 注意: 审稿周期和接收率为基于公开信息的粗略估计，"
                 "实际情况可能因稿件质量、审稿人分配等因素而异。"
                 "建议投稿前仔细阅读目标期刊的 Author Guidelines。")

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  期刊匹配推荐 (Journal Matcher)")
    print(f"  关键词: {', '.join(config['keywords'][:3])}...")
    print(f"{'#'*60}")

    # 步骤 1: 同主题论文检索与期刊分布分析
    journal_stats = step1_analyze_publication_landscape(config)
    if not journal_stats:
        print("未检索到相关论文，无法进行期刊推荐。")
        print("建议：扩大关键词范围或放宽 JCR 分区限制。")
        sys.exit(1)

    # 步骤 2: 期刊信息补充
    enriched = step2_enrich_journal_info(journal_stats, top_n=config["top_n"] + 5)

    # 步骤 3: 综合评分与推荐
    recommendations = step3_score_and_recommend(enriched, config)
    if not recommendations:
        print("\n没有期刊满足所有约束条件。")
        print("建议：降低最低 IF 要求、放宽 JCR 分区、或取消 OA 限制。")
        sys.exit(1)

    # 生成报告
    print(f"\n{'='*60}")
    print(f"  生成推荐报告...")
    print(f"{'='*60}\n")

    report = generate_report(recommendations, config)
    print(report)

    # 保存报告
    output_file = "journal_recommendations.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存到: {output_file}")

    # 保存原始数据
    data_file = "journal_recommendations_data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(recommendations, f, ensure_ascii=False, indent=2, default=str)
    print(f"原始数据已保存到: {data_file}")


if __name__ == "__main__":
    main()
```

---

## 分步 curl 示例

### 1. 检索同主题论文

```bash
AK="YOUR_ACCESS_KEY"

# 检索同主题论文（50 篇，用于分析期刊分布）
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["perovskite", "solar cell", "efficiency", "stability"],
    "question": "Novel passivation strategy for perovskite solar cells achieving over 25% efficiency with improved stability",
    "type": 5,
    "jcrZones": ["Q1"],
    "pageSize": 50
  }' | python3 -c "
import sys, json
data = json.loads(sys.stdin.read().strip().split('\n')[0])
journals = {}
for p in data['data']:
    j = p.get('publicationEnName', '')
    if j:
        journals.setdefault(j, []).append(p.get('impactFactor', 0))
print('期刊分布:')
for j, ifs in sorted(journals.items(), key=lambda x: -len(x[1]))[:10]:
    avg_if = sum(i for i in ifs if i) / max(len([i for i in ifs if i]), 1)
    print(f'  {j}: {len(ifs)} 篇, 平均IF={avg_if:.1f}')
"
```

### 2. 查询期刊详情

```bash
AK="YOUR_ACCESS_KEY"

# 查询候选期刊的审稿周期和接收率
curl -s "https://open.bohrium.com/openapi/v1/search/web" \
  -G \
  --data-urlencode "q=Advanced Energy Materials impact factor 2025 review time acceptance rate" \
  --data-urlencode "num=5" \
  -H "accessKey: $AK" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for hit in data.get('organic_results', []):
    print(f\"  {hit['title']}\")
    print(f\"  {hit.get('snippet', '')[:200]}\")
    print()
"

# 查询投稿要求
curl -s "https://open.bohrium.com/openapi/v1/search/web" \
  -G \
  --data-urlencode "q=Advanced Energy Materials submission guidelines open access APC" \
  --data-urlencode "num=5" \
  -H "accessKey: $AK"
```

---

## 使用技巧

### 关键词选择

```python
# 推荐：与论文核心方法和应用领域紧密相关的 3-8 个英文术语
keywords = ["graph neural network", "molecular property prediction",
            "geometric deep learning", "quantum chemistry"]

# 不推荐：太宽泛
keywords = ["machine learning", "chemistry"]
# 不推荐：太窄（可能检索不到足够的同主题论文）
keywords = ["equivariant spherical harmonics message passing for QM9"]
```

### 约束组合策略

```python
# 冲击高区（IF 10+，Q1）
config = {"if_min": 10, "if_max": 50, "jcr_zones": ["Q1"]}

# 稳妥投稿（IF 3-10，Q1+Q2，审稿快）
config = {"if_min": 3, "if_max": 10, "jcr_zones": ["Q1", "Q2"],
          "review_speed": "fast"}

# OA 优先（任意 IF，仅 OA）
config = {"if_min": 0, "open_access": True, "jcr_zones": []}

# 避开被拒期刊
config = {"exclude_journals": ["Nature Chemistry", "JACS"]}
```

### 结果数量不足时的调整

如果推荐结果少于预期：
1. 放宽 IF 范围（降低 `if_min` 或提高 `if_max`）
2. 增加 JCR 分区（如从 `["Q1"]` 改为 `["Q1", "Q2"]`）
3. 取消 OA 限制
4. 增大 `pageSize`（从 50 提到 100），获取更多同主题论文样本

### 分段执行

对于网络不稳定的环境，可以将各步骤拆开执行，中间结果保存为 JSON：

```python
import json

# 步骤 1 结果保存
journal_stats = step1_analyze_publication_landscape(CONFIG)
with open("step1_journal_stats.json", "w") as f:
    json.dump(journal_stats, f, ensure_ascii=False)

# 后续步骤从文件加载
with open("step1_journal_stats.json") as f:
    journal_stats = json.load(f)
enriched = step2_enrich_journal_info(journal_stats)
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 检索结果为空 | 关键词太窄或 JCR 分区过于严格 | 扩大关键词范围，移除 JCR 分区筛选 |
| 期刊分布过于集中 | 检索量不足，样本太少 | 增大 `pageSize` 到 50-100 |
| 推荐列表为空 | IF 范围或 OA 约束过严 | 放宽 `if_min`/`if_max`，取消 OA 限制 |
| 审稿周期信息缺失 | web-search 未找到相关信息 | 手动查询目标期刊官网或 Journal Citation Reports |
| 响应含多行 JSON | paper-search 返回 streaming 格式 | 取第一行解析即可：`json.loads(r.text.split('\n')[0])` |
| 401 Unauthorized | accessKey 无效 | 确认 ACCESS_KEY 正确，检查 `~/.openclaw/openclaw.json` 配置 |
| web-search 无结果 | 期刊名称拼写有误或太冷门 | 核实期刊名称，尝试简化搜索词 |
| IF 数据不准确 | paper-search 中的 IF 可能滞后 | 以 web-search 或 Journal Citation Reports 的最新数据为准 |

---

## 搭配使用

- **journal-matcher** 选定期刊 → **pre-review** 按目标期刊要求预审论文
- **literature-review** 完成综述 → **journal-matcher** 选择综述论文的投稿期刊
- **paper-dissector** 分析竞品论文 → 观察其发表期刊，作为 **journal-matcher** 的参考
- **topic-scout** 确定研究方向 → 写完论文后用 **journal-matcher** 选期刊
