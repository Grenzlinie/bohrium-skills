---
name: bohrium-pdf-parser
description: "Parse PDF documents via Bohrium open API. Use when: user asks about extracting text, tables, charts, formulas, or molecules from PDF files on Bohrium, submitting PDFs by URL or file upload. NOT for: file management, dataset management, or knowledge base operations."
---

# SKILL: Bohrium PDF 解析

## 概述

使用 Bohrium 平台提供的 PDF 解析服务（Uni-Parser），从 PDF 中提取文本、表格、图表、公式、分子式等内容。支持两种提交方式：

- **URL 提交** — 传入 PDF 下载链接
- **文件上传** — 上传本地 PDF 文件

**无 CLI 支持** — 全部通过 HTTP API 操作。

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"bohrium-pdf-parser": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.ACCESS_KEY` 注入到运行环境。

## 通用代码模板

```python
import os, time, uuid, requests

AK = os.environ.get("ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi/v1/parse"
HEADERS = {"accessKey": AK}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}
```

---

## 解析工作流

```
1. 提交 PDF（URL 或文件上传）→ 获得 token
2. 用 token 轮询结果 → status == "success" 时完成
```

同步模式（`sync=true`）提交后等待解析完成再返回，但不含 content，仍需调用 `get-result` 获取；异步模式（`sync=false`，默认）需要轮询 `get-result` 等待 status 变为 `success`。

---

## 解析选项说明

解析参数使用整数值控制精度：

| 值 | 含义 |
|----|------|
| `-1` | 返回 Base64 图片（不做识别） |
| `0` | 禁用该模块 |
| `1` | 快速模式 |
| `2` | 高精度模式 |
| `3` | 直接提取（仅 `textual` 支持，用于数字 PDF 直接提取文本） |

| 参数 | 类型 | 说明 |
|------|------|------|
| `sync` | bool/string | `true` 同步等待，`false` 异步轮询 |
| `textual` | int | 解析文本内容（支持 0/1/2/3） |
| `equation` | int | 解析公式（支持 0/1/2） |
| `table` | int | 解析表格（支持 0/1/2） |
| `chart` | int | 解析图表（支持 0/1） |
| `figure` | int | 解析图像（支持 -1/0/1） |
| `expression` | int | 解析化学反应式（支持 0/1） |
| `molecule` | int | 解析分子式（支持 0/1） |
| `pages` | list[int] / int | 指定解析页码（0-indexed），省略则解析全部页 |
| `timeout` | int | 超时时间（秒） |

> **注意**：JSON 请求体中 `pages` 可传数组 `[0, 1, 2]`；multipart form 中只能传单个整数。

---

## URL 提交解析

```python
r = requests.post(f"{BASE}/trigger-url-async", headers=HEADERS_JSON, json={
    "url": "https://www.nature.com/articles/s41586-021-03819-2.pdf",
    "sync": False,
    "textual": 2,
    "table": 2,
    "molecule": 0,
    "chart": 0,
    "figure": 0,
    "expression": 1,
    "equation": 2,
    "pages": [0],           # 0-indexed，省略则解析全部页
    "timeout": 1800
})
data = r.json()
token = data["token"]
print(f"Token: {token}, Status: {data['status']}")
```

**响应字段：**

| 字段 | 说明 |
|------|------|
| `token` | 任务标识，用于查询结果（网关自动生成） |
| `status` | 初始状态为 `undefined` |
| `created_time` | 创建时间 |
| `page_count` | PDF 总页数 |
| `time_dict` | 各阶段耗时 |

> URL 方式下网关会自动注入 `token` 字段，客户端无需自行生成。

---

## 文件上传解析

文件上传使用 multipart/form-data，**必须由客户端生成并传入 `token` 字段**（网关对 multipart 请求不自动注入 token）。认证推荐使用 query param 方式。

```python
import uuid
from pathlib import Path

pdf_path = Path("./paper.pdf")
task_token = str(uuid.uuid4())

with open(pdf_path, "rb") as f:
    r = requests.post(
        f"{BASE}/trigger-file-async?accessKey={AK}",
        files={"file": (pdf_path.name, f, "application/pdf")},
        data={
            "token": task_token,    # 必须：客户端生成的 UUID
            "sync": "false",
            "textual": "2",
            "table": "2",
            "molecule": "0",
            "chart": "0",
            "figure": "0",
            "expression": "1",
            "equation": "2",
            "timeout": "1800"
        },
        timeout=60
    )
token = r.json()["token"]
```

> **关键点**：
> - `token` 字段必填，传客户端生成的 UUID
> - 认证使用 query param `?accessKey=AK`（multipart 请求中 header 认证可能失效）
> - 不要设置 `Content-Type` header，让 requests 自动处理 multipart boundary
> - form data 中所有值都是字符串（`"2"` 而非 `2`）

---

## 查询解析结果

```python
r = requests.post(f"{BASE}/get-result", headers=HEADERS_JSON, json={
    "token": token,
    "content": True,        # 返回解析出的文本
    "objects": False,       # 返回解析出的对象（表格、图等）
    "pages_dict": False     # 是否返回按页结果；true 时返回列表结构
})
data = r.json()
print(f"Status: {data['status']}, Content length: {len(data.get('content', ''))}")
```

**响应字段：**

| 字段 | 说明 |
|------|------|
| `status` | `success` / `undefined`（排队中）/ `processing` / `failed` |
| `token` | 任务标识 |
| `content` | 解析出的文本（LaTeX 标记格式） |
| `pages_dict` | 按页的解析结果列表（当前接口返回 list，不要假设为 dict） |
| `lang` | 检测到的语言（`en` / `zh` 等） |
| `proc_page` / `total_page` | 已处理/总页数 |
| `proc_textual` / `total_textual` | 已处理/总文本块数 |
| `proc_table` / `total_table` | 已处理/总表格数 |
| `proc_mol` / `total_mol` | 已处理/总分子式数 |
| `proc_equa` / `total_equa` | 已处理/总公式数 |
| `time_dict` | 各阶段耗时详情 |
| `cost` | 费用 |

---

## 异步轮询完整示例

```python
import os, time, requests

AK = os.environ.get("ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi/v1/parse"
HEADERS = {"accessKey": AK}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}

# 1. 提交
r = requests.post(f"{BASE}/trigger-url-async", headers=HEADERS_JSON, json={
    "url": "https://www.nature.com/articles/s41586-021-03819-2.pdf",
    "sync": False,
    "textual": 2, "table": 2, "molecule": 0,
    "chart": 0, "figure": 0,
    "expression": 1, "equation": 2,
    "pages": [0],
    "timeout": 1800
})
submit = r.json()
if submit.get("code"):
    print(f"Submit failed: {submit.get('message')}")
    exit(1)

token = submit["token"]
print(f"Submitted, token={token}")

# 2. 轮询结果
for attempt in range(60):
    time.sleep(3)
    r = requests.post(f"{BASE}/get-result", headers=HEADERS_JSON, json={
        "token": token,
        "content": True,
        "objects": False,
        "pages_dict": False
    })
    result = r.json()
    status = result.get("status", "")
    print(f"  [{attempt+1}] status={status}")

    if status == "success":
        print(f"Done! Content length: {len(result.get('content', ''))}")
        print(f"Language: {result.get('lang')}, Cost: {result.get('cost')}")
        print(f"Preview: {result.get('content', '')[:200]}")
        break
    elif status == "failed":
        print(f"Failed: {result.get('description', 'unknown error')}")
        break
else:
    print("Timeout: task did not complete within 180 seconds")
```

---

## 同步模式示例

同步模式（`sync=true`）提交后等待解析完成再返回，无需轮询状态。但**返回中不含 content 字段**，仍需调用 `get-result` 获取解析内容：

```python
# 1. 同步提交 — 阻塞等待解析完成
r = requests.post(f"{BASE}/trigger-url-async", headers=HEADERS_JSON, json={
    "url": "https://www.nature.com/articles/s41586-021-03819-2.pdf",
    "sync": True,
    "textual": 2, "table": 2,
    "molecule": 0, "chart": 0, "figure": 0,
    "expression": 1, "equation": 2,
    "pages": [0],
    "timeout": 1800
})
submit = r.json()
token = submit["token"]
# submit["status"] == "success"，但不含 content

# 2. 获取内容
r = requests.post(f"{BASE}/get-result", headers=HEADERS_JSON, json={
    "token": token,
    "content": True, "objects": False, "pages_dict": False
})
result = r.json()
print(f"Content: {result['content'][:200]}")
```

---

## curl 示例

```bash
AK="YOUR_ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v1/parse"

# URL 提交
curl -s -X POST "$BASE/trigger-url-async" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{"url":"https://www.nature.com/articles/s41586-021-03819-2.pdf","sync":false,"textual":2,"table":2,"molecule":0,"chart":0,"figure":0,"expression":1,"equation":2,"pages":[0],"timeout":1800}'

# 文件上传（注意 token 必填，认证用 query param）
curl -s -X POST "$BASE/trigger-file-async?accessKey=$AK" \
  -F "file=@paper.pdf" \
  -F "token=$(uuidgen)" \
  -F "sync=false" -F "textual=2" -F "table=2" \
  -F "equation=2" -F "molecule=0" -F "chart=0" -F "figure=0"

# 查询结果
curl -s -X POST "$BASE/get-result" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{"token":"YOUR_TOKEN","content":true,"objects":false,"pages_dict":true}'
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `Token is required` | 文件上传时未传 `token` 字段 | multipart 请求必须由客户端生成 UUID 作为 `token` 字段传入 |
| 文件上传 401 | header 认证对 multipart 请求可能失效 | 改用 query param：`?accessKey=AK` |
| `AccessKey is required` | 未传或传错 accessKey | Header 名为 `accessKey`（camelCase），或用 query param |
| URL 提交超时 | 服务端无法下载目标 PDF（如 arxiv 网络不通） | 换用其他可达的 PDF URL，或改用文件上传方式 |
| `int_parsing` 错误 | 文件上传时 `pages` 传了 JSON 数组 | multipart form 中 `pages` 只能传单个整数 |
| `status: undefined` | 异步任务排队中 | 等待后重新调用 `get-result`，建议间隔 3 秒轮询 |
| `status: processing` | 正在解析 | 继续轮询，大文件可能需要 1-3 分钟 |
| content 含 LaTeX 标记 | 正常行为 | 解析结果用 `\begin{title}` 等标记段落结构，需后处理提取纯文本 |
| 大文件解析慢 | 页数多或内容复杂 | 用 `pages` 参数指定需要的页码，减少解析范围 |
| `figure` 返回 403 | AccessKey 无该模块权限 | 设置 `figure: 0` 禁用，或联系平台开通权限 |
