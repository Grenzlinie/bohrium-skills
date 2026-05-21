---
name: field-mapper
description: "Research field landscape mapping combining paper analysis, scholar identification, and knowledge hierarchy. Use when: user is new to a field and needs a comprehensive overview of sub-areas, key journals, leading scholars, and must-read papers. NOT for: specific topic deep-dive (use literature-review), choosing a research topic (use topic-scout)."
---

# SKILL: 领域图谱绘制 (Field Mapper)

## 概述

**领域图谱绘制**是一个编排型技能，通过组合多个 Bohrium 原子技能，为初次进入某一学科/领域的研究者自动生成完整的领域全景图：子领域分支树、核心期刊与顶会列表、关键学者网络、必读论文清单以及领域发展时间线。

**编排流程：**

```
用户输入领域/学科关键词 + 绘制深度（overview / detailed）
  │
  ├─ Step 1: paper-search   ─── 检索高引经典论文与近年综述
  ├─ Step 2: scholar-search  ── 识别领军学者与新锐研究者
  ├─ Step 3: lkm             ── 构建概念层级与子领域关系图谱
  └─ Step 4: wiki            ── 补充基础概念定义与学科分类
  │
  ▼
  输出：子领域分支树 + 核心期刊/顶会 + 学者网络 + 必读论文 + 发展时间线
```

**适用场景：**

- 研究生入学，快速了解一个全新领域的全貌
- 跨学科研究者需要建立对陌生领域的系统认知
- 课题组开拓新方向前的领域调研
- 基金申请前的领域背景梳理

**不适用：**

- 已确定主题的深度文献调研 → 用 `literature-review`
- 选题探索与创新机会发现 → 用 `topic-scout`
- 单纯查找某篇论文 → 用 `bohrium-paper-search`
- 单纯查找某位学者 → 用 `bohrium-scholar-search`

**无 CLI 支持** — 通过 Python 脚本编排多个 HTTP API 完成。

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"field-mapper": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.ACCESS_KEY` 注入到运行环境。

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `field` | string | 是 | — | 领域/学科关键词，如"计算材料学"、"蛋白质工程"、"量子计算" |
| `depth` | string | 否 | `"overview"` | 绘制深度：`"overview"`（概览，快速出图）/ `"detailed"`（详细，含更多层级和论文） |
| `language` | string | 否 | `"en-US"` | Wiki 百科语言：`"en-US"` 或 `"zh-CN"` |

## 输出格式

### 1. 子领域分支树（层级结构）

```
领域名称
├── 子领域 A
│   ├── 方向 A1
│   └── 方向 A2
├── 子领域 B
│   ├── 方向 B1
│   ├── 方向 B2
│   └── 方向 B3
└── 子领域 C
    └── 方向 C1
```

### 2. 核心期刊与顶会列表

| 期刊/会议 | 类型 | 影响因子 | 出现论文数 |
|-----------|------|---------|-----------|
| Nature Materials | 期刊 | 41.2 | 8 |
| ICML | 会议 | — | 5 |

### 3. 关键学者网络（按子方向分组）

| 子方向 | 学者 | 机构 | h-index | 论文数 | 引用数 |
|--------|------|------|---------|--------|--------|
| 方向 A | 张三 | MIT | 45 | 200 | 15000 |
| 方向 B | 李四 | Stanford | 38 | 150 | 12000 |

### 4. 必读论文清单（10-20 篇，按推荐阅读顺序排列）

阅读顺序遵循：经典奠基 → 权威综述 → 近年进展

| 序号 | 阅读阶段 | 标题 | DOI | 年份 | 引用数 | 推荐理由 |
|------|----------|------|-----|------|--------|----------|
| 1 | 经典奠基 | ... | ... | 2005 | 5000 | 领域开创性工作 |
| 2 | 经典奠基 | ... | ... | 2008 | 3000 | 奠定理论基础 |
| 3 | 权威综述 | ... | ... | 2020 | 800 | 全面综述近十年进展 |
| 4 | 近年进展 | ... | ... | 2024 | 50 | 最新方法突破 |

### 5. 领域发展时间线（里程碑事件）

```
2005  ── 领域起源：XXX 论文发表，首次提出 YYY 概念
2010  ── 方法突破：ZZZ 方法将精度提升 N 个数量级
2018  ── 规模应用：AAA 团队实现工业级应用
2023  ── 最新前沿：BBB 方向成为热点
```

---

## 报告分析深度要求

### 必读论文清单的排序逻辑

论文推荐**不能仅按引用数排序**，必须同时使用两种策略：
- **经典高引**（按总引用数）：确保覆盖奠基性工作和权威综述
- **前沿高速**（按月均引用数，12 个月内额外加权）：确保覆盖最新突破

最终清单应混合两组结果，确保既有 2005 年的经典工作，也有 2024 年的最新进展。

### 子领域分支树的完整性检查

生成分支树后，必须用 LKM 知识图谱进行交叉验证：
- 检查 LKM 返回的相关概念是否都在分支树中有对应
- 如果 LKM 提示某子方向存在但分支树中没有，需补充检索或标注为"可能遗漏"
- 分支树中每个叶节点应至少有 1 篇代表性论文作为支撑

### 关键学者数据透明度

学者信息表中的 h-index 和引用数**必须标注**：
> 注：h-index 和引用数据来源于 Bohrium 学术搜索（检索日期：YYYY-MM-DD），可能与 Google Scholar 等其他来源存在差异。

### 禁止的行为

- ❌ 分支树只有两层深度就停止（对于成熟领域应至少 3 层）
- ❌ 必读论文全是近 5 年的工作而无经典奠基文献
- ❌ 时间线中的里程碑事件不附论文来源
- ❌ h-index 等指标不标注数据来源

---

## 工作流程图

```
输入: field, depth, language
        │
        ▼
┌──────────────────────────────────────┐
│  步骤 1: 论文语义检索                  │
│  POST /v1/paper/rag/pass/keyword     │
│  → 分两轮检索：经典高引 + 近年综述      │
│  → 提取期刊分布、年份分布、作者列表      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 2: 学者搜索与画像                │
│  POST /v1/paper-server/scholar/search│
│  GET  /v1/paper-server/scholar/info  │
│  → 从高引论文作者中提取候选学者         │
│  → 获取学者画像：机构、研究方向、h-index │
│  → 按研究方向对学者分组                │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 3: 知识图谱概念层级               │
│  POST /v1/lkm/search                │
│  → 搜索领域核心概念节点                │
│  → 提取子领域关系与层级结构             │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 4: Wiki 百科补充                 │
│  POST /v1/.../wiki_v2/search_index   │
│  POST /v1/.../wiki_v2/article        │
│  → 搜索领域相关百科词条                │
│  → 获取子领域定义与分类信息             │
│  → 与 LKM 结果交叉合并，构建子领域树    │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 5: 综合分析与图谱生成             │
│  → 合并 Wiki 层级 + LKM 概念图谱       │
│  → 构建子领域分支树                    │
│  → 统计核心期刊/顶会                   │
│  → 按子方向分组学者网络                │
│  → 排序必读论文清单                    │
│  → 生成发展时间线                      │
└──────────────────────────────────────┘
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
    print("请在 ~/.openclaw/openclaw.json 中配置 field-mapper.env.ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET = {"accessKey": AK}
```

---

## 分步说明

### Step 1: 论文语义检索 (paper-search)

**目标：** 分两轮检索——第一轮获取经典高引论文（不限时间，按引用排序），第二轮获取近年综述和进展（限近 3 年）。从结果中提取期刊分布、年份分布、作者候选列表。

**API 调用：**

```
POST https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword
Header: accessKey: $ACCESS_KEY, Content-Type: application/json
Body: {
    "words": ["field", "keyword", "list"],
    "question": "comprehensive overview of FIELD",
    "type": 5,
    "startTime": "",
    "endTime": "",
    "jcrZones": ["Q1"],
    "pageSize": 30
}
```

**关键返回字段：**

| 字段 | 用途 |
|------|------|
| `enName` | 论文标题 |
| `enAbstract` | 摘要，判断是否为综述 |
| `citationNums` | 引用数，区分经典与新作 |
| `coverDateStart` | 发表日期，构建时间线 |
| `impactFactor` | 影响因子，评估期刊等级 |
| `publicationEnName` | 期刊名，统计核心期刊 |
| `authors` | 作者列表，衔接 Step 2 |
| `doi` | DOI，论文唯一标识 |

### Step 2: 学者搜索与画像 (scholar-search)

**目标：** 从 Step 1 高引论文的作者中提取候选学者，获取其详细画像（机构、研究方向、h-index），按研究方向分组。

**API 调用：**

```
# 搜索学者
POST https://open.bohrium.com/openapi/v1/paper-server/scholar/search
Body: {"name": "学者姓名", "tags": "领域关键词", "page": 1, "pageSize": 10}

# 获取学者详情
GET https://open.bohrium.com/openapi/v1/paper-server/scholar/info?scholarId=xxx
```

**关键返回字段：**

| 字段 | 用途 |
|------|------|
| `scholarId` | 学者 ID，查详情用 |
| `nameEn` / `nameZh` | 学者姓名 |
| `scholarOrgNameEn` | 所属机构 |
| `paperNums` | 论文数 |
| `citationNums` | 引用数 |
| `hIndex` | h-index |
| `researchDirection` | 研究方向列表（详情接口） |

### Step 3: 知识图谱概念层级 (LKM)

**目标：** 从知识图谱中搜索领域核心概念，提取子领域之间的关系与层级结构。

**API 调用：**

```
POST https://open.bohrium.com/openapi/v1/lkm/search
Body: {"query": "领域概念", "limit": 20}
```

### Step 4: Wiki 百科补充

**目标：** 搜索领域相关的百科词条，获取子领域的标准定义与分类信息，与 LKM 结果交叉合并构建完整的子领域树。

**API 调用：**

```
# 搜索词条索引
POST https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2/search_index_name
Body: {"name": "关键词", "node_types": ["field", "topic"], "style": "Feynman"}
返回: {"wiki_indices": [{"node_id": "...", "node_name": "...", "node_type": "..."}]}

# 获取词条正文
POST https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2/article
Body: {"node_id": "...", "language": "en-US", "style": "Feynman"}
返回: {"document": {"article_name": "...", "main_content": "...", "applications": "..."}}
```

---

## 完整编排脚本

以下脚本实现从输入到输出的完整领域图谱绘制流程。

```python
#!/usr/bin/env python3
"""
领域图谱绘制 (Field Mapper) — 完整编排脚本

用法:
    export ACCESS_KEY="your_access_key"
    python3 field_mapper.py

可修改下方 CONFIG 区域的参数来调整领域和绘制深度。
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
    print("请在 ~/.openclaw/openclaw.json 中配置 field-mapper.env.ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET = {"accessKey": AK}

# -- 用户可修改区域 --
CONFIG = {
    "field": "computational materials science",       # 修改为目标领域
    "keywords": [                                     # 3-8 个英文术语
        "computational materials science",
        "density functional theory",
        "molecular dynamics",
        "machine learning potential",
        "high-throughput screening",
    ],
    "depth": "overview",       # "overview"（概览）或 "detailed"（详细）
    "language": "en-US",       # Wiki 语言: "en-US" 或 "zh-CN"
}

# 根据深度调整参数
DEPTH_PARAMS = {
    "overview":  {"paper_page_size": 20, "scholar_top_n": 5, "lkm_limit": 10, "wiki_max": 5},
    "detailed":  {"paper_page_size": 30, "scholar_top_n": 10, "lkm_limit": 20, "wiki_max": 10},
}
PARAMS = DEPTH_PARAMS.get(CONFIG["depth"], DEPTH_PARAMS["overview"])


# ============================================================
# 辅助函数
# ============================================================

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
        return None
    except Exception as e:
        print(f"  [WARN] 请求异常: {e}")
        return None


def parse_paper_response(response):
    """解析论文检索响应（可能为 streaming 多行 JSON）"""
    if response is None:
        return []
    # 如果已经是 dict（safe_request 已解析），直接取 data
    if isinstance(response, dict):
        if response.get("code") == 0:
            return response.get("data", [])
        return []
    return []


def search_papers_raw(keywords, question, start_time="", end_time="",
                      jcr_zones=None, page_size=20):
    """原始论文检索，返回解析后的论文列表"""
    payload = {
        "words": keywords,
        "question": question,
        "type": 5,
        "startTime": start_time,
        "endTime": end_time,
        "jcrZones": jcr_zones or [],
        "pageSize": page_size,
    }
    # paper-search 可能返回 streaming 格式，需要特殊处理
    try:
        r = requests.post(
            f"{BASE}/v1/paper/rag/pass/keyword",
            headers=HEADERS,
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        text = r.text.strip()
        first_line = text.split('\n')[0]
        data = json.loads(first_line)
        if data.get("code") == 0:
            return data.get("data", [])
    except Exception as e:
        print(f"  [WARN] 论文检索异常: {e}")
    return []


# ============================================================
# 步骤 1: 论文语义检索（双轮）
# ============================================================

def step1_search_papers(config, params):
    """
    双轮检索：
      轮次 A — 不限时间，Q1 期刊，按引用数排序 → 经典高引论文
      轮次 B — 限近 3 年，综述类关键词 → 近年综述和进展
    """
    print(f"\n{'='*60}")
    print(f"步骤 1: 论文语义检索（双轮）")
    print(f"  领域: {config['field']}")
    print(f"  关键词: {config['keywords']}")
    print(f"{'='*60}\n")

    all_papers = []
    seen_dois = set()

    # --- 轮次 A: 经典高引论文 ---
    print("  轮次 A: 检索经典高引论文（不限时间，Q1 期刊）...")
    classics = search_papers_raw(
        keywords=config["keywords"],
        question=f"foundational and highly cited papers in {config['field']}",
        jcr_zones=["Q1"],
        page_size=params["paper_page_size"],
    )
    classics.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
    for p in classics:
        doi = p.get("doi", "")
        if doi and doi not in seen_dois:
            seen_dois.add(doi)
            p["_search_round"] = "classic"
            all_papers.append(p)
    print(f"    检索到 {len(classics)} 篇，去重后新增 {sum(1 for p in all_papers if p['_search_round']=='classic')} 篇")

    # --- 轮次 B: 近年综述与进展 ---
    end_time = datetime.now().strftime("%Y-%m-%d")
    start_time = (datetime.now() - timedelta(days=3*365)).strftime("%Y-%m-%d")
    print(f"\n  轮次 B: 检索近年综述与进展（{start_time} ~ {end_time}）...")
    recent = search_papers_raw(
        keywords=config["keywords"] + ["review", "survey", "perspective"],
        question=f"recent reviews and advances in {config['field']}",
        start_time=start_time,
        end_time=end_time,
        page_size=params["paper_page_size"],
    )
    recent.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
    count_before = len(all_papers)
    for p in recent:
        doi = p.get("doi", "")
        if doi and doi not in seen_dois:
            seen_dois.add(doi)
            p["_search_round"] = "recent"
            all_papers.append(p)
    print(f"    检索到 {len(recent)} 篇，去重后新增 {len(all_papers) - count_before} 篇")

    print(f"\n  合计: {len(all_papers)} 篇论文（经典 + 近年）")

    # 提取期刊分布
    journal_counter = Counter()
    for p in all_papers:
        journal = p.get("publicationEnName", "")
        if journal:
            journal_counter[journal] += 1

    # 提取年份分布
    year_counter = Counter()
    for p in all_papers:
        year = p.get("coverDateStart", "")[:4]
        if year:
            year_counter[year] += 1

    # 提取候选作者
    candidate_authors = []
    for p in sorted(all_papers, key=lambda x: x.get("citationNums", 0), reverse=True)[:15]:
        authors = p.get("authors", [])
        if isinstance(authors, list):
            for a in authors[:2]:
                name = a if isinstance(a, str) else a.get("name", "")
                if name and name not in candidate_authors:
                    candidate_authors.append(name)

    print(f"\n  Top 5 期刊: {journal_counter.most_common(5)}")
    print(f"  年份分布: {sorted(year_counter.items())}")
    print(f"  候选作者: {len(candidate_authors)} 位")

    return all_papers, journal_counter, year_counter, candidate_authors


# ============================================================
# 步骤 2: 学者搜索与画像
# ============================================================

def step2_scholar_profiles(config, candidate_authors, params):
    """
    搜索候选学者，获取详细画像，按研究方向分组。
    """
    print(f"\n{'='*60}")
    print(f"步骤 2: 学者搜索与画像")
    print(f"{'='*60}\n")

    scholar_results = []
    scholar_ids_seen = set()

    for name in candidate_authors[:params["scholar_top_n"]]:
        print(f"  搜索学者: {name}")
        data = safe_request("POST", f"{BASE}/v1/paper-server/scholar/search",
            headers=HEADERS,
            json={
                "name": name,
                "tags": config["field"],
                "page": 1,
                "pageSize": 5,
            }
        )
        if data and data.get("data", {}).get("items"):
            for item in data["data"]["items"][:2]:
                sid = item.get("scholarId", "")
                if sid and sid not in scholar_ids_seen:
                    scholar_ids_seen.add(sid)
                    scholar_results.append(item)
                    print(f"    [{sid}] {item.get('nameEn', '')} "
                          f"({item.get('scholarOrgNameEn', '')})")
                    print(f"      论文: {item.get('paperNums', 0)}, "
                          f"引用: {item.get('citationNums', 0)}, "
                          f"h-index: {item.get('hIndex', 0)}")

    # 获取详细画像
    scholar_profiles = []
    for scholar in scholar_results[:params["scholar_top_n"]]:
        sid = scholar.get("scholarId")
        if not sid:
            continue
        info = safe_request("GET", f"{BASE}/v1/paper-server/scholar/info",
            headers=HEADERS_GET,
            params={"scholarId": sid},
        )
        if info and info.get("data"):
            profile = info["data"]
            profile["_search_name"] = scholar.get("nameEn", "")
            profile["_org"] = scholar.get("scholarOrgNameEn", "")
            profile["_paper_nums"] = scholar.get("paperNums", 0)
            profile["_citation_nums"] = scholar.get("citationNums", 0)
            profile["_h_index"] = scholar.get("hIndex", 0)
            scholar_profiles.append(profile)
            directions = profile.get("researchDirection", [])
            print(f"\n  学者画像: {profile.get('nameEn', '')}")
            print(f"    研究方向: {directions}")

    # 按研究方向分组
    direction_scholars = defaultdict(list)
    for prof in scholar_profiles:
        directions = prof.get("researchDirection", [])
        if not directions:
            directions = ["未分类"]
        for d in directions:
            direction_scholars[d].append({
                "name": prof.get("nameEn", prof.get("_search_name", "")),
                "org": prof.get("_org", ""),
                "h_index": prof.get("_h_index", 0),
                "paper_nums": prof.get("_paper_nums", 0),
                "citation_nums": prof.get("_citation_nums", 0),
            })

    print(f"\n  识别学者: {len(scholar_profiles)} 位")
    print(f"  研究方向分组: {list(direction_scholars.keys())}")

    return scholar_profiles, direction_scholars


# ============================================================
# 步骤 3: 知识图谱概念层级 (LKM)
# ============================================================

def step3_lkm_concepts(config, params):
    """
    从知识图谱中搜索领域概念，提取子领域之间的关系。
    """
    print(f"\n{'='*60}")
    print(f"步骤 3: 知识图谱概念层级")
    print(f"{'='*60}\n")

    lkm_concepts = []

    # 搜索领域核心概念
    print(f"  搜索领域概念: {config['field']}")
    data = safe_request("POST", f"{BASE}/v1/lkm/search",
        headers=HEADERS,
        json={
            "query": f"sub-fields and key concepts in {config['field']}",
            "limit": params["lkm_limit"],
        }
    )
    if data and data.get("data"):
        lkm_concepts = data["data"] if isinstance(data["data"], list) else [data["data"]]
        print(f"    返回 {len(lkm_concepts)} 个知识节点")
    else:
        print(f"    未返回有效数据")

    # 对每个关键词也单独搜索，捕获更细粒度的概念
    for kw in config["keywords"][:5]:
        print(f"  补充搜索: {kw}")
        data = safe_request("POST", f"{BASE}/v1/lkm/search",
            headers=HEADERS,
            json={
                "query": kw,
                "limit": 5,
            }
        )
        if data and data.get("data"):
            extra = data["data"] if isinstance(data["data"], list) else [data["data"]]
            lkm_concepts.extend(extra)
            print(f"    新增 {len(extra)} 个节点")

    print(f"\n  LKM 概念总数: {len(lkm_concepts)}")
    return lkm_concepts


# ============================================================
# 步骤 4: Wiki 百科补充
# ============================================================

def step4_wiki_supplement(config, params):
    """
    搜索百科词条，获取子领域的标准定义与分类信息。
    """
    print(f"\n{'='*60}")
    print(f"步骤 4: Wiki 百科补充")
    print(f"{'='*60}\n")

    WIKI_BASE = f"{BASE}/v1/literature-sage/wiki_v2"
    wiki_entries = []

    # 4a. 搜索领域词条索引
    print(f"  搜索词条索引: {config['field']}")
    data = safe_request("POST", f"{WIKI_BASE}/search_index_name",
        headers=HEADERS,
        json={
            "name": config["field"],
            "node_types": ["field", "topic"],
            "style": "Feynman",
        }
    )

    indices = []
    if data and data.get("wiki_indices"):
        indices = data["wiki_indices"]
        print(f"    找到 {len(indices)} 个词条索引")
        for idx in indices[:5]:
            print(f"      [{idx['node_type']}] {idx['node_name']} (id={idx['node_id']})")

    # 也对每个关键词搜索
    for kw in config["keywords"][:3]:
        data = safe_request("POST", f"{WIKI_BASE}/search_index_name",
            headers=HEADERS,
            json={
                "name": kw,
                "node_types": ["field", "topic"],
                "style": "Feynman",
            }
        )
        if data and data.get("wiki_indices"):
            # 去重
            existing_ids = {i["node_id"] for i in indices}
            for idx in data["wiki_indices"]:
                if idx["node_id"] not in existing_ids:
                    indices.append(idx)
                    existing_ids.add(idx["node_id"])

    print(f"    合计索引: {len(indices)} 个")

    # 4b. 获取词条正文（取前 N 个）
    print(f"\n  获取词条正文（最多 {params['wiki_max']} 个）...")
    for idx in indices[:params["wiki_max"]]:
        node_id = idx["node_id"]
        print(f"    获取: {idx['node_name']} ({node_id})")

        article_data = safe_request("POST", f"{WIKI_BASE}/article",
            headers=HEADERS,
            json={
                "node_id": node_id,
                "language": config.get("language", "en-US"),
                "style": "Feynman",
            }
        )
        if article_data and article_data.get("document"):
            doc = article_data["document"]
            entry = {
                "node_id": node_id,
                "node_name": idx["node_name"],
                "node_type": idx["node_type"],
                "article_name": doc.get("article_name", ""),
                "main_content": doc.get("main_content", "")[:500],
                "applications": doc.get("applications", ""),
            }
            wiki_entries.append(entry)
            print(f"      标题: {entry['article_name']}")
        else:
            print(f"      未获取到正文")

    print(f"\n  获取百科词条: {len(wiki_entries)} 个")
    return indices, wiki_entries


# ============================================================
# 步骤 5: 综合分析与图谱生成
# ============================================================

def build_subfield_tree(lkm_concepts, wiki_indices, wiki_entries):
    """
    合并 Wiki 层级与 LKM 概念图谱，构建子领域分支树。

    策略：
    1. 以 Wiki 的 field/topic 层级为骨架（提供标准分类）
    2. 用 LKM 概念补充未被 Wiki 覆盖的子领域和交叉概念
    3. 去重合并，形成统一的子领域树
    """
    tree = defaultdict(list)

    # 从 Wiki 索引构建骨架
    field_nodes = [i for i in wiki_indices if i.get("node_type") == "field"]
    topic_nodes = [i for i in wiki_indices if i.get("node_type") == "topic"]

    if field_nodes:
        for fn in field_nodes:
            tree[fn["node_name"]] = []  # 子领域作为一级节点
    if topic_nodes:
        # 将 topic 节点挂到最近的 field 下（简单策略：按顺序分配）
        for tn in topic_nodes:
            # 尝试从 Wiki entry 中获取归属信息
            assigned = False
            for fn in field_nodes:
                if fn["node_name"].lower() in tn["node_name"].lower():
                    tree[fn["node_name"]].append(tn["node_name"])
                    assigned = True
                    break
            if not assigned:
                # 未能归类的 topic 作为独立方向
                if field_nodes:
                    # 归入第一个 field（兜底）
                    tree[field_nodes[0]["node_name"]].append(tn["node_name"])
                else:
                    tree["其他方向"].append(tn["node_name"])

    # 从 LKM 概念补充
    wiki_names = {i["node_name"].lower() for i in wiki_indices}
    for concept in lkm_concepts:
        # LKM 返回结构可能不同，尝试多种取名方式
        name = ""
        if isinstance(concept, dict):
            name = concept.get("name", concept.get("content", concept.get("query", "")))
        elif isinstance(concept, str):
            name = concept

        if name and name.lower() not in wiki_names:
            tree["LKM 补充概念"].append(name)

    return dict(tree)


def rank_reading_list(papers):
    """
    推荐阅读顺序算法：

    分三个阶段排列论文：
      阶段 1 - 经典奠基：高引用（>100）且发表较早（>5年前）的论文
      阶段 2 - 权威综述：标题/摘要中含 review/survey/perspective 的论文
      阶段 3 - 近年进展：近 3 年内发表的论文，按引用排序

    每个阶段内部按引用数降序排列。
    """
    now = datetime.now()
    five_years_ago = (now - timedelta(days=5*365)).strftime("%Y-%m-%d")
    three_years_ago = (now - timedelta(days=3*365)).strftime("%Y-%m-%d")

    classics = []    # 阶段 1: 经典奠基
    reviews = []     # 阶段 2: 权威综述
    recent = []      # 阶段 3: 近年进展
    other = []       # 兜底

    review_keywords = ["review", "survey", "perspective", "overview", "tutorial", "roadmap"]

    for p in papers:
        title = (p.get("enName") or "").lower()
        abstract = (p.get("enAbstract") or "").lower()
        citations = p.get("citationNums", 0)
        pub_date = p.get("coverDateStart", "")
        is_review = any(kw in title or kw in abstract for kw in review_keywords)

        if is_review:
            reviews.append(p)
        elif citations > 100 and pub_date < five_years_ago:
            classics.append(p)
        elif pub_date >= three_years_ago:
            recent.append(p)
        else:
            other.append(p)

    # 各阶段内按引用降序
    classics.sort(key=lambda x: x.get("citationNums", 0), reverse=True)
    reviews.sort(key=lambda x: x.get("citationNums", 0), reverse=True)
    recent.sort(key=lambda x: x.get("citationNums", 0), reverse=True)
    other.sort(key=lambda x: x.get("citationNums", 0), reverse=True)

    # 组合最终列表（限 10-20 篇）
    reading_list = []
    phases = [
        ("经典奠基", classics, 5),
        ("权威综述", reviews, 5),
        ("近年进展", recent, 7),
        ("补充阅读", other, 3),
    ]

    for phase_name, phase_papers, max_count in phases:
        for p in phase_papers[:max_count]:
            reading_list.append({
                "phase": phase_name,
                "title": p.get("enName", ""),
                "doi": p.get("doi", ""),
                "year": p.get("coverDateStart", "")[:4],
                "citations": p.get("citationNums", 0),
                "journal": p.get("publicationEnName", ""),
                "impact_factor": p.get("impactFactor", 0),
                "reason": _reading_reason(p, phase_name),
            })
            if len(reading_list) >= 20:
                break
        if len(reading_list) >= 20:
            break

    return reading_list


def _reading_reason(paper, phase):
    """生成推荐理由"""
    reasons = []
    citations = paper.get("citationNums", 0)
    impact_factor = paper.get("impactFactor", 0)

    if phase == "经典奠基":
        reasons.append("领域奠基性工作")
        if citations > 500:
            reasons.append(f"极高引用 ({citations})")
    elif phase == "权威综述":
        reasons.append("系统性综述文章")
        if impact_factor > 10:
            reasons.append(f"高影响因子期刊 (IF={impact_factor})")
    elif phase == "近年进展":
        reasons.append("近年最新进展")
        if citations > 20:
            reasons.append(f"短期内快速积累引用 ({citations})")
    else:
        reasons.append("领域相关高质量论文")

    return "；".join(reasons)


def build_timeline(papers):
    """从论文年份中提取里程碑，构建领域发展时间线。"""
    papers_by_year = defaultdict(list)
    for p in papers:
        year = p.get("coverDateStart", "")[:4]
        if year:
            papers_by_year[year].append(p)

    timeline = []
    for year in sorted(papers_by_year.keys()):
        year_papers = papers_by_year[year]
        top_paper = max(year_papers, key=lambda x: x.get("citationNums", 0))
        timeline.append({
            "year": year,
            "paper_count": len(year_papers),
            "milestone_title": top_paper.get("enName", ""),
            "milestone_doi": top_paper.get("doi", ""),
            "milestone_citations": top_paper.get("citationNums", 0),
        })
    return timeline


def step5_synthesize(config, papers, journal_counter, year_counter,
                     scholar_profiles, direction_scholars,
                     lkm_concepts, wiki_indices, wiki_entries):
    """综合所有数据，生成完整的领域图谱。"""
    print(f"\n{'='*60}")
    print(f"步骤 5: 综合分析与图谱生成")
    print(f"{'='*60}\n")

    # 5a. 构建子领域分支树
    print("  5a. 构建子领域分支树...")
    subfield_tree = build_subfield_tree(lkm_concepts, wiki_indices, wiki_entries)

    # 5b. 核心期刊与顶会列表
    print("  5b. 统计核心期刊/顶会...")
    top_journals = []
    for journal, count in journal_counter.most_common(15):
        # 从论文中获取该期刊的平均影响因子
        ifs = [p.get("impactFactor", 0) for p in papers
               if p.get("publicationEnName") == journal and p.get("impactFactor")]
        avg_if = sum(ifs) / len(ifs) if ifs else 0
        top_journals.append({
            "name": journal,
            "paper_count": count,
            "avg_impact_factor": round(avg_if, 1),
        })

    # 5c. 学者网络（已在 Step 2 中按方向分组）
    print("  5c. 学者网络已就绪")

    # 5d. 必读论文清单（推荐阅读顺序）
    print("  5d. 生成必读论文清单...")
    reading_list = rank_reading_list(papers)

    # 5e. 领域发展时间线
    print("  5e. 生成发展时间线...")
    timeline = build_timeline(papers)

    result = {
        "field": config["field"],
        "depth": config["depth"],
        "generated_at": datetime.now().isoformat(),
        "paper_count": len(papers),
        "scholar_count": len(scholar_profiles),
        "subfield_tree": subfield_tree,
        "top_journals": top_journals,
        "scholar_network": dict(direction_scholars),
        "reading_list": reading_list,
        "timeline": timeline,
        "wiki_entries": wiki_entries,
    }

    return result


# ============================================================
# 格式化输出
# ============================================================

def format_field_map(result):
    """将结构化结果格式化为 Markdown。"""
    lines = []
    lines.append(f"# 领域图谱: {result['field']}")
    lines.append(f"\n> 绘制深度: {result['depth']}")
    lines.append(f"> 生成时间: {result['generated_at']}")
    lines.append(f"> 论文数: {result['paper_count']}, 学者数: {result['scholar_count']}")

    # ---- 1. 子领域分支树 ----
    fence = chr(96) * 3  # code fence marker
    lines.append("\n## 1. 子领域分支树\n")
    lines.append(fence)
    lines.append(result["field"])
    tree = result["subfield_tree"]
    tree_keys = list(tree.keys())
    for i, subfield in enumerate(tree_keys):
        is_last = (i == len(tree_keys) - 1)
        prefix = "└── " if is_last else "├── "
        lines.append(f"{prefix}{subfield}")
        children = tree[subfield]
        for j, child in enumerate(children):
            child_is_last = (j == len(children) - 1)
            indent = "    " if is_last else "│   "
            child_prefix = "└── " if child_is_last else "├── "
            lines.append(f"{indent}{child_prefix}{child}")
    lines.append(fence)

    # ---- 2. 核心期刊/顶会 ----
    lines.append("\n## 2. 核心期刊与顶会\n")
    lines.append("| # | 期刊/会议 | 出现论文数 | 平均影响因子 |")
    lines.append("|---|----------|-----------|-------------|")
    for i, j in enumerate(result["top_journals"][:10], 1):
        lines.append(f"| {i} | {j['name']} | {j['paper_count']} | {j['avg_impact_factor']} |")

    # ---- 3. 学者网络 ----
    lines.append("\n## 3. 关键学者网络（按子方向分组）\n")
    for direction, scholars in result["scholar_network"].items():
        lines.append(f"\n### {direction}\n")
        lines.append("| 学者 | 机构 | h-index | 论文数 | 引用数 |")
        lines.append("|------|------|---------|--------|--------|")
        for s in scholars:
            lines.append(f"| {s['name']} | {s['org']} | {s['h_index']} | "
                         f"{s['paper_nums']} | {s['citation_nums']} |")

    # ---- 4. 必读论文清单 ----
    lines.append("\n## 4. 必读论文清单（推荐阅读顺序）\n")
    lines.append("> 阅读顺序：经典奠基 -> 权威综述 -> 近年进展\n")
    lines.append("| 序号 | 阅读阶段 | 标题 | DOI | 年份 | 引用 | 推荐理由 |")
    lines.append("|------|----------|------|-----|------|------|----------|")
    for i, r in enumerate(result["reading_list"], 1):
        title = r["title"][:60] + ("..." if len(r["title"]) > 60 else "")
        lines.append(f"| {i} | {r['phase']} | {title} | "
                     f"`{r['doi']}` | {r['year']} | {r['citations']} | {r['reason']} |")

    # ---- 5. 发展时间线 ----
    lines.append("\n## 5. 领域发展时间线\n")
    lines.append(fence)
    for t in result["timeline"]:
        title = t["milestone_title"][:70] + ("..." if len(t["milestone_title"]) > 70 else "")
        lines.append(f"{t['year']}  ── ({t['paper_count']} 篇) "
                     f"{title} [引用: {t['milestone_citations']}]")
    lines.append(fence)

    # ---- 附录: Wiki 百科摘要 ----
    if result.get("wiki_entries"):
        lines.append("\n## 附录: 百科概念速查\n")
        for entry in result["wiki_entries"]:
            lines.append(f"### {entry['article_name'] or entry['node_name']}\n")
            content = entry.get("main_content", "")[:300]
            if content:
                lines.append(f"{content}...\n")

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  领域图谱绘制 (Field Mapper) — {config['field']}")
    print(f"  深度: {config['depth']}")
    print(f"{'#'*60}")

    # 步骤 1: 论文检索
    papers, journal_counter, year_counter, candidate_authors = \
        step1_search_papers(config, PARAMS)
    if not papers:
        print("未检索到论文，退出")
        sys.exit(1)

    # 步骤 2: 学者画像
    scholar_profiles, direction_scholars = \
        step2_scholar_profiles(config, candidate_authors, PARAMS)

    # 步骤 3: LKM 概念层级
    lkm_concepts = step3_lkm_concepts(config, PARAMS)

    # 步骤 4: Wiki 百科补充
    wiki_indices, wiki_entries = step4_wiki_supplement(config, PARAMS)

    # 步骤 5: 综合生成
    result = step5_synthesize(
        config, papers, journal_counter, year_counter,
        scholar_profiles, direction_scholars,
        lkm_concepts, wiki_indices, wiki_entries,
    )

    # 输出
    output = format_field_map(result)
    print("\n" + output)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"field_map_{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n领域图谱已保存到: {output_file}")

    data_file = f"field_map_{timestamp}_data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"原始数据已保存到: {data_file}")


if __name__ == "__main__":
    main()
```

---

## curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# Step 1a: 检索经典高引论文
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{
    "words": ["computational materials science", "density functional theory", "molecular dynamics"],
    "question": "foundational and highly cited papers in computational materials science",
    "type": 5,
    "jcrZones": ["Q1"],
    "pageSize": 20
  }'

# Step 1b: 检索近年综述
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{
    "words": ["computational materials science", "review", "survey", "perspective"],
    "question": "recent reviews and advances in computational materials science",
    "type": 5,
    "startTime": "2023-01-01",
    "endTime": "2026-05-13",
    "pageSize": 20
  }'

# Step 2: 学者搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper-server/scholar/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"name": "Jorg Neugebauer", "tags": "computational materials science", "page": 1, "pageSize": 5}'

# Step 2b: 学者详情
curl -s "https://open.bohrium.com/openapi/v1/paper-server/scholar/info?scholarId=SCHOLAR_ID" \
  -H "accessKey: $AK"

# Step 3: LKM 概念搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"query": "sub-fields and key concepts in computational materials science", "limit": 20}'

# Step 4a: Wiki 词条索引搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2/search_index_name" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"name": "computational materials science", "node_types": ["field", "topic"], "style": "Feynman"}'

# Step 4b: Wiki 词条正文
curl -s -X POST "https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2/article" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"node_id": "NODE_ID_HERE", "language": "en-US", "style": "Feynman"}'
```

---

## 概览模式与详细模式对比

| 维度 | 概览模式 (`overview`) | 详细模式 (`detailed`) |
|------|----------------------|----------------------|
| 论文检索数（每轮） | 20 篇 | 30 篇 |
| 学者画像数 | 5 位 | 10 位 |
| LKM 概念搜索上限 | 10 个 | 20 个 |
| Wiki 词条获取上限 | 5 个 | 10 个 |
| 必读论文清单长度 | 10-15 篇 | 15-20 篇 |
| 预计耗时 | 1-3 分钟 | 3-8 分钟 |
| 适合场景 | 快速了解领域全貌 | 全面深入的领域认知 |

---

## 推荐阅读顺序算法说明

必读论文清单按以下三阶段排列，确保读者从基础到前沿循序渐进：

| 阶段 | 筛选条件 | 数量上限 | 阅读目的 |
|------|----------|---------|---------|
| 经典奠基 | 引用 > 100 且发表超过 5 年 | 5 篇 | 建立领域核心概念和方法论基础 |
| 权威综述 | 标题/摘要含 review/survey/perspective | 5 篇 | 系统了解领域发展脉络和研究现状 |
| 近年进展 | 近 3 年发表 | 7 篇 | 掌握最新方法和前沿方向 |
| 补充阅读 | 其余高引论文 | 3 篇 | 拓展视野 |

每个阶段内部按引用数降序排列。

---

## 子领域树构建策略说明

子领域分支树通过合并两个数据源构建：

1. **Wiki 百科骨架** — 以 `search_index_name` 返回的 `field` 和 `topic` 节点为基础，field 节点作为一级子领域，topic 节点作为二级方向。Wiki 提供标准化的学科分类体系。

2. **LKM 概念补充** — 对知识图谱搜索结果去重后，将 Wiki 中未覆盖的概念归入"LKM 补充概念"分组。LKM 擅长发现跨学科的交叉概念和新兴方向。

**合并规则：**
- Wiki field 节点 → 一级子领域
- Wiki topic 节点 → 通过名称匹配归入最近的 field 下
- 未匹配的 topic → 归入第一个 field 或"其他方向"
- LKM 独有概念 → 归入"LKM 补充概念"分组

---

## 使用技巧

### 关键词选择

```python
# 推荐：3-8 个专业英文术语，覆盖领域核心分支
keywords = [
    "computational materials science",   # 领域主关键词
    "density functional theory",         # 理论方法
    "molecular dynamics",                # 模拟方法
    "machine learning potential",        # 交叉方向
    "high-throughput screening",         # 应用范式
]

# 不推荐：太笼统或太少
keywords = ["materials", "science"]
```

### 深度模式选择

- 第一次接触全新领域 → 用 `overview`，5 分钟内获取全貌
- 需要写开题报告或基金申请 → 用 `detailed`，获取更完整的子领域和学者信息

### 分段执行

网络不稳定时，可以将步骤拆开独立执行，每步保存中间结果为 JSON：

```python
# 保存 Step 1 结果
papers, journal_counter, year_counter, authors = step1_search_papers(config, PARAMS)
with open("step1_papers.json", "w") as f:
    json.dump(papers, f, ensure_ascii=False)

# 后续步骤从文件加载
with open("step1_papers.json") as f:
    papers = json.load(f)
```

---

## 搭配使用

- **field-mapper** 绘制全景图 → **literature-review** 对某个子领域做深度综述
- **field-mapper** 发现子领域 → **topic-scout** 在子领域中寻找选题
- **field-mapper** 识别关键学者 → **bohrium-scholar-search** 深入了解学者成果
- **field-mapper** 获取必读论文 → **bohrium-pdf-parser** 解析全文精读
- **field-mapper** 保存结果 → **bohrium-knowledge-base** 存入知识库归档

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 论文检索结果为空 | 关键词太专业或太少 | 扩大关键词范围，增加近义词，去掉 JCR 分区筛选 |
| 子领域树太单薄 | Wiki 中该领域词条少或 LKM 返回空 | 增加关键词数量，尝试英文和中文双语搜索 |
| 学者搜索无结果 | 姓名拼写问题或学者未被收录 | 尝试不同拼写方式，或跳过该学者 |
| Wiki 词条正文为空 | 该节点暂无正文 | 正常现象，部分节点仅作索引 |
| 论文检索返回多行 JSON | paper-search 采用 streaming 格式 | 取第一行解析：`json.loads(r.text.split('\n')[0])` |
| 必读论文清单太短 | 经典论文或综述太少 | 放宽 JCR 分区限制，扩大时间范围 |
| 401 Unauthorized | accessKey 无效 | 检查 `~/.openclaw/openclaw.json` 中的配置 |
| 整体执行超时 | 网络不稳定或 API 负载高 | 使用 `overview` 模式，或分段执行 |
