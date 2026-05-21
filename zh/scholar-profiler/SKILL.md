---
name: scholar-profiler
description: "Comprehensive scholar profiling combining publication analysis, knowledge graph positioning, and web presence. Use when: user wants a complete profile of a researcher including their trajectory, collaboration network, and impact. NOT for: simple scholar search (use bohrium-scholar-search), paper search (use bohrium-paper-search)."
---

# SKILL: 学者画像 (Scholar Profiler)

## 概述

编排 `bohrium-scholar-search`、`bohrium-paper-search`、`bohrium-lkm`、`bohrium-web-search` 四个原子技能，对单个学者进行全方位画像分析。从基本信息查询、发文轨迹分析、知识图谱定位到网络资料补充，输出完整的学者画像报告。

**编排流程：**

```
学者姓名 + 机构（可选，消歧用）
        │
        ▼
┌─────────────────────┐
│  scholar-search      │  搜索学者 → 获取基础信息（h-index、引用、机构）
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  paper-search        │  检索发表记录 → 分析研究方向变迁
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  lkm search          │  知识图谱搜索 → 定位学者在知识网络中的位置
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  web-search          │  网络搜索 → 补充机构主页、新闻、学术社交媒体
└────────┬────────────┘
         │
         ▼
    学者画像报告
```

**适用场景：**

- 全面了解一位学者的学术背景、研究轨迹和影响力
- 评估潜在合作者的研究方向契合度
- 分析某学者的合作网络和核心合作者
- 审稿或引用前快速了解论文作者的背景
- 为学术交流或招聘提供决策依据

**不适用：**

- 仅需搜索学者基本信息 → `bohrium-scholar-search`
- 仅需检索论文 → `bohrium-paper-search`
- 跨多篇论文的文献综述 → `literature-review`
- 竞品技术监控 → `tech-radar`

## 认证配置

本技能复用底层四个原子技能共同的 ACCESS_KEY：

```json
"scholar-profiler": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.ACCESS_KEY` 注入到运行环境。

### 获取流程（运行时）

```
读取 os.environ["ACCESS_KEY"]
  ├─ 非空 → 直接使用
  └─ 为空 → 提示用户：
           「未在 OpenClaw 配置中检测到 ACCESS_KEY，请在 ~/.openclaw/openclaw.json
            的 scholar-profiler.env.ACCESS_KEY 中填入从 https://bohrium.dp.tech
            个人设置页获取的 AccessKey，然后重启 OpenClaw 会话。」
```

**重要：** 不要把 AccessKey 另存到其他文件或写死到代码，统一通过 OpenClaw 环境变量注入。

### 错误处理

若 API 返回 `Invalid AccessKey`（code 2000）或 HTTP 401：
1. 说明 OpenClaw 配置中的 Key 已失效或错误
2. 提示用户：「您的 AccessKey 已失效，请在 `~/.openclaw/openclaw.json` 中更新 `scholar-profiler.env.ACCESS_KEY` 并重启 OpenClaw 会话。」

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scholar_name` | string | 是 | 学者姓名（中英文均可） |
| `institution` | string | 否 | 所属机构（用于消歧，多个同名学者时推荐填写） |

## 输出结构

学者画像报告包含以下五部分：

1. **基础数据卡片** — h-index、总引用数、所属机构、联系方式
2. **研究轨迹** — 早期方向 → 当前方向 → 可能的新方向，附时间线
3. **合作网络描述** — 核心合作者、合作频次、机构分布
4. **Top-5 代表作** — 被引最高的 5 篇论文，附影响因子和期刊信息
5. **近期研究趋势判断** — 基于近 2 年发文分析，判断研究重心变化
6. **数据透明度声明** — 数据来源、时效性、置信度标注

---

## 报告质量控制

### 数据透明度要求

**所有指标必须标注数据来源和局限性**：
- ✅ "h-index: 89（来源：Bohrium scholar-search，可能与 Google Scholar 数据有差异）"
- ✅ "总引用数: 12,000+（基于 Bohrium 收录论文，实际值可能更高）"
- ❌ "h-index: 89"（无来源标注）
- ❌ "该学者在领域内排名前 5"（无量化依据）

**生成报告时必须在"基础数据卡片"底部注明**：
> 以上数据来源于 Bohrium 学术搜索数据库（检索日期：YYYY-MM-DD）。h-index 和引用数统计范围受数据库收录范围影响，可能与 Google Scholar 等其他来源存在差异。如需精确数据，建议交叉验证。

### 核心论文完整性检查

**报告中的"Top-5 代表作"必须经过自检**：
- 如果学者详情中有 `researchDirection`，检查 Top-5 是否覆盖了其主要方向（每个方向至少 1 篇）
- 如果 Top-5 全部来自同一子方向，需额外检索其他方向的代表作
- 对于知名学者（h-index > 50），如果 Top-5 最高被引 < 100，说明可能遗漏了核心工作——通过扩展关键词重新检索

### 产业化与社会影响分析

对于有显著产业化成果的学者（如创办公司、参与政策制定），报告**必须包含**：
1. **学术→产业链路**：论文→开源软件→商业化路径（如有）
2. **政策/组织影响**：在学术机构、政府咨询、标准制定中的角色
3. **注明信息来源**：产业化信息主要来自 web-search 结果，标注"基于公开网络信息"

### 禁止的行为

- ❌ 不标注数据来源地直接给出 h-index 或排名
- ❌ 遗漏学者的核心工作（如该学者最知名的论文未出现在报告中）
- ❌ 只报告数字而不做趋势判断（如"近 2 年发文 5 篇"而不分析这意味着活跃度上升还是下降）
- ❌ 合作网络只列姓名不分析合作模式（应区分长期合作者 vs 偶尔合作）

---

## 各接口说明

### 接口 1：学者搜索与详情 (`scholar-search`)

| 操作 | 方法 | 端点 |
|------|------|------|
| 学者搜索 | POST | `/openapi/v1/paper-server/scholar/search` |
| 学者详情 | GET | `/openapi/v1/paper-server/scholar/info?scholarId=xxx` |

**搜索请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 学者姓名关键词（1~99 字符） |
| `school` | string | 否 | 学校/机构 |
| `page` | int | 否 | 页码，默认 1 |
| `pageSize` | int | 否 | 每页条数，默认 5 |

**搜索返回关键字段（`data.items[]`）：**

| 字段 | 说明 |
|------|------|
| `scholarId` | 学者唯一 ID |
| `nameEn` / `nameZh` | 英文名 / 中文名 |
| `paperNums` | 发文量 |
| `citationNums` | 引用量 |
| `hIndex` | h-index |
| `scholarOrgNameEn` / `scholarOrgNameZh` | 所属机构 |
| `isHighCited` | 是否高被引学者 |

**详情返回额外字段：**

| 字段 | 说明 |
|------|------|
| `researchDirection` | 研究方向数组 |
| `educationBackground` / `educationBackgroundZh` | 教育经历 |
| `workExperience` / `workExperienceZh` | 工作经历 |

### 接口 2：论文检索 (`paper-search`)

| 操作 | 方法 | 端点 |
|------|------|------|
| 关键词检索 | POST | `/openapi/v1/paper/rag/pass/keyword` |

**请求参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `words` | string[] | 关键词列表（放入学者姓名 + 研究方向） |
| `question` | string | 自然语言检索问题 |
| `type` | int | 检索类型，固定为 `5`（全方位检索） |
| `pageSize` | int | 返回论文数量 |

**返回关键字段（`data[]`）：**

| 字段 | 说明 |
|------|------|
| `doi` | DOI |
| `enName` | 英文标题 |
| `enAbstract` | 英文摘要 |
| `authors` | 作者列表 |
| `coverDateStart` | 发表日期 |
| `publicationEnName` | 期刊名 |
| `impactFactor` | 影响因子 |
| `citationNums` | 被引次数 |

### 接口 3：知识图谱搜索 (`lkm`)

| 操作 | 方法 | 端点 |
|------|------|------|
| 知识图谱搜索 | POST | `/openapi/v1/lkm/search` |

**请求参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `query` | string | 搜索查询（学者的研究主题） |
| `limit` | int | 返回结果数量 |

### 接口 4：网络搜索 (`web-search`)

| 操作 | 方法 | 端点 |
|------|------|------|
| 网页搜索 | GET | `/openapi/v1/search/web?q=QUERY&num=N` |

**请求参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `q` | string | 搜索关键词 |
| `num` | int | 返回结果数（1-10） |

**返回关键字段（`organic_results[]`）：**

| 字段 | 说明 |
|------|------|
| `title` | 页面标题 |
| `link` | 页面 URL |
| `snippet` | 摘要片段 |

---

## 完整编排脚本

以下 Python 脚本实现端到端的学者画像流程。

```python
#!/usr/bin/env python3
"""
学者画像 (Scholar Profiler)
编排 scholar-search + paper-search + lkm + web-search，输出完整学者画像报告。

用法:
    export ACCESS_KEY="your_access_key"
    python scholar_profiler.py "Yann LeCun"
    python scholar_profiler.py "张三" "清华大学"
"""

import os
import sys
import json
import requests
from datetime import datetime
from collections import Counter, defaultdict

# ─── 配置 ───────────────────────────────────────────────

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误：未设置 ACCESS_KEY 环境变量。")
    print("请在 ~/.openclaw/openclaw.json 中配置 scholar-profiler.env.ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"

H_JSON = {"accessKey": AK, "Content-Type": "application/json"}
H_AK   = {"accessKey": AK}


# ─── 步骤 1：学者搜索与基础信息 ──────────────────────────

def search_scholar(name: str, institution: str = "") -> dict | None:
    """
    搜索学者并获取详细信息。
    返回学者基础数据字典，搜索失败则返回 None。
    """
    print(f"[步骤 1/4] 学者搜索：{name}")
    if institution:
        print(f"  消歧机构：{institution}")

    # 1a. 搜索学者
    payload = {
        "name": name,
        "page": 1,
        "pageSize": 5
    }
    if institution:
        payload["school"] = institution

    try:
        r = requests.post(
            f"{BASE}/v1/paper-server/scholar/search",
            headers=H_JSON,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  搜索失败：{e}")
        return None

    items = data.get("data", {}).get("items", [])
    if not items:
        print("  未找到匹配的学者。")
        return None

    # 选择最匹配的学者（优先匹配机构）
    scholar = items[0]
    if institution and len(items) > 1:
        for item in items:
            org = (item.get("scholarOrgNameEn", "") +
                   item.get("scholarOrgNameZh", "")).lower()
            if institution.lower() in org:
                scholar = item
                break

    scholar_id = scholar["scholarId"]
    print(f"  匹配学者：{scholar.get('nameEn', '')} / {scholar.get('nameZh', '')}")
    print(f"  机构：{scholar.get('scholarOrgNameEn', '') or scholar.get('scholarOrgNameZh', '')}")
    print(f"  scholarId：{scholar_id}")

    # 1b. 获取学者详情
    print(f"  获取详细信息...")
    try:
        r = requests.get(
            f"{BASE}/v1/paper-server/scholar/info",
            headers=H_AK,
            params={"scholarId": scholar_id},
            timeout=30
        )
        r.raise_for_status()
        info = r.json().get("data", {})
    except Exception as e:
        print(f"  详情获取失败：{e}，使用搜索结果中的基础数据")
        info = scholar

    # 合并搜索结果与详情
    profile = {
        "scholarId": scholar_id,
        "nameEn": info.get("nameEn", scholar.get("nameEn", "")),
        "nameZh": info.get("nameZh", scholar.get("nameZh", "")),
        "institution": (info.get("scholarOrgNameEn", "") or
                        info.get("scholarOrgNameZh", "") or
                        scholar.get("scholarOrgNameEn", "")),
        "paperNums": info.get("paperNums", scholar.get("paperNums", 0)),
        "citationNums": info.get("citationNums", scholar.get("citationNums", 0)),
        "hIndex": info.get("hIndex", scholar.get("hIndex", 0)),
        "isHighCited": scholar.get("isHighCited", False),
        "researchDirection": info.get("researchDirection", []),
        "educationBackground": (info.get("educationBackgroundZh") or
                                 info.get("educationBackground", "")),
        "workExperience": (info.get("workExperienceZh") or
                           info.get("workExperience", "")),
    }

    print(f"  h-index: {profile['hIndex']}, "
          f"论文: {profile['paperNums']}, "
          f"引用: {profile['citationNums']}")

    return profile


# ─── 步骤 2：发文轨迹分析 ────────────────────────────────

def analyze_publications(scholar_name: str, research_dirs: list) -> dict:
    """
    检索学者的发表记录，分析研究方向变迁和合作网络。
    返回 {papers, trajectory, collaborators, top_papers}。
    """
    print(f"\n[步骤 2/4] 发文轨迹分析：{scholar_name}")

    # 构建检索关键词：学者姓名 + 研究方向
    words = [scholar_name]
    if research_dirs:
        words.extend(research_dirs[:3])

    question = f"publications by {scholar_name}"

    try:
        r = requests.post(
            f"{BASE}/v1/paper/rag/pass/keyword",
            headers=H_JSON,
            json={
                "words": words,
                "question": question,
                "type": 5,
                "pageSize": 20
            },
            timeout=30
        )
        r.raise_for_status()
        text = r.text.strip()
        first_line = text.split('\n')[0]
        data = json.loads(first_line)
    except Exception as e:
        print(f"  检索失败：{e}")
        return {"papers": [], "trajectory": [], "collaborators": [],
                "top_papers": []}

    papers = data.get("data", [])
    print(f"  检索到 {len(papers)} 篇相关论文")

    if not papers:
        return {"papers": [], "trajectory": [], "collaborators": [],
                "top_papers": []}

    # ── 分析研究方向变迁 ──
    trajectory = analyze_trajectory(papers)

    # ── 分析合作网络 ──
    collaborators = analyze_collaborators(papers, scholar_name)

    # ── 提取 Top-5 代表作（按引用数排序） ──
    sorted_papers = sorted(papers, key=lambda p: p.get("citationNums", 0),
                           reverse=True)
    top_papers = []
    for p in sorted_papers[:5]:
        top_papers.append({
            "title": p.get("enName", ""),
            "doi": p.get("doi", ""),
            "journal": p.get("publicationEnName", ""),
            "date": p.get("coverDateStart", ""),
            "citations": p.get("citationNums", 0),
            "impactFactor": p.get("impactFactor", 0),
        })
        print(f"  TOP: {p.get('enName', '')[:60]}... "
              f"(引用: {p.get('citationNums', 0)})")

    return {
        "papers": papers,
        "trajectory": trajectory,
        "collaborators": collaborators,
        "top_papers": top_papers,
    }


def analyze_trajectory(papers: list) -> list:
    """
    按时间线分析论文关键词变化，检测研究方向转变。

    策略：
    1. 按发表年份分组
    2. 从每篇论文的标题和摘要中提取高频术语
    3. 比较不同时期的术语分布，识别方向变迁

    返回 [{period, year_range, dominant_topics, paper_count}]。
    """
    if not papers:
        return []

    # 按年份分组
    papers_by_year = defaultdict(list)
    for p in papers:
        year = p.get("coverDateStart", "")[:4]
        if year and year.isdigit():
            papers_by_year[int(year)].append(p)

    if not papers_by_year:
        return []

    years = sorted(papers_by_year.keys())
    min_year, max_year = years[0], years[-1]
    span = max_year - min_year + 1

    # 根据时间跨度确定分期策略
    if span <= 3:
        # 时间跨度短，逐年分析
        periods = [(y, y) for y in years]
    elif span <= 10:
        # 中等跨度，分为 3 个时期
        third = span // 3
        periods = [
            (min_year, min_year + third),
            (min_year + third + 1, min_year + 2 * third),
            (min_year + 2 * third + 1, max_year),
        ]
    else:
        # 长跨度，分为早期、中期、近期
        periods = [
            (min_year, min_year + span // 3),
            (min_year + span // 3 + 1, min_year + 2 * span // 3),
            (min_year + 2 * span // 3 + 1, max_year),
        ]

    period_labels = ["早期", "中期", "近期"] if len(periods) >= 3 else \
                    [f"{s}-{e}" for s, e in periods]

    trajectory = []
    for i, (start, end) in enumerate(periods):
        period_papers = []
        for y in range(start, end + 1):
            period_papers.extend(papers_by_year.get(y, []))

        if not period_papers:
            continue

        # 从标题中提取关键词
        title_words = Counter()
        for p in period_papers:
            title = p.get("enName", "").lower()
            # 提取有意义的多词短语和单词
            words = [w for w in title.split()
                     if len(w) > 3 and w not in STOP_WORDS]
            title_words.update(words)

        dominant = [w for w, _ in title_words.most_common(5)]

        label = period_labels[i] if i < len(period_labels) else f"{start}-{end}"
        trajectory.append({
            "period": label,
            "year_range": f"{start}-{end}",
            "paper_count": len(period_papers),
            "dominant_topics": dominant,
        })

    return trajectory


# 英文停用词（用于标题关键词提取）
STOP_WORDS = {
    "the", "and", "for", "with", "from", "that", "this", "which",
    "their", "have", "been", "were", "are", "was", "has", "its",
    "into", "using", "based", "approach", "method", "methods",
    "study", "analysis", "research", "paper", "novel", "new",
    "through", "between", "about", "also", "than", "more",
    "under", "over", "after", "before", "other", "such", "each",
    "when", "where", "what", "both", "some", "only", "most",
}


def analyze_collaborators(papers: list, scholar_name: str) -> list:
    """
    分析合作网络：统计共同作者出现频次。
    返回 [{name, count, institutions}] 按频次降序。
    """
    coauthor_count = Counter()
    coauthor_papers = defaultdict(list)

    name_lower = scholar_name.lower()

    for p in papers:
        authors = p.get("authors", [])
        if isinstance(authors, str):
            # 有时 authors 是逗号分隔字符串
            authors = [a.strip() for a in authors.split(",")]

        for author in authors:
            if isinstance(author, dict):
                author_name = author.get("name", "")
            else:
                author_name = str(author)

            # 跳过目标学者本人
            if not author_name or author_name.lower() == name_lower:
                continue

            coauthor_count[author_name] += 1
            coauthor_papers[author_name].append(
                p.get("enName", "")[:50]
            )

    # 按合作频次排序，取 Top-10
    collaborators = []
    for name, count in coauthor_count.most_common(10):
        collaborators.append({
            "name": name,
            "count": count,
            "sample_papers": coauthor_papers[name][:3],
        })

    if collaborators:
        print(f"  合作网络：识别到 {len(coauthor_count)} 位合作者")
        for c in collaborators[:5]:
            print(f"    - {c['name']}（合作 {c['count']} 次）")

    return collaborators


# ─── 步骤 3：知识图谱定位 ────────────────────────────────

def locate_in_knowledge_graph(research_dirs: list) -> list:
    """
    在知识图谱中搜索学者的研究方向，定位其在知识网络中的位置。
    返回知识节点列表。
    """
    print(f"\n[步骤 3/4] 知识图谱定位")

    if not research_dirs:
        print("  无研究方向信息，跳过知识图谱定位。")
        return []

    query = " ".join(research_dirs[:5])
    print(f"  搜索查询：{query}")

    try:
        r = requests.post(
            f"{BASE}/v1/lkm/search",
            headers=H_JSON,
            json={"query": query, "limit": 10},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  知识图谱搜索失败：{e}")
        return []

    raw = data.get("data", [])
    # API may return dict or list; normalize to list
    if isinstance(raw, dict):
        nodes = [raw] if raw else []
    elif isinstance(raw, list):
        nodes = raw
    else:
        nodes = []
    print(f"  找到 {len(nodes)} 个相关知识节点")

    return nodes


# ─── 步骤 4：网络资料补充 ────────────────────────────────

def search_web_presence(scholar_name: str, institution: str = "") -> list:
    """
    搜索学者的网络资料：机构主页、Google Scholar、新闻报道等。
    返回搜索结果列表。
    """
    print(f"\n[步骤 4/4] 网络资料补充：{scholar_name}")

    queries = [
        f"{scholar_name} {institution} researcher homepage",
        f"{scholar_name} scholar profile research",
    ]

    all_results = []
    for q in queries:
        try:
            r = requests.get(
                f"{BASE}/v1/search/web",
                headers=H_AK,
                params={"q": q, "num": 5},
                timeout=30
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("organic_results", [])
            all_results.extend(results)
        except Exception as e:
            print(f"  搜索失败（{q[:30]}...）：{e}")

    # 去重（按 link）
    seen_links = set()
    unique_results = []
    for res in all_results:
        link = res.get("link", "")
        if link and link not in seen_links:
            seen_links.add(link)
            unique_results.append(res)

    print(f"  找到 {len(unique_results)} 条网络资料")
    for res in unique_results[:5]:
        print(f"    - {res.get('title', '')[:60]}")
        print(f"      {res.get('link', '')}")

    return unique_results


# ─── 报告生成 ───────────────────────────────────────────

def generate_report(
    profile: dict,
    pub_analysis: dict,
    kg_nodes: list,
    web_results: list,
) -> str:
    """
    汇总所有分析结果，生成学者画像报告（Markdown 格式）。
    """
    lines = []

    name_display = profile.get("nameEn", "")
    if profile.get("nameZh"):
        name_display += f" / {profile['nameZh']}"

    lines.append(f"# 学者画像报告：{name_display}\n")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> 数据来源：Bohrium OpenAPI (scholar-search + paper-search "
                 f"+ lkm + web-search)\n")

    # ── 1. 基础数据卡片 ──
    lines.append("## 1. 基础数据卡片\n")
    lines.append("| 指标 | 值 |")
    lines.append("|------|------|")
    lines.append(f"| **姓名** | {name_display} |")
    lines.append(f"| **机构** | {profile.get('institution', 'N/A')} |")
    lines.append(f"| **h-index** | {profile.get('hIndex', 'N/A')} |")
    lines.append(f"| **总论文数** | {profile.get('paperNums', 'N/A')} |")
    lines.append(f"| **总引用数** | {profile.get('citationNums', 'N/A')} |")
    high_cited = "是" if profile.get("isHighCited") else "否"
    lines.append(f"| **高被引学者** | {high_cited} |")

    directions = profile.get("researchDirection", [])
    if directions:
        dir_str = "、".join(directions) if isinstance(directions, list) else str(directions)
        lines.append(f"| **研究方向** | {dir_str} |")

    edu = profile.get("educationBackground", "")
    if edu:
        lines.append(f"| **教育经历** | {edu[:100]} |")

    work = profile.get("workExperience", "")
    if work:
        lines.append(f"| **工作经历** | {work[:100]} |")

    lines.append("")

    # ── 2. 研究轨迹 ──
    lines.append("## 2. 研究轨迹\n")
    trajectory = pub_analysis.get("trajectory", [])
    if trajectory:
        lines.append("| 时期 | 年份范围 | 论文数 | 主要研究主题 |")
        lines.append("|------|---------|--------|------------|")
        for t in trajectory:
            topics = "、".join(t["dominant_topics"][:5]) if t["dominant_topics"] else "N/A"
            lines.append(
                f"| {t['period']} | {t['year_range']} | "
                f"{t['paper_count']} | {topics} |"
            )
        lines.append("")

        # 方向变迁分析
        if len(trajectory) >= 2:
            early_topics = set(trajectory[0].get("dominant_topics", []))
            recent_topics = set(trajectory[-1].get("dominant_topics", []))
            new_topics = recent_topics - early_topics
            if new_topics:
                lines.append(f"**方向变迁**：近期新增研究主题包括 "
                             f"{', '.join(new_topics)}，"
                             f"可能反映出研究重心的转移。\n")
            else:
                lines.append("**方向变迁**：研究主题较为一致，"
                             "核心方向保持稳定。\n")
    else:
        lines.append("未获取到足够的发文数据进行轨迹分析。\n")

    # ── 3. 合作网络 ──
    lines.append("## 3. 合作网络\n")
    collaborators = pub_analysis.get("collaborators", [])
    if collaborators:
        lines.append("| # | 合作者 | 合作论文数 | 代表性合作论文 |")
        lines.append("|---|--------|-----------|--------------|")
        for i, c in enumerate(collaborators[:10], 1):
            sample = c["sample_papers"][0][:40] + "..." if c["sample_papers"] else "N/A"
            lines.append(
                f"| {i} | {c['name']} | {c['count']} | {sample} |"
            )
        lines.append("")

        # 合作网络概要
        total_collaborators = len(pub_analysis.get("collaborators", []))
        top_collab = collaborators[0] if collaborators else None
        if top_collab:
            lines.append(
                f"**网络概要**：共识别到合作者若干，"
                f"最频繁的合作者为 **{top_collab['name']}**"
                f"（合作 {top_collab['count']} 篇）。\n"
            )
    else:
        lines.append("未获取到合作者数据。\n")

    # ── 4. Top-5 代表作 ──
    lines.append("## 4. Top-5 代表作\n")
    top_papers = pub_analysis.get("top_papers", [])
    if top_papers:
        lines.append("| # | 标题 | 期刊 | 影响因子 | 被引次数 | 发表日期 |")
        lines.append("|---|------|------|---------|---------|---------|")
        for i, p in enumerate(top_papers, 1):
            title = p["title"][:50] + ("..." if len(p["title"]) > 50 else "")
            title = title.replace("|", "\\|")
            journal = (p.get("journal") or "N/A")[:25]
            journal = journal.replace("|", "\\|")
            lines.append(
                f"| {i} | {title} | {journal} | "
                f"{p.get('impactFactor', 0)} | "
                f"{p.get('citations', 0)} | "
                f"{p.get('date', 'N/A')[:10]} |"
            )
        lines.append("")
    else:
        lines.append("未检索到代表性论文。\n")

    # ── 5. 近期研究趋势判断 ──
    lines.append("## 5. 近期研究趋势判断\n")
    papers = pub_analysis.get("papers", [])
    if papers:
        # 统计近 2 年论文
        current_year = datetime.now().year
        recent_papers = [
            p for p in papers
            if p.get("coverDateStart", "")[:4].isdigit()
            and int(p["coverDateStart"][:4]) >= current_year - 2
        ]
        older_papers = [
            p for p in papers
            if p.get("coverDateStart", "")[:4].isdigit()
            and int(p["coverDateStart"][:4]) < current_year - 2
        ]

        lines.append(f"- **近 2 年发文数**：{len(recent_papers)} 篇"
                     f"（检索范围内）")
        lines.append(f"- **更早发文数**：{len(older_papers)} 篇"
                     f"（检索范围内）")

        if recent_papers:
            recent_topics = Counter()
            for p in recent_papers:
                title = p.get("enName", "").lower()
                words = [w for w in title.split()
                         if len(w) > 3 and w not in STOP_WORDS]
                recent_topics.update(words)

            hot_topics = [w for w, _ in recent_topics.most_common(5)]
            lines.append(f"- **近期高频主题**：{', '.join(hot_topics)}")

            # 趋势判断
            if len(recent_papers) > len(older_papers):
                lines.append("- **趋势判断**：发文量增长，研究活跃度上升")
            elif len(recent_papers) == 0:
                lines.append("- **趋势判断**：近期无新发文，"
                             "可能处于积累期或方向调整中")
            else:
                lines.append("- **趋势判断**：发文节奏稳定")
        lines.append("")
    else:
        lines.append("数据不足，无法进行趋势判断。\n")

    # ── 附录：知识图谱定位 ──
    if kg_nodes:
        lines.append("## 附录 A：知识图谱中的位置\n")
        lines.append("以下是该学者研究方向在知识图谱中匹配到的相关节点：\n")
        for i, node in enumerate(kg_nodes[:5], 1):
            if isinstance(node, dict):
                node_text = json.dumps(node, ensure_ascii=False)[:200]
                lines.append(f"{i}. {node_text}")
            else:
                lines.append(f"{i}. {str(node)[:200]}")
        lines.append("")

    # ── 附录：网络资料 ──
    if web_results:
        lines.append("## 附录 B：相关网络资料\n")
        lines.append("| # | 来源 | 链接 |")
        lines.append("|---|------|------|")
        for i, res in enumerate(web_results[:8], 1):
            title = res.get("title", "N/A")[:50].replace("|", "\\|")
            link = res.get("link", "")
            lines.append(f"| {i} | {title} | {link} |")
        lines.append("")

    return "\n".join(lines)


# ─── 主流程 ─────────────────────────────────────────────

def profile_scholar(scholar_name: str, institution: str = ""):
    """
    学者画像主函数。

    参数：
        scholar_name: 学者姓名（中英文均可）
        institution: 所属机构（可选，用于消歧）
    """
    print("=" * 60)
    print("  学者画像 (Scholar Profiler)")
    print(f"  学者：{scholar_name}")
    if institution:
        print(f"  机构：{institution}")
    print("=" * 60)

    # ── 步骤 1：学者搜索与基础信息 ──
    profile = search_scholar(scholar_name, institution)
    if not profile:
        print("\n无法找到目标学者，画像流程终止。")
        print("建议：")
        print("  1. 检查姓名拼写")
        print("  2. 尝试中英文不同形式的姓名")
        print("  3. 提供机构名称辅助消歧")
        return None

    # ── 步骤 2：发文轨迹分析 ──
    research_dirs = profile.get("researchDirection", [])
    pub_analysis = analyze_publications(
        profile.get("nameEn") or scholar_name,
        research_dirs
    )

    # ── 步骤 3：知识图谱定位 ──
    kg_nodes = locate_in_knowledge_graph(research_dirs)

    # ── 步骤 4：网络资料补充 ──
    web_results = search_web_presence(
        profile.get("nameEn") or scholar_name,
        profile.get("institution", "")
    )

    # ── 生成报告 ──
    print("\n" + "=" * 60)
    print("  生成学者画像报告...")
    print("=" * 60 + "\n")

    report = generate_report(profile, pub_analysis, kg_nodes, web_results)
    print(report)

    return report


# ─── 入口 ───────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python scholar_profiler.py <学者姓名> [机构名称]")
        print()
        print("示例：")
        print('  python scholar_profiler.py "Yann LeCun"')
        print('  python scholar_profiler.py "张三" "清华大学"')
        print('  python scholar_profiler.py "Geoffrey Hinton" "University of Toronto"')
        sys.exit(1)

    name = sys.argv[1]
    inst = sys.argv[2] if len(sys.argv) > 2 else ""

    profile_scholar(name, inst)
```

---

## 各步骤详解

### 步骤 1：学者搜索与基础信息 (`scholar-search`)

先通过 `scholar/search` 搜索候选学者列表，若提供了机构参数则优先匹配机构名称。然后用 `scholarId` 拉取完整详情。

```python
# 搜索学者
r = requests.post(f"{BASE}/v1/paper-server/scholar/search",
    headers=H_JSON,
    json={"name": "Yann LeCun", "page": 1, "pageSize": 5})

# 获取详情
scholar_id = r.json()["data"]["items"][0]["scholarId"]
r = requests.get(f"{BASE}/v1/paper-server/scholar/info",
    headers=H_AK,
    params={"scholarId": scholar_id})
```

**消歧策略**：当搜索返回多个同名学者时，遍历候选列表，匹配 `scholarOrgNameEn` 或 `scholarOrgNameZh` 中是否包含用户提供的机构名称。

---

### 步骤 2：发文轨迹分析 (`paper-search`)

用学者姓名 + 研究方向作为关键词检索论文，然后：

1. **按年份分组**：将论文按 `coverDateStart` 的年份分入不同时期
2. **提取高频术语**：从每个时期的论文标题中统计关键词
3. **检测方向转变**：比较早期与近期的关键词集合，找出新增主题
4. **合作者统计**：从 `authors` 字段提取共同作者，按频次排序

```python
# 按时期划分的方向变迁检测
early_topics = {"molecular dynamics", "force field"}
recent_topics = {"graph neural network", "force field", "equivariant"}
new_directions = recent_topics - early_topics
# → {"graph neural network", "equivariant"} 为近期新方向
```

---

### 步骤 3：知识图谱定位 (`lkm`)

将学者的研究方向输入知识图谱搜索，了解其研究领域在整个科学知识网络中的位置。

```python
r = requests.post(f"{BASE}/v1/lkm/search",
    headers=H_JSON,
    json={"query": "molecular dynamics deep learning force field", "limit": 10})
```

---

### 步骤 4：网络资料补充 (`web-search`)

搜索学者的机构主页、Google Scholar 页面、新闻报道等网络资料，补充 API 无法获取的信息。

```python
r = requests.get(f"{BASE}/v1/search/web",
    headers=H_AK,
    params={"q": "Yann LeCun researcher homepage", "num": 5})
```

---

## curl 示例

```bash
AK="$ACCESS_KEY"
BASE="https://open.bohrium.com/openapi"

# ── 步骤 1：学者搜索 ──
curl -s -X POST "$BASE/v1/paper-server/scholar/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"name":"Yann LeCun","page":1,"pageSize":5}'

# ── 步骤 1：学者详情 ──
# 将上一步返回的 scholarId 替换下方 SCHOLAR_ID
curl -s "$BASE/v1/paper-server/scholar/info?scholarId=SCHOLAR_ID" \
  -H "accessKey: $AK"

# ── 步骤 2：论文检索 ──
curl -s -X POST "$BASE/v1/paper/rag/pass/keyword" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{
    "words": ["Yann LeCun", "deep learning", "convolutional"],
    "question": "publications by Yann LeCun",
    "type": 5,
    "pageSize": 20
  }'

# ── 步骤 3：知识图谱定位 ──
curl -s -X POST "$BASE/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "deep learning convolutional neural networks", "limit": 10}'

# ── 步骤 4：网络资料搜索 ──
curl -s "$BASE/v1/search/web?q=Yann+LeCun+researcher+homepage&num=5" \
  -H "accessKey: $AK"
```

---

## 使用示例

### 基本用法

```python
# 查询知名学者
profile_scholar("Yann LeCun")

# 同名消歧
profile_scholar("张三", institution="清华大学")

# 英文姓名 + 机构
profile_scholar("Geoffrey Hinton", institution="University of Toronto")
```

### 命令行调用

```bash
# 基本查询
python scholar_profiler.py "Yann LeCun"

# 带机构消歧
python scholar_profiler.py "张三" "清华大学"
```

---

## 错误处理

| 场景 | 错误信息 | 处理方式 |
|------|---------|---------|
| ACCESS_KEY 未设置 | `未设置 ACCESS_KEY 环境变量` | 配置 `~/.openclaw/openclaw.json` |
| 学者搜索无结果 | `未找到匹配的学者` | 检查姓名拼写，尝试中英文不同形式 |
| 多个同名学者 | 自动选第一个 | 传入 `institution` 参数辅助消歧 |
| 论文检索为空 | `检索到 0 篇相关论文` | 可能姓名不匹配，尝试英文全名 |
| 知识图谱无结果 | `无研究方向信息，跳过` | 学者详情中无 `researchDirection` |
| 网络搜索失败 | `搜索失败` | 网络问题或关键词问题，不影响主报告 |
| Invalid AccessKey / 401 | Key 已失效 | 更新 `~/.openclaw/openclaw.json` 并重启会话 |

---

## 搭配使用

- **scholar-profiler** 了解学者背景 → **paper-search** 深入阅读其论文
- **scholar-profiler** 发现合作者 → 对合作者再次运行 **scholar-profiler** 构建合作网络图
- **scholar-profiler** 判断研究趋势 → **literature-review** 对该方向做完整文献综述
- **scholar-profiler** 获取研究方向 → **tech-radar** 持续监控该方向的最新进展
- **scholar-profiler** 输出报告 → **knowledge-base** 存档供后续查阅
