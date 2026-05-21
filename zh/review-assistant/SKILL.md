---
name: review-assistant
description: "Peer review assistance combining PDF analysis, literature coverage check, and novelty verification to help reviewers write structured reviews. Use when: user is reviewing a paper as a referee and needs help assessing novelty, completeness, and writing a structured review. NOT for: pre-submission self-review (use pre-review), paper reading (use paper-dissector)."
---

# SKILL: 同行评议辅助 (Review Assistant)

## 概述

编排 `bohrium-pdf-parser`、`bohrium-paper-search`、`bohrium-lkm` 三个原子技能，辅助审稿人对论文进行同行评议。从 PDF 全文解析到文献覆盖度检查、核心论断验证，最终输出符合期刊/会议标准的结构化审稿意见框架。

**编排流程：**

```
待审论文 PDF + 期刊/会议审稿标准（可选）
        │
        ▼
┌─────────────────┐
│  pdf-parser      │  全文解析 → 提取文本、表格、公式、参考文献
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  paper-search    │  文献覆盖度检查 → 是否遗漏重要相关工作？
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  lkm claims/match│  核心论断验证 → 论文声明是否有证据支撑？
└────────┬────────┘
         │
         ▼
   结构化审稿意见框架
   (Summary / Strengths / Weaknesses /
    Questions / Minor Comments / Recommendation)
```

**适用场景：**

- 作为审稿人，需要对论文进行系统性评审
- 需要快速评估论文的新颖性和文献覆盖度
- 需要生成符合期刊/会议格式的结构化审稿意见
- 审稿时间紧张，需要 AI 辅助梳理论文的优缺点
- 想确保审稿意见全面、公正、有据可依

**不适用：**

- 投稿前自查 → `pre-review`（从作者视角出发，提供评分和改进优先级）
- 精读他人论文 → `paper-dissector`（侧重理解方法和拆解逻辑）
- 跨多篇论文综述 → `literature-review`
- 仅需搜索论文 → `bohrium-paper-search`
- 仅需解析 PDF → `bohrium-pdf-parser`
- 仅需验证单个论断 → `bohrium-lkm`

---

## 伦理准则

> **负责任使用声明**：本技能旨在**辅助**审稿人，而非替代审稿人的专业判断。请在使用时遵守以下准则：

1. **AI 辅助，人工决策** — 本工具输出的是审稿意见的"框架"和"素材"，最终的审稿意见必须由审稿人根据自身专业知识审核、修改和完善。不要直接复制粘贴 AI 生成的意见作为最终审稿结果。

2. **保密性** — 同行评审是保密过程。请确保待审论文 PDF 仅通过安全的方式传输，不要将论文内容泄露给第三方。使用本技能时，论文内容会通过 Bohrium API 处理，请确认这符合您所在期刊/会议的审稿保密政策。

3. **公正性** — AI 生成的分析可能存在偏差（如对某些研究领域覆盖不足）。审稿人有责任确保最终意见公正、客观，不因 AI 工具的局限性而对论文产生不公正的评价。

4. **透明性** — 如果期刊/会议有关于 AI 辅助审稿的政策，请遵守相关规定。部分期刊要求审稿人披露是否使用了 AI 工具辅助审稿。

5. **建设性** — 审稿的目的是帮助作者改进论文。请确保最终的审稿意见具有建设性，提供具体的改进建议，而非仅仅指出问题。

6. **不滥用** — 不要利用本工具获取未发表论文的研究思路用于自己的研究。审稿是一项学术义务，应以诚信为本。

---

## 认证配置

本技能复用底层三个原子技能共同的 ACCESS_KEY：

```json
"review-assistant": {
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
| `paper` | string | 是 | 待审论文 PDF URL（建议 arXiv 直链或可下载链接） |
| `review_standard` | string | 否 | 期刊/会议审稿标准名称（如 "NeurIPS", "Nature", "ICLR"），用于调整评审侧重点 |

## 输出结构

审稿意见框架包含以下六部分，符合主流期刊/会议的审稿格式：

1. **Summary** — 一段话概括论文的研究问题、方法和主要贡献
2. **Strengths** — 论文的 3-5 个优点（新颖性、实验设计、写作质量等）
3. **Weaknesses** — 论文的 3-5 个不足（方法局限、实验缺失、文献遗漏等）
4. **Questions for Authors** — 需要作者在 rebuttal 中回答的关键问题
5. **Minor Comments** — 小问题和建议（格式、表述、笔误等）
6. **Recommendation** — 评审建议（Accept / Minor Revision / Major Revision / Reject）

---

## 审稿质量控制

### Weaknesses 的可操作性

每个 weakness **必须附带具体的改进建议**，不能只指出问题：
- ✅ "缺少与 MACE (Batatia 2022) 的对比。建议在 Table 2 中增加一行，数据可从原文 Table 3 获取。"
- ❌ "实验对比不够全面。"（指出了问题但没有告诉作者怎么改）

### Questions 的针对性

问题必须是**该论文特有的**，不能是通用审稿模板问题：
- ✅ "Figure 3 中 loss 在 epoch 50 后出现异常抖动，这是训练不稳定还是学习率调度的副作用？"
- ❌ "是否考虑过其他 baseline？"（太泛，每篇论文都能问）

### Recommendation 的一致性

评审建议必须与 Strengths/Weaknesses 的严重程度一致：
- 如果 Weaknesses 中有"致命缺陷"（如核心实验有错误），不能给 Minor Revision
- 如果所有 Weaknesses 都是"补充实验/改善写作"级别，不应给 Major Revision

### 禁止的行为

- ❌ 只指出问题不给解决方案
- ❌ 使用模板化审稿语言（如"The paper is well-written but..."开头的通用评语）
- ❌ Strengths 和 Weaknesses 数量严重不均（如 1 个优点 + 8 个缺点，或反之）
- ❌ 推荐理由与正文评价矛盾

---

## 完整编排脚本

以下 Python 脚本实现端到端的同行评议辅助流程。

```python
#!/usr/bin/env python3
"""
同行评议辅助 (Review Assistant)
编排 pdf-parser + paper-search + lkm，输出结构化审稿意见框架。
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
    print("请在 ~/.openclaw/openclaw.json 中配置 review-assistant.env.ACCESS_KEY")
    sys.exit(1)

BASE_PARSE = "https://open.bohrium.com/openapi/v1/parse"
BASE_LKM   = "https://open.bohrium.com/openapi/v1/lkm"
BASE_PAPER = "https://open.bohrium.com/openapi/v1/paper"

H_JSON = {"accessKey": AK, "Content-Type": "application/json"}

# ─── 步骤 1：PDF 全文解析 ──────────────────────────────

def parse_pdf(pdf_url: str) -> dict:
    """
    调用 pdf-parser 解析待审论文 PDF 全文。
    返回 {status, content, pages_dict, total_page, lang}。
    """
    print(f"[步骤 1/3] PDF 全文解析：{pdf_url}")

    payload = {
        "url": pdf_url,
        "sync": False,
        "textual": True,
        "table": True,
        "expression": True,
        "equation": True,
        "timeout": 1800
    }

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

    # 轮询结果（最多等 180 秒）
    for attempt in range(90):
        time.sleep(2)
        try:
            r = requests.post(
                f"{BASE_PARSE}/get-result",
                headers=H_JSON,
                json={
                    "token": token,
                    "content": True,
                    "objects": False,
                    "pages_dict": True
                },
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

    print("  超时：解析任务未在 180 秒内完成。")
    return {"status": "timeout", "content": "", "error": "解析超时（180秒）"}


# ─── 文本分析工具函数 ──────────────────────────────────

def extract_sections(text: str) -> dict:
    """
    从 pdf-parser 返回的文本中按段落标记拆分各节。
    返回 {section_name: section_text}。
    """
    sections = {}
    # pdf-parser 使用 LaTeX 风格标记
    parts = re.split(r'\\begin\{(?:section|subsection)\}\{([^}]*)\}', text)

    # parts 格式: [前文, 标题1, 内容1, 标题2, 内容2, ...]
    if len(parts) >= 3:
        for i in range(1, len(parts) - 1, 2):
            sec_name = parts[i].strip().lower()
            sec_text = parts[i + 1] if (i + 1) < len(parts) else ""
            sections[sec_name] = sec_text
    else:
        # 无法按标记拆分，用启发式方式识别段落
        section_patterns = [
            (r'(?i)abstract', "abstract"),
            (r'(?i)introduction', "introduction"),
            (r'(?i)related\s*work', "related work"),
            (r'(?i)method(?:ology|s)?', "methods"),
            (r'(?i)experiment(?:s|al)?', "experiments"),
            (r'(?i)result(?:s)?', "results"),
            (r'(?i)discussion', "discussion"),
            (r'(?i)conclusion(?:s)?', "conclusion"),
            (r'(?i)reference(?:s)?', "references"),
        ]
        for pattern, name in section_patterns:
            match = re.search(pattern, text)
            if match:
                start = match.start()
                end = len(text)
                for p2, _ in section_patterns:
                    m2 = re.search(p2, text[start + len(match.group()):])
                    if m2:
                        candidate_end = start + len(match.group()) + m2.start()
                        if candidate_end < end:
                            end = candidate_end
                sections[name] = text[start:end]

    return sections


def extract_claims(text: str, sections: dict) -> list[str]:
    """
    从论文中提取核心科学论断（创新声明、实验结论）。
    优先从 Abstract、Introduction、Results、Conclusion 提取。
    """
    claims = []

    key_sections = ["abstract", "introduction", "conclusion", "results", "discussion"]
    key_text_parts = []
    for sec in key_sections:
        for sec_name, sec_text in sections.items():
            if sec in sec_name:
                key_text_parts.append(sec_text)

    combined = "\n".join(key_text_parts) if key_text_parts else text

    # 提取创新声明
    novelty_patterns = [
        r'[^.]*(?:we\s+(?:propose|present|introduce|develop|design))\b[^.]+\.',
        r'[^.]*(?:our\s+(?:method|approach|framework|model|algorithm|system))\b[^.]+\.',
        r'[^.]*(?:novel|new|first|unique)\b[^.]*(?:approach|method|framework|model)\b[^.]+\.',
    ]

    # 提取实验结论
    result_patterns = [
        r'[^.]*(?:show(?:s|ed)?|demonstrate(?:s|d)?|indicate(?:s|d)?)\s+that\b[^.]+\.',
        r'[^.]*(?:outperform(?:s|ed)?|surpass(?:es|ed)?|exceed(?:s|ed)?)\b[^.]+\.',
        r'[^.]*(?:achieve(?:s|d)?|attain(?:s|ed)?)\s+(?:state-of-the-art|SOTA|best|superior)\b[^.]+\.',
        r'[^.]*(?:improve(?:s|d)?|enhance(?:s|d)?|boost(?:s|ed)?)\b[^.]*(?:by|over|compared)\b[^.]+\.',
    ]

    for pattern in novelty_patterns + result_patterns:
        matches = re.findall(pattern, combined, re.IGNORECASE)
        for m in matches:
            claim = m.strip()
            if 20 < len(claim) < 500:
                claims.append(claim)

    # 去重
    seen = set()
    unique = []
    for c in claims:
        normalized = c.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(c)

    return unique[:20]


def extract_reference_keywords(text: str, sections: dict) -> list[str]:
    """
    从论文的 Related Work 和 Introduction 中提取关键方法名/模型名，
    用于后续 paper-search 检索比对。
    """
    keywords = set()

    target_text = ""
    for sec_name, sec_text in sections.items():
        if "related" in sec_name or "introduction" in sec_name or "background" in sec_name:
            target_text += sec_text + "\n"

    if not target_text:
        target_text = text[:5000]

    # 提取方法/模型名
    method_patterns = re.findall(
        r'\b([A-Z][a-zA-Z]*(?:Net|GAN|BERT|GPT|Transformer|CNN|RNN|GNN|'
        r'VAE|Flow|Model|Method|Algorithm|Framework|Network|Diff|LLM|'
        r'former|tion|ing))\b',
        target_text
    )
    keywords.update(method_patterns)

    # 提取引用上下文中的关键术语
    cite_contexts = re.findall(
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s*(?:\[[\d,\s]+\]|\([\w\s,]+\d{4}\))',
        target_text
    )
    for ctx in cite_contexts:
        if len(ctx) > 3:
            keywords.add(ctx)

    return list(keywords)[:15]


def extract_referenced_works(text: str) -> list[str]:
    """
    从论文参考文献段落中提取被引用的论文标题。
    """
    refs = []
    ref_match = re.search(r'(?i)\\begin\{(?:section|subsection)\}\{references?\}', text)
    if not ref_match:
        ref_match = re.search(r'(?i)\breferences?\b\s*\n', text)

    if ref_match:
        ref_text = text[ref_match.start():]
        titles_quoted = re.findall(r'["“]([^"”]{20,200})["”]', ref_text)
        refs.extend(titles_quoted)
        titles_period = re.findall(r'(?:(?:19|20)\d{2}[a-z]?\.?\s*)([A-Z][^.]{20,200}?)\.', ref_text)
        refs.extend(titles_period)

    return refs[:50]


def check_experiment_completeness(text: str, sections: dict) -> dict:
    """
    检查实验设计的完整性：是否有对比实验、消融实验、统计检验。
    """
    result = {
        "has_baseline_comparison": False,
        "has_ablation_study": False,
        "has_statistical_test": False,
        "has_multiple_datasets": False,
        "has_qualitative_analysis": False,
        "missing_items": []
    }

    exp_text = ""
    for sec_name, sec_text in sections.items():
        if any(k in sec_name for k in ["experiment", "result", "evaluation", "ablation"]):
            exp_text += sec_text + "\n"

    if not exp_text:
        exp_text = text

    if re.search(r'(?i)(baseline|comparison|compared?\s+(?:to|with)|benchmark|state-of-the-art|SOTA)', exp_text):
        result["has_baseline_comparison"] = True
    else:
        result["missing_items"].append("缺少与基线方法的对比实验 (baseline comparison)")

    if re.search(r'(?i)(ablation|ablative|variant|without\s+\w+\s+module|w/o)', exp_text):
        result["has_ablation_study"] = True
    else:
        result["missing_items"].append("缺少消融实验 (ablation study)")

    if re.search(r'(?i)(p-value|t-test|significant|confidence\s+interval|standard\s+deviation|'
                 r'error\s+bar|mean\s*[±\+\-]|std|variance|ANOVA)', exp_text):
        result["has_statistical_test"] = True
    else:
        result["missing_items"].append("缺少统计检验或误差分析 (statistical test / error analysis)")

    dataset_mentions = re.findall(r'(?i)(dataset|benchmark|corpus)\b', exp_text)
    if len(dataset_mentions) >= 2:
        result["has_multiple_datasets"] = True
    else:
        result["missing_items"].append("仅在单一数据集上验证，建议要求作者增加多数据集实验")

    if re.search(r'(?i)(qualitative|case\s+study|visualization|example|illustrat)', exp_text):
        result["has_qualitative_analysis"] = True
    else:
        result["missing_items"].append("缺少定性分析或案例展示 (qualitative analysis / case study)")

    return result


def check_logic_chain(claims: list[str], sections: dict) -> list[dict]:
    """
    检查论证逻辑链：每个结论是否在实验部分有对应的数据支撑。
    """
    logic_results = []

    exp_text = ""
    for sec_name, sec_text in sections.items():
        if any(k in sec_name for k in ["experiment", "result", "evaluation"]):
            exp_text += sec_text + "\n"

    for claim in claims:
        key_terms = re.findall(r'\b([A-Z][a-zA-Z]+|[a-z]+(?:tion|ment|ness|ity))\b', claim)
        key_terms = [t for t in key_terms if len(t) > 3][:5]

        matches_in_exp = 0
        for term in key_terms:
            if re.search(re.escape(term), exp_text, re.IGNORECASE):
                matches_in_exp += 1

        coverage = matches_in_exp / max(len(key_terms), 1)

        if coverage >= 0.6:
            support_level = "充分支撑"
        elif coverage >= 0.3:
            support_level = "部分支撑"
        else:
            support_level = "支撑不足"

        logic_results.append({
            "claim": claim,
            "key_terms": key_terms,
            "support_level": support_level,
            "coverage": coverage
        })

    return logic_results


# ─── 步骤 2：文献覆盖度检查 ────────────────────────────

def check_literature_coverage(
    keywords: list[str],
    referenced_works: list[str],
    paper_text: str
) -> dict:
    """
    用 paper-search 检索领域重要文献，与论文已引用的文献对比，
    找出遗漏的重要相关工作。
    """
    print(f"\n[步骤 2/3] 文献覆盖度检查")
    print(f"  提取到 {len(keywords)} 个关键术语，{len(referenced_works)} 篇参考文献")

    if not keywords:
        print("  未提取到关键术语，跳过文献覆盖度检查。")
        return {"searched_papers": [], "missing_papers": [], "coverage_ratio": 0}

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
                "jcrZones": ["Q1", "Q2"],
                "pageSize": 20
            },
            timeout=30
        )
        data = r.json()
    except Exception as e:
        print(f"  检索失败：{e}")
        return {"searched_papers": [], "missing_papers": [], "coverage_ratio": 0}

    if isinstance(data, str):
        data = json.loads(data.split('\n')[0])

    searched_papers = data.get("data", [])
    print(f"  检索到 {len(searched_papers)} 篇领域重要文献")

    ref_text_lower = " ".join(referenced_works).lower()
    paper_text_lower = paper_text.lower()

    missing_papers = []
    covered_papers = []

    for p in searched_papers:
        title = p.get("enName", "")
        doi = p.get("doi", "")
        citations = p.get("citationNums", 0)
        authors = p.get("authors", "")

        title_words = [w.lower() for w in title.split() if len(w) > 4]
        title_match = sum(1 for w in title_words if w in paper_text_lower)
        title_coverage = title_match / max(len(title_words), 1)

        doi_in_text = doi.lower() in paper_text_lower if doi else False
        is_cited = doi_in_text or title_coverage > 0.5

        paper_info = {
            "title": title,
            "doi": doi,
            "citations": citations,
            "authors": authors[:100],
            "journal": p.get("publicationEnName", ""),
            "year": p.get("coverDateStart", "")[:4],
            "impact_factor": p.get("impactFactor", 0),
            "is_cited": is_cited
        }

        if is_cited:
            covered_papers.append(paper_info)
        else:
            if citations > 20 or p.get("impactFactor", 0) > 3:
                missing_papers.append(paper_info)

    coverage_ratio = len(covered_papers) / max(len(searched_papers), 1)

    print(f"  已引用：{len(covered_papers)} 篇")
    print(f"  可能遗漏的重要文献：{len(missing_papers)} 篇")
    if missing_papers:
        for mp in missing_papers[:5]:
            print(f"    - {mp['title'][:60]}... (被引={mp['citations']}, IF={mp['impact_factor']})")

    return {
        "searched_papers": searched_papers,
        "covered_papers": covered_papers,
        "missing_papers": missing_papers,
        "coverage_ratio": coverage_ratio
    }


# ─── 步骤 3：核心论断验证 ────────────────────────────────

def verify_claims(claims: list[str]) -> list[dict]:
    """
    对每条核心论断调用 lkm claims/match，验证其在已有文献中的支撑情况。
    """
    print(f"\n[步骤 3/3] 核心论断验证：共 {len(claims)} 条论断")
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
                "new_claim_likely": None,
                "assessment": "验证失败"
            })
            continue

        variables = data.get("data", {}).get("variables", [])
        papers = data.get("data", {}).get("papers", {})
        new_claim_likely = data.get("data", {}).get("new_claim_likely", None)

        assessment = assess_claim_for_review(claim, variables, new_claim_likely)
        print(f"    评估：{assessment['level']} — {assessment['summary']}")

        results.append({
            "claim": claim,
            "status": "verified",
            "variables": variables,
            "papers": papers,
            "new_claim_likely": new_claim_likely,
            "assessment": assessment
        })

    return results


def assess_claim_for_review(claim: str, variables: list, new_claim_likely: bool) -> dict:
    """
    从审稿人视角评估论断，判断其是否值得肯定（作为 Strength）
    或需要质疑（作为 Weakness / Question）。
    """
    if not variables:
        return {
            "level": "无匹配",
            "summary": "知识图谱中未找到相关论断",
            "for_review": "可作为新颖性亮点（Strength），但需要求作者提供更充分的实验证据",
            "category": "strength_or_question"
        }

    top_score = max(v.get("score", 0) for v in variables)
    roles = [v.get("role", "") for v in variables]
    has_conclusion = "conclusion" in roles
    has_premise = "premise" in roles

    if new_claim_likely:
        return {
            "level": "可能新发现",
            "summary": f"LKM 判定可能是新发现（new_claim_likely=True），最高匹配分 {top_score:.2f}",
            "for_review": "新颖性较高，可作为 Strength 肯定；建议在 Questions 中要求作者补充更多证据",
            "category": "strength"
        }
    elif top_score > 0.8 and has_conclusion:
        return {
            "level": "高度重合",
            "summary": f"与已有结论高度匹配（score={top_score:.2f}），新颖性存疑",
            "for_review": "应列入 Weakness：与已有工作高度重合，需要作者明确增量贡献",
            "category": "weakness"
        }
    elif top_score > 0.8 and has_premise:
        return {
            "level": "基础已知",
            "summary": f"前提假设已有文献支撑（score={top_score:.2f}），但结论可能是新的",
            "for_review": "基础扎实可作为 Strength；但需确认作者是否引用了相关前提工作",
            "category": "strength"
        }
    elif top_score > 0.5:
        return {
            "level": "部分相关",
            "summary": f"存在中等相关研究（score={top_score:.2f}），有差异",
            "for_review": "建议在 Questions 中要求作者与相关工作进行更详细的对比讨论",
            "category": "question"
        }
    else:
        return {
            "level": "弱相关",
            "summary": f"仅有弱相关匹配（score={top_score:.2f}），研究方向较新",
            "for_review": "新颖性可作为 Strength；但实验严谨性需重点审查",
            "category": "strength"
        }


# ─── 审稿意见生成 ────────────────────────────────────────

def generate_review(
    pdf_url: str,
    review_standard: str,
    parse_result: dict,
    sections: dict,
    claims: list[str],
    claim_results: list[dict],
    experiment_check: dict,
    literature_check: dict,
    logic_results: list[dict]
) -> str:
    """
    汇总所有分析结果，生成结构化审稿意见框架（Markdown 格式）。
    """
    report = []
    report.append("# 审稿意见框架 (Review Draft)\n")
    report.append(f"**待审论文**：{pdf_url}")
    report.append(f"**审稿标准**：{review_standard or '通用标准'}")
    report.append(f"**总页数**：{parse_result.get('total_page', 'N/A')}")
    report.append(f"**论文语言**：{parse_result.get('lang', 'unknown')}")
    report.append("")
    report.append("> **提示**：以下内容为 AI 辅助生成的审稿意见框架，请审稿人根据自身专业判断进行审核、修改和补充。")
    report.append("")

    content = parse_result.get("content", "")

    # ── 1. Summary ──
    report.append("## 1. Summary\n")
    abstract_text = ""
    for sec_name, sec_text in sections.items():
        if "abstract" in sec_name:
            abstract_text = re.sub(r'\\[a-z]+\{[^}]*\}', '', sec_text).strip()
            break

    if abstract_text:
        # 截取合理长度的摘要
        summary_text = abstract_text[:600]
        report.append(f"本文{summary_text}")
        report.append("")
        report.append("*[请审稿人根据全文理解修订上述总结，确保准确反映论文核心贡献]*\n")
    else:
        report.append("*[请审稿人撰写 1 段话的论文总结，涵盖：研究问题、提出的方法、主要实验结果]*\n")

    # ── 2. Strengths ──
    report.append("## 2. Strengths\n")

    strengths = []

    # 基于论断验证结果提取 Strengths
    novel_claims = [
        cr for cr in claim_results
        if cr.get("assessment", {}).get("category") == "strength"
    ]
    if novel_claims:
        top_novel = novel_claims[0]
        claim_short = top_novel["claim"][:120]
        strengths.append(
            f"**S1. 新颖性**：论文提出的核心方法/发现具有一定新颖性。"
            f"例如：\"{claim_short}\" — "
            f"{top_novel.get('assessment', {}).get('summary', '')}"
        )

    # 基于实验完整性检查
    exp_positives = []
    if experiment_check.get("has_baseline_comparison"):
        exp_positives.append("与基线方法进行了对比")
    if experiment_check.get("has_ablation_study"):
        exp_positives.append("包含消融实验")
    if experiment_check.get("has_statistical_test"):
        exp_positives.append("提供了统计检验/误差分析")
    if experiment_check.get("has_multiple_datasets"):
        exp_positives.append("在多个数据集上验证")
    if experiment_check.get("has_qualitative_analysis"):
        exp_positives.append("包含定性分析/案例展示")

    if len(exp_positives) >= 3:
        strengths.append(
            f"**S{len(strengths)+1}. 实验设计较为完善**："
            f"论文的实验部分{'、'.join(exp_positives)}，整体设计较为充分。"
        )
    elif len(exp_positives) >= 1:
        strengths.append(
            f"**S{len(strengths)+1}. 实验有一定基础**："
            f"论文{'、'.join(exp_positives)}。"
        )

    # 基于文献覆盖度
    coverage = literature_check.get("coverage_ratio", 0)
    if coverage >= 0.6:
        strengths.append(
            f"**S{len(strengths)+1}. 文献综述充分**："
            f"论文对领域重要文献的覆盖率为 {coverage:.0%}，相关工作讨论较为全面。"
        )

    # 基于论证逻辑
    well_supported = sum(1 for lr in logic_results if lr["support_level"] == "充分支撑")
    if logic_results and well_supported / len(logic_results) >= 0.6:
        strengths.append(
            f"**S{len(strengths)+1}. 论证逻辑清晰**："
            f"{well_supported}/{len(logic_results)} 条核心结论在实验部分有充分的数据支撑。"
        )

    # 基于段落结构
    expected_secs = ["abstract", "introduction", "method", "experiment", "conclusion"]
    found_secs = sum(
        1 for exp in expected_secs
        if any(exp in sec for sec in sections.keys())
    )
    if found_secs >= 4:
        strengths.append(
            f"**S{len(strengths)+1}. 论文结构规范**："
            f"段落结构完整，包含标准的各个章节。"
        )

    # 确保至少有 3 个 Strengths
    if len(strengths) < 3:
        strengths.append(
            f"**S{len(strengths)+1}. [待补充]**："
            f"*[请审稿人根据领域专业知识补充论文的其他优点]*"
        )
    if len(strengths) < 3:
        strengths.append(
            f"**S{len(strengths)+1}. [待补充]**："
            f"*[请审稿人根据领域专业知识补充论文的其他优点]*"
        )

    for s in strengths:
        report.append(f"- {s}")
    report.append("")

    # ── 3. Weaknesses ──
    report.append("## 3. Weaknesses\n")

    weaknesses = []

    # 基于论断验证结果提取 Weaknesses
    weak_claims = [
        cr for cr in claim_results
        if cr.get("assessment", {}).get("category") == "weakness"
    ]
    if weak_claims:
        for wc in weak_claims[:2]:
            claim_short = wc["claim"][:120]
            weaknesses.append(
                f"**W{len(weaknesses)+1}. 新颖性不足**："
                f"论断 \"{claim_short}\" 与已有工作高度重合 — "
                f"{wc.get('assessment', {}).get('summary', '')}。"
                f"建议作者明确阐述与已有工作的差异及增量贡献。"
            )

    # 基于实验缺失项
    missing_exp = experiment_check.get("missing_items", [])
    if missing_exp:
        missing_str = "；".join(missing_exp[:3])
        weaknesses.append(
            f"**W{len(weaknesses)+1}. 实验设计不完整**："
            f"{missing_str}。"
            f"这些缺失可能削弱论文结论的可信度。"
        )

    # 基于文献遗漏
    missing_papers = literature_check.get("missing_papers", [])
    if missing_papers:
        missing_titles = [mp["title"][:50] for mp in missing_papers[:3]]
        weaknesses.append(
            f"**W{len(weaknesses)+1}. 文献覆盖不足**："
            f"以下 {len(missing_papers)} 篇重要文献未被引用或讨论，"
            f"例如：{'; '.join(missing_titles)}。"
            f"建议作者在 Related Work 中补充讨论。"
        )

    # 基于论证逻辑
    weak_logic = [lr for lr in logic_results if lr["support_level"] == "支撑不足"]
    if weak_logic:
        weaknesses.append(
            f"**W{len(weaknesses)+1}. 部分结论缺少数据支撑**："
            f"{len(weak_logic)} 条结论在实验部分未找到充分的数据支撑。"
            f"例如：\"{weak_logic[0]['claim'][:80]}\"。"
            f"建议作者补充对应的实验数据或调整结论措辞。"
        )

    # 确保至少有 3 个 Weaknesses
    while len(weaknesses) < 3:
        weaknesses.append(
            f"**W{len(weaknesses)+1}. [待补充]**："
            f"*[请审稿人根据领域专业知识补充论文的不足之处]*"
        )

    for w in weaknesses:
        report.append(f"- {w}")
    report.append("")

    # ── 4. Questions for Authors ──
    report.append("## 4. Questions for Authors\n")

    questions = []

    # 基于论断验证中的 "question" 类别
    question_claims = [
        cr for cr in claim_results
        if cr.get("assessment", {}).get("category") == "question"
    ]
    for qc in question_claims[:3]:
        claim_short = qc["claim"][:100]
        questions.append(
            f"Q{len(questions)+1}. 关于论断 \"{claim_short}\"：能否与已有相关工作"
            f"（匹配分 {max(v.get('score', 0) for v in qc.get('variables', [{'score': 0}])):.2f}）"
            f"进行更详细的对比和讨论？"
        )

    # 基于实验缺失项生成问题
    if not experiment_check.get("has_ablation_study"):
        questions.append(
            f"Q{len(questions)+1}. 能否提供消融实验来验证各组件的独立贡献？"
        )
    if not experiment_check.get("has_statistical_test"):
        questions.append(
            f"Q{len(questions)+1}. 实验结果是否具有统计显著性？能否提供误差棒或置信区间？"
        )

    # 基于论证逻辑生成问题
    for wl in weak_logic[:2]:
        claim_short = wl["claim"][:80]
        questions.append(
            f"Q{len(questions)+1}. 关于 \"{claim_short}\"，能否提供更直接的实验数据来支撑这一结论？"
        )

    if not questions:
        questions.append(
            "Q1. *[请审稿人根据自身理解提出需要作者回答的关键问题]*"
        )

    for q in questions[:6]:
        report.append(f"- {q}")
    report.append("")

    # ── 5. Minor Comments ──
    report.append("## 5. Minor Comments\n")

    minor_comments = []

    # 基于段落完整性
    expected = {
        "abstract": "摘要 (Abstract)",
        "introduction": "引言 (Introduction)",
        "related": "相关工作 (Related Work)",
        "method": "方法 (Methods)",
        "experiment": "实验 (Experiments)",
        "conclusion": "结论 (Conclusion)",
    }
    for key, name in expected.items():
        found = any(key in sec for sec in sections.keys())
        if not found:
            minor_comments.append(
                f"M{len(minor_comments)+1}. 未检测到 {name} 段落（可能是段落命名不同），"
                f"建议使用标准段落命名以提高可读性。"
            )

    minor_comments.append(
        f"M{len(minor_comments)+1}. *[请审稿人补充格式、排版、拼写等小问题]*"
    )

    for mc in minor_comments[:8]:
        report.append(f"- {mc}")
    report.append("")

    # ── 6. Recommendation ──
    report.append("## 6. Recommendation\n")

    # 综合评估给出建议
    score_factors = {
        "novelty": 0,
        "experiments": 0,
        "literature": 0,
        "logic": 0,
    }

    # 新颖性
    novelty_strength_count = sum(
        1 for cr in claim_results
        if cr.get("assessment", {}).get("category") == "strength"
    )
    novelty_weakness_count = sum(
        1 for cr in claim_results
        if cr.get("assessment", {}).get("category") == "weakness"
    )
    if claim_results:
        score_factors["novelty"] = (
            novelty_strength_count - novelty_weakness_count * 2
        ) / len(claim_results)
    else:
        score_factors["novelty"] = 0

    # 实验
    exp_items = [
        experiment_check.get("has_baseline_comparison", False),
        experiment_check.get("has_ablation_study", False),
        experiment_check.get("has_statistical_test", False),
        experiment_check.get("has_multiple_datasets", False),
        experiment_check.get("has_qualitative_analysis", False),
    ]
    score_factors["experiments"] = sum(exp_items) / len(exp_items)

    # 文献覆盖
    score_factors["literature"] = literature_check.get("coverage_ratio", 0)

    # 论证逻辑
    if logic_results:
        well_supported_count = sum(
            1 for lr in logic_results if lr["support_level"] == "充分支撑"
        )
        score_factors["logic"] = well_supported_count / len(logic_results)

    # 加权总分
    overall = (
        score_factors["novelty"] * 0.35 +
        score_factors["experiments"] * 0.30 +
        score_factors["literature"] * 0.15 +
        score_factors["logic"] * 0.20
    )

    if overall >= 0.7:
        recommendation = "Accept / Minor Revision"
        recommendation_detail = (
            "论文在新颖性、实验设计和文献覆盖方面表现较好。建议小修后接收。"
        )
    elif overall >= 0.4:
        recommendation = "Major Revision"
        recommendation_detail = (
            "论文有一定贡献，但存在需要解决的重要问题。建议大修后重新提交。"
        )
    elif overall >= 0.2:
        recommendation = "Major Revision / Reject"
        recommendation_detail = (
            "论文存在较多不足，需要大幅改进。建议大修或考虑拒稿。"
        )
    else:
        recommendation = "Reject"
        recommendation_detail = (
            "论文在关键方面（新颖性/实验/文献）存在明显不足。建议拒稿。"
        )

    report.append(f"**建议**：{recommendation}\n")
    report.append(f"{recommendation_detail}\n")

    report.append("**各维度评估：**\n")
    report.append("| 维度 | 评估 | 说明 |")
    report.append("|------|------|------|")

    dim_labels = {
        "novelty": ("新颖性", "论文核心贡献的原创性"),
        "experiments": ("实验充分性", "实验设计的完整性和严谨性"),
        "literature": ("文献覆盖", "相关工作讨论的全面性"),
        "logic": ("论证逻辑", "结论与数据的对应关系"),
    }
    for dim, (label, desc) in dim_labels.items():
        val = score_factors[dim]
        if val >= 0.7:
            level = "良好"
        elif val >= 0.4:
            level = "一般"
        else:
            level = "不足"
        report.append(f"| {label} | {level} | {desc} |")

    report.append("")
    report.append("> **再次提醒**：以上建议仅供参考。最终评审意见应由审稿人根据专业知识和完整阅读全文后做出判断。")
    report.append("")

    # ── 附录：详细数据 ──
    report.append("---\n")
    report.append("## 附录：AI 分析详细数据\n")
    report.append("以下数据供审稿人在撰写最终意见时参考。\n")

    # 论断验证明细
    if claim_results:
        report.append("### A1. 论断验证明细\n")
        report.append("| # | 论断（截取） | 验证结果 | 审稿建议 |")
        report.append("|---|------------|---------|---------|")
        for i, cr in enumerate(claim_results):
            claim_short = cr["claim"][:80].replace("|", "\\|")
            assessment = cr.get("assessment", {})
            level = assessment.get("level", "未知")
            for_review = assessment.get("for_review", "").replace("|", "\\|")[:60]
            report.append(f"| {i+1} | {claim_short} | {level} | {for_review} |")
        report.append("")

    # 文献覆盖明细
    if missing_papers:
        report.append("### A2. 可能遗漏的重要文献\n")
        report.append("| # | 标题 | 期刊 | 年份 | 被引 | IF |")
        report.append("|---|------|------|------|------|-----|")
        for i, mp in enumerate(missing_papers[:10]):
            title = mp["title"][:50].replace("|", "\\|")
            journal = mp.get("journal", "N/A")[:20].replace("|", "\\|")
            report.append(
                f"| {i+1} | {title} | {journal} | "
                f"{mp.get('year', 'N/A')} | {mp['citations']} | {mp['impact_factor']} |"
            )
        report.append("")

    # 实验完整性明细
    report.append("### A3. 实验完整性检查\n")
    exp_items_display = {
        "基线对比实验": experiment_check.get("has_baseline_comparison"),
        "消融实验": experiment_check.get("has_ablation_study"),
        "统计检验/误差分析": experiment_check.get("has_statistical_test"),
        "多数据集验证": experiment_check.get("has_multiple_datasets"),
        "定性分析/案例展示": experiment_check.get("has_qualitative_analysis"),
    }
    report.append("| 检查项 | 状态 |")
    report.append("|--------|------|")
    for item, status in exp_items_display.items():
        icon = "通过" if status else "缺失"
        report.append(f"| {item} | {icon} |")
    report.append("")

    return "\n".join(report)


# ─── 主流程 ─────────────────────────────────────────────

def review_paper(pdf_url: str, review_standard: str = ""):
    """
    同行评议辅助主函数。

    参数：
        pdf_url: 待审论文 PDF 的 URL（建议使用可直接下载的链接）
        review_standard: 期刊/会议审稿标准名称（可选）
    """
    print("=" * 60)
    print("  同行评议辅助 (Review Assistant)")
    print(f"  论文：{pdf_url}")
    print(f"  审稿标准：{review_standard or '通用标准'}")
    print("=" * 60)

    # ── 步骤 1：PDF 全文解析 ──
    parse_result = parse_pdf(pdf_url)

    if parse_result["status"] != "success":
        error = parse_result.get("error", "未知错误")
        print(f"\nPDF 解析失败（{error}），无法继续评审。")
        print("可能的原因及解决方案：")
        print("  1. PDF URL 不可直接下载 → 请提供直链（如 arXiv PDF 链接）")
        print("  2. PDF 文件损坏或格式不支持 → 尝试其他版本")
        print("  3. 网络连接问题 → 检查网络后重试")
        return

    content = parse_result["content"]

    # 提取段落结构
    sections = extract_sections(content)
    print(f"\n识别到 {len(sections)} 个段落：{', '.join(sections.keys())}")

    # 提取核心论断
    claims = extract_claims(content, sections)
    print(f"提取到 {len(claims)} 条核心论断")

    # 提取关键术语和参考文献
    keywords = extract_reference_keywords(content, sections)
    referenced_works = extract_referenced_works(content)
    print(f"提取到 {len(keywords)} 个关键术语，{len(referenced_works)} 篇参考文献")

    # 检查实验完整性
    experiment_check = check_experiment_completeness(content, sections)
    print(f"实验完整性检查完成，缺失项：{len(experiment_check['missing_items'])} 项")

    # 检查论证逻辑链
    logic_results = check_logic_chain(claims, sections)

    # ── 步骤 2：文献覆盖度检查 ──
    literature_check = check_literature_coverage(keywords, referenced_works, content)

    # ── 步骤 3：核心论断验证 ──
    claim_results = verify_claims(claims)

    # ── 生成审稿意见 ──
    print("\n" + "=" * 60)
    print("  生成审稿意见框架...")
    print("=" * 60 + "\n")

    review = generate_review(
        pdf_url, review_standard, parse_result, sections, claims,
        claim_results, experiment_check, literature_check, logic_results
    )
    print(review)

    return review


# ─── 入口 ───────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python review_assistant.py <PDF_URL> [审稿标准]")
        print()
        print("示例：")
        print("  python review_assistant.py https://arxiv.org/pdf/2107.06922")
        print('  python review_assistant.py https://arxiv.org/pdf/2107.06922 "NeurIPS"')
        print('  python review_assistant.py https://arxiv.org/pdf/2301.12345 "Nature"')
        print('  python review_assistant.py https://arxiv.org/pdf/2301.12345 "ICLR 2026"')
        sys.exit(1)

    paper = sys.argv[1]
    standard = sys.argv[2] if len(sys.argv) > 2 else ""

    review_paper(paper, standard)
```

---

## curl 示例

以下展示各步骤的独立 curl 调用方式，便于调试和集成。

### 步骤 1：PDF 全文解析

```bash
# 提交解析任务
curl -X POST "https://open.bohrium.com/openapi/v1/parse/trigger-url-async" \
  -H "accessKey: $ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://arxiv.org/pdf/2107.06922",
    "sync": false,
    "textual": true,
    "table": true,
    "expression": true,
    "equation": true,
    "timeout": 1800
  }'

# 返回示例：{"token": "abc123", "code": 0}

# 查询解析结果
curl -X POST "https://open.bohrium.com/openapi/v1/parse/get-result" \
  -H "accessKey: $ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123",
    "content": true,
    "objects": false,
    "pages_dict": true
  }'
```

### 步骤 2：文献覆盖度检查

```bash
# 用关键词检索领域重要文献
curl -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "accessKey: $ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "words": ["Transformer", "Attention", "Self-Attention", "BERT"],
    "question": "key methods related to Transformer and Attention mechanisms",
    "type": 5,
    "jcrZones": ["Q1", "Q2"],
    "pageSize": 20
  }'
```

### 步骤 3：核心论断验证

```bash
# 验证单条论断
curl -X POST "https://open.bohrium.com/openapi/v1/lkm/claims/match" \
  -H "accessKey: $ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Our method outperforms all existing baselines on GLUE benchmark by 2.5 points",
    "limit": 5
  }'

# 返回示例：
# {
#   "data": {
#     "variables": [
#       {"id": "...", "content": "...", "score": 0.75, "role": "conclusion"},
#       ...
#     ],
#     "papers": {...},
#     "new_claim_likely": false
#   }
# }
```

---

## 各步骤详解

### 步骤 1：PDF 全文解析 (`pdf-parser`)

调用 `trigger-url-async` 提交 PDF 解析任务，异步轮询 `get-result` 获取结果。审稿需要解析**全文**，因为需要检查所有段落的完整性和论证链。

```python
# 审稿模式：解析全文，不设 pages 参数
payload = {
    "url": pdf_url,
    "sync": False,
    "textual": True,
    "table": True,
    "expression": True,
    "equation": True,
    "timeout": 1800
}
```

**解析结果用途：**

| 提取内容 | 用途 |
|---------|------|
| Abstract + Conclusion | 提取核心论断 → 步骤 3 论断验证 |
| Related Work + Introduction | 提取关键术语 → 步骤 2 文献覆盖度检查 |
| Experiments + Results | 检查实验完整性 → Strengths / Weaknesses |
| References | 提取已引文献列表 → 步骤 2 覆盖度比对 |
| 全文段落结构 | 评估写作质量 → Minor Comments |

---

### 步骤 2：文献覆盖度检查 (`paper-search`)

从论文中提取的关键术语出发，用 `paper-search` 检索领域重要文献（限定 Q1/Q2），然后与论文已引用的参考文献交叉比对，找出遗漏的重要相关工作。遗漏的文献会反映在 Weaknesses 和 Questions 中。

```python
r = requests.post(
    f"{BASE_PAPER}/rag/pass/keyword",
    headers=H_JSON,
    json={
        "words": keywords[:8],
        "question": question,
        "type": 5,
        "jcrZones": ["Q1", "Q2"],
        "pageSize": 20
    }
)
```

**覆盖度判定逻辑：**

- 对检索到的每篇高引论文，检查其标题关键词或 DOI 是否在论文全文中出现
- 未出现的高引论文（被引 > 20 或 IF > 3）标记为"可能遗漏"
- 覆盖率高 → 列入 Strengths；覆盖率低或遗漏多 → 列入 Weaknesses

---

### 步骤 3：核心论断验证 (`lkm claims/match`)

从论文中提取核心论断，逐条送入 LKM 验证。与 `pre-review` 侧重"评估审稿风险"不同，`review-assistant` 侧重**为审稿意见提供证据支撑**：哪些论断有文献基础（可作为 Strength 肯定），哪些与已有工作重合（应列入 Weakness 质疑）。

**验证结果到审稿意见的映射：**

| 验证结果 | 审稿意见映射 |
|---------|------------|
| `new_claim_likely=True` 或弱匹配 | → **Strength**（新颖性亮点） |
| 高分匹配 + `role=conclusion` | → **Weakness**（与已有工作重合） |
| 高分匹配 + `role=premise` | → **Strength**（基础扎实） |
| 中等匹配 | → **Question**（要求作者讨论差异） |

---

## 使用示例

### 评审一篇 arXiv 论文

```python
review_paper("https://arxiv.org/pdf/2107.06922")
```

### 按会议标准评审

```python
review_paper("https://arxiv.org/pdf/2301.12345", review_standard="NeurIPS")
```

### 按期刊标准评审

```python
review_paper("https://arxiv.org/pdf/2301.12345", review_standard="Nature")
```

### 命令行调用

```bash
# 基本评审
python review_assistant.py https://arxiv.org/pdf/2107.06922

# 指定审稿标准
python review_assistant.py https://arxiv.org/pdf/2107.06922 "NeurIPS"

# 指定期刊
python review_assistant.py https://arxiv.org/pdf/2301.12345 "Nature"
```

---

## 错误处理

| 场景 | 错误信息 | 处理方式 |
|------|---------|---------|
| ACCESS_KEY 未设置 | `未设置 ACCESS_KEY 环境变量` | 配置 `~/.openclaw/openclaw.json` |
| PDF URL 不可访问 | `提交失败` / `解析失败` | 检查 URL 是否为直链，尝试其他 PDF 源 |
| PDF 解析超时 | `解析任务未在 180 秒内完成` | 论文页数过多，检查 URL 后重试 |
| 论断提取为空 | `提取到 0 条核心论断` | 论文使用非标准表述，手动输入论断用 lkm 验证 |
| 文献检索失败 | `检索失败` | 检查网络或减少关键词数量后重试 |
| LKM 验证超时 | `验证失败：timeout` | 减少论断数量，分批验证 |

---

## 常见问题 (FAQ)

### Q1: review-assistant 和 pre-review 有什么区别？

| 维度 | review-assistant（本技能） | pre-review |
|------|--------------------------|------------|
| **使用者** | 审稿人（评审他人论文） | 作者（自查自己的论文） |
| **视角** | 审稿人视角：生成 Review 意见 | 审稿模拟：预测审稿人会提什么问题 |
| **输出格式** | Summary / Strengths / Weaknesses / Questions | 评分 + 改进优先级 |
| **侧重点** | 公正评价优缺点，提出建设性意见 | 找漏洞，给出修改建议 |

### Q2: 生成的审稿意见可以直接提交吗？

**不可以。** 本工具生成的是审稿意见的"框架"和"素材"，不是最终的审稿意见。审稿人必须：

1. 完整阅读论文全文
2. 基于自身专业知识审核和修改 AI 生成的内容
3. 补充 AI 无法覆盖的领域特定观点
4. 确保意见公正、准确、具有建设性

### Q3: AI 分析的新颖性判断准确吗？

LKM 的新颖性验证基于已有知识图谱，有以下局限：

- 知识图谱可能不覆盖最新发表的论文
- 术语差异可能导致漏检
- 跨学科创新可能未被充分匹配

因此，AI 的新颖性判断仅供参考，审稿人需结合领域经验做最终判断。

### Q4: 支持哪些审稿标准？

`review_standard` 参数目前仅用于审稿意见的上下文标注，不影响分析逻辑。未来计划针对不同期刊/会议的评审标准（如 NeurIPS 的 Checklist、Nature 的 Reporting Summary）进行适配。

### Q5: 如何确保审稿保密性？

- 论文 PDF 通过 Bohrium API 处理，不会存储或分享
- 建议使用 arXiv 等已公开的 PDF 链接
- 如果论文尚未公开，请确认使用 AI 辅助审稿符合您所在期刊/会议的保密政策

### Q6: 多长的论文可以处理？

pdf-parser 的异步模式可处理较长论文（timeout 设为 1800 秒）。实测通常：

- 10 页以内论文：30-60 秒解析
- 10-30 页论文：60-120 秒解析
- 30 页以上论文：可能需要 2-3 分钟

---

## 与其他技能的区别

| 技能 | 目标 | 视角 | 输出 |
|------|------|------|------|
| **review-assistant**（本技能） | 辅助同行评议 | 审稿人视角 | 结构化审稿意见框架 |
| `pre-review` | 投稿前自查 | 模拟审稿人 | 评分 + 改进优先级 |
| `paper-dissector` | 精读论文 | 读者视角 | 方法拆解 + 精读笔记 |
| `literature-review` | 领域文献综述 | 研究者视角 | 文献脉络 + 趋势分析 |

## 搭配使用

- **review-assistant** 发现文献遗漏 → **paper-search** 深入检索遗漏文献
- **review-assistant** 发现论断存疑 → **lkm** 深入追溯证据链
- **review-assistant** 对比竞争工作 → **paper-dissector** 精读已有相关论文
- **review-assistant** 不确定领域背景 → **literature-review** 快速了解领域现状
