---
name: bohrium-scholar-search
description: "Search scholars and fetch scholar profile via open.bohrium.com. Use when: user asks to find/search/look up a scholar, researcher, or academic by name, affiliation, or research direction; or asks about a specific researcher's publications, citations, h-index, education, work experience, or research profile. NOT for: paper/patent content search (use bohrium-paper-search), knowledge base management, or file operations."
---

# SKILL: Bohrium 学者搜索与画像查询

## 概述

通过 Bohrium OpenAPI（`open.bohrium.com`）查询学者信息，包含两个核心接口：

| 接口 | 方法 | 路径 | 用途 |
|------|------|------|------|
| 学者搜索 | POST | `/openapi/v1/paper-server/scholar/search` | 按姓名/机构/研究方向等条件检索 |
| 学者详情 | GET | `/openapi/v1/paper-server/scholar/info?scholarId=xxx` | 根据 scholarId 获取完整画像 |

**典型用法：** 输入学者姓名 → 搜索候选列表 → 选中目标 `scholarId` → 拉取完整画像（发文量、引用、h-index、研究方向、教育/工作经历）。

**无 CLI 支持** — 全部通过 HTTP API 操作。

## 认证配置

BOHR_ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"bohrium-scholar-search": {
  "enabled": true,
  "apiKey": "YOUR_BOHR_ACCESS_KEY",
  "env": {
    "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.BOHR_ACCESS_KEY` 注入到运行环境。

### 获取流程（运行时）

```
读取 os.environ["BOHR_ACCESS_KEY"]
  ├─ 非空 → 直接使用
  └─ 为空 → 提示用户：
           「未在 OpenClaw 配置中检测到 BOHR_ACCESS_KEY，请在 ~/.openclaw/openclaw.json
            的 bohrium-scholar-search.env.BOHR_ACCESS_KEY 中填入从 https://bohrium.dp.tech
            个人设置页获取的 AccessKey，然后重启 OpenClaw 会话。」
```

**重要：** 不要把 AccessKey 另存到其他文件或写死到代码，统一通过 OpenClaw 环境变量注入。

### 错误处理

若 API 返回 `Invalid AccessKey`（code 2000）或 HTTP 401：
1. 说明 OpenClaw 配置中的 Key 已失效或错误
2. 提示用户：「您的 BOHR_ACCESS_KEY 已失效，请在 `~/.openclaw/openclaw.json` 中更新 `bohrium-scholar-search.env.BOHR_ACCESS_KEY` 并重启 OpenClaw 会话。」

## 通用代码模板

```python
import os, requests

AK = os.environ.get("BOHR_ACCESS_KEY", "")
if not AK:
    raise RuntimeError(
        "BOHR_ACCESS_KEY not found. Please configure it in ~/.openclaw/openclaw.json "
        "under bohrium-scholar-search.env.BOHR_ACCESS_KEY."
    )

BASE = "https://open.bohrium.com/openapi/v1/paper-server"
HEADERS_JSON = {"Authorization": f"Bearer {AK}", "Content-Type": "application/json"}
HEADERS = {"Authorization": f"Bearer {AK}"}
```

---

## 标准工作流

```
用户提问（学者相关）
  │
  ├─ 已知 scholarId → 直接调 Scholar Info
  └─ 未知 scholarId → 先调 Scholar Search
       └─ 从返回的 items[].scholarId 取 ID → 再调 Scholar Info
```

---

## 学者搜索

### 基本搜索

```python
r = requests.post(f"{BASE}/scholar/search", headers=HEADERS_JSON, json={
    "name": "Yann LeCun",
    "page": 1,
    "pageSize": 5
})
data = r.json()
for item in data["data"]["items"]:
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
    "pageSize": 10
})
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 学者姓名关键词（1~99 字符） |
| `school` | string | 否 | 学校/机构 |
| `tags` | string | 否 | 研究兴趣标签 |
| `affiliation` | string | 否 | 机构英文名 |
| `affiliationZh` | string | 否 | 机构中文名 |
| `page` | int | 否 | 页码，默认 1 |
| `pageSize` | int | 否 | 每页条数，默认 10 |

### 响应关键字段

`data.items[]` 数组，每个元素包含：

| 字段 | 说明 |
|------|------|
| `scholarId` | 学者唯一 ID，详情接口必填 |
| `nameEn` / `nameZh` | 英文名 / 中文名 |
| `paperNums` | 发文量 |
| `citationNums` | 引用量 |
| `hIndex` | h-index |
| `scholarOrgNameEn` / `scholarOrgNameZh` | 所属机构英文/中文名 |
| `isHighCited` | 是否为高被引学者 |

---

## 学者详情

用搜索结果中的 `scholarId` 查询完整画像：

```python
r = requests.get(
    f"{BASE}/scholar/info",
    headers=HEADERS,
    params={"scholarId": scholar_id}
)
info = r.json()["data"]
print(info.get("nameEn"), "|", info.get("nameZh"))
print("Research:", info.get("researchDirection"))
print("Education:", info.get("educationBackgroundZh") or info.get("educationBackground"))
print("Work:", info.get("workExperienceZh") or info.get("workExperience"))
```

### 额外返回字段

在搜索结果字段之上额外返回：

| 字段 | 说明 |
|------|------|
| `researchDirection` | 研究方向数组 |
| `educationBackground` / `educationBackgroundZh` | 教育经历（英/中） |
| `workExperience` / `workExperienceZh` | 工作经历（英/中） |

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
AK="$BOHR_ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v1/paper-server"

# Step 1: 学者搜索
curl -s -X POST "$BASE/scholar/search" \
  -H "Authorization: Bearer $AK" \
  -H "Content-Type: application/json" \
  -d '{"name":"Yann LeCun","page":1,"pageSize":3}'

# Step 2: 拉取详情
curl -s "$BASE/scholar/info?scholarId=RETURNED_ID" \
  -H "Authorization: Bearer $AK"
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `BOHR_ACCESS_KEY` 为空 | OpenClaw 未注入环境变量 | 检查 `~/.openclaw/openclaw.json` 中 `bohrium-scholar-search.env.BOHR_ACCESS_KEY` 是否填入 |
| `Invalid AccessKey` / 401 | Key 已失效或错误 | 更新 `~/.openclaw/openclaw.json` 中的 AccessKey 并重启会话 |
| 搜索返回空列表 | 1) 24 位无空格字符串会被误识别为内部 ID；2) 上游用户级限流 | 使用自然姓名而非 ID；稍后重试 |
| 详情接口参数错误 | 缺 `scholarId` | 先调搜索接口取 `data.items[].scholarId` |
| `name` 长度报错 | 超出 1~99 字符 | 截短姓名关键词 |
