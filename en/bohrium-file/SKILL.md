---
name: bohrium-file
description: "Manage files on Bohrium via open.bohrium.com API. Use when: user asks about listing/downloading/sharing/transferring files on Bohrium, getting download URLs, managing file shares, or bulk downloading job output files. NOT for: dataset management (use bohrium-dataset), job submission (use bohrium-job), object storage operations (use bohrium-dataset)."
---

# SKILL: Bohrium File Management

## Overview

Manage files on the Bohrium platform via `open.bohrium.com` file service endpoints, including listing, downloading, sharing, transfer tasks, and bulk operations.

**Core capabilities:**

| Group | Endpoint | Description |
|-------|----------|-------------|
| List | `/v1/file/list` | Browse files |
| Download | `/v1/file/get_oss_url` | Get file download URL |
| Share | `/v1/file/share` | Create/manage share links |
| Transfer | `/v1/file/transfer/*` | Large file transfer tasks (create/list/retry/cancel) |
| Job files | `/v1/file/job/*` | Bulk save/download job output files |
| Dataset | `/v1/file/ds/download` | Download dataset files |
| Accounting | `/v1/file/accounting` | Check disk usage |

**Use when:**

- Downloading compute job output files
- Creating share links to send to colleagues
- Bulk downloading job outputs
- Checking disk space usage
- Managing large file transfers

**Don't use for:**

- Dataset creation/versioning → `bohrium-dataset`
- Submitting compute jobs → `bohrium-job`
- PDF document parsing → `bohrium-pdf-parser`

**No CLI support** — HTTP API only.

## Auth configuration

```json
"bohrium-file": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

## Common template

```python
import os, requests

AK = os.environ["ACCESS_KEY"]
BASE = "https://open.bohrium.com/openapi/v1/file"
H = {"accessKey": AK, "Content-Type": "application/json"}
H_GET = {"accessKey": AK}
```

---

## 1. List files — `/file/list`

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

## 2. Get download URL — `/file/get_oss_url`

```python
r = requests.post(f"{BASE}/get_oss_url", headers=H, json={
    "path": "/path/to/your/file.tar.gz"
})
data = r.json()
download_url = data.get("data", {}).get("url")
print(f"Download: {download_url}")
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | yes | File path on Bohrium |

---

## 3. File sharing

### Create share

```python
r = requests.post(f"{BASE}/share", headers=H, json={
    "path": "/path/to/file.pdf",
    "expiration": 7  # days until expiration
})
data = r.json()
print(f"Share token: {data.get('data', {}).get('token')}")
print(f"Share URL: {data.get('data', {}).get('url')}")
```

### Get share info

```python
r = requests.get(f"{BASE}/share", headers=H_GET, params={
    "token": "share_token_here"
})
print(r.json())
```

### Update share

```python
r = requests.put(f"{BASE}/share", headers=H, json={
    "token": "share_token_here",
    "expiration": 30
})
print(r.json())
```

### Check if file is shareable

```python
r = requests.post(f"{BASE}/check_share", headers=H, json={
    "path": "/path/to/file.pdf"
})
print(r.json())
```

---

## 4. Transfer task management

### Create transfer task

```python
r = requests.post(f"{BASE}/transfer/add", headers=H, json={
    "source": "/path/to/source",
    "destination": "/path/to/dest"
})
task_id = r.json().get("data", {}).get("id")
print(f"Transfer task: {task_id}")
```

### List transfer tasks

```python
r = requests.get(f"{BASE}/transfer/list", headers=H_GET)
for task in r.json().get("data", {}).get("items", []):
    print(f"  [{task['id']}] {task.get('status')} - {task.get('source')}")
```

### Get transfer download URL

```python
task_id = "123"
r = requests.get(f"{BASE}/transfer/file-dl/{task_id}", headers=H_GET)
print(r.json())
```

### Retry / Cancel transfer

```python
# Retry
requests.post(f"{BASE}/transfer/retry", headers=H, json={"id": task_id})

# Cancel
requests.post(f"{BASE}/transfer/cancel", headers=H, json={"id": task_id})
```

---

## 5. Bulk job file operations

### Bulk save job files

```python
r = requests.post(f"{BASE}/job/multi_save", headers=H, json={
    "jobId": 12345,
    "files": ["/output/result.json", "/output/model.pt"]
})
print(r.json())
```

### Bulk download job files

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

## 6. Dataset file download — `/file/ds/download`

```python
r = requests.post(f"{BASE}/ds/download", headers=H, json={
    "datasetId": 678,
    "path": "/data/train.csv"
})
print(r.json())
```

---

## 7. Disk usage — `/file/accounting`

```python
r = requests.get(f"{BASE}/accounting", headers=H_GET, params={
    "projectId": 109538,
    "userId": 27071
})
data = r.json()
print(f"Used: {data.get('data', {}).get('used')}")
print(f"Total: {data.get('data', {}).get('total')}")
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `projectId` | int | yes | Project ID |
| `userId` | int | yes | User ID |

---

## 8. Recent files — `/file/recent`

```python
r = requests.get(f"{BASE}/recent", headers=H_GET)
for f in r.json().get("data", []):
    print(f"  {f.get('name')} - {f.get('accessTime')}")
```

---

## curl examples

```bash
AK="YOUR_ACCESS_KEY"

# List files
curl -s "https://open.bohrium.com/openapi/v1/file/list?page=1&pageSize=10" \
  -H "accessKey: $AK" | jq .

# Get download URL
curl -s -X POST "https://open.bohrium.com/openapi/v1/file/get_oss_url" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"path":"/path/to/file.tar.gz"}' | jq .

# Create share
curl -s -X POST "https://open.bohrium.com/openapi/v1/file/share" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"path":"/path/to/file.pdf","expiration":7}' | jq .

# Bulk download job files
curl -s -X POST "https://open.bohrium.com/openapi/v1/file/job/multi_download" \
  -H "accessKey: $AK" -H "Content-Type: application/json" \
  -d '{"jobId":12345,"files":["/output/result.json"]}' | jq .

# Disk usage
curl -s "https://open.bohrium.com/openapi/v1/file/accounting" \
  -H "accessKey: $AK" | jq .

# Transfer task list
curl -s "https://open.bohrium.com/openapi/v1/file/transfer/list" \
  -H "accessKey: $AK" | jq .
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `get_oss_url` returns empty | File path doesn't exist | Use `/file/list` first to confirm path |
| Share link expired | Past expiration | Recreate share or extend `expiration` |
| Transfer task failed | Source unreachable | Use `transfer/retry` |
| Bulk download no URLs | Job cleaned up | Job outputs have retention limits |

## Pairs well with

- **job** submit compute → **file** bulk download results
- **file** get download URL → analyze locally or in **sandbox**
- **file** create share link → send to collaborators
- **dataset** manage versions → **file** download specific version files
