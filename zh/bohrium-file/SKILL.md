---
name: bohrium-file
description: "Manage files on Bohrium via open.bohrium.com API. Use when: user asks about listing/downloading/sharing/transferring files on Bohrium, getting download URLs, managing file shares, or bulk downloading job output files. NOT for: dataset management (use bohrium-dataset), job submission (use bohrium-job), object storage operations (use bohrium-dataset)."
---

# SKILL: Bohrium 文件管理

## 概述

通过 `open.bohrium.com` 的文件服务端点管理 Bohrium 平台上的文件，包括文件列表、下载、分享、传输任务和批量操作。

**核心能力：**

| 功能分组 | 端点 | 说明 |
|----------|------|------|
| 文件列表 | `/v1/file/list` | 浏览文件列表 |
| 文件下载 | `/v1/file/get_oss_url` | 获取文件下载链接 |
| 文件分享 | `/v1/file/share` | 创建/管理分享链接 |
| 传输任务 | `/v1/file/transfer/*` | 大文件传输任务（创建/列表/重试/取消） |
| 任务文件 | `/v1/file/job/*` | 批量保存/下载计算任务输出文件 |
| 数据集下载 | `/v1/file/ds/download` | 下载数据集文件 |
| 磁盘统计 | `/v1/file/accounting` | 查看磁盘用量 |

**适用场景：**

- 下载计算任务的输出文件
- 创建文件分享链接发给同事
- 批量下载 job 产出
- 查看磁盘空间使用情况
- 管理大文件传输任务

**不适用：**

- 数据集创建/版本管理 → `bohrium-dataset`
- 提交计算任务 → `bohrium-job`
- PDF 文档解析 → `bohrium-pdf-parser`

**无 CLI 支持** — 通过 HTTP API 操作。

## 认证配置

```json
"bohrium-file": {
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
BASE = "https://open.bohrium.com/openapi/v1/file"
H = {"accessKey": AK, "Content-Type": "application/json"}
H_GET = {"accessKey": AK}
```

---

## 1. 文件列表 — `/file/list`

```python
r = requests.get(f"{BASE}/list", headers=H_GET, params={
    "page": 1,
    "pageSize": 20
})
data = r.json()
for f in data.get("data", {}).get("items", []):
    print(f"  {f.get('name')} ({f.get('size')} bytes)")
```

---

## 2. 获取文件下载链接 — `/file/get_oss_url`

```python
r = requests.post(f"{BASE}/get_oss_url", headers=H, json={
    "path": "/path/to/your/file.tar.gz"
})
data = r.json()
download_url = data.get("data", {}).get("url")
print(f"Download: {download_url}")
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `path` | string | 是 | 文件在 Bohrium 上的路径 |

---

## 3. 文件分享

### 创建分享

```python
r = requests.post(f"{BASE}/share", headers=H, json={
    "path": "/path/to/file.pdf",
    "expiration": 7  # 过期天数
})
data = r.json()
print(f"Share token: {data.get('data', {}).get('token')}")
print(f"Share URL: {data.get('data', {}).get('url')}")
```

### 查看分享信息

```python
r = requests.get(f"{BASE}/share", headers=H_GET, params={
    "token": "share_token_here"
})
print(r.json())
```

### 更新分享

```python
r = requests.put(f"{BASE}/share", headers=H, json={
    "token": "share_token_here",
    "expiration": 30
})
print(r.json())
```

### 检查文件是否可分享

```python
r = requests.post(f"{BASE}/check_share", headers=H, json={
    "path": "/path/to/file.pdf"
})
print(r.json())
```

---

## 4. 传输任务管理

### 创建传输任务

```python
r = requests.post(f"{BASE}/transfer/add", headers=H, json={
    "source": "/path/to/source",
    "destination": "/path/to/dest"
})
task_id = r.json().get("data", {}).get("id")
print(f"Transfer task: {task_id}")
```

### 列出传输任务

```python
r = requests.get(f"{BASE}/transfer/list", headers=H_GET)
for task in r.json().get("data", {}).get("items", []):
    print(f"  [{task['id']}] {task.get('status')} - {task.get('source')}")
```

### 获取传输下载链接

```python
task_id = "123"
r = requests.get(f"{BASE}/transfer/file-dl/{task_id}", headers=H_GET)
print(r.json())
```

### 重试/取消传输

```python
# 重试
requests.post(f"{BASE}/transfer/retry", headers=H, json={"id": task_id})

# 取消
requests.post(f"{BASE}/transfer/cancel", headers=H, json={"id": task_id})
```

---

## 5. 任务文件批量操作

### 批量保存任务文件

```python
r = requests.post(f"{BASE}/job/multi_save", headers=H, json={
    "jobId": 12345,
    "files": ["/output/result.json", "/output/model.pt"]
})
print(r.json())
```

### 批量下载任务文件

```python
r = requests.post(f"{BASE}/job/multi_download", headers=H, json={
    "jobId": 12345,
    "files": ["/output/result.json", "/output/model.pt"]
})
data = r.json()
for f in data.get("data", {}).get("urls", []):
    print(f"  Download: {f}")
```

---

## 6. 数据集文件下载 — `/file/ds/download`

```python
r = requests.post(f"{BASE}/ds/download", headers=H, json={
    "datasetId": 678,
    "path": "/data/train.csv"
})
print(r.json())
```

---

## 7. 磁盘用量统计 — `/file/accounting`

```python
r = requests.get(f"{BASE}/accounting", headers=H_GET, params={
    "projectId": 109538,
    "userId": 27071
})
data = r.json()
print(f"Used: {data.get('data', {}).get('used')}")
print(f"Total: {data.get('data', {}).get('total')}")
```

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `projectId` | int | 是 | 项目 ID |
| `userId` | int | 是 | 用户 ID |

---

## 8. 最近文件 — `/file/recent`

```python
r = requests.get(f"{BASE}/recent", headers=H_GET)
for f in r.json().get("data", []):
    print(f"  {f.get('name')} - {f.get('accessTime')}")
```

---

## curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 文件列表
curl -s "https://open.bohrium.com/openapi/v1/file/list?page=1&pageSize=10" \
  -H "accessKey: $AK" | jq .

# 获取下载链接
curl -s -X POST "https://open.bohrium.com/openapi/v1/file/get_oss_url" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"path":"/path/to/file.tar.gz"}' | jq .

# 创建分享
curl -s -X POST "https://open.bohrium.com/openapi/v1/file/share" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"path":"/path/to/file.pdf","expiration":7}' | jq .

# 批量下载任务文件
curl -s -X POST "https://open.bohrium.com/openapi/v1/file/job/multi_download" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"jobId":12345,"files":["/output/result.json"]}' | jq .

# 磁盘用量
curl -s "https://open.bohrium.com/openapi/v1/file/accounting" \
  -H "accessKey: $AK" | jq .

# 传输任务列表
curl -s "https://open.bohrium.com/openapi/v1/file/transfer/list" \
  -H "accessKey: $AK" | jq .
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `get_oss_url` 返回空 | 文件路径不存在 | 先用 `/file/list` 确认文件路径 |
| 分享链接失效 | 过期 | 重新创建分享或延长 `expiration` |
| 传输任务失败 | 源文件不可达 | 用 `transfer/retry` 重试 |
| 批量下载无 URL | job 已清理 | 任务输出有保留期限，过期后不可下载 |

## 搭配使用

- **job** 提交计算 → **file** 批量下载结果
- **file** 获取下载链接 → 本地分析或 **sandbox** 中运行
- **file** 创建分享链接 → 发给协作者
- **dataset** 管理版本 → **file** 下载特定版本的文件
