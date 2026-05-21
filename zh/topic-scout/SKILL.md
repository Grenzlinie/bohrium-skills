---
name: topic-scout
description: "Research topic discovery and recommendation by analyzing trends, active scholars, and knowledge gaps. Use when: user needs help choosing a research topic, finding innovation opportunities, or exploring emerging directions in a field. NOT for: specific paper search (use bohrium-paper-search), literature review on a known topic (use literature-review)."
---

# SKILL: 论文选题探测器 (Topic Scout)

## 概述

**论文选题探测器**是一个编排型技能，通过组合多个 Bohrium 原子技能，自动完成从趋势发现、学者追踪、知识空白检测到行业动态补充的全流程，最终为用户输出 3-5 个经过论证的研究选题推荐。

**编排流程：**

```
用户输入研究领域/方向
  │
  ├─ Step 1: paper-search  ─── 检索近 2-3 年高引论文，识别增长趋势
  ├─ Step 2: scholar-search ── 查找活跃学者，分析研究方向迁移
  ├─ Step 3: lkm            ── 分析变量关系图谱，发现弱连接/缺失连接（研究空白）
  └─ Step 4: web-search     ── 补充产业动态、政策方向、资助趋势
  │
  ▼
  输出：3-5 个推荐选题（含描述、价值分析、竞争评估、可行性判断、入门论文）
```

**适用场景：**

- 研究生选题探索
- 课题组开拓新方向
- 基金申请前的选题调研
- 跨学科创新机会发现

**不适用：**

- 特定论文检索 → 用 `bohrium-paper-search`
- 已知主题的文献综述 → 用 `literature-review`
- 单纯查找学者信息 → 用 `bohrium-scholar-search`

**无 CLI 支持** — 通过 Python 脚本编排多个 HTTP API 完成。

## 认证配置

本技能复用以下原子技能的认证，统一使用同一个 ACCESS_KEY：

```json
"topic-scout": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取，OpenClaw 会自动将 `env.ACCESS_KEY` 注入到运行环境。

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `field` | string | 是 | 研究领域/方向，如"锂电池固态电解质"、"蛋白质结构预测" |
| `preference` | string | 否 | 偏好约束：`theory`（理论）/ `experiment`（实验）/ `computation`（计算），默认不限 |
| `exclude_areas` | list[str] | 否 | 需要排除的子方向，如 `["polymer electrolyte", "liquid electrolyte"]` |

## 输出格式

每个推荐选题包含以下信息：

| 字段 | 说明 |
|------|------|
| 选题描述 | 一句话概括研究问题 |
| 值得做的原因 | 基于空白/趋势/影响力的论证 |
| 竞争评估 | 活跃团队数量和分布 |
| 可行性判断 | 数据、方法、资源的可获得性 |
| 入门论文 | 2-3 篇推荐阅读的论文（含 DOI） |

---

## 数据质量控制（关键步骤）

API 返回的论文列表可能包含大量与用户研究领域不相关的结果（关键词语义泛化导致），**必须在生成选题推荐前进行相关性过滤**。

### 过滤规则

```python
def filter_relevant_papers(papers, field_keywords, min_hits=2):
    """
    只保留标题+摘要中至少命中 min_hits 个领域核心术语的论文。

    field_keywords: 用户研究领域的核心术语（不是搜索关键词，而是判断相关性的术语）
    例如用户研究 "solid-state electrolyte for lithium battery"
    field_keywords = ["solid", "electrolyte", "lithium", "ionic", "garnet", "sulfide"]
    """
    filtered = []
    for p in papers:
        text = (p.get("enName", "") + " " + p.get("enAbstract", "")).lower()
        hits = sum(1 for k in field_keywords if k.lower() in text)
        if hits >= min_hits:
            filtered.append(p)
    return filtered
```

### 过滤后检查

- 如果过滤后 <5 篇：放宽 `min_hits=1` 或扩展领域关键词
- 如果过滤后仍有大量不相关结果：在推荐中明确说明「检索精度有限，以下结果经过领域关键词过滤」
- **永远不要**基于不相关论文生成选题推荐（如搜固态电解质却基于"MoS2阴极"论文推荐选题）

---

## 报告分析深度要求

**选题推荐不是 API 数据的格式化转储**。你是一个专业选题顾问，必须在推荐中提供：

1. **研究空白量化**：具体指出哪些变量关系缺乏研究、缺乏多少（LKM 匹配条数 < N）
2. **竞争分析**：有多少个活跃团队/机构在该方向工作，是蓝海还是红海
3. **可行性评估**：数据可获得性、计算资源需求、实验条件要求的具体判断
4. **基于数据的趋势判断**：从发表数量年度变化、引用增速推断方向热度

### 禁止的行为

- 仅列出论文标题而不分析其与选题的关系
- 用模糊表述代替具体数据（如"该方向竞争适中"而不说明具体团队数量）
- 推荐明显超出用户能力范围的选题而不标注风险
- 基于标题猜测论文内容（如果没有摘要，不要总结该论文的研究方向）

### 推荐的做法

- 引用具体竞争数据："该方向目前有约 8 个活跃团队（MIT、Stanford 等），年发文 20+ 篇"
- 量化研究空白："LKM 论断匹配仅返回 2 条弱相关结果（score < 0.3），表明该假说尚未被系统研究"
- 评估可行性："该方向需要 DFT 计算资源，适合有 HPC 集群的课题组"
- 明确标注数据来源不足："部分趋势判断基于有限的检索结果，建议进一步验证"

---

## 完整编排脚本

以下脚本实现了从输入到输出的完整选题探测流程。

```python
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from collections import Counter

# ─── 配置 ───────────────────────────────────────────────

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("ERROR: ACCESS_KEY 未配置。")
    print("请在 ~/.openclaw/openclaw.json 中配置 topic-scout.env.ACCESS_KEY")
    sys.exit(1)

HEADERS = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET = {"accessKey": AK}

BASE_PAPER  = "https://open.bohrium.com/openapi/v1/paper"
BASE_SCHOLAR = "https://open.bohrium.com/openapi/v1/paper-server"
BASE_LKM    = "https://open.bohrium.com/openapi/v1/lkm"
BASE_WEB    = "https://open.bohrium.com/openapi/v1/search/web"

# ─── 输入参数 ────────────────────────────────────────────

FIELD = "solid-state electrolyte for lithium batteries"  # 修改为你的研究领域
PREFERENCE = ""          # theory / experiment / computation / 留空不限
EXCLUDE_AREAS = []       # 排除的子方向

# ─── 辅助函数 ────────────────────────────────────────────

def safe_request(method, url, **kwargs):
    """带错误处理的请求封装"""
    try:
        r = requests.request(method, url, timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        print(f"  [WARN] 请求超时: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"  [WARN] HTTP 错误 {e.response.status_code}: {url}")
        if e.response.status_code == 401:
            print("  [ERROR] ACCESS_KEY 无效，请检查配置")
        return None
    except Exception as e:
        print(f"  [WARN] 请求异常: {e}")
        return None

def build_keywords(field, exclude_areas=None):
    """从研究领域描述生成搜索关键词列表。

    技巧：
    - 将领域描述拆分为 3-8 个专业术语
    - 加入方法学关键词（如 machine learning, first-principles）以捕获交叉趋势
    - 排除不需要的子方向
    """
    # 基础关键词：直接从领域描述拆分
    words = [w.strip() for w in field.replace(",", " ").split() if len(w.strip()) > 2]

    # 去重并限制数量
    seen = set()
    unique_words = []
    for w in words:
        wl = w.lower()
        if wl not in seen:
            seen.add(wl)
            unique_words.append(w)
    return unique_words[:8]


# ═══════════════════════════════════════════════════════════
# Step 1: 论文趋势分析 (paper-search)
# ═══════════════════════════════════════════════════════════

print("=" * 60)
print("Step 1: 检索近 2-3 年高引论文，识别增长趋势")
print("=" * 60)

now = datetime.now()
start_date = (now - timedelta(days=3*365)).strftime("%Y-%m-%d")
end_date = now.strftime("%Y-%m-%d")

keywords = build_keywords(FIELD, EXCLUDE_AREAS)
print(f"  关键词: {keywords}")
print(f"  时间范围: {start_date} ~ {end_date}")

paper_data = safe_request("POST", f"{BASE_PAPER}/rag/pass/keyword",
    headers=HEADERS,
    json={
        "words": keywords,
        "question": f"Recent advances and emerging trends in {FIELD}",
        "type": 5,
        "startTime": start_date,
        "endTime": end_date,
        "jcrZones": ["Q1", "Q2"],
        "pageSize": 20
    }
)

papers = []
trend_keywords = Counter()
top_journals = Counter()

if paper_data and paper_data.get("code") == 0:
    papers = paper_data.get("data", [])
    print(f"  检索到 {len(papers)} 篇论文")

    for p in papers:
        # 统计高频关键词（从标题和摘要提取）
        title = (p.get("enName") or "").lower()
        abstract = (p.get("enAbstract") or "").lower()
        for kw in keywords:
            if kw.lower() in title or kw.lower() in abstract:
                trend_keywords[kw] += 1

        # 统计期刊分布
        journal = p.get("publicationEnName", "Unknown")
        if journal:
            top_journals[journal] += 1

    print(f"  高频主题词: {trend_keywords.most_common(5)}")
    print(f"  Top 期刊: {top_journals.most_common(3)}")

    # 按引用排序，取 Top 5 作为标杆论文
    papers_sorted = sorted(papers, key=lambda x: x.get("citationNums", 0), reverse=True)
    print("\n  Top 5 高引论文:")
    for i, p in enumerate(papers_sorted[:5], 1):
        print(f"    [{i}] {p.get('enName', 'N/A')[:80]}")
        print(f"        DOI: {p.get('doi', 'N/A')}, 引用: {p.get('citationNums', 0)}, "
              f"IF: {p.get('impactFactor', 0)}")
else:
    print("  [WARN] 论文检索未返回有效数据，继续后续步骤")


# ═══════════════════════════════════════════════════════════
# Step 2: 活跃学者分析 (scholar-search)
# ═══════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("Step 2: 查找活跃学者，分析研究方向迁移")
print("=" * 60)

# 从高引论文的作者中提取候选学者
candidate_authors = []
if papers:
    for p in papers_sorted[:10]:
        authors = p.get("authors", [])
        if isinstance(authors, list):
            for a in authors[:2]:  # 取前两位作者（通常是通讯/一作）
                name = a if isinstance(a, str) else a.get("name", "")
                if name and name not in candidate_authors:
                    candidate_authors.append(name)

# 也可以直接按领域搜索
scholar_results = []
search_names = candidate_authors[:5] if candidate_authors else [FIELD.split()[0]]

for name in search_names:
    print(f"  搜索学者: {name}")
    data = safe_request("POST", f"{BASE_SCHOLAR}/scholar/search",
        headers=HEADERS,
        json={
            "name": name,
            "tags": FIELD,
            "page": 1,
            "pageSize": 5
        }
    )
    if data and data.get("data", {}).get("items"):
        for item in data["data"]["items"][:2]:
            scholar_results.append(item)
            print(f"    [{item.get('scholarId', '')}] {item.get('nameEn', '')} "
                  f"({item.get('scholarOrgNameEn', '')})")
            print(f"      论文: {item.get('paperNums', 0)}, "
                  f"引用: {item.get('citationNums', 0)}, "
                  f"h-index: {item.get('hIndex', 0)}")

# 对 Top 学者拉取详情，分析研究方向
scholar_profiles = []
for scholar in scholar_results[:5]:
    sid = scholar.get("scholarId")
    if not sid:
        continue
    info = safe_request("GET", f"{BASE_SCHOLAR}/scholar/info",
        headers=HEADERS_GET,
        params={"scholarId": sid}
    )
    if info and info.get("data"):
        profile = info["data"]
        scholar_profiles.append(profile)
        directions = profile.get("researchDirection", [])
        print(f"\n  学者画像: {profile.get('nameEn', '')}")
        print(f"    研究方向: {directions}")

# 统计研究方向分布，识别方向迁移信号
direction_counter = Counter()
for prof in scholar_profiles:
    for d in prof.get("researchDirection", []):
        direction_counter[d] += 1

if direction_counter:
    print(f"\n  学者研究方向热点: {direction_counter.most_common(5)}")

active_teams_count = len(set(
    s.get("scholarOrgNameEn", "Unknown") for s in scholar_results
))
print(f"  活跃机构数: {active_teams_count}")


# ═══════════════════════════════════════════════════════════
# Step 3: 知识空白检测 (LKM)
# ═══════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("Step 3: 分析知识图谱，发现研究空白")
print("=" * 60)

# Step 3a: 知识图谱搜索 — 获取已知变量关系
print("  3a. 知识图谱搜索...")
kg_data = safe_request("POST", f"{BASE_LKM}/search",
    headers=HEADERS,
    json={
        "query": f"key variables and relationships in {FIELD}",
        "limit": 10
    }
)

if kg_data:
    print(f"  知识图谱返回数据: {json.dumps(kg_data, ensure_ascii=False)[:200]}...")

# Step 3b: 论断匹配 — 检测哪些假说尚未被验证
# 从论文趋势中提取潜在论断进行检测
print("\n  3b. 论断匹配（研究空白检测）...")

# 构造待检测的论断：基于领域知识提出几个假说
test_claims = [
    f"Novel approaches in {FIELD} can significantly improve performance",
    f"Machine learning methods can accelerate discovery in {FIELD}",
    f"The combination of experimental and computational methods in {FIELD} leads to better understanding",
]

gaps = []  # 存储检测到的研究空白

for claim in test_claims:
    print(f"\n  检测论断: {claim[:60]}...")
    result = safe_request("POST", f"{BASE_LKM}/claims/match",
        headers=HEADERS,
        json={
            "text": claim,
            "limit": 5
        }
    )

    if result and result.get("data"):
        data = result["data"]
        new_claim = data.get("new_claim_likely", False)
        variables = data.get("variables", [])

        # ── 解读 new_claim_likely ──
        # True  → 知识图谱中没有充分的支持/反驳证据，说明：
        #         1) 这是一个尚未被充分研究的方向（研究空白）
        #         2) 或者表述太新颖，还没有形成共识
        #         → 选题信号：值得深入探索
        #
        # False → 已有较多证据支持或反驳
        #         → 如果是支持，说明方向已有基础但可能竞争激烈
        #         → 如果是反驳，需要重新审视假说

        if new_claim:
            gaps.append({
                "claim": claim,
                "signal": "NEW_CLAIM",
                "detail": "知识图谱中缺乏相关证据，可能是研究空白"
            })
            print(f"    *** new_claim_likely=True → 潜在研究空白! ***")
        else:
            match_count = len(variables)
            print(f"    new_claim_likely=False, 匹配到 {match_count} 条已有论断")
            # 即使不是新论断，如果匹配的变量关系较少（< 3），也可能有拓展空间
            if match_count < 3:
                gaps.append({
                    "claim": claim,
                    "signal": "WEAK_EVIDENCE",
                    "detail": f"仅匹配 {match_count} 条证据，该方向可能有拓展空间"
                })
                print(f"    证据较弱 → 可能有拓展空间")

        # 打印匹配到的已有论断（用于分析竞争）
        for v in variables[:3]:
            print(f"      - [{v.get('role', '')}] {v.get('content', '')[:80]}...")

print(f"\n  检测到 {len(gaps)} 个潜在研究空白信号")
for g in gaps:
    print(f"    [{g['signal']}] {g['claim'][:60]}...")
    print(f"      → {g['detail']}")


# ═══════════════════════════════════════════════════════════
# Step 4: 产业与政策动态 (web-search)
# ═══════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("Step 4: 补充产业动态、政策方向、资助趋势")
print("=" * 60)

web_queries = [
    f"{FIELD} industry trends 2024 2025",
    f"{FIELD} funding grants research 2025",
    f"{FIELD} breakthrough news recent",
]

industry_insights = []

for q in web_queries:
    print(f"  搜索: {q[:50]}...")
    data = safe_request("GET", BASE_WEB,
        headers=HEADERS_GET,
        params={"q": q, "num": 5}
    )
    if data and data.get("organic_results"):
        for hit in data["organic_results"][:3]:
            insight = {
                "title": hit.get("title", ""),
                "link": hit.get("link", ""),
                "snippet": hit.get("snippet", ""),
                "query_type": q.split()[-2] if len(q.split()) > 2 else "general"
            }
            industry_insights.append(insight)
            print(f"    [{hit.get('title', 'N/A')[:50]}]")
            print(f"      {hit.get('snippet', '')[:100]}")

print(f"\n  收集到 {len(industry_insights)} 条产业/政策信息")


# ═══════════════════════════════════════════════════════════
# 综合分析与选题推荐
# ═══════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("综合分析：生成选题推荐")
print("=" * 60)

# ── 汇总所有信号 ──
print("\n信号汇总:")
print(f"  论文趋势关键词: {trend_keywords.most_common(5)}")
print(f"  学者方向热点: {direction_counter.most_common(5)}")
print(f"  研究空白信号: {len(gaps)} 个")
print(f"  产业动态: {len(industry_insights)} 条")
print(f"  活跃团队/机构: {active_teams_count} 个")

# ── 构建推荐数据 ──
# 注意：以下推荐逻辑是示例框架。实际使用时，
# 应由 LLM 根据上述汇总信号进行智能推理和推荐。

recommendations = []

# 基于研究空白生成推荐
for i, gap in enumerate(gaps[:3]):
    entry_papers = []
    if papers_sorted:
        for p in papers_sorted[:3]:
            entry_papers.append({
                "title": p.get("enName", "N/A"),
                "doi": p.get("doi", "N/A"),
                "citations": p.get("citationNums", 0)
            })

    rec = {
        "topic": f"基于{gap['signal']}信号的选题方向 {i+1}",
        "description": gap["claim"],
        "why_worth": gap["detail"],
        "competition": f"目前约 {active_teams_count} 个活跃机构在相关领域",
        "feasibility": "待根据具体方向评估数据/方法/资源可获得性",
        "entry_papers": entry_papers
    }
    recommendations.append(rec)

# ── 输出推荐 ──
print("\n" + "=" * 60)
print(f"推荐选题（共 {len(recommendations)} 个）")
print("=" * 60)

for i, rec in enumerate(recommendations, 1):
    print(f"\n{'─' * 50}")
    print(f"选题 {i}: {rec['topic']}")
    print(f"{'─' * 50}")
    print(f"  描述: {rec['description']}")
    print(f"  值得做的原因: {rec['why_worth']}")
    print(f"  竞争评估: {rec['competition']}")
    print(f"  可行性判断: {rec['feasibility']}")
    print(f"  入门论文:")
    for j, ep in enumerate(rec["entry_papers"], 1):
        print(f"    [{j}] {ep['title'][:70]}")
        print(f"        DOI: {ep['doi']}, 引用: {ep['citations']}")

print("\n" + "=" * 60)
print("选题探测完成。以上结果基于 Bohrium 平台数据，建议结合导师意见进一步筛选。")
print("=" * 60)
```

---

## 分步说明

### Step 1: 论文趋势分析 (paper-search)

**目标：** 获取近 2-3 年的高引论文，识别研究增长点。

**API 调用：**

```python
POST https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword
Header: accessKey: $ACCESS_KEY, Content-Type: application/json
Body: {
    "words": ["solid-state", "electrolyte", "lithium", "battery"],
    "question": "Recent advances and emerging trends in solid-state electrolyte for lithium batteries",
    "type": 5,
    "startTime": "2023-05-01",
    "endTime": "2026-05-13",
    "jcrZones": ["Q1", "Q2"],
    "pageSize": 20
}
```

**关键返回字段：**

| 字段 | 用途 |
|------|------|
| `enName` | 论文标题，用于提取主题词 |
| `enAbstract` | 摘要，用于深入分析趋势 |
| `citationNums` | 引用数，用于判断影响力 |
| `coverDateStart` | 发表时间，用于绘制趋势曲线 |
| `impactFactor` | 期刊影响因子，用于质量过滤 |
| `authors` | 作者列表，用于衔接 Step 2 |

**关键词选择技巧：**

```python
# 趋势发现的关键词策略不同于普通文献检索：

# 1. 核心领域词（2-3 个）— 锚定研究范围
core = ["solid-state electrolyte", "lithium battery"]

# 2. 方法学交叉词（1-2 个）— 捕获跨学科趋势
method = ["machine learning", "first-principles"]

# 3. 属性/性能词（1-2 个）— 定位具体突破点
property = ["ionic conductivity", "interfacial stability"]

# 组合策略：core + method 发现交叉创新
#           core + property 发现性能突破
words = core + method  # 或 core + property
```

### Step 2: 活跃学者分析 (scholar-search)

**目标：** 找到领域内活跃的研究者，分析他们的方向迁移（方向迁移往往预示着新机会）。

**API 调用：**

```python
# 搜索学者
POST https://open.bohrium.com/openapi/v1/paper-server/scholar/search
Body: {"name": "学者姓名", "tags": "solid-state electrolyte", "page": 1, "pageSize": 10}

# 获取学者详情
GET https://open.bohrium.com/openapi/v1/paper-server/scholar/info?scholarId=xxx
```

**分析要点：**

- 从 Step 1 高引论文的作者中提取候选学者
- 比较学者的 `researchDirection` 与论文主题，判断是否有方向迁移
- 统计不同机构的覆盖度，评估竞争激烈程度
- 高 h-index + 方向迁移 = 强信号（大牛也在转向的方向更有前景）

### Step 3: 知识空白检测 (LKM)

**目标：** 利用大知识模型的知识图谱，发现尚未被充分研究的连接关系。

**API 调用：**

```python
# 知识图谱搜索
POST https://open.bohrium.com/openapi/v1/lkm/search
Body: {"query": "key variables and relationships in solid-state electrolyte", "limit": 10}

# 论断匹配（核心！）
POST https://open.bohrium.com/openapi/v1/lkm/claims/match
Body: {"text": "一个待验证的科学假说", "limit": 5}
```

**`new_claim_likely` 解读——选题的黄金信号：**

| `new_claim_likely` 值 | 含义 | 选题信号 |
|---|---|---|
| `true` | 知识图谱中缺乏支持/反驳该论断的证据 | **研究空白**——该方向可能尚未被充分探索，是高价值选题候选 |
| `false` + 少量 variables | 有少量相关证据但不充分 | **拓展空间**——方向已有基础但仍有创新余地 |
| `false` + 大量 variables | 已有充分证据 | **成熟方向**——竞争激烈，需要更精细的切入角度 |

**构造有效的检测论断：**

```python
# GOOD: 包含明确的变量和关系
"Doping Li7La3Zr2O12 with Ta improves ionic conductivity above 1 mS/cm at room temperature"

# GOOD: 提出跨学科假说
"Machine learning potentials can replace DFT for screening solid electrolyte candidates"

# BAD: 太笼统，无法有效检测
"Solid-state batteries are better"
```

### Step 4: 产业与政策动态 (web-search)

**目标：** 补充学术之外的信号——产业需求、政策风向、资助热点。

**API 调用：**

```python
GET https://open.bohrium.com/openapi/v1/search/web?q=QUERY&num=5
Header: accessKey: $ACCESS_KEY
```

**推荐搜索策略：**

```python
queries = [
    f"{FIELD} industry trends 2024 2025",       # 产业趋势
    f"{FIELD} funding grants research 2025",     # 资助信号
    f"{FIELD} breakthrough news recent",         # 最新突破
    f"{FIELD} challenges bottleneck",            # 瓶颈问题（=选题机会）
]
```

---

## curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# Step 1: 论文趋势
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{
    "words": ["solid-state", "electrolyte", "lithium"],
    "question": "emerging trends in solid-state electrolyte research",
    "type": 5,
    "startTime": "2023-01-01",
    "endTime": "2026-05-13",
    "jcrZones": ["Q1", "Q2"],
    "pageSize": 10
  }' | python3 -m json.tool

# Step 2: 学者搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper-server/scholar/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"name": "Janek", "tags": "solid-state electrolyte", "page": 1, "pageSize": 5}'

# Step 2b: 学者详情
curl -s "https://open.bohrium.com/openapi/v1/paper-server/scholar/info?scholarId=SCHOLAR_ID" \
  -H "accessKey: $AK"

# Step 3a: 知识图谱搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"query": "solid-state electrolyte ionic conductivity factors", "limit": 10}'

# Step 3b: 论断匹配（检测空白）
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/claims/match" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"text": "Sulfide-based solid electrolytes can achieve ionic conductivity comparable to liquid electrolytes at room temperature", "limit": 5}'

# Step 4: 产业动态
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=solid-state+battery+industry+trends+2025&num=5" \
  -H "accessKey: $AK"
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 论文检索结果太少 | 关键词太专业或时间范围太窄 | 放宽关键词（去掉限定词），将时间范围扩展到 3-5 年 |
| 论文检索结果不相关 | `words` 和 `question` 不匹配 | 确保 `words` 是 `question` 中的核心术语子集 |
| 学者搜索无结果 | 姓名拼写错误或该学者未被收录 | 尝试不同拼写，或跳过该学者 |
| `new_claim_likely` 总是 `false` | 论断太宽泛或领域研究已很成熟 | 构造更具体的论断，包含明确变量和关系 |
| `new_claim_likely` 总是 `true` | 论断表述太新颖或太具体 | 适当泛化论断，使用领域通用术语 |
| web-search 无结果 | 关键词太专业 | 用更通俗的表述，英文通常比中文命中率高 |
| 401 错误 | ACCESS_KEY 无效 | 检查 `~/.openclaw/openclaw.json` 中的配置 |
| 某一步超时 | 后端负载高 | 脚本已内置超时处理，该步骤会被跳过，不影响后续流程 |

---

## 使用建议

1. **关键词迭代**：第一轮用宽泛关键词探索全局；根据 Step 1 结果中出现的高频术语，替换关键词做第二轮精准探测。

2. **论断设计**：Step 3 的论断匹配质量直接决定空白检测效果。建议从 Step 1 的高引论文中提取核心结论，然后修改变量或条件构造新论断。

3. **交叉验证**：如果某个方向在 Step 1（论文增长）、Step 2（学者迁移）、Step 3（知识空白）三个维度都有信号，则是高置信度选题。

4. **排除已知方向**：使用 `exclude_areas` 参数过滤掉自己已经熟悉或不想做的方向，提高探测效率。

5. **偏好约束**：设置 `preference` 可以在生成推荐时优先考虑理论/实验/计算方向，避免推荐超出自身能力范围的选题。

## 搭配使用

- **topic-scout** 推荐选题 → **bohrium-paper-search** 深入检索入门论文全文
- **topic-scout** 发现空白 → **bohrium-lkm** 进一步分析证据链
- **topic-scout** 确定方向 → **bohrium-pdf-parser** 解析关键论文
- **topic-scout** 选定选题 → **bohrium-job** 提交初步计算验证
