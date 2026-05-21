---
name: collaborator-finder
description: "Potential collaborator discovery by matching research complementarity, activity level, and expertise gaps. Use when: user is looking for research collaborators with complementary skills or resources. NOT for: scholar profile lookup (use scholar-profiler), paper search (use bohrium-paper-search)."
---

# SKILL: 合作者发现 (Collaborator Finder)

## 概述

合作者发现是一个**编排型技能**，通过组合 `scholar-search`、`paper-search`、`lkm` 三个原子技能，根据用户自身研究方向和合作需求，自动搜索、筛选并推荐具有互补性的潜在合作者。

**编排流程：**

```
用户输入：自身研究方向 + 合作需求 + 地域偏好（可选）
        │
        ▼
┌─────────────────────────┐
│  Step 1: scholar-search  │  按需求关键词搜索活跃学者 → 获取基础信息
│  POST scholar/search     │  逐个拉取 scholar/info → 研究方向、发文量、h-index
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Step 2: paper-search    │  检索候选学者的发表记录 → 验证真实产出
│  POST paper/rag/pass/    │  分析近期活跃度、研究重点、代表作
│       keyword            │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Step 3: lkm search      │  分析用户方向与候选者方向在知识图谱中的连接
│  POST lkm/search         │  评估互补性：弱连接 = 高互补潜力
└────────┬────────────────┘
         │
         ▼
  5-10 位推荐合作者报告
  （方向匹配度、互补性说明、活跃度、代表作、联系线索）
```

**适用场景：**

- 寻找拥有互补实验/计算/理论能力的合作者
- 跨学科项目组建团队时发现潜在人选
- 基金申请时寻找合适的合作单位和负责人
- 研究方向拓展时寻找在目标领域有积累的学者

**不适用：**

- 查看已知学者的完整画像 → `scholar-profiler`
- 检索特定论文 → `bohrium-paper-search`
- 文献综述 → `literature-review`
- 领域技术对比 → `tech-compare`

**无 CLI 支持** — 通过 Python 脚本编排多个 HTTP API 完成。

## 认证配置

本技能复用底层原子技能共同的 ACCESS_KEY：

```json
"collaborator-finder": {
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
            的 collaborator-finder.env.ACCESS_KEY 中填入从 https://bohrium.dp.tech
            个人设置页获取的 AccessKey，然后重启 OpenClaw 会话。」
```

**重要：** 不要把 AccessKey 另存到其他文件或写死到代码，统一通过 OpenClaw 环境变量注入。

### 错误处理

若 API 返回 `Invalid AccessKey`（code 2000）或 HTTP 401：
1. 说明 OpenClaw 配置中的 Key 已失效或错误
2. 提示用户：「您的 AccessKey 已失效，请在 `~/.openclaw/openclaw.json` 中更新 `collaborator-finder.env.ACCESS_KEY` 并重启 OpenClaw 会话。」

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `my_direction` | string | 是 | 自身研究方向描述，如"分子动力学模拟"、"锂电池正极材料" |
| `collaboration_need` | string | 是 | 合作需求描述，如"需要实验验证"、"需要算法专长"、"需要高通量计算资源" |
| `geo_preference` | string | 否 | 地域偏好，如"中国"、"北美"、"欧洲"，留空不限 |

## 输出结构

推荐合作者报告包含 5-10 位候选人，每位包含：

| 字段 | 说明 |
|------|------|
| 学者姓名与机构 | 中英文姓名、所属机构 |
| 研究方向匹配度 | 与用户需求的匹配程度评估（高/中/低） |
| 互补性说明 | 候选者能力如何弥补用户的专长缺口 |
| 近期活跃度 | 近 2-3 年发文量、h-index、引用趋势 |
| 代表作品 | 2-3 篇最相关论文（标题、期刊、引用数） |
| 联系线索 | 机构主页或学术平台链接（基于机构信息推测） |
| 数据时效标注 | 学者数据检索日期、论文覆盖时间范围 |

---

## 推荐策略与质量控制

### 分层推荐（关键策略）

**不能只推荐"大牛"**。推荐结果必须包含三个层次的候选者：

1. **领军学者（h-index > 50）**：1-2 位，适合联合承担重大项目或挂名咨询
2. **活跃同行（h-index 20-50）**：3-4 位，最可能建立对等合作关系
3. **新锐学者（h-index 10-20，近 2 年高产）**：2-3 位，合作门槛低、互动意愿强

**推荐理由**：每位候选者必须明确说明"为什么 TA 有动机跟你合作"——纯粹列出"TA 很厉害"不构成合作理由。

### 互补性分析深度要求

互补性说明不能是泛泛的"TA 做实验你做计算"，必须具体到：
- **具体技能缺口**："你缺乏 in-situ XPS 表征能力，TA 在 [具体论文] 中展示了该技术"
- **数据/资源互补**："你有 DFT 数据但缺实验验证，TA 的组有 [具体设备/平台]"
- **协同效应**："你的 X 方法 + TA 的 Y 数据 = 可以解决 Z 问题（目前无人做）"

### 可操作联系建议

"联系线索"必须包含可操作的策略，而非仅给出 Google Scholar 链接：

1. **共同引用切入**：指出你和候选者共同引用了哪些论文，可作为邮件话题
2. **会议机会**：该候选者近期论文投向的会议（可能在那里遇到）
3. **合作先例**：候选者是否有跨组合作的历史（判断合作意愿）
4. **联系方式来源**：标注通讯作者邮箱来源（如"见其 2024 年 Nature 论文通讯作者信息"）

### 数据透明度

每位候选者的信息卡底部**必须标注**：
> 数据来源：Bohrium scholar-search + paper-search（检索日期：YYYY-MM-DD）。论文覆盖范围：[起始时间]-[结束时间]。h-index 和引用数可能与其他数据源有差异。

### 禁止的行为

- ❌ 只推荐 h-index 最高的学者而忽略合作可行性
- ❌ 互补性说明用模板化语言（如"在该领域有丰富经验"）
- ❌ 联系线索只给 Google Scholar 链接而无可操作策略
- ❌ 不区分候选者的合作意愿和可及性
- ❌ h-index/引用数不标注数据来源和时效

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
| `name` | string | 是 | 学者姓名或领域关键词（1~99 字符） |
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
| `words` | string[] | 关键词列表（放入候选学者姓名 + 需求方向） |
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
| `query` | string | 搜索查询（研究方向关键词） |
| `limit` | int | 返回结果数量 |

---

## 完整编排脚本

以下 Python 脚本实现端到端的合作者发现流程。

```python
#!/usr/bin/env python3
"""
合作者发现 (Collaborator Finder)
编排 scholar-search + paper-search + lkm，发现具有互补性的潜在合作者。

用法:
    export ACCESS_KEY="your_access_key"
    python collaborator_finder.py "分子动力学模拟" "需要实验验证能力"
    python collaborator_finder.py "锂电池正极材料" "需要机器学习算法专长" "中国"
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from collections import Counter

# ─── 配置 ───────────────────────────────────────────────

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误：未设置 ACCESS_KEY 环境变量。")
    print("请在 ~/.openclaw/openclaw.json 中配置 collaborator-finder.env.ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"

H_JSON = {"accessKey": AK, "Content-Type": "application/json"}
H_AK   = {"accessKey": AK}


# ─── 辅助函数 ─────────────────────────────────────────────

def extract_need_keywords(collaboration_need: str) -> list[str]:
    """
    从合作需求描述中提取搜索关键词。
    将常见的中文需求映射为英文学术关键词。
    """
    keyword_map = {
        "实验验证": ["experimental", "synthesis", "characterization"],
        "实验": ["experimental", "synthesis", "measurement"],
        "计算": ["computational", "simulation", "DFT", "ab initio"],
        "算法": ["algorithm", "machine learning", "deep learning", "optimization"],
        "机器学习": ["machine learning", "neural network", "deep learning"],
        "深度学习": ["deep learning", "neural network", "graph neural network"],
        "数据": ["dataset", "database", "high-throughput", "data-driven"],
        "高通量": ["high-throughput", "screening", "automated"],
        "理论": ["theoretical", "analytical", "first-principles"],
        "合成": ["synthesis", "fabrication", "preparation"],
        "表征": ["characterization", "spectroscopy", "microscopy"],
        "模拟": ["simulation", "molecular dynamics", "Monte Carlo"],
        "力场": ["force field", "interatomic potential", "molecular dynamics"],
    }

    extracted = []
    need_lower = collaboration_need.lower()
    for zh_key, en_keywords in keyword_map.items():
        if zh_key in collaboration_need:
            extracted.extend(en_keywords)

    # 如果映射未命中，直接将需求作为关键词
    if not extracted:
        extracted = [w.strip() for w in collaboration_need.replace("，", ",").split(",")
                     if w.strip()]

    # 去重并保序
    seen = set()
    unique = []
    for kw in extracted:
        if kw.lower() not in seen:
            seen.add(kw.lower())
            unique.append(kw)

    return unique[:6]


def compute_activity_score(papers: list, current_year: int) -> dict:
    """
    根据论文列表计算学者近期活跃度。
    返回 {recent_count, total_count, recent_citations, activity_level}。
    """
    recent_cutoff = current_year - 2
    recent_papers = []
    total_citations = 0

    for p in papers:
        year_str = p.get("coverDateStart", "")[:4]
        if year_str and year_str.isdigit():
            total_citations += p.get("citationNums", 0)
            if int(year_str) >= recent_cutoff:
                recent_papers.append(p)

    recent_citations = sum(p.get("citationNums", 0) for p in recent_papers)

    if len(recent_papers) >= 5:
        activity_level = "高"
    elif len(recent_papers) >= 2:
        activity_level = "中"
    else:
        activity_level = "低"

    return {
        "recent_count": len(recent_papers),
        "total_count": len(papers),
        "recent_citations": recent_citations,
        "total_citations": total_citations,
        "activity_level": activity_level,
    }


# ─── 步骤 1：搜索候选学者 ──────────────────────────────────

def search_candidate_scholars(
    collaboration_need: str,
    need_keywords: list[str],
    geo_preference: str = "",
    max_candidates: int = 15,
) -> list[dict]:
    """
    根据合作需求关键词搜索候选学者。
    对每位候选者拉取详情，收集研究方向和基础指标。
    返回候选学者列表。
    """
    print(f"[步骤 1/3] 搜索候选学者")
    print(f"  需求关键词：{need_keywords}")
    if geo_preference:
        print(f"  地域偏好：{geo_preference}")

    candidates = []
    seen_ids = set()

    # 用多组关键词搜索，扩大覆盖面
    search_queries = need_keywords[:4]  # 最多用前 4 个关键词分别搜索

    for query in search_queries:
        payload = {
            "name": query,
            "page": 1,
            "pageSize": 10,
        }
        if geo_preference:
            payload["school"] = geo_preference

        try:
            r = requests.post(
                f"{BASE}/v1/paper-server/scholar/search",
                headers=H_JSON,
                json=payload,
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  搜索「{query}」失败：{e}")
            continue

        items = data.get("data", {}).get("items", [])
        print(f"  搜索「{query}」→ 返回 {len(items)} 位学者")

        for item in items:
            sid = item.get("scholarId", "")
            if not sid or sid in seen_ids:
                continue
            seen_ids.add(sid)

            # 拉取学者详情
            try:
                r = requests.get(
                    f"{BASE}/v1/paper-server/scholar/info",
                    headers=H_AK,
                    params={"scholarId": sid},
                    timeout=30,
                )
                r.raise_for_status()
                info = r.json().get("data", {})
            except Exception:
                info = item

            candidate = {
                "scholarId": sid,
                "nameEn": info.get("nameEn", item.get("nameEn", "")),
                "nameZh": info.get("nameZh", item.get("nameZh", "")),
                "institution": (info.get("scholarOrgNameEn", "") or
                                info.get("scholarOrgNameZh", "") or
                                item.get("scholarOrgNameEn", "")),
                "paperNums": info.get("paperNums", item.get("paperNums", 0)),
                "citationNums": info.get("citationNums", item.get("citationNums", 0)),
                "hIndex": info.get("hIndex", item.get("hIndex", 0)),
                "isHighCited": item.get("isHighCited", False),
                "researchDirection": info.get("researchDirection", []),
            }
            candidates.append(candidate)

            name_display = candidate["nameEn"] or candidate["nameZh"]
            print(f"    + {name_display} ({candidate['institution']}) "
                  f"h={candidate['hIndex']}")

            if len(candidates) >= max_candidates:
                break

        if len(candidates) >= max_candidates:
            break

    print(f"  共获取 {len(candidates)} 位候选学者\n")
    return candidates


# ─── 步骤 2：验证候选者的真实产出 ──────────────────────────

def verify_candidates(
    candidates: list[dict],
    need_keywords: list[str],
) -> list[dict]:
    """
    通过论文检索验证每位候选学者的实际产出和近期活跃度。
    为每位候选者补充 papers, activity, top_papers 字段。
    返回经过验证和排序的候选列表。
    """
    print(f"[步骤 2/3] 验证候选者的实际产出")

    current_year = datetime.now().year

    for i, candidate in enumerate(candidates):
        name = candidate["nameEn"] or candidate["nameZh"]
        print(f"  [{i+1}/{len(candidates)}] 检索 {name} 的论文...")

        # 用学者姓名 + 需求关键词检索论文
        words = [name] + need_keywords[:2]
        question = f"research publications by {name}"

        try:
            r = requests.post(
                f"{BASE}/v1/paper/rag/pass/keyword",
                headers=H_JSON,
                json={
                    "words": words,
                    "question": question,
                    "type": 5,
                    "pageSize": 15,
                },
                timeout=30,
            )
            r.raise_for_status()
            text = r.text.strip()
            first_line = text.split("\n")[0]
            data = json.loads(first_line)
            papers = data.get("data", [])
        except Exception as e:
            print(f"    检索失败：{e}")
            papers = []

        candidate["papers"] = papers

        # 计算活跃度
        activity = compute_activity_score(papers, current_year)
        candidate["activity"] = activity

        # 提取 Top-3 代表作（按引用数排序）
        sorted_papers = sorted(papers, key=lambda p: p.get("citationNums", 0),
                               reverse=True)
        candidate["top_papers"] = []
        for p in sorted_papers[:3]:
            candidate["top_papers"].append({
                "title": p.get("enName", ""),
                "doi": p.get("doi", ""),
                "journal": p.get("publicationEnName", ""),
                "date": p.get("coverDateStart", ""),
                "citations": p.get("citationNums", 0),
                "impactFactor": p.get("impactFactor", 0),
            })

        print(f"    论文数: {len(papers)}, "
              f"近期: {activity['recent_count']}, "
              f"活跃度: {activity['activity_level']}")

    # 按综合评分排序：近期活跃度 + h-index + 论文匹配数
    def score(c):
        act = c.get("activity", {})
        return (
            act.get("recent_count", 0) * 3 +
            c.get("hIndex", 0) * 2 +
            len(c.get("papers", [])) +
            (10 if c.get("isHighCited") else 0)
        )

    candidates.sort(key=score, reverse=True)

    print(f"  验证完成，按综合评分排序\n")
    return candidates


# ─── 步骤 3：分析研究互补性 ──────────────────────────────────

def analyze_complementarity(
    my_direction: str,
    candidates: list[dict],
) -> list[dict]:
    """
    利用知识图谱分析用户研究方向与每位候选者方向之间的互补性。
    弱连接或跨域连接意味着高互补潜力。
    为每位候选者补充 complementarity 字段。
    返回更新后的候选列表。
    """
    print(f"[步骤 3/3] 分析研究互补性")
    print(f"  用户方向：{my_direction}")

    # 先获取用户方向的知识图谱节点
    print(f"  查询用户方向的知识图谱位置...")
    my_kg_nodes = []
    try:
        r = requests.post(
            f"{BASE}/v1/lkm/search",
            headers=H_JSON,
            json={"query": my_direction, "limit": 10},
            timeout=30,
        )
        r.raise_for_status()
        my_kg_nodes = r.json().get("data", [])
        print(f"    找到 {len(my_kg_nodes)} 个相关知识节点")
    except Exception as e:
        print(f"    知识图谱搜索失败：{e}")

    # 提取用户方向的概念集合
    my_concepts = set()
    for node in my_kg_nodes:
        if isinstance(node, dict):
            for key in ["name", "label", "title", "concept"]:
                if key in node and node[key]:
                    my_concepts.add(str(node[key]).lower())

    # 对每位候选者查询其方向的知识图谱位置并比较
    for i, candidate in enumerate(candidates[:10]):
        name = candidate["nameEn"] or candidate["nameZh"]
        directions = candidate.get("researchDirection", [])

        if not directions:
            # 从论文标题中推断方向
            titles = [p.get("enName", "") for p in candidate.get("papers", [])[:5]]
            direction_query = " ".join(titles)[:200] if titles else name
        else:
            direction_query = " ".join(directions[:3])

        print(f"  [{i+1}] {name}: ", end="")

        try:
            r = requests.post(
                f"{BASE}/v1/lkm/search",
                headers=H_JSON,
                json={"query": direction_query, "limit": 10},
                timeout=30,
            )
            r.raise_for_status()
            cand_kg_nodes = r.json().get("data", [])
        except Exception as e:
            print(f"知识图谱查询失败 ({e})")
            candidate["complementarity"] = {
                "score": "未知",
                "explanation": "知识图谱查询失败，无法评估互补性",
                "shared_concepts": [],
                "unique_concepts": [],
            }
            continue

        # 提取候选者的概念集合
        cand_concepts = set()
        for node in cand_kg_nodes:
            if isinstance(node, dict):
                for key in ["name", "label", "title", "concept"]:
                    if key in node and node[key]:
                        cand_concepts.add(str(node[key]).lower())

        # 计算互补性
        shared = my_concepts & cand_concepts
        unique_to_candidate = cand_concepts - my_concepts

        if len(shared) == 0 and len(unique_to_candidate) == 0:
            comp_score = "低"
            explanation = "知识图谱中未找到明确的连接或互补关系"
        elif len(unique_to_candidate) > len(shared) and len(shared) > 0:
            comp_score = "高"
            explanation = (f"存在 {len(shared)} 个共同概念作为合作基础，"
                          f"同时候选者独有 {len(unique_to_candidate)} 个互补概念")
        elif len(unique_to_candidate) > 0:
            comp_score = "高"
            explanation = (f"候选者带来 {len(unique_to_candidate)} 个用户方向中"
                          f"缺少的概念，互补潜力大")
        elif len(shared) > 3:
            comp_score = "中"
            explanation = (f"有 {len(shared)} 个共同概念，方向重叠度较高，"
                          f"互补性一般但沟通成本低")
        else:
            comp_score = "中"
            explanation = "存在一定交集，具备合作基础"

        candidate["complementarity"] = {
            "score": comp_score,
            "explanation": explanation,
            "shared_concepts": list(shared)[:5],
            "unique_concepts": list(unique_to_candidate)[:5],
        }

        print(f"互补性={comp_score}（共同{len(shared)}/独有{len(unique_to_candidate)}）")

    print(f"  互补性分析完成\n")
    return candidates


# ─── 报告生成 ───────────────────────────────────────────

def generate_report(
    my_direction: str,
    collaboration_need: str,
    geo_preference: str,
    candidates: list[dict],
    top_n: int = 10,
) -> str:
    """
    汇总分析结果，生成合作者推荐报告（Markdown 格式）。
    """
    lines = []

    lines.append(f"# 合作者发现报告\n")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> 数据来源：Bohrium OpenAPI (scholar-search + paper-search + lkm)\n")
    lines.append(f"## 检索条件\n")
    lines.append(f"| 参数 | 值 |")
    lines.append(f"|------|------|")
    lines.append(f"| **自身研究方向** | {my_direction} |")
    lines.append(f"| **合作需求** | {collaboration_need} |")
    lines.append(f"| **地域偏好** | {geo_preference or '不限'} |")
    lines.append(f"| **候选学者数** | {len(candidates)} |")
    lines.append(f"")

    # 推荐列表
    lines.append(f"## 推荐合作者\n")

    selected = candidates[:top_n]

    for rank, cand in enumerate(selected, 1):
        name_display = cand.get("nameEn", "")
        if cand.get("nameZh"):
            name_display += f" / {cand['nameZh']}"

        lines.append(f"### {rank}. {name_display}\n")

        # 基础信息表
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|------|")
        lines.append(f"| **机构** | {cand.get('institution', 'N/A')} |")
        lines.append(f"| **h-index** | {cand.get('hIndex', 'N/A')} |")
        lines.append(f"| **总论文数** | {cand.get('paperNums', 'N/A')} |")
        lines.append(f"| **总引用数** | {cand.get('citationNums', 'N/A')} |")

        high_cited = "是" if cand.get("isHighCited") else "否"
        lines.append(f"| **高被引学者** | {high_cited} |")

        directions = cand.get("researchDirection", [])
        if directions:
            dir_str = "、".join(directions) if isinstance(directions, list) else str(directions)
            lines.append(f"| **研究方向** | {dir_str} |")

        activity = cand.get("activity", {})
        lines.append(f"| **近期活跃度** | {activity.get('activity_level', 'N/A')}"
                     f"（近 2 年 {activity.get('recent_count', 0)} 篇）|")
        lines.append(f"")

        # 互补性分析
        comp = cand.get("complementarity", {})
        if comp:
            lines.append(f"**互补性评估：{comp.get('score', 'N/A')}**\n")
            lines.append(f"{comp.get('explanation', '')}\n")

            shared = comp.get("shared_concepts", [])
            unique = comp.get("unique_concepts", [])
            if shared:
                lines.append(f"- 共同概念：{', '.join(shared)}")
            if unique:
                lines.append(f"- 互补概念：{', '.join(unique)}")
            lines.append(f"")

        # 代表作
        top_papers = cand.get("top_papers", [])
        if top_papers:
            lines.append(f"**代表作品：**\n")
            for j, p in enumerate(top_papers, 1):
                title = p.get("title", "N/A")
                journal = p.get("journal", "N/A")
                citations = p.get("citations", 0)
                doi = p.get("doi", "")
                date = p.get("date", "")[:10]
                doi_link = f"https://doi.org/{doi}" if doi else ""
                lines.append(f"{j}. **{title}**")
                lines.append(f"   - {journal} | 引用: {citations} | "
                             f"日期: {date}")
                if doi_link:
                    lines.append(f"   - DOI: [{doi}]({doi_link})")
            lines.append(f"")

        # 联系线索
        inst = cand.get("institution", "")
        name_en = cand.get("nameEn", "")
        if inst and name_en:
            lines.append(f"**联系线索：**\n")
            lines.append(f"- 机构主页：搜索「{name_en} {inst}」")
            lines.append(f"- Google Scholar："
                         f"https://scholar.google.com/scholar?q={name_en.replace(' ', '+')}")
            lines.append(f"")

        lines.append(f"---\n")

    # 总结建议
    lines.append(f"## 总结与建议\n")

    high_comp = [c for c in selected
                 if c.get("complementarity", {}).get("score") == "高"]
    high_active = [c for c in selected
                   if c.get("activity", {}).get("activity_level") == "高"]

    if high_comp:
        names = [c.get("nameEn", "") or c.get("nameZh", "") for c in high_comp[:3]]
        lines.append(f"- **高互补性候选者**：{', '.join(names)}"
                     f" — 研究方向与您形成良好互补，优先考虑联系")
    if high_active:
        names = [c.get("nameEn", "") or c.get("nameZh", "") for c in high_active[:3]]
        lines.append(f"- **高活跃度候选者**：{', '.join(names)}"
                     f" — 近期产出活跃，合作意愿和推进效率可能更高")

    lines.append(f"\n**建议下一步**：")
    lines.append(f"1. 对感兴趣的候选者运行 `scholar-profiler` 获取完整画像")
    lines.append(f"2. 阅读候选者的代表作品，评估具体合作切入点")
    lines.append(f"3. 通过机构主页或学术会议寻找联系方式")
    lines.append(f"4. 在初次联系时，说明具体的互补点和合作构想")

    return "\n".join(lines)


# ─── 主流程 ─────────────────────────────────────────────

def find_collaborators(
    my_direction: str,
    collaboration_need: str,
    geo_preference: str = "",
):
    """
    合作者发现主函数。

    参数：
        my_direction: 自身研究方向描述
        collaboration_need: 合作需求描述
        geo_preference: 地域偏好（可选）
    """
    print("=" * 60)
    print("  合作者发现 (Collaborator Finder)")
    print(f"  研究方向：{my_direction}")
    print(f"  合作需求：{collaboration_need}")
    if geo_preference:
        print(f"  地域偏好：{geo_preference}")
    print("=" * 60)

    # 提取搜索关键词
    need_keywords = extract_need_keywords(collaboration_need)
    print(f"\n提取的需求关键词：{need_keywords}\n")

    # ── 步骤 1：搜索候选学者 ──
    candidates = search_candidate_scholars(
        collaboration_need=collaboration_need,
        need_keywords=need_keywords,
        geo_preference=geo_preference,
        max_candidates=15,
    )

    if not candidates:
        print("\n未找到候选学者，流程终止。")
        print("建议：")
        print("  1. 尝试更宽泛的合作需求描述")
        print("  2. 移除地域限制")
        print("  3. 使用英文关键词描述需求")
        return None

    # ── 步骤 2：验证候选者的真实产出 ──
    candidates = verify_candidates(candidates, need_keywords)

    # ── 步骤 3：分析研究互补性 ──
    candidates = analyze_complementarity(my_direction, candidates)

    # ── 生成报告 ──
    print("=" * 60)
    print("  生成合作者推荐报告...")
    print("=" * 60 + "\n")

    report = generate_report(
        my_direction=my_direction,
        collaboration_need=collaboration_need,
        geo_preference=geo_preference,
        candidates=candidates,
        top_n=10,
    )

    print(report)
    return report


# ─── 入口 ───────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：python collaborator_finder.py <研究方向> <合作需求> [地域偏好]")
        print()
        print("示例：")
        print('  python collaborator_finder.py "分子动力学模拟" "需要实验验证能力"')
        print('  python collaborator_finder.py "锂电池正极材料" "需要机器学习算法专长" "中国"')
        print('  python collaborator_finder.py "protein structure prediction" '
              '"need experimental validation" "North America"')
        sys.exit(1)

    direction = sys.argv[1]
    need = sys.argv[2]
    geo = sys.argv[3] if len(sys.argv) > 3 else ""

    find_collaborators(direction, need, geo)
```

---

## 各步骤详解

### 步骤 1：搜索候选学者 (`scholar-search`)

将用户的合作需求转化为搜索关键词，通过 `scholar/search` 搜索多组关键词，获取候选学者列表。对每位候选者拉取 `scholar/info` 详情，获取研究方向和基础指标。

```python
# 从合作需求提取关键词
need_keywords = extract_need_keywords("需要实验验证能力")
# → ["experimental", "synthesis", "characterization"]

# 搜索学者
r = requests.post(f"{BASE}/v1/paper-server/scholar/search",
    headers=H_JSON,
    json={"name": "experimental synthesis", "page": 1, "pageSize": 10})

# 获取详情
scholar_id = r.json()["data"]["items"][0]["scholarId"]
r = requests.get(f"{BASE}/v1/paper-server/scholar/info",
    headers=H_AK,
    params={"scholarId": scholar_id})
```

**搜索策略**：用多个关键词分别搜索并去重合并，确保覆盖不同表述下的学者。如有地域偏好，使用 `school` 参数传入机构/地区名称进行过滤。

---

### 步骤 2：验证候选者的真实产出 (`paper-search`)

用候选学者姓名 + 需求关键词检索其发表记录，验证其在目标方向的真实产出：

1. **近期活跃度**：统计近 2 年发文量，判断学者是否仍活跃
2. **代表作品**：按引用数排序，提取 Top-3 论文
3. **综合评分排序**：近期活跃度 x3 + h-index x2 + 论文匹配数 + 高被引加分

```python
# 检索候选者论文
r = requests.post(f"{BASE}/v1/paper/rag/pass/keyword",
    headers=H_JSON,
    json={
        "words": ["John Smith", "experimental", "synthesis"],
        "question": "research publications by John Smith",
        "type": 5,
        "pageSize": 15
    })
```

---

### 步骤 3：分析研究互补性 (`lkm`)

分别查询用户方向和每位候选者方向在知识图谱中的位置，通过概念集合的交集与差集评估互补性：

- **共同概念**（交集）= 合作基础，降低沟通成本
- **候选者独有概念**（差集）= 互补潜力，能为用户带来新能力
- 弱连接（少量交集 + 大量独有）= 最佳互补

```python
# 查询用户方向的知识图谱
r = requests.post(f"{BASE}/v1/lkm/search",
    headers=H_JSON,
    json={"query": "molecular dynamics simulation force field", "limit": 10})
my_nodes = r.json()["data"]

# 查询候选者方向的知识图谱
r = requests.post(f"{BASE}/v1/lkm/search",
    headers=H_JSON,
    json={"query": "experimental synthesis characterization lithium battery", "limit": 10})
cand_nodes = r.json()["data"]

# 比较概念集合 → 评估互补性
shared = my_concepts & cand_concepts        # 合作基础
unique = cand_concepts - my_concepts        # 互补潜力
```

---

## curl 示例

```bash
AK="$ACCESS_KEY"
BASE="https://open.bohrium.com/openapi"

# ── 步骤 1a：按需求关键词搜索学者 ──
curl -s -X POST "$BASE/v1/paper-server/scholar/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"name":"experimental synthesis","page":1,"pageSize":10}'

# ── 步骤 1b：获取学者详情 ──
# 将上一步返回的 scholarId 替换下方 SCHOLAR_ID
curl -s "$BASE/v1/paper-server/scholar/info?scholarId=SCHOLAR_ID" \
  -H "accessKey: $AK"

# ── 步骤 2：检索候选者的论文 ──
curl -s -X POST "$BASE/v1/paper/rag/pass/keyword" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{
    "words": ["John Smith", "experimental", "synthesis"],
    "question": "research publications by John Smith",
    "type": 5,
    "pageSize": 15
  }'

# ── 步骤 3a：查询用户方向的知识图谱 ──
curl -s -X POST "$BASE/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "molecular dynamics simulation force field", "limit": 10}'

# ── 步骤 3b：查询候选者方向的知识图谱 ──
curl -s -X POST "$BASE/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "experimental synthesis characterization lithium battery", "limit": 10}'
```

---

## 使用示例

### 基本用法

```python
# 寻找实验合作者
find_collaborators(
    my_direction="分子动力学模拟",
    collaboration_need="需要实验验证能力"
)

# 寻找算法专家
find_collaborators(
    my_direction="锂电池正极材料",
    collaboration_need="需要机器学习算法专长"
)

# 限定地域
find_collaborators(
    my_direction="protein structure prediction",
    collaboration_need="need experimental validation",
    geo_preference="North America"
)
```

### 命令行调用

```bash
# 基本查询
python collaborator_finder.py "分子动力学模拟" "需要实验验证能力"

# 带地域偏好
python collaborator_finder.py "锂电池正极材料" "需要机器学习算法专长" "中国"

# 英文输入
python collaborator_finder.py "protein structure prediction" \
  "need experimental validation" "North America"
```

---

## 错误处理

| 场景 | 错误信息 | 处理方式 |
|------|---------|---------|
| ACCESS_KEY 未设置 | `未设置 ACCESS_KEY 环境变量` | 配置 `~/.openclaw/openclaw.json` |
| 学者搜索无结果 | `搜索「xxx」→ 返回 0 位学者` | 尝试更宽泛的关键词，或移除地域限制 |
| 论文检索为空 | `检索失败` 或返回 0 篇 | 可能学者姓名不匹配，不影响其他候选者 |
| 知识图谱查询失败 | `知识图谱查询失败` | 互补性标记为"未知"，不影响其他维度评估 |
| Invalid AccessKey / 401 | Key 已失效 | 更新 `~/.openclaw/openclaw.json` 并重启会话 |
| 候选者数量不足 | 总候选者 < 5 | 扩大关键词范围，或分多次使用不同需求描述搜索 |

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 推荐结果与需求不太匹配 | 需求描述过于笼统 | 使用更具体的描述，如"需要锂电池正极材料合成经验"而非仅"需要实验" |
| 候选者中有不活跃的学者 | 搜索返回了历史数据较老的学者 | 关注报告中的"近期活跃度"字段，优先选择标记为"高"的候选者 |
| 互补性评估为"未知" | 知识图谱中缺少对应概念 | 正常现象；参考候选者的研究方向和论文自行判断 |
| 地域过滤不精确 | `school` 参数是模糊匹配 | 尝试不同粒度的地域描述：具体大学名 > 城市 > 国家 |
| 返回结果太少 | 关键词太窄或地域限制太严 | 分步放宽：先移除地域限制，再扩大关键词范围 |
| 同一学者出现多次 | 不同关键词搜索返回同一人 | 脚本已内置去重（按 scholarId），若仍重复请检查是否有不同 scholarId |
| 如何判断合作可行性 | 报告提供线索但不做最终判断 | 综合考虑互补性、活跃度、地理距离、语言等因素自行评估 |

---

## 搭配使用

- **collaborator-finder** 发现候选者 → **scholar-profiler** 深入了解目标学者的完整画像
- **collaborator-finder** 获取代表作 → **paper-dissector** 深度解读合作者的关键论文
- **collaborator-finder** + **topic-scout** → 先确定选题方向，再寻找该方向的合作伙伴
- **collaborator-finder** + **literature-review** → 对合作候选者的研究领域做完整文献调研
- **collaborator-finder** 输出报告 → **knowledge-base** 存档供课题组讨论参考
