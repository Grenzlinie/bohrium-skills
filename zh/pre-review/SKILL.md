---
name: pre-review
description: "Pre-submission review simulation combining PDF analysis, literature coverage check, and novelty verification. Use when: user wants to simulate peer review on their own manuscript before submission, check for weaknesses, or identify missing references. NOT for: reading/analyzing others' papers (use paper-dissector), general literature review (use literature-review)."
---

# SKILL: 审稿人视角预审 (Pre-Review)

## 概述

编排 `bohrium-pdf-parser`、`bohrium-paper-search`、`bohrium-lkm` 三个原子技能，以审稿人视角对自己的论文稿件进行投稿前预审。从 PDF 全文解析到新颖性验证、文献覆盖度检查，输出包含评分和改进优先级的结构化审稿意见。

**编排流程：**

```
自己的论文 PDF + 目标期刊/会议（可选）
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
│  lkm claims/match│  新颖性验证 → 类似方法/结论是否已有人发表？
└────────┬────────┘
         │
         ▼
   结构化审稿意见 + 评分 + 改进优先级
```

**适用场景：**

- 论文投稿前自查，模拟审稿人可能提出的问题
- 检查论文是否遗漏重要相关工作
- 验证核心创新点的新颖性（是否已有类似方法/结论）
- 评估实验设计的充分性（缺少哪些对比/消融实验）
- 检查论证逻辑链是否完整（结论是否有数据支撑）
- 获取写作改进建议（结构/清晰度/规范性）

**不适用：**

- 精读他人论文 → `paper-dissector`
- 跨多篇论文综述 → `literature-review`
- 仅需搜索论文 → `bohrium-paper-search`
- 仅需解析 PDF → `bohrium-pdf-parser`
- 仅需验证单个论断 → `bohrium-lkm`

## 认证配置

本技能复用底层三个原子技能共同的 ACCESS_KEY：

```json
"pre-review": {
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
| `paper` | string | 是 | 论文 PDF URL（建议 arXiv 直链或可下载链接） |
| `target_venue` | string | 否 | 目标期刊/会议名称（如 "Nature", "NeurIPS"），用于调整评审标准 |

## 输出结构

审稿意见包含以下六部分，模拟真实审稿流程：

1. **新颖性评估** — 核心创新点与已有工作的差异化程度
2. **实验充分性检查** — 是否缺少关键对比实验或消融实验
3. **文献覆盖度报告** — 遗漏的重要相关工作
4. **论证逻辑链检查** — 每个结论是否有充分的数据/实验支撑
5. **写作改进建议** — 结构、清晰度、规范性方面的改进点
6. **综合评分与改进优先级** — 按审稿评分标准给出整体评价和优先改进项

---

## 评审评分标准

模拟顶会/顶刊审稿评分体系：

| 维度 | 分值范围 | 评分依据 |
|------|---------|---------|
| 新颖性 (Novelty) | 1-10 | LKM 验证结果：new_claim_likely 比例、已有工作差异度 |
| 实验充分性 (Soundness) | 1-10 | 是否有足够对比实验、消融实验、统计检验 |
| 文献覆盖 (Related Work) | 1-10 | paper-search 检索到的高引论文中被引用的比例 |
| 论证逻辑 (Clarity) | 1-10 | 结论是否有对应实验数据支撑 |
| 写作质量 (Presentation) | 1-10 | 结构完整性、表述清晰度 |
| **综合评分** | **1-10** | **加权平均，新颖性和实验充分性权重最高** |

**综合评分解读：**

| 分数 | 对应审稿意见 | 建议 |
|------|-------------|------|
| 8-10 | Strong Accept | 稿件质量优秀，可直接投稿 |
| 6-7 | Weak Accept / Borderline | 有改进空间，修改后投稿 |
| 4-5 | Weak Reject | 存在明显不足，需要较大修改 |
| 1-3 | Strong Reject | 需要重大修改或重新设计实验 |

### 评审标准按目标期刊/会议适配

不同 venue 的评审侧重完全不同。当 `target_venue` 非空时，**必须**调整各维度权重和审查重点：

| 期刊/会议类型 | 新颖性权重 | 方法严谨性权重 | 影响力权重 | 特殊关注点 |
|---|---|---|---|---|
| **Nature/Science** | 35% | 25% | 25% | 跨学科影响力、独立验证、broader impact |
| **NeurIPS/ICML/ICLR** | 30% | 35% | 15% | 消融实验完整性、计算成本讨论、误差棒/置信区间 |
| **JACS/Angew** | 25% | 35% | 20% | 充分表征数据、反应机理讨论、对照实验 |
| **JCTC/JCP** | 20% | 40% | 20% | 方法严格推导、benchmark 全面性、数值稳定性 |
| **默认（未指定）** | 25% | 30% | 20% | 均衡评估 |

**按 venue 生成特定审稿问题**：

**NeurIPS/ICML/ICLR 类**：
- 是否有与 SOTA 的公平对比（相同数据集/划分/硬件）？
- 是否有消融实验验证每个组件的贡献？
- 是否讨论了计算成本和可扩展性？
- 是否有错误棒/置信区间（至少 3 次独立运行）？

**Nature/Science 类**：
- 核心发现是否有独立验证（不同方法/数据集确认同一结论）？
- 是否讨论了 broader impact 和潜在社会影响？
- 图片是否自解释（不看正文能否理解核心结果）？

**JACS/化学类**：
- 是否有充分的表征数据支撑结构确认？
- 是否讨论了反应机理或提出了合理假说？
- 是否有对照实验排除替代解释？

### 投稿定位建议（新增输出模块）

在审稿意见末尾，**必须**给出投稿定位建议：

1. **能投什么级别**：基于稿件当前质量，给出适合的期刊/会议级别范围
2. **差距分析**：如果目标 venue 级别高于稿件当前质量，明确指出"要投 X，还需要补充什么"
3. **替代选择**：推荐 2-3 个与稿件匹配度更高的同级或略低级别 venue

示例：
> **投稿定位**: 稿件当前质量适合 JCIM/Computational Chemistry 级别期刊（预估评分 6.5/10）。如目标为 NeurIPS，需补充：(1) 与 MACE/Equiformer 的公平对比; (2) 至少 3 个数据集的泛化验证; (3) 计算成本 vs 精度的 Pareto 分析。

---

## 数据质量控制（关键步骤）

文献覆盖度检查中，`paper-search` 返回的论文可能与稿件的具体任务和数据类型不匹配，**必须过滤出真正的基准竞争者（same task, same dataset type）才能做有意义的对比**。

### 过滤规则

```python
def filter_benchmark_competitors(papers, task_keywords, dataset_keywords, min_task_hits=1, min_dataset_hits=1):
    """
    只保留与稿件在同一任务和同类数据集上工作的论文作为基准竞争者。

    task_keywords: 稿件所解决的具体任务术语
    例如稿件做 "molecular force field prediction"
    task_keywords = ["force field", "interatomic potential", "energy prediction", "force prediction"]

    dataset_keywords: 稿件使用的数据集类型术语
    dataset_keywords = ["MD17", "ANI", "QM9", "rMD17", "molecular dynamics"]
    """
    competitors = []
    for p in papers:
        text = (p.get("enName", "") + " " + p.get("enAbstract", "")).lower()
        task_hits = sum(1 for k in task_keywords if k.lower() in text)
        data_hits = sum(1 for k in dataset_keywords if k.lower() in text)
        if task_hits >= min_task_hits and data_hits >= min_dataset_hits:
            competitors.append(p)
    return competitors
```

### 过滤后检查

- 如果过滤后 <3 篇基准竞争者：放宽数据集关键词匹配或扩展任务描述
- 如果过滤后全是非竞争者：在报告中明确标注「未找到直接可比的基准工作，以下覆盖度检查基于相关领域论文」
- **永远不要**将不同任务/不同数据类型的论文作为"遗漏的重要文献"报告给用户

---

## 报告分析深度要求

**预审报告不是 API 数据的格式化转储**。你是一个严格的审稿人，必须在报告中提供：

1. **具体指标对比**：与竞争论文在相同 benchmark 上的具体数值比较（MAE、RMSE、F1 等），不能只说"质量较好"
2. **新颖性差异的具体说明**：不能仅报告 `new_claim_likely=True/False`，必须指出与最相似已有工作的具体差异维度（方法、数据、场景、指标）
3. **可操作的改进建议**：每个不足点都必须附带具体的修改方案，不能只说"建议补充"
4. **审稿人视角的风险评估**：指出审稿人最可能质疑的 1-2 个核心问题

### 禁止的行为

- 用模糊的"质量评估"代替具体数据对比（如"实验较为充分"）
- 将不同任务的论文标记为"遗漏的重要文献"
- 给出脱离稿件内容的通用写作建议
- 对新颖性评估仅报告 LKM 的 True/False 标签而不解释含义

### 推荐的做法

- 具体指标对比："稿件在 MD17 上报告 MAE=0.5 kcal/mol，而 NequIP [ref] 报告 MAE=0.3 kcal/mol，需要解释差距原因"
- 精确新颖性分析："LKM 匹配到 SchNet (score=0.82, role=premise)，说明等变性方法的基础假设已有支撑，但本文的具体架构设计是新的"
- 可操作建议："建议在 Table 2 中增加 NequIP 和 MACE 的对比行，数据可从原始论文 Table 1 获取"
- 风险预警："审稿人可能质疑：为何未与 MACE (2023) 对比？该工作在相同 benchmark 上有更优结果"

---

## 完整编排脚本

以下 Python 脚本实现端到端的审稿人视角预审流程。

```python
#!/usr/bin/env python3
"""
审稿人视角预审 (Pre-Review)
编排 pdf-parser + paper-search + lkm，输出结构化审稿意见。
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
    print("请在 ~/.openclaw/openclaw.json 中配置 pre-review.env.ACCESS_KEY")
    sys.exit(1)

BASE_PARSE = "https://open.bohrium.com/openapi/v1/parse"
BASE_LKM   = "https://open.bohrium.com/openapi/v1/lkm"
BASE_PAPER = "https://open.bohrium.com/openapi/v1/paper"

H_JSON = {"accessKey": AK, "Content-Type": "application/json"}

# ─── 步骤 1：PDF 全文解析 ──────────────────────────────

def parse_pdf(pdf_url: str) -> dict:
    """
    调用 pdf-parser 解析论文 PDF 全文。
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
                # 找到下一个段落或文末
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

    # 优先从关键段落提取
    key_sections = ["abstract", "introduction", "conclusion", "results", "discussion"]
    key_text_parts = []
    for sec in key_sections:
        for sec_name, sec_text in sections.items():
            if sec in sec_name:
                key_text_parts.append(sec_text)

    combined = "\n".join(key_text_parts) if key_text_parts else text

    # 提取创新声明（"we propose", "we present", "we introduce" 等）
    novelty_patterns = [
        r'[^.]*(?:we\s+(?:propose|present|introduce|develop|design))\b[^.]+\.',
        r'[^.]*(?:our\s+(?:method|approach|framework|model|algorithm|system))\b[^.]+\.',
        r'[^.]*(?:novel|new|first|unique)\b[^.]*(?:approach|method|framework|model)\b[^.]+\.',
    ]

    # 提取实验结论（"show that", "demonstrate", "outperform" 等）
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

    return unique[:20]  # 最多 20 条


def extract_reference_keywords(text: str, sections: dict) -> list[str]:
    """
    从论文的 Related Work 和 Introduction 中提取关键方法名/模型名，
    用于后续 paper-search 检索比对。
    """
    keywords = set()

    # 优先从 Related Work 和 Introduction 提取
    target_text = ""
    for sec_name, sec_text in sections.items():
        if "related" in sec_name or "introduction" in sec_name or "background" in sec_name:
            target_text += sec_text + "\n"

    if not target_text:
        target_text = text[:5000]

    # 提取方法/模型名（大写字母开头的专有名词）
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

    # 提取引用中的作者名（如 "Zhang et al."）后面的方法描述
    method_after_cite = re.findall(
        r'(?:\[[\d,\s]+\]|\([\w\s,]+\d{4}\))\s*(?:proposed|introduced|developed|presented)\s+([^.]{10,80})',
        target_text, re.IGNORECASE
    )
    for m in method_after_cite:
        keywords.add(m.strip())

    return list(keywords)[:15]


def extract_referenced_works(text: str) -> list[str]:
    """
    从论文参考文献段落中提取被引用的论文标题，
    用于检查文献覆盖度。
    """
    refs = []
    # 尝试定位 References 段落
    ref_match = re.search(r'(?i)\\begin\{(?:section|subsection)\}\{references?\}', text)
    if not ref_match:
        ref_match = re.search(r'(?i)\breferences?\b\s*\n', text)

    if ref_match:
        ref_text = text[ref_match.start():]
        # 提取引用条目中的标题（通常在引号内或特定格式中）
        # 模式 1："Title in quotes"
        titles_quoted = re.findall(r'["“]([^"”]{20,200})["”]', ref_text)
        refs.extend(titles_quoted)

        # 模式 2：arXiv 引用中 "Title." 格式
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

    # 对比实验
    if re.search(r'(?i)(baseline|comparison|compared?\s+(?:to|with)|benchmark|state-of-the-art|SOTA)', exp_text):
        result["has_baseline_comparison"] = True
    else:
        result["missing_items"].append("缺少与基线方法的对比实验 (baseline comparison)")

    # 消融实验
    if re.search(r'(?i)(ablation|ablative|variant|without\s+\w+\s+module|w/o)', exp_text):
        result["has_ablation_study"] = True
    else:
        result["missing_items"].append("缺少消融实验 (ablation study)")

    # 统计检验
    if re.search(r'(?i)(p-value|t-test|significant|confidence\s+interval|standard\s+deviation|'
                 r'error\s+bar|mean\s*[±\+\-]|std|variance|ANOVA)', exp_text):
        result["has_statistical_test"] = True
    else:
        result["missing_items"].append("缺少统计检验或误差分析 (statistical test / error analysis)")

    # 多数据集
    dataset_mentions = re.findall(r'(?i)(dataset|benchmark|corpus)\b', exp_text)
    if len(dataset_mentions) >= 2:
        result["has_multiple_datasets"] = True
    else:
        result["missing_items"].append("仅在单一数据集上验证，建议增加多数据集实验")

    # 定性分析
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
        # 从结论中提取关键术语
        key_terms = re.findall(r'\b([A-Z][a-zA-Z]+|[a-z]+(?:tion|ment|ness|ity))\b', claim)
        key_terms = [t for t in key_terms if len(t) > 3][:5]

        # 检查这些术语是否在实验部分出现
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
                "jcrZones": ["Q1", "Q2"],
                "pageSize": 20
            },
            timeout=30
        )
        data = r.json()
    except Exception as e:
        print(f"  检索失败：{e}")
        return {"searched_papers": [], "missing_papers": [], "coverage_ratio": 0}

    # 处理可能的 streaming 响应
    if isinstance(data, str):
        data = json.loads(data.split('\n')[0])

    searched_papers = data.get("data", [])
    print(f"  检索到 {len(searched_papers)} 篇领域重要文献")

    # 检查覆盖度：每篇检索到的高引论文是否在参考文献中
    ref_text_lower = " ".join(referenced_works).lower()
    paper_text_lower = paper_text.lower()

    missing_papers = []
    covered_papers = []

    for p in searched_papers:
        title = p.get("enName", "")
        doi = p.get("doi", "")
        citations = p.get("citationNums", 0)
        authors = p.get("authors", "")

        # 判断是否已引用：标题关键词或 DOI 在全文中出现
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
            # 只标记高引论文为"遗漏"
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


# ─── 步骤 3：新颖性验证 ────────────────────────────────

def verify_novelty(claims: list[str]) -> list[dict]:
    """
    对每条核心创新声明调用 lkm claims/match，验证新颖性。
    """
    print(f"\n[步骤 3/3] 新颖性验证：共 {len(claims)} 条核心论断")
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
                "novelty_level": "未知"
            })
            continue

        variables = data.get("data", {}).get("variables", [])
        papers = data.get("data", {}).get("papers", {})
        new_claim_likely = data.get("data", {}).get("new_claim_likely", None)

        # 判断新颖性级别
        novelty = assess_novelty(claim, variables, new_claim_likely)
        print(f"    新颖性：{novelty['level']} — {novelty['summary']}")

        results.append({
            "claim": claim,
            "status": "verified",
            "variables": variables,
            "papers": papers,
            "new_claim_likely": new_claim_likely,
            "novelty_level": novelty["level"],
            "novelty_summary": novelty["summary"],
            "novelty_detail": novelty["detail"],
            "novelty_risk": novelty["risk"]
        })

    return results


def assess_novelty(claim: str, variables: list, new_claim_likely: bool) -> dict:
    """
    评估论断的新颖性级别。

    评估逻辑：
    - new_claim_likely = True + 无高分匹配 → 高新颖性（但需确认实验充分性）
    - 高分匹配到已有 conclusion → 低新颖性（类似结论已有人发表）
    - 高分匹配到 premise → 中等新颖性（基础假设有支撑，但结论可能是新的）
    - 弱匹配 → 较高新颖性（相关研究少）
    """
    if not variables:
        return {
            "level": "高新颖性（无匹配）",
            "summary": "知识图谱中未找到相关论断，可能是全新贡献",
            "detail": "未找到相似的已有工作，该创新点可能较为独特。但也可能是术语差异导致未匹配，"
                      "建议手动确认是否存在使用不同术语描述相同方法的已有工作。",
            "risk": "低风险（需确认无术语差异导致的漏检）"
        }

    top_score = max(v.get("score", 0) for v in variables)
    roles = [v.get("role", "") for v in variables]
    has_conclusion = "conclusion" in roles
    has_premise = "premise" in roles

    if new_claim_likely:
        return {
            "level": "高新颖性",
            "summary": f"LKM 判定为可能新发现（new_claim_likely=True），最高匹配分 {top_score:.2f}",
            "detail": "知识图谱中证据不足以支撑或反驳该论断。这是正面信号——"
                      "说明该创新点在已有文献中确实较少被报道。审稿人可能会重点关注实验设计的严谨性。",
            "risk": "低风险（审稿人关注实验严谨性）"
        }
    elif top_score > 0.8 and has_conclusion:
        return {
            "level": "低新颖性",
            "summary": f"高度匹配已有结论（score={top_score:.2f}），类似工作已有人发表",
            "detail": "匹配到高度相似的已有研究结论。审稿人可能认为新颖性不足。"
                      "建议：(1) 明确阐述与已有工作的差异；(2) 提供更强的实验证据证明改进。",
            "risk": "高风险（审稿人可能质疑新颖性）"
        }
    elif top_score > 0.8 and has_premise:
        return {
            "level": "中等新颖性",
            "summary": f"基础假设已有支撑（score={top_score:.2f}），但结论可能是新的",
            "detail": "匹配到的是前提假设而非结论，说明研究基础有文献支持但具体结论可能是新贡献。"
                      "建议在论文中明确引用这些前提工作，强调本文在此基础上的创新。",
            "risk": "中等风险（需引用前提工作并阐明差异）"
        }
    elif top_score > 0.5:
        return {
            "level": "中等新颖性",
            "summary": f"存在中等相关研究（score={top_score:.2f}），有差异但非全新",
            "detail": "存在相关但不完全一致的已有工作。"
                      "建议：在 Related Work 中讨论这些相关工作，明确阐述方法/条件上的差异。",
            "risk": "中等风险（需在论文中讨论差异）"
        }
    else:
        return {
            "level": "较高新颖性",
            "summary": f"仅有弱相关匹配（score={top_score:.2f}），该方向研究较少",
            "detail": "文献支撑较弱，该方向研究较少。这意味着较高的新颖性，"
                      "但审稿人可能因此更严格审视实验设计的可靠性。",
            "risk": "低风险（但审稿人可能更严格审查实验）"
        }


# ─── 评分与报告生成 ────────────────────────────────────

def compute_scores(
    novelty_results: list[dict],
    experiment_check: dict,
    literature_check: dict,
    logic_results: list[dict],
    sections: dict
) -> dict:
    """
    根据各项检查结果计算评审评分。
    """
    scores = {}

    # 1. 新颖性评分 (Novelty)
    if novelty_results:
        high_novelty = sum(
            1 for r in novelty_results
            if "高" in r.get("novelty_level", "")
        )
        medium_novelty = sum(
            1 for r in novelty_results
            if "中等" in r.get("novelty_level", "")
        )
        low_novelty = sum(
            1 for r in novelty_results
            if "低" in r.get("novelty_level", "")
        )
        total = len(novelty_results)
        novelty_score = min(10, max(1,
            round((high_novelty * 9 + medium_novelty * 6 + low_novelty * 3) / max(total, 1))
        ))
    else:
        novelty_score = 5  # 无法评估，给中间分
    scores["novelty"] = novelty_score

    # 2. 实验充分性评分 (Soundness)
    exp_items = [
        experiment_check.get("has_baseline_comparison", False),
        experiment_check.get("has_ablation_study", False),
        experiment_check.get("has_statistical_test", False),
        experiment_check.get("has_multiple_datasets", False),
        experiment_check.get("has_qualitative_analysis", False),
    ]
    soundness_score = min(10, max(1, round(sum(exp_items) / len(exp_items) * 10)))
    scores["soundness"] = soundness_score

    # 3. 文献覆盖评分 (Related Work)
    coverage = literature_check.get("coverage_ratio", 0)
    missing_count = len(literature_check.get("missing_papers", []))
    if coverage >= 0.7 and missing_count <= 2:
        related_score = 9
    elif coverage >= 0.5 and missing_count <= 5:
        related_score = 7
    elif coverage >= 0.3:
        related_score = 5
    else:
        related_score = 3
    scores["related_work"] = related_score

    # 4. 论证逻辑评分 (Clarity)
    if logic_results:
        well_supported = sum(
            1 for r in logic_results if r["support_level"] == "充分支撑"
        )
        clarity_score = min(10, max(1,
            round(well_supported / max(len(logic_results), 1) * 10)
        ))
    else:
        clarity_score = 5
    scores["clarity"] = clarity_score

    # 5. 写作质量评分 (Presentation)
    presentation_score = 5  # 基准分
    # 有完整的 Abstract、Introduction、Methods、Experiments、Conclusion
    expected_sections = ["abstract", "introduction", "method", "experiment", "conclusion"]
    found = sum(
        1 for exp in expected_sections
        if any(exp in sec for sec in sections.keys())
    )
    presentation_score = min(10, max(1, round(found / len(expected_sections) * 10)))
    scores["presentation"] = presentation_score

    # 综合评分（加权平均，新颖性和实验充分性权重最高）
    weights = {
        "novelty": 0.30,
        "soundness": 0.30,
        "related_work": 0.15,
        "clarity": 0.15,
        "presentation": 0.10,
    }
    overall = sum(scores[k] * weights[k] for k in weights)
    scores["overall"] = round(overall, 1)

    return scores


def score_to_decision(score: float) -> str:
    """将分数转换为审稿决定。"""
    if score >= 8:
        return "Strong Accept — 稿件质量优秀，可直接投稿"
    elif score >= 6:
        return "Weak Accept / Borderline — 有改进空间，修改后投稿"
    elif score >= 4:
        return "Weak Reject — 存在明显不足，需要较大修改"
    else:
        return "Strong Reject — 需要重大修改或重新设计实验"


def generate_review_report(
    pdf_url: str,
    target_venue: str,
    parse_result: dict,
    sections: dict,
    novelty_results: list[dict],
    experiment_check: dict,
    literature_check: dict,
    logic_results: list[dict],
    scores: dict
) -> str:
    """
    汇总所有分析结果，生成结构化审稿意见报告（Markdown 格式）。
    """
    report = []
    report.append("# 审稿人视角预审报告\n")
    report.append(f"**论文 PDF**：{pdf_url}")
    report.append(f"**目标期刊/会议**：{target_venue or '未指定'}")
    report.append(f"**总页数**：{parse_result.get('total_page', 'N/A')}")
    report.append(f"**论文语言**：{parse_result.get('lang', 'unknown')}\n")

    # ── 综合评分 ──
    report.append("## 综合评分\n")
    report.append(f"**综合评分：{scores['overall']}/10 — {score_to_decision(scores['overall'])}**\n")
    report.append("| 维度 | 评分 | 说明 |")
    report.append("|------|------|------|")
    dimension_names = {
        "novelty": "新颖性 (Novelty)",
        "soundness": "实验充分性 (Soundness)",
        "related_work": "文献覆盖 (Related Work)",
        "clarity": "论证逻辑 (Clarity)",
        "presentation": "写作质量 (Presentation)",
    }
    for dim, name in dimension_names.items():
        s = scores[dim]
        if s >= 8:
            level = "优秀"
        elif s >= 6:
            level = "良好"
        elif s >= 4:
            level = "一般"
        else:
            level = "不足"
        report.append(f"| {name} | {s}/10 | {level} |")
    report.append("")

    # ── 1. 新颖性评估 ──
    report.append("## 1. 新颖性评估\n")
    if novelty_results:
        # 按新颖性分级统计
        levels = [r.get("novelty_level", "未知") for r in novelty_results]
        high_count = sum(1 for l in levels if "高" in l)
        med_count = sum(1 for l in levels if "中等" in l)
        low_count = sum(1 for l in levels if "低" in l)

        report.append(f"共验证 {len(novelty_results)} 条核心论断：")
        report.append(f"高新颖性 {high_count} 条 / 中等新颖性 {med_count} 条 / "
                      f"低新颖性 {low_count} 条\n")

        report.append("| # | 论断（截取） | 新颖性 | 风险 | 建议 |")
        report.append("|---|------------|--------|------|------|")
        for i, r in enumerate(novelty_results):
            claim_short = r["claim"][:80].replace("|", "\\|")
            level = r.get("novelty_level", "未知")
            risk = r.get("novelty_risk", "").replace("|", "\\|")
            detail = r.get("novelty_detail", "")[:60].replace("|", "\\|")
            report.append(f"| {i+1} | {claim_short} | {level} | {risk} | {detail} |")

        report.append("")

        # 对低新颖性条目给出具体改进建议
        low_novelty_items = [r for r in novelty_results if "低" in r.get("novelty_level", "")]
        if low_novelty_items:
            report.append("### 新颖性不足的论断需重点改进\n")
            for r in low_novelty_items:
                report.append(f"- **论断**：{r['claim'][:120]}")
                report.append(f"  - **问题**：{r['novelty_summary']}")
                report.append(f"  - **建议**：{r['novelty_detail']}")
                # 列出匹配到的已有工作
                if r.get("variables"):
                    report.append(f"  - **已有类似工作**：")
                    for v in r["variables"][:3]:
                        content = v.get("content", "")[:100].replace("|", "\\|")
                        score = v.get("score", 0)
                        report.append(f"    - (score={score:.2f}) {content}")
            report.append("")
    else:
        report.append("未能提取到可验证的核心论断。\n")

    # ── 2. 实验充分性检查 ──
    report.append("## 2. 实验充分性检查\n")
    exp_items = {
        "基线对比实验 (Baseline Comparison)": experiment_check.get("has_baseline_comparison"),
        "消融实验 (Ablation Study)": experiment_check.get("has_ablation_study"),
        "统计检验/误差分析 (Statistical Test)": experiment_check.get("has_statistical_test"),
        "多数据集验证 (Multiple Datasets)": experiment_check.get("has_multiple_datasets"),
        "定性分析/案例展示 (Qualitative Analysis)": experiment_check.get("has_qualitative_analysis"),
    }

    report.append("| 检查项 | 状态 |")
    report.append("|--------|------|")
    for item, status in exp_items.items():
        icon = "通过" if status else "缺失"
        report.append(f"| {item} | {icon} |")
    report.append("")

    missing = experiment_check.get("missing_items", [])
    if missing:
        report.append("### 审稿人可能提出的问题\n")
        for m in missing:
            report.append(f"- {m}")
        report.append("")
        report.append("**改进建议**：补充上述缺失的实验，尤其是消融实验和统计检验，"
                      "这是审稿人最常要求补充的内容。\n")

    # ── 3. 文献覆盖度报告 ──
    report.append("## 3. 文献覆盖度报告\n")
    coverage = literature_check.get("coverage_ratio", 0)
    report.append(f"**覆盖率**：{coverage:.0%}（已引用的领域重要文献占比）\n")

    missing_papers = literature_check.get("missing_papers", [])
    if missing_papers:
        report.append("### 可能遗漏的重要文献\n")
        report.append("以下高引/高影响因子文献未在论文中被引用，审稿人可能要求补充：\n")
        report.append("| # | 标题 | 期刊 | 年份 | 被引次数 | 影响因子 |")
        report.append("|---|------|------|------|---------|---------|")
        for i, mp in enumerate(missing_papers[:10]):
            title = mp["title"][:50].replace("|", "\\|")
            journal = mp.get("journal", "N/A")[:20].replace("|", "\\|")
            report.append(
                f"| {i+1} | {title} | {journal} | "
                f"{mp.get('year', 'N/A')} | {mp['citations']} | {mp['impact_factor']} |"
            )
        report.append("")
        report.append("**改进建议**：在 Related Work 部分补充讨论上述遗漏文献，"
                      "特别是高引用的奠基性工作。\n")
    else:
        report.append("文献覆盖较为完整，未发现明显遗漏的重要文献。\n")

    # ── 4. 论证逻辑链检查 ──
    report.append("## 4. 论证逻辑链检查\n")
    if logic_results:
        report.append("| # | 结论（截取） | 支撑程度 | 覆盖率 |")
        report.append("|---|------------|---------|--------|")
        for i, lr in enumerate(logic_results):
            claim_short = lr["claim"][:80].replace("|", "\\|")
            report.append(
                f"| {i+1} | {claim_short} | {lr['support_level']} | "
                f"{lr['coverage']:.0%} |"
            )
        report.append("")

        weak_logic = [lr for lr in logic_results if lr["support_level"] == "支撑不足"]
        if weak_logic:
            report.append("### 支撑不足的结论\n")
            report.append("以下结论在实验部分未找到充分的数据支撑，审稿人可能质疑：\n")
            for lr in weak_logic:
                report.append(f"- **结论**：{lr['claim'][:120]}")
                report.append(f"  - **建议**：补充对应的实验数据或修改结论措辞")
            report.append("")
    else:
        report.append("未能提取到可检查的论证链。\n")

    # ── 5. 写作改进建议 ──
    report.append("## 5. 写作改进建议\n")

    # 检查段落完整性
    expected = {
        "abstract": "摘要 (Abstract)",
        "introduction": "引言 (Introduction)",
        "related": "相关工作 (Related Work)",
        "method": "方法 (Methods)",
        "experiment": "实验 (Experiments)",
        "result": "结果 (Results)",
        "conclusion": "结论 (Conclusion)",
    }
    found_sections = set()
    for sec_name in sections.keys():
        for key in expected:
            if key in sec_name:
                found_sections.add(key)

    missing_secs = [
        name for key, name in expected.items()
        if key not in found_sections
    ]

    if missing_secs:
        report.append("### 结构完整性\n")
        report.append("以下标准段落未检测到（可能是段落命名不同或确实缺失）：\n")
        for ms in missing_secs:
            report.append(f"- {ms}")
        report.append("")

    report.append("### 通用写作建议\n")
    report.append("- 确保每个实验结论都有对应的数据表格或图表支撑")
    report.append("- Abstract 应包含：问题、方法、关键结果、影响")
    report.append("- Introduction 末尾应有清晰的贡献列表（contributions）")
    report.append("- Related Work 应明确说明本文与每个相关工作的差异")
    report.append("- 实验部分应说明超参数选择的依据")
    report.append("- Conclusion 不应引入 Abstract 中未提及的新内容\n")

    # ── 6. 改进优先级 ──
    report.append("## 6. 改进优先级\n")

    priorities = []

    # 按严重程度排序改进项
    if any("低" in r.get("novelty_level", "") for r in novelty_results):
        priorities.append({
            "priority": "P0 — 紧急",
            "item": "新颖性不足",
            "action": "明确阐述与已有工作的差异，补充更强的实验证据证明改进"
        })

    if missing:
        for m in missing[:3]:
            priorities.append({
                "priority": "P1 — 高优先级",
                "item": "实验不完整",
                "action": m
            })

    if missing_papers:
        priorities.append({
            "priority": "P1 — 高优先级",
            "item": "文献覆盖不足",
            "action": f"补充引用 {len(missing_papers)} 篇重要文献，"
                      f"在 Related Work 中讨论其与本文的关系"
        })

    weak_logic_items = [lr for lr in logic_results if lr["support_level"] == "支撑不足"]
    if weak_logic_items:
        priorities.append({
            "priority": "P2 — 中优先级",
            "item": "论证逻辑薄弱",
            "action": f"为 {len(weak_logic_items)} 个支撑不足的结论补充实验数据"
        })

    if missing_secs:
        priorities.append({
            "priority": "P3 — 低优先级",
            "item": "段落结构不完整",
            "action": f"补充缺失的段落：{', '.join(missing_secs)}"
        })

    if priorities:
        report.append("| 优先级 | 改进项 | 具体行动 |")
        report.append("|--------|--------|---------|")
        for p in priorities:
            report.append(f"| {p['priority']} | {p['item']} | {p['action'][:80]} |")
    else:
        report.append("未发现需要紧急改进的问题，稿件质量较好。")

    report.append("")
    return "\n".join(report)


# ─── 主流程 ─────────────────────────────────────────────

def pre_review(pdf_url: str, target_venue: str = ""):
    """
    审稿人视角预审主函数。

    参数：
        pdf_url: 论文 PDF 的 URL（建议使用可直接下载的链接）
        target_venue: 目标期刊/会议名称（可选）
    """
    print("=" * 60)
    print("  审稿人视角预审 (Pre-Review)")
    print(f"  论文：{pdf_url}")
    print(f"  目标：{target_venue or '未指定'}")
    print("=" * 60)

    # ── 步骤 1：PDF 全文解析 ──
    parse_result = parse_pdf(pdf_url)

    if parse_result["status"] != "success":
        error = parse_result.get("error", "未知错误")
        print(f"\nPDF 解析失败（{error}），无法继续预审。")
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

    # ── 步骤 3：新颖性验证 ──
    novelty_results = verify_novelty(claims)

    # ── 计算评分 ──
    scores = compute_scores(
        novelty_results, experiment_check, literature_check,
        logic_results, sections
    )

    # ── 生成报告 ──
    print("\n" + "=" * 60)
    print("  生成审稿意见报告...")
    print("=" * 60 + "\n")

    report = generate_review_report(
        pdf_url, target_venue, parse_result, sections,
        novelty_results, experiment_check, literature_check,
        logic_results, scores
    )
    print(report)

    return report


# ─── 入口 ───────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python pre_review.py <PDF_URL> [目标期刊/会议]")
        print()
        print("示例：")
        print("  python pre_review.py https://arxiv.org/pdf/2107.06922")
        print('  python pre_review.py https://arxiv.org/pdf/2107.06922 "NeurIPS 2026"')
        print('  python pre_review.py https://arxiv.org/pdf/2301.12345 "Nature"')
        sys.exit(1)

    paper = sys.argv[1]
    venue = sys.argv[2] if len(sys.argv) > 2 else ""

    pre_review(paper, venue)
```

---

## 各步骤详解

### 步骤 1：PDF 全文解析 (`pdf-parser`)

调用 `trigger-url-async` 提交 PDF 解析任务，异步轮询 `get-result` 获取结果。与 `paper-dissector` 不同，预审需要解析**全文**（不限制页数），因为需要检查 Related Work、Experiments、References 等各个段落的完整性。

```python
# 预审模式：解析全文，不设 pages 参数
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
| Abstract + Conclusion | 提取核心论断 → 步骤 3 新颖性验证 |
| Related Work + Introduction | 提取关键术语 → 步骤 2 文献覆盖度检查 |
| Experiments + Results | 检查实验完整性（对比/消融/统计） |
| References | 提取已引文献列表 → 步骤 2 覆盖度比对 |
| 全文段落结构 | 评估写作质量和结构完整性 |

---

### 步骤 2：文献覆盖度检查 (`paper-search`)

从论文中提取的关键术语出发，用 `paper-search` 检索领域重要文献（限定 Q1/Q2 高影响力论文），然后与论文已引用的参考文献交叉比对，找出遗漏的重要相关工作。

```python
# 检索领域重要文献（限定 Q1/Q2）
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
- 计算覆盖率 = 已引用数 / 检索总数

---

### 步骤 3：新颖性验证 (`lkm claims/match`)

从论文中提取的核心创新声明和实验结论，逐条送入 LKM 进行新颖性验证。与 `paper-dissector` 侧重"验证论断可信度"不同，预审侧重**评估审稿人是否会质疑新颖性**。

```python
# 提取创新声明
novelty_patterns = [
    r'[^.]*(?:we\s+(?:propose|present|introduce|develop|design))\b[^.]+\.',
    r'[^.]*(?:novel|new|first|unique)\b[^.]*(?:approach|method)\b[^.]+\.',
]

# 提取实验结论
result_patterns = [
    r'[^.]*(?:outperform|surpass|exceed)\b[^.]+\.',
    r'[^.]*(?:achieve)\s+(?:state-of-the-art|SOTA|best|superior)\b[^.]+\.',
]
```

**新颖性评估分级：**

```
高新颖性（new_claim_likely=True 或 score < 0.5）
  → 审稿风险：低
  → 但审稿人可能更严格审查实验设计

中等新颖性（score 0.5-0.8 或匹配到 premise）
  → 审稿风险：中等
  → 需在论文中明确讨论差异

低新颖性（score > 0.8 且匹配到 conclusion）
  → 审稿风险：高
  → 审稿人可能直接拒稿（novelty 不足）
  → 必须阐明与已有工作的差异、证明改进
```

---

## 使用示例

### 对 arXiv 论文进行预审

```python
pre_review("https://arxiv.org/pdf/2107.06922")
```

### 指定目标会议进行预审

```python
pre_review("https://arxiv.org/pdf/2301.12345", target_venue="NeurIPS 2026")
```

### 命令行调用

```bash
# 基本预审
python pre_review.py https://arxiv.org/pdf/2107.06922

# 指定目标期刊
python pre_review.py https://arxiv.org/pdf/2107.06922 "Nature"
```

---

## 错误处理

| 场景 | 错误信息 | 处理方式 |
|------|---------|---------|
| ACCESS_KEY 未设置 | `未设置 ACCESS_KEY 环境变量` | 配置 `~/.openclaw/openclaw.json` |
| PDF URL 不可访问 | `提交失败` / `解析失败` | 检查 URL 是否为直链，尝试其他 PDF 源 |
| PDF 解析超时 | `解析任务未在 180 秒内完成` | 论文页数过多，尝试缩短论文或分段处理 |
| 论断提取为空 | `未能提取到可验证的核心论断` | 论文使用非标准表述，手动输入论断用 lkm 验证 |
| 文献检索失败 | `检索失败` | 检查网络或减少关键词数量后重试 |
| LKM 验证超时 | `验证失败：timeout` | 减少论断数量，分批验证 |

---

## 与其他技能的区别

| 技能 | 目标 | 视角 |
|------|------|------|
| **pre-review**（本技能） | 投稿前自查 | 审稿人视角：找漏洞、评新颖性 |
| `paper-dissector` | 精读他人论文 | 读者视角：理解方法、拆解逻辑 |
| `literature-review` | 领域文献综述 | 研究者视角：梳理脉络、发现趋势 |

## 搭配使用

- **pre-review** 发现文献遗漏 → **paper-search** 检索并阅读遗漏文献
- **pre-review** 发现新颖性不足 → **lkm** 深入对比已有工作的证据链
- **pre-review** 完成后 → **paper-dissector** 精读审稿意见中提到的竞争论文
- **pre-review** 输出改进建议 → 修改论文后再次 **pre-review** 验证改进效果
