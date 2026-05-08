---
name: bohrium-database
description: "Query scientific databases (materials structures, polymers, common data, molecular properties) via open.bohrium.com. Use when: user asks about querying material structures, phase diagrams, polymer data, common scientific datasets, or molecular property lookup. NOT for: molecule-in-paper search (use bohrium-mol-search), paper search (use bohrium-paper-search), knowledge base (use bohrium-knowledge-base)."
---

# SKILL: Bohrium 科学数据库查询

## 概述

通过 `open.bohrium.com` 的多个端点查询科学数据库，涵盖材料结构、高分子、通用科学数据集和分子属性。

**支持的数据源：**

| 端点前缀 | 数据类型 | 说明 |
|----------|----------|------|
| `/v1/structures/` | 材料结构 | 晶体结构查询、遍历、相图凸包 |
| `/v1/database/` | 通用数据 | 公共数据集列表、高分子数据 |
| `/v1/molecular/` | 分子属性 | 按名称/SMILES/InChI/分子式查分子属性数据 |

**适用场景：**

- 按化学式查询晶体结构及能量
- 获取某组成的相图凸包数据
- 浏览公共材料数据集
- 查询高分子材料列表
- 查询分子的属性/结构数据

**不适用：**

- 搜索含某分子的论文 → `bohrium-mol-search`
- 论文/专利搜索 → `bohrium-paper-search`
- 知识库文件管理 → `bohrium-knowledge-base`

**无 CLI 支持** — 通过 HTTP API 操作。

## 认证配置

```json
"bohrium-database": {
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
BASE = "https://open.bohrium.com/openapi/v1"
H = {"accessKey": AK, "Content-Type": "application/json"}
H_GET = {"accessKey": AK}
```

---

## 1. 材料结构查询 — `/structures/query`

按化学式分页查询材料结构数据（含结构、能量、描述符）。

```python
r = requests.get(f"{BASE}/structures/query", headers=H_GET, params={
    "formula": "Li2O",
    "page": 1,
    "pageSize": 20
})
data = r.json()
for s in data.get("data", {}).get("items", []):
    print(f"  Formula: {s['formula']}, Energy: {s['energy']}")
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `formula` | string | 是 | 化学式（如 `Li2O`, `Fe2O3`） |
| `page` | int | 否 | 页码，默认 1 |
| `pageSize` | int | 否 | 每页数量，默认 20 |

**返回字段：**

| 字段 | 说明 |
|------|------|
| `formula` | 化学式 |
| `structure` | 结构数据（通常为 JSON 或 POSCAR 格式） |
| `energy` | 能量值 (eV) |
| `descriptor` | 结构描述符 |
| `submissionTime` | 提交时间 |

---

## 2. 结构遍历 — `/structures/iterate`

游标方式遍历全部结构数据（适合批量导出）。

```python
start_id = 0
while True:
    r = requests.get(f"{BASE}/structures/iterate", headers=H_GET, params={
        "startId": start_id,
        "limit": 100
    })
    data = r.json().get("data", {})
    items = data.get("items", [])
    if not items:
        break
    for s in items:
        print(f"  [{s['id']}] {s['formula']} E={s['energy']}")
    start_id = data.get("nextStartId", 0)
    if start_id == 0:
        break
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `startId` | int | 否 | 起始 ID（首次传 0） |
| `limit` | int | 否 | 每批数量 |

---

## 3. 相图凸包查询 — `/structures/query_hull_by_composition/:composition`

按化学组成查询相图凸包数据（返回凸包图的 OSS 链接）。

```python
composition = "Li-Fe-O"
r = requests.get(f"{BASE}/structures/query_hull_by_composition/{composition}", headers=H_GET)
data = r.json()
print(f"  Hull URL: {data.get('data', {}).get('hull')}")
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `composition` (path) | string | 是 | 化学组成，元素用 `-` 连接（如 `Li-Fe-O`） |

---

## 4. 通用数据集列表 — `/database/common_data/list`

查询公共科学数据集。

```python
r = requests.post(f"{BASE}/database/common_data/list", headers=H, json={
    "page": 1,
    "pageSize": 20
})
data = r.json()
for item in data.get("data", {}).get("items", []):
    print(f"  {item.get('name')}: {item.get('description')}")
```

---

## 5. 高分子数据列表 — `/database/polymer/list`

查询高分子材料数据。

```python
r = requests.post(f"{BASE}/database/polymer/list", headers=H, json={
    "page": 1,
    "pageSize": 20
})
data = r.json()
for item in data.get("data", {}).get("items", []):
    print(f"  {item.get('name')}: {item.get('properties')}")
```

---

## 6. 分子属性查询 — `/molecular/search`

按分子名、SMILES、InChI 或分子式查询分子属性数据。

```python
r = requests.post(f"{BASE}/molecular/search", headers=H, json={
    "query": "aspirin",
    "page": 1,
    "pageSize": 10
})
data = r.json()
print(data)
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 分子名 / SMILES / InChI / 分子式 |
| `page` | int | 否 | 页码，默认 1 |
| `pageSize` | int | 否 | 每页数量，默认 10 |

> **注意**：如需搜索含特定分子的论文（相似度/子结构匹配），请使用 `bohrium-mol-search`。

---

## curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 按化学式查结构
curl -s "https://open.bohrium.com/openapi/v1/structures/query?formula=Li2O&page=1&pageSize=10" \
  -H "accessKey: $AK" | jq .

# 相图凸包
curl -s "https://open.bohrium.com/openapi/v1/structures/query_hull_by_composition/Li-Fe-O" \
  -H "accessKey: $AK" | jq .

# 遍历结构
curl -s "https://open.bohrium.com/openapi/v1/structures/iterate?startId=0&limit=10" \
  -H "accessKey: $AK" | jq .

# 通用数据集
curl -s -X POST "https://open.bohrium.com/openapi/v1/database/common_data/list" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"page":1,"pageSize":10}' | jq .

# 高分子数据
curl -s -X POST "https://open.bohrium.com/openapi/v1/database/polymer/list" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"page":1,"pageSize":10}' | jq .

# 分子属性查询
curl -s -X POST "https://open.bohrium.com/openapi/v1/molecular/search" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"query":"aspirin","page":1,"pageSize":10}' | jq .
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| structures/query 无结果 | 化学式不在数据库中 | 检查拼写，试更常见的化学式 |
| 相图链接 404 | OSS 文件过期或不存在 | 该组成可能尚无凸包数据 |
| molecular/search 超时 | 后端处理慢 | 用 SMILES 代替分子名（更精确） |
| database 接口 404 | 路径不在白名单 | 仅支持 `common_data/list` 和 `polymer/list` |

## 搭配使用

- **database** 查到材料结构 → **paper-search** 搜索相关合成/表征论文
- **database** 获取分子属性 → **mol-search** 查找讨论该分子的文献
- **database** 导出结构数据 → **sandbox** 做计算分析
