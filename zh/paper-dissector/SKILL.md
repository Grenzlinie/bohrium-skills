---
name: paper-dissector
description: "Deep paper analysis combining PDF parsing, knowledge graph verification, and citation checking. Use when: user wants to deeply understand a specific paper, critique its methodology, or extract structured insights from a paper. NOT for: searching papers (use bohrium-paper-search), literature review across many papers (use literature-review)."
---

# SKILL: 论文精读拆解 (Paper Dissector)

## 概述

编排 `bohrium-pdf-parser`、`bohrium-lkm`、`bohrium-paper-search` 三个原子技能，对单篇论文进行深度拆解分析。从 PDF 解析到核心论断验证、引文质量评估，输出结构化的精读报告。

**编排流程：**

```
PDF URL / DOI / 标题
        │
        ▼
┌─────────────────┐
│  pdf-parser      │  全文解析 → 提取文本、表格、公式
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  lkm claims/match│  提取核心论断 → 知识图谱验证 → 证据链追溯
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  paper-search    │  检索关键引文 → 评估引用恰当性
└────────┬────────┘
         │
         ▼
   结构化精读报告
```

**两种分析深度：**

| 模式 | 解析范围 | 论断验证 | 引文检索 | 适用场景 |
|------|----------|----------|----------|----------|
| 快速拆解 | 前 3-5 页（摘要+方法+结论） | 前 3 条核心论断 | 前 5 篇关键引文 | 初筛、组会汇报准备 |
| 深度批判 | 全文所有页 | 所有主要论断 | 全部引文抽查 | 审稿、方法论评估、跟进研究 |

**适用场景：**

- 精读一篇论文，理解其研究问题、方法创新和实验设计
- 验证论文核心结论是否有足够文献支撑
- 评估引用文献的质量和恰当性
- 快速生成论文拆解笔记供组会讨论

**不适用：**

- 搜索论文 → `bohrium-paper-search`
- 跨多篇论文的综述 → `literature-review`
- 仅需提取 PDF 文本 → `bohrium-pdf-parser`
- 仅需验证单个论断 → `bohrium-lkm`

## 认证配置

本技能复用底层三个原子技能共同的 ACCESS_KEY：

```json
"paper-dissector": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `paper` | string | 是 | 论文 PDF URL、DOI、或标题 |
| `mode` | string | 否 | `quick`（快速拆解，默认）或 `deep`（深度批判） |

## 输出结构

精读报告包含以下六部分：

1. **一句话总结** — 用一句话概括论文核心贡献
2. **研究问题拆解** — What（研究什么）→ Why（为什么重要）→ How（怎么解决）
3. **方法创新标注** — 论文方法论中的创新点及其与已有方法的差异
4. **实验设计评价** — 数据是否充分支撑结论，实验设计是否存在漏洞
5. **局限性与未来方向** — 论文自述局限 + 分析发现的潜在问题
6. **值得跟进的引文** — 推荐阅读的引用文献及推荐理由

---

## 报告分析深度要求

**精读报告不是论文内容的复述**。你是一个有批判性思维的研究者，必须在报告中提供：

### 方法创新标注的深度标准

- **必须对比已有方法**：不能只说"提出了一种新方法"，必须指出"相比 [具体方法]，本文的改进在于 [具体差异]"
- **用 LKM 验证新颖性**：如果 LKM 匹配到高相似度已有工作，需在报告中指出"注意：[已有工作] 使用了类似思路"
- **定量对比**：方法改进幅度必须引用论文中的具体数字（如"相比 baseline 提升 15% AUROC"）

### 实验设计评价的严格标准

不能仅说"实验充分/不充分"，必须逐条检查：

| 检查项 | 评价标准 |
|--------|---------|
| Baseline 选择 | 是否包含最新 SOTA？是否有非深度学习 baseline？ |
| 数据集多样性 | 是否在多个数据集验证？是否有分布外测试？ |
| 消融实验 | 每个创新组件是否都有单独的消融？ |
| 统计显著性 | 是否报告误差棒/p-value/多次运行？ |
| 公平对比 | 超参数调优是否对所有方法一致？计算资源是否可比？ |

### 禁止的行为

- ❌ 只复述论文摘要（这不是精读）
- ❌ "本文提出了一种方法，效果很好"——这是什么都没说
- ❌ 局限性只引用论文自述的 limitation，不做独立判断
- ❌ 实验评价不引用具体数字
- ❌ "值得跟进的引文"只列标题不说明为什么值得读

---

## 完整编排脚本

以下 Python 脚本实现端到端的论文精读拆解流程。

```python
#!/usr/bin/env python3
"""
论文精读拆解 (Paper Dissector)
编排 pdf-parser + lkm + paper-search，输出结构化精读报告。
"""

import os
import re
import sys
import json
import time
import requests

# ─── 配置 ───────────────────────────────────────────────

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误：未设置 ACCESS_KEY 环境变量。")
    print("请在 ~/.openclaw/openclaw.json 中配置 paper-dissector.env.ACCESS_KEY")
    sys.exit(1)

BASE_PARSE = "https://open.bohrium.com/openapi/v1/parse"
BASE_LKM   = "https://open.bohrium.com/openapi/v1/lkm"
BASE_PAPER  = "https://open.bohrium.com/openapi/v1/paper"

H_JSON = {"accessKey": AK, "Content-Type": "application/json"}
H_AK   = {"accessKey": AK}

# ─── 工具函数 ───────────────────────────────────────────

def doi_to_pdf_url(doi: str) -> str:
    """尝试将 DOI 转换为可下载的 PDF URL（优先 Sci-Hub / arXiv）"""
    if doi.startswith("10.48550/arxiv."):
        arxiv_id = doi.replace("10.48550/arxiv.", "")
        return f"https://arxiv.org/pdf/{arxiv_id}"
    if "arxiv.org" in doi:
        return doi if doi.endswith(".pdf") else doi + ".pdf"
    # 通用 DOI：返回 doi.org 链接，实际使用时可能需要手动提供 PDF URL
    return f"https://doi.org/{doi}"


def extract_claims_from_text(text: str, mode: str = "quick") -> list[str]:
    """
    从论文文本中提取核心科学论断。
    策略：定位 Abstract、Conclusion、Results 段落，提取断言性语句。
    """
    claims = []

    # 按段落标记拆分（pdf-parser 返回的格式含 LaTeX 风格标记）
    sections = re.split(r'\\begin\{(?:title|section|subsection)\}', text)

    # 识别关键段落：Abstract, Introduction, Results, Discussion, Conclusion
    key_section_patterns = [
        r'(?i)abstract',
        r'(?i)conclusion',
        r'(?i)results?\s*(and\s*discussion)?',
        r'(?i)discussion',
        r'(?i)summary',
    ]

    key_text_parts = []
    for section in sections:
        first_line = section.strip()[:200].lower()
        for pattern in key_section_patterns:
            if re.search(pattern, first_line):
                key_text_parts.append(section)
                break

    # 如果未匹配到段落标记，fallback 到全文
    if not key_text_parts:
        key_text_parts = [text]

    combined = "\n".join(key_text_parts)

    # 提取断言性语句：包含 "show that", "demonstrate", "indicate",
    # "suggest", "reveal", "confirm", "prove", "find that" 等
    claim_patterns = [
        r'[^.]*(?:show(?:s|ed)?|demonstrate(?:s|d)?|indicate(?:s|d)?|'
        r'suggest(?:s|ed)?|reveal(?:s|ed)?|confirm(?:s|ed)?|'
        r'prove(?:s|d)?|find(?:s)?|found)\s+that\b[^.]+\.',
        r'[^.]*(?:outperform(?:s|ed)?|achieve(?:s|d)?|improve(?:s|d)?)\b[^.]+\.',
        r'[^.]*(?:we (?:propose|present|introduce|develop))\b[^.]+\.',
    ]

    for pattern in claim_patterns:
        matches = re.findall(pattern, combined, re.IGNORECASE)
        for m in matches:
            claim = m.strip()
            # 过滤太短或太长的句子
            if 20 < len(claim) < 500:
                claims.append(claim)

    # 去重
    seen = set()
    unique_claims = []
    for c in claims:
        normalized = c.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            unique_claims.append(c)

    # 根据模式限制数量
    if mode == "quick":
        return unique_claims[:3]
    return unique_claims[:15]


def extract_cited_keywords(text: str, mode: str = "quick") -> list[str]:
    """
    从论文文本中提取关键引用相关的术语，用于后续 paper-search 检索。
    """
    # 提取方法名、模型名、数据集名等专有名词
    # 策略：找 Introduction 和 Related Work 中的高频名词短语
    keywords = set()

    # 匹配引用上下文中的关键术语（出现在 [数字] 前后的名词短语）
    cite_contexts = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\[[\d,\s]+\]', text)
    for ctx in cite_contexts:
        if len(ctx) > 3:
            keywords.add(ctx)

    # 匹配方法/模型名（通常以大写开头的复合词）
    method_patterns = re.findall(
        r'\b([A-Z][a-zA-Z]*(?:Net|GAN|BERT|GPT|Transformer|CNN|RNN|'
        r'GNN|VAE|Flow|Model|Method|Algorithm|Framework|Network))\b',
        text
    )
    keywords.update(method_patterns)

    result = list(keywords)
    if mode == "quick":
        return result[:5]
    return result[:15]


# ─── 步骤 1：PDF 解析 ──────────────────────────────────

def parse_pdf(pdf_url: str, mode: str = "quick") -> dict:
    """
    调用 pdf-parser 解析 PDF。
    quick 模式只解析前 5 页，deep 模式解析全文。
    返回 {content, pages_dict, status}。
    """
    print(f"[步骤 1/3] PDF 解析：{pdf_url}")
    print(f"  模式：{'快速拆解（前5页）' if mode == 'quick' else '深度批判（全文）'}")

    payload = {
        "url": pdf_url,
        "sync": False,
        "textual": True,
        "table": True,
        "molecule": False,
        "chart": True,
        "figure": False,
        "expression": True,
        "equation": True,
        "timeout": 1800
    }

    # quick 模式只解析前 5 页
    if mode == "quick":
        payload["pages"] = [0, 1, 2, 3, 4]

    # 提交解析任务
    try:
        r = requests.post(
            f"{BASE_PARSE}/trigger-url-async",
            headers=H_JSON,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("  错误：无法连接到 open.bohrium.com，请检查网络。")
        return {"status": "failed", "content": "", "error": "连接失败"}
    except requests.exceptions.Timeout:
        print("  错误：提交请求超时。")
        return {"status": "failed", "content": "", "error": "请求超时"}

    submit = r.json()
    if submit.get("code"):
        print(f"  提交失败：{submit.get('message', '未知错误')}")
        return {"status": "failed", "content": "", "error": submit.get("message")}

    token = submit["token"]
    print(f"  已提交，token={token}")

    # 轮询结果（最多等 120 秒）
    for attempt in range(60):
        time.sleep(2)
        try:
            r = requests.post(
                f"{BASE_PARSE}/get-result",
                headers=H_JSON,
                json={"token": token, "content": True, "objects": False, "pages_dict": True},
                timeout=30
            )
            result = r.json()
        except Exception as e:
            print(f"  [{attempt+1}] 查询失败：{e}")
            continue

        status = result.get("status", "")
        proc_page = result.get("proc_page", 0)
        total_page = result.get("total_page", 0)

        if status == "success":
            content = result.get("content", "")
            print(f"  解析完成！共 {total_page} 页，内容长度 {len(content)} 字符")
            return {
                "status": "success",
                "content": content,
                "pages_dict": result.get("pages_dict", {}),
                "total_page": total_page,
                "lang": result.get("lang", "en")
            }
        elif status == "failed":
            desc = result.get("description", "未知错误")
            print(f"  解析失败：{desc}")
            return {"status": "failed", "content": "", "error": desc}
        else:
            if attempt % 5 == 0:
                print(f"  [{attempt+1}] 解析中... ({proc_page}/{total_page} 页)")

    print("  超时：解析任务未在 120 秒内完成。")
    print("  提示：论文页数较多时，可尝试 quick 模式或直接提供更短的 PDF。")
    return {"status": "timeout", "content": "", "error": "解析超时（120秒）"}


# ─── 步骤 2：LKM 论断验证 ──────────────────────────────

def verify_claims(claims: list[str]) -> list[dict]:
    """
    对每条论断调用 lkm claims/match，返回验证结果。
    """
    print(f"\n[步骤 2/3] 论断验证：共 {len(claims)} 条论断")
    results = []

    for i, claim in enumerate(claims):
        print(f"\n  论断 {i+1}/{len(claims)}：")
        print(f"    {claim[:100]}{'...' if len(claim) > 100 else ''}")

        try:
            r = requests.post(
                f"{BASE_LKM}/claims/match",
                headers=H_JSON,
                json={"text": claim, "limit": 5},
                timeout=30
            )
            data = r.json()
        except Exception as e:
            print(f"    验证失败：{e}")
            results.append({
                "claim": claim,
                "status": "error",
                "error": str(e),
                "variables": [],
                "new_claim_likely": None
            })
            continue

        variables = data.get("data", {}).get("variables", [])
        papers = data.get("data", {}).get("papers", {})
        new_claim = data.get("data", {}).get("new_claim_likely", None)

        # 解读验证结果
        interpretation = interpret_verification(claim, variables, new_claim)
        print(f"    {interpretation['summary']}")

        results.append({
            "claim": claim,
            "status": "verified",
            "variables": variables,
            "papers": papers,
            "new_claim_likely": new_claim,
            "interpretation": interpretation
        })

    return results


def interpret_verification(claim: str, variables: list, new_claim_likely: bool) -> dict:
    """
    解读 LKM 验证结果，判断论断的支撑程度。

    解读逻辑：
    - score > 0.8：强相关匹配，该领域已有高度相似的研究结论
    - score 0.5-0.8：中等相关，存在相关研究但表述或条件不同
    - score < 0.5：弱相关，可能是较新的发现
    - new_claim_likely = True：知识图谱中无足够支撑/反驳证据，可能是新发现
    - role = "premise"：匹配到的是前提条件，说明论断的基础假设有文献支持
    - role = "conclusion"：匹配到的是已有结论，说明类似结论已有人提出
    """
    if not variables:
        return {
            "level": "无匹配",
            "summary": "知识图谱中未找到相关论断，可能是全新发现或表述差异较大",
            "detail": "建议：手动检查该论断是否使用了非常规术语"
        }

    top_score = max(v.get("score", 0) for v in variables)
    roles = [v.get("role", "") for v in variables]
    has_conclusion = "conclusion" in roles
    has_premise = "premise" in roles

    if new_claim_likely:
        level = "可能新发现"
        summary = f"LKM 判定该论断可能是新发现（new_claim_likely=True），最高匹配分 {top_score:.2f}"
        detail = "知识图谱中证据不足以支撑或反驳该论断，建议重点关注其实验设计的严谨性"
    elif top_score > 0.8:
        level = "强支撑"
        summary = f"有强相关已有研究（score={top_score:.2f}），该结论在领域内已有充分基础"
        if has_conclusion:
            detail = "匹配到已有结论，说明类似发现已被报道。需关注本文的增量贡献"
        else:
            detail = "匹配到相关前提，论断的基础假设在文献中得到支持"
    elif top_score > 0.5:
        level = "部分支撑"
        summary = f"存在中等相关研究（score={top_score:.2f}），但条件或表述存在差异"
        detail = "有相关工作但不完全一致，需关注本文方法/条件的差异是否构成创新"
    else:
        level = "弱支撑"
        summary = f"仅有弱相关匹配（score={top_score:.2f}），该方向研究较少"
        detail = "文献支撑较弱，可能是较新的研究方向。建议检查实验是否充分可靠"

    return {"level": level, "summary": summary, "detail": detail}


# ─── 步骤 3：引文检索与评估 ─────────────────────────────

def check_citations(keywords: list[str], paper_text: str, mode: str = "quick") -> list[dict]:
    """
    用 paper-search 检索关键引文，评估引用质量。
    """
    print(f"\n[步骤 3/3] 引文检索：共 {len(keywords)} 个关键术语")

    if not keywords:
        print("  未提取到关键引用术语，跳过引文检索。")
        return []

    # 构造搜索请求
    question = f"key methods and results related to: {', '.join(keywords[:5])}"
    search_words = keywords[:8]

    try:
        r = requests.post(
            f"{BASE_PAPER}/rag/pass/keyword",
            headers=H_JSON,
            json={
                "words": search_words,
                "question": question,
                "type": 5,
                "pageSize": 10 if mode == "quick" else 20
            },
            timeout=30
        )
        data = r.json()
    except Exception as e:
        print(f"  检索失败：{e}")
        return []

    papers = data.get("data", [])
    print(f"  找到 {len(papers)} 篇相关文献")

    citation_results = []
    for p in papers:
        doi = p.get("doi", "")
        title = p.get("enName", "")
        abstract = p.get("enAbstract", "")
        citations = p.get("citationNums", 0)
        impact_factor = p.get("impactFactor", 0)
        journal = p.get("publicationEnName", "")
        date = p.get("coverDateStart", "")

        # 判断引用质量
        quality = "高" if (citations > 50 or impact_factor > 5) else "中" if (citations > 10 or impact_factor > 2) else "一般"

        # 判断是否值得跟进
        worth_following = citations > 20 or impact_factor > 3

        citation_results.append({
            "doi": doi,
            "title": title,
            "journal": journal,
            "date": date,
            "citations": citations,
            "impact_factor": impact_factor,
            "quality": quality,
            "worth_following": worth_following,
            "abstract_preview": abstract[:200] if abstract else ""
        })

    # 按引用数排序
    citation_results.sort(key=lambda x: x["citations"], reverse=True)

    # 输出值得跟进的引文
    worth = [c for c in citation_results if c["worth_following"]]
    if worth:
        print(f"  值得跟进的引文：{len(worth)} 篇")
        for c in worth[:5]:
            print(f"    - {c['title'][:60]}... (IF={c['impact_factor']}, 被引={c['citations']})")

    return citation_results


# ─── 报告生成 ───────────────────────────────────────────

def generate_report(
    paper_input: str,
    mode: str,
    parse_result: dict,
    claim_results: list[dict],
    citation_results: list[dict]
) -> str:
    """
    汇总所有分析结果，生成结构化精读报告（Markdown 格式）。
    """
    report = []
    report.append(f"# 论文精读拆解报告\n")
    report.append(f"**输入**：{paper_input}")
    report.append(f"**分析模式**：{'快速拆解' if mode == 'quick' else '深度批判'}")
    report.append(f"**解析状态**：{parse_result.get('status', 'unknown')}")
    report.append(f"**论文语言**：{parse_result.get('lang', 'unknown')}")
    report.append(f"**总页数**：{parse_result.get('total_page', 'N/A')}\n")

    content = parse_result.get("content", "")

    # ── 1. 一句话总结 ──
    report.append("## 1. 一句话总结\n")
    if content:
        # 提取摘要段落用于总结
        abstract_match = re.search(
            r'(?i)\\begin\{(?:abstract|section)\}.*?abstract.*?\\end\{(?:abstract|section)\}',
            content, re.DOTALL
        )
        if abstract_match:
            report.append(f"> 基于摘要自动提取（请根据全文理解进行修订）：\n")
            abstract_text = re.sub(r'\\[a-z]+\{[^}]*\}', '', abstract_match.group())[:300]
            report.append(f"_{abstract_text.strip()}_\n")
        else:
            report.append("> 请根据解析全文撰写一句话总结。\n")
    else:
        report.append("> PDF 解析未成功，无法自动生成。\n")

    # ── 2. 研究问题拆解 ──
    report.append("## 2. 研究问题拆解\n")
    report.append("| 维度 | 内容 |")
    report.append("|------|------|")
    report.append("| **What** — 研究什么 | （请根据全文填写） |")
    report.append("| **Why** — 为什么重要 | （请根据 Introduction 填写） |")
    report.append("| **How** — 怎么解决 | （请根据 Methods 填写） |\n")

    # ── 3. 方法创新标注 ──
    report.append("## 3. 方法创新标注\n")
    if claim_results:
        for cr in claim_results:
            interp = cr.get("interpretation", {})
            level = interp.get("level", "未知")
            detail = interp.get("detail", "")
            claim_text = cr["claim"][:150]
            if level in ("可能新发现", "弱支撑"):
                report.append(f"- **[创新]** {claim_text}")
                report.append(f"  - 验证结果：{level} — {detail}")
    else:
        report.append("未提取到可分析的方法论断。\n")

    report.append("")

    # ── 4. 实验设计评价 ──
    report.append("## 4. 实验设计评价\n")
    report.append("### 论断验证结果\n")
    if claim_results:
        report.append("| # | 论断（截取） | 验证级别 | 解读 |")
        report.append("|---|------------|---------|------|")
        for i, cr in enumerate(claim_results):
            interp = cr.get("interpretation", {})
            claim_short = cr["claim"][:80].replace("|", "\\|")
            level = interp.get("level", "未知")
            summary = interp.get("summary", "").replace("|", "\\|")
            report.append(f"| {i+1} | {claim_short} | {level} | {summary} |")

        report.append("")
        report.append("### 验证结果解读指南\n")
        report.append("- **强支撑**（score > 0.8）：该结论在领域内已有充分文献基础，需关注增量贡献")
        report.append("- **部分支撑**（score 0.5-0.8）：存在相关研究但条件不同，方法/条件差异可能构成创新")
        report.append("- **弱支撑**（score < 0.5）：研究方向较新，需重点检查实验设计的严谨性")
        report.append("- **可能新发现**（new_claim_likely=True）：知识图谱中证据不足，建议审慎对待")
        report.append("- **无匹配**：可能是全新发现，也可能是术语差异导致未匹配\n")

        # 统计支撑分布
        levels = [cr.get("interpretation", {}).get("level", "未知") for cr in claim_results]
        report.append("### 支撑分布\n")
        for lv in ["强支撑", "部分支撑", "弱支撑", "可能新发现", "无匹配"]:
            count = levels.count(lv)
            if count > 0:
                report.append(f"- {lv}：{count} 条")
        report.append("")
    else:
        report.append("未提取到可验证的论断。\n")

    # ── 5. 局限性与未来方向 ──
    report.append("## 5. 局限性与未来方向\n")
    if content:
        # 尝试提取 Limitations 段落
        limit_match = re.search(
            r'(?i)(limitation|future\s*work|future\s*direction)[s]?.*?(?=\\begin\{|$)',
            content[:10000], re.DOTALL
        )
        if limit_match:
            report.append(f"> 论文自述局限（自动提取，请核实）：\n")
            limit_text = limit_match.group()[:500]
            report.append(f"_{limit_text.strip()}_\n")
        else:
            report.append("> 未检测到显式的 Limitations 段落。请根据方法和实验分析潜在局限。\n")

    new_claim_count = sum(
        1 for cr in claim_results
        if cr.get("interpretation", {}).get("level") in ("可能新发现", "弱支撑")
    )
    if new_claim_count > 0:
        report.append(f"**分析发现**：有 {new_claim_count} 条论断在知识图谱中支撑较弱，"
                      f"这些可能是值得深入验证的新方向。\n")

    # ── 6. 值得跟进的引文 ──
    report.append("## 6. 值得跟进的引文\n")
    worth = [c for c in citation_results if c["worth_following"]]
    if worth:
        report.append("| # | 标题 | 期刊 | 影响因子 | 被引次数 | 推荐理由 |")
        report.append("|---|------|------|---------|---------|---------|")
        for i, c in enumerate(worth[:10]):
            title = c["title"][:50].replace("|", "\\|")
            journal = c["journal"][:20].replace("|", "\\|") if c["journal"] else "N/A"
            reason = f"IF={c['impact_factor']}, 高引用" if c["citations"] > 50 else "领域相关"
            report.append(
                f"| {i+1} | {title} | {journal} | "
                f"{c['impact_factor']} | {c['citations']} | {reason} |"
            )
        report.append("")
    else:
        report.append("未检索到明显值得跟进的引文。\n")

    return "\n".join(report)


# ─── 主流程 ─────────────────────────────────────────────

def dissect_paper(paper_input: str, mode: str = "quick"):
    """
    论文精读拆解主函数。

    参数：
        paper_input: PDF URL / DOI / 论文标题
        mode: "quick"（快速拆解）或 "deep"（深度批判）
    """
    print("=" * 60)
    print("  论文精读拆解 (Paper Dissector)")
    print(f"  输入：{paper_input}")
    print(f"  模式：{'快速拆解' if mode == 'quick' else '深度批判'}")
    print("=" * 60)

    # 判断输入类型并转换为 PDF URL
    pdf_url = paper_input
    if paper_input.startswith("10."):
        # DOI 格式
        pdf_url = doi_to_pdf_url(paper_input)
        print(f"\n检测到 DOI 输入，转换为 URL：{pdf_url}")
    elif not paper_input.startswith("http"):
        # 可能是论文标题，先用 paper-search 搜索
        print(f"\n检测到标题输入，先搜索论文...")
        try:
            r = requests.post(
                f"{BASE_PAPER}/rag/pass/keyword",
                headers=H_JSON,
                json={
                    "words": paper_input.split()[:5],
                    "question": paper_input,
                    "type": 5,
                    "pageSize": 1
                },
                timeout=30
            )
            data = r.json()
            if data.get("data"):
                first = data["data"][0]
                doi = first.get("doi", "")
                title = first.get("enName", "")
                print(f"  找到：{title}")
                print(f"  DOI：{doi}")
                if doi:
                    pdf_url = doi_to_pdf_url(doi)
                else:
                    print("  警告：未找到 DOI，无法获取 PDF URL。请直接提供 PDF 链接。")
                    return
            else:
                print("  未找到匹配论文。请提供更精确的标题或直接提供 PDF URL。")
                return
        except Exception as e:
            print(f"  搜索失败：{e}。请直接提供 PDF URL。")
            return

    # ── 步骤 1：PDF 解析 ──
    parse_result = parse_pdf(pdf_url, mode)

    if parse_result["status"] not in ("success",):
        error = parse_result.get("error", "未知错误")
        print(f"\nPDF 解析失败（{error}），无法继续分析。")
        print("可能的原因及解决方案：")
        print("  1. PDF URL 不可直接下载 → 请提供直链（如 arXiv PDF 链接）")
        print("  2. PDF 文件损坏或格式不支持 → 尝试其他版本")
        print("  3. 网络连接问题 → 检查网络后重试")
        print("  4. 解析超时 → 尝试 quick 模式或减少页数")
        return

    content = parse_result["content"]

    # ── 步骤 2：提取并验证论断 ──
    claims = extract_claims_from_text(content, mode)
    print(f"\n从论文中提取到 {len(claims)} 条核心论断")

    claim_results = []
    if claims:
        claim_results = verify_claims(claims)
    else:
        print("  未能自动提取论断。可能原因：")
        print("  - 论文使用非标准表述")
        print("  - PDF 解析内容不完整")
        print("  建议：手动输入核心论断，用 lkm claims/match 逐条验证")

    # ── 步骤 3：引文检索 ──
    keywords = extract_cited_keywords(content, mode)
    citation_results = check_citations(keywords, content, mode)

    # ── 生成报告 ──
    print("\n" + "=" * 60)
    print("  生成精读报告...")
    print("=" * 60 + "\n")

    report = generate_report(paper_input, mode, parse_result, claim_results, citation_results)
    print(report)

    return report


# ─── 入口 ───────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python paper_dissector.py <PDF_URL|DOI|标题> [quick|deep]")
        print()
        print("示例：")
        print("  python paper_dissector.py https://arxiv.org/pdf/2107.06922 quick")
        print("  python paper_dissector.py 10.1038/s41586-021-03819-2 deep")
        print('  python paper_dissector.py "Attention Is All You Need" quick')
        sys.exit(1)

    paper = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "quick"

    if mode not in ("quick", "deep"):
        print(f"未知模式：{mode}，使用默认 quick 模式")
        mode = "quick"

    dissect_paper(paper, mode)
```

---

## 各步骤详解

### 步骤 1：PDF 解析 (`pdf-parser`)

调用 `trigger-url-async` 提交 PDF 解析任务，异步轮询 `get-result` 获取结果。

**quick 模式优化**：只解析前 5 页（摘要 + 引言 + 方法 + 结论通常在这个范围内），大幅缩短等待时间。

```python
# quick 模式：只解析前 5 页
payload["pages"] = [0, 1, 2, 3, 4]

# deep 模式：不设 pages 参数，解析全文
```

**解析结果格式**：pdf-parser 返回的文本使用 LaTeX 风格标记（`\begin{title}`、`\begin{section}` 等），脚本基于这些标记定位关键段落。

---

### 步骤 2：论断提取与 LKM 验证

#### 论断提取策略

从解析文本的关键段落（Abstract、Results、Conclusion）中，匹配断言性语句：

```python
# 匹配 "show that", "demonstrate that", "indicate that" 等模式
claim_patterns = [
    r'[^.]*(?:show|demonstrate|indicate|suggest|reveal|confirm|prove|find)\s+that\b[^.]+\.',
    r'[^.]*(?:outperform|achieve|improve)\b[^.]+\.',
    r'[^.]*(?:we propose|we present|we introduce)\b[^.]+\.',
]
```

#### LKM 验证结果解读

`claims/match` 返回的关键字段解读：

| 字段 | 含义 | 解读方法 |
|------|------|----------|
| `score` | 匹配相关度（0-1） | > 0.8 强相关，0.5-0.8 中等，< 0.5 弱相关 |
| `role` | `premise` 或 `conclusion` | premise = 匹配到前提假设；conclusion = 匹配到已有结论 |
| `new_claim_likely` | 是否可能是新发现 | `true` 表示知识图谱中证据不足 |
| `provenance` | 来源论文信息 | 可追溯到具体论文和版本 |

**验证结果分级：**

```
强支撑（score > 0.8）
  → 该结论在领域内已有充分基础
  → 关注点：本文的增量贡献是什么？

部分支撑（score 0.5-0.8）
  → 存在相关研究但条件/方法不同
  → 关注点：差异是否构成创新？

弱支撑（score < 0.5）
  → 该方向研究较少
  → 关注点：实验设计是否充分可靠？

可能新发现（new_claim_likely = True）
  → 知识图谱中无足够支撑/反驳证据
  → 关注点：实验的可重复性和数据的充分性

无匹配
  → 可能是全新发现，也可能是术语差异
  → 关注点：手动检查是否有等价表述的已有研究
```

#### 支撑 vs 反驳证据的区分

当 `claims/match` 返回匹配结果时，需结合 `role` 和 `content` 综合判断：

- 若匹配到的 `conclusion` 与输入论断方向一致（如：A 提升 B → 匹配到"A 显著增强 B"），说明已有 **支撑证据**
- 若匹配到的 `conclusion` 与输入论断方向相反（如：A 提升 B → 匹配到"A 对 B 无显著影响"），说明存在 **矛盾证据**
- 使用 `claims/{id}/evidence` 可进一步获取证据链细节

```python
# 进一步获取证据链
for var in claim_match_result["data"]["variables"]:
    claim_id = var["id"]
    r = requests.get(f"{BASE_LKM}/claims/{claim_id}/evidence", headers=H_JSON)
    evidence = r.json()
    for ev in evidence.get("data", []):
        print(f"  证据来源：{ev.get('paper_title')}")
        print(f"  证据类型：{ev.get('evidence_type')}")
        print(f"  证据内容：{ev.get('text')[:200]}")
```

---

### 步骤 3：引文检索与评估 (`paper-search`)

从论文文本中提取关键术语（方法名、模型名、引用上下文），用 `paper-search` 检索相关文献，评估引用质量。

**引文质量分级：**

| 级别 | 条件 | 说明 |
|------|------|------|
| 高 | 被引 > 50 或 IF > 5 | 高影响力论文，通常是领域基础工作 |
| 中 | 被引 > 10 或 IF > 2 | 有一定影响力的相关工作 |
| 一般 | 其他 | 需判断是否为关键方法来源 |

---

## 使用示例

### 快速拆解一篇 arXiv 论文

```python
dissect_paper("https://arxiv.org/pdf/2107.06922", mode="quick")
```

### 通过 DOI 深度批判

```python
dissect_paper("10.1038/s41586-021-03819-2", mode="deep")
```

### 通过标题搜索并分析

```python
dissect_paper("Attention Is All You Need", mode="quick")
```

### 命令行调用

```bash
# 快速拆解
python paper_dissector.py https://arxiv.org/pdf/2107.06922 quick

# 深度批判
python paper_dissector.py 10.1038/s41586-021-03819-2 deep

# 标题搜索
python paper_dissector.py "Highly accurate protein structure prediction with AlphaFold" deep
```

---

## 错误处理

| 场景 | 错误信息 | 处理方式 |
|------|---------|---------|
| ACCESS_KEY 未设置 | `未设置 ACCESS_KEY 环境变量` | 配置 `~/.openclaw/openclaw.json` |
| PDF URL 不可访问 | `提交失败` / `解析失败` | 检查 URL 是否为直链，尝试其他 PDF 源 |
| PDF 解析超时 | `解析任务未在 120 秒内完成` | 使用 quick 模式减少页数，或对超长论文拆分处理 |
| 网络连接失败 | `无法连接到 open.bohrium.com` | 检查网络连接、DNS 解析 |
| 论断提取为空 | `未能自动提取论断` | 论文使用非标准表述，手动输入论断用 lkm 验证 |
| LKM 验证超时 | `验证失败：timeout` | 减少论断数量，或分批验证 |
| 论文搜索无结果 | `未找到匹配论文` | 使用更精确的标题或直接提供 PDF URL |
| DOI 无法转为 PDF URL | `未找到 DOI` | 手动从出版商页面获取 PDF 直链 |

---

## 搭配使用

- **paper-dissector** 拆解单篇论文 → **paper-search** 扩展阅读相关文献
- **paper-dissector** 验证论断 → **lkm** 深入追溯证据链
- **paper-dissector** 输出报告 → **knowledge-base** 存档笔记
- 多篇 **paper-dissector** 报告 → 汇总为综述大纲
