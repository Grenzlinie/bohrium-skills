---
name: frontier-alert
description: "Research frontier early warning by detecting citation acceleration, new cross-domain connections, and emerging workshop topics. Use when: user wants to discover potentially emerging research directions before they become mainstream. NOT for: known-topic monitoring (use tech-radar), literature review (use literature-review)."
---

# SKILL: 研究前沿预警 (Frontier Alert)

## 概述

研究前沿预警是一个**编排型 Skill**，串联多个 Bohrium 原子技能，通过三条独立的信号通道检测潜在新兴研究方向：

1. **引用加速异常** — 识别近 6-12 个月内引用数飙升的论文
2. **跨领域新连接** — 利用知识图谱检测尚未被充分研究的跨域关联
3. **新兴会议/资助信号** — 搜索顶会新增 workshop 和新设基金项目

**编排流程：**

```
输入: 关注领域 (1-3 个), 预警灵敏度 (conservative / aggressive)
  │
  ├─ 1. paper-search   → 检测近期高引论文（引用加速异常）
  ├─ 2. lkm            → 检测知识图谱中的新跨域连接
  └─ 3. web-search     → 搜索顶会新 workshop、新基金公告
  │
  ▼
  输出: 信号列表，每条含描述 / 证据来源 / 置信度 / 建议动作
```

**适用场景：**

- 提前捕捉即将爆发的研究热点
- 发现跨学科交叉创新机会
- 追踪新设立的会议 workshop 和基金方向

**不适用：**

- 已知主题的竞品监控 → 用 `tech-radar`
- 已知主题的文献综述 → 用 `literature-review`
- 单次论文检索 → 用 `bohrium-paper-search`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"frontier-alert": {
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
| `focus_areas` | list[str] | 是 | — | 关注领域，1-3 个，如 `["perovskite solar cells", "solid-state batteries"]` |
| `sensitivity` | string | 否 | `"conservative"` | 预警灵敏度：`"conservative"`（高置信信号优先）/ `"aggressive"`（宁多勿漏） |

### 灵敏度说明

| 模式 | 引用加速阈值 | LKM 新论断门槛 | web-search 查询数 |
|------|-------------|---------------|-------------------|
| `conservative` | 引用 >= 20 且 Q1 期刊 | 仅 `new_claim_likely=true` | 每领域 2 条查询 |
| `aggressive` | 引用 >= 5 不限分区 | 包含 `new_claim_likely=true` 和弱证据 | 每领域 4 条查询 |

---

## 输出格式

每条预警信号包含以下字段：

| 字段 | 说明 |
|------|------|
| `signal_id` | 信号编号 |
| `channel` | 信号来源通道：`citation_acceleration` / `cross_domain_connection` / `emerging_venue` |
| `description` | 信号描述（一句话概括） |
| `evidence` | 证据来源列表（论文 DOI、知识图谱节点、网页 URL 等） |
| `confidence` | 置信度评估：`high` / `medium` / `low` |
| `action` | 建议动作：`watch`（持续关注）/ `dive-in`（深入调研）/ `ignore`（可忽略） |

---

## 信号质量控制

### 引用加速度检测（避免时效偏差）

检测"引用加速"信号时，**不能仅按总引用数排序**，必须计算引用速度：

```
引用速度 = 总引用数 / 发表至今月数
加速度 = 近 6 月月均引用 / 总体月均引用
```

- **加速度 > 2.0** 且近 6 月引用 > 10：`high` confidence 加速信号
- **加速度 1.5-2.0**：`medium` confidence
- **加速度 < 1.5**：不作为加速信号报告

### 信号去噪规则

以下情况**不应**作为前沿信号报告：
- 综述论文的引用增长（综述被引高是正常的，不代表前沿突破）
- 仅因为新发表而引用数低的论文（新 ≠ 前沿）
- 与用户监控方向关联度低的跨领域信号（除非明确标注为"跨领域启发"）

### 可操作性要求

每条信号的 `action` 建议必须附带具体理由：
- `dive-in`：必须说明"为什么值得深入"——如"该方法可能直接应用于你的 X 问题"
- `watch`：必须说明"关注什么指标来判断是否需要行动"
- `ignore`：必须说明"为什么可以暂时忽略"

---

## 通用代码模板

```python
import os
import sys
import json
import requests
from datetime import datetime, timedelta

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("ERROR: ACCESS_KEY 未配置。")
    print("请在 ~/.openclaw/openclaw.json 中配置 frontier-alert.env.ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET = {"accessKey": AK}

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
```

---

## 完整编排脚本

以下脚本实现端到端的研究前沿预警流程。

```python
#!/usr/bin/env python3
"""
研究前沿预警 (Frontier Alert) — 完整编排脚本

用法:
    export ACCESS_KEY="your_access_key"
    python3 frontier_alert.py

可修改下方 CONFIG 区域的参数来调整关注领域和灵敏度。
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from collections import Counter

# ============================================================
# 配置
# ============================================================

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("ERROR: 请设置环境变量 ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_GET = {"accessKey": AK}

# -- 用户可修改区域 --
CONFIG = {
    "focus_areas": [
        "perovskite solar cells",
        "solid-state electrolyte",
    ],
    "sensitivity": "conservative",   # "conservative" 或 "aggressive"
}

# 灵敏度参数映射
SENSITIVITY_PARAMS = {
    "conservative": {
        "citation_threshold": 20,
        "jcr_zones": ["Q1"],
        "include_weak_evidence": False,
        "web_queries_per_area": 2,
        "paper_page_size": 20,
    },
    "aggressive": {
        "citation_threshold": 5,
        "jcr_zones": [],
        "include_weak_evidence": True,
        "web_queries_per_area": 4,
        "paper_page_size": 30,
    },
}

params = SENSITIVITY_PARAMS[CONFIG["sensitivity"]]

# ============================================================
# 辅助函数
# ============================================================

def safe_request(method, url, **kwargs):
    """带错误处理的请求封装"""
    try:
        r = requests.request(method, url, timeout=30, **kwargs)
        r.raise_for_status()
        text = r.text.strip()
        first_line = text.split('\n')[0]
        return json.loads(first_line)
    except requests.exceptions.Timeout:
        print(f"  [WARN] 请求超时: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"  [WARN] HTTP 错误 {e.response.status_code}: {url}")
        return None
    except Exception as e:
        print(f"  [WARN] 请求异常: {e}")
        return None


def assess_confidence(citation_count, impact_factor, jcr_zone):
    """基于引用数、影响因子和 JCR 分区评估信号置信度"""
    score = 0
    if citation_count >= 50:
        score += 3
    elif citation_count >= 20:
        score += 2
    elif citation_count >= 5:
        score += 1

    if impact_factor >= 10:
        score += 2
    elif impact_factor >= 5:
        score += 1

    if jcr_zone in ("Q1",):
        score += 1

    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    return "low"


def suggest_action(confidence, channel):
    """根据置信度和信号通道推荐动作"""
    if confidence == "high":
        return "dive-in"
    elif confidence == "medium":
        return "watch"
    else:
        return "ignore"


# ============================================================
# 信号容器
# ============================================================

signals = []
signal_counter = 0


def add_signal(channel, description, evidence, confidence, action):
    """添加一条预警信号"""
    global signal_counter
    signal_counter += 1
    signals.append({
        "signal_id": signal_counter,
        "channel": channel,
        "description": description,
        "evidence": evidence,
        "confidence": confidence,
        "action": action,
    })


# ============================================================
# Step 1: 引用加速异常检测 (paper-search)
# ============================================================

print("=" * 60)
print("Step 1: 检测引用加速异常 — 近 6-12 个月高引论文")
print("=" * 60)

now = datetime.now()

# 搜索两个时间窗口：6 个月和 12 个月，用于对比加速度
windows = [
    ("近 6 个月", (now - timedelta(days=180)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")),
    ("近 12 个月", (now - timedelta(days=365)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")),
]

for area in CONFIG["focus_areas"]:
    print(f"\n  领域: {area}")
    keywords = [w.strip() for w in area.split() if len(w.strip()) > 2]

    for window_label, start_time, end_time in windows:
        print(f"    时间窗口: {window_label} ({start_time} ~ {end_time})")

        data = safe_request("POST", f"{BASE}/v1/paper/rag/pass/keyword",
            headers=HEADERS_JSON,
            json={
                "words": keywords,
                "question": f"Recent breakthroughs and emerging trends in {area}",
                "type": 5,
                "startTime": start_time,
                "endTime": end_time,
                "jcrZones": params["jcr_zones"],
                "pageSize": params["paper_page_size"],
            }
        )

        if not data or data.get("code") != 0:
            print(f"    [WARN] 检索未返回有效数据")
            continue

        papers = data.get("data", [])
        # 按引用数降序排列
        papers.sort(key=lambda p: p.get("citationNums", 0), reverse=True)

        # 筛选引用数超过阈值的论文
        hot_papers = [
            p for p in papers
            if p.get("citationNums", 0) >= params["citation_threshold"]
        ]

        print(f"    检索到 {len(papers)} 篇论文，其中 {len(hot_papers)} 篇"
              f"引用 >= {params['citation_threshold']}")

        for p in hot_papers[:5]:
            # 计算引用加速度：短时间内获得高引用 = 加速信号
            pub_date = p.get("coverDateStart", "")
            citations = p.get("citationNums", 0)
            impact_factor = p.get("impactFactor", 0)
            jcr = ""
            if impact_factor >= 10:
                jcr = "Q1"

            # 计算论文年龄（月）
            try:
                pub_dt = datetime.strptime(pub_date[:10], "%Y-%m-%d")
                age_months = max(1, (now - pub_dt).days / 30)
                citations_per_month = citations / age_months
            except (ValueError, TypeError):
                age_months = 12
                citations_per_month = citations / 12

            # 月均引用 >= 5 视为加速信号
            acceleration_threshold = 5 if CONFIG["sensitivity"] == "aggressive" else 10
            if citations_per_month >= acceleration_threshold:
                confidence = assess_confidence(citations, impact_factor, jcr)
                action = suggest_action(confidence, "citation_acceleration")

                add_signal(
                    channel="citation_acceleration",
                    description=(
                        f"[{area}] 引用加速: \"{p.get('enName', '')[:80]}\" "
                        f"发表 {age_months:.0f} 个月已获 {citations} 次引用 "
                        f"(月均 {citations_per_month:.1f})"
                    ),
                    evidence=[{
                        "type": "paper",
                        "doi": p.get("doi", ""),
                        "title": p.get("enName", ""),
                        "journal": p.get("publicationEnName", ""),
                        "citations": citations,
                        "impact_factor": impact_factor,
                        "date": pub_date,
                    }],
                    confidence=confidence,
                    action=action,
                )
                print(f"      [SIGNAL] {p.get('enName', '')[:60]}... "
                      f"(月均引用 {citations_per_month:.1f}, 置信度 {confidence})")


# ============================================================
# Step 2: 跨领域新连接检测 (LKM)
# ============================================================

print("\n" + "=" * 60)
print("Step 2: 检测知识图谱中的新跨域连接")
print("=" * 60)

for area in CONFIG["focus_areas"]:
    print(f"\n  领域: {area}")

    # Step 2a: 知识图谱搜索 — 获取已知概念网络
    print("    2a. 知识图谱搜索...")
    kg_data = safe_request("POST", f"{BASE}/v1/lkm/search",
        headers=HEADERS_JSON,
        json={
            "query": f"emerging connections and novel relationships in {area}",
            "limit": 10,
        }
    )

    kg_nodes = []
    if kg_data and kg_data.get("data"):
        kg_nodes = kg_data["data"] if isinstance(kg_data["data"], list) else [kg_data["data"]]
        print(f"      找到 {len(kg_nodes)} 个知识节点")

    # Step 2b: 论断匹配 — 构造跨域假说进行检测
    print("    2b. 论断匹配（跨域连接检测）...")

    # 构造跨域假说：将当前领域与常见交叉方向组合
    cross_domain_claims = [
        f"Machine learning methods can significantly accelerate discovery in {area}",
        f"High-throughput screening combined with {area} enables rapid materials optimization",
        f"Transfer learning from related domains improves prediction accuracy in {area}",
        f"Autonomous experimentation platforms can optimize {area} research workflows",
    ]

    for claim in cross_domain_claims:
        result = safe_request("POST", f"{BASE}/v1/lkm/claims/match",
            headers=HEADERS_JSON,
            json={
                "text": claim,
                "limit": 5,
            }
        )

        if not result or not result.get("data"):
            continue

        match_data = result["data"]
        new_claim = match_data.get("new_claim_likely", False)
        variables = match_data.get("variables", [])
        match_count = len(variables)

        # 判断信号强度
        is_signal = False
        if new_claim:
            is_signal = True
            confidence = "medium"
            detail = "知识图谱中缺乏相关证据，可能是尚未被探索的跨域连接"
        elif params["include_weak_evidence"] and match_count < 3:
            is_signal = True
            confidence = "low"
            detail = f"仅匹配 {match_count} 条证据，该跨域连接可能有拓展空间"

        if is_signal:
            action = suggest_action(confidence, "cross_domain_connection")
            evidence_list = [{
                "type": "lkm_claim",
                "claim_text": claim,
                "new_claim_likely": new_claim,
                "match_count": match_count,
            }]
            # 附加匹配到的已有证据
            for v in variables[:3]:
                evidence_list.append({
                    "type": "lkm_variable",
                    "role": v.get("role", ""),
                    "content": v.get("content", "")[:200],
                })

            add_signal(
                channel="cross_domain_connection",
                description=(
                    f"[{area}] 跨域新连接: {claim[:100]}... "
                    f"({'新论断' if new_claim else f'弱证据({match_count}条)'})"
                ),
                evidence=evidence_list,
                confidence=confidence,
                action=action,
            )
            tag = "NEW_CLAIM" if new_claim else "WEAK_EVIDENCE"
            print(f"      [{tag}] {claim[:60]}... (置信度 {confidence})")
        else:
            print(f"      [已知] {claim[:60]}... ({match_count} 条证据)")


# ============================================================
# Step 3: 新兴会议与资助信号检测 (web-search)
# ============================================================

print("\n" + "=" * 60)
print("Step 3: 搜索顶会新 workshop 和新基金公告")
print("=" * 60)

current_year = now.year

for area in CONFIG["focus_areas"]:
    print(f"\n  领域: {area}")

    # 构造搜索查询
    web_queries = [
        f"{area} new workshop {current_year} call for papers",
        f"{area} emerging research funding {current_year}",
    ]

    # aggressive 模式增加更多查询
    if params["web_queries_per_area"] >= 4:
        web_queries.extend([
            f"{area} special issue call {current_year}",
            f"{area} new conference track {current_year}",
        ])

    for q in web_queries:
        print(f"    搜索: {q[:50]}...")
        data = safe_request("GET", f"{BASE}/v1/search/web",
            headers=HEADERS_GET,
            params={"q": q, "num": 5}
        )

        if not data or not data.get("organic_results"):
            print(f"      无结果")
            continue

        for hit in data["organic_results"][:3]:
            title = hit.get("title", "")
            snippet = hit.get("snippet", "")
            link = hit.get("link", "")

            # 检测是否包含 workshop / funding / call for papers 等关键词
            combined = (title + " " + snippet).lower()
            venue_keywords = ["workshop", "symposium", "call for papers",
                              "special issue", "new track", "inaugural"]
            funding_keywords = ["funding", "grant", "award", "call for proposals",
                                "research program", "initiative"]

            is_venue_signal = any(kw in combined for kw in venue_keywords)
            is_funding_signal = any(kw in combined for kw in funding_keywords)

            if is_venue_signal or is_funding_signal:
                signal_type = "会议/workshop" if is_venue_signal else "基金/资助"
                confidence = "medium" if is_venue_signal and is_funding_signal else "low"
                # 如果标题中直接包含当前年份，提高置信度
                if str(current_year) in title:
                    confidence = "medium"
                action = suggest_action(confidence, "emerging_venue")

                add_signal(
                    channel="emerging_venue",
                    description=(
                        f"[{area}] 新兴{signal_type}: {title[:80]}"
                    ),
                    evidence=[{
                        "type": "web",
                        "title": title,
                        "url": link,
                        "snippet": snippet[:300],
                    }],
                    confidence=confidence,
                    action=action,
                )
                print(f"      [SIGNAL] [{signal_type}] {title[:60]}... (置信度 {confidence})")
            else:
                print(f"      [跳过] {title[:60]}...")


# ============================================================
# 汇总报告
# ============================================================

print("\n" + "=" * 60)
print("研究前沿预警报告")
print("=" * 60)

print(f"\n生成时间: {now.isoformat()}")
print(f"关注领域: {', '.join(CONFIG['focus_areas'])}")
print(f"预警灵敏度: {CONFIG['sensitivity']}")
print(f"信号总数: {len(signals)}")

# 按通道统计
channel_counts = Counter(s["channel"] for s in signals)
print(f"\n  引用加速异常: {channel_counts.get('citation_acceleration', 0)} 条")
print(f"  跨域新连接:   {channel_counts.get('cross_domain_connection', 0)} 条")
print(f"  新兴会议/资助: {channel_counts.get('emerging_venue', 0)} 条")

# 按置信度统计
conf_counts = Counter(s["confidence"] for s in signals)
print(f"\n  高置信度: {conf_counts.get('high', 0)} 条")
print(f"  中置信度: {conf_counts.get('medium', 0)} 条")
print(f"  低置信度: {conf_counts.get('low', 0)} 条")

# 按动作统计
action_counts = Counter(s["action"] for s in signals)
print(f"\n  建议深入 (dive-in): {action_counts.get('dive-in', 0)} 条")
print(f"  建议关注 (watch):   {action_counts.get('watch', 0)} 条")
print(f"  可忽略 (ignore):    {action_counts.get('ignore', 0)} 条")

# 按优先级排序输出详细信号
priority_order = {"high": 0, "medium": 1, "low": 2}
sorted_signals = sorted(signals, key=lambda s: priority_order.get(s["confidence"], 99))

print(f"\n{'─' * 60}")
print("详细信号列表（按置信度排序）")
print(f"{'─' * 60}")

for s in sorted_signals:
    print(f"\n  [{s['signal_id']:02d}] [{s['confidence'].upper():6s}] [{s['action']:7s}]")
    print(f"       通道: {s['channel']}")
    print(f"       描述: {s['description']}")
    print(f"       证据:")
    for ev in s["evidence"][:3]:
        if ev["type"] == "paper":
            print(f"         - 论文: {ev.get('title', '')[:60]}...")
            print(f"           DOI: {ev.get('doi', 'N/A')}, "
                  f"引用: {ev.get('citations', 0)}, "
                  f"IF: {ev.get('impact_factor', 0)}")
        elif ev["type"] == "lkm_claim":
            print(f"         - LKM 论断: {ev.get('claim_text', '')[:60]}...")
            print(f"           new_claim_likely: {ev.get('new_claim_likely')}, "
                  f"匹配数: {ev.get('match_count', 0)}")
        elif ev["type"] == "web":
            print(f"         - 网页: {ev.get('title', '')[:60]}...")
            print(f"           URL: {ev.get('url', '')}")

print(f"\n{'=' * 60}")
print("预警完成。建议优先跟进 dive-in 信号，定期复查 watch 信号。")
print("=" * 60)

# 输出 JSON 格式（便于程序化消费）
output_file = f"frontier_alert_{now.strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": now.isoformat(),
        "config": CONFIG,
        "sensitivity_params": params,
        "signal_count": len(signals),
        "signals": signals,
    }, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存到: {output_file}")
```

---

## 分步说明

### Step 1: 引用加速异常检测 (paper-search)

**目标：** 找出近 6-12 个月内引用数异常增长的论文，这类论文往往是新兴研究方向的早期标志。

**API 调用：**

```python
POST https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword
Header: accessKey: $ACCESS_KEY, Content-Type: application/json
Body: {
    "words": ["perovskite", "solar", "cells"],
    "question": "Recent breakthroughs and emerging trends in perovskite solar cells",
    "type": 5,
    "startTime": "2025-11-13",
    "endTime": "2026-05-13",
    "jcrZones": ["Q1"],
    "pageSize": 20
}
```

**关键指标：**

| 指标 | 计算方式 | 意义 |
|------|---------|------|
| 月均引用 | `citationNums / 论文年龄（月）` | 引用加速度，越高越可能是新兴热点 |
| 引用数 | `citationNums` | 绝对影响力 |
| 影响因子 | `impactFactor` | 期刊质量，高 IF 期刊的新方向更可信 |

**引用加速度判定逻辑：**

```python
# 论文年龄（月）
age_months = (now - pub_date).days / 30

# 月均引用
citations_per_month = citationNums / age_months

# conservative 模式：月均 >= 10 触发信号
# aggressive 模式：月均 >= 5 触发信号
```

### Step 2: 跨领域新连接检测 (LKM)

**目标：** 利用大知识模型的知识图谱，检测跨学科连接中是否存在尚未被充分研究的新关联。

**API 调用：**

```python
# 2a. 知识图谱搜索
POST https://open.bohrium.com/openapi/v1/lkm/search
Body: {
    "query": "emerging connections and novel relationships in perovskite solar cells",
    "limit": 10
}

# 2b. 论断匹配 — 检测跨域假说
POST https://open.bohrium.com/openapi/v1/lkm/claims/match
Body: {
    "text": "Machine learning methods can significantly accelerate discovery in perovskite solar cells",
    "limit": 5
}
```

**`new_claim_likely` 信号解读：**

| 返回值 | 含义 | 预警信号 |
|--------|------|---------|
| `true` | 知识图谱中缺乏该论断的支持/反驳证据 | **跨域新连接**——该方向尚未被充分探索 |
| `false` + 少量 variables (< 3) | 有少量相关证据但不充分 | **弱连接**——方向有基础但仍有空间（仅 aggressive 模式报告） |
| `false` + 大量 variables | 已有充分证据 | 已知连接，不产生信号 |

### Step 3: 新兴会议与资助信号 (web-search)

**目标：** 通过搜索新设 workshop、特刊征稿和新基金公告，捕捉学术社区正在组织化关注的新方向。

**API 调用：**

```python
GET https://open.bohrium.com/openapi/v1/search/web?q=QUERY&num=5
Header: accessKey: $ACCESS_KEY
```

**推荐搜索策略：**

```python
queries = [
    f"{area} new workshop {current_year} call for papers",    # 新 workshop
    f"{area} emerging research funding {current_year}",       # 新基金
    f"{area} special issue call {current_year}",              # 特刊征稿
    f"{area} new conference track {current_year}",            # 新会议 track
]
```

**信号过滤关键词：**

- 会议信号：`workshop`, `symposium`, `call for papers`, `special issue`, `new track`, `inaugural`
- 资助信号：`funding`, `grant`, `award`, `call for proposals`, `research program`, `initiative`

---

## curl 示例

```bash
AK="$ACCESS_KEY"

# Step 1: 引用加速异常 — 近 6 个月 Q1 高引论文
curl -s -X POST "https://open.bohrium.com/openapi/v1/paper/rag/pass/keyword" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "words": ["perovskite", "solar", "cells"],
    "question": "Recent breakthroughs and emerging trends in perovskite solar cells",
    "type": 5,
    "startTime": "2025-11-13",
    "endTime": "2026-05-13",
    "jcrZones": ["Q1"],
    "pageSize": 20
  }'

# Step 2a: 知识图谱搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "emerging connections and novel relationships in perovskite solar cells",
    "limit": 10
  }'

# Step 2b: 论断匹配 — 跨域连接检测
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/claims/match" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning methods can significantly accelerate discovery in perovskite solar cells",
    "limit": 5
  }'

# Step 3: 新兴 workshop 搜索
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=perovskite+solar+cells+new+workshop+2026+call+for+papers&num=5" \
  -H "accessKey: $AK"

# Step 3: 新基金公告搜索
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=perovskite+solar+cells+emerging+research+funding+2026&num=5" \
  -H "accessKey: $AK"
```

---

## 搭配使用

- **frontier-alert** 发现信号 → **literature-review** 对高置信信号做深度综述
- **frontier-alert** 发现信号 → **topic-scout** 将信号转化为具体选题推荐
- **frontier-alert** 长期运行 → **tech-radar** 对确认的方向进行持续监控
- **bohrium-paper-search** — 本技能的引用加速检测能力来源
- **bohrium-lkm** — 本技能的跨域连接检测能力来源
- **bohrium-web-search** — 本技能的会议/资助信号检测能力来源

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `ACCESS_KEY` 为空 | OpenClaw 未注入环境变量 | 检查 `~/.openclaw/openclaw.json` 中 `frontier-alert.env.ACCESS_KEY` 是否填入 |
| 401 Unauthorized | accessKey 无效或过期 | 更新 `~/.openclaw/openclaw.json` 中的 AccessKey 并重启会话 |
| 引用加速信号为零 | 领域较冷门或时间窗口内无异常论文 | 切换到 `aggressive` 模式降低阈值，或扩大时间窗口到 12 个月 |
| LKM 论断匹配全部返回 `false` | 论断太宽泛或领域研究已很成熟 | 构造更具体的跨域假说，包含明确的变量和方法 |
| LKM 论断匹配全部返回 `true` | 论断表述太新颖或太具体 | 适当泛化论断，使用领域通用术语 |
| web-search 无有效信号 | 关键词太专业或该领域尚无新设 workshop | 用更通俗的表述搜索，英文通常比中文命中率高 |
| 信号太多难以筛选 | `aggressive` 模式 + 多个关注领域 | 切换到 `conservative` 模式，或减少关注领域数量 |
| 某一步超时 | 后端负载高 | 脚本已内置超时处理，该步骤跳过不影响后续流程 |
| 重复运行结果相同 | 短期内数据库无更新 | 建议每 1-2 周运行一次，数据更新需要时间 |
