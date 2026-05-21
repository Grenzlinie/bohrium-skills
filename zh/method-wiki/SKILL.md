---
name: method-wiki
description: "Research method encyclopedia combining SciencePedia, paper search, PDF parsing, and knowledge graph. Use when: user wants to quickly understand a research method's principles, applicability, common pitfalls, and key references. NOT for: field overview (use field-mapper), paper analysis (use paper-dissector)."
---

# SKILL: 方法论百科 (Method Wiki)

## 概述

**方法论百科**是一个编排型技能，通过组合四个 Bohrium 原子技能，为研究者自动生成某一研究方法的完整知识卡片：一句话定义、核心原理、适用与不适用场景、关键参数调参建议、常见陷阱、推荐教程/论文以及相关/替代方法。

**编排流程：**

```
用户输入方法名称 + 使用场景（可选）
  │
  ├─ Step 1: wiki            ── 获取方法的基础定义与概念层级
  ├─ Step 2: paper-search    ── 检索方法论综述与经典原始论文
  ├─ Step 3: pdf-parser      ── 从综述论文中提取方法核心步骤
  └─ Step 4: lkm             ── 补充方法关系（前置知识、衍生方法）
  │
  ▼
  输出：方法卡片（定义 + 原理 + 适用性 + 参数 + 陷阱 + 推荐论文 + 相关方法）
```

**适用场景：**

- 初次接触某一研究方法，需要快速建立全局认知
- 论文阅读中遇到不熟悉的方法，需要了解其原理和适用范围
- 选择研究方法前的可行性评估——该方法是否适合自己的问题
- 编写论文 Methods 部分前的方法论梳理
- 教学备课，需要准备方法论的结构化讲义

**不适用：**

- 领域全景概览 → 用 `field-mapper`
- 单篇论文精读拆解 → 用 `paper-dissector`
- 多种技术路线对比 → 用 `tech-compare`
- 单纯搜索论文 → 用 `bohrium-paper-search`
- 单纯查百科词条 → 用 `bohrium-wiki`

**无 CLI 支持** — 通过 Python 脚本编排多个 HTTP API 完成。

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"method-wiki": {
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
| `method` | string | 是 | — | 方法名称，如 `"molecular dynamics"`、`"variational autoencoder"`、`"density functional theory"` |
| `context` | string | 否 | `""` | 使用场景说明，如 `"我想用它来模拟蛋白质折叠"` |
| `language` | string | 否 | `"en-US"` | Wiki 百科语言：`"en-US"` 或 `"zh-CN"` |

## 输出格式（方法卡片）

### 1. 一句话定义

> 分子动力学（Molecular Dynamics）是一种通过数值求解牛顿运动方程来模拟原子/分子体系随时间演化行为的计算方法。

### 2. 核心原理（3-5 句）

简洁阐述方法的理论基础、关键假设和基本流程，面向没有该方法背景的研究者。

### 3. 适用场景与不适用场景

| 适用 | 不适用 |
|------|--------|
| 纳米尺度体系的动力学模拟 | 电子结构精确计算 |
| 蛋白质折叠、配体结合等构象采样 | 化学键断裂/形成（需 ab initio MD） |

### 4. 关键参数与调参建议

| 参数 | 典型范围 | 调参建议 |
|------|---------|---------|
| 时间步长 | 1-2 fs | 含氢键约束可用 2 fs，否则 1 fs |
| 温度控制 | Nose-Hoover / Langevin | 平衡模拟推荐 Nose-Hoover |

### 5. 常见陷阱 / 注意事项

- 初始结构未充分弛豫导致模拟发散
- 截断半径设置不当导致能量不守恒
- ...

### 6. 实操决策指南（核心产出）

**这一节是方法百科区别于教材的关键价值**。必须基于检索到的论文统计数据，提供：

**6.1 方法选择决策树**（输入你的体系特征 → 推荐具体设置）
```
你的问题是什么？
├─ 结构优化？→ ...（推荐泛函/力场 + 具体软件配置）
├─ 反应路径？→ ...
├─ 光谱预测？→ ...
└─ 动力学性质？→ ...
```

**6.2 参数推荐矩阵**（按应用场景区分，含具体数值）

| 应用场景 | 推荐设置 | 典型精度 | 来源 |
|---------|---------|---------|------|
| 催化表面 | RPBE 或 BEEF-vdW, ENCUT=500 eV | 吸附能 ±0.1-0.3 eV | [统计来源] |
| 有机分子 | B3LYP-D3/def2-TZVP | 构型能 <1 kcal/mol | [统计来源] |

**6.3 "什么时候该方法不够用"的明确判据**（带具体阈值）
- "如果你的体系有 >10⁴ 个原子 → 不用 DFT，用 ML 力场"
- "如果需要化学精度 (<1 kcal/mol) → 不用 DFT，用 CCSD(T)"

**6.4 近年使用趋势**（从检索论文中统计）
- "2020-2026 年该方法在催化/电池/MOF 方向的使用频率"
- "哪个泛函/力场在哪个子领域使用最多"
- 基于论文统计的实证数据，而非教材陈述

### 7. 推荐教程与论文

| 类型 | 标题 | DOI | 推荐理由 |
|------|------|-----|---------|
| 经典原始论文 | ... | ... | 方法提出的奠基之作 |
| 权威综述 | ... | ... | 最全面的方法论综述 |
| 实践教程 | ... | ... | 含代码的上手教程 |

### 8. 相关/替代方法

| 方法 | 关系 | 说明 |
|------|------|------|
| 蒙特卡洛方法 | 替代 | 适合热力学平衡性质，不提供动力学信息 |
| Ab initio MD | 衍生 | 在每一步用 DFT 计算力，精度更高但成本极大 |
| 粗粒化 MD | 衍生 | 简化自由度以模拟更大尺度 |

---

## 工作流程图

```
输入: method, context, language
        │
        ▼
┌──────────────────────────────────────┐
│  步骤 1: Wiki 百科定义               │
│  POST /v1/.../wiki_v2/search_index   │
│  POST /v1/.../wiki_v2/article        │
│  → 搜索方法相关百科词条               │
│  → 获取定义、概念层级、应用领域        │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 2: 论文检索                     │
│  POST /v1/paper/rag/pass/keyword     │
│  → 第一轮：检索方法论综述             │
│  → 第二轮：检索经典原始论文           │
│  → 第三轮：检索实践教程类论文         │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 3: PDF 解析                     │
│  POST /v1/parse/trigger-url-async    │
│  POST /v1/parse/get-result (轮询)     │
│  → 选取最佳综述论文                   │
│  → 解析前 5-8 页提取方法核心步骤       │
│  → 识别参数表格、算法伪代码           │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 4: 知识图谱补充                 │
│  POST /v1/lkm/search                │
│  → 搜索方法的前置知识                │
│  → 搜索衍生/替代方法                 │
│  → 搜索方法的已知局限               │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 5: 综合生成方法卡片             │
│  → 合并 Wiki 定义 + PDF 方法步骤       │
│  → 提取参数与调参建议                │
│  → 整理适用/不适用场景               │
│  → 列出常见陷阱                      │
│  → 排序推荐论文清单                  │
│  → 构建相关方法网络                  │
│  → 基于论文统计生成实操决策指南       │
│  → 统计各子方向的方法使用频率         │
└──────────────────────────────────────┘
```

---

## 通用代码模板

```python
import os, sys, json, time, re, requests
from collections import Counter, defaultdict

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误: 请设置环境变量 ACCESS_KEY")
    print("请在 ~/.openclaw/openclaw.json 中配置 method-wiki.env.ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET = {"accessKey": AK}
```

---

## 分步说明

### Step 1: Wiki 百科定义 (wiki)

**目标：** 搜索方法相关的百科词条，获取权威定义、概念层级和应用领域信息。这一步为方法卡片提供"定义"和"核心原理"的骨架。

**API 调用：**

```
# 搜索词条索引
POST https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2/search_index_name
Header: accessKey: $ACCESS_KEY, Content-Type: application/json
Body: {
    "name": "molecular dynamics",
    "node_types": ["field", "topic"],
    "style": "Feynman"
}
返回: {"wiki_indices": [{"node_id": "...", "node_name": "...", "node_type": "..."}]}

# 获取词条正文
POST https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2/article
Body: {
    "node_id": "...",
    "language": "en-US",
    "style": "Feynman"
}
返回: {"document": {"article_name": "...", "main_content": "...", "applications": "..."}}
```

**关键返回字段：**

| 字段 | 用途 |
|------|------|
| `node_name` | 词条名称，确认匹配正确 |
| `node_type` | `field` 或 `topic`，判断方法所属层级 |
| `main_content` | 正文内容，提取定义和原理 |
| `applications` | 应用领域信息，填充适用场景 |

### Step 2: 论文检索 (paper-search)

**目标：** 分三轮检索——方法论综述（了解方法全貌）、经典原始论文（追溯方法起源）、实践教程类论文（获取参数和代码）。从结果中筛选出最能解释该方法的论文。

**API 调用：**

```
POST https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword
Header: accessKey: $ACCESS_KEY, Content-Type: application/json
Body: {
    "words": ["molecular dynamics", "review", "tutorial"],
    "question": "comprehensive review of molecular dynamics simulation method",
    "type": 5,
    "startTime": "",
    "endTime": "",
    "jcrZones": [],
    "pageSize": 20
}
```

**三轮检索策略：**

| 轮次 | 目的 | 关键词策略 | 排序依据 |
|------|------|-----------|---------|
| A | 方法论综述 | method + review/survey/tutorial | 引用数 |
| B | 经典原始论文 | method + original/seminal + Q1 | 引用数（仅保留 >100 引用） |
| C | 实践教程 | method + tutorial/guide/implementation/code | 发表时间（优先近 3 年） |

**关键返回字段：**

| 字段 | 用途 |
|------|------|
| `enName` | 论文标题，判断是否为综述/教程 |
| `enAbstract` | 摘要，提取方法概述 |
| `citationNums` | 引用数，筛选高影响力论文 |
| `doi` | DOI，用于后续 PDF 解析 |
| `coverDateStart` | 发表日期，区分经典与最新 |
| `publicationEnName` | 期刊名 |
| `impactFactor` | 影响因子 |

### Step 3: PDF 解析 (pdf-parser)

**目标：** 选取 Step 2 中最佳的综述论文，解析其前 5-8 页（通常包含方法概述、核心步骤、参数表格），提取方法的具体实施细节和关键参数。

**API 调用：**

```
# 提交解析任务
POST https://open.bohrium.com/openapi/v1/parse/trigger-url-async
Body: {
    "url": "https://doi.org/10.xxxx/...",
    "sync": false,
    "textual": true,
    "table": true,
    "expression": true,
    "equation": true,
    "pages": [0, 1, 2, 3, 4, 5, 6, 7],
    "timeout": 1800
}
返回: {"token": "...", "status": "undefined"}

# 轮询结果
POST https://open.bohrium.com/openapi/v1/parse/get-result
Body: {
    "token": "...",
    "content": true,
    "objects": false,
    "pages_dict": true
}
返回: {"status": "success", "content": "...", "pages_dict": {...}}
```

**从解析内容中提取的信息：**

| 提取目标 | 提取策略 |
|----------|---------|
| 方法核心步骤 | 定位含 "algorithm"、"procedure"、"steps" 的段落 |
| 参数表格 | 识别 `\begin{table}` 标记中的参数名与取值范围 |
| 数学公式 | 提取核心方程（如 MD 中的牛顿方程、DFT 中的 Kohn-Sham 方程） |
| 注意事项 | 定位含 "caution"、"note"、"pitfall"、"common mistake" 的段落 |

### Step 4: 知识图谱补充 (lkm)

**目标：** 从知识图谱中搜索方法的前置知识、衍生方法、替代方法和已知局限，构建方法的关系网络。

**API 调用：**

```
POST https://open.bohrium.com/openapi/v1/lkm/search
Body: {"query": "prerequisites for molecular dynamics simulation", "limit": 10}

POST https://open.bohrium.com/openapi/v1/lkm/search
Body: {"query": "methods derived from molecular dynamics", "limit": 10}

POST https://open.bohrium.com/openapi/v1/lkm/search
Body: {"query": "alternatives to molecular dynamics simulation", "limit": 10}

POST https://open.bohrium.com/openapi/v1/lkm/search
Body: {"query": "limitations and pitfalls of molecular dynamics", "limit": 10}
```

**四组查询策略：**

| 查询 | 目的 | 填充卡片部分 |
|------|------|------------|
| `prerequisites for {method}` | 前置知识 | 相关方法（关系=前置） |
| `methods derived from {method}` | 衍生方法 | 相关方法（关系=衍生） |
| `alternatives to {method}` | 替代方法 | 相关方法（关系=替代） |
| `limitations and pitfalls of {method}` | 已知局限 | 常见陷阱 |

---

## 完整编排脚本

以下脚本实现从输入到输出的完整方法卡片生成流程。

```python
#!/usr/bin/env python3
"""
方法论百科 (Method Wiki) — 完整编排脚本

用法:
    export ACCESS_KEY="your_access_key"
    python3 method_wiki.py

可修改下方 CONFIG 区域的参数来调整目标方法。
"""

import os
import sys
import json
import time
import re
import requests
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# ============================================================
# 配置
# ============================================================

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误: 请设置环境变量 ACCESS_KEY")
    print("请在 ~/.openclaw/openclaw.json 中配置 method-wiki.env.ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET = {"accessKey": AK}

# -- 用户可修改区域 --
CONFIG = {
    "method": "molecular dynamics",                # 修改为目标方法名称
    "context": "",                                 # 可选：使用场景说明
    "language": "en-US",                           # Wiki 语言: "en-US" 或 "zh-CN"
}


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


def search_papers_raw(keywords, question, start_time="", end_time="",
                      jcr_zones=None, page_size=20):
    """论文检索，返回解析后的论文列表"""
    payload = {
        "words": keywords,
        "question": question,
        "type": 5,
        "startTime": start_time,
        "endTime": end_time,
        "jcrZones": jcr_zones or [],
        "pageSize": page_size,
    }
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
# 步骤 1: Wiki 百科定义
# ============================================================

def step1_wiki_definition(config):
    """
    搜索方法相关百科词条，获取定义、概念层级和应用领域。
    """
    print(f"\n{'='*60}")
    print(f"步骤 1: Wiki 百科定义")
    print(f"  方法: {config['method']}")
    print(f"{'='*60}\n")

    WIKI_BASE = f"{BASE}/v1/literature-sage/wiki_v2"
    wiki_entries = []

    # 1a. 搜索词条索引
    print(f"  搜索词条索引: {config['method']}")
    data = safe_request("POST", f"{WIKI_BASE}/search_index_name",
        headers=HEADERS,
        json={
            "name": config["method"],
            "node_types": ["field", "topic"],
            "style": "Feynman",
        }
    )

    indices = []
    if data and data.get("wiki_indices"):
        indices = data["wiki_indices"]
        print(f"    找到 {len(indices)} 个词条索引")
        for idx in indices[:5]:
            print(f"      [{idx['node_type']}] {idx['node_name']} "
                  f"(id={idx['node_id']})")
    else:
        print(f"    未找到精确匹配词条，尝试拆分关键词搜索...")
        # 尝试拆分关键词（如 "variational autoencoder" -> "variational", "autoencoder"）
        for keyword in config["method"].split():
            if len(keyword) <= 3:
                continue
            data = safe_request("POST", f"{WIKI_BASE}/search_index_name",
                headers=HEADERS,
                json={
                    "name": keyword,
                    "node_types": ["field", "topic"],
                    "style": "Feynman",
                }
            )
            if data and data.get("wiki_indices"):
                existing_ids = {i["node_id"] for i in indices}
                for idx in data["wiki_indices"]:
                    if idx["node_id"] not in existing_ids:
                        indices.append(idx)
                        existing_ids.add(idx["node_id"])
                print(f"    关键词 '{keyword}' 补充 "
                      f"{len(data['wiki_indices'])} 个词条")

    print(f"    合计索引: {len(indices)} 个")

    # 1b. 获取词条正文（取前 3 个最相关的）
    print(f"\n  获取词条正文（最多 3 个）...")
    for idx in indices[:3]:
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
                "main_content": doc.get("main_content", ""),
                "applications": doc.get("applications", ""),
            }
            wiki_entries.append(entry)
            print(f"      标题: {entry['article_name']}")
            print(f"      内容长度: {len(entry['main_content'])} 字符")
        else:
            print(f"      未获取到正文")

    print(f"\n  获取百科词条: {len(wiki_entries)} 个")
    return indices, wiki_entries


# ============================================================
# 步骤 2: 论文检索（三轮）
# ============================================================

def step2_search_papers(config):
    """
    三轮检索：
      轮次 A — 方法论综述：method + review/survey/tutorial
      轮次 B — 经典原始论文：method + Q1 高引
      轮次 C — 实践教程：method + tutorial/guide/code（近 3 年）
    """
    print(f"\n{'='*60}")
    print(f"步骤 2: 论文检索（三轮）")
    print(f"  方法: {config['method']}")
    print(f"{'='*60}\n")

    method = config["method"]
    all_papers = []
    seen_dois = set()

    # --- 轮次 A: 方法论综述 ---
    print("  轮次 A: 检索方法论综述...")
    reviews = search_papers_raw(
        keywords=[method, "review", "survey", "tutorial"],
        question=f"comprehensive review of {method} method: principles, algorithms, applications",
        page_size=20,
    )
    reviews.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
    for p in reviews:
        doi = p.get("doi", "")
        if doi and doi not in seen_dois:
            seen_dois.add(doi)
            p["_search_round"] = "review"
            all_papers.append(p)
    print(f"    检索到 {len(reviews)} 篇，去重后新增 "
          f"{sum(1 for p in all_papers if p['_search_round']=='review')} 篇")

    # --- 轮次 B: 经典原始论文 ---
    print(f"\n  轮次 B: 检索经典原始论文（高引 Q1）...")
    classics = search_papers_raw(
        keywords=[method],
        question=f"original foundational paper that proposed or established {method}",
        jcr_zones=["Q1"],
        page_size=15,
    )
    classics.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
    count_before = len(all_papers)
    for p in classics:
        doi = p.get("doi", "")
        if doi and doi not in seen_dois:
            seen_dois.add(doi)
            p["_search_round"] = "classic"
            all_papers.append(p)
    print(f"    检索到 {len(classics)} 篇，去重后新增 "
          f"{len(all_papers) - count_before} 篇")

    # --- 轮次 C: 实践教程（近 3 年） ---
    end_time = datetime.now().strftime("%Y-%m-%d")
    start_time = (datetime.now() - timedelta(days=3*365)).strftime("%Y-%m-%d")
    print(f"\n  轮次 C: 检索实践教程（{start_time} ~ {end_time}）...")
    tutorials = search_papers_raw(
        keywords=[method, "tutorial", "guide", "implementation", "best practices"],
        question=f"practical tutorial or implementation guide for {method}",
        start_time=start_time,
        end_time=end_time,
        page_size=15,
    )
    tutorials.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
    count_before = len(all_papers)
    for p in tutorials:
        doi = p.get("doi", "")
        if doi and doi not in seen_dois:
            seen_dois.add(doi)
            p["_search_round"] = "tutorial"
            all_papers.append(p)
    print(f"    检索到 {len(tutorials)} 篇，去重后新增 "
          f"{len(all_papers) - count_before} 篇")

    print(f"\n  合计: {len(all_papers)} 篇论文"
          f"（综述 + 经典 + 教程）")

    return all_papers


# ============================================================
# 步骤 3: PDF 解析（综述论文）
# ============================================================

def step3_parse_review(all_papers):
    """
    选取最佳综述论文，解析前 8 页提取方法核心步骤、参数表格等。
    """
    print(f"\n{'='*60}")
    print(f"步骤 3: PDF 解析（综述论文）")
    print(f"{'='*60}\n")

    # 选取最佳综述论文：优先选标题含 review/survey/tutorial 且引用最高的
    review_keywords = ["review", "survey", "tutorial", "overview",
                       "introduction", "guide", "primer"]
    candidates = []
    for p in all_papers:
        title = (p.get("enName") or "").lower()
        abstract = (p.get("enAbstract") or "").lower()
        is_review = any(kw in title or kw in abstract for kw in review_keywords)
        if is_review:
            candidates.append(p)

    if not candidates:
        # 退而求其次：按引用数取前 2 篇
        candidates = sorted(all_papers, key=lambda p: p.get("citationNums", 0),
                            reverse=True)[:2]
        print("  未找到明确的综述论文，选择高引论文进行解析")

    # 最多解析 2 篇
    to_parse = candidates[:2]
    parsed_results = []

    for p in to_parse:
        doi = p.get("doi", "")
        title = p.get("enName", "")
        if not doi:
            print(f"  跳过（无 DOI）: {title[:60]}")
            continue

        pdf_url = f"https://doi.org/{doi}"
        print(f"\n  解析: {title[:60]}...")
        print(f"    URL: {pdf_url}")

        # 提交解析任务（前 8 页）
        try:
            r = requests.post(
                f"{BASE}/v1/parse/trigger-url-async",
                headers=HEADERS,
                json={
                    "url": pdf_url,
                    "sync": False,
                    "textual": True,
                    "table": True,
                    "expression": True,
                    "equation": True,
                    "pages": [0, 1, 2, 3, 4, 5, 6, 7],
                    "timeout": 1800,
                },
                timeout=30,
            )
            r.raise_for_status()
            submit = r.json()
        except Exception as e:
            print(f"    提交失败: {e}")
            continue

        if submit.get("code"):
            print(f"    提交失败: {submit.get('message', '未知错误')}")
            continue

        token = submit["token"]
        print(f"    已提交，token={token}")

        # 轮询结果（最多等 90 秒）
        content = ""
        for attempt in range(45):
            time.sleep(2)
            try:
                r = requests.post(
                    f"{BASE}/v1/parse/get-result",
                    headers=HEADERS,
                    json={
                        "token": token,
                        "content": True,
                        "objects": False,
                        "pages_dict": True,
                    },
                    timeout=30,
                )
                result = r.json()
            except Exception as e:
                if attempt % 10 == 0:
                    print(f"    [{attempt+1}] 查询失败: {e}")
                continue

            status = result.get("status", "")
            if status == "success":
                content = result.get("content", "")
                print(f"    解析完成！内容长度 {len(content)} 字符")
                break
            elif status == "failed":
                print(f"    解析失败: {result.get('description', '未知错误')}")
                break
            else:
                if attempt % 10 == 0:
                    proc = result.get("proc_page", 0)
                    total = result.get("total_page", 0)
                    print(f"    [{attempt+1}] 解析中... ({proc}/{total} 页)")

        if content:
            parsed_results.append({
                "doi": doi,
                "title": title,
                "content": content,
            })

    print(f"\n  成功解析: {len(parsed_results)} 篇")
    return parsed_results


def extract_method_details(parsed_results):
    """
    从解析的综述论文中提取方法细节：步骤、参数、注意事项。
    """
    method_steps = []
    parameter_hints = []
    pitfall_hints = []

    step_patterns = [
        r'(?i)(?:step|stage|phase)\s*\d[^.]*\.',
        r'(?i)(?:algorithm|procedure|protocol)\s*[:.].*?(?:\n|$)',
    ]

    param_patterns = [
        r'(?i)(?:parameter|hyperparameter|setting|configuration)\s*[:.].*?(?:\n|$)',
        r'(?i)(?:typical|default|recommended)\s+(?:value|range|setting)[^.]*\.',
    ]

    pitfall_patterns = [
        r'(?i)(?:caution|note|warning|pitfall|common\s+mistake|'
        r'common\s+error|should\s+be\s+careful|avoid)[^.]*\.',
        r'(?i)(?:a\s+common\s+(?:issue|problem|challenge))[^.]*\.',
    ]

    for pr in parsed_results:
        content = pr["content"]

        # 提取方法步骤
        for pattern in step_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                cleaned = m.strip()
                if 15 < len(cleaned) < 500:
                    method_steps.append(cleaned)

        # 提取参数建议
        for pattern in param_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                cleaned = m.strip()
                if 15 < len(cleaned) < 500:
                    parameter_hints.append(cleaned)

        # 提取注意事项
        for pattern in pitfall_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                cleaned = m.strip()
                if 15 < len(cleaned) < 500:
                    pitfall_hints.append(cleaned)

    # 去重
    method_steps = list(dict.fromkeys(method_steps))[:10]
    parameter_hints = list(dict.fromkeys(parameter_hints))[:10]
    pitfall_hints = list(dict.fromkeys(pitfall_hints))[:10]

    return {
        "method_steps": method_steps,
        "parameter_hints": parameter_hints,
        "pitfall_hints": pitfall_hints,
    }


# ============================================================
# 步骤 4: 知识图谱补充 (lkm)
# ============================================================

def step4_lkm_relations(config):
    """
    从知识图谱中搜索方法的前置知识、衍生方法、替代方法和已知局限。
    """
    print(f"\n{'='*60}")
    print(f"步骤 4: 知识图谱补充")
    print(f"{'='*60}\n")

    method = config["method"]
    relations = {
        "prerequisites": [],
        "derivatives": [],
        "alternatives": [],
        "limitations": [],
    }

    queries = {
        "prerequisites": f"prerequisites and foundational concepts for {method}",
        "derivatives": f"methods derived from or extending {method}",
        "alternatives": f"alternative methods to {method}",
        "limitations": f"limitations pitfalls and known issues of {method}",
    }

    for relation_type, query in queries.items():
        print(f"  查询 [{relation_type}]: {query[:50]}...")
        data = safe_request("POST", f"{BASE}/v1/lkm/search",
            headers=HEADERS,
            json={"query": query, "limit": 10},
        )
        if data and data.get("data"):
            results = data["data"] if isinstance(data["data"], list) else [data["data"]]
            relations[relation_type] = results
            print(f"    返回 {len(results)} 个知识节点")
        else:
            print(f"    未返回有效数据")

    # 额外搜索方法本身的核心概念
    print(f"\n  补充搜索: 方法核心概念...")
    data = safe_request("POST", f"{BASE}/v1/lkm/search",
        headers=HEADERS,
        json={"query": f"core principles and theory of {method}", "limit": 10},
    )
    core_concepts = []
    if data and data.get("data"):
        core_concepts = data["data"] if isinstance(data["data"], list) else [data["data"]]
        print(f"    返回 {len(core_concepts)} 个核心概念")

    relations["core_concepts"] = core_concepts
    return relations


# ============================================================
# 步骤 5: 综合生成方法卡片
# ============================================================

def build_reading_list(all_papers):
    """
    构建推荐论文清单，按类型排序：经典原始论文 → 权威综述 → 实践教程。
    """
    review_kws = ["review", "survey", "perspective", "overview"]
    tutorial_kws = ["tutorial", "guide", "introduction to", "primer",
                    "best practices", "practical"]

    originals = []
    reviews = []
    tutorials = []
    others = []

    for p in all_papers:
        title = (p.get("enName") or "").lower()
        abstract = (p.get("enAbstract") or "").lower()
        citations = p.get("citationNums", 0)
        round_type = p.get("_search_round", "")

        is_review = any(kw in title or kw in abstract for kw in review_kws)
        is_tutorial = any(kw in title or kw in abstract for kw in tutorial_kws)

        if is_tutorial:
            tutorials.append(p)
        elif is_review:
            reviews.append(p)
        elif citations > 100 and round_type == "classic":
            originals.append(p)
        else:
            others.append(p)

    # 各类别内按引用降序
    originals.sort(key=lambda x: x.get("citationNums", 0), reverse=True)
    reviews.sort(key=lambda x: x.get("citationNums", 0), reverse=True)
    tutorials.sort(key=lambda x: x.get("citationNums", 0), reverse=True)
    others.sort(key=lambda x: x.get("citationNums", 0), reverse=True)

    reading_list = []
    categories = [
        ("经典原始论文", originals, 3),
        ("权威综述", reviews, 4),
        ("实践教程", tutorials, 3),
        ("补充阅读", others, 2),
    ]

    for cat_name, cat_papers, max_count in categories:
        for p in cat_papers[:max_count]:
            reading_list.append({
                "category": cat_name,
                "title": p.get("enName", ""),
                "doi": p.get("doi", ""),
                "year": p.get("coverDateStart", "")[:4],
                "citations": p.get("citationNums", 0),
                "journal": p.get("publicationEnName", ""),
                "impact_factor": p.get("impactFactor", 0),
                "reason": _recommend_reason(p, cat_name),
            })
            if len(reading_list) >= 12:
                break
        if len(reading_list) >= 12:
            break

    return reading_list


def _recommend_reason(paper, category):
    """生成推荐理由"""
    citations = paper.get("citationNums", 0)
    impact_factor = paper.get("impactFactor", 0)

    if category == "经典原始论文":
        if citations > 500:
            return f"领域奠基性工作，极高引用（{citations}）"
        return "方法提出的原始论文"
    elif category == "权威综述":
        if impact_factor > 10:
            return f"高影响因子期刊综述（IF={impact_factor}），系统梳理方法全貌"
        return "系统性综述，适合全面了解方法"
    elif category == "实践教程":
        return "含实践指导，适合快速上手"
    else:
        return "领域相关高质量论文"


def build_related_methods(lkm_relations):
    """
    从 LKM 结果中构建相关方法网络。
    """
    related = []

    relation_map = {
        "prerequisites": "前置知识",
        "derivatives": "衍生方法",
        "alternatives": "替代方法",
    }

    for relation_type, label in relation_map.items():
        concepts = lkm_relations.get(relation_type, [])
        for concept in concepts:
            name = ""
            description = ""
            if isinstance(concept, dict):
                name = concept.get("name", concept.get("content",
                    concept.get("query", "")))
                description = concept.get("description",
                    concept.get("text", ""))
            elif isinstance(concept, str):
                name = concept

            if name:
                related.append({
                    "method": name,
                    "relation": label,
                    "description": description[:100] if description else "",
                })

    # 去重
    seen = set()
    unique_related = []
    for r in related:
        key = r["method"].lower()
        if key not in seen:
            seen.add(key)
            unique_related.append(r)

    return unique_related[:15]


def step5_synthesize(config, wiki_entries, all_papers, parsed_results,
                     method_details, lkm_relations):
    """综合所有数据，生成方法卡片。"""
    print(f"\n{'='*60}")
    print(f"步骤 5: 综合生成方法卡片")
    print(f"{'='*60}\n")

    method = config["method"]

    # 5a. 提取定义和核心原理（从 Wiki）
    print("  5a. 提取定义和核心原理...")
    definition = ""
    core_content = ""
    applications = ""
    for entry in wiki_entries:
        mc = entry.get("main_content", "")
        if mc and not definition:
            # 第一段作为定义
            paragraphs = [p.strip() for p in mc.split('\n') if p.strip()]
            if paragraphs:
                definition = paragraphs[0][:300]
            if len(paragraphs) > 1:
                core_content = "\n".join(paragraphs[1:4])[:800]
        app = entry.get("applications", "")
        if app and not applications:
            applications = app[:500]

    # 5b. 推荐论文清单
    print("  5b. 构建推荐论文清单...")
    reading_list = build_reading_list(all_papers)

    # 5c. 相关方法网络
    print("  5c. 构建相关方法网络...")
    related_methods = build_related_methods(lkm_relations)

    # 5d. 组装卡片
    card = {
        "method": method,
        "context": config.get("context", ""),
        "generated_at": datetime.now().isoformat(),
        "paper_count": len(all_papers),
        "definition": definition,
        "core_content": core_content,
        "applications": applications,
        "method_steps": method_details.get("method_steps", []),
        "parameter_hints": method_details.get("parameter_hints", []),
        "pitfall_hints": method_details.get("pitfall_hints", []),
        "lkm_limitations": lkm_relations.get("limitations", []),
        "reading_list": reading_list,
        "related_methods": related_methods,
        "wiki_entries": wiki_entries,
    }

    return card


# ============================================================
# 格式化输出
# ============================================================

def format_method_card(card):
    """将结构化结果格式化为 Markdown 方法卡片。"""
    lines = []
    method = card["method"]

    lines.append(f"# 方法卡片: {method}")
    lines.append(f"\n> 生成时间: {card['generated_at']}")
    lines.append(f"> 检索论文数: {card['paper_count']}")
    if card.get("context"):
        lines.append(f"> 使用场景: {card['context']}")

    # ---- 1. 一句话定义 ----
    lines.append("\n## 1. 一句话定义\n")
    if card["definition"]:
        lines.append(f"> {card['definition']}")
    else:
        lines.append(f"> （Wiki 中未找到精确定义，请根据论文摘要补充）")

    # ---- 2. 核心原理 ----
    lines.append("\n## 2. 核心原理\n")
    if card["core_content"]:
        lines.append(card["core_content"])
    else:
        lines.append("（待补充：请根据综述论文摘要和 LKM 核心概念整理）")

    # ---- 3. 适用场景与不适用场景 ----
    lines.append("\n## 3. 适用场景与不适用场景\n")
    if card["applications"]:
        lines.append("### 适用场景\n")
        lines.append(card["applications"])
        lines.append("")
    else:
        lines.append("### 适用场景\n")
        lines.append("（请根据 Wiki 应用领域和论文内容补充）\n")

    lines.append("### 不适用场景\n")
    limitations = card.get("lkm_limitations", [])
    if limitations:
        for lim in limitations[:5]:
            text = ""
            if isinstance(lim, dict):
                text = lim.get("content", lim.get("text",
                    lim.get("name", str(lim))))
            elif isinstance(lim, str):
                text = lim
            if text:
                lines.append(f"- {text[:150]}")
    else:
        lines.append("（请根据方法的已知局限补充不适用的场景）")
    lines.append("")

    # ---- 4. 关键参数与调参建议 ----
    lines.append("## 4. 关键参数与调参建议\n")
    hints = card.get("parameter_hints", [])
    if hints:
        lines.append("| # | 参数/设置建议 |")
        lines.append("|---|-------------|")
        for i, hint in enumerate(hints[:8], 1):
            lines.append(f"| {i} | {hint[:200]} |")
    else:
        lines.append("（PDF 解析未提取到明确参数建议，请参阅推荐综述论文中的参数表格）")
    lines.append("")

    # ---- 5. 常见陷阱 / 注意事项 ----
    lines.append("## 5. 常见陷阱 / 注意事项\n")
    pitfalls = card.get("pitfall_hints", [])
    lkm_lims = card.get("lkm_limitations", [])

    all_pitfalls = []
    for p in pitfalls:
        all_pitfalls.append(p)
    for lim in lkm_lims:
        text = ""
        if isinstance(lim, dict):
            text = lim.get("content", lim.get("text",
                lim.get("name", "")))
        elif isinstance(lim, str):
            text = lim
        if text and text not in all_pitfalls:
            all_pitfalls.append(text)

    if all_pitfalls:
        for p in all_pitfalls[:8]:
            lines.append(f"- {p[:200]}")
    else:
        lines.append("（未自动提取到注意事项，请参阅推荐综述论文中的 "
                      "Limitations / Common Mistakes 章节）")
    lines.append("")

    # ---- 6. 推荐教程与论文 ----
    lines.append("## 6. 推荐教程与论文\n")
    lines.append("> 阅读顺序：经典原始论文 -> 权威综述 -> 实践教程\n")
    reading_list = card.get("reading_list", [])
    if reading_list:
        lines.append("| 序号 | 类型 | 标题 | DOI | 年份 | 引用 | 推荐理由 |")
        lines.append("|------|------|------|-----|------|------|----------|")
        for i, r in enumerate(reading_list, 1):
            title = r["title"][:55] + ("..." if len(r["title"]) > 55 else "")
            lines.append(
                f"| {i} | {r['category']} | {title} | "
                f"`{r['doi']}` | {r['year']} | {r['citations']} | "
                f"{r['reason']} |"
            )
    else:
        lines.append("（未检索到相关论文）")
    lines.append("")

    # ---- 7. 相关/替代方法 ----
    lines.append("## 7. 相关/替代方法\n")
    related = card.get("related_methods", [])
    if related:
        lines.append("| 方法 | 关系 | 说明 |")
        lines.append("|------|------|------|")
        for r in related[:10]:
            desc = r["description"][:80] if r["description"] else "—"
            lines.append(f"| {r['method']} | {r['relation']} | {desc} |")
    else:
        lines.append("（知识图谱中未找到明确的关系网络，"
                      "请根据论文中的 Related Work 章节补充）")
    lines.append("")

    # ---- 附录: Wiki 百科原文 ----
    wiki_entries = card.get("wiki_entries", [])
    if wiki_entries:
        lines.append("---\n")
        lines.append("## 附录: 百科原文摘录\n")
        for entry in wiki_entries:
            name = entry.get("article_name") or entry.get("node_name", "")
            lines.append(f"### {name}\n")
            content = entry.get("main_content", "")[:500]
            if content:
                lines.append(f"{content}...\n")

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  方法论百科 (Method Wiki) — {config['method']}")
    if config.get("context"):
        print(f"  使用场景: {config['context']}")
    print(f"{'#'*60}")

    # 步骤 1: Wiki 百科定义
    wiki_indices, wiki_entries = step1_wiki_definition(config)

    # 步骤 2: 论文检索（三轮）
    all_papers = step2_search_papers(config)

    # 步骤 3: PDF 解析
    parsed_results = step3_parse_review(all_papers)
    method_details = extract_method_details(parsed_results)

    # 步骤 4: 知识图谱补充
    lkm_relations = step4_lkm_relations(config)

    # 步骤 5: 综合生成方法卡片
    card = step5_synthesize(
        config, wiki_entries, all_papers, parsed_results,
        method_details, lkm_relations,
    )

    # 输出
    output = format_method_card(card)
    print("\n" + output)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    method_tag = config["method"].replace(" ", "_")
    output_file = f"method_card_{method_tag}_{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n方法卡片已保存到: {output_file}")

    data_file = f"method_card_{method_tag}_{timestamp}_data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2, default=str)
    print(f"原始数据已保存到: {data_file}")


if __name__ == "__main__":
    main()
```

---

## curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# Step 1a: Wiki 搜索词条索引
curl -s -X POST "https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2/search_index_name" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{
    "name": "molecular dynamics",
    "node_types": ["field", "topic"],
    "style": "Feynman"
  }'

# Step 1b: Wiki 获取词条正文
curl -s -X POST "https://open.bohrium.com/openapi/v1/literature-sage/wiki_v2/article" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{
    "node_id": "NODE_ID_HERE",
    "language": "en-US",
    "style": "Feynman"
  }'

# Step 2a: 检索方法论综述
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{
    "words": ["molecular dynamics", "review", "survey", "tutorial"],
    "question": "comprehensive review of molecular dynamics method: principles, algorithms, applications",
    "type": 5,
    "pageSize": 20
  }'

# Step 2b: 检索经典原始论文
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{
    "words": ["molecular dynamics"],
    "question": "original foundational paper that proposed or established molecular dynamics",
    "type": 5,
    "jcrZones": ["Q1"],
    "pageSize": 15
  }'

# Step 2c: 检索实践教程（近 3 年）
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{
    "words": ["molecular dynamics", "tutorial", "guide", "implementation", "best practices"],
    "question": "practical tutorial or implementation guide for molecular dynamics",
    "type": 5,
    "startTime": "2023-01-01",
    "endTime": "2026-05-13",
    "pageSize": 15
  }'

# Step 3a: 提交 PDF 解析（综述论文前 8 页）
TOKEN=$(curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/trigger-url-async" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{
    "url": "https://doi.org/10.xxxx/review_paper_doi",
    "sync": false,
    "textual": true,
    "table": true,
    "expression": true,
    "equation": true,
    "pages": [0, 1, 2, 3, 4, 5, 6, 7],
    "timeout": 1800
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "Token: $TOKEN"

# Step 3b: 轮询解析结果
sleep 10
curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/get-result" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\", \"content\": true, \"objects\": false, \"pages_dict\": true}"

# Step 4a: LKM 搜索前置知识
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"query": "prerequisites and foundational concepts for molecular dynamics", "limit": 10}'

# Step 4b: LKM 搜索衍生方法
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"query": "methods derived from or extending molecular dynamics", "limit": 10}'

# Step 4c: LKM 搜索替代方法
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"query": "alternative methods to molecular dynamics", "limit": 10}'

# Step 4d: LKM 搜索已知局限
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"query": "limitations pitfalls and known issues of molecular dynamics", "limit": 10}'
```

---

## 使用示例

### 示例 1: 不带使用场景

```python
CONFIG = {
    "method": "variational autoencoder",
    "context": "",
    "language": "en-US",
}
```

### 示例 2: 带使用场景（上下文相关检索）

```python
CONFIG = {
    "method": "density functional theory",
    "context": "我想用它来计算锂电池正极材料的电子结构",
    "language": "zh-CN",
}
```

### 示例 3: 命令行快速调用

```bash
export ACCESS_KEY="your_key"

# 直接修改脚本中的 CONFIG 后运行
python3 method_wiki.py

# 或通过环境变量传参（需在脚本中添加对应读取逻辑）
METHOD="molecular dynamics" python3 method_wiki.py
```

---

## 使用技巧

### 方法名称选择

```python
# 推荐：使用标准英文术语
method = "molecular dynamics"
method = "variational autoencoder"
method = "density functional theory"
method = "Monte Carlo tree search"
method = "transformer attention mechanism"

# 不推荐：太笼统或用缩写
method = "MD"           # 太模糊，可能匹配到医学领域
method = "DFT"          # 太模糊，可能匹配到信号处理
method = "deep learning" # 太宽泛，不是具体方法
```

### 使用场景的作用

提供 `context` 参数可以帮助：

- 论文检索时更聚焦于特定应用领域的方法综述
- 输出卡片中的"适用场景"部分更贴合用户需求
- 推荐论文优先返回与用户场景相关的教程

```python
# 不带场景：返回通用的 MD 方法卡片
CONFIG = {"method": "molecular dynamics", "context": ""}

# 带场景：偏向蛋白质模拟领域的 MD 方法介绍
CONFIG = {"method": "molecular dynamics", "context": "模拟蛋白质折叠过程"}
```

### 分段执行

网络不稳定时，可以将步骤拆开独立执行，每步保存中间结果为 JSON：

```python
# 保存 Step 1 结果
indices, wiki_entries = step1_wiki_definition(config)
with open("step1_wiki.json", "w") as f:
    json.dump({"indices": indices, "entries": wiki_entries}, f, ensure_ascii=False)

# 保存 Step 2 结果
all_papers = step2_search_papers(config)
with open("step2_papers.json", "w") as f:
    json.dump(all_papers, f, ensure_ascii=False)

# 后续步骤从文件加载
with open("step2_papers.json") as f:
    all_papers = json.load(f)
```

---

## 搭配使用

- **method-wiki** 快速了解方法原理 → **paper-dissector** 精读方法论文
- **method-wiki** 发现相关方法 → **tech-compare** 对比多种方法的优劣
- **method-wiki** 获取推荐论文 → **bohrium-pdf-parser** 解析全文精读
- **method-wiki** 梳理方法全貌 → **literature-review** 深度综述该方法的进展
- **method-wiki** 识别前置知识 → 递归调用 **method-wiki** 补全知识链
- **method-wiki** 保存卡片 → **bohrium-knowledge-base** 存入知识库归档

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Wiki 搜索结果为空 | 方法名称在百科中未收录或使用了非标准名称 | 尝试换用英文全称、常见别名或拆分关键词搜索 |
| 论文检索结果太少 | 方法过于小众或关键词太窄 | 去掉 JCR 分区限制，扩大关键词（加入上位概念） |
| PDF 解析失败 | DOI 对应的 PDF 不可直接下载 | 改用 arXiv PDF 链接或其他可直接访问的 URL |
| PDF 解析超时 | 论文页数多或服务器负载高 | 脚本已限制仅解析前 8 页，可进一步减少页数 |
| 参数建议提取为空 | 综述论文中未使用标准化的参数描述 | 正常现象，请参阅推荐论文原文中的参数表格 |
| 陷阱提取为空 | 论文中未明确列出 pitfalls/warnings | 检查 LKM limitations 结果，或手动查阅推荐综述 |
| LKM 相关方法为空 | 知识图谱未覆盖该方法的关系网络 | 检查推荐论文的 Related Work 章节，手动补充 |
| 论文检索返回多行 JSON | paper-search 采用 streaming 格式 | 取第一行解析：`json.loads(r.text.split('\n')[0])` |
| 401 Unauthorized | accessKey 无效 | 检查 `~/.openclaw/openclaw.json` 中的配置 |
| 方法卡片定义不准确 | Wiki 返回的词条不是最佳匹配 | 检查 Step 1 返回的词条列表，手动指定 node_id 重新获取 |
