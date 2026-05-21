---
name: tech-radar
description: "Technology and competitor monitoring by tracking publications, patents, and news from target organizations or researchers. Use when: user wants to monitor competitor technology moves, track a specific scholar's outputs, or stay updated on a technology direction. NOT for: one-time paper search (use bohrium-paper-search), scholar profile lookup (use bohrium-scholar-search)."
---

# SKILL: 竞品技术监控 (Tech Radar)

## 概述

编排多个 Bohrium 原子技能（paper-search、scholar-search、web-search、knowledge-base），对目标组织、学者或技术方向进行**周期性**监控，自动产出结构化情报报告。

**核心流程：**

```
输入监控目标
  │
  ├─ 1. paper-search   → 检索目标相关的最新论文
  ├─ 2. patent-search   → 检索目标相关的最新专利
  ├─ 3. scholar-search  → 追踪目标学者的最新动态
  ├─ 4. web-search      → 搜索新闻、产品发布、技术博客
  │
  ├─ 5. 增量分析        → 与上次基线对比，提取新增/变化项
  │
  └─ 6. 输出报告        → 新动态列表 + 趋势判断 + 影响评估 + 建议
       └─ (可选) 存入知识库作为下次基线
```

**适用场景：**
- 跟踪竞争对手的论文、专利和产品动态
- 监控某学者/课题组的最新发表
- 追踪某技术方向的发展趋势

**不适用：**
- 一次性论文搜索 → 用 `bohrium-paper-search`
- 单纯查询学者信息 → 用 `bohrium-scholar-search`
- 一次性网页搜索 → 用 `bohrium-web-search`

**无 CLI 支持** — 全部通过 HTTP API 编排。

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"tech-radar": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.ACCESS_KEY` 注入到运行环境。

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| 监控目标 | list | 是 | 公司名 / 学者姓名 / 技术关键词，可混合多个 |
| 时间窗口 | string | 否 | 默认近 30 天，格式 `YYYY-MM-DD` |
| 对比基线 | dict | 否 | 上次报告数据（从知识库获取），用于增量分析 |
| 知识库 ID | int | 否 | 用于存储/读取历史基线的知识库 nodesId |

## 输出内容

| 板块 | 内容 |
|------|------|
| 新动态列表 | 按类型分类：论文 / 专利 / 新闻，各项含标题、来源、日期、摘要 |
| 趋势判断 | 加速 / 减速 / 方向转变，基于发文频率、专利申请量、新闻热度变化 |
| 影响评估 | 对自身研究/业务的潜在影响分析 |
| 建议关注项 | 需重点跟进的论文、专利或事件 |

---

## 报告质量控制

### 趋势判断的定量依据

趋势判断**不能只是主观感受**，必须有定量支撑：
- **加速**：近 6 月论文数 > 前 6 月的 1.5 倍，或出现多篇高引用速度论文（月均引用 > 5）
- **减速**：近 6 月论文数 < 前 6 月的 0.6 倍
- **方向转变**：高频关键词发生显著变化（前期 Top-5 关键词 ≥ 2 个被新词替换）

每个趋势判断必须附带"判断依据"一行，引用具体数字。

### 新动态的过滤与去噪

- 排除综述论文（综述发表不代表新动态，只是对已有工作的总结）
- 排除仅标题相关但内容无关的检索噪音
- 新闻类动态需标注来源可靠性（学术机构官网 vs 一般媒体）

### 禁止的行为

- ❌ "趋势：该方向正在加速发展"而不给出具体数据支撑
- ❌ 将所有近期论文都标为"重要新动态"而不区分优先级
- ❌ 影响评估使用模板化语言（如"值得关注"），必须说明具体影响什么、怎么影响

---

## 通用代码模板

```python
import os
import json
import requests
from datetime import datetime, timedelta

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    raise RuntimeError(
        "ACCESS_KEY not found. Please configure it in ~/.openclaw/openclaw.json "
        "under tech-radar.env.ACCESS_KEY."
    )

HEADERS = {"accessKey": AK}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}

# API 基础地址
BASE_PAPER = "https://open.bohrium.com/openapi/v1/paper"
BASE_SCHOLAR = "https://open.bohrium.com/openapi/v1/paper-server"
BASE_WEB = "https://open.bohrium.com/openapi/v1/search/web"
BASE_KB = "https://open.bohrium.com/openapi/v1/knowledge"
```

---

## 完整编排脚本

以下脚本实现端到端的竞品监控流程，包括数据采集、增量对比、报告生成和基线存储。

### 第一步：定义监控配置

```python
# ============================================================
# 监控配置
# ============================================================
MONITOR_CONFIG = {
    "targets": {
        "companies": ["DeepMind", "OpenAI"],           # 目标公司
        "scholars": ["Yann LeCun", "Geoffrey Hinton"], # 目标学者
        "keywords": ["large language model", "protein structure prediction"],  # 技术关键词
    },
    "time_window_days": 30,          # 时间窗口（天）
    "knowledge_base_id": None,       # 知识库 ID（可选，用于基线存储）
    "knowledge_base_node_id": None,  # 知识库 nodesId（可选）
}

# 计算时间范围
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=MONITOR_CONFIG["time_window_days"])).strftime("%Y-%m-%d")
```

### 第二步：论文检索

```python
def search_papers(keywords, start_time, end_time, page_size=20):
    """通过 paper-search 检索最新论文"""
    results = []
    try:
        r = requests.post(
            f"{BASE_PAPER}/rag/pass/keyword",
            headers=HEADERS_JSON,
            json={
                "words": keywords,
                "question": " ".join(keywords),
                "type": 5,
                "startTime": start_time,
                "endTime": end_time,
                "pageSize": page_size,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") == 0 and data.get("data"):
            for p in data["data"]:
                results.append({
                    "type": "paper",
                    "title": p.get("enName", ""),
                    "doi": p.get("doi", ""),
                    "authors": p.get("authors", []),
                    "date": p.get("coverDateStart", ""),
                    "journal": p.get("publicationEnName", ""),
                    "abstract": p.get("enAbstract", "")[:300],
                    "citations": p.get("citationNums", 0),
                    "impact_factor": p.get("impactFactor", 0),
                })
    except requests.RequestException as e:
        print(f"[WARN] 论文检索失败: {e}")
    return results


# 执行：为每组关键词检索论文
all_papers = []
for kw_group in MONITOR_CONFIG["targets"]["keywords"]:
    # 将短语拆为词组
    words = kw_group.split()
    papers = search_papers(words, start_date, end_date)
    all_papers.extend(papers)

# 也为目标公司名搜索相关论文
for company in MONITOR_CONFIG["targets"]["companies"]:
    papers = search_papers([company], start_date, end_date, page_size=10)
    all_papers.extend(papers)

# 按 DOI 去重
seen_dois = set()
unique_papers = []
for p in all_papers:
    doi = p.get("doi", "")
    if doi and doi not in seen_dois:
        seen_dois.add(doi)
        unique_papers.append(p)
    elif not doi:
        unique_papers.append(p)
all_papers = unique_papers

print(f"[论文] 共检索到 {len(all_papers)} 篇去重后的论文")
```

### 第三步：专利检索

```python
def search_patents(keyword, page=1, page_size=10):
    """通过 patent-search 检索最新专利"""
    results = []
    try:
        r = requests.post(
            f"{BASE_PAPER}/rag/pass/patent",
            headers=HEADERS_JSON,
            json={
                "keyword": keyword,
                "page": page,
                "pageSize": page_size,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        # 专利接口返回格式可能为数组或包含 data 字段
        patent_list = data if isinstance(data, list) else data.get("data", [])
        if isinstance(patent_list, list):
            for p in patent_list:
                results.append({
                    "type": "patent",
                    "title": p.get("title", p.get("enName", str(p)[:200])),
                    "applicant": p.get("applicant", ""),
                    "date": p.get("date", p.get("applicationDate", "")),
                    "abstract": str(p.get("abstract", p.get("enAbstract", "")))[:300],
                    "patent_id": p.get("patentId", p.get("id", "")),
                    "raw": p,
                })
    except requests.RequestException as e:
        print(f"[WARN] 专利检索失败 ({keyword}): {e}")
    return results


# 执行：为每个关键词和公司搜索专利
all_patents = []
for kw in MONITOR_CONFIG["targets"]["keywords"]:
    patents = search_patents(kw)
    all_patents.extend(patents)

for company in MONITOR_CONFIG["targets"]["companies"]:
    patents = search_patents(company)
    all_patents.extend(patents)

print(f"[专利] 共检索到 {len(all_patents)} 条专利")
```

### 第四步：学者动态追踪

```python
def track_scholar(name):
    """通过 scholar-search 追踪学者最新动态"""
    result = {"name": name, "found": False, "info": {}}
    try:
        # 搜索学者
        r = requests.post(
            f"{BASE_SCHOLAR}/scholar/search",
            headers=HEADERS_JSON,
            json={"name": name, "page": 1, "pageSize": 3},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        items = data.get("data", {}).get("items", [])
        if not items:
            return result

        # 取第一个匹配结果
        scholar = items[0]
        scholar_id = scholar.get("scholarId", "")

        result["found"] = True
        result["info"] = {
            "scholar_id": scholar_id,
            "name_en": scholar.get("nameEn", ""),
            "name_zh": scholar.get("nameZh", ""),
            "org": scholar.get("scholarOrgNameEn", "") or scholar.get("scholarOrgNameZh", ""),
            "paper_count": scholar.get("paperNums", 0),
            "citation_count": scholar.get("citationNums", 0),
            "h_index": scholar.get("hIndex", 0),
            "is_high_cited": scholar.get("isHighCited", False),
        }

        # 获取详细信息
        if scholar_id:
            r2 = requests.get(
                f"{BASE_SCHOLAR}/scholar/info",
                headers=HEADERS,
                params={"scholarId": scholar_id},
                timeout=30,
            )
            if r2.status_code == 200:
                detail = r2.json().get("data", {})
                result["info"]["research_direction"] = detail.get("researchDirection", [])

    except requests.RequestException as e:
        print(f"[WARN] 学者追踪失败 ({name}): {e}")
    return result


# 执行：追踪所有目标学者
scholar_updates = []
for scholar_name in MONITOR_CONFIG["targets"]["scholars"]:
    update = track_scholar(scholar_name)
    scholar_updates.append(update)
    if update["found"]:
        info = update["info"]
        print(f"[学者] {info['name_en']}: 论文 {info['paper_count']}, "
              f"引用 {info['citation_count']}, h-index {info['h_index']}")
```

### 第五步：新闻与网络信息搜索

```python
def search_news(query, num=5):
    """通过 web-search 搜索新闻和动态"""
    results = []
    try:
        r = requests.get(
            BASE_WEB,
            headers=HEADERS,
            params={"q": query, "num": num},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        for hit in data.get("organic_results", []):
            results.append({
                "type": "news",
                "title": hit.get("title", ""),
                "url": hit.get("link", ""),
                "snippet": hit.get("snippet", "")[:300],
                "position": hit.get("position", 0),
            })
    except requests.RequestException as e:
        print(f"[WARN] 新闻搜索失败 ({query}): {e}")
    return results


# 执行：为每个目标搜索新闻
all_news = []
for company in MONITOR_CONFIG["targets"]["companies"]:
    news = search_news(f"{company} technology news 2024")
    all_news.extend(news)

for kw in MONITOR_CONFIG["targets"]["keywords"]:
    news = search_news(f"{kw} latest research breakthrough")
    all_news.extend(news)

# 按 URL 去重
seen_urls = set()
unique_news = []
for n in all_news:
    url = n.get("url", "")
    if url and url not in seen_urls:
        seen_urls.add(url)
        unique_news.append(n)
    elif not url:
        unique_news.append(n)
all_news = unique_news

print(f"[新闻] 共检索到 {len(all_news)} 条去重后的新闻")
```

### 第六步：读取历史基线（可选）

```python
def load_baseline(kb_node_id, kb_id):
    """从知识库中读取上次监控报告作为基线"""
    if not kb_node_id or not kb_id:
        return None
    try:
        r = requests.post(
            f"{BASE_KB}/file/search",
            headers=HEADERS_JSON,
            json={
                "queryContent": "tech-radar baseline report",
                "nodesId": kb_node_id,
                "knowledgeBaseId": kb_id,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        files = data.get("Files", [])
        if files:
            # 取最近的一份基线
            latest = files[0]
            print(f"[基线] 找到历史基线: {latest.get('fileName', '')}")
            return {
                "content": latest.get("content", ""),
                "file_name": latest.get("fileName", ""),
                "resource_id": latest.get("userResourceId", ""),
            }
    except requests.RequestException as e:
        print(f"[WARN] 基线读取失败: {e}")
    return None


# 执行：尝试加载基线
baseline = load_baseline(
    MONITOR_CONFIG.get("knowledge_base_node_id"),
    MONITOR_CONFIG.get("knowledge_base_id"),
)
```

### 第七步：增量分析与报告生成

```python
def incremental_analysis(current_papers, current_patents, current_news,
                         scholar_updates, baseline):
    """与基线对比，生成增量分析报告"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "time_window": f"{start_date} ~ {end_date}",
        "summary": {},
        "new_activities": {"papers": [], "patents": [], "news": []},
        "scholar_status": [],
        "trend": "",
        "impact_assessment": "",
        "action_items": [],
    }

    # ---- 新动态列表 ----
    report["new_activities"]["papers"] = current_papers
    report["new_activities"]["patents"] = current_patents
    report["new_activities"]["news"] = current_news
    report["scholar_status"] = scholar_updates

    # ---- 增量对比 ----
    new_paper_count = len(current_papers)
    new_patent_count = len(current_patents)
    new_news_count = len(current_news)

    baseline_paper_count = 0
    baseline_patent_count = 0
    if baseline and baseline.get("content"):
        # 尝试解析上次基线中的统计数据
        try:
            bl_data = json.loads(baseline["content"])
            baseline_paper_count = len(bl_data.get("new_activities", {}).get("papers", []))
            baseline_patent_count = len(bl_data.get("new_activities", {}).get("patents", []))
        except (json.JSONDecodeError, TypeError):
            pass

    # ---- 趋势判断 ----
    if baseline:
        paper_delta = new_paper_count - baseline_paper_count
        patent_delta = new_patent_count - baseline_patent_count

        if paper_delta > 5 or patent_delta > 3:
            report["trend"] = "加速 - 目标在该领域的投入明显增加"
        elif paper_delta < -5 or patent_delta < -3:
            report["trend"] = "减速 - 目标在该领域的产出有所下降"
        elif abs(paper_delta) <= 2 and abs(patent_delta) <= 1:
            report["trend"] = "平稳 - 目标保持稳定的研究产出节奏"
        else:
            report["trend"] = "波动 - 需持续观察确认趋势方向"

        report["summary"]["vs_baseline"] = {
            "paper_delta": paper_delta,
            "patent_delta": patent_delta,
            "baseline_file": baseline.get("file_name", ""),
        }
    else:
        report["trend"] = "首次监控 - 暂无历史基线可对比，本次数据将作为基线"

    # ---- 影响评估 ----
    high_impact_papers = [p for p in current_papers if p.get("impact_factor", 0) > 10]
    high_cite_papers = [p for p in current_papers if p.get("citations", 0) > 50]

    impact_notes = []
    if high_impact_papers:
        impact_notes.append(
            f"发现 {len(high_impact_papers)} 篇高影响因子论文（IF>10），建议重点阅读"
        )
    if high_cite_papers:
        impact_notes.append(
            f"发现 {len(high_cite_papers)} 篇高引用论文（>50次），代表领域热点"
        )
    if new_patent_count > 0:
        impact_notes.append(
            f"检索到 {new_patent_count} 条专利，关注是否涉及核心技术路线"
        )
    report["impact_assessment"] = "; ".join(impact_notes) if impact_notes else "本周期内未发现高影响动态"

    # ---- 建议关注项 ----
    action_items = []
    for p in high_impact_papers[:3]:
        t = p.get('title', '') or ''
        t = t if isinstance(t, str) else str(t)
        action_items.append(f"[论文] 精读: {t[:80]} (IF={p.get('impact_factor', 'N/A')})")
    for p in current_patents[:3]:
        t = p.get('title', '') or ''
        t = t if isinstance(t, str) else str(t)
        action_items.append(f"[专利] 关注: {t[:80]}")
    for s in scholar_updates:
        if s["found"] and s["info"].get("is_high_cited"):
            action_items.append(
                f"[学者] 重点追踪: {s['info']['name_en']} (高被引学者, h={s['info']['h_index']})"
            )
    report["action_items"] = action_items

    # ---- 统计摘要 ----
    report["summary"]["total_papers"] = new_paper_count
    report["summary"]["total_patents"] = new_patent_count
    report["summary"]["total_news"] = new_news_count
    report["summary"]["scholars_tracked"] = len([s for s in scholar_updates if s["found"]])

    return report


# 执行：生成报告
report = incremental_analysis(all_papers, all_patents, all_news, scholar_updates, baseline)
```

### 第八步：格式化输出报告

```python
def format_report(report):
    """将报告格式化为可读文本"""
    lines = []
    lines.append("=" * 60)
    lines.append("  竞品技术监控报告 (Tech Radar)")
    lines.append("=" * 60)
    lines.append(f"生成时间: {report['generated_at']}")
    lines.append(f"监控窗口: {report['time_window']}")
    lines.append("")

    # 统计概览
    s = report["summary"]
    lines.append("## 统计概览")
    lines.append(f"  - 论文: {s.get('total_papers', 0)} 篇")
    lines.append(f"  - 专利: {s.get('total_patents', 0)} 条")
    lines.append(f"  - 新闻: {s.get('total_news', 0)} 条")
    lines.append(f"  - 追踪学者: {s.get('scholars_tracked', 0)} 位")
    if "vs_baseline" in s:
        vs = s["vs_baseline"]
        lines.append(f"  - 与上次对比: 论文 {vs['paper_delta']:+d}, 专利 {vs['patent_delta']:+d}")
    lines.append("")

    # 趋势判断
    lines.append("## 趋势判断")
    lines.append(f"  {report['trend']}")
    lines.append("")

    # 影响评估
    lines.append("## 影响评估")
    lines.append(f"  {report['impact_assessment']}")
    lines.append("")

    # 建议关注项
    if report["action_items"]:
        lines.append("## 建议关注项")
        for item in report["action_items"]:
            lines.append(f"  - {item}")
        lines.append("")

    # 论文列表
    papers = report["new_activities"]["papers"]
    if papers:
        lines.append(f"## 最新论文 (共 {len(papers)} 篇)")
        for i, p in enumerate(papers[:10], 1):
            t = p.get('title', '') or ''
            t = t if isinstance(t, str) else str(t)
            lines.append(f"  {i}. {t[:100]}")
            lines.append(f"     期刊: {p.get('journal', 'N/A')} | 日期: {p.get('date', 'N/A')} "
                         f"| 引用: {p.get('citations', 0)} | IF: {p.get('impact_factor', 0)}")
        if len(papers) > 10:
            lines.append(f"  ... 及其余 {len(papers) - 10} 篇")
        lines.append("")

    # 专利列表
    patents = report["new_activities"]["patents"]
    if patents:
        lines.append(f"## 最新专利 (共 {len(patents)} 条)")
        for i, p in enumerate(patents[:10], 1):
            t = p.get('title', '') or ''
            t = t if isinstance(t, str) else str(t)
            lines.append(f"  {i}. {t[:100]}")
            lines.append(f"     申请人: {p.get('applicant', 'N/A')} | 日期: {p.get('date', 'N/A')}")
        if len(patents) > 10:
            lines.append(f"  ... 及其余 {len(patents) - 10} 条")
        lines.append("")

    # 新闻列表
    news = report["new_activities"]["news"]
    if news:
        lines.append(f"## 最新新闻 (共 {len(news)} 条)")
        for i, n in enumerate(news[:10], 1):
            t = n.get('title', '') or ''
            t = t if isinstance(t, str) else str(t)
            lines.append(f"  {i}. {t[:100]}")
            lines.append(f"     {n.get('url', '')}")
            snippet = n.get('snippet', '') or ''
            lines.append(f"     {snippet[:150]}")
        lines.append("")

    # 学者动态
    scholars = report.get("scholar_status", [])
    tracked = [s for s in scholars if s["found"]]
    if tracked:
        lines.append(f"## 学者动态 (共追踪 {len(tracked)} 位)")
        for s in tracked:
            info = s["info"]
            lines.append(f"  - {info['name_en']} ({info.get('org', 'N/A')})")
            lines.append(f"    论文: {info['paper_count']} | 引用: {info['citation_count']} "
                         f"| h-index: {info['h_index']}"
                         + (" | 高被引学者" if info.get("is_high_cited") else ""))
            if info.get("research_direction"):
                lines.append(f"    研究方向: {', '.join(info['research_direction'][:5])}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# 执行：输出报告
report_text = format_report(report)
print(report_text)
```

### 第九步：存储基线到知识库（可选）

```python
def save_baseline_to_kb(report, kb_node_id):
    """将本次报告作为基线存入知识库，供下次增量对比"""
    if not kb_node_id:
        print("[基线] 未配置知识库，跳过基线存储")
        return

    import hashlib
    import tempfile
    import base64
    import urllib.request

    # 将报告 JSON 写入临时文件
    report_json = json.dumps(report, ensure_ascii=False, indent=2)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"tech-radar-baseline-{timestamp}.json"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        f.write(report_json)
        tmp_path = f.name

    try:
        file_size = os.path.getsize(tmp_path)

        # 计算 MD5
        h = hashlib.md5()
        with open(tmp_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        file_md5 = h.hexdigest()

        # 获取上传凭证
        r = requests.get(
            f"{BASE_KB}/file/multipart",
            headers=HEADERS,
            params={
                "fileName": file_name,
                "md5": file_md5,
                "parentId": kb_node_id,
                "size": file_size,
            },
            timeout=30,
        )
        r.raise_for_status()
        mp_data = r.json().get("data", {})

        if mp_data.get("fileExist"):
            # 文件已存在，直接注册
            r_sub = requests.post(
                f"{BASE_KB}/file/submit",
                headers=HEADERS_JSON,
                json={
                    "parentId": kb_node_id,
                    "fileName": file_name,
                    "md5": file_md5,
                    "size": file_size,
                    "url": mp_data.get("path", ""),
                },
                timeout=30,
            )
            print(f"[基线] 文件已存在，注册结果: {r_sub.json().get('code')}")
            return

        host = mp_data["host"]
        path = mp_data["path"]
        token = mp_data["token"]

        # 二进制上传
        content_type = "application/json; charset=utf-8"
        encoded_file_name = urllib.parse.quote(file_name, safe="-_.!~*'()")
        storage_param = base64.b64encode(json.dumps({
            "path": path,
            "option": {
                "contentDisposition": (
                    f'inline; filename="{encoded_file_name}"; '
                    f"filename*=UTF-8''{encoded_file_name}"
                ),
                "contentType": content_type,
            },
        }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).decode("utf-8")

        file_content = open(tmp_path, "rb").read()
        upload_url = host.rstrip("/") + "/api/upload/binary"

        req = urllib.request.Request(upload_url, method="POST", data=file_content)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("X-Storage-Param", storage_param)
        req.add_header("Content-Type", "application/octet-stream")

        with urllib.request.urlopen(req, timeout=300) as resp:
            upload_result = json.loads(resp.read().decode("utf-8"))

        final_path = (upload_result.get("data") or {}).get("path") or path

        # 注册到知识库
        r_sub = requests.post(
            f"{BASE_KB}/file/submit",
            headers=HEADERS_JSON,
            json={
                "parentId": kb_node_id,
                "fileName": file_name,
                "md5": file_md5,
                "size": file_size,
                "url": final_path,
            },
            timeout=30,
        )
        result = r_sub.json()
        if result.get("code") == 0:
            print(f"[基线] 成功存储到知识库: {file_name}")
        else:
            print(f"[基线] 存储失败: {result}")

    finally:
        os.unlink(tmp_path)


# 执行：存储基线
save_baseline_to_kb(report, MONITOR_CONFIG.get("knowledge_base_node_id"))
```

---

## 周期化运行

将上述脚本保存为 `tech_radar_monitor.py`，可通过 cron 或定时任务周期执行：

```bash
# 每周一早上 9 点执行一次监控
# crontab -e
0 9 * * 1 cd /path/to/project && ACCESS_KEY="your_key" python3 tech_radar_monitor.py >> tech_radar.log 2>&1
```

也可结合飞书消息推送，将报告自动发送到指定群聊（使用 `lark-im` 技能）。

---

## 与基线对比的详细示例

以下示例展示如何从知识库读取上一次的基线，与本次采集结果做精细对比：

```python
def detailed_baseline_comparison(current_report, baseline_content):
    """精细化基线对比，找出新增、消失、变化的条目"""
    try:
        prev = json.loads(baseline_content)
    except (json.JSONDecodeError, TypeError):
        return {"error": "无法解析基线内容"}

    prev_papers = {p["doi"]: p for p in prev.get("new_activities", {}).get("papers", []) if p.get("doi")}
    curr_papers = {p["doi"]: p for p in current_report["new_activities"]["papers"] if p.get("doi")}

    prev_patents = set()
    for p in prev.get("new_activities", {}).get("patents", []):
        pid = p.get("patent_id", p.get("title", ""))
        if pid:
            prev_patents.add(pid)

    curr_patents = set()
    for p in current_report["new_activities"]["patents"]:
        pid = p.get("patent_id", p.get("title", ""))
        if pid:
            curr_patents.add(pid)

    # 新增论文 = 本次有但上次没有
    new_paper_dois = set(curr_papers.keys()) - set(prev_papers.keys())
    # 消失论文 = 上次有但本次没有（可能时间窗口滑动导致）
    gone_paper_dois = set(prev_papers.keys()) - set(curr_papers.keys())

    new_patent_ids = curr_patents - prev_patents

    # 学者指标变化
    scholar_changes = []
    prev_scholars = {s["name"]: s for s in prev.get("scholar_status", []) if s.get("found")}
    for s in current_report.get("scholar_status", []):
        if not s.get("found"):
            continue
        name = s["name"]
        if name in prev_scholars:
            prev_info = prev_scholars[name].get("info", {})
            curr_info = s.get("info", {})
            paper_diff = curr_info.get("paper_count", 0) - prev_info.get("paper_count", 0)
            cite_diff = curr_info.get("citation_count", 0) - prev_info.get("citation_count", 0)
            if paper_diff != 0 or cite_diff != 0:
                scholar_changes.append({
                    "name": name,
                    "paper_delta": paper_diff,
                    "citation_delta": cite_diff,
                })

    comparison = {
        "new_papers": [curr_papers[d] for d in new_paper_dois],
        "gone_papers_count": len(gone_paper_dois),
        "new_patents_count": len(new_patent_ids),
        "scholar_changes": scholar_changes,
    }

    print(f"[对比] 新增论文 {len(new_paper_dois)} 篇, "
          f"滑出窗口 {len(gone_paper_dois)} 篇, "
          f"新增专利 {len(new_patent_ids)} 条")
    for sc in scholar_changes:
        print(f"[对比] 学者 {sc['name']}: 论文 {sc['paper_delta']:+d}, 引用 {sc['citation_delta']:+d}")

    return comparison


# 使用示例
if baseline and baseline.get("content"):
    comparison = detailed_baseline_comparison(report, baseline["content"])
```

---

## curl 示例

```bash
AK="$ACCESS_KEY"

# 论文检索
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{"words":["large language model"],"question":"latest advances in large language models","type":5,"startTime":"2024-12-01","endTime":"2025-01-01","pageSize":10}'

# 专利检索
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/patent" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{"keyword":"large language model","page":1,"pageSize":10}'

# 学者搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper-server/scholar/search" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{"name":"Yann LeCun","page":1,"pageSize":3}'

# 学者详情
curl -s "https://open.bohrium.com/openapi/v1/paper-server/scholar/info?scholarId=SCHOLAR_ID" \
  -H "accessKey: $AK"

# Web 搜索
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=DeepMind+latest+research&num=5" \
  -H "accessKey: $AK"

# 知识库文献搜索（读取基线）
curl -s -X POST "https://open.bohrium.com/openapi/v1/knowledge/file/search" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{"queryContent":"tech-radar baseline report","nodesId":123,"knowledgeBaseId":456}'
```

---

## 搭配使用

- **bohrium-paper-search** — 本技能的论文/专利检索能力来源
- **bohrium-scholar-search** — 本技能的学者追踪能力来源
- **bohrium-web-search** — 本技能的新闻搜索能力来源
- **bohrium-knowledge-base** — 存储历史基线，支持增量对比
- **bohrium-pdf-parser** — 对关键论文做全文解析，深入分析
- **lark-im** — 将监控报告推送到飞书群聊
- **lark-mail** — 将监控报告通过飞书邮箱发送

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `ACCESS_KEY` 为空 | OpenClaw 未注入环境变量 | 检查 `~/.openclaw/openclaw.json` 中 `tech-radar.env.ACCESS_KEY` 是否填入 |
| 401 Unauthorized | accessKey 无效或过期 | 更新 `~/.openclaw/openclaw.json` 中的 AccessKey 并重启会话 |
| 论文检索结果为空 | 关键词太窄或时间范围太短 | 放宽关键词、扩大时间窗口、去掉 JCR 分区限制 |
| 专利检索返回格式异常 | 专利接口不支持 `type`/`rerank` 等参数 | 只传 `keyword`、`page`、`pageSize` 三个参数 |
| 学者搜索无结果 | 姓名拼写不匹配或姓名过长 | 使用标准英文拼写，控制在 1-99 字符 |
| 基线对比无效果 | 知识库中无历史报告 | 首次运行时无基线可对比，第二次运行即可看到增量变化 |
| 网络超时 | 某个 API 响应慢 | 脚本已设置 30 秒超时并捕获异常，单个失败不影响整体流程 |
| 报告数据量过大 | 监控目标过多或时间窗口太宽 | 减少目标数量、缩短时间窗口、降低 `pageSize` |
| 知识库上传失败 | 存储服务异常或凭证过期 | 检查知识库 ID 是否正确，重试一次 |
