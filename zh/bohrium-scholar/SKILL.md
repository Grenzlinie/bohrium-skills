---
name: bohrium-scholar
description: "Scholar profile lookup via open.bohrium.com. Use when: user asks about finding a researcher's profile, h-index, citations, education/work background, or searching scholars by name/affiliation/research tags. NOT for: paper content search (use bohrium-paper-search), knowledge base (use bohrium-knowledge-base)."
---

# SKILL: Bohrium 学者检索

## 概述

通过 Bohrium OpenAPI（`open.bohrium.com`）查询学者信息，包含两个核心接口：

| 接口 | 方法 | 路径 | 用途 |
|------|------|------|------|
| 学者搜索 | POST | `/openapi/v1/paper-server/scholar/search` | 按姓名 / 机构 / 研究方向检索候选 |
| 学者详情 | GET  | `/openapi/v1/paper-server/scholar/info?scholarId=xxx` | 根据 scholarId 获取完整画像 |

**典型用法**：输入学者姓名 → 搜索候选列表 → 选中目标 `scholarId` → 拉取完整画像（发文量、引用、h-index、研究方向、教育 / 工作经历）。

**不适用**：

- 按关键词搜论文 → `bohrium-paper-search`
- 读 PDF 全文 → `bohrium-pdf-parser`

## 认证配置

```json
"bohrium-scholar": {
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
BASE = "https://open.bohrium.com/openapi/v1/paper-server"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS = {"accessKey": AK}
```

---

## 标准工作流

```
用户提问（学者相关）
  ├─ 已知 scholarId → 直接调 Scholar Info
  └─ 未知 scholarId → 先调 Scholar Search
       └─ 从返回的 items[].scholarId 取 ID → 再调 Scholar Info
```

---

## 1. 学者搜索 — `POST /scholar/search`

### 基本搜索

```python
r = requests.post(f"{BASE}/scholar/search", headers=HEADERS_JSON, json={
    "name": "Yann LeCun",
    "page": 1,
    "pageSize": 5,
})
for item in r.json()["data"]["items"]:
    print(f"[{item['scholarId']}] {item.get('nameEn','')} / {item.get('nameZh','')}")
    print(f"  Org: {item.get('scholarOrgNameEn','')}")
    print(f"  Papers: {item.get('paperNums',0)}, Citations: {item.get('citationNums',0)}, h-index: {item.get('hIndex',0)}")
```

### 带筛选条件

```python
r = requests.post(f"{BASE}/scholar/search", headers=HEADERS_JSON, json={
    "name": "张三",
    "school": "清华大学",
    "affiliationZh": "清华大学",
    "tags": "machine learning",
    "page": 1,
    "pageSize": 10,
})
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 学者姓名关键词（1~99 字符，超出范围直接返回空） |
| `school` | string | 否 | 学校 / 机构 |
| `tags` | string | 否 | 研究兴趣标签 |
| `affiliation` | string | 否 | 机构英文名 |
| `affiliationZh` | string | 否 | 机构中文名 |
| `page` | int | 否 | 页码，默认 1 |
| `pageSize` | int | 否 | 每页条数，默认 10（建议 ≤ 20） |
| `source` | string | 否 | 曝光来源标识（如 `mix_search`） |
| `searchSource` | string | 否 | 搜索来源标识（如 `scholar_tab_search`） |
| `searchName` | string | 否 | 搜索名称（用于日志归因） |
| `isNewPaper` | bool | 否 | 仅搜索有新论文的学者 |

> **限制**：如果 `name` 是 24 位无空格字符串，网关会判为内部 ID 格式而返回空 items。

### 响应字段（`data`）

| 字段 | 说明 |
|------|------|
| `total` | 总条数 |
| `page` / `pageSize` | 当前分页 |
| `searchId` | 本次搜索标识（可用于上报 / 排查） |
| `items[]` | 学者列表 |

### `items[]` 关键字段（实测）

| 字段 | 说明 |
|------|------|
| `scholarId` | 学者唯一 ID，详情接口必填 |
| `nameEn` / `nameZh` | 英文名 / 中文名 |
| `paperNums` | 发文量 |
| `citationNums` | 引用量 |
| `hIndex` | h-index |
| `scholarOrgNameEn` / `scholarOrgNameZh` | 所属机构 |
| `discipline` / `major` | 学科 / 专业 |
| `researchDirection` | 研究方向数组 |
| `educationBackground` / `educationBackgroundEn` / `educationBackgroundZh` | 教育经历 |
| `workExperience` / `workExperienceEn` / `workExperienceZh` | 工作经历 |
| `avatar` | 头像 URL |
| `orcid` | ORCID 号 |
| `email` / `RawEmail` | 邮箱 |
| `source` | 数据来源（如 `google`） |
| `isHighCited` | 是否高被引学者 |
| `mergeScholarId` | 已合并的 ID（如有） |
| `userExtId` / `userId` | Bohrium 平台对应用户 ID（如已认领） |

---

## 2. 学者详情 — `GET /scholar/info`

用搜索结果中的 `scholarId` 查询完整画像：

```python
r = requests.get(
    f"{BASE}/scholar/info",
    headers=HEADERS,
    params={"scholarId": scholar_id, "viewType": "detail"},  # viewType 可选
)
info = r.json()["data"]
print(info.get("nameEn"), "|", info.get("nameZh"))
print("Research:", info.get("researchDirection"))
print("Education:", info.get("educationBackgroundZh") or info.get("educationBackground"))
print("Work:", info.get("workExperienceZh") or info.get("workExperience"))
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scholarId` | string | 是 | 学者唯一标识（query 参数） |
| `viewType` | string | 否 | 访问类型，用于日志归因（如 `detail`） |

### 响应字段（除 search 已覆盖的之外，info 还包含）

| 字段 | 说明 |
|------|------|
| `researchDirection` | 研究方向数组 |
| `educationBackground` / `educationBackgroundEn` / `educationBackgroundZh` | 教育经历（多语言） |
| `workExperience` / `workExperienceEn` / `workExperienceZh` | 工作经历（多语言） |
| `discipline` / `major` | 学科 / 专业 |
| `email` / `RawEmail` | 邮箱（如已公开） |

---

## 结果呈现建议

将 API 返回格式化为用户友好的摘要，建议重点展示：

- **姓名**：`nameEn` / `nameZh`
- **机构**：`scholarOrgNameEn` / `scholarOrgNameZh`
- **学术指标**：`paperNums` / `citationNums` / `hIndex`
- **高被引**：`isHighCited`
- **研究方向**：`researchDirection`
- **教育经历**：优先 `educationBackgroundZh`，无则 `educationBackground`
- **工作经历**：优先 `workExperienceZh`，无则 `workExperience`

若搜索返回多个候选，先以摘要表格形式列出供用户确认，再查详情。

---

## curl 示例

```bash
AK="$ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v1/paper-server"

# Step 1: 学者搜索
curl -s -X POST "$BASE/scholar/search" \
  -H "accessKey: $AK" \
  -H "Content-Type: application/json" \
  -d '{"name":"Yann LeCun","page":1,"pageSize":3}'

# Step 2: 学者详情
curl -s -G "$BASE/scholar/info" \
  -H "accessKey: $AK" \
  --data-urlencode "scholarId=SCHOLAR_ID"
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `search` 返回空 `items` | 姓名写法不匹配或真无此人 | 换英文名常见拼写；或加 `school` 缩小范围 |
| `search` 返回空但确定有此人 | `name` 是 24 位无空格字符串，被判为内部 ID | 加空格或拆分姓名 |
| `search` 高频请求返回空 | 接口有用户级限流，触发后返空而非报错 | 降低 QPS，加退避重试 |
| `401` / `AccessKey is required` | Header 名字写错 | 用 `accessKey`（首字母小写），不是 `Authorization` |
| `code=10001` | 参数错误（如 `name` 越界、`scholarId` 为空） | 校验必填、长度 1-99 |
| `info` 返回字段不全 | 学者本人未补全 | 尊重已有字段；前端按字段可选展示 |

## 错误码

| code | 说明 |
|------|------|
| 0 | 成功 |
| -1 | 未知错误 |
| 10001 | 参数错误 |
| 10002 | 业务错误 |

## 搭配使用

- **scholar** 找到代表人物 → **paper-search** 深挖该学者的论文与引用网络
- **scholar** 的 `researchDirection` 作为关键词 → **paper-search / web-search** 扩展检索
- **scholar** 拿到论文 DOI → **pdf-parser** 下载全文解析
