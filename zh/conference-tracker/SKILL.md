---
name: conference-tracker
description: "Academic conference and event tracking by searching for latest conference info, accepted papers, and keynote speakers. Use when: user wants to decide which conferences to attend, track conference deadlines, or find relevant sessions. NOT for: paper content search (use bohrium-paper-search), competitor monitoring (use tech-radar)."
---

# SKILL: 会议/学术活动追踪 (Conference Tracker)

## 概述

编排 `bohrium-web-search`、`bohrium-paper-search`、`bohrium-scholar-search` 三个原子技能，对学术会议和活动进行全方位追踪。从会议信息检索、录用论文分析、到主题演讲者查询，输出完整的会议日历和与用户研究方向的相关性分析。

**编排流程：**

```
会议列表/领域关键词 + 用户研究方向
        │
        ▼
┌─────────────────────┐
│  web-search          │  搜索会议最新信息（日期、CFP、录用论文列表）
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  paper-search        │  检索会议已发表论文，分析研究热点
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  scholar-search      │  查询主题/特邀演讲者背景
└────────┬────────────┘
         │
         ▼
    会议追踪报告
    ├─ 会议日历（时间线）
    ├─ 与用户方向的相关性排名
    ├─ 值得关注的 Session / Workshop
    └─ 重要截止日期提醒
```

**适用场景：**

- 决定参加哪些学术会议
- 追踪会议投稿截止日期（CFP deadline）
- 了解会议录用论文和研究趋势
- 查找特定方向的 workshop 和 session
- 了解会议主题/特邀演讲者

**不适用：**

- 单纯的论文内容搜索 → `bohrium-paper-search`
- 竞品技术监控 → `tech-radar`
- 单纯查找学者信息 → `bohrium-scholar-search`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"conference-tracker": {
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
            的 conference-tracker.env.ACCESS_KEY 中填入从 https://bohrium.dp.tech
            个人设置页获取的 AccessKey，然后重启 OpenClaw 会话。」
```

**重要：** 不要把 AccessKey 另存到其他文件或写死到代码，统一通过 OpenClaw 环境变量注入。

---

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `conferences` | list[str] | 否 | 会议名称或缩写列表，如 `["NeurIPS", "ICML", "ICLR"]` |
| `field_keywords` | list[str] | 否 | 领域关键词（当不指定会议时，自动匹配相关会议） |
| `research_direction` | string | 是 | 用户自身研究方向（用于相关性排序） |
| `year` | int | 否 | 目标年份，默认当前年份 |

> **注意：** `conferences` 和 `field_keywords` 至少填一个。

## 输出内容

| 板块 | 内容 |
|------|------|
| 会议日历 | 按时间排列的会议信息：名称、日期、地点、投稿截止日期、录用率 |
| 相关性排名 | 各会议/session 与用户研究方向的匹配度评分和理由 |
| 值得关注的 Session | 与用户方向高度相关的 workshop、session、tutorial 列表 |
| 重要截止日期 | 按时间排序的 deadline 提醒：投稿、注册、camera-ready |
| 主题演讲者 | Keynote/invited speaker 列表及其研究背景 |

---

## 数据质量控制

### 录用率数据标注

录用率等统计数据**必须标注来源和年份**：
- ✅ "NeurIPS 2025 录用率: 25.8%（来源：官方公告）"
- ✅ "ICML 录用率: ~28%（估计值，基于近三年平均）"
- ❌ "录用率约 20%"（无来源、无年份）

### 截止日期可靠性

- web-search 获取的截止日期可能已过期或不准确
- 每个日期必须标注来源 URL 和检索日期
- 如果距投稿截止日期 < 30 天，必须加粗提醒并建议用户去官网二次确认

### 禁止的行为

- ❌ 给出录用率/截止日期而不标注来源和年份
- ❌ 将过期的会议信息作为推荐输出
- ❌ 相关性排名不说明具体匹配点（不能只说"与你的方向相关"）

---

## 各接口说明

### 接口 1：会议信息搜索 (`web-search`)

| 操作 | 方法 | 端点 |
|------|------|------|
| 网页搜索 | GET | `/openapi/v1/search/web?q=QUERY&num=N` |

**请求参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `q` | string | 搜索关键词（如 `"NeurIPS 2026 call for papers deadline"`） |
| `num` | int | 返回结果数（1-10），推荐 5 |

**返回关键字段（`organic_results[]`）：**

| 字段 | 说明 |
|------|------|
| `title` | 页面标题 |
| `link` | 页面 URL |
| `snippet` | 摘要片段 |
| `position` | 排名位置 |

### 接口 2：会议论文检索 (`paper-search`)

| 操作 | 方法 | 端点 |
|------|------|------|
| 关键词检索 | POST | `/openapi/v1/paper/rag/pass/keyword` |

**请求参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `words` | string[] | 关键词列表（会议名 + 研究方向） |
| `question` | string | 自然语言检索问题 |
| `type` | int | 检索类型，固定为 `5`（全方位检索） |
| `startTime` | string | 起始日期 `YYYY-MM-DD` |
| `endTime` | string | 截止日期 `YYYY-MM-DD` |
| `pageSize` | int | 返回论文数量 |

**返回关键字段（`data[]`）：**

| 字段 | 说明 |
|------|------|
| `doi` | DOI |
| `enName` | 英文标题 |
| `enAbstract` | 英文摘要 |
| `authors` | 作者列表 |
| `coverDateStart` | 发表日期 |
| `publicationEnName` | 期刊/会议名 |
| `impactFactor` | 影响因子 |
| `citationNums` | 被引次数 |

### 接口 3：演讲者查询 (`scholar-search`)

| 操作 | 方法 | 端点 |
|------|------|------|
| 学者搜索 | POST | `/openapi/v1/paper-server/scholar/search` |
| 学者详情 | GET | `/openapi/v1/paper-server/scholar/info?scholarId=xxx` |

**搜索请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 学者姓名关键词（1~99 字符） |
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
| `scholarOrgNameEn` | 所属机构 |
| `isHighCited` | 是否高被引学者 |

**详情返回额外字段：**

| 字段 | 说明 |
|------|------|
| `researchDirection` | 研究方向数组 |
| `educationBackground` | 教育经历 |
| `workExperience` | 工作经历 |

---

## 完整编排脚本

以下 Python 脚本实现端到端的会议追踪流程，包括信息采集、论文分析、演讲者查询和报告生成。

```python
#!/usr/bin/env python3
"""
会议/学术活动追踪 (Conference Tracker)
编排 web-search + paper-search + scholar-search，输出会议追踪报告。

用法:
    export ACCESS_KEY="your_access_key"
    python conference_tracker.py
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# ─── 配置 ───────────────────────────────────────────────

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误：未设置 ACCESS_KEY 环境变量。")
    print("请在 ~/.openclaw/openclaw.json 中配置 conference-tracker.env.ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"

H_JSON = {"accessKey": AK, "Content-Type": "application/json"}
H_AK   = {"accessKey": AK}


# ─── 用户可修改区域 ─────────────────────────────────────

CONFIG = {
    # 目标会议列表（缩写或全称均可）
    "conferences": [
        "NeurIPS",
        "ICML",
        "ICLR",
        "AAAI",
        "ACL",
    ],
    # 领域关键词（当不指定会议时用于自动匹配）
    "field_keywords": [
        "machine learning",
        "natural language processing",
        "deep learning",
    ],
    # 用户自身研究方向（用于相关性排序）
    "research_direction": "graph neural networks for molecular property prediction",
    # 目标年份
    "year": datetime.now().year,
}


# ─── 步骤 1：搜索会议最新信息 ───────────────────────────

def search_conference_info(conference_name, year):
    """
    通过 web-search 搜索会议的最新信息，包括日期、地点、CFP、录用论文。

    Args:
        conference_name: 会议名称或缩写
        year: 目标年份

    Returns:
        dict: {name, queries_results: [{query, results}]}
    """
    print(f"  搜索: {conference_name} {year}")

    # 构建多组搜索查询，覆盖不同维度的信息
    queries = [
        f"{conference_name} {year} conference dates location deadline",
        f"{conference_name} {year} call for papers CFP submission",
        f"{conference_name} {year} accepted papers keynote speakers",
        f"{conference_name} {year} workshops tutorials sessions",
    ]

    conf_info = {
        "name": conference_name,
        "year": year,
        "search_results": [],
        "dates": [],
        "deadlines": [],
        "location": "",
        "urls": [],
    }

    for query in queries:
        try:
            r = requests.get(
                f"{BASE}/v1/search/web",
                headers=H_AK,
                params={"q": query, "num": 5},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("organic_results", [])

            for res in results:
                conf_info["search_results"].append({
                    "query": query,
                    "title": res.get("title", ""),
                    "url": res.get("link", ""),
                    "snippet": res.get("snippet", ""),
                })

                # 收集官方 URL
                url = res.get("link", "")
                if url and url not in conf_info["urls"]:
                    conf_info["urls"].append(url)

        except requests.RequestException as e:
            print(f"    [WARN] 搜索失败 ({query[:40]}...): {e}")

    print(f"    找到 {len(conf_info['search_results'])} 条搜索结果")
    return conf_info


def step1_search_all_conferences(config):
    """
    步骤 1：搜索所有目标会议的最新信息。

    如果未指定会议列表，则用领域关键词搜索相关会议。
    """
    year = config["year"]

    print(f"\n{'='*60}")
    print(f"步骤 1/3：搜索会议最新信息")
    print(f"  目标年份: {year}")
    print(f"{'='*60}\n")

    conferences = config.get("conferences", [])

    # 如果未指定会议，先通过领域关键词搜索相关会议
    if not conferences and config.get("field_keywords"):
        print("  未指定会议列表，通过领域关键词自动匹配...\n")
        keywords = " ".join(config["field_keywords"])
        try:
            r = requests.get(
                f"{BASE}/v1/search/web",
                headers=H_AK,
                params={
                    "q": f"top conferences {year} {keywords}",
                    "num": 5,
                },
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()

            # 从搜索结果中提取会议名称（启发式）
            for res in data.get("organic_results", []):
                snippet = res.get("snippet", "") + " " + res.get("title", "")
                print(f"    参考: {res.get('title', '')[:80]}")

        except requests.RequestException as e:
            print(f"  [WARN] 关键词匹配失败: {e}")

        # 回退到配置中的领域关键词作为会议搜索
        conferences = config.get("field_keywords", [])

    # 逐个会议搜索信息
    all_conf_info = []
    for conf in conferences:
        info = search_conference_info(conf, year)
        all_conf_info.append(info)

    print(f"\n  共追踪 {len(all_conf_info)} 个会议/方向")
    return all_conf_info


# ─── 步骤 2：检索会议发表论文 ───────────────────────────

def search_conference_papers(conference_name, research_direction,
                             year, page_size=15):
    """
    通过 paper-search 检索会议已发表论文，并分析与用户方向的相关性。

    Args:
        conference_name: 会议名称
        research_direction: 用户研究方向
        year: 目标年份
        page_size: 返回论文数量

    Returns:
        dict: {papers, topic_distribution, relevance_score}
    """
    # 用会议名 + 用户方向构建检索请求
    words = conference_name.split() + research_direction.split()[:5]
    question = (
        f"papers published at {conference_name} related to "
        f"{research_direction}"
    )

    # 时间范围：目标年份前后各半年
    start_time = f"{year - 1}-07-01"
    end_time = f"{year}-12-31"

    try:
        r = requests.post(
            f"{BASE}/v1/paper/rag/pass/keyword",
            headers=H_JSON,
            json={
                "words": words,
                "question": question,
                "type": 5,
                "startTime": start_time,
                "endTime": end_time,
                "pageSize": page_size,
            },
            timeout=30,
        )
        r.raise_for_status()

        text = r.text.strip()
        first_line = text.split("\n")[0]
        data = json.loads(first_line)

        if data.get("code") != 0:
            print(f"    [WARN] 论文检索失败: {data.get('message', '')}")
            return {"papers": [], "topic_distribution": {},
                    "relevance_score": 0}

        papers = data.get("data", [])

    except Exception as e:
        print(f"    [WARN] 论文检索异常 ({conference_name}): {e}")
        return {"papers": [], "topic_distribution": {},
                "relevance_score": 0}

    # 分析论文主题分布
    topic_counter = Counter()
    for p in papers:
        title = p.get("enName", "").lower()
        words_in_title = [
            w for w in title.split()
            if len(w) > 3 and w not in STOP_WORDS
        ]
        topic_counter.update(words_in_title)

    topic_distribution = dict(topic_counter.most_common(10))

    # 计算与用户方向的相关性评分（基于关键词重叠）
    user_keywords = set(research_direction.lower().split())
    paper_keywords = set(topic_counter.keys())
    overlap = user_keywords & paper_keywords
    relevance_score = (
        len(overlap) / max(len(user_keywords), 1) * 100
    )

    return {
        "papers": papers,
        "topic_distribution": topic_distribution,
        "relevance_score": round(relevance_score, 1),
    }


# 英文停用词
STOP_WORDS = {
    "the", "and", "for", "with", "from", "that", "this", "which",
    "their", "have", "been", "were", "are", "was", "has", "its",
    "into", "using", "based", "approach", "method", "methods",
    "study", "analysis", "research", "paper", "novel", "new",
    "through", "between", "about", "also", "than", "more",
    "under", "over", "after", "before", "other", "such", "each",
    "when", "where", "what", "both", "some", "only", "most",
    "learning", "model", "models", "data", "results", "proposed",
    "performance", "show", "demonstrate", "achieve",
}


def step2_search_all_papers(all_conf_info, config):
    """
    步骤 2：为每个会议检索相关论文。
    """
    research_direction = config["research_direction"]
    year = config["year"]

    print(f"\n{'='*60}")
    print(f"步骤 2/3：检索会议发表论文")
    print(f"  用户研究方向: {research_direction}")
    print(f"{'='*60}\n")

    all_paper_analysis = {}
    for conf_info in all_conf_info:
        conf_name = conf_info["name"]
        print(f"  检索: {conf_name} 相关论文...")

        analysis = search_conference_papers(
            conf_name, research_direction, year
        )
        all_paper_analysis[conf_name] = analysis

        paper_count = len(analysis["papers"])
        relevance = analysis["relevance_score"]
        print(f"    论文: {paper_count} 篇, "
              f"相关性: {relevance}%")

        # 显示 Top-3 论文
        sorted_papers = sorted(
            analysis["papers"],
            key=lambda p: p.get("citationNums", 0),
            reverse=True,
        )
        for p in sorted_papers[:3]:
            print(f"    - {p.get('enName', '')[:70]}... "
                  f"(引用: {p.get('citationNums', 0)})")

    return all_paper_analysis


# ─── 步骤 3：查询主题/特邀演讲者 ────────────────────────

def search_speaker(speaker_name):
    """
    通过 scholar-search 查询演讲者的学术背景。

    Args:
        speaker_name: 演讲者姓名

    Returns:
        dict: 演讲者信息
    """
    result = {
        "name": speaker_name,
        "found": False,
        "info": {},
    }

    try:
        # 搜索学者
        r = requests.post(
            f"{BASE}/v1/paper-server/scholar/search",
            headers=H_JSON,
            json={"name": speaker_name, "page": 1, "pageSize": 3},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        items = data.get("data", {}).get("items", [])

        if not items:
            return result

        scholar = items[0]
        scholar_id = scholar.get("scholarId", "")

        result["found"] = True
        result["info"] = {
            "scholar_id": scholar_id,
            "name_en": scholar.get("nameEn", ""),
            "name_zh": scholar.get("nameZh", ""),
            "org": (scholar.get("scholarOrgNameEn", "")
                    or scholar.get("scholarOrgNameZh", "")),
            "paper_count": scholar.get("paperNums", 0),
            "citation_count": scholar.get("citationNums", 0),
            "h_index": scholar.get("hIndex", 0),
            "is_high_cited": scholar.get("isHighCited", False),
        }

        # 获取详细信息
        if scholar_id:
            r2 = requests.get(
                f"{BASE}/v1/paper-server/scholar/info",
                headers=H_AK,
                params={"scholarId": scholar_id},
                timeout=30,
            )
            if r2.status_code == 200:
                detail = r2.json().get("data", {})
                result["info"]["research_direction"] = detail.get(
                    "researchDirection", []
                )

    except requests.RequestException as e:
        print(f"    [WARN] 学者查询失败 ({speaker_name}): {e}")

    return result


def extract_speakers_from_search(all_conf_info):
    """
    从步骤 1 的搜索结果中，启发式提取可能的演讲者姓名。

    策略：搜索结果中出现 "keynote" / "invited" / "speaker" 附近的人名。
    这里采用简化方案：再做一次专门搜索。
    """
    speakers_by_conf = {}

    for conf_info in all_conf_info:
        conf_name = conf_info["name"]
        year = conf_info["year"]

        print(f"  搜索 {conf_name} {year} 的演讲者...")

        try:
            r = requests.get(
                f"{BASE}/v1/search/web",
                headers=H_AK,
                params={
                    "q": (f"{conf_name} {year} keynote speaker "
                          f"invited talk"),
                    "num": 5,
                },
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()

            speakers_by_conf[conf_name] = {
                "search_results": [
                    {
                        "title": res.get("title", ""),
                        "url": res.get("link", ""),
                        "snippet": res.get("snippet", ""),
                    }
                    for res in data.get("organic_results", [])
                ]
            }

            for res in data.get("organic_results", [])[:2]:
                print(f"    {res.get('title', '')[:70]}")

        except requests.RequestException as e:
            print(f"    [WARN] 演讲者搜索失败: {e}")
            speakers_by_conf[conf_name] = {"search_results": []}

    return speakers_by_conf


def step3_search_speakers(all_conf_info, speaker_names=None):
    """
    步骤 3：查询主题/特邀演讲者信息。

    如果提供了 speaker_names，直接查询这些学者。
    否则先从搜索结果中提取演讲者线索。
    """
    print(f"\n{'='*60}")
    print(f"步骤 3/3：查询主题/特邀演讲者")
    print(f"{'='*60}\n")

    # 先搜索各会议的演讲者信息
    speakers_search = extract_speakers_from_search(all_conf_info)

    # 如果用户提供了演讲者姓名，查询其详细信息
    speaker_profiles = []
    if speaker_names:
        print(f"\n  查询 {len(speaker_names)} 位指定演讲者的学术背景...\n")
        for name in speaker_names:
            profile = search_speaker(name)
            speaker_profiles.append(profile)
            if profile["found"]:
                info = profile["info"]
                print(
                    f"    {info['name_en']}: "
                    f"h={info['h_index']}, "
                    f"论文={info['paper_count']}, "
                    f"引用={info['citation_count']}"
                )
            else:
                print(f"    {name}: 未找到匹配学者")

    return {
        "speakers_search": speakers_search,
        "speaker_profiles": speaker_profiles,
    }


# ─── 报告生成 ───────────────────────────────────────────

def compute_relevance_ranking(all_paper_analysis, research_direction):
    """
    根据论文分析结果，计算各会议与用户方向的相关性排名。
    """
    ranking = []
    for conf_name, analysis in all_paper_analysis.items():
        ranking.append({
            "conference": conf_name,
            "relevance_score": analysis["relevance_score"],
            "paper_count": len(analysis["papers"]),
            "top_topics": list(analysis["topic_distribution"].keys())[:5],
        })

    ranking.sort(key=lambda x: x["relevance_score"], reverse=True)
    return ranking


def generate_report(all_conf_info, all_paper_analysis,
                    speaker_data, config):
    """
    汇总所有分析结果，生成会议追踪报告（Markdown 格式）。
    """
    lines = []
    year = config["year"]
    direction = config["research_direction"]

    lines.append(f"# 学术会议追踪报告 {year}\n")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> 用户研究方向：{direction}")
    lines.append(f"> 追踪会议数：{len(all_conf_info)}")
    lines.append(f"> 数据来源：Bohrium OpenAPI "
                 f"(web-search + paper-search + scholar-search)\n")

    # ── 1. 会议日历（时间线） ──
    lines.append("## 1. 会议日历\n")
    lines.append("| # | 会议 | 年份 | 搜索到的信息条数 | 官方链接 |")
    lines.append("|---|------|------|-----------------|---------|")
    for i, conf in enumerate(all_conf_info, 1):
        info_count = len(conf["search_results"])
        first_url = conf["urls"][0] if conf["urls"] else "N/A"
        lines.append(
            f"| {i} | **{conf['name']}** | {conf['year']} | "
            f"{info_count} | {first_url} |"
        )
    lines.append("")

    # 为每个会议输出关键信息摘要
    for conf in all_conf_info:
        if conf["search_results"]:
            lines.append(f"### {conf['name']} {conf['year']}\n")
            # 取前 3 条最相关的搜索结果
            for res in conf["search_results"][:3]:
                title = res["title"][:80]
                snippet = res["snippet"][:150]
                url = res["url"]
                lines.append(f"- **{title}**")
                lines.append(f"  {snippet}")
                lines.append(f"  [{url}]({url})")
            lines.append("")

    # ── 2. 相关性排名 ──
    lines.append("## 2. 与研究方向的相关性排名\n")
    ranking = compute_relevance_ranking(all_paper_analysis, direction)
    lines.append("| 排名 | 会议 | 相关性评分 | 相关论文数 | 高频主题 |")
    lines.append("|------|------|-----------|-----------|---------|")
    for i, r in enumerate(ranking, 1):
        topics = ", ".join(r["top_topics"][:3]) if r["top_topics"] else "N/A"
        lines.append(
            f"| {i} | **{r['conference']}** | "
            f"{r['relevance_score']}% | "
            f"{r['paper_count']} | {topics} |"
        )
    lines.append("")

    if ranking and ranking[0]["relevance_score"] > 0:
        best = ranking[0]
        lines.append(
            f"**推荐**：**{best['conference']}** 与您的研究方向 "
            f"「{direction}」相关性最高（{best['relevance_score']}%），"
            f"建议优先关注。\n"
        )

    # ── 3. 值得关注的论文/Session ──
    lines.append("## 3. 值得关注的论文\n")
    for conf_name, analysis in all_paper_analysis.items():
        papers = analysis["papers"]
        if not papers:
            continue

        sorted_papers = sorted(
            papers,
            key=lambda p: p.get("citationNums", 0),
            reverse=True,
        )

        lines.append(f"### {conf_name}\n")
        lines.append("| # | 标题 | 期刊/会议 | 引用 | 日期 |")
        lines.append("|---|------|----------|------|------|")
        for j, p in enumerate(sorted_papers[:5], 1):
            title = p.get("enName", "")[:60]
            title = title.replace("|", "\\|")
            pub = (p.get("publicationEnName", "") or "N/A")[:25]
            pub = pub.replace("|", "\\|")
            cites = p.get("citationNums", 0)
            date = p.get("coverDateStart", "N/A")[:10]
            lines.append(
                f"| {j} | {title}... | {pub} | {cites} | {date} |"
            )
        lines.append("")

        # 主题分布
        if analysis["topic_distribution"]:
            top_5 = list(analysis["topic_distribution"].items())[:5]
            topic_str = ", ".join(
                f"{w}({c})" for w, c in top_5
            )
            lines.append(f"**主题分布**：{topic_str}\n")

    # ── 4. 重要截止日期 ──
    lines.append("## 4. 重要截止日期\n")
    lines.append(
        "> 以下截止日期信息来源于网络搜索，请以各会议官方网站为准。\n"
    )
    deadline_found = False
    for conf in all_conf_info:
        for res in conf["search_results"]:
            snippet_lower = res["snippet"].lower()
            if any(kw in snippet_lower for kw in [
                "deadline", "submission", "camera-ready",
                "registration", "notification",
            ]):
                if not deadline_found:
                    lines.append(
                        "| 会议 | 相关信息 | 来源 |"
                    )
                    lines.append("|------|---------|------|")
                    deadline_found = True

                snippet = res["snippet"][:120].replace("|", "\\|")
                url = res["url"]
                lines.append(
                    f"| {conf['name']} | {snippet} | "
                    f"[link]({url}) |"
                )

    if not deadline_found:
        lines.append(
            "未从搜索结果中提取到明确的截止日期信息。"
            "建议访问各会议官方网站查看。"
        )
    lines.append("")

    # ── 5. 主题/特邀演讲者 ──
    lines.append("## 5. 主题/特邀演讲者\n")

    # 搜索到的演讲者线索
    speakers_search = speaker_data.get("speakers_search", {})
    for conf_name, sdata in speakers_search.items():
        if sdata.get("search_results"):
            lines.append(f"### {conf_name}\n")
            for res in sdata["search_results"][:3]:
                title = res["title"][:80]
                snippet = res["snippet"][:150]
                url = res["url"]
                lines.append(f"- **{title}**")
                lines.append(f"  {snippet}")
                if url:
                    lines.append(f"  [{url}]({url})")
            lines.append("")

    # 演讲者详细画像
    profiles = speaker_data.get("speaker_profiles", [])
    found_profiles = [p for p in profiles if p["found"]]
    if found_profiles:
        lines.append("### 演讲者学术背景\n")
        lines.append(
            "| 姓名 | 机构 | h-index | 论文数 | 引用数 | "
            "高被引 | 研究方向 |"
        )
        lines.append(
            "|------|------|---------|--------|--------|"
            "--------|---------|"
        )
        for p in found_profiles:
            info = p["info"]
            dirs = ", ".join(
                info.get("research_direction", [])[:3]
            ) or "N/A"
            high_cited = "是" if info.get("is_high_cited") else "否"
            lines.append(
                f"| {info['name_en']} | {info.get('org', 'N/A')} | "
                f"{info['h_index']} | {info['paper_count']} | "
                f"{info['citation_count']} | {high_cited} | "
                f"{dirs} |"
            )
        lines.append("")

    return "\n".join(lines)


# ─── 主流程 ─────────────────────────────────────────────

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  学术会议追踪 (Conference Tracker)")
    print(f"  研究方向: {config['research_direction']}")
    print(f"  目标年份: {config['year']}")
    print(f"{'#'*60}")

    # 步骤 1：搜索会议信息
    all_conf_info = step1_search_all_conferences(config)
    if not all_conf_info:
        print("未找到任何会议信息，退出。")
        sys.exit(1)

    # 步骤 2：检索会议论文
    all_paper_analysis = step2_search_all_papers(all_conf_info, config)

    # 步骤 3：查询演讲者（可传入已知演讲者姓名）
    speaker_data = step3_search_speakers(all_conf_info)

    # 生成报告
    print(f"\n{'='*60}")
    print("  生成会议追踪报告...")
    print(f"{'='*60}\n")

    report = generate_report(
        all_conf_info, all_paper_analysis, speaker_data, config
    )
    print(report)

    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"conference_tracker_{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存到: {output_file}")

    return report


if __name__ == "__main__":
    main()
```

---

## 各步骤详解

### 步骤 1：搜索会议最新信息 (`web-search`)

通过多组关键词搜索每个会议的不同维度信息：

```python
# 会议日期和地点
r = requests.get(f"{BASE}/v1/search/web",
    headers=H_AK,
    params={"q": "NeurIPS 2026 conference dates location", "num": 5})

# 征稿信息
r = requests.get(f"{BASE}/v1/search/web",
    headers=H_AK,
    params={"q": "NeurIPS 2026 call for papers CFP deadline", "num": 5})

# 录用论文和演讲者
r = requests.get(f"{BASE}/v1/search/web",
    headers=H_AK,
    params={"q": "NeurIPS 2026 accepted papers keynote speakers", "num": 5})

# Workshop 和 Tutorial
r = requests.get(f"{BASE}/v1/search/web",
    headers=H_AK,
    params={"q": "NeurIPS 2026 workshops tutorials sessions", "num": 5})
```

**搜索策略**：每个会议发送 4 组查询，覆盖日期/地点、CFP/deadline、录用论文/演讲者、workshop/tutorial 四个维度，确保信息全面。

---

### 步骤 2：检索会议发表论文 (`paper-search`)

用会议名 + 用户研究方向组合检索，分析主题分布和相关性：

```python
r = requests.post(f"{BASE}/v1/paper/rag/pass/keyword",
    headers=H_JSON,
    json={
        "words": ["NeurIPS", "graph", "neural", "molecular"],
        "question": "papers at NeurIPS related to graph neural networks for molecular property prediction",
        "type": 5,
        "startTime": "2025-07-01",
        "endTime": "2026-12-31",
        "pageSize": 15,
    })
```

**相关性评分算法**：将用户研究方向拆词，与会议论文标题的高频词取交集，计算重叠比例作为相关性百分比。评分越高说明会议与用户方向越契合。

---

### 步骤 3：查询主题/特邀演讲者 (`scholar-search`)

先通过 web-search 搜索演讲者线索，再用 scholar-search 查询学术背景：

```python
# 搜索演讲者线索
r = requests.get(f"{BASE}/v1/search/web",
    headers=H_AK,
    params={"q": "NeurIPS 2026 keynote speaker invited talk", "num": 5})

# 查询学者详情
r = requests.post(f"{BASE}/v1/paper-server/scholar/search",
    headers=H_JSON,
    json={"name": "Yann LeCun", "page": 1, "pageSize": 3})

scholar_id = r.json()["data"]["items"][0]["scholarId"]

r = requests.get(f"{BASE}/v1/paper-server/scholar/info",
    headers=H_AK,
    params={"scholarId": scholar_id})
```

---

## curl 示例

```bash
AK="$ACCESS_KEY"
BASE="https://open.bohrium.com/openapi"

# ── 步骤 1：搜索会议信息 ──

# 会议日期和 CFP
curl -s "$BASE/v1/search/web?q=NeurIPS+2026+call+for+papers+deadline&num=5" \
  -H "accessKey: $AK"

# Workshop 信息
curl -s "$BASE/v1/search/web?q=NeurIPS+2026+workshops+tutorials+sessions&num=5" \
  -H "accessKey: $AK"

# 录用论文和演讲者
curl -s "$BASE/v1/search/web?q=NeurIPS+2026+accepted+papers+keynote+speakers&num=5" \
  -H "accessKey: $AK"

# ── 步骤 2：检索会议论文 ──

curl -s -X POST "$BASE/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["NeurIPS", "graph", "neural", "network", "molecular"],
    "question": "graph neural networks for molecular property prediction at NeurIPS",
    "type": 5,
    "startTime": "2025-07-01",
    "endTime": "2026-12-31",
    "pageSize": 15
  }'

# ── 步骤 3：查询演讲者 ──

# 搜索演讲者线索
curl -s "$BASE/v1/search/web?q=NeurIPS+2026+keynote+speaker+invited+talk&num=5" \
  -H "accessKey: $AK"

# 查询学者信息
curl -s -X POST "$BASE/v1/paper-server/scholar/search" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{"name":"Yann LeCun","page":1,"pageSize":3}'

# 获取学者详情（替换 SCHOLAR_ID）
curl -s "$BASE/v1/paper-server/scholar/info?scholarId=SCHOLAR_ID" \
  -H "accessKey: $AK"
```

---

## 使用示例

### 基本用法：指定会议列表

```python
CONFIG = {
    "conferences": ["NeurIPS", "ICML", "ICLR"],
    "field_keywords": [],
    "research_direction": "graph neural networks for molecular property prediction",
    "year": 2026,
}
```

### 按领域自动匹配会议

```python
CONFIG = {
    "conferences": [],  # 不指定会议，由系统自动匹配
    "field_keywords": ["protein structure prediction", "drug discovery"],
    "research_direction": "protein-ligand binding affinity prediction",
    "year": 2026,
}
```

### 查询已知演讲者

```python
# 在步骤 3 中传入已知演讲者姓名
speaker_data = step3_search_speakers(
    all_conf_info,
    speaker_names=["Yann LeCun", "Geoffrey Hinton", "Yoshua Bengio"]
)
```

### 命令行调用

```bash
export ACCESS_KEY="your_access_key"
python conference_tracker.py
```

---

## 搭配使用

- **conference-tracker** 发现高相关性会议 → **bohrium-paper-search** 深入检索该会议的论文
- **conference-tracker** 识别演讲者 → **scholar-profiler** 生成演讲者完整画像
- **conference-tracker** 发现热点方向 → **literature-review** 对该方向做文献综述
- **conference-tracker** 追踪多个会议 → **tech-radar** 持续监控领域动态
- **conference-tracker** 输出报告 → **bohrium-knowledge-base** 存档供团队共享

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `ACCESS_KEY` 为空 | OpenClaw 未注入环境变量 | 检查 `~/.openclaw/openclaw.json` 中 `conference-tracker.env.ACCESS_KEY` 是否填入 |
| 401 Unauthorized | accessKey 无效或过期 | 更新 `~/.openclaw/openclaw.json` 中的 AccessKey 并重启会话 |
| 会议搜索结果为空 | 会议名称拼写错误或过于冷门 | 使用会议的标准英文缩写（如 `NeurIPS` 而非 `nips`），或尝试全称 |
| 论文检索结果为空 | 关键词组合太窄或时间范围不匹配 | 放宽关键词、扩大时间窗口（会议论文发表时间可能与会议日期不同） |
| 相关性评分全部为 0 | 用户研究方向描述过于笼统或使用中文 | 使用具体的英文术语描述研究方向，如 `"graph neural networks for molecular property prediction"` |
| 演讲者搜索无结果 | 会议尚未公布演讲者名单 | 正常现象，会议通常在举办前几个月才公布演讲者 |
| 学者搜索未匹配到正确的人 | 同名学者较多 | 在演讲者查询中，结合搜索结果中的机构信息手动确认 |
| 响应含多行 JSON | paper-search 返回 streaming 格式 | 取第一行解析即可：`json.loads(r.text.split('\n')[0])` |
| 网络超时 | 某个 API 响应慢 | 脚本已设置 30 秒超时并捕获异常，单个失败不影响整体流程 |
| 截止日期信息不准确 | 网络搜索结果可能过时 | 始终以会议官方网站公布的信息为准，本工具仅作参考 |
