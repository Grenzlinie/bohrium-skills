---
name: patent-paper-cross
description: "Patent-paper cross analysis combining academic publication search, patent search, and scholar profiling. Use when: user wants to assess technology commercialization status, identify unpatented research opportunities, or understand IP landscape. NOT for: pure paper search (use bohrium-paper-search), competitor monitoring (use tech-radar)."
---

# SKILL: 专利-论文交叉分析 (Patent-Paper Cross Analysis)

## 概述

专利-论文交叉分析是一个**编排型 Skill**，串联 `paper-search`、`paper-search patent`、`scholar-search` 三个原子 Skill，自动完成从学术论文检索、专利检索、学者/团队识别到交叉分析报告生成的完整流程。通过对比论文与专利在同一技术方向上的分布，揭示技术商业化状态、未专利化的研究机会和知识产权格局。

**组合的原子 Skill：**

| 步骤 | 原子 Skill | 端点 | 功能 |
|------|-----------|------|------|
| 1 | `paper-search` | `/v1/paper/rag/pass/keyword` | 检索相关学术论文 |
| 2 | `paper-search patent` | `/v1/paper/rag/pass/patent` | 检索相关专利 |
| 3 | `scholar-search` | `/v1/paper-server/scholar/search` | 识别同时拥有论文和专利的学者/团队 |
| 4 | 综合分析 | — | 交叉比对，输出技术转化评估报告 |

**适用场景：**

- 评估某技术方向的商业化成熟度（论文多但专利少 = 早期学术阶段）
- 发现尚未被专利保护的研究成果（纯学术机会）
- 了解技术方向的知识产权格局（活跃专利申请人、专利集中度）
- 识别学术界与产业界的桥梁人物（同时发论文和申请专利的学者）
- 为技术转让、投资决策提供数据支撑

**不适用：**

- 纯论文检索 → `bohrium-paper-search`
- 竞品技术监控 → `tech-radar`
- 单篇论文精读 → `paper-dissector`
- 完整文献综述 → `literature-review`
- 单纯学者查询 → `bohrium-scholar-search`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"patent-paper-cross": {
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
| `keywords` | string[] | 是 | — | 技术方向关键词列表（3-8 个英文术语） |
| `question` | string | 否 | 自动生成 | 自然语言问题描述，提升语义检索相关性 |
| `focus_orgs` | string[] | 否 | [] | 重点关注的公司/机构名称（用于专利申请人筛选和学者匹配） |
| `time_range` | int | 否 | 5 | 检索时间范围（年） |
| `paper_top_n` | int | 否 | 20 | 论文检索数量 |
| `patent_top_n` | int | 否 | 20 | 专利检索数量 |
| `jcr_zones` | string[] | 否 | [] | JCR 分区筛选，如 `["Q1", "Q2"]` |

---

## 输出格式

交叉分析结果包含以下结构化部分：

### 1. 论文 vs 专利数量趋势对比

按年份对比论文发表量与专利申请量，判断技术所处阶段。

### 2. 已专利化技术点

在论文和专利中同时出现的技术主题，代表已被产业界关注并保护的技术。

### 3. 纯学术机会

仅在论文中出现但尚无对应专利的技术主题，代表潜在的知识产权机会。

### 4. 活跃专利申请人

专利数量最多的申请人/机构，反映 IP 竞争格局。

### 5. 技术转化成熟度评估

综合论文-专利比率、时间差、申请人多样性等维度，给出技术转化阶段判断。

---

## 分析深度要求

### 趋势对比的定量标准

论文 vs 专利趋势对比**必须有具体数字支撑**：
- ✅ "2022-2024 年论文发表量从 12 篇增至 45 篇（年增长 93%），同期专利申请从 3 件增至 18 件"
- ❌ "论文和专利数量都在增长"（无具体数字）

### "纯学术机会"的判定严谨性

标记为"纯学术机会"的技术点需满足：
- 在论文中出现 ≥ 3 次（排除偶发提及）
- 在专利数据库中确认无相同技术方案的申请（不能仅因为关键词不匹配就判定无专利）
- 标注"基于 Bohrium 检索范围内的判断，建议在专利数据库中二次确认"

### 禁止的行为

- ❌ 将关键词不同但技术本质相同的论文和专利判为"不匹配"
- ❌ 技术转化阶段判断无定量依据
- ❌ 不标注数据覆盖范围和时间窗口

---

## 工作流程图

```
输入: keywords[], focus_orgs[], time_range
        |
        v
+--------------------------------------+
|  步骤 1: 学术论文检索                  |
|  POST /v1/paper/rag/pass/keyword     |
|  -> 检索相关论文                      |
|  -> 提取年份分布、关键词、作者         |
+---------------+----------------------+
                |
                v
+--------------------------------------+
|  步骤 2: 专利检索                      |
|  POST /v1/paper/rag/pass/patent      |
|  -> 检索相关专利                      |
|  -> 提取申请人、年份、技术分类         |
+---------------+----------------------+
                |
                v
+--------------------------------------+
|  步骤 3: 学者/团队识别                 |
|  POST /v1/paper-server/scholar/search|
|  -> 从论文高产作者中检索学者画像       |
|  -> 判断是否同时持有专利               |
+---------------+----------------------+
                |
                v
+--------------------------------------+
|  步骤 4: 交叉分析与报告生成            |
|  -> 论文 vs 专利趋势对比              |
|  -> 已专利化技术点识别                |
|  -> 纯学术机会发现                    |
|  -> 活跃申请人分析                    |
|  -> 技术转化成熟度评估                |
+--------------------------------------+
```

---

## 通用代码模板

```python
import os, sys, json, requests
from datetime import datetime, timedelta
from collections import Counter, defaultdict

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误: 请设置环境变量 ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS = {"accessKey": AK}
```

---

## 步骤 1: 学术论文检索

使用 `paper-search` 的关键词检索端点，获取该技术方向的学术论文列表。

### Python 示例

```python
def search_papers(keywords, question="", top_n=20,
                  start_time="", end_time="", jcr_zones=None):
    """
    检索学术论文。

    Args:
        keywords: 技术方向关键词列表
        question: 自然语言问题描述
        top_n: 返回论文数量
        start_time: 起始日期 YYYY-MM-DD
        end_time: 截止日期 YYYY-MM-DD
        jcr_zones: JCR 分区筛选

    Returns:
        论文列表，按引用数降序排列
    """
    if not question:
        question = " ".join(keywords)

    payload = {
        "words": keywords,
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

    # API 可能返回多行 JSON（streaming），取第一行
    text = r.text.strip()
    first_line = text.split('\n')[0]
    data = json.loads(first_line)

    if data.get("code") != 0:
        raise RuntimeError(f"论文检索失败: {data.get('message', 'unknown error')}")

    papers = data["data"]
    papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
    return papers
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["perovskite", "solar cell", "stability"],
    "question": "perovskite solar cell stability improvement methods",
    "type": 5,
    "startTime": "2021-01-01",
    "endTime": "2026-01-01",
    "jcrZones": ["Q1"],
    "pageSize": 20
  }'
```

---

## 步骤 2: 专利检索

使用 `paper-search patent` 端点检索相关专利。

### Python 示例

```python
def search_patents(keyword, page=1, page_size=20):
    """
    检索专利。

    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页数量

    Returns:
        专利列表
    """
    payload = {
        "keyword": keyword,
        "page": page,
        "pageSize": page_size
    }

    r = requests.post(
        f"{BASE}/v1/paper/rag/pass/patent",
        headers=HEADERS_JSON,
        json=payload
    )
    r.raise_for_status()
    data = r.json()

    # 专利 API 返回数组格式
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "data" in data:
        return data["data"] if isinstance(data["data"], list) else [data["data"]]
    else:
        return []


def search_patents_multi_keyword(keywords, page_size=20):
    """
    使用多个关键词分别检索专利，合并去重。

    Args:
        keywords: 关键词列表
        page_size: 每个关键词返回的专利数量

    Returns:
        去重后的专利列表
    """
    all_patents = []
    seen_ids = set()

    for kw in keywords:
        try:
            patents = search_patents(kw, page=1, page_size=page_size)
            for p in patents:
                # 使用专利号或标题去重
                pid = str(p.get("patentNo", p.get("title", "")))
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_patents.append(p)
            print(f"  关键词 '{kw}': 检索到 {len(patents)} 条专利")
        except Exception as e:
            print(f"  关键词 '{kw}': 检索失败 - {e}")

    return all_patents
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 单关键词专利检索
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/patent" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "keyword": "perovskite solar cell",
    "page": 1,
    "pageSize": 20
  }'

# 翻页检索
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/patent" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "keyword": "perovskite solar cell stability",
    "page": 2,
    "pageSize": 20
  }'
```

---

## 步骤 3: 学者/团队识别

从步骤 1 中的高产作者中检索学者画像，判断其是否同时持有论文和专利（跨学术-产业的桥梁人物）。

### Python 示例

```python
def identify_bridge_scholars(papers, patents, focus_orgs=None):
    """
    从论文作者中识别高产学者，并交叉比对专利申请人。

    Args:
        papers: 论文列表
        patents: 专利列表
        focus_orgs: 重点关注的机构列表

    Returns:
        dict: {
            "top_authors": [...],        # 论文高产作者
            "patent_applicants": [...],   # 专利活跃申请人
            "bridge_scholars": [...],     # 同时出现在两侧的人物
            "scholar_profiles": [...]     # 学者详细画像
        }
    """
    # 统计论文作者
    author_count = Counter()
    author_papers = defaultdict(list)
    for p in papers:
        authors = p.get("authors", [])
        for author in authors:
            if isinstance(author, dict):
                name = author.get("name", author.get("nameEn", ""))
            else:
                name = str(author)
            if name:
                author_count[name] += 1
                author_papers[name].append(p.get("enName", ""))

    top_authors = [
        {"name": name, "paper_count": count}
        for name, count in author_count.most_common(10)
    ]

    # 统计专利申请人
    applicant_count = Counter()
    for pat in patents:
        applicant = pat.get("applicant", pat.get("assignee", ""))
        if applicant:
            applicant_count[applicant] += 1

    patent_applicants = [
        {"name": name, "patent_count": count}
        for name, count in applicant_count.most_common(10)
    ]

    # 交叉比对：找出同时出现在论文作者和专利申请人中的名称
    author_names = set(n.lower() for n in author_count.keys())
    applicant_names = set(n.lower() for n in applicant_count.keys())
    bridge_names = author_names & applicant_names

    # 若有重点关注机构，也在申请人中匹配
    if focus_orgs:
        for org in focus_orgs:
            org_lower = org.lower()
            for applicant in applicant_count.keys():
                if org_lower in applicant.lower():
                    bridge_names.add(applicant.lower())

    bridge_scholars = []
    for name in bridge_names:
        bridge_scholars.append({
            "name": name,
            "paper_count": author_count.get(name, 0),
            "patent_count": applicant_count.get(name, 0),
        })

    # 对论文 Top-5 作者查询学者画像
    scholar_profiles = []
    for author_info in top_authors[:5]:
        name = author_info["name"]
        try:
            r = requests.post(
                f"{BASE}/v1/paper-server/scholar/search",
                headers=HEADERS_JSON,
                json={"name": name, "page": 1, "pageSize": 3}
            )
            r.raise_for_status()
            data = r.json()
            items = data.get("data", {}).get("items", [])
            if items:
                scholar = items[0]
                scholar_profiles.append({
                    "name": name,
                    "nameEn": scholar.get("nameEn", ""),
                    "nameZh": scholar.get("nameZh", ""),
                    "institution": (scholar.get("scholarOrgNameEn", "") or
                                    scholar.get("scholarOrgNameZh", "")),
                    "paperNums": scholar.get("paperNums", 0),
                    "citationNums": scholar.get("citationNums", 0),
                    "hIndex": scholar.get("hIndex", 0),
                    "paper_count_in_topic": author_info["paper_count"],
                })
                print(f"  学者: {name} -> h-index={scholar.get('hIndex', 0)}, "
                      f"机构={scholar.get('scholarOrgNameEn', '')}")
        except Exception as e:
            print(f"  学者搜索失败: {name} -> {e}")

    return {
        "top_authors": top_authors,
        "patent_applicants": patent_applicants,
        "bridge_scholars": bridge_scholars,
        "scholar_profiles": scholar_profiles,
    }
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 根据论文高产作者搜索学者画像
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper-server/scholar/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"name": "Author Name", "page": 1, "pageSize": 3}'

# 获取学者详情
curl -s "https://open.bohrium.com/openapi/v1/paper-server/scholar/info?scholarId=SCHOLAR_ID" \
  -H "accessKey: $AK"
```

---

## 步骤 4: 交叉分析与报告生成

将前三步结果进行交叉比对，生成技术转化评估报告。

### Python 示例

```python
def cross_analyze(papers, patents, scholar_result, keywords):
    """
    交叉分析论文与专利数据，生成结构化报告。

    Args:
        papers: 论文列表
        patents: 专利列表
        scholar_result: 学者识别结果
        keywords: 原始检索关键词

    Returns:
        dict: 包含趋势对比、技术点分析、成熟度评估等
    """
    analysis = {}

    # ── 1. 论文 vs 专利年度趋势 ──
    paper_years = Counter()
    for p in papers:
        year = p.get("coverDateStart", "")[:4]
        if year and year.isdigit():
            paper_years[int(year)] += 1

    patent_years = Counter()
    for pat in patents:
        # 专利的日期字段视返回格式而定
        date_str = (pat.get("applicationDate", "") or
                    pat.get("publicationDate", "") or
                    pat.get("date", ""))
        year = str(date_str)[:4]
        if year and year.isdigit():
            patent_years[int(year)] += 1

    all_years = sorted(set(list(paper_years.keys()) +
                           list(patent_years.keys())))
    trend = []
    for y in all_years:
        trend.append({
            "year": y,
            "paper_count": paper_years.get(y, 0),
            "patent_count": patent_years.get(y, 0),
        })

    analysis["trend"] = trend

    # ── 2. 技术点提取与交叉比对 ──
    # 从论文标题提取关键技术术语
    paper_terms = Counter()
    for p in papers:
        title = p.get("enName", "").lower()
        for kw in keywords:
            if kw.lower() in title:
                paper_terms[kw.lower()] += 1
        # 也提取高频词
        words = [w for w in title.split() if len(w) > 4]
        paper_terms.update(words)

    # 从专利标题提取关键技术术语
    patent_terms = Counter()
    for pat in patents:
        raw_title = pat.get("title") or pat.get("name") or ""
        title = (raw_title if isinstance(raw_title, str) else str(raw_title)).lower()
        for kw in keywords:
            if kw.lower() in title:
                patent_terms[kw.lower()] += 1
        words = [w for w in title.split() if len(w) > 4]
        patent_terms.update(words)

    # 已专利化技术点（同时出现在论文和专利中的术语）
    common_terms = set(paper_terms.keys()) & set(patent_terms.keys())
    patented_tech = [
        {"term": t, "paper_freq": paper_terms[t], "patent_freq": patent_terms[t]}
        for t in common_terms
        if paper_terms[t] >= 2 and patent_terms[t] >= 1
    ]
    patented_tech.sort(key=lambda x: x["patent_freq"], reverse=True)

    # 纯学术机会（仅在论文中出现的高频术语）
    paper_only = set(paper_terms.keys()) - set(patent_terms.keys())
    academic_opps = [
        {"term": t, "paper_freq": paper_terms[t]}
        for t in paper_only
        if paper_terms[t] >= 3
    ]
    academic_opps.sort(key=lambda x: x["paper_freq"], reverse=True)

    analysis["patented_tech"] = patented_tech[:15]
    analysis["academic_opportunities"] = academic_opps[:15]

    # ── 3. 活跃专利申请人 ──
    analysis["patent_applicants"] = scholar_result.get("patent_applicants", [])

    # ── 4. 桥梁学者 ──
    analysis["bridge_scholars"] = scholar_result.get("bridge_scholars", [])
    analysis["scholar_profiles"] = scholar_result.get("scholar_profiles", [])

    # ── 5. 技术转化成熟度评估 ──
    total_papers = len(papers)
    total_patents = len(patents)

    if total_papers == 0:
        maturity = "数据不足"
        maturity_detail = "未检索到学术论文，无法评估。"
    elif total_patents == 0:
        maturity = "早期学术阶段"
        maturity_detail = (f"检索到 {total_papers} 篇论文但无相关专利，"
                           "技术仍处于学术研究阶段，尚未进入产业化。")
    else:
        ratio = total_patents / total_papers
        if ratio < 0.1:
            maturity = "学术主导期"
            maturity_detail = (
                f"论文/专利比 = {total_papers}:{total_patents}，"
                f"专利占比仅 {ratio:.0%}。技术以学术研究为主，"
                "产业化刚起步，存在大量未被专利保护的研究成果。"
            )
        elif ratio < 0.5:
            maturity = "技术转化期"
            maturity_detail = (
                f"论文/专利比 = {total_papers}:{total_patents}，"
                f"专利占比 {ratio:.0%}。产业界已开始关注，"
                "部分核心技术已被专利保护，但仍有可观的空白领域。"
            )
        elif ratio < 1.0:
            maturity = "产业加速期"
            maturity_detail = (
                f"论文/专利比 = {total_papers}:{total_patents}，"
                f"专利占比 {ratio:.0%}。产业化程度较高，"
                "核心技术大部分已被专利覆盖，新进入者需注意 IP 壁垒。"
            )
        else:
            maturity = "产业成熟期"
            maturity_detail = (
                f"论文/专利比 = {total_papers}:{total_patents}，"
                "专利数量超过论文。技术已充分商业化，"
                "IP 竞争激烈，建议关注改进型专利或寻找细分方向突破。"
            )

    analysis["maturity"] = maturity
    analysis["maturity_detail"] = maturity_detail

    return analysis


def format_report(keywords, papers, patents, analysis):
    """
    格式化输出交叉分析报告（Markdown）。
    """
    lines = []

    lines.append(f"# 专利-论文交叉分析报告")
    lines.append(f"\n> 技术方向: {', '.join(keywords)}")
    lines.append(f"> 生成时间: {datetime.now().isoformat()}")
    lines.append(f"> 检索论文数: {len(papers)}, 检索专利数: {len(patents)}")

    # 1. 趋势对比
    lines.append("\n## 1. 论文 vs 专利数量趋势对比\n")
    trend = analysis.get("trend", [])
    if trend:
        lines.append("| 年份 | 论文数 | 专利数 | 论文/专利比 |")
        lines.append("|------|--------|--------|------------|")
        for t in trend:
            ratio = (f"{t['paper_count']/t['patent_count']:.1f}"
                     if t['patent_count'] > 0 else "-")
            lines.append(
                f"| {t['year']} | {t['paper_count']} | "
                f"{t['patent_count']} | {ratio} |"
            )
    else:
        lines.append("无足够的时间数据生成趋势。")

    # 2. 已专利化技术点
    lines.append("\n## 2. 已专利化技术点\n")
    lines.append("以下技术主题同时出现在学术论文和专利中，表明已被产业界关注并保护：\n")
    patented = analysis.get("patented_tech", [])
    if patented:
        lines.append("| # | 技术术语 | 论文出现频次 | 专利出现频次 |")
        lines.append("|---|---------|-------------|-------------|")
        for i, t in enumerate(patented[:10], 1):
            lines.append(
                f"| {i} | {t['term']} | {t['paper_freq']} | "
                f"{t['patent_freq']} |"
            )
    else:
        lines.append("未发现同时出现在论文和专利中的技术术语。")

    # 3. 纯学术机会
    lines.append("\n## 3. 纯学术机会（未专利化研究方向）\n")
    lines.append("以下技术主题仅在论文中出现，尚无对应专利，"
                 "可能是潜在的知识产权布局机会：\n")
    opps = analysis.get("academic_opportunities", [])
    if opps:
        lines.append("| # | 技术术语 | 论文出现频次 | 建议 |")
        lines.append("|---|---------|-------------|------|")
        for i, o in enumerate(opps[:10], 1):
            suggestion = "高频出现，建议优先评估" if o["paper_freq"] >= 5 else "值得关注"
            lines.append(
                f"| {i} | {o['term']} | {o['paper_freq']} | "
                f"{suggestion} |"
            )
    else:
        lines.append("所有高频论文技术点均已有对应专利覆盖。")

    # 4. 活跃专利申请人
    lines.append("\n## 4. 活跃专利申请人\n")
    applicants = analysis.get("patent_applicants", [])
    if applicants:
        lines.append("| # | 申请人 | 专利数量 |")
        lines.append("|---|--------|---------|")
        for i, a in enumerate(applicants[:10], 1):
            lines.append(f"| {i} | {a['name']} | {a['patent_count']} |")
    else:
        lines.append("未提取到专利申请人信息。")

    # 桥梁学者
    bridge = analysis.get("bridge_scholars", [])
    if bridge:
        lines.append("\n### 跨学术-产业桥梁人物\n")
        lines.append("以下人物/机构同时出现在论文作者和专利申请人中：\n")
        lines.append("| 名称 | 相关论文数 | 相关专利数 |")
        lines.append("|------|----------|----------|")
        for b in bridge:
            lines.append(
                f"| {b['name']} | {b['paper_count']} | "
                f"{b['patent_count']} |"
            )

    # 学者画像
    profiles = analysis.get("scholar_profiles", [])
    if profiles:
        lines.append("\n### 领域高产学者画像\n")
        lines.append("| # | 学者 | 机构 | h-index | 总论文数 | 总引用数 | 本领域论文数 |")
        lines.append("|---|------|------|---------|---------|---------|------------|")
        for i, s in enumerate(profiles, 1):
            lines.append(
                f"| {i} | {s['nameEn'] or s['name']} | "
                f"{s['institution']} | {s['hIndex']} | "
                f"{s['paperNums']} | {s['citationNums']} | "
                f"{s['paper_count_in_topic']} |"
            )

    # 5. 技术转化成熟度评估
    lines.append("\n## 5. 技术转化成熟度评估\n")
    lines.append(f"**阶段判断: {analysis.get('maturity', '未知')}**\n")
    lines.append(analysis.get("maturity_detail", ""))

    return "\n".join(lines)
```

---

## 完整编排示例

以下是将全部步骤串联的端到端 Python 脚本：

```python
#!/usr/bin/env python3
"""
专利-论文交叉分析 (Patent-Paper Cross Analysis) — 完整编排脚本

用法:
    export ACCESS_KEY="your_access_key"
    python3 patent_paper_cross.py

可修改下方 CONFIG 区域的参数来调整检索范围。
"""

import os
import sys
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
HEADERS = {"accessKey": AK}

# -- 用户可修改区域 --
CONFIG = {
    "keywords": ["perovskite", "solar cell", "stability"],
    "question": "perovskite solar cell stability and commercialization",
    "focus_orgs": [],                # 可选: ["LONGi", "First Solar"]
    "time_range_years": 5,
    "jcr_zones": [],
    "paper_top_n": 20,
    "patent_top_n": 20,
}


# ============================================================
# 步骤 1: 学术论文检索
# ============================================================

def step1_search_papers(config):
    end_time = datetime.now().strftime("%Y-%m-%d")
    start_time = (
        datetime.now() - timedelta(days=365 * config["time_range_years"])
    ).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"步骤 1: 学术论文检索")
    print(f"  关键词: {config['keywords']}")
    print(f"  时间范围: {start_time} ~ {end_time}")
    print(f"{'='*60}\n")

    payload = {
        "words": config["keywords"],
        "question": config.get("question", " ".join(config["keywords"])),
        "type": 5,
        "startTime": start_time,
        "endTime": end_time,
        "jcrZones": config.get("jcr_zones", []),
        "pageSize": config["paper_top_n"]
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

        if data.get("code") != 0:
            print(f"  检索失败: {data.get('message')}")
            return []

        papers = data["data"]
        papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
        print(f"  检索到 {len(papers)} 篇论文")
        for i, p in enumerate(papers[:5]):
            print(f"    {i+1}. {p.get('enName', '')[:60]}... "
                  f"(引用: {p.get('citationNums', 0)})")
        return papers

    except Exception as e:
        print(f"  检索异常: {e}")
        return []


# ============================================================
# 步骤 2: 专利检索
# ============================================================

def step2_search_patents(config):
    print(f"\n{'='*60}")
    print(f"步骤 2: 专利检索")
    print(f"{'='*60}\n")

    all_patents = []
    seen_ids = set()

    # 使用多个关键词组合检索
    keyword_queries = [
        " ".join(config["keywords"]),  # 全部关键词
    ]
    # 也尝试两两组合
    kws = config["keywords"]
    if len(kws) >= 2:
        for i in range(min(len(kws), 3)):
            for j in range(i + 1, min(len(kws), 4)):
                keyword_queries.append(f"{kws[i]} {kws[j]}")

    for kw in keyword_queries:
        try:
            payload = {
                "keyword": kw,
                "page": 1,
                "pageSize": config["patent_top_n"]
            }
            r = requests.post(
                f"{BASE}/v1/paper/rag/pass/patent",
                headers=HEADERS_JSON,
                json=payload
            )
            r.raise_for_status()
            data = r.json()

            patents = data if isinstance(data, list) else data.get("data", [])
            if not isinstance(patents, list):
                patents = []

            new_count = 0
            for p in patents:
                pid = str(p.get("patentNo", p.get("title", "")))
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_patents.append(p)
                    new_count += 1

            print(f"  关键词 '{kw}': {len(patents)} 条专利, "
                  f"{new_count} 条新增")

        except Exception as e:
            print(f"  关键词 '{kw}': 检索失败 - {e}")

    print(f"\n  专利合计（去重后）: {len(all_patents)} 条")
    return all_patents


# ============================================================
# 步骤 3: 学者/团队识别
# ============================================================

def step3_identify_scholars(papers, patents, focus_orgs):
    print(f"\n{'='*60}")
    print(f"步骤 3: 学者/团队识别")
    print(f"{'='*60}\n")

    # 统计论文作者
    author_count = Counter()
    author_papers = defaultdict(list)
    for p in papers:
        authors = p.get("authors", [])
        for author in authors:
            if isinstance(author, dict):
                name = author.get("name", author.get("nameEn", ""))
            else:
                name = str(author)
            if name:
                author_count[name] += 1
                author_papers[name].append(p.get("enName", ""))

    top_authors = [
        {"name": name, "paper_count": count}
        for name, count in author_count.most_common(10)
    ]
    print(f"  论文高产作者 Top-5:")
    for a in top_authors[:5]:
        print(f"    - {a['name']} ({a['paper_count']} 篇)")

    # 统计专利申请人
    applicant_count = Counter()
    for pat in patents:
        applicant = pat.get("applicant", pat.get("assignee", ""))
        if applicant:
            applicant_count[applicant] += 1

    patent_applicants = [
        {"name": name, "patent_count": count}
        for name, count in applicant_count.most_common(10)
    ]
    if patent_applicants:
        print(f"\n  专利活跃申请人 Top-5:")
        for a in patent_applicants[:5]:
            print(f"    - {a['name']} ({a['patent_count']} 件)")

    # 交叉比对
    author_names = set(n.lower() for n in author_count.keys())
    applicant_names = set(n.lower() for n in applicant_count.keys())
    bridge_names = author_names & applicant_names

    if focus_orgs:
        for org in focus_orgs:
            org_lower = org.lower()
            for applicant in applicant_count.keys():
                if org_lower in applicant.lower():
                    bridge_names.add(applicant.lower())

    bridge_scholars = []
    for name in bridge_names:
        bridge_scholars.append({
            "name": name,
            "paper_count": author_count.get(name, 0),
            "patent_count": applicant_count.get(name, 0),
        })

    if bridge_scholars:
        print(f"\n  跨学术-产业桥梁人物: {len(bridge_scholars)} 个")
        for b in bridge_scholars:
            print(f"    - {b['name']} (论文: {b['paper_count']}, "
                  f"专利: {b['patent_count']})")

    # 查询 Top-5 论文作者的学者画像
    scholar_profiles = []
    print(f"\n  查询学者画像...")
    for author_info in top_authors[:5]:
        name = author_info["name"]
        try:
            r = requests.post(
                f"{BASE}/v1/paper-server/scholar/search",
                headers=HEADERS_JSON,
                json={"name": name, "page": 1, "pageSize": 3}
            )
            r.raise_for_status()
            data = r.json()
            items = data.get("data", {}).get("items", [])
            if items:
                scholar = items[0]
                scholar_profiles.append({
                    "name": name,
                    "nameEn": scholar.get("nameEn", ""),
                    "nameZh": scholar.get("nameZh", ""),
                    "institution": (scholar.get("scholarOrgNameEn", "") or
                                    scholar.get("scholarOrgNameZh", "")),
                    "paperNums": scholar.get("paperNums", 0),
                    "citationNums": scholar.get("citationNums", 0),
                    "hIndex": scholar.get("hIndex", 0),
                    "paper_count_in_topic": author_info["paper_count"],
                })
                print(f"    {name}: h={scholar.get('hIndex', 0)}, "
                      f"机构={scholar.get('scholarOrgNameEn', '')[:30]}")
        except Exception as e:
            print(f"    {name}: 查询失败 - {e}")

    return {
        "top_authors": top_authors,
        "patent_applicants": patent_applicants,
        "bridge_scholars": bridge_scholars,
        "scholar_profiles": scholar_profiles,
    }


# ============================================================
# 步骤 4: 交叉分析与报告生成
# ============================================================

def step4_cross_analyze(config, papers, patents, scholar_result):
    print(f"\n{'='*60}")
    print(f"步骤 4: 交叉分析与报告生成")
    print(f"{'='*60}\n")

    keywords = config["keywords"]

    # ── 4a. 年度趋势分析 ──
    print("  4a. 年度趋势分析...")
    paper_years = Counter()
    for p in papers:
        year = p.get("coverDateStart", "")[:4]
        if year and year.isdigit():
            paper_years[int(year)] += 1

    patent_years = Counter()
    for pat in patents:
        date_str = (pat.get("applicationDate", "") or
                    pat.get("publicationDate", "") or
                    pat.get("date", ""))
        year = str(date_str)[:4]
        if year and year.isdigit():
            patent_years[int(year)] += 1

    all_years = sorted(set(list(paper_years.keys()) +
                           list(patent_years.keys())))
    trend = []
    for y in all_years:
        trend.append({
            "year": y,
            "paper_count": paper_years.get(y, 0),
            "patent_count": patent_years.get(y, 0),
        })
        print(f"    {y}: 论文 {paper_years.get(y, 0)}, "
              f"专利 {patent_years.get(y, 0)}")

    # ── 4b. 技术点交叉分析 ──
    print("\n  4b. 技术点交叉分析...")

    paper_terms = Counter()
    for p in papers:
        title = p.get("enName", "").lower()
        for kw in keywords:
            if kw.lower() in title:
                paper_terms[kw.lower()] += 1
        words = [w for w in title.split() if len(w) > 4]
        paper_terms.update(words)

    patent_terms = Counter()
    for pat in patents:
        raw_title = pat.get("title") or pat.get("name") or ""
        title = (raw_title if isinstance(raw_title, str) else str(raw_title)).lower()
        for kw in keywords:
            if kw.lower() in title:
                patent_terms[kw.lower()] += 1
        words = [w for w in title.split() if len(w) > 4]
        patent_terms.update(words)

    common_terms = set(paper_terms.keys()) & set(patent_terms.keys())
    patented_tech = [
        {"term": t, "paper_freq": paper_terms[t],
         "patent_freq": patent_terms[t]}
        for t in common_terms
        if paper_terms[t] >= 2 and patent_terms[t] >= 1
    ]
    patented_tech.sort(key=lambda x: x["patent_freq"], reverse=True)
    print(f"    已专利化技术点: {len(patented_tech)} 个")

    paper_only = set(paper_terms.keys()) - set(patent_terms.keys())
    academic_opps = [
        {"term": t, "paper_freq": paper_terms[t]}
        for t in paper_only
        if paper_terms[t] >= 3
    ]
    academic_opps.sort(key=lambda x: x["paper_freq"], reverse=True)
    print(f"    纯学术机会: {len(academic_opps)} 个")

    # ── 4c. 成熟度评估 ──
    print("\n  4c. 成熟度评估...")
    total_papers = len(papers)
    total_patents = len(patents)

    if total_papers == 0:
        maturity = "数据不足"
        maturity_detail = "未检索到学术论文，无法评估。"
    elif total_patents == 0:
        maturity = "早期学术阶段"
        maturity_detail = (
            f"检索到 {total_papers} 篇论文但无相关专利，"
            "技术仍处于学术研究阶段，尚未进入产业化。"
        )
    else:
        ratio = total_patents / total_papers
        if ratio < 0.1:
            maturity = "学术主导期"
            maturity_detail = (
                f"论文/专利比 = {total_papers}:{total_patents}，"
                f"专利占比仅 {ratio:.0%}。技术以学术研究为主，"
                "产业化刚起步，存在大量未被专利保护的研究成果。"
            )
        elif ratio < 0.5:
            maturity = "技术转化期"
            maturity_detail = (
                f"论文/专利比 = {total_papers}:{total_patents}，"
                f"专利占比 {ratio:.0%}。产业界已开始关注，"
                "部分核心技术已被专利保护，但仍有可观的空白领域。"
            )
        elif ratio < 1.0:
            maturity = "产业加速期"
            maturity_detail = (
                f"论文/专利比 = {total_papers}:{total_patents}，"
                f"专利占比 {ratio:.0%}。产业化程度较高，"
                "核心技术大部分已被专利覆盖，新进入者需注意 IP 壁垒。"
            )
        else:
            maturity = "产业成熟期"
            maturity_detail = (
                f"论文/专利比 = {total_papers}:{total_patents}，"
                "专利数量超过论文。技术已充分商业化，"
                "IP 竞争激烈，建议关注改进型专利或寻找细分方向突破。"
            )

    print(f"    成熟度判断: {maturity}")

    analysis = {
        "trend": trend,
        "patented_tech": patented_tech[:15],
        "academic_opportunities": academic_opps[:15],
        "patent_applicants": scholar_result.get("patent_applicants", []),
        "bridge_scholars": scholar_result.get("bridge_scholars", []),
        "scholar_profiles": scholar_result.get("scholar_profiles", []),
        "maturity": maturity,
        "maturity_detail": maturity_detail,
    }

    # ── 4d. 生成报告 ──
    print("\n  4d. 生成报告...")
    report = format_report(keywords, papers, patents, analysis)
    return report, analysis


def format_report(keywords, papers, patents, analysis):
    """格式化输出交叉分析报告（Markdown）。"""
    lines = []

    lines.append("# 专利-论文交叉分析报告")
    lines.append(f"\n> 技术方向: {', '.join(keywords)}")
    lines.append(f"> 生成时间: {datetime.now().isoformat()}")
    lines.append(f"> 检索论文数: {len(papers)}, 检索专利数: {len(patents)}")

    # 1. 趋势对比
    lines.append("\n## 1. 论文 vs 专利数量趋势对比\n")
    trend = analysis.get("trend", [])
    if trend:
        lines.append("| 年份 | 论文数 | 专利数 | 论文/专利比 |")
        lines.append("|------|--------|--------|------------|")
        for t in trend:
            ratio = (f"{t['paper_count']/t['patent_count']:.1f}"
                     if t["patent_count"] > 0 else "-")
            lines.append(
                f"| {t['year']} | {t['paper_count']} | "
                f"{t['patent_count']} | {ratio} |"
            )
    else:
        lines.append("无足够的时间数据生成趋势。")

    # 2. 已专利化技术点
    lines.append("\n## 2. 已专利化技术点\n")
    lines.append("以下技术主题同时出现在学术论文和专利中，"
                 "表明已被产业界关注并保护：\n")
    patented = analysis.get("patented_tech", [])
    if patented:
        lines.append("| # | 技术术语 | 论文出现频次 | 专利出现频次 |")
        lines.append("|---|---------|-------------|-------------|")
        for i, t in enumerate(patented[:10], 1):
            lines.append(
                f"| {i} | {t['term']} | {t['paper_freq']} | "
                f"{t['patent_freq']} |"
            )
    else:
        lines.append("未发现同时出现在论文和专利中的技术术语。")

    # 3. 纯学术机会
    lines.append("\n## 3. 纯学术机会（未专利化研究方向）\n")
    lines.append("以下技术主题仅在论文中出现，尚无对应专利，"
                 "可能是潜在的知识产权布局机会：\n")
    opps = analysis.get("academic_opportunities", [])
    if opps:
        lines.append("| # | 技术术语 | 论文出现频次 | 建议 |")
        lines.append("|---|---------|-------------|------|")
        for i, o in enumerate(opps[:10], 1):
            suggestion = ("高频出现，建议优先评估"
                          if o["paper_freq"] >= 5 else "值得关注")
            lines.append(
                f"| {i} | {o['term']} | {o['paper_freq']} | "
                f"{suggestion} |"
            )
    else:
        lines.append("所有高频论文技术点均已有对应专利覆盖。")

    # 4. 活跃专利申请人
    lines.append("\n## 4. 活跃专利申请人\n")
    applicants = analysis.get("patent_applicants", [])
    if applicants:
        lines.append("| # | 申请人 | 专利数量 |")
        lines.append("|---|--------|---------|")
        for i, a in enumerate(applicants[:10], 1):
            lines.append(
                f"| {i} | {a['name']} | {a['patent_count']} |"
            )
    else:
        lines.append("未提取到专利申请人信息。")

    bridge = analysis.get("bridge_scholars", [])
    if bridge:
        lines.append("\n### 跨学术-产业桥梁人物\n")
        lines.append("以下人物/机构同时出现在论文作者和专利申请人中：\n")
        lines.append("| 名称 | 相关论文数 | 相关专利数 |")
        lines.append("|------|----------|----------|")
        for b in bridge:
            lines.append(
                f"| {b['name']} | {b['paper_count']} | "
                f"{b['patent_count']} |"
            )

    profiles = analysis.get("scholar_profiles", [])
    if profiles:
        lines.append("\n### 领域高产学者画像\n")
        lines.append("| # | 学者 | 机构 | h-index | 总论文数 "
                     "| 总引用数 | 本领域论文数 |")
        lines.append("|---|------|------|---------|---------|"
                     "---------|------------|")
        for i, s in enumerate(profiles, 1):
            lines.append(
                f"| {i} | {s['nameEn'] or s['name']} | "
                f"{s['institution']} | {s['hIndex']} | "
                f"{s['paperNums']} | {s['citationNums']} | "
                f"{s['paper_count_in_topic']} |"
            )

    # 5. 成熟度评估
    lines.append("\n## 5. 技术转化成熟度评估\n")
    lines.append(f"**阶段判断: {analysis.get('maturity', '未知')}**\n")
    lines.append(analysis.get("maturity_detail", ""))

    # 成熟度参考标准
    lines.append("\n### 成熟度参考标准\n")
    lines.append("| 阶段 | 专利/论文比 | 特征 |")
    lines.append("|------|-----------|------|")
    lines.append("| 早期学术阶段 | 0% | 无相关专利 |")
    lines.append("| 学术主导期 | < 10% | 学术研究为主，产业化刚起步 |")
    lines.append("| 技术转化期 | 10%-50% | 产业界开始关注，部分技术已被保护 |")
    lines.append("| 产业加速期 | 50%-100% | 核心技术大部分已被专利覆盖 |")
    lines.append("| 产业成熟期 | > 100% | 专利超过论文，IP 竞争激烈 |")

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  专利-论文交叉分析")
    print(f"  技术方向: {', '.join(config['keywords'])}")
    if config.get("focus_orgs"):
        print(f"  重点机构: {', '.join(config['focus_orgs'])}")
    print(f"{'#'*60}")

    # 步骤 1: 论文检索
    papers = step1_search_papers(config)

    # 步骤 2: 专利检索
    patents = step2_search_patents(config)

    if not papers and not patents:
        print("\n未检索到任何论文或专利，退出。")
        sys.exit(1)

    # 步骤 3: 学者/团队识别
    scholar_result = step3_identify_scholars(
        papers, patents, config.get("focus_orgs", [])
    )

    # 步骤 4: 交叉分析
    report, analysis = step4_cross_analyze(
        config, papers, patents, scholar_result
    )

    # 输出报告
    print("\n" + report)

    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    kw_tag = "_".join(config["keywords"][:3])
    output_file = f"patent_paper_cross_{kw_tag}_{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存到: {output_file}")

    # 保存原始数据
    data_file = f"patent_paper_cross_{kw_tag}_{timestamp}_data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump({
            "config": config,
            "paper_count": len(papers),
            "patent_count": len(patents),
            "analysis": analysis,
        }, f, ensure_ascii=False, indent=2)
    print(f"原始数据已保存到: {data_file}")


if __name__ == "__main__":
    main()
```

---

## 使用技巧

### 关键词选择

```python
# 推荐: 3-8 个专业术语，兼顾学术和产业用语
keywords = ["perovskite", "solar cell", "stability", "encapsulation"]
keywords = ["solid state battery", "electrolyte", "lithium"]
keywords = ["CRISPR", "gene editing", "delivery"]

# 不推荐: 太笼统
keywords = ["energy", "material"]
```

### 重点机构筛选

```python
# 设置重点关注的公司/机构，用于专利申请人匹配
config = {
    "keywords": ["perovskite", "solar cell"],
    "focus_orgs": ["LONGi", "First Solar", "Oxford PV"],
}
```

### 扩大专利检索范围

专利 API 参数较简单（仅 keyword + 分页），若结果不足，可以：

```python
# 方法 1: 使用多个关键词组合
patents = search_patents_multi_keyword(
    ["perovskite solar cell", "perovskite stability",
     "perovskite encapsulation"],
    page_size=20
)

# 方法 2: 翻页获取更多结果
all_patents = []
for page in range(1, 4):
    patents = search_patents("perovskite solar cell", page=page, page_size=20)
    all_patents.extend(patents)
```

### 分段执行

对于网络不稳定的环境，可以将步骤拆开单独执行：

```python
# 步骤 1+2 结果保存
papers = step1_search_papers(config)
patents = step2_search_patents(config)
with open("step12_data.json", "w") as f:
    json.dump({"papers": papers, "patents": patents}, f, ensure_ascii=False)

# 后续步骤从文件加载
with open("step12_data.json") as f:
    saved = json.load(f)
papers, patents = saved["papers"], saved["patents"]
scholar_result = step3_identify_scholars(papers, patents, [])
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 论文检索结果为空 | 关键词太窄或时间范围太小 | 使用更通用的英文术语，放宽时间限制 |
| 专利检索结果为空 | 关键词与专利库不匹配 | 尝试产业界常用术语而非学术缩写 |
| 专利 API 返回异常 | 传入了不支持的参数（如 `rerank`、`type`） | 专利 API 仅支持 `keyword`、`page`、`pageSize` 三个参数 |
| 桥梁学者识别为空 | 论文作者和专利申请人的名称格式不同 | 正常现象，名称匹配依赖字符串比对，后续版本将引入模糊匹配 |
| 成熟度判断不准确 | 样本量太少 | 增大 `paper_top_n` 和 `patent_top_n`，或扩大时间范围 |
| 技术点提取不精确 | 基于词频的简单提取 | 将结果作为参考起点，结合领域知识人工修正 |
| 响应含多行 JSON | paper-search 返回 streaming 格式 | 取第一行解析：`json.loads(r.text.split('\n')[0])` |
| 401 Unauthorized | accessKey 无效 | 确认 ACCESS_KEY 正确，检查 `~/.openclaw/openclaw.json` 配置 |
| 学者搜索无结果 | 姓名拼写与数据库不匹配 | 尝试全名或不同拼写形式 |

---

## 搭配使用

- **bohrium-paper-search** — 本技能的论文检索能力来源
- **bohrium-paper-search (patent)** — 本技能的专利检索能力来源
- **bohrium-scholar-search** — 本技能的学者画像能力来源
- **literature-review** — 对发现的纯学术机会方向做深入文献综述
- **scholar-profiler** — 对桥梁学者做更全面的学者画像分析
- **tech-radar** — 持续监控技术方向的专利和论文动态
- **tech-compare** — 对多条技术路线分别进行交叉分析后对比
