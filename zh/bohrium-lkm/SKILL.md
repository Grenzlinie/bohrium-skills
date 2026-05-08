---
name: bohrium-lkm
description: "Large Knowledge Model (LKM) via open.bohrium.com. Use when: user asks about searching scientific knowledge graphs, verifying claims with evidence, querying variable relationships, or batch OCR of papers. NOT for: general paper search (use bohrium-paper-search), knowledge base management (use bohrium-knowledge-base)."
---

# SKILL: Bohrium LKM (大知识模型)

## 概述

通过 `open.bohrium.com` 的 LKM (Large Knowledge Model) 端点，提供科学知识图谱搜索、论断验证与证据链追溯、变量关系批量查询、论文 OCR 批处理等能力。

**核心能力：**

| 端点 | 功能 |
|------|------|
| `/v1/lkm/search` | 知识图谱语义搜索 |
| `/v1/lkm/claims/match` | 论断匹配：输入一个科学论断，找到支持/反驳的证据 |
| `/v1/lkm/claims/:id/evidence` | 获取特定论断的证据链详情 |
| `/v1/lkm/variables/batch` | 批量查询变量关系（如：温度对催化活性的影响） |
| `/v1/lkm/papers/ocr/batch` | 批量论文 OCR（提取结构化内容） |

**适用场景：**

- 验证一个科学结论是否有文献支持
- 查找两个变量之间的关系（正相关/负相关/无关）
- 从知识图谱中搜索特定领域的知识节点
- 批量 OCR 论文获取结构化数据

**不适用：**

- 通用论文关键词搜索 → `bohrium-paper-search`
- 知识库文件管理 → `bohrium-knowledge-base`
- PDF 单篇解析 → `bohrium-pdf-parser`

**无 CLI 支持** — 通过 HTTP API 操作。

## 认证配置

```json
"bohrium-lkm": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

## 通用代码模板

```python
import os, requests

AK = os.environ["ACCESS_KEY"]
BASE = "https://open.bohrium.com/openapi/v1/lkm"
H = {"accessKey": AK, "Content-Type": "application/json"}
```

---

## 1. 知识图谱搜索 — `/lkm/search`

```python
r = requests.post(f"{BASE}/search", headers=H, json={
    "query": "effect of temperature on lithium ion battery degradation",
    "limit": 10
})
data = r.json()
print(data)
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 自然语言搜索查询 |
| `limit` | int | 否 | 最大返回数量 |

---

## 2. 论断匹配 — `/lkm/claims/match`

输入一个科学论断，系统返回支持或反驳该论断的已有证据。

```python
r = requests.post(f"{BASE}/claims/match", headers=H, json={
    "claim": "Graphene oxide improves the mechanical strength of concrete",
    "limit": 5
})
data = r.json()
for item in data.get("data", []):
    print(f"  Claim ID: {item['id']}")
    print(f"  Support: {item.get('support_level')}")
    print(f"  Source: {item.get('source')}")
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `claim` | string | 是 | 待验证的科学论断 |
| `limit` | int | 否 | 最大返回匹配数 |

---

## 3. 证据链查询 — `/lkm/claims/:id/evidence`

根据论断 ID 获取详细的证据链（来源论文、实验数据、推理路径）。

```python
claim_id = "abc123"
r = requests.get(f"{BASE}/claims/{claim_id}/evidence", headers=H)
data = r.json()
for ev in data.get("data", []):
    print(f"  Paper: {ev.get('paper_title')}")
    print(f"  Evidence: {ev.get('text')}")
    print(f"  Type: {ev.get('evidence_type')}")
```

---

## 4. 变量关系批量查询 — `/lkm/variables/batch`

查询多组变量之间的关系（如正相关、负相关、无关）。

```python
r = requests.post(f"{BASE}/variables/batch", headers=H, json={
    "pairs": [
        {"variable1": "temperature", "variable2": "reaction rate"},
        {"variable1": "pH", "variable2": "enzyme activity"},
        {"variable1": "pressure", "variable2": "boiling point"}
    ]
})
data = r.json()
for pair in data.get("data", []):
    print(f"  {pair['variable1']} vs {pair['variable2']}: {pair.get('relationship')}")
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pairs` | array | 是 | 变量对列表 |
| `pairs[].variable1` | string | 是 | 变量 1 |
| `pairs[].variable2` | string | 是 | 变量 2 |

---

## 5. 论文批量 OCR — `/lkm/papers/ocr/batch`

批量对论文进行 OCR 提取结构化内容。

```python
r = requests.post(f"{BASE}/papers/ocr/batch", headers=H, json={
    "paper_ids": ["doi:10.1038/s41586-021-03819-2", "doi:10.1126/science.abf3041"]
})
data = r.json()
for paper in data.get("data", []):
    print(f"  Paper: {paper.get('title')}")
    print(f"  Status: {paper.get('status')}")
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `paper_ids` | string[] | 是 | 论文标识列表（DOI 或内部 ID） |

---

## curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 知识图谱搜索
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"query":"lithium battery degradation mechanism","limit":10}' | jq .

# 论断匹配
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/claims/match" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"claim":"MoS2 is a promising catalyst for hydrogen evolution","limit":5}' | jq .

# 证据链
curl -s -X GET "https://open.bohrium.com/openapi/v1/lkm/claims/abc123/evidence" \
  -H "accessKey: $AK" | jq .

# 变量关系
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/variables/batch" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"pairs":[{"variable1":"temperature","variable2":"conductivity"}]}' | jq .

# 批量 OCR
curl -s -X POST "https://open.bohrium.com/openapi/v1/lkm/papers/ocr/batch" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"paper_ids":["doi:10.1038/s41586-021-03819-2"]}' | jq .
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| claims/match 无结果 | 论断描述太笼统 | 使用更具体的科学表述，包含变量和关系 |
| variables/batch 超时 | 变量对过多 | 分批提交，每批不超过 10 对 |
| OCR 状态 pending | 后端处理中 | 轮询结果或等待回调 |

## 搭配使用

- **lkm** 验证论断 → **paper-search** 找到原始论文全文
- **lkm** 查变量关系 → **mol-search** 查相关分子的结构
- **lkm** 批量 OCR → **knowledge-base** 存储提取结果
