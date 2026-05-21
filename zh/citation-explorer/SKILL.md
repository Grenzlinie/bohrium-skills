---
name: citation-explorer
description: "Citation network exploration combining PDF parsing, paper search, and knowledge graph to trace academic lineage. Use when: user wants to understand the citation context of a paper, find intellectual ancestors or descendants. NOT for: general paper search (use bohrium-paper-search), single paper analysis (use paper-dissector)."
---

# SKILL: 引用网络探索 (Citation Explorer)

## 概述

引用网络探索是一个**编排型 Skill**，串联 `bohrium-pdf-parser`、`bohrium-paper-search`、`bohrium-lkm` 三个原子技能，从一篇种子论文出发，沿引用链向前（被谁引用）和向后（引用了谁）追溯学术传承关系，构建多跳引用网络并标注每个节点的角色（开创性工作/方法改进/应用拓展）。

**编排流程：**

```
种子论文（DOI / 标题 / PDF URL）
        │
        ▼
┌─────────────────┐
│  pdf-parser      │  解析种子论文 → 提取参考文献列表
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  paper-search    │  检索被引论文（forward）+ 参考文献（backward）
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  lkm search      │  分析概念继承关系 → 标注节点角色
└────────┬────────┘
         │
         ▼
   引用网络谱系报告
```

**适用场景：**

- 从一篇论文出发，追溯其学术传承脉络
- 理解某个方法/理论的演化路径（从开创到改进到应用）
- 发现引用网络中被低估的重要节点（高桥接度但低引用的论文）
- 为文献综述构建引用骨架

**不适用：**

- 通用论文搜索 → `bohrium-paper-search`
- 单篇论文深度拆解 → `paper-dissector`
- 多篇论文综述 → `literature-review`
- 仅需提取 PDF 文本 → `bohrium-pdf-parser`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

本技能复用底层三个原子技能共同的 ACCESS_KEY：

```json
"citation-explorer": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

---

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `seed` | string | 是 | — | 种子论文：DOI、标题、或 PDF URL |
| `direction` | string | 否 | `"both"` | 探索方向：`"forward"`（被引方向）、`"backward"`（参考文献方向）、`"both"`（双向） |
| `depth` | int | 否 | `1` | 探索跳数：1-3 跳。1 跳 = 种子论文的直接引用/被引；2 跳 = 再追一层；3 跳 = 最大深度 |

**深度与规模对照：**

| 深度 | 典型节点数 | 典型耗时 | 适用场景 |
|------|-----------|---------|---------|
| 1 跳 | 10-30 | 1-3 分钟 | 快速了解直接引用关系 |
| 2 跳 | 30-100 | 3-8 分钟 | 追溯方法演化路径 |
| 3 跳 | 100-300 | 8-15 分钟 | 构建完整学术谱系 |

---

## 输出结构

引用网络谱系报告包含以下四部分：

### 1. 引用谱系描述

关键传承路径的叙述，标注从开创性工作到当前种子论文的方法/思想演化链。

### 2. 节点论文标注

每个节点论文的角色分类：

| 角色 | 说明 | 识别依据 |
|------|------|----------|
| 开创性工作 (Pioneering) | 首次提出核心概念/方法 | 高引用、早期发表、LKM 中无更早的同概念节点 |
| 方法改进 (Method-Improvement) | 对已有方法的优化或变体 | 引用开创性工作、LKM 概念相似但有差异 |
| 应用拓展 (Application-Extension) | 将方法应用到新领域/新场景 | 引用方法论文、但研究领域不同 |

### 3. 推荐跟进阅读

被低估的重要节点：高桥接度（连接不同子领域）但引用数不突出的论文，这些论文往往是方法迁移的关键桥梁。

### 4. 网络统计

节点总数、边总数、核心传承路径长度、时间跨度等。

---

## 报告质量控制

### 节点角色标注的准确性

- **开创性工作**的判定不能仅依赖"高引用+早期发表"——必须通过 LKM 验证该概念在知识图谱中是否确实无更早的同义节点
- **方法改进**与**应用拓展**的区别必须明确：前者改进了核心算法/理论，后者只是迁移到新领域
- 如果无法确定角色，标注为"待确认"并说明原因，**不要猜测**

### 时效性覆盖

引用谱系分析必须覆盖完整时间跨度：
- **上游方向（backward）**：必须追溯到该领域的奠基工作，不能只找近 5 年的引用源
- **下游方向（forward）**：必须包含 2024-2025 年的最新引用者（如有），以反映当前发展方向
- 如果检索结果在某个时间段出现断层，需在报告中说明

### 定量声明溯源

网络统计中的所有数字必须可追溯：
- ✅ "核心传承路径包含 8 个节点，时间跨度 2005-2024"（基于检索到的具体论文列出）
- ❌ "该方法被引用超过 1000 次"（未标注来源和时间点）

### 禁止的行为

- ❌ 将仅标题相似但实际无引用关系的论文标为同一传承链
- ❌ 网络图中只有高引论文而遗漏"桥梁论文"（低引但连接两个子领域的关键工作）
- ❌ 推荐跟进阅读不说明理由

---

## 工作流程图

```
输入: seed, direction, depth
        │
        ▼
┌──────────────────────────────────────┐
│  步骤 1: 种子论文解析                  │
│  ├─ 输入为 PDF URL → pdf-parser 解析  │
│  ├─ 输入为 DOI → 转 PDF URL → 解析    │
│  └─ 输入为标题 → paper-search 定位    │
│  → 提取参考文献列表（backward 种子）   │
│  → 提取关键术语（forward 搜索词）      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 2: 多跳引用网络扩展              │
│  FOR hop = 1 TO depth:               │
│    backward: paper-search 检索参考文献 │
│    forward:  paper-search 检索施引论文 │
│    → 去重合并到引用网络                │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 3: 概念继承分析                  │
│  POST /v1/lkm/search                │
│  → 查询每条边的概念关系               │
│  → 判断继承类型（开创/改进/应用）      │
│  → 标注关键传承路径                   │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  步骤 4: 报告生成                     │
│  → 引用谱系描述                      │
│  → 节点标注（开创/改进/应用）         │
│  → 推荐跟进阅读                      │
│  → 网络统计                          │
└──────────────────────────────────────┘
```

---

## 完整编排脚本

以下 Python 脚本实现端到端的引用网络探索流程。

```python
#!/usr/bin/env python3
"""
引用网络探索 (Citation Explorer)
编排 pdf-parser + paper-search + lkm，追溯学术传承谱系。
"""

import os
import re
import sys
import json
import time
import requests
from datetime import datetime

# ─── 配置 ───────────────────────────────────────────────

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误：未设置 ACCESS_KEY 环境变量。")
    print("请在 ~/.openclaw/openclaw.json 中配置 citation-explorer.env.ACCESS_KEY")
    sys.exit(1)

BASE_PARSE = "https://open.bohrium.com/openapi/v1/parse"
BASE_LKM   = "https://open.bohrium.com/openapi/v1/lkm"
BASE_PAPER = "https://open.bohrium.com/openapi/v1/paper"

H_JSON = {"accessKey": AK, "Content-Type": "application/json"}
H_AK   = {"accessKey": AK}

# ─── 数据结构 ─────────────────────────────────────────────

class PaperNode:
    """引用网络中的论文节点。"""
    def __init__(self, doi="", title="", year="", journal="",
                 citations=0, impact_factor=0, abstract=""):
        self.doi = doi
        self.title = title
        self.year = year
        self.journal = journal
        self.citations = citations
        self.impact_factor = impact_factor
        self.abstract = abstract
        self.role = ""           # pioneering / method-improvement / application-extension
        self.role_reason = ""
        self.hop = 0             # 距离种子论文的跳数
        self.backward_refs = []  # 该论文引用的 DOI 列表
        self.forward_refs = []   # 引用该论文的 DOI 列表

    def to_dict(self):
        return {
            "doi": self.doi,
            "title": self.title,
            "year": self.year,
            "journal": self.journal,
            "citations": self.citations,
            "impact_factor": self.impact_factor,
            "role": self.role,
            "role_reason": self.role_reason,
            "hop": self.hop
        }


class CitationNetwork:
    """引用网络图。"""
    def __init__(self):
        self.nodes = {}   # doi -> PaperNode
        self.edges = []   # (from_doi, to_doi, direction)

    def add_node(self, node: PaperNode):
        if node.doi and node.doi not in self.nodes:
            self.nodes[node.doi] = node

    def add_edge(self, from_doi: str, to_doi: str, direction: str):
        edge = (from_doi, to_doi, direction)
        if edge not in self.edges:
            self.edges.append(edge)

    def get_node(self, doi: str) -> PaperNode:
        return self.nodes.get(doi)

    def stats(self) -> dict:
        years = [n.year for n in self.nodes.values() if n.year]
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "year_range": f"{min(years)}–{max(years)}" if years else "N/A",
            "pioneering_count": sum(
                1 for n in self.nodes.values() if n.role == "pioneering"
            ),
            "improvement_count": sum(
                1 for n in self.nodes.values() if n.role == "method-improvement"
            ),
            "extension_count": sum(
                1 for n in self.nodes.values() if n.role == "application-extension"
            ),
        }


# ─── 工具函数 ─────────────────────────────────────────────

def doi_to_pdf_url(doi: str) -> str:
    """尝试将 DOI 转换为可下载的 PDF URL。"""
    if doi.startswith("10.48550/arxiv."):
        arxiv_id = doi.replace("10.48550/arxiv.", "")
        return f"https://arxiv.org/pdf/{arxiv_id}"
    if "arxiv.org" in doi:
        return doi if doi.endswith(".pdf") else doi + ".pdf"
    return f"https://doi.org/{doi}"


def extract_references_from_text(text: str) -> list[str]:
    """
    从 pdf-parser 解析文本中提取参考文献信息。
    返回提取到的引用关键词列表（用于后续 paper-search）。
    """
    references = []

    # 策略 1：匹配 DOI 模式
    doi_pattern = r'10\.\d{4,9}/[^\s,;}\])]+'
    dois = re.findall(doi_pattern, text)
    for d in dois:
        # 清理尾部标点
        d = d.rstrip(".")
        references.append(d)

    # 策略 2：匹配引用上下文中的作者-年份模式，如 "Smith et al., 2020"
    author_year_pattern = r'([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*(?:19|20)\d{2})'
    author_years = re.findall(author_year_pattern, text)
    for ay in author_years:
        references.append(ay.strip())

    # 策略 3：从 References/Bibliography 段落提取标题
    ref_section = re.search(
        r'(?i)(?:references|bibliography)\s*\n(.*?)(?:\n\s*\n|\Z)',
        text, re.DOTALL
    )
    if ref_section:
        ref_text = ref_section.group(1)
        # 匹配引号中的标题或首字母大写的长短语
        titles = re.findall(r'"([^"]{20,150})"', ref_text)
        references.extend(titles[:20])

    # 去重
    seen = set()
    unique = []
    for r in references:
        if r.lower() not in seen:
            seen.add(r.lower())
            unique.append(r)

    return unique


def extract_key_concepts(text: str) -> list[str]:
    """从论文文本中提取关键概念术语，用于 forward 搜索。"""
    concepts = set()

    # 匹配方法/模型名
    method_names = re.findall(
        r'\b([A-Z][a-zA-Z]*(?:Net|GAN|BERT|GPT|Transformer|CNN|RNN|'
        r'GNN|VAE|Flow|Model|Method|Algorithm|Framework|Network|'
        r'Potential|Field|Force|Kernel|Attention))\b',
        text
    )
    concepts.update(method_names)

    # 匹配 "we propose/present/introduce X" 中的 X
    proposed = re.findall(
        r'(?:we\s+(?:propose|present|introduce|develop))\s+([A-Z][a-zA-Z\s]{3,40})',
        text, re.IGNORECASE
    )
    for p in proposed:
        concepts.add(p.strip())

    # 匹配标题中的术语（假设标题在开头）
    title_match = re.search(r'\\begin\{title\}(.*?)\\end\{title\}', text, re.DOTALL)
    if title_match:
        title_words = title_match.group(1).strip().split()
        # 取标题中的实词（长度 > 3）
        for w in title_words:
            if len(w) > 3 and w[0].isupper():
                concepts.add(w)

    return list(concepts)[:15]


# ─── 步骤 1：种子论文解析 ──────────────────────────────────

def resolve_seed(seed_input: str) -> dict:
    """
    解析种子论文输入，返回论文元信息和全文内容。

    返回:
        {
            "doi": str, "title": str, "pdf_url": str,
            "content": str, "references": list[str],
            "concepts": list[str], "metadata": dict
        }
    """
    print(f"[步骤 1/3] 种子论文解析：{seed_input}")

    result = {
        "doi": "", "title": "", "pdf_url": "",
        "content": "", "references": [], "concepts": [],
        "metadata": {}
    }

    # 判断输入类型
    if seed_input.startswith("http"):
        result["pdf_url"] = seed_input
        print(f"  输入类型：PDF URL")
    elif seed_input.startswith("10."):
        result["doi"] = seed_input
        result["pdf_url"] = doi_to_pdf_url(seed_input)
        print(f"  输入类型：DOI → {result['pdf_url']}")
    else:
        # 标题搜索
        print(f"  输入类型：标题，先搜索定位...")
        try:
            r = requests.post(
                f"{BASE_PAPER}/rag/pass/keyword",
                headers=H_JSON,
                json={
                    "words": seed_input.split()[:5],
                    "question": seed_input,
                    "type": 5,
                    "pageSize": 1
                },
                timeout=30
            )
            text = r.text.strip()
            first_line = text.split('\n')[0]
            data = json.loads(first_line)

            if data.get("data"):
                first = data["data"][0]
                result["doi"] = first.get("doi", "")
                result["title"] = first.get("enName", "")
                result["metadata"] = first
                print(f"  找到：{result['title']}")
                print(f"  DOI：{result['doi']}")
                if result["doi"]:
                    result["pdf_url"] = doi_to_pdf_url(result["doi"])
                else:
                    print("  警告：未找到 DOI，跳过 PDF 解析")
                    return result
            else:
                print("  未找到匹配论文，请提供更精确的标题或 DOI")
                return result
        except Exception as e:
            print(f"  搜索失败：{e}")
            return result

    # 使用 paper-search 获取元信息（如果还没有）
    if not result["metadata"] and result["doi"]:
        try:
            r = requests.post(
                f"{BASE_PAPER}/rag/pass/keyword",
                headers=H_JSON,
                json={
                    "words": [result["doi"]],
                    "question": result["doi"],
                    "type": 5,
                    "pageSize": 1
                },
                timeout=30
            )
            text = r.text.strip()
            first_line = text.split('\n')[0]
            data = json.loads(first_line)
            if data.get("data"):
                result["metadata"] = data["data"][0]
                result["title"] = result["metadata"].get("enName", "")
        except Exception:
            pass

    # PDF 解析：提取参考文献和关键概念
    if result["pdf_url"]:
        print(f"  提交 PDF 解析...")
        try:
            r = requests.post(
                f"{BASE_PARSE}/trigger-url-async",
                headers=H_JSON,
                json={
                    "url": result["pdf_url"],
                    "sync": False,
                    "textual": True,
                    "table": False,
                    "molecule": False,
                    "chart": False,
                    "figure": False,
                    "expression": False,
                    "equation": False,
                    "timeout": 1800
                },
                timeout=30
            )
            submit = r.json()
            if submit.get("code"):
                print(f"  PDF 提交失败：{submit.get('message')}")
            else:
                token = submit["token"]
                print(f"  已提交，token={token}，轮询结果...")

                # 轮询（最多 120 秒）
                for attempt in range(60):
                    time.sleep(2)
                    try:
                        r = requests.post(
                            f"{BASE_PARSE}/get-result",
                            headers=H_JSON,
                            json={
                                "token": token,
                                "content": True,
                                "objects": False,
                                "pages_dict": False
                            },
                            timeout=30
                        )
                        res = r.json()
                        status = res.get("status", "")

                        if status == "success":
                            result["content"] = res.get("content", "")
                            print(f"  解析完成！内容长度 {len(result['content'])} 字符")
                            break
                        elif status == "failed":
                            print(f"  解析失败：{res.get('description', '未知')}")
                            break
                        else:
                            if attempt % 5 == 0:
                                proc = res.get("proc_page", 0)
                                total = res.get("total_page", 0)
                                print(f"  [{attempt+1}] 解析中... ({proc}/{total} 页)")
                    except Exception as e:
                        print(f"  [{attempt+1}] 查询失败：{e}")
                        continue
                else:
                    print("  PDF 解析超时（120 秒）")

        except Exception as e:
            print(f"  PDF 解析请求失败：{e}")

    # 提取参考文献和关键概念
    if result["content"]:
        result["references"] = extract_references_from_text(result["content"])
        result["concepts"] = extract_key_concepts(result["content"])
        print(f"  提取到 {len(result['references'])} 条参考文献线索")
        print(f"  提取到 {len(result['concepts'])} 个关键概念")
    else:
        # fallback：从元信息中提取
        if result["metadata"]:
            abstract = result["metadata"].get("enAbstract", "")
            title = result["metadata"].get("enName", "")
            result["concepts"] = (title + " " + abstract).split()[:10]
            print(f"  PDF 解析不可用，使用元信息中的关键词")

    return result


# ─── 步骤 2：多跳引用网络扩展 ─────────────────────────────

def expand_network(seed_result: dict, direction: str, depth: int) -> CitationNetwork:
    """
    从种子论文出发，多跳扩展引用网络。

    参数：
        seed_result: resolve_seed 的返回值
        direction: "forward" / "backward" / "both"
        depth: 探索跳数 1-3
    """
    print(f"\n[步骤 2/3] 引用网络扩展（方向={direction}，深度={depth}跳）")

    network = CitationNetwork()

    # 添加种子节点
    meta = seed_result.get("metadata", {})
    seed_node = PaperNode(
        doi=seed_result.get("doi", "") or meta.get("doi", ""),
        title=seed_result.get("title", "") or meta.get("enName", ""),
        year=meta.get("coverDateStart", "")[:4],
        journal=meta.get("publicationEnName", ""),
        citations=meta.get("citationNums", 0),
        impact_factor=meta.get("impactFactor", 0),
        abstract=meta.get("enAbstract", "")
    )
    seed_node.hop = 0
    seed_node.role = "seed"
    network.add_node(seed_node)

    seed_doi = seed_node.doi
    print(f"  种子节点：{seed_node.title[:60]} (DOI: {seed_doi})")

    # 每跳的待扩展节点队列
    current_frontier = [seed_doi]

    for hop in range(1, depth + 1):
        print(f"\n  === 第 {hop} 跳 ===")
        next_frontier = []

        for frontier_doi in current_frontier:
            frontier_node = network.get_node(frontier_doi)
            if not frontier_node:
                continue

            # ── backward：检索参考文献 ──
            if direction in ("backward", "both"):
                print(f"  [backward] 从 {frontier_doi[:30]}... 向后追溯")
                backward_papers = _search_references(
                    frontier_node, seed_result, hop
                )
                for p in backward_papers:
                    node = _paper_to_node(p, hop)
                    network.add_node(node)
                    network.add_edge(frontier_doi, node.doi, "backward")
                    if hop < depth and node.doi not in next_frontier:
                        next_frontier.append(node.doi)
                print(f"    找到 {len(backward_papers)} 篇参考文献")

            # ── forward：检索施引论文 ──
            if direction in ("forward", "both"):
                print(f"  [forward] 从 {frontier_doi[:30]}... 向前追溯")
                forward_papers = _search_citing(
                    frontier_node, seed_result, hop
                )
                for p in forward_papers:
                    node = _paper_to_node(p, hop)
                    network.add_node(node)
                    network.add_edge(node.doi, frontier_doi, "forward")
                    if hop < depth and node.doi not in next_frontier:
                        next_frontier.append(node.doi)
                print(f"    找到 {len(forward_papers)} 篇施引论文")

        current_frontier = next_frontier[:20]  # 限制每跳扩展规模
        print(f"  第 {hop} 跳完成，网络节点数：{len(network.nodes)}")

    stats = network.stats()
    print(f"\n  网络构建完成：{stats['total_nodes']} 个节点，"
          f"{stats['total_edges']} 条边")
    return network


def _search_references(node: PaperNode, seed_result: dict, hop: int) -> list:
    """
    用 paper-search 检索一个节点的参考文献。
    利用从 PDF 中提取的参考文献线索作为搜索词。
    """
    # 对种子节点使用 PDF 提取的参考文献，对其他节点使用标题关键词
    if hop == 1 and seed_result.get("references"):
        # 从种子论文的参考文献列表中搜索
        refs = seed_result["references"]
        # 优先搜索 DOI
        doi_refs = [r for r in refs if r.startswith("10.")][:5]
        title_refs = [r for r in refs if not r.startswith("10.")][:5]
        search_words = doi_refs + title_refs
    else:
        # 使用节点标题关键词搜索更早的论文
        title_words = [w for w in node.title.split() if len(w) > 3][:5]
        search_words = title_words

    if not search_words:
        return []

    try:
        # 搜索发表日期早于当前节点的论文
        end_time = f"{node.year}-12-31" if node.year else ""
        r = requests.post(
            f"{BASE_PAPER}/rag/pass/keyword",
            headers=H_JSON,
            json={
                "words": search_words,
                "question": node.title,
                "type": 5,
                "endTime": end_time,
                "pageSize": 10
            },
            timeout=30
        )
        text = r.text.strip()
        first_line = text.split('\n')[0]
        data = json.loads(first_line)
        papers = data.get("data", [])
        # 过滤掉与当前节点相同的论文
        papers = [p for p in papers if p.get("doi") != node.doi]
        # 按引用数排序，取 top 结果
        papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
        return papers[:8]
    except Exception as e:
        print(f"    参考文献检索失败：{e}")
        return []


def _search_citing(node: PaperNode, seed_result: dict, hop: int) -> list:
    """
    用 paper-search 检索引用了当前节点的论文（施引方向）。
    策略：搜索相同概念但发表时间更晚的论文。
    """
    # 使用节点标题关键词 + 种子论文的概念
    concepts = seed_result.get("concepts", [])
    title_words = [w for w in node.title.split() if len(w) > 3][:3]
    search_words = list(set(title_words + concepts[:3]))

    if not search_words:
        return []

    try:
        # 搜索发表日期晚于当前节点的论文
        start_time = f"{node.year}-01-01" if node.year else ""
        r = requests.post(
            f"{BASE_PAPER}/rag/pass/keyword",
            headers=H_JSON,
            json={
                "words": search_words,
                "question": f"papers citing or building upon: {node.title}",
                "type": 5,
                "startTime": start_time,
                "pageSize": 10
            },
            timeout=30
        )
        text = r.text.strip()
        first_line = text.split('\n')[0]
        data = json.loads(first_line)
        papers = data.get("data", [])
        papers = [p for p in papers if p.get("doi") != node.doi]
        papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)
        return papers[:8]
    except Exception as e:
        print(f"    施引论文检索失败：{e}")
        return []


def _paper_to_node(paper: dict, hop: int) -> PaperNode:
    """将 paper-search 返回的论文转为 PaperNode。"""
    node = PaperNode(
        doi=paper.get("doi", ""),
        title=paper.get("enName", ""),
        year=paper.get("coverDateStart", "")[:4],
        journal=paper.get("publicationEnName", ""),
        citations=paper.get("citationNums", 0),
        impact_factor=paper.get("impactFactor", 0),
        abstract=paper.get("enAbstract", "")
    )
    node.hop = hop
    return node


# ─── 步骤 3：概念继承分析（LKM） ──────────────────────────

def analyze_lineage(network: CitationNetwork, seed_result: dict) -> CitationNetwork:
    """
    使用 LKM 分析引用网络中节点之间的概念继承关系，标注节点角色。
    """
    print(f"\n[步骤 3/3] 概念继承分析（LKM）")

    seed_doi = seed_result.get("doi", "")
    seed_concepts = seed_result.get("concepts", [])

    # 3a. 用 LKM search 获取种子论文的核心概念网络
    print(f"  3a. 查询种子论文的知识图谱...")
    seed_title = seed_result.get("title", "") or seed_result.get("metadata", {}).get("enName", "")
    kg_concepts = []
    try:
        r = requests.post(
            f"{BASE_LKM}/search",
            headers=H_JSON,
            json={"query": seed_title, "limit": 10},
            timeout=30
        )
        kg_data = r.json()
        kg_concepts = kg_data.get("data", [])
        print(f"      找到 {len(kg_concepts)} 个知识图谱概念")
    except Exception as e:
        print(f"      知识图谱搜索失败：{e}")

    # 3b. 为每个非种子节点分析角色
    print(f"\n  3b. 节点角色标注...")
    nodes_to_analyze = [
        n for n in network.nodes.values() if n.role != "seed"
    ]

    for i, node in enumerate(nodes_to_analyze):
        if not node.abstract and not node.title:
            node.role = "unknown"
            node.role_reason = "元信息不足"
            continue

        # 用 LKM search 查询该节点的概念
        try:
            r = requests.post(
                f"{BASE_LKM}/search",
                headers=H_JSON,
                json={"query": node.title, "limit": 5},
                timeout=30
            )
            node_kg = r.json().get("data", [])
        except Exception:
            node_kg = []

        # 判断角色
        role, reason = _classify_node_role(
            node, kg_concepts, node_kg, network
        )
        node.role = role
        node.role_reason = reason

        if (i + 1) % 5 == 0 or (i + 1) == len(nodes_to_analyze):
            print(f"      已标注 {i+1}/{len(nodes_to_analyze)} 个节点")

    # 统计
    stats = network.stats()
    print(f"\n  标注完成：")
    print(f"    开创性工作：{stats['pioneering_count']} 篇")
    print(f"    方法改进：{stats['improvement_count']} 篇")
    print(f"    应用拓展：{stats['extension_count']} 篇")

    return network


def _classify_node_role(
    node: PaperNode,
    seed_kg: list,
    node_kg: list,
    network: CitationNetwork
) -> tuple[str, str]:
    """
    根据以下信号判断节点角色：
    - 发表年份（早期 → 开创性）
    - 引用数量（高引用 + 早期 → 开创性）
    - 知识图谱概念重叠度（高重叠 → 方法改进；低重叠 → 应用拓展）
    - 在网络中的位置（入度高 → 开创性）
    """
    # 计算与种子论文的概念重叠
    seed_concept_texts = set()
    for item in seed_kg:
        if isinstance(item, dict):
            seed_concept_texts.add(
                str(item.get("content", "")).lower()[:100]
            )

    node_concept_texts = set()
    for item in node_kg:
        if isinstance(item, dict):
            node_concept_texts.add(
                str(item.get("content", "")).lower()[:100]
            )

    # 概念重叠率
    if seed_concept_texts and node_concept_texts:
        overlap = len(seed_concept_texts & node_concept_texts)
        overlap_ratio = overlap / max(len(seed_concept_texts), 1)
    else:
        overlap_ratio = 0.5  # 默认中等

    # 计算网络入度（被引用次数）
    in_degree = sum(
        1 for (_, to_doi, _) in network.edges if to_doi == node.doi
    )

    # 判断逻辑
    try:
        year_int = int(node.year) if node.year else 2020
    except ValueError:
        year_int = 2020

    # 开创性工作：早期发表 + 高引用 + 高入度
    if (year_int < 2015 and node.citations > 100) or (in_degree >= 3):
        return "pioneering", (
            f"早期高引用工作（{node.year}年，{node.citations}次引用，"
            f"网络入度={in_degree}）"
        )

    # 方法改进：与种子论文概念高度重叠
    if overlap_ratio > 0.3:
        return "method-improvement", (
            f"与种子论文概念重叠度高（{overlap_ratio:.0%}），"
            f"属于同方法的迭代改进"
        )

    # 应用拓展：概念重叠低，说明应用到了不同领域
    if overlap_ratio < 0.2:
        return "application-extension", (
            f"与种子论文概念重叠度低（{overlap_ratio:.0%}），"
            f"可能是跨领域应用"
        )

    # 默认归为方法改进
    return "method-improvement", (
        f"概念重叠度中等（{overlap_ratio:.0%}），归为方法改进"
    )


# ─── 报告生成 ──────────────────────────────────────────────

def generate_report(
    seed_input: str,
    direction: str,
    depth: int,
    seed_result: dict,
    network: CitationNetwork
) -> str:
    """
    生成引用网络谱系报告（Markdown 格式）。
    """
    report = []
    stats = network.stats()

    report.append("# 引用网络探索报告\n")
    report.append(f"**种子论文**：{seed_result.get('title', seed_input)}")
    report.append(f"**DOI**：{seed_result.get('doi', 'N/A')}")
    report.append(f"**探索方向**：{direction}")
    report.append(f"**探索深度**：{depth} 跳")
    report.append(f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # ── 1. 网络统计 ──
    report.append("## 1. 网络统计\n")
    report.append(f"| 指标 | 值 |")
    report.append(f"|------|-----|")
    report.append(f"| 节点总数 | {stats['total_nodes']} |")
    report.append(f"| 边总数 | {stats['total_edges']} |")
    report.append(f"| 时间跨度 | {stats['year_range']} |")
    report.append(f"| 开创性工作 | {stats['pioneering_count']} 篇 |")
    report.append(f"| 方法改进 | {stats['improvement_count']} 篇 |")
    report.append(f"| 应用拓展 | {stats['extension_count']} 篇 |")
    report.append("")

    # ── 2. 引用谱系描述 ──
    report.append("## 2. 引用谱系（关键传承路径）\n")

    # 按角色和年份组织谱系叙述
    pioneering = sorted(
        [n for n in network.nodes.values() if n.role == "pioneering"],
        key=lambda x: x.year or "9999"
    )
    improvements = sorted(
        [n for n in network.nodes.values() if n.role == "method-improvement"],
        key=lambda x: x.year or "9999"
    )
    extensions = sorted(
        [n for n in network.nodes.values() if n.role == "application-extension"],
        key=lambda x: x.year or "9999"
    )

    if pioneering:
        report.append("### 开创性工作\n")
        report.append("以下论文奠定了该领域的理论/方法基础：\n")
        for n in pioneering:
            report.append(
                f"- **[{n.year}]** {n.title} "
                f"(被引 {n.citations}, IF={n.impact_factor})"
            )
            report.append(f"  - {n.role_reason}")
            if n.doi:
                report.append(f"  - DOI: `{n.doi}`")
        report.append("")

    if improvements:
        report.append("### 方法改进脉络\n")
        report.append("以下论文在已有方法基础上进行了迭代优化：\n")
        for n in improvements[:10]:  # 最多列 10 篇
            report.append(
                f"- **[{n.year}]** {n.title} "
                f"(被引 {n.citations})"
            )
            report.append(f"  - {n.role_reason}")
        report.append("")

    if extensions:
        report.append("### 应用拓展\n")
        report.append("以下论文将核心方法应用到了新领域：\n")
        for n in extensions[:10]:
            report.append(
                f"- **[{n.year}]** {n.title} "
                f"(被引 {n.citations})"
            )
            report.append(f"  - {n.role_reason}")
        report.append("")

    # ── 3. 节点标注全表 ──
    report.append("## 3. 节点论文标注\n")
    report.append("| # | 年份 | 标题 | 期刊 | 被引 | 角色 | 跳数 |")
    report.append("|---|------|------|------|------|------|------|")

    sorted_nodes = sorted(
        network.nodes.values(),
        key=lambda x: (x.hop, -(x.citations or 0))
    )
    for i, n in enumerate(sorted_nodes, 1):
        role_label = {
            "seed": "种子",
            "pioneering": "开创",
            "method-improvement": "改进",
            "application-extension": "应用",
            "unknown": "未知"
        }.get(n.role, n.role)
        title_short = n.title[:50] + ("..." if len(n.title) > 50 else "")
        journal_short = (n.journal[:15] + "...") if len(n.journal) > 15 else n.journal
        report.append(
            f"| {i} | {n.year} | {title_short} | "
            f"{journal_short} | {n.citations} | {role_label} | {n.hop} |"
        )
    report.append("")

    # ── 4. 推荐跟进阅读 ──
    report.append("## 4. 推荐跟进阅读\n")
    report.append("以下论文在引用网络中具有较高桥接价值，但引用数可能不突出，"
                  "值得深入阅读：\n")

    # 计算桥接度：同时有入边和出边的节点
    in_nodes = set(to_d for (_, to_d, _) in network.edges)
    out_nodes = set(fr_d for (fr_d, _, _) in network.edges)
    bridge_nodes = in_nodes & out_nodes

    recommended = []
    for doi in bridge_nodes:
        node = network.get_node(doi)
        if node and node.role != "seed":
            # 桥接度 = 入度 + 出度
            in_deg = sum(1 for (_, t, _) in network.edges if t == doi)
            out_deg = sum(1 for (f, _, _) in network.edges if f == doi)
            bridge_score = in_deg + out_deg
            recommended.append((node, bridge_score))

    recommended.sort(key=lambda x: x[1], reverse=True)

    if recommended:
        for node, score in recommended[:10]:
            report.append(
                f"- **{node.title}** ({node.year}, 被引 {node.citations})"
            )
            report.append(
                f"  - 桥接度：{score}（连接 {score} 个子网络节点）"
            )
            report.append(f"  - 角色：{node.role} — {node.role_reason}")
            if node.doi:
                report.append(f"  - DOI: `{node.doi}`")
    else:
        report.append("当前探索深度下未发现明显的桥接节点。"
                      "建议增加探索深度（depth=2 或 3）以发现更多传承路径。")

    report.append("")

    return "\n".join(report)


# ─── 主流程 ────────────────────────────────────────────────

def explore_citations(seed_input: str, direction: str = "both", depth: int = 1):
    """
    引用网络探索主函数。

    参数：
        seed_input: 种子论文（DOI / 标题 / PDF URL）
        direction: "forward" / "backward" / "both"
        depth: 探索跳数（1-3）
    """
    print("=" * 60)
    print("  引用网络探索 (Citation Explorer)")
    print(f"  种子论文：{seed_input}")
    print(f"  探索方向：{direction}")
    print(f"  探索深度：{depth} 跳")
    print("=" * 60)

    # 参数校验
    if direction not in ("forward", "backward", "both"):
        print(f"未知方向：{direction}，使用默认 both")
        direction = "both"
    if depth < 1 or depth > 3:
        print(f"深度 {depth} 超出范围（1-3），已调整为 {max(1, min(3, depth))}")
        depth = max(1, min(3, depth))

    # 步骤 1：种子论文解析
    seed_result = resolve_seed(seed_input)
    if not seed_result.get("doi") and not seed_result.get("concepts"):
        print("\n无法解析种子论文，请检查输入。")
        return

    # 步骤 2：多跳引用网络扩展
    network = expand_network(seed_result, direction, depth)

    # 步骤 3：概念继承分析
    network = analyze_lineage(network, seed_result)

    # 生成报告
    print("\n" + "=" * 60)
    print("  生成引用网络谱系报告...")
    print("=" * 60 + "\n")

    report = generate_report(seed_input, direction, depth, seed_result, network)
    print(report)

    return report


# ─── 入口 ──────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python citation_explorer.py <DOI|标题|PDF_URL> [forward|backward|both] [1|2|3]")
        print()
        print("示例：")
        print("  python citation_explorer.py 10.1038/s41586-021-03819-2 both 2")
        print("  python citation_explorer.py https://arxiv.org/pdf/2107.06922 backward 1")
        print('  python citation_explorer.py "Attention Is All You Need" both 3')
        sys.exit(1)

    seed = sys.argv[1]
    direction = sys.argv[2] if len(sys.argv) > 2 else "both"
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    explore_citations(seed, direction, depth)
```

---

## 各步骤详解

### 步骤 1：种子论文解析 (`pdf-parser`)

解析种子论文的 PDF 全文，核心目标是提取两类信息：

1. **参考文献列表**：用于 backward 方向的追溯
2. **关键概念术语**：用于 forward 方向的搜索

**参考文献提取策略：**

```python
# 策略 1：DOI 模式匹配
doi_pattern = r'10\.\d{4,9}/[^\s,;}\])]+'

# 策略 2：作者-年份模式 → "Smith et al., 2020"
author_year_pattern = r'([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*(?:19|20)\d{2})'

# 策略 3：References 段落中的引号标题
ref_section = re.search(r'(?i)(?:references|bibliography)\s*\n(.*)', text)
```

**关键概念提取策略：**

```python
# 匹配方法名（如 Transformer, AlphaFold）
# 匹配 "we propose X" 中的 X
# 匹配标题中的实词
```

---

### 步骤 2：多跳引用网络扩展 (`paper-search`)

使用 `paper-search` 的时间过滤功能实现方向性搜索：

- **backward（参考文献方向）**：搜索 `endTime < 当前节点发表年份` 的论文
- **forward（被引方向）**：搜索 `startTime > 当前节点发表年份` 的论文

每跳限制扩展规模（最多 20 个前沿节点），避免网络爆炸。

```python
# backward 搜索：比当前论文更早的文献
payload = {
    "words": reference_keywords,
    "question": node.title,
    "endTime": f"{node.year}-12-31",
    "pageSize": 10
}

# forward 搜索：比当前论文更新的文献
payload = {
    "words": concept_keywords,
    "question": f"papers citing or building upon: {node.title}",
    "startTime": f"{node.year}-01-01",
    "pageSize": 10
}
```

---

### 步骤 3：概念继承分析 (`lkm`)

对每个非种子节点调用 `lkm/search`，查询其核心概念，然后与种子论文的概念网络对比，判断节点角色：

**角色判断逻辑：**

```
开创性工作 (pioneering)
  条件：早期发表（< 2015）+ 高引用（> 100）或网络入度 >= 3
  含义：该领域的奠基性论文

方法改进 (method-improvement)
  条件：与种子论文概念重叠度 > 30%
  含义：在已有方法基础上的迭代优化

应用拓展 (application-extension)
  条件：与种子论文概念重叠度 < 20%
  含义：将方法迁移到新领域
```

---

## 使用示例

### 从 DOI 出发，双向探索 2 跳

```python
explore_citations("10.1038/s41586-021-03819-2", direction="both", depth=2)
```

### 从 arXiv PDF 出发，只看参考文献方向

```python
explore_citations("https://arxiv.org/pdf/2107.06922", direction="backward", depth=1)
```

### 从标题出发，追溯完整传承谱系

```python
explore_citations("Attention Is All You Need", direction="both", depth=3)
```

### 命令行调用

```bash
# 双向 2 跳
python citation_explorer.py 10.1038/s41586-021-03819-2 both 2

# 只向后追溯 1 跳（看参考文献）
python citation_explorer.py https://arxiv.org/pdf/2107.06922 backward 1

# 完整谱系（3 跳）
python citation_explorer.py "Highly accurate protein structure prediction with AlphaFold" both 3
```

---

## curl 示例

以下展示各步骤的独立 curl 调用：

### 步骤 1：PDF 解析提取参考文献

```bash
AK="YOUR_ACCESS_KEY"

# 提交 PDF 解析
TOKEN=$(curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/trigger-url-async" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "url": "https://arxiv.org/pdf/2107.06922",
    "sync": false,
    "textual": true,
    "table": false,
    "molecule": false,
    "chart": false,
    "figure": false,
    "expression": false,
    "equation": false,
    "timeout": 1800
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "Token: $TOKEN"

# 轮询结果
sleep 10
curl -s -X POST "https://open.bohrium.com/openapi/v1/parse/get-result" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d "{\"token\": \"$TOKEN\", \"content\": true, \"objects\": false, \"pages_dict\": false}"
```

### 步骤 2：搜索参考文献（backward）和施引论文（forward）

```bash
# backward：搜索种子论文引用的早期文献
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["AlphaFold", "protein structure", "deep learning"],
    "question": "protein structure prediction foundational methods",
    "type": 5,
    "endTime": "2020-12-31",
    "pageSize": 10
  }'

# forward：搜索引用了种子论文的后续工作
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["AlphaFold", "protein structure", "deep learning"],
    "question": "papers building upon AlphaFold protein structure prediction",
    "type": 5,
    "startTime": "2021-07-01",
    "pageSize": 10
  }'
```

### 步骤 3：LKM 概念继承分析

```bash
# 查询种子论文的知识图谱概念
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "Highly accurate protein structure prediction with AlphaFold", "limit": 10}' \
  | python3 -m json.tool

# 查询网络中某节点的概念（用于对比重叠度）
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"query": "Improved protein structure prediction using potentials from deep learning", "limit": 5}' \
  | python3 -m json.tool
```

---

## 错误处理

| 场景 | 错误信息 | 处理方式 |
|------|---------|---------|
| ACCESS_KEY 未设置 | `未设置 ACCESS_KEY 环境变量` | 配置 `~/.openclaw/openclaw.json` |
| 种子论文搜索无结果 | `未找到匹配论文` | 使用更精确的标题或直接提供 DOI |
| PDF 解析失败 | `PDF 提交失败` / `解析失败` | 检查 URL 是否为直链；退化为仅使用元信息 |
| PDF 解析超时 | `PDF 解析超时（120 秒）` | 论文页数过多，可直接提供 DOI（跳过 PDF 解析） |
| paper-search 无结果 | 某跳扩展返回 0 篇 | 正常现象，说明该方向引用链较短 |
| LKM 搜索失败 | `知识图谱搜索失败` | 不影响整体流程，节点角色标注退化为基于引用数判断 |
| 网络过大（depth=3） | 执行时间过长 | 降低 depth 或限制 direction 为单向 |
| 401 Unauthorized | accessKey 无效 | 确认 ACCESS_KEY 正确 |

---

## 常见问题

| 问题 | 回答 |
|------|------|
| **forward 搜索不精确怎么办？** | paper-search 基于语义检索而非引用关系数据库，forward 结果是"概念相关的后续论文"而非精确的施引列表。对精度要求高时，建议结合 Google Scholar 的引用数据交叉验证。 |
| **depth=3 太慢了？** | 3 跳会产生大量 API 调用。建议先用 depth=1 快速预览，确认方向后再用 depth=2。depth=3 适合离线批量分析。 |
| **节点角色标注不准？** | 自动标注基于 LKM 概念重叠度和引用数的启发式规则，可能存在误判。报告生成后建议人工校验关键节点。 |
| **参考文献提取不全？** | PDF 中的参考文献格式多样，正则匹配难以覆盖所有格式。提取到的是用于搜索的线索，不要求 100% 召回。 |
| **如何只看某个子方向？** | 使用 direction="backward" 只看源头，direction="forward" 只看后续发展。双向探索信息最全但耗时最长。 |
| **能否自定义节点角色判定阈值？** | 可以修改 `_classify_node_role` 中的年份阈值、引用数阈值和重叠度阈值来适应不同领域。 |

---

## 搭配使用

- **citation-explorer** 构建引用骨架 → **literature-review** 针对关键分支展开综述
- **citation-explorer** 发现开创性工作 → **paper-dissector** 深度拆解该论文
- **citation-explorer** 标注应用拓展节点 → **field-mapper** 分析跨领域迁移路径
- **citation-explorer** 输出推荐阅读列表 → **bohrium-knowledge-base** 存档管理
