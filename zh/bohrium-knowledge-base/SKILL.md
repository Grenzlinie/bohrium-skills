---
name: bohrium-knowledge-base
description: "Manage Bohrium knowledge bases via open.bohrium.com API. Use when: user asks about creating/listing/searching knowledge bases, managing literature/papers, uploading files, tagging, notes, or searching literature content. NOT for: compute jobs, nodes, images, or datasets."
---

# SKILL: Bohrium 知识库 (Knowledge Base) 管理

## 概述

管理 Bohrium 平台的知识库（Literature Sage）。知识库提供文献管理、文件夹组织、标签分类、笔记、文献内容搜索与召回、权限管理等功能。

**无 CLI 支持** — 与 bohrium-job/node/image 等不同，知识库没有 `bohr` CLI 命令，全部通过 HTTP API 操作。

## 认证配置

BOHR_ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"bohrium-knowledge-base": {
  "enabled": true,
  "apiKey": "YOUR_BOHR_ACCESS_KEY",
  "env": {
    "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.BOHR_ACCESS_KEY` 注入到运行环境。

## 路由映射

```
外部调用: GET/POST https://open.bohrium.com/openapi/v2/knowledge/{path}
         Header: Authorization: Bearer $BOHR_ACCESS_KEY

网关转发: → literature-sage.bohrium.com/api/v1/{path}
         Header: X-User-Id, X-Org-Id (由 BOHR_ACCESS_KEY 自动转换)
```

## 通用代码模板

```python
import os, requests

AK = os.environ.get("BOHR_ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi/v2/knowledge"
HEADERS = {"Authorization": f"Bearer {AK}"}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}
```

---

## 知识库管理

### 创建知识库

```python
r = requests.post(f"{BASE}/knowledge_base/create", headers=HEADERS_JSON, json={
    "knowledgeBaseName": "My Knowledge Base",
    "cover": "",
    "introduction": "A collection of papers on molecular dynamics",
    "privilege": 1  # 1=私有, 2=公开
})
print(r.json())
# {"code": 0, "data": {"id": 123, "msg": "Knowledge base created successfully."}}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `knowledgeBaseName` | string | 是 | 知识库名称 |
| `cover` | string | 是 | 封面图 URL（可为空字符串） |
| `introduction` | string | 是 | 知识库简介 |
| `privilege` | integer | 是 | 1=私有, 2=公开 |

### 我的知识库列表

```python
r = requests.get(f"{BASE}/knowledge_base/list", headers=HEADERS,
    params={"keyword": "", "pageSize": 10, "pageNum": 1})
data = r.json()["data"]
for kb in data["list"]:
    print(f"[{kb['id']}] {kb['name']} (nodeId={kb['nodeId']}, privilege={kb['privilege']})")
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | string | 否 | 搜索关键字 |
| `pageSize` | integer | 否 | 每页条数（默认 10） |
| `pageNum` | integer | 否 | 页码（默认 1） |
| `orderBy` | integer | 否 | 1=favoriteCount, 2=docCount, 3=sessionCount, 4=releaseTime |
| `order` | integer | 否 | 1=asc, 2=desc |

**返回字段：**

| 字段 | 说明 |
|------|------|
| `id` | 知识库 ID |
| `name` | 知识库名称 |
| `nodeId` | 知识库节点 ID（用于查询文献、文件夹操作） |
| `introduction` | 简介 |
| `cover` | 封面 URL |
| `privilege` | 1=私有, 2=公开 |
| `isZotero` | 是否 Zotero 同步知识库 |
| `count` | 文献数量 |
| `updateTime` | 更新时间（ISO 8601） |
| `createTime` | 创建时间（ISO 8601） |
| `source` | 来源标识 |
| `favoriteCount` | 收藏数 |
| `sessionCount` | 会话数 |

### 更新知识库

```python
r = requests.post(f"{BASE}/knowledge_base/update", headers=HEADERS_JSON, json={
    "knowledgeBaseName": "Updated Name",
    "cover": "",
    "introduction": "Updated introduction",
    "NodesId": 456,       # 知识库节点 ID
    "privilege": 2         # 改为公开
})
# {"code": 0, "data": {"id": 123, "msg": "Knowledge base updated successfully."}}
```

### 知识库详情

```python
node_id = 456
r = requests.get(f"{BASE}/knowledge_base/{node_id}", headers=HEADERS)
print(r.json())
```

### 发现公开知识库

```python
r = requests.get(f"{BASE}/knowledge_base/discover", headers=HEADERS,
    params={"pageSize": 10, "pageNum": 1})
```

### 推荐知识库

```python
r = requests.get(f"{BASE}/knowledge_base/recommendation", headers=HEADERS)
# data: {list, total, config_reason}
```

### 收藏 / 取消收藏

```python
requests.post(f"{BASE}/knowledge_base/favorite",   headers=HEADERS_JSON, json={"nodesId": YOUR_KB_NODES_ID})
requests.post(f"{BASE}/knowledge_base/unfavorite", headers=HEADERS_JSON, json={"nodesId": YOUR_KB_NODES_ID})

# 查看我收藏的知识库
r = requests.get(f"{BASE}/knowledge_base/favorite", headers=HEADERS,
    params={"pageNum": 1, "pageSize": 10})
```

### 浏览历史 / 搜索历史

```python
# 记录浏览
requests.post(f"{BASE}/knowledge_base/browse/add", headers=HEADERS_JSON, json={
    "fileId": 12345,
    "fileType": 1,
    "parentId": YOUR_KB_NODES_ID,
    "rootFolderId": YOUR_KB_NODES_ID,
    "nodesId": YOUR_KB_NODES_ID
})

# 查询浏览/搜索历史
requests.post(f"{BASE}/knowledge_base/browse/query",  headers=HEADERS_JSON, json={"pageNum":1,"pageSize":10})
requests.post(f"{BASE}/knowledge_base/history/query", headers=HEADERS_JSON, json={"pageNum":1,"pageSize":10})
```

### 搜索知识库

```python
r = requests.post(f"{BASE}/knowledge_base/search/name", headers=HEADERS_JSON, json={
    "nodesId": 456,              # 知识库 nodesId；0 表示搜索所有有权限的知识库
    "searchText": "molecular dynamics",
    "searchType": 0,             # 0=全部, 1=只搜文件夹, 2=只搜文件
    "pageNum": 1,
    "pageSize": 10
})
data = r.json()["data"]
print(f"共 {data['total']} 条")
for f in data["folders"]: print("[DIR]", f["name"])
for f in data["files"]:   print("[FILE]", f["fileName"])
```

### 删除知识库

知识库本身没有专用的 `delete` 端点，删除知识库 = 删除其根 `nodesId`（因为知识库本质上就是一个根文件夹）：

```python
r = requests.post(f"{BASE}/folder/delete", headers=HEADERS_JSON, json={
    "nodesId": YOUR_KB_NODES_ID   # 知识库的 nodesID
})
# 只有 Owner 角色 (role=1) 才能删除
```

---

## 文件夹管理

### 根目录列表（知识库列表）

```python
r = requests.get(f"{BASE}/folder/root", headers=HEADERS)
data = r.json()["data"]
print(f"共 {data['total']} 个知识库, {data['docCount']} 篇文献")
for item in data["list"]:
    print(f"  [{item['id']}] {item['name']} ({item['docCount']} 篇, "
          f"relationship={'拥有' if item['relationship'] == 1 else '加入'})")
```

**返回字段：**

| 字段 | 说明 |
|------|------|
| `total` | 知识库数量 |
| `list[].id` | 文件夹/知识库 ID |
| `list[].name` | 名称 |
| `list[].docCount` | 文献数量 |
| `list[].relationship` | 1=拥有该知识库, 2=已加入 |
| `docCount` | 总文献数 |

### 子目录列表（一级）

```python
r = requests.get(f"{BASE}/folder/children", headers=HEADERS,
    params={"folderId": 456, "pageNum": 1, "pageSize": 20})
data = r.json()["data"]

# 路径面包屑
for p in data["path"]:
    print(f"  {'>' * p['depth']} {p['name']} (id={p['nodesId']})")

# 子文件夹
for f in data["folders"]:
    print(f"  [DIR] {f['name']} ({f['docCount']} 篇, id={f['id']})")

# 文献
for f in data["files"]:
    print(f"  [FILE] {f['name']} | {f['fileName']} | {f['date']}")
```

**返回字段：**

| 字段 | 说明 |
|------|------|
| `path[]` | 路径面包屑 `{nodesId, name, depth}` |
| `folders[]` | 子文件夹 `{id, name, docCount, createdTime}` |
| `files[]` | 文献列表 |
| `files[].nodesId` | 文献节点 ID |
| `files[].paperId` | 论文 ID |
| `files[].md5` | 文件 MD5 |
| `files[].enName` | 英文标题 |
| `files[].zhName` | 中文标题 |
| `files[].fileName` | 文件名 |
| `files[].authors` | 作者列表 |
| `files[].date` | 发表日期 |
| `files[].literatureType` | 文献类型 |
| `fileCount` | 文件总数 |

### 目录树

```python
r = requests.get(f"{BASE}/folder/directory", headers=HEADERS,
    params={"folderId": 456})
# 递归树结构: {result: [{nodesId, name, subFolders: [...]}]}

# 文件树（含文献）：
r = requests.get(f"{BASE}/folder/file_tree", headers=HEADERS,
    params={"folderId": 456})
```

### 创建文件夹

```python
r = requests.post(f"{BASE}/folder/create", headers=HEADERS_JSON, json={
    "parentId": 456,             # 父文件夹 ID
    "folderName": "My Folder"
})
# {"code": 0, "data": {"message": "..."}}
```

### 重命名文件夹

```python
r = requests.post(f"{BASE}/folder/update", headers=HEADERS_JSON, json={
    "nodesId": 789,              # 文件夹节点 ID
    "folderName": "New Name"
})
```

### 移动文件夹

```python
r = requests.post(f"{BASE}/folder/move", headers=HEADERS_JSON, json={
    "sourceFolderId": 789,       # 源文件夹 ID
    "targetFolderId": 456        # 目标文件夹 ID
})
```

### 删除文件夹

```python
r = requests.post(f"{BASE}/folder/delete", headers=HEADERS_JSON, json={
    "nodesId": 789
})
```

---

## 文献管理

### 文献列表

```python
r = requests.get(f"{BASE}/file", headers=HEADERS,
    params={
        "parentId": 456,        # 文件夹 ID
        "pageNum": 1,
        "pageSize": 20,
        "order": 1,             # 1=asc, 2=desc（整数，不是字符串）
        "orderBy": 1,           # 1=createdTime, 2=updatedTime, etc.
        "noTag": False          # True 只看未打标签的
    })
```

### 文献详情

```python
r = requests.get(f"{BASE}/file/detail", headers=HEADERS,
    params={"resourceId": "12345"})
detail = r.json()["data"]
print(f"标题: {detail['enName']}")
print(f"作者: {', '.join(a['name'] for a in detail.get('authorDetails', []))}")
print(f"DOI: {detail.get('doi', '')}")
print(f"摘要: {detail.get('enAbstract', '')}")
```

**返回字段（精选）：**

| 字段 | 说明 |
|------|------|
| `id` | 文献 ID |
| `enName` / `zhName` | 英文/中文标题 |
| `authors` | 作者列表 |
| `authorDetails[]` | 作者详情（含 scholarId, avatar, name, paperNums, citationNums, hIndex） |
| `doi` | DOI |
| `enAbstract` / `zhAbstract` | 英文/中文摘要 |
| `date` | 发表日期 |
| `fileName` | 文件名 |
| `md5` | 文件 MD5 |
| `paperId` | 论文 ID |
| `publicationEnName` | 期刊名 |
| `literatureType` | 文献类型 |
| `openAccess` | 是否开放获取 |
| `existPDF` | 是否有 PDF |
| `summary[]` | 章节摘要 `{title, zhTitle, content, zhContent}` |

### 文献下载链接

```python
r = requests.post(f"{BASE}/file/read", headers=HEADERS_JSON, json={
    "userResourceId": [12345]    # 注意是数组，参数名是 userResourceId
})
# 返回每个 resource 的下载链接列表
```

### 上传文件

支持将本地文件（PDF、Markdown 等）上传到知识库中。

#### 上传流程（三步）

```
1) GET  /file/multipart   → 获取上传凭证 (host, path, token)
2) POST {host}/api/upload/binary  → 上传文件二进制内容
3) POST /file/submit       → 将文件注册到知识库（使其可见）
```

#### 获取上传凭证

```python
# 计算文件MD5和大小
import hashlib
def md5_hex(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

# 获取上传凭证
file_path = "paper.pdf"
file_name = "paper.pdf"
file_size = os.path.getsize(file_path)
file_md5 = md5_hex(file_path)
parent_id = 456  # 知识库或文件夹的nodeId

r = requests.get(f"{BASE}/file/multipart", headers=HEADERS,
    params={
        "fileName": file_name,
        "md5": file_md5,
        "parentId": parent_id,
        "size": file_size
    })

multipart_data = r.json()["data"]
if multipart_data.get("fileExist"):
    print("文件已存在，无需重复上传")
else:
    host = multipart_data["host"]
    path = multipart_data["path"]
    token = multipart_data["token"]
    print(f"获取上传凭证成功: {host}, {path}")
```

#### 执行二进制上传

```python
import base64
import json
import urllib.request

def make_storage_param(remote_path: str, encoded_file_name: str, content_type: str) -> str:
    payload = {
        "path": remote_path,
        "option": {
            "contentDisposition": (
                f'inline; filename="{encoded_file_name}"; '
                f"filename*=UTF-8''{encoded_file_name}"
            ),
            "contentType": content_type,
        },
    }
    b = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(b).decode("utf-8")

# 文件上传到存储服务
file_content = open(file_path, "rb").read()
content_type = "application/pdf"  # 或其他合适的MIME类型
encoded_file_name = urllib.parse.quote(file_name, safe="-_.!~*'()")

storage_param = make_storage_param(path, encoded_file_name, content_type)
upload_url = host.rstrip("/") + "/api/upload/binary"

req = urllib.request.Request(upload_url, method="POST", data=file_content)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("X-Storage-Param", storage_param)
req.add_header("Content-Type", "application/octet-stream")

with urllib.request.urlopen(req, timeout=300) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))

print("二进制文件上传完成")
```

#### 注册文件到知识库

```python
# 将上传的文件注册到知识库中，使其在知识库中可见
final_path = (upload_result.get("data") or {}).get("path") or path

r = requests.post(f"{BASE}/file/submit", headers=HEADERS_JSON, json={
    "parentId": parent_id,
    "fileName": file_name,
    "md5": file_md5,
    "size": file_size,
    "url": final_path  # 上传完成后返回的路径
})

result = r.json()
if result.get("code") == 0:
    print("文件成功注册到知识库")
elif result.get("code") == 230117:  # 文件已存在
    print("文件已在知识库中")
else:
    print(f"注册失败: {result}")
```

#### 完整的上传函数示例

```python
import hashlib
import base64
import json
import urllib.request
import mimetypes
import os

def guess_content_type(path):
    suffix = os.path.splitext(path)[1].lower()
    if suffix in {".md", ".markdown"}:
        return "text/markdown; charset=utf-8"
    if suffix in {".txt"}:
        return "text/plain; charset=utf-8"

    ctype, _ = mimetypes.guess_type(path)
    if ctype is None:
        return "application/octet-stream"

    if ctype.startswith("text/"):
        return f"{ctype}; charset=utf-8"
    return ctype

def upload_file_to_knowledge_base(file_path, parent_id, custom_file_name=None):
    # 准备文件信息
    file_name = custom_file_name or os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # 计算MD5
    def md5_hex(path):
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    file_md5 = md5_hex(file_path)

    # 步骤1: 获取上传凭证
    r = requests.get(f"{BASE}/file/multipart", headers=HEADERS,
        params={
            "fileName": file_name,
            "md5": file_md5,
            "parentId": parent_id,
            "size": file_size
        })

    multipart_data = r.json()["data"]

    if multipart_data.get("fileExist"):
        print("文件已存在，跳过上传，但注册到知识库...")

        # 即使文件已存在，仍需注册到知识库
        r_submit = requests.post(f"{BASE}/file/submit", headers=HEADERS_JSON, json={
            "parentId": parent_id,
            "fileName": file_name,
            "md5": file_md5,
            "size": file_size,
            "url": multipart_data.get("path", "")  # 使用已存在的路径
        })
        return r_submit.json()

    # 获取上传凭证
    host = multipart_data["host"]
    path = multipart_data["path"]
    token = multipart_data["token"]

    # 准备上传参数
    content_type = guess_content_type(file_path)
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

    # 步骤2: 二进制上传
    file_content = open(file_path, "rb").read()
    upload_url = host.rstrip("/") + "/api/upload/binary"

    req = urllib.request.Request(upload_url, method="POST", data=file_content)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-Storage-Param", storage_param)
    req.add_header("Content-Type", "application/octet-stream")

    with urllib.request.urlopen(req, timeout=300) as resp:
        upload_result = json.loads(resp.read().decode("utf-8"))

    # 步骤3: 注册文件到知识库
    final_path = (upload_result.get("data") or {}).get("path") or path

    r_submit = requests.post(f"{BASE}/file/submit", headers=HEADERS_JSON, json={
        "parentId": parent_id,
        "fileName": file_name,
        "md5": file_md5,
        "size": file_size,
        "url": final_path
    })

    return r_submit.json()

# 使用示例
result = upload_file_to_knowledge_base("./paper.pdf", 456)
print(result)
```

#### 幂等性

如果文件已存在（`fileExist=true`），系统会跳过二进制上传步骤，但仍会调用 submit 接口确保文件在知识库中可见。这使得多次上传同一文件是安全的操作。

#### 脚本方式上传

项目还提供了 `scripts/bohrium-kb-upload.py` 脚本，支持命令行上传：

```bash
# 单个文件上传
python3 scripts/bohrium-kb-upload.py ./paper.pdf --parent-id 456

# 批量上传目录下所有PDF
for f in pdfs/*.pdf; do
  python3 scripts/bohrium-kb-upload.py "$f" --parent-id 456
done
```

### 编辑文献信息

```python
r = requests.post(f"{BASE}/file/edit", headers=HEADERS_JSON, json={
    "id": 12345,
    "name": '{"cn":"中文标题","en":"English Title"}',
    "doi": "10.1234/example",
    "authors": '["Author A","Author B"]',
    "date": "2024-01-15",
    "journal": "Nature",
    "abstract": '{"cn":"中文摘要","en":"English abstract"}',
    "importance": 1,
    "recallable": True,
    "unableRecallEnMsg": "",
    "unableRecallZhMsg": ""
})
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | integer | 是 | 文献 ID |
| `name` | string (JSON) | 是 | `{"cn":"...","en":"..."}` 格式 |
| `doi` | string | 是 | DOI |
| `authors` | string (JSON array) | 是 | `["Author A","Author B"]` 格式 |
| `date` | string | 是 | 日期 `YYYY-MM-DD` |
| `journal` | string | 是 | 期刊名 |
| `abstract` | string (JSON) | 是 | `{"cn":"...","en":"..."}` 格式 |
| `importance` | integer | 是 | 重要程度 |
| `recallable` | boolean | 是 | 是否可被召回 |
| `unableRecallEnMsg` | string | 是 | 不可召回原因（英文） |
| `unableRecallZhMsg` | string | 是 | 不可召回原因（中文） |

### 删除文献

```python
r = requests.post(f"{BASE}/file/delete_literature", headers=HEADERS_JSON, json={
    "userResourceId": 12345     # 参数名是 userResourceId
})
```

### 重命名文献

```python
r = requests.post(f"{BASE}/file/update_literature", headers=HEADERS_JSON, json={
    "userResourceId": 12345,    # 参数名是 userResourceId
    "fileName": "New Literature Name"   # 参数名是 fileName
})
```

### 移动文献

```python
r = requests.post(f"{BASE}/file/move", headers=HEADERS_JSON, json={
    "fileNodesIdList": [12345, 12346],   # 文献节点 ID 列表（注意是数组）
    "folderNodesId": 789                 # 目标文件夹 nodesId
})
```

### 文献内容搜索

```python
r = requests.post(f"{BASE}/file/search", headers=HEADERS_JSON, json={
    "queryContent": "molecular dynamics simulation",
    "nodesId": 456,
    "knowledgeBaseId": 123
})
data = r.json()["data"]
print(f"共找到 {data['total']} 条结果")
for f in data["Files"]:
    print(f"  [{f['userResourceId']}] {f['fileName']}: {f['content'][:100]}...")
```

**返回字段：**

| 字段 | 说明 |
|------|------|
| `total` | 匹配总数 |
| `Files[].userResourceId` | 文献 ID |
| `Files[].fileName` | 文件名 |
| `Files[].content` | 匹配内容片段 |
| `Files[].knowledgeBaseName` | 所属知识库名称 |

### 文献元信息 / 辅助端点

```python
# 按 userResourceId 获取文献元信息（md5/paperId/publicationId 等）
requests.post(f"{BASE}/file/fileinfo", headers=HEADERS_JSON, json={
    "userResourceId": 12345,
    # 或用 "enclosureId": 67890
})

# 拿某文件夹下所有文献的 ID 列表（分页不需要）
requests.post(f"{BASE}/file/ids", headers=HEADERS_JSON, json={"parentId": 456})

# 单个文献的标签信息
requests.get(f"{BASE}/file/tagInfo", headers=HEADERS, params={"resourceId": 12345})

# 上传记录 / 容量
requests.get(f"{BASE}/file/upload/record", headers=HEADERS, params={"pageNum":1,"pageSize":10})
requests.get(f"{BASE}/file/capacity",      headers=HEADERS)   # {remainingCapacity, totalCapacity, usedCapacity}
```

---

## 标签管理

### 标签列表

```python
r = requests.get(f"{BASE}/tag", headers=HEADERS,
    params={"keyword": ""})  # 可选关键字过滤
data = r.json()["data"]
for tag in data["list"]:
    print(f"  [{tag['id']}] {tag['name']} ({tag['count']} 篇)")
```

### 创建标签

```python
r = requests.post(f"{BASE}/tag", headers=HEADERS_JSON, json={
    "name": "Machine Learning"
})
tag = r.json()["data"]
print(f"Created tag: {tag['id']} - {tag['name']}")
```

### 编辑标签

```python
r = requests.put(f"{BASE}/tag", headers=HEADERS_JSON, json={
    "tagId": 101,
    "name": "Deep Learning"
})
```

### 删除标签

```python
r = requests.delete(f"{BASE}/tag", headers=HEADERS_JSON, json={
    "tagId": 101
})
```

### 给文献打标签

```python
r = requests.post(f"{BASE}/file/tag", headers=HEADERS_JSON, json={
    "tagId": 101,
    "resourceId": 12345
})
```

### 取消文献标签

```python
r = requests.post(f"{BASE}/file/untag", headers=HEADERS_JSON, json={
    "tagId": 101,
    "resourceId": 12345
})
```

### 文献标签统计

```python
r = requests.get(f"{BASE}/file/tag", headers=HEADERS,
    params={
        "parentId": 456,       # 文件夹节点 ID（可选）
        "rootFolderId": 123,   # 知识库根文件夹 ID（可选）
        "query": 2,            # 1=按作者搜索, 2=按关键字搜索（可选）
        "keyword": "ML"        # 搜索关键字（可选）
    })
data = r.json()["data"]
print(f"总文献数: {data['allDocCount']}, 未打标签: {data['noTagCount']}")
for tag in data["tags"]:
    print(f"  [{tag['id']}] {tag['name']}: {tag['count']} 篇")
```

---

## 笔记

### 获取笔记

```python
r = requests.get(f"{BASE}/note", headers=HEADERS,
    params={"resourceId": 12345})
note = r.json()["data"]
print(f"笔记内容: {note['note']}")
```

### 创建/更新笔记

```python
r = requests.post(f"{BASE}/note", headers=HEADERS_JSON, json={
    "resourceId": 12345,
    "note": "This paper introduces a novel approach to..."
})
# {"code": 0}
```

---

## 文献召回与搜索

### 文献切片查看

查看特定文献的解析切片结果：

```python
r = requests.post(f"{BASE}/box/search_by_md5_paper_id", headers=HEADERS_JSON, json={
    "md5": "abc123...",
    "paper_id": "paper_001",
    "page_num": 1,
    "page_size": 10
})
```

### 指定文献召回

在指定文献中进行语义召回。**注意：upstream 字段名是 `papers`/`text`/`k`，不是 `query`/`paperIds`/`topK`。**

```python
r = requests.post(f"{BASE}/recall/papers", headers=HEADERS_JSON, json={
    "papers": [
        {"paperId": "paper_001", "md5": ""},
        {"paperId": "", "md5": "abc123..."}
    ],
    "text": "molecular dynamics force field",
    "k": 5
})
```

### 混合召回（知识库级）

在整个知识库中进行混合语义搜索。**注意：字段名用蛇形 (`knowledge_base_id`)；`keywords` 必填（不能为空字典）。**

```python
r = requests.post(f"{BASE}/recall/hybrid", headers=HEADERS_JSON, json={
    "knowledge_base_id": 456,                # 知识库 nodesId
    "text": "deep potential energy surface",
    "k": 10,
    "keywords": {"deep potential": 1.0, "energy surface": 0.5}   # 必填、非空
})
```

---

## 权限管理

> **重要：** 所有 `/account/*` 端点用 `nodesId`（知识库的节点 ID），**不是** `knowledgeBaseId`。

### 权限列表

```python
r = requests.get(f"{BASE}/account/acl", headers=HEADERS,
    params={"nodesId": YOUR_KB_NODES_ID})
# data: {privilege, shareMode, userList: [{id, role, isCreator, userName, ...}]}
```

### 设置分享状态

```python
r = requests.post(f"{BASE}/account/share_status", headers=HEADERS_JSON, json={
    "nodesId": YOUR_KB_NODES_ID,
    "privilege": 1,    # 1=公开, 2=私密
    "shareMode": 1     # 1=不分享, 2=链接分享
})
```

### 更新用户权限

```python
r = requests.post(f"{BASE}/account/user_role", headers=HEADERS_JSON, json={
    "nodesId": YOUR_KB_NODES_ID,
    "userId": 456,
    "role": 67801    # 见下方"角色值"说明
})
```

### 删除用户权限

```python
r = requests.delete(f"{BASE}/account/user_role", headers=HEADERS_JSON, json={
    "nodesId": YOUR_KB_NODES_ID,
    "userId": 456
})
```

### 批量添加读者

```python
r = requests.post(f"{BASE}/account/batch_add_readers", headers=HEADERS_JSON, json={
    "nodesId": YOUR_KB_NODES_ID,
    "userList": [
        {"id": 456, "role": 67801},
        {"id": 789, "role": 67801}
    ]
    # 或用 phones / emails / userNos 三选一：
    # "phones": ["13800000000"]
})
```

### 申请加入知识库

```python
r = requests.post(f"{BASE}/account/join_request", headers=HEADERS_JSON, json={
    "nodesId": YOUR_KB_NODES_ID
})
```

### 查询用户角色

```python
r = requests.get(f"{BASE}/account/user_knowledge_base_role", headers=HEADERS,
    params={"nodesId": YOUR_KB_NODES_ID})
# data: {roles: [int, ...]}
```

### 其他权限端点

| 端点 | 方法 | 用途 |
|------|------|------|
| `/account/knowledge_base/join/tree` | GET | 当前用户加入的所有知识库（树形） |
| `/account/knowledge_base/join/detail` | POST | 查询某知识库加入详情 `{nodesId}` |
| `/account/knowledge_base/exit` | POST | 主动退出知识库 `{nodesId}` |
| `/account/user_pending_join_req` | GET | 用户在某 KB 的待审申请 `?nodesId=` |
| `/account/join_request` | GET / PUT | 查询/审批加入申请 |
| `/account/join_request/personal` | GET | 自己提交的加入申请列表 |
| `/account/join_request/manageable` | GET | 自己可审批的加入申请 |
| `/account/feishu_bot/send_message` | POST | 飞书机器人发消息 `{type, msg}` |

---

## 权限角色说明

| 角色值 | 角色 | 权限 |
|--------|------|------|
| 1 | 拥有者 (Owner) | 完全控制：增删改查、权限管理、删除知识库 |
| 2 | 编辑者 (Editor) | 增删改查文献、管理标签和文件夹 |
| 3 | 阅读者 (Reader) | 只读：查看文献、下载、搜索 |

**知识库可见性（privilege）：**

| 值 | 说明 |
|----|------|
| 1 | 私有 — 仅拥有者和被授权用户可见 |
| 2 | 公开 — 所有人可发现和查看 |

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `code` 非 0 | API 调用错误 | 检查返回的 `error.msg` 或 `message` 字段获取具体错误信息 |
| 401 Unauthorized | 鉴权无效或过期 | 确认 BOHR_ACCESS_KEY 正确 |
| 找不到知识库 | 使用了错误的 ID | `nodesId`（节点 ID）和 `id`（知识库 ID）是不同概念；权限/文件夹端点统一用 `nodesId`，列表端点也会同时返回二者 |
| 404 page not found | 尝试访问下游 `/api/v2/*` 能力 | 网关统一转发到下游 `/api/v1/*`；本文档示例经此转发，均可正常使用 |
| `code=230606 keywords is required` | `recall/hybrid` 的 `keywords` 为空 | 至少传一个 `keyword: weight` 键值对 |
| `code=230105` | 文件相关端点参数名错 | `userResourceId`（不是 `resourceId`/`name`/`targetFolderId`）；详见上文示例 |
| 文献搜索无结果 | 文献尚未完成索引 | 新导入的文献需要等待后台解析和索引完成 |
| 编辑文献 name/abstract 格式错误 | 需要 JSON 字符串 | `name` 和 `abstract` 字段需要传 JSON 字符串如 `'{"cn":"...","en":"..."}'` |
| 文件夹操作报权限错误 | 角色权限不足 | 需要编辑者或拥有者角色才能修改；删除知识库（folder/delete 根 nodesId）需要 Owner |

## 网关限制说明

- 所有 `/openapi/v2/knowledge/<path>` 请求会被转发到 literature-sage `/api/v1/<path>`。
- literature-sage 的 `/api/v2/*` 下游能力（如 v2 版的 recall）通过本网关不可达。但本文档示例均经网关转发到下游 `/api/v1/*`，可正常使用。
- 知识库本身没有专用 delete 端点，删除等同于 `POST /folder/delete {nodesId: <KB_nodesID>}`。
