---
name: reading-club
description: "Journal club paper curation combining paper search, PDF summary, and shared knowledge base. Use when: user needs to organize a reading group session, select papers for discussion, and generate discussion guides. NOT for: personal literature review (use literature-review), paper deep analysis (use paper-dissector)."
---

# SKILL: 文献阅读俱乐部 (Reading Club)

## 概述

文献阅读俱乐部是一个**编排型 Skill**，串联 `paper-search`、`pdf-parser`、`knowledge-base` 三个原子 Skill，为研究组 Journal Club 活动自动完成论文筛选、摘要生成、讨论指南编写和共享知识库归档的完整流程。

**组合的原子 Skill：**

| 步骤 | 原子 Skill | 端点 | 功能 |
|------|-----------|------|------|
| 1 | `paper-search` | `POST /v1/paper/rag/pass/keyword` | 语义检索并筛选最具讨论价值的论文 |
| 2 | `pdf-parser` | `POST /v1/parse/trigger-url-async` + `get-result` | 为每篇候选论文生成快速摘要 |
| 3 | `knowledge-base` | `POST /v1/knowledge/knowledge_base/create` + 上传流程 | 将推荐论文及讨论指南存入共享知识库 |

**适用场景：**

- 组织 Journal Club / 读书会，需要筛选本周讨论论文
- 多人研究组选题，需兼顾不同研究方向的多样性
- 生成带讨论问题的论文推荐列表
- 将讨论材料集中存入共享知识库供组员预习

**不适用：**

- 个人文献综述 → `literature-review`
- 单篇论文深度拆解 → `paper-dissector`
- 仅搜索论文 → `bohrium-paper-search`
- 仅管理知识库文件 → `bohrium-knowledge-base`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"reading-club": {
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
| `topic` | string | 是 | — | 本次 Session 的讨论主题 |
| `keywords` | string[] | 否 | 从 topic 提取 | 检索关键词列表（3-8 个英文术语） |
| `time_range` | int | 否 | 1 | 检索时间范围（年），从当前向前推算 |
| `start_time` | string | 否 | 自动计算 | 起始日期 `YYYY-MM-DD` |
| `end_time` | string | 否 | 今天 | 截止日期 `YYYY-MM-DD` |
| `jcr_zones` | string[] | 否 | [] | JCR 分区筛选，如 `["Q1", "Q2"]` |
| `participant_directions` | string[] | 否 | [] | 参会者研究方向列表，用于多样性筛选 |
| `num_papers` | int | 否 | 5 | 最终推荐论文数量（3-5 篇） |
| `save_to_kb` | bool | 否 | true | 是否将结果存入共享知识库 |

---

## 输出格式

最终输出包含 3-5 篇推荐论文，每篇包含：

### 1. 论文基本信息

标题、作者、期刊、影响因子、引用数、发表日期、DOI。

### 2. 讨论指南问题

针对每篇论文设计的 3-5 个讨论问题，覆盖：
- 研究动机与问题定义
- 方法创新与技术路线
- 实验设计与结果解读
- 局限性与改进方向

### 3. 背景知识引读

帮助非该方向的组员快速理解论文所需的背景知识要点。

### 4. 论文间关联

推荐论文之间的方法对比、互补关系、或争议性观点的对照。

---

## 推荐质量控制

### 论文选择的多样性

推荐的 3-5 篇论文**不能全是同一子方向的近期工作**，必须包含：
- 至少 1 篇方法/视角与其他论文不同的工作（提供碰撞和讨论张力）
- 至少 1 篇近 12 个月发表的最新工作（保证前沿性）
- 如果参与者来自不同背景（`participant_directions`），每个方向至少覆盖 1 篇

### 讨论问题的深度

讨论问题**不能是论文内容的简单回顾**（如"本文的方法是什么"），应该是：
- 批判性问题："如果数据分布变化，该方法的哪个假设会失效？"
- 对比性问题："A 方法和 B 方法在什么场景下优劣逆转？"
- 延伸性问题："这个思路能否迁移到 [参与者方向]？具体改什么？"

### 禁止的行为

- ❌ 推荐论文全来自同一研究组或同一会议
- ❌ 讨论问题可以通过读摘要就回答（太浅）
- ❌ 背景知识引读只是复述论文 Introduction（应提炼核心前置知识）

---

## 工作流程图

```
输入: topic, keywords, participant_directions
        |
        v
+--------------------------------------+
|  步骤 1: 论文检索与筛选                |
|  POST /v1/paper/rag/pass/keyword     |
|  -> 按引用数、发表时间、影响因子排序     |
|  -> 考虑参会者方向进行多样性筛选        |
|  -> 筛选最具讨论价值的候选论文          |
+---------------+-----------------------+
                |
                v
+--------------------------------------+
|  步骤 2: 候选论文快速摘要               |
|  POST /v1/parse/trigger-url-async    |
|  POST /v1/parse/get-result (轮询)     |
|  -> 解析前 3-5 页（摘要+方法+结论）     |
|  -> 提取核心贡献、方法要点、关键结果     |
+---------------+-----------------------+
                |
                v
+--------------------------------------+
|  步骤 3: 生成讨论指南                   |
|  -> 为每篇论文生成讨论问题              |
|  -> 编写背景知识引读                    |
|  -> 分析论文间关联                      |
+---------------+-----------------------+
                |
                v (可选)
+--------------------------------------+
|  步骤 4: 存入共享知识库                  |
|  POST /v1/knowledge/knowledge_base/  |
|       create                         |
|  -> 上传论文 PDF 和讨论指南             |
+--------------------------------------+
```

---

## 通用代码模板

```python
import os, time, requests, json
from datetime import datetime, timedelta

AK = os.environ.get("ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS = {"accessKey": AK}
```

---

## 步骤 1: 论文检索与筛选

使用 `paper-search` 进行语义检索，然后根据讨论价值进行综合排序和多样性筛选。

### 筛选策略

最具讨论价值的论文通常具备以下特征（加权打分）：

| 因素 | 权重 | 说明 |
|------|------|------|
| 近期发表 | 0.3 | 近 3 个月内发表的论文优先 |
| 高影响力 | 0.25 | 高引用数或高影响因子期刊 |
| 争议性 | 0.25 | 提出与主流不同的观点或方法 |
| 方向多样性 | 0.2 | 覆盖不同参会者的研究方向 |

### Python 示例

```python
def search_and_filter_papers(topic, keywords, num_papers=5,
                             start_time="", end_time="",
                             jcr_zones=None, participant_directions=None):
    """
    检索并筛选最具讨论价值的论文。

    Args:
        topic: 讨论主题
        keywords: 关键词列表
        num_papers: 最终推荐数量
        start_time: 起始日期 YYYY-MM-DD
        end_time: 截止日期 YYYY-MM-DD
        jcr_zones: JCR 分区筛选
        participant_directions: 参会者研究方向列表

    Returns:
        筛选后的论文列表
    """
    # 检索候选论文（获取较多候选以便筛选）
    candidate_size = max(num_papers * 6, 30)

    payload = {
        "words": keywords,
        "question": topic,
        "type": 5,
        "startTime": start_time,
        "endTime": end_time,
        "jcrZones": jcr_zones or [],
        "pageSize": candidate_size
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
    print(f"[步骤1] 检索到 {len(papers)} 篇候选论文")

    if not papers:
        return []

    # 计算讨论价值分数
    now = datetime.now()
    three_months_ago = (now - timedelta(days=90)).strftime("%Y-%m-%d")

    for p in papers:
        score = 0.0

        # 近期发表加分（权重 0.3）
        pub_date = p.get("coverDateStart", "")
        if pub_date >= three_months_ago:
            score += 0.3
        elif pub_date >= (now - timedelta(days=180)).strftime("%Y-%m-%d"):
            score += 0.15

        # 高影响力加分（权重 0.25）
        citations = p.get("citationNums", 0)
        impact_factor = p.get("impactFactor", 0)
        if citations > 100 or impact_factor > 10:
            score += 0.25
        elif citations > 30 or impact_factor > 5:
            score += 0.15
        elif citations > 10 or impact_factor > 2:
            score += 0.08

        # 争议性/新颖性加分（权重 0.25）
        # 高引用+近期发表 = 热点/可能有争议
        if citations > 50 and pub_date >= (now - timedelta(days=365)).strftime("%Y-%m-%d"):
            score += 0.25
        # 低引用+高影响因子期刊+近期 = 新颖
        elif citations < 10 and impact_factor > 5 and pub_date >= three_months_ago:
            score += 0.20

        p["_discussion_score"] = score

    # 按讨论价值分数排序
    papers.sort(key=lambda p: p["_discussion_score"], reverse=True)

    # 多样性筛选：如果提供了参会者方向，确保覆盖不同方向
    if participant_directions and len(participant_directions) > 1:
        selected = _diversity_select(papers, participant_directions, num_papers)
    else:
        selected = papers[:num_papers]

    print(f"[步骤1] 筛选出 {len(selected)} 篇最具讨论价值的论文:")
    for i, p in enumerate(selected):
        print(f"  {i+1}. [{p.get('doi', 'N/A')}] {p['enName'][:70]}")
        print(f"     期刊: {p.get('publicationEnName', 'N/A')}, "
              f"IF: {p.get('impactFactor', 0)}, "
              f"引用: {p.get('citationNums', 0)}, "
              f"讨论分: {p['_discussion_score']:.2f}")

    return selected


def _diversity_select(papers, directions, num_papers):
    """
    多样性选择：确保推荐论文覆盖不同参会者的研究方向。

    策略：为每个方向分配至少 1 篇名额，剩余名额按讨论分数补充。
    """
    selected = []
    used_dois = set()

    # 为每个方向选择最佳论文
    slots_per_direction = max(1, num_papers // len(directions))

    for direction in directions:
        count = 0
        for p in papers:
            if p.get("doi", "") in used_dois:
                continue

            # 简单的方向匹配：检查论文标题和摘要是否包含方向关键词
            title = p.get("enName", "").lower()
            abstract = p.get("enAbstract", "").lower()
            direction_lower = direction.lower()

            if direction_lower in title or direction_lower in abstract:
                selected.append(p)
                used_dois.add(p.get("doi", ""))
                count += 1
                if count >= slots_per_direction:
                    break

    # 剩余名额按讨论分数补充
    remaining = num_papers - len(selected)
    for p in papers:
        if remaining <= 0:
            break
        if p.get("doi", "") not in used_dois:
            selected.append(p)
            used_dois.add(p.get("doi", ""))
            remaining -= 1

    return selected[:num_papers]
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["large language model", "scientific discovery", "AI for science"],
    "question": "How are large language models being applied to accelerate scientific discovery?",
    "type": 5,
    "startTime": "2025-01-01",
    "endTime": "2026-05-13",
    "jcrZones": ["Q1"],
    "pageSize": 30
  }'
```

---

## 步骤 2: 候选论文快速摘要

对筛选出的论文进行快速 PDF 解析（仅前 3-5 页），提取核心内容用于生成讨论指南。

### Python 示例

```python
def generate_quick_summaries(papers):
    """
    为每篇候选论文生成快速摘要。

    Args:
        papers: 步骤 1 筛选后的论文列表

    Returns:
        dict: {doi: {"content": str, "summary": dict}}
    """
    print(f"\n[步骤2] 为 {len(papers)} 篇论文生成快速摘要...")

    summaries = {}
    tokens = {}

    # 批量提交解析任务
    for p in papers:
        doi = p.get("doi", "")
        if not doi:
            continue

        pdf_url = f"https://doi.org/{doi}"

        try:
            r = requests.post(
                f"{BASE}/v1/parse/trigger-url-async",
                headers=HEADERS_JSON,
                json={
                    "url": pdf_url,
                    "sync": False,
                    "textual": True,
                    "table": True,
                    "expression": True,
                    "equation": True,
                    "pages": [0, 1, 2, 3, 4],  # 只解析前 5 页
                    "timeout": 1800
                }
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("code"):
                tokens[doi] = data["token"]
                print(f"  提交: {doi} -> token={data['token'][:16]}...")
            else:
                print(f"  跳过: {doi} -> {data.get('message', 'error')}")
        except Exception as e:
            print(f"  失败: {doi} -> {e}")

    if not tokens:
        print("  警告: 无法提交任何解析任务")
        # 即使解析失败，仍可基于元数据生成讨论指南
        for p in papers:
            doi = p.get("doi", "")
            summaries[doi] = {
                "content": "",
                "summary": _extract_summary_from_metadata(p)
            }
        return summaries

    # 轮询解析结果
    print(f"\n  等待 {len(tokens)} 个解析任务完成...\n")
    pending = dict(tokens)
    max_wait = 120
    start = time.time()

    while pending and (time.time() - start) < max_wait:
        time.sleep(3)
        done_keys = []
        for doi, token in pending.items():
            try:
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
                    content = result.get("content", "")
                    summaries[doi] = {
                        "content": content,
                        "summary": _extract_summary_from_content(content)
                    }
                    print(f"  完成: {doi} ({len(content)} 字符)")
                    done_keys.append(doi)
                elif status == "failed":
                    print(f"  失败: {doi}")
                    done_keys.append(doi)
            except Exception as e:
                print(f"  错误: {doi} -> {e}")

        for k in done_keys:
            del pending[k]

    # 为未解析成功的论文使用元数据生成摘要
    for p in papers:
        doi = p.get("doi", "")
        if doi and doi not in summaries:
            summaries[doi] = {
                "content": "",
                "summary": _extract_summary_from_metadata(p)
            }

    print(f"[步骤2] 摘要生成完成: {len(summaries)} 篇")
    return summaries


def _extract_summary_from_content(content):
    """
    从解析内容中提取结构化摘要。
    """
    import re

    summary = {
        "core_contribution": "",
        "method_highlights": [],
        "key_results": [],
        "limitations": []
    }

    # 提取核心贡献（通常在 Abstract 或 Introduction 的 "we propose/present" 句子中）
    propose_patterns = re.findall(
        r'[^.]*(?:we (?:propose|present|introduce|develop|demonstrate))\b[^.]+\.',
        content, re.IGNORECASE
    )
    if propose_patterns:
        summary["core_contribution"] = propose_patterns[0].strip()

    # 提取方法要点
    method_patterns = re.findall(
        r'[^.]*(?:our (?:method|approach|framework|model|algorithm))[^.]+\.',
        content, re.IGNORECASE
    )
    summary["method_highlights"] = [m.strip() for m in method_patterns[:3]]

    # 提取关键结果
    result_patterns = re.findall(
        r'[^.]*(?:achieve|outperform|improve|result|accuracy|performance)[^.]+\.',
        content, re.IGNORECASE
    )
    summary["key_results"] = [r.strip() for r in result_patterns[:3]]

    return summary


def _extract_summary_from_metadata(paper):
    """
    当 PDF 解析失败时，从论文元数据中提取摘要信息。
    """
    abstract = paper.get("enAbstract", "")
    return {
        "core_contribution": abstract[:300] if abstract else "（无摘要信息）",
        "method_highlights": [],
        "key_results": [],
        "limitations": []
    }
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 提交解析任务（仅前 5 页）
TOKEN=$(curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/trigger-url-async" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "url": "https://arxiv.org/pdf/2303.08774",
    "sync": false,
    "textual": true,
    "table": true,
    "expression": true,
    "equation": true,
    "pages": [0, 1, 2, 3, 4],
    "timeout": 1800
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "Token: $TOKEN"

# 轮询结果
sleep 5
curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/get-result" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d "{\"token\": \"$TOKEN\", \"content\": true, \"objects\": false, \"pages_dict\": false}"
```

---

## 步骤 3: 生成讨论指南并存入知识库

基于论文元数据和解析内容，生成结构化讨论指南，并可选地存入共享知识库。

### Python 示例

```python
def generate_discussion_guide(papers, summaries):
    """
    为每篇论文生成讨论指南，并分析论文间关联。

    Args:
        papers: 推荐论文列表
        summaries: {doi: {"content": str, "summary": dict}}

    Returns:
        dict: 包含每篇论文的讨论指南和整体关联分析
    """
    print(f"\n[步骤3] 生成讨论指南...")

    guide = {
        "session_papers": [],
        "cross_paper_connections": []
    }

    for p in papers:
        doi = p.get("doi", "")
        title = p.get("enName", "")
        abstract = p.get("enAbstract", "")
        journal = p.get("publicationEnName", "")
        impact_factor = p.get("impactFactor", 0)
        citations = p.get("citationNums", 0)
        date = p.get("coverDateStart", "")
        authors = p.get("authors", [])

        paper_summary = summaries.get(doi, {}).get("summary", {})

        paper_guide = {
            "doi": doi,
            "title": title,
            "authors": authors[:5],  # 前 5 位作者
            "journal": journal,
            "impact_factor": impact_factor,
            "citations": citations,
            "date": date,
            "core_contribution": paper_summary.get("core_contribution", abstract[:300]),
            "discussion_questions": _generate_questions(p, paper_summary),
            "background_primer": _generate_background(p, paper_summary),
            "method_highlights": paper_summary.get("method_highlights", []),
            "key_results": paper_summary.get("key_results", [])
        }

        guide["session_papers"].append(paper_guide)

    # 分析论文间关联
    guide["cross_paper_connections"] = _analyze_connections(papers, summaries)

    return guide


def _generate_questions(paper, summary):
    """
    为单篇论文生成讨论问题。
    """
    questions = []

    # 问题 1: 研究动机
    questions.append({
        "category": "研究动机",
        "question": f"本文要解决的核心问题是什么？为什么这个问题在当前研究背景下重要？",
        "hint": "关注 Introduction 中对现有方法的不足的描述。"
    })

    # 问题 2: 方法创新
    if summary.get("method_highlights"):
        method_desc = summary["method_highlights"][0][:100]
        questions.append({
            "category": "方法创新",
            "question": f"本文提出的方法与已有方法的本质区别是什么？这种设计选择背后的直觉是什么？",
            "hint": f"方法要点: {method_desc}"
        })
    else:
        questions.append({
            "category": "方法创新",
            "question": "本文的方法论贡献是什么？与 baseline 方法相比有哪些关键改进？",
            "hint": "关注 Methods 部分的核心算法/模型架构。"
        })

    # 问题 3: 实验设计
    questions.append({
        "category": "实验设计",
        "question": "实验设计是否充分支撑了论文的核心论断？有哪些可能的混淆因素或遗漏的对照实验？",
        "hint": "检查 baseline 选择是否公平，评估指标是否全面，数据集是否有代表性。"
    })

    # 问题 4: 局限与拓展
    questions.append({
        "category": "局限与拓展",
        "question": "本文方法的主要局限性是什么？如果你要在此基础上做后续研究，你会怎么改进？",
        "hint": "思考适用范围、计算成本、数据依赖、可解释性等方面。"
    })

    # 问题 5: 领域影响
    citations = paper.get("citationNums", 0)
    if citations > 50:
        questions.append({
            "category": "领域影响",
            "question": f"本文已被引用 {citations} 次，你认为它对该领域的主要影响是什么？哪些后续工作直接受益于此？",
            "hint": "思考方法的通用性和可迁移性。"
        })
    else:
        questions.append({
            "category": "领域影响",
            "question": "本文的工作是否有可能改变该子领域的研究范式？为什么？",
            "hint": "结合领域发展趋势判断。"
        })

    return questions


def _generate_background(paper, summary):
    """
    生成背景知识引读，帮助非该方向的组员快速进入。
    """
    abstract = summary.get("core_contribution", "")
    journal = paper.get("publicationEnName", "")

    primer = {
        "field_context": f"本文发表于 {journal}，属于该领域的{'高影响力' if paper.get('impactFactor', 0) > 5 else '专业'}期刊。",
        "key_concepts": [],
        "prerequisite_reading": "建议预习论文的 Abstract 和 Introduction 部分，重点理解问题定义和已有方法的不足。",
        "estimated_reading_time": "快速浏览: 15-20 分钟（摘要+图表+结论）；精读: 45-60 分钟"
    }

    return primer


def _analyze_connections(papers, summaries):
    """
    分析推荐论文之间的关联关系。

    策略：基于关键词重叠、方法相似性、时间先后关系等维度分析。
    """
    connections = []

    for i in range(len(papers)):
        for j in range(i + 1, len(papers)):
            p1 = papers[i]
            p2 = papers[j]

            # 检查标题和摘要中的关键词重叠
            t1_words = set(p1.get("enName", "").lower().split())
            t2_words = set(p2.get("enName", "").lower().split())
            # 去除常见停用词
            stop_words = {"a", "an", "the", "of", "in", "for", "and", "or",
                          "to", "with", "on", "by", "is", "are", "was",
                          "were", "from", "at", "as", "its", "this", "that"}
            t1_words -= stop_words
            t2_words -= stop_words
            overlap = t1_words & t2_words

            if len(overlap) >= 2:
                # 判断关联类型
                date1 = p1.get("coverDateStart", "")
                date2 = p2.get("coverDateStart", "")

                if date1 and date2:
                    if abs(len(date1) - len(date2)) < 10:
                        relation = "同期研究"
                    elif date1 < date2:
                        relation = "先后发展"
                    else:
                        relation = "先后发展"
                else:
                    relation = "主题相关"

                connections.append({
                    "paper_a": p1.get("enName", "")[:60],
                    "paper_b": p2.get("enName", "")[:60],
                    "relation_type": relation,
                    "shared_keywords": list(overlap)[:5],
                    "discussion_point": f"对比这两篇论文在 {', '.join(list(overlap)[:3])} 方面的不同处理方式。"
                })

    return connections


def save_to_knowledge_base(topic, guide, papers):
    """
    创建共享知识库并将讨论材料存入。

    Args:
        topic: Session 主题
        guide: 讨论指南
        papers: 论文列表

    Returns:
        知识库 ID
    """
    print(f"\n[步骤4] 存入共享知识库...")

    # 创建知识库
    session_date = datetime.now().strftime("%Y-%m-%d")
    kb_name = f"Journal Club — {topic} ({session_date})"

    r = requests.post(
        f"{BASE}/v1/knowledge/knowledge_base/create",
        headers=HEADERS_JSON,
        json={
            "knowledgeBaseName": kb_name,
            "cover": "",
            "introduction": f"Reading Club session: {topic}. "
                          f"Contains {len(papers)} recommended papers with discussion guides.",
            "privilege": 1  # 1=私有
        }
    )
    r.raise_for_status()
    data = r.json()

    if data.get("code") != 0:
        print(f"  创建知识库失败: {data.get('message')}")
        return None

    kb_id = data["data"]["id"]
    print(f"  知识库已创建: ID={kb_id}, 名称={kb_name}")

    # 生成讨论指南 Markdown 并保存为文件后上传
    guide_md = format_guide_markdown(topic, guide)
    guide_filename = f"discussion_guide_{session_date}.md"

    # 将指南写入临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                      delete=False, encoding="utf-8") as f:
        f.write(guide_md)
        temp_path = f.name

    # 上传讨论指南（使用知识库上传流程）
    try:
        _upload_file_to_kb(temp_path, kb_id, guide_filename)
        print(f"  讨论指南已上传: {guide_filename}")
    except Exception as e:
        print(f"  上传讨论指南失败: {e}")
    finally:
        os.unlink(temp_path)

    print(f"[步骤4] 知识库准备完成: {kb_name}")
    return kb_id


def _upload_file_to_kb(file_path, parent_id, file_name):
    """
    将文件上传到知识库（三步流程）。
    """
    import hashlib, base64, urllib.request, urllib.parse, mimetypes

    file_size = os.path.getsize(file_path)

    # 计算 MD5
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    file_md5 = h.hexdigest()

    # 步骤 1: 获取上传凭证
    r = requests.get(
        f"{BASE}/v1/knowledge/file/multipart",
        headers=HEADERS,
        params={
            "fileName": file_name,
            "md5": file_md5,
            "parentId": parent_id,
            "size": file_size
        }
    )
    multipart = r.json()["data"]

    if multipart.get("fileExist"):
        # 文件已存在，仍需注册
        requests.post(f"{BASE}/v1/knowledge/file/submit", headers=HEADERS_JSON, json={
            "parentId": parent_id,
            "fileName": file_name,
            "md5": file_md5,
            "size": file_size,
            "url": multipart.get("path", "")
        })
        return

    host = multipart["host"]
    path = multipart["path"]
    token = multipart["token"]

    # 步骤 2: 二进制上传
    file_content = open(file_path, "rb").read()

    suffix = os.path.splitext(file_name)[1].lower()
    if suffix in {".md", ".markdown"}:
        content_type = "text/markdown; charset=utf-8"
    elif suffix == ".pdf":
        content_type = "application/pdf"
    else:
        ctype, _ = mimetypes.guess_type(file_name)
        content_type = ctype or "application/octet-stream"

    encoded_name = urllib.parse.quote(file_name, safe="-_.!~*'()")
    storage_param = base64.b64encode(json.dumps({
        "path": path,
        "option": {
            "contentDisposition": (
                f'inline; filename="{encoded_name}"; '
                f"filename*=UTF-8''{encoded_name}"
            ),
            "contentType": content_type,
        },
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).decode("utf-8")

    upload_url = host.rstrip("/") + "/api/upload/binary"
    req = urllib.request.Request(upload_url, method="POST", data=file_content)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-Storage-Param", storage_param)
    req.add_header("Content-Type", "application/octet-stream")

    with urllib.request.urlopen(req, timeout=300) as resp:
        upload_result = json.loads(resp.read().decode("utf-8"))

    # 步骤 3: 注册文件到知识库
    final_path = (upload_result.get("data") or {}).get("path") or path

    requests.post(f"{BASE}/v1/knowledge/file/submit", headers=HEADERS_JSON, json={
        "parentId": parent_id,
        "fileName": file_name,
        "md5": file_md5,
        "size": file_size,
        "url": final_path
    })
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 创建共享知识库
curl -s -X POST "https://open.bohrium.com/openapi/v1/knowledge/knowledge_base/create" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "knowledgeBaseName": "Journal Club — LLM for Science (2026-05-13)",
    "cover": "",
    "introduction": "Reading Club session papers and discussion guides",
    "privilege": 1
  }' | python3 -m json.tool

# 获取上传凭证（以上传讨论指南 Markdown 为例）
curl -s -G "https://open.bohrium.com/openapi/v1/knowledge/file/multipart" \
  -H "accessKey: $AK" \
  --data-urlencode "fileName=discussion_guide.md" \
  --data-urlencode "md5=YOUR_FILE_MD5" \
  --data-urlencode "parentId=YOUR_KB_NODE_ID" \
  --data-urlencode "size=YOUR_FILE_SIZE"
```

---

## 输出格式化

### Python 示例

```python
def format_guide_markdown(topic, guide):
    """
    将讨论指南格式化为 Markdown。
    """
    lines = []
    session_date = datetime.now().strftime("%Y-%m-%d")

    lines.append(f"# Journal Club 讨论指南")
    lines.append(f"\n**主题**: {topic}")
    lines.append(f"**日期**: {session_date}")
    lines.append(f"**推荐论文数**: {len(guide['session_papers'])}")

    # 论文概览表
    lines.append("\n## 论文概览\n")
    lines.append("| # | 标题 | 期刊 | IF | 引用 | 日期 |")
    lines.append("|---|------|------|----|------|------|")
    for i, pg in enumerate(guide["session_papers"], 1):
        title_short = pg["title"][:50] + ("..." if len(pg["title"]) > 50 else "")
        lines.append(
            f"| {i} | {title_short} | {pg['journal']} | "
            f"{pg['impact_factor']} | {pg['citations']} | {pg['date'][:10]} |"
        )

    # 每篇论文的详细讨论指南
    for i, pg in enumerate(guide["session_papers"], 1):
        lines.append(f"\n---\n")
        lines.append(f"## 论文 {i}: {pg['title']}")
        lines.append(f"\n**DOI**: `{pg['doi']}`")
        lines.append(f"**期刊**: {pg['journal']} (IF={pg['impact_factor']})")
        lines.append(f"**引用**: {pg['citations']}")
        lines.append(f"**日期**: {pg['date']}")

        if pg.get("authors"):
            authors_str = ", ".join(pg["authors"][:5])
            if len(pg["authors"]) > 5:
                authors_str += f" 等 ({len(pg['authors'])} 位作者)"
            lines.append(f"**作者**: {authors_str}")

        # 核心贡献
        lines.append(f"\n### 核心贡献\n")
        lines.append(pg["core_contribution"][:500])

        # 方法要点
        if pg.get("method_highlights"):
            lines.append(f"\n### 方法要点\n")
            for mh in pg["method_highlights"]:
                lines.append(f"- {mh[:200]}")

        # 关键结果
        if pg.get("key_results"):
            lines.append(f"\n### 关键结果\n")
            for kr in pg["key_results"]:
                lines.append(f"- {kr[:200]}")

        # 讨论问题
        lines.append(f"\n### 讨论问题\n")
        for q in pg["discussion_questions"]:
            lines.append(f"**[{q['category']}]** {q['question']}")
            lines.append(f"  - *提示*: {q['hint']}")
            lines.append("")

        # 背景引读
        primer = pg.get("background_primer", {})
        if primer:
            lines.append(f"### 背景知识引读\n")
            lines.append(f"- {primer.get('field_context', '')}")
            lines.append(f"- {primer.get('prerequisite_reading', '')}")
            lines.append(f"- 预计阅读时间: {primer.get('estimated_reading_time', '')}")

    # 论文间关联
    connections = guide.get("cross_paper_connections", [])
    if connections:
        lines.append(f"\n---\n")
        lines.append(f"## 论文间关联\n")
        for conn in connections:
            lines.append(f"### {conn['paper_a']} <-> {conn['paper_b']}\n")
            lines.append(f"- **关系类型**: {conn['relation_type']}")
            lines.append(f"- **共同关键词**: {', '.join(conn['shared_keywords'])}")
            lines.append(f"- **讨论建议**: {conn['discussion_point']}")
            lines.append("")

    return "\n".join(lines)
```

---

## 完整编排示例

以下是将全部步骤串联的端到端 Python 脚本：

```python
#!/usr/bin/env python3
"""
文献阅读俱乐部 (Reading Club) — 完整编排脚本

用法:
    export ACCESS_KEY="your_access_key"
    python3 reading_club.py

可修改下方 CONFIG 区域的参数来调整主题和筛选条件。
"""

import os
import sys
import time
import json
import tempfile
import hashlib
import base64
import urllib.request
import urllib.parse
import mimetypes
import re
import requests
from datetime import datetime, timedelta

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
    "topic": "Large language models for scientific discovery",
    "keywords": ["large language model", "scientific discovery",
                 "AI for science", "foundation model", "scientific reasoning"],
    "time_range_years": 1,
    "jcr_zones": ["Q1"],
    "participant_directions": [
        "molecular dynamics",
        "drug discovery",
        "materials science"
    ],
    "num_papers": 5,
    "save_to_kb": True,
}


# ============================================================
# 步骤 1: 论文检索与筛选
# ============================================================

def step1_search_and_filter(config):
    end_time = datetime.now().strftime("%Y-%m-%d")
    start_time = (datetime.now() - timedelta(
        days=365 * config["time_range_years"]
    )).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"步骤 1: 论文检索与筛选")
    print(f"  主题: {config['topic']}")
    print(f"  关键词: {config['keywords']}")
    print(f"  时间范围: {start_time} ~ {end_time}")
    print(f"  参会者方向: {config.get('participant_directions', [])}")
    print(f"{'='*60}\n")

    candidate_size = max(config["num_papers"] * 6, 30)

    r = requests.post(
        f"{BASE}/v1/paper/rag/pass/keyword",
        headers=HEADERS_JSON,
        json={
            "words": config["keywords"],
            "question": config["topic"],
            "type": 5,
            "startTime": start_time,
            "endTime": end_time,
            "jcrZones": config["jcr_zones"],
            "pageSize": candidate_size
        }
    )
    r.raise_for_status()

    text = r.text.strip()
    first_line = text.split('\n')[0]
    data = json.loads(first_line)

    if data.get("code") != 0:
        print(f"检索失败: {data.get('message')}")
        sys.exit(1)

    papers = data["data"]
    print(f"检索到 {len(papers)} 篇候选论文")

    if not papers:
        return []

    # 计算讨论价值分数
    now = datetime.now()
    three_months_ago = (now - timedelta(days=90)).strftime("%Y-%m-%d")

    for p in papers:
        score = 0.0

        pub_date = p.get("coverDateStart", "")
        if pub_date >= three_months_ago:
            score += 0.3
        elif pub_date >= (now - timedelta(days=180)).strftime("%Y-%m-%d"):
            score += 0.15

        citations = p.get("citationNums", 0)
        impact_factor = p.get("impactFactor", 0)
        if citations > 100 or impact_factor > 10:
            score += 0.25
        elif citations > 30 or impact_factor > 5:
            score += 0.15
        elif citations > 10 or impact_factor > 2:
            score += 0.08

        if citations > 50 and pub_date >= (now - timedelta(days=365)).strftime("%Y-%m-%d"):
            score += 0.25
        elif citations < 10 and impact_factor > 5 and pub_date >= three_months_ago:
            score += 0.20

        p["_discussion_score"] = score

    papers.sort(key=lambda p: p["_discussion_score"], reverse=True)

    # 多样性筛选
    directions = config.get("participant_directions", [])
    num = config["num_papers"]

    if directions and len(directions) > 1:
        selected = []
        used_dois = set()

        for direction in directions:
            for p in papers:
                doi = p.get("doi", "")
                if doi in used_dois:
                    continue
                title = p.get("enName", "").lower()
                abstract = p.get("enAbstract", "").lower()
                if direction.lower() in title or direction.lower() in abstract:
                    selected.append(p)
                    used_dois.add(doi)
                    break

        remaining = num - len(selected)
        for p in papers:
            if remaining <= 0:
                break
            doi = p.get("doi", "")
            if doi not in used_dois:
                selected.append(p)
                used_dois.add(doi)
                remaining -= 1

        selected = selected[:num]
    else:
        selected = papers[:num]

    print(f"\n筛选出 {len(selected)} 篇推荐论文:\n")
    for i, p in enumerate(selected, 1):
        print(f"  {i}. {p['enName'][:70]}")
        print(f"     DOI: {p.get('doi', 'N/A')} | "
              f"IF: {p.get('impactFactor', 0)} | "
              f"引用: {p.get('citationNums', 0)} | "
              f"讨论分: {p['_discussion_score']:.2f}")

    return selected


# ============================================================
# 步骤 2: 快速摘要
# ============================================================

def step2_quick_summaries(papers):
    print(f"\n{'='*60}")
    print(f"步骤 2: 为 {len(papers)} 篇论文生成快速摘要")
    print(f"{'='*60}\n")

    summaries = {}
    tokens = {}

    for p in papers:
        doi = p.get("doi", "")
        if not doi:
            continue

        pdf_url = f"https://doi.org/{doi}"
        try:
            r = requests.post(
                f"{BASE}/v1/parse/trigger-url-async",
                headers=HEADERS_JSON,
                json={
                    "url": pdf_url,
                    "sync": False,
                    "textual": True,
                    "table": True,
                    "expression": True,
                    "equation": True,
                    "pages": [0, 1, 2, 3, 4],
                    "timeout": 1800
                }
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("code"):
                tokens[doi] = data["token"]
                print(f"  提交: {doi} -> token={data['token'][:16]}...")
            else:
                print(f"  跳过: {doi} -> {data.get('message', 'error')}")
        except Exception as e:
            print(f"  失败: {doi} -> {e}")

    # 轮询
    if tokens:
        print(f"\n  等待 {len(tokens)} 个解析任务...\n")
        pending = dict(tokens)
        max_wait = 120
        start = time.time()

        while pending and (time.time() - start) < max_wait:
            time.sleep(3)
            done_keys = []
            for doi, token in pending.items():
                try:
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
                        content = result.get("content", "")
                        summary = {"core_contribution": "", "method_highlights": [], "key_results": []}

                        # 提取核心贡献
                        propose = re.findall(
                            r'[^.]*(?:we (?:propose|present|introduce|develop))\b[^.]+\.',
                            content, re.IGNORECASE
                        )
                        if propose:
                            summary["core_contribution"] = propose[0].strip()

                        # 提取方法要点
                        methods = re.findall(
                            r'[^.]*(?:our (?:method|approach|framework|model))[^.]+\.',
                            content, re.IGNORECASE
                        )
                        summary["method_highlights"] = [m.strip() for m in methods[:3]]

                        # 提取关键结果
                        results = re.findall(
                            r'[^.]*(?:achieve|outperform|improve)[^.]+\.',
                            content, re.IGNORECASE
                        )
                        summary["key_results"] = [r_.strip() for r_ in results[:3]]

                        summaries[doi] = {"content": content, "summary": summary}
                        print(f"  完成: {doi} ({len(content)} 字符)")
                        done_keys.append(doi)
                    elif status == "failed":
                        print(f"  失败: {doi}")
                        done_keys.append(doi)
                except Exception as e:
                    print(f"  错误: {doi} -> {e}")

            for k in done_keys:
                del pending[k]

    # 为未解析的论文使用元数据
    for p in papers:
        doi = p.get("doi", "")
        if doi and doi not in summaries:
            abstract = p.get("enAbstract", "")
            summaries[doi] = {
                "content": "",
                "summary": {
                    "core_contribution": abstract[:300] if abstract else "",
                    "method_highlights": [],
                    "key_results": []
                }
            }

    print(f"\n摘要生成完成: {len(summaries)} 篇")
    return summaries


# ============================================================
# 步骤 3: 生成讨论指南
# ============================================================

def step3_generate_guide(papers, summaries):
    print(f"\n{'='*60}")
    print(f"步骤 3: 生成讨论指南")
    print(f"{'='*60}\n")

    guide = {"session_papers": [], "cross_paper_connections": []}

    for p in papers:
        doi = p.get("doi", "")
        paper_summary = summaries.get(doi, {}).get("summary", {})
        abstract = p.get("enAbstract", "")

        questions = [
            {
                "category": "研究动机",
                "question": "本文要解决的核心问题是什么？为什么这个问题在当前研究背景下重要？",
                "hint": "关注 Introduction 中对现有方法的不足的描述。"
            },
            {
                "category": "方法创新",
                "question": "本文提出的方法与已有方法的本质区别是什么？这种设计选择背后的直觉是什么？",
                "hint": "关注 Methods 部分的核心算法/模型架构。"
            },
            {
                "category": "实验设计",
                "question": "实验设计是否充分支撑了论文的核心论断？有哪些遗漏的对照实验？",
                "hint": "检查 baseline 选择是否公平，评估指标是否全面。"
            },
            {
                "category": "局限与拓展",
                "question": "本文方法的主要局限性是什么？如果你要做后续研究，你会怎么改进？",
                "hint": "思考适用范围、计算成本、数据依赖等方面。"
            },
        ]

        citations = p.get("citationNums", 0)
        if citations > 50:
            questions.append({
                "category": "领域影响",
                "question": f"本文已被引用 {citations} 次，它对该领域的主要影响是什么？",
                "hint": "思考方法的通用性和可迁移性。"
            })
        else:
            questions.append({
                "category": "领域影响",
                "question": "本文的工作是否有可能改变该子领域的研究范式？为什么？",
                "hint": "结合领域发展趋势判断。"
            })

        paper_guide = {
            "doi": doi,
            "title": p.get("enName", ""),
            "authors": p.get("authors", [])[:5],
            "journal": p.get("publicationEnName", ""),
            "impact_factor": p.get("impactFactor", 0),
            "citations": citations,
            "date": p.get("coverDateStart", ""),
            "core_contribution": paper_summary.get("core_contribution", abstract[:300]),
            "discussion_questions": questions,
            "background_primer": {
                "field_context": f"发表于 {p.get('publicationEnName', 'N/A')}"
                                 f"{'（高影响力期刊）' if p.get('impactFactor', 0) > 5 else ''}。",
                "prerequisite_reading": "建议预习 Abstract 和 Introduction，理解问题定义和已有方法的不足。",
                "estimated_reading_time": "快速浏览: 15-20 分钟；精读: 45-60 分钟"
            },
            "method_highlights": paper_summary.get("method_highlights", []),
            "key_results": paper_summary.get("key_results", [])
        }

        guide["session_papers"].append(paper_guide)

    # 分析论文间关联
    stop_words = {"a", "an", "the", "of", "in", "for", "and", "or", "to",
                  "with", "on", "by", "is", "are", "was", "were", "from",
                  "at", "as", "its", "this", "that", "using", "based"}

    for i in range(len(papers)):
        for j in range(i + 1, len(papers)):
            p1, p2 = papers[i], papers[j]
            t1 = set(p1.get("enName", "").lower().split()) - stop_words
            t2 = set(p2.get("enName", "").lower().split()) - stop_words
            overlap = t1 & t2

            if len(overlap) >= 2:
                guide["cross_paper_connections"].append({
                    "paper_a": p1.get("enName", "")[:60],
                    "paper_b": p2.get("enName", "")[:60],
                    "relation_type": "主题相关",
                    "shared_keywords": list(overlap)[:5],
                    "discussion_point": f"对比这两篇论文在 {', '.join(list(overlap)[:3])} 方面的不同处理方式。"
                })

    print(f"讨论指南已生成:")
    print(f"  - {len(guide['session_papers'])} 篇论文")
    print(f"  - {len(guide['cross_paper_connections'])} 组论文间关联")

    return guide


# ============================================================
# 步骤 4: 存入知识库 + 格式化输出
# ============================================================

def format_guide_markdown(topic, guide):
    lines = []
    session_date = datetime.now().strftime("%Y-%m-%d")

    lines.append(f"# Journal Club 讨论指南")
    lines.append(f"\n**主题**: {topic}")
    lines.append(f"**日期**: {session_date}")
    lines.append(f"**推荐论文数**: {len(guide['session_papers'])}")

    lines.append("\n## 论文概览\n")
    lines.append("| # | 标题 | 期刊 | IF | 引用 | 日期 |")
    lines.append("|---|------|------|----|------|------|")
    for i, pg in enumerate(guide["session_papers"], 1):
        t = pg["title"][:50] + ("..." if len(pg["title"]) > 50 else "")
        lines.append(f"| {i} | {t} | {pg['journal']} | "
                     f"{pg['impact_factor']} | {pg['citations']} | {pg['date'][:10]} |")

    for i, pg in enumerate(guide["session_papers"], 1):
        lines.append(f"\n---\n")
        lines.append(f"## 论文 {i}: {pg['title']}")
        lines.append(f"\n**DOI**: `{pg['doi']}`")
        lines.append(f"**期刊**: {pg['journal']} (IF={pg['impact_factor']})")
        lines.append(f"**引用**: {pg['citations']}")
        lines.append(f"**日期**: {pg['date']}")

        if pg.get("authors"):
            authors_str = ", ".join(pg["authors"][:5])
            if len(pg["authors"]) > 5:
                authors_str += f" 等 ({len(pg['authors'])} 位作者)"
            lines.append(f"**作者**: {authors_str}")

        lines.append(f"\n### 核心贡献\n")
        lines.append(pg["core_contribution"][:500])

        if pg.get("method_highlights"):
            lines.append(f"\n### 方法要点\n")
            for mh in pg["method_highlights"]:
                lines.append(f"- {mh[:200]}")

        if pg.get("key_results"):
            lines.append(f"\n### 关键结果\n")
            for kr in pg["key_results"]:
                lines.append(f"- {kr[:200]}")

        lines.append(f"\n### 讨论问题\n")
        for q in pg["discussion_questions"]:
            lines.append(f"**[{q['category']}]** {q['question']}")
            lines.append(f"  - *提示*: {q['hint']}")
            lines.append("")

        primer = pg.get("background_primer", {})
        if primer:
            lines.append(f"### 背景知识引读\n")
            lines.append(f"- {primer.get('field_context', '')}")
            lines.append(f"- {primer.get('prerequisite_reading', '')}")
            lines.append(f"- 预计阅读时间: {primer.get('estimated_reading_time', '')}")

    connections = guide.get("cross_paper_connections", [])
    if connections:
        lines.append(f"\n---\n")
        lines.append(f"## 论文间关联\n")
        for conn in connections:
            lines.append(f"### {conn['paper_a']} <-> {conn['paper_b']}\n")
            lines.append(f"- **关系类型**: {conn['relation_type']}")
            lines.append(f"- **共同关键词**: {', '.join(conn['shared_keywords'])}")
            lines.append(f"- **讨论建议**: {conn['discussion_point']}")
            lines.append("")

    return "\n".join(lines)


def step4_save_to_kb(topic, guide):
    print(f"\n{'='*60}")
    print(f"步骤 4: 存入共享知识库")
    print(f"{'='*60}\n")

    session_date = datetime.now().strftime("%Y-%m-%d")
    kb_name = f"Journal Club — {topic} ({session_date})"

    r = requests.post(
        f"{BASE}/v1/knowledge/knowledge_base/create",
        headers=HEADERS_JSON,
        json={
            "knowledgeBaseName": kb_name,
            "cover": "",
            "introduction": f"Reading Club session: {topic}. "
                          f"Contains {len(guide['session_papers'])} recommended papers.",
            "privilege": 1
        }
    )
    r.raise_for_status()
    data = r.json()

    if data.get("code") != 0:
        print(f"创建知识库失败: {data.get('message')}")
        return None

    kb_id = data["data"]["id"]
    print(f"知识库已创建: ID={kb_id}, 名称={kb_name}")

    # 生成并上传讨论指南
    guide_md = format_guide_markdown(topic, guide)
    guide_filename = f"discussion_guide_{session_date}.md"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                      delete=False, encoding="utf-8") as f:
        f.write(guide_md)
        temp_path = f.name

    try:
        _upload_file(temp_path, kb_id, guide_filename)
        print(f"讨论指南已上传: {guide_filename}")
    except Exception as e:
        print(f"上传讨论指南失败: {e}")
    finally:
        os.unlink(temp_path)

    return kb_id


def _upload_file(file_path, parent_id, file_name):
    """三步上传文件到知识库。"""
    file_size = os.path.getsize(file_path)

    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    file_md5 = h.hexdigest()

    r = requests.get(f"{BASE}/v1/knowledge/file/multipart", headers=HEADERS, params={
        "fileName": file_name, "md5": file_md5, "parentId": parent_id, "size": file_size
    })
    mp = r.json()["data"]

    if mp.get("fileExist"):
        requests.post(f"{BASE}/v1/knowledge/file/submit", headers=HEADERS_JSON, json={
            "parentId": parent_id, "fileName": file_name,
            "md5": file_md5, "size": file_size, "url": mp.get("path", "")
        })
        return

    host, path, token = mp["host"], mp["path"], mp["token"]

    file_content = open(file_path, "rb").read()
    suffix = os.path.splitext(file_name)[1].lower()
    content_type = {".md": "text/markdown; charset=utf-8",
                    ".pdf": "application/pdf"}.get(suffix, "application/octet-stream")

    enc_name = urllib.parse.quote(file_name, safe="-_.!~*'()")
    sp = base64.b64encode(json.dumps({
        "path": path,
        "option": {
            "contentDisposition": f'inline; filename="{enc_name}"; filename*=UTF-8\'\'{enc_name}',
            "contentType": content_type,
        },
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).decode("utf-8")

    req = urllib.request.Request(host.rstrip("/") + "/api/upload/binary",
                                 method="POST", data=file_content)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-Storage-Param", sp)
    req.add_header("Content-Type", "application/octet-stream")

    with urllib.request.urlopen(req, timeout=300) as resp:
        upload_result = json.loads(resp.read().decode("utf-8"))

    final_path = (upload_result.get("data") or {}).get("path") or path
    requests.post(f"{BASE}/v1/knowledge/file/submit", headers=HEADERS_JSON, json={
        "parentId": parent_id, "fileName": file_name,
        "md5": file_md5, "size": file_size, "url": final_path
    })


# ============================================================
# 主流程
# ============================================================

def main():
    config = CONFIG

    print(f"\n{'#'*60}")
    print(f"  文献阅读俱乐部 (Reading Club)")
    print(f"  主题: {config['topic']}")
    print(f"{'#'*60}")

    # 步骤 1: 检索与筛选
    papers = step1_search_and_filter(config)
    if not papers:
        print("未检索到论文，退出")
        sys.exit(1)

    # 步骤 2: 快速摘要
    summaries = step2_quick_summaries(papers)

    # 步骤 3: 生成讨论指南
    guide = step3_generate_guide(papers, summaries)

    # 输出讨论指南
    output = format_guide_markdown(config["topic"], guide)
    print("\n" + output)

    # 步骤 4: 存入知识库（可选）
    if config.get("save_to_kb", True):
        kb_id = step4_save_to_kb(config["topic"], guide)
        if kb_id:
            print(f"\n知识库 ID: {kb_id}")

    # 保存本地副本
    output_file = f"reading_club_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n讨论指南已保存到: {output_file}")


if __name__ == "__main__":
    main()
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 检索结果为空 | 关键词太窄或时间范围太小 | 扩大关键词范围，放宽时间限制，移除 JCR 分区筛选 |
| 推荐论文方向单一 | 未设置 `participant_directions` | 填写参会者研究方向列表以启用多样性筛选 |
| PDF 解析全部失败 | DOI 对应的 PDF 不可直接下载 | 不影响讨论指南生成，脚本会使用论文元数据（标题和摘要）作为替代 |
| 讨论问题太泛 | 摘要信息不充分 | PDF 解析成功后会自动提取更具体的方法和结果信息来定制问题 |
| 响应含多行 JSON | paper-search 返回 streaming 格式 | 取第一行解析即可：`json.loads(r.text.split('\n')[0])` |
| 知识库创建失败 | ACCESS_KEY 权限不足 | 确认 ACCESS_KEY 有效，检查 `~/.openclaw/openclaw.json` 配置 |
| 上传文件失败 | 文件过大或网络不稳定 | 讨论指南为 Markdown 文本文件，通常很小；如果失败可手动保存本地副本 |
| 401 Unauthorized | accessKey 无效 | 确认 ACCESS_KEY 正确，检查 `~/.openclaw/openclaw.json` 配置 |
| 论文间关联为空 | 推荐论文标题差异较大 | 正常现象；论文关联基于关键词重叠，跨领域论文可能无直接关联 |
| 执行时间过长 | PDF 解析等待较久 | 解析仅解析前 5 页，通常 1-2 分钟完成；如超时脚本会自动跳过 |

---

## 搭配使用

- **reading-club** 筛选讨论论文 -> **paper-dissector** 为主讲人深度拆解其中一篇
- **reading-club** 存入知识库 -> **bohrium-knowledge-base** 管理和搜索历次讨论材料
- **frontier-alert** 发现最新热点 -> **reading-club** 围绕热点组织讨论
- **conference-tracker** 追踪会议论文 -> **reading-club** 从会议论文中选题讨论
