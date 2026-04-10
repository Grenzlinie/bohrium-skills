---
name: bohrium-knowledge-base
description: "Manage Bohrium knowledge bases via openapi.dp.tech API. Use when: user asks about creating/listing/searching knowledge bases, managing literature/papers, uploading files, tagging, notes, or searching literature content. NOT for: compute jobs, nodes, images, or datasets."
---

# SKILL: Bohrium Knowledge Base Management

## Overview

Manage knowledge bases (Literature Sage) on the Bohrium platform. Knowledge bases provide literature management, folder organization, tagging, notes, literature content search & recall, and permission management.

**No CLI support** — Unlike bohrium-job/node/image, knowledge bases have no `bohr` CLI commands. All operations use the HTTP API.

## Authentication

ACCESS_KEY is read from the OpenClaw config `~/.openclaw/openclaw.json`:

```json
"bohrium-knowledge-base": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

OpenClaw automatically injects `env.ACCESS_KEY` into the runtime.

## Route Mapping

```
External call: GET/POST https://openapi.dp.tech/openapi/v1/knowledge/{path}
               Header: accessKey: YOUR_ACCESS_KEY

Gateway forwards: → literature-sage.bohrium.com/api/v1/{path}
                  Header: X-User-Id, X-Org-Id (converted from accessKey)
```

## Common Code Template

```python
import os, requests

AK = os.environ.get("ACCESS_KEY", "")
BASE = "https://openapi.dp.tech/openapi/v1/knowledge"
HEADERS = {"accessKey": AK}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}
```

---

## Knowledge Base Management

### Create Knowledge Base

```python
r = requests.post(f"{BASE}/knowledge_base/create", headers=HEADERS_JSON, json={
    "knowledgeBaseName": "My Knowledge Base",
    "cover": "",
    "introduction": "A collection of papers on molecular dynamics",
    "privilege": 1  # 1=private, 2=public
})
print(r.json())
# {"code": 0, "data": {"id": 123, "msg": "Knowledge base created successfully."}}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `knowledgeBaseName` | string | Yes | Knowledge base name |
| `cover` | string | Yes | Cover image URL (can be empty string) |
| `introduction` | string | Yes | Knowledge base description |
| `privilege` | integer | Yes | 1=private, 2=public |

### List My Knowledge Bases

```python
r = requests.get(f"{BASE}/knowledge_base/list", headers=HEADERS,
    params={"keyword": "", "pageSize": 10, "pageNum": 1})
data = r.json()["data"]
for kb in data["list"]:
    print(f"[{kb['id']}] {kb['name']} (nodeId={kb['nodeId']}, privilege={kb['privilege']})")
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keyword` | string | No | Search keyword |
| `pageSize` | integer | No | Items per page (default 10) |
| `pageNum` | integer | No | Page number (default 1) |

**Response Fields:**

| Field | Description |
|-------|-------------|
| `id` | Knowledge base ID |
| `name` | Knowledge base name |
| `nodeId` | Knowledge base node ID (used for literature queries, folder operations) |
| `introduction` | Description |
| `cover` | Cover image URL |
| `privilege` | 1=private, 2=public |
| `isZotero` | Whether it's a Zotero-synced knowledge base |
| `count` | Literature count |
| `updateTime` | Update time (ISO 8601) |
| `createTime` | Creation time (ISO 8601) |
| `source` | Source identifier |
| `favoriteCount` | Favorite count |
| `sessionCount` | Session count |

### Update Knowledge Base

```python
r = requests.post(f"{BASE}/knowledge_base/update", headers=HEADERS_JSON, json={
    "knowledgeBaseName": "Updated Name",
    "cover": "",
    "introduction": "Updated introduction",
    "NodesId": 456,       # Knowledge base node ID
    "privilege": 2         # Change to public
})
# {"code": 0, "data": {"id": 123, "msg": "Knowledge base updated successfully."}}
```

### Knowledge Base Details

```python
node_id = 456
r = requests.get(f"{BASE}/knowledge_base/{node_id}", headers=HEADERS)
print(r.json())
```

### Discover Public Knowledge Bases

```python
r = requests.get(f"{BASE}/knowledge_base/discover", headers=HEADERS,
    params={"pageSize": 10, "pageNum": 1})
```

### Search Knowledge Bases

```python
r = requests.get(f"{BASE}/knowledge_base/search", headers=HEADERS,
    params={"keyword": "molecular dynamics"})
```

### Copy Knowledge Base

```python
r = requests.post(f"{BASE}/knowledge_base/copy", headers=HEADERS_JSON, json={
    "knowledgeBaseId": 123
})
```

---

## Folder Management

### List Root Directories (Knowledge Bases)

```python
r = requests.get(f"{BASE}/folder/root", headers=HEADERS)
data = r.json()["data"]
print(f"Total: {data['total']} knowledge bases, {data['docCount']} documents")
for item in data["list"]:
    print(f"  [{item['id']}] {item['name']} ({item['docCount']} docs, "
          f"relationship={'owner' if item['relationship'] == 1 else 'member'})")
```

**Response Fields:**

| Field | Description |
|-------|-------------|
| `total` | Number of knowledge bases |
| `list[].id` | Folder/knowledge base ID |
| `list[].name` | Name |
| `list[].docCount` | Document count |
| `list[].relationship` | 1=owner, 2=member |
| `docCount` | Total document count |

### List Children (One Level)

```python
r = requests.get(f"{BASE}/folder/children", headers=HEADERS,
    params={"folderId": 456, "pageNum": 1, "pageSize": 20})
data = r.json()["data"]

# Breadcrumb path
for p in data["path"]:
    print(f"  {'>' * p['depth']} {p['name']} (id={p['nodesId']})")

# Subfolders
for f in data["subFolders"]:
    print(f"  [DIR] {f['name']} ({f['docCount']} docs)")

# Files
for f in data["files"]:
    print(f"  [FILE] {f['name']} | {f['fileName']} | {f['date']}")
```

**Response Fields:**

| Field | Description |
|-------|-------------|
| `path[]` | Breadcrumb path `{nodesId, name, depth}` |
| `subFolders[]` | Subfolders `{nodesId, name, docCount, createdTime}` |
| `files[]` | Literature list |
| `files[].nodesId` | Literature node ID |
| `files[].paperId` | Paper ID |
| `files[].md5` | File MD5 |
| `files[].enName` | English title |
| `files[].zhName` | Chinese title |
| `files[].fileName` | File name |
| `files[].authors` | Author list |
| `files[].date` | Publication date |
| `files[].literatureType` | Literature type |
| `fileCount` | Total file count |

### Directory Tree

```python
r = requests.get(f"{BASE}/folder/directory", headers=HEADERS,
    params={"folderId": 456})
# Recursive tree: [{nodesId, name, subFolders: [{nodesId, name, subFolders: [...]}]}]
```

### Create Folder

```python
r = requests.post(f"{BASE}/folder/create", headers=HEADERS_JSON, json={
    "parentId": 456,             # Parent folder ID
    "folderName": "My Folder"
})
# {"code": 0, "data": {"message": "..."}}
```

### Rename Folder

```python
r = requests.post(f"{BASE}/folder/update", headers=HEADERS_JSON, json={
    "nodesId": 789,              # Folder node ID
    "folderName": "New Name"
})
```

### Move Folder

```python
r = requests.post(f"{BASE}/folder/move", headers=HEADERS_JSON, json={
    "sourceFolderId": 789,       # Source folder ID
    "targetFolderId": 456        # Target folder ID
})
```

### Delete Folder

```python
r = requests.post(f"{BASE}/folder/delete", headers=HEADERS_JSON, json={
    "nodesId": 789
})
```

---

## Literature Management

### List Literature

```python
r = requests.get(f"{BASE}/file", headers=HEADERS,
    params={
        "parentId": 456,        # Folder ID
        "pageNum": 1,
        "pageSize": 20,
        "order": "desc",        # asc / desc
        "orderBy": "createdTime",
        "noTag": False          # True = only untagged items
    })
```

### Literature Details

```python
r = requests.get(f"{BASE}/file/detail", headers=HEADERS,
    params={"resourceId": "12345"})
detail = r.json()["data"]
print(f"Title: {detail['enName']}")
print(f"Authors: {', '.join(a['name'] for a in detail.get('authorDetails', []))}")
print(f"DOI: {detail.get('doi', '')}")
print(f"Abstract: {detail.get('enAbstract', '')}")
```

**Response Fields (selected):**

| Field | Description |
|-------|-------------|
| `id` | Literature ID |
| `enName` / `zhName` | English / Chinese title |
| `authors` | Author list |
| `authorDetails[]` | Author details (scholarId, avatar, name, paperNums, citationNums, hIndex) |
| `doi` | DOI |
| `enAbstract` / `zhAbstract` | English / Chinese abstract |
| `date` | Publication date |
| `fileName` | File name |
| `md5` | File MD5 |
| `paperId` | Paper ID |
| `publicationEnName` | Journal name |
| `literatureType` | Literature type |
| `openAccess` | Open access flag |
| `existPDF` | PDF availability |
| `summary[]` | Section summaries `{title, zhTitle, content, zhContent}` |

### Download Literature Link

```python
r = requests.post(f"{BASE}/file/read", headers=HEADERS_JSON, json={
    "resourceId": 12345
})
# Returns download URL
```

### Upload File

Supports uploading local files (PDF, Markdown, etc.) to the knowledge base.

#### Upload Flow (Three Steps)

```
1) GET  /file/multipart   → Get upload credentials (host, path, token)
2) POST {host}/api/upload/binary  → Upload file binary content
3) POST /file/submit       → Register file to knowledge base (make it visible)
```

#### Get Upload Credentials

```python
# Calculate file MD5 and size
import hashlib
def md5_hex(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

# Get upload credentials
file_path = "paper.pdf"
file_name = "paper.pdf"
file_size = os.path.getsize(file_path)
file_md5 = md5_hex(file_path)
parent_id = 456  # NodeId of knowledge base or folder

r = requests.get(f"{BASE}/file/multipart", headers=HEADERS,
    params={
        "fileName": file_name,
        "md5": file_md5,
        "parentId": parent_id,
        "size": file_size
    })

multipart_data = r.json()["data"]
if multipart_data.get("fileExist"):
    print("File already exists, no need to upload again")
else:
    host = multipart_data["host"]
    path = multipart_data["path"]
    token = multipart_data["token"]
    print(f"Successfully obtained upload credentials: {host}, {path}")
```

#### Execute Binary Upload

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

# Upload file to storage service
file_content = open(file_path, "rb").read()
content_type = "application/pdf"  # Or other appropriate MIME type
encoded_file_name = urllib.parse.quote(file_name, safe="-_.!~*'()")

storage_param = make_storage_param(path, encoded_file_name, content_type)
upload_url = host.rstrip("/") + "/api/upload/binary"

req = urllib.request.Request(upload_url, method="POST", data=file_content)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("X-Storage-Param", storage_param)
req.add_header("Content-Type", "application/octet-stream")

with urllib.request.urlopen(req, timeout=300) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))

print("Binary file upload completed")
```

#### Register File to Knowledge Base

```python
# Register the uploaded file to the knowledge base to make it visible in the KB
final_path = (upload_result.get("data") or {}).get("path") or path

r = requests.post(f"{BASE}/file/submit", headers=HEADERS_JSON, json={
    "parentId": parent_id,
    "fileName": file_name,
    "md5": file_md5,
    "size": file_size,
    "url": final_path  # Path returned after upload completes
})

result = r.json()
if result.get("code") == 0:
    print("File successfully registered to knowledge base")
elif result.get("code") == 230117:  # File already exists
    print("File already exists in knowledge base")
else:
    print(f"Registration failed: {result}")
```

#### Complete Upload Function Example

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
    # Prepare file info
    file_name = custom_file_name or os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # Calculate MD5
    def md5_hex(path):
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    file_md5 = md5_hex(file_path)

    # Step 1: Get upload credentials
    r = requests.get(f"{BASE}/file/multipart", headers=HEADERS,
        params={
            "fileName": file_name,
            "md5": file_md5,
            "parentId": parent_id,
            "size": file_size
        })

    multipart_data = r.json()["data"]

    if multipart_data.get("fileExist"):
        print("File already exists, skipping upload but registering to knowledge base...")

        # Even if file exists, still need to register to knowledge base
        r_submit = requests.post(f"{BASE}/file/submit", headers=HEADERS_JSON, json={
            "parentId": parent_id,
            "fileName": file_name,
            "md5": file_md5,
            "size": file_size,
            "url": multipart_data.get("path", "")  # Use existing path
        })
        return r_submit.json()

    # Get upload credentials
    host = multipart_data["host"]
    path = multipart_data["path"]
    token = multipart_data["token"]

    # Prepare upload parameters
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

    # Step 2: Binary upload
    file_content = open(file_path, "rb").read()
    upload_url = host.rstrip("/") + "/api/upload/binary"

    req = urllib.request.Request(upload_url, method="POST", data=file_content)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-Storage-Param", storage_param)
    req.add_header("Content-Type", "application/octet-stream")

    with urllib.request.urlopen(req, timeout=300) as resp:
        upload_result = json.loads(resp.read().decode("utf-8"))

    # Step 3: Register file to knowledge base
    final_path = (upload_result.get("data") or {}).get("path") or path

    r_submit = requests.post(f"{BASE}/file/submit", headers=HEADERS_JSON, json={
        "parentId": parent_id,
        "fileName": file_name,
        "md5": file_md5,
        "size": file_size,
        "url": final_path
    })

    return r_submit.json()

# Example usage
result = upload_file_to_knowledge_base("./paper.pdf", 456)
print(result)
```

#### Idempotency

If the file already exists (`fileExist=true`), the system skips the binary upload step but still calls the submit interface to ensure the file is visible in the knowledge base. This makes uploading the same file multiple times a safe operation.

#### Script-based Upload

The project also provides a `scripts/bohrium-kb-upload.py` script that supports command-line uploads:

```bash
# Upload a single file
python3 scripts/bohrium-kb-upload.py ./paper.pdf --parent-id 456

# Batch upload all PDFs in directory
for f in pdfs/*.pdf; do
  python3 scripts/bohrium-kb-upload.py "$f" --parent-id 456
done
```

### Edit Literature Metadata

```python
r = requests.post(f"{BASE}/file/edit", headers=HEADERS_JSON, json={
    "id": 12345,
    "name": '{"cn":"Chinese Title","en":"English Title"}',
    "doi": "10.1234/example",
    "authors": '["Author A","Author B"]',
    "date": "2024-01-15",
    "journal": "Nature",
    "abstract": '{"cn":"Chinese abstract","en":"English abstract"}',
    "importance": 1,
    "recallable": True,
    "unableRecallEnMsg": "",
    "unableRecallZhMsg": ""
})
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Literature ID |
| `name` | string (JSON) | Yes | `{"cn":"...","en":"..."}` format |
| `doi` | string | Yes | DOI |
| `authors` | string (JSON array) | Yes | `["Author A","Author B"]` format |
| `date` | string | Yes | Date `YYYY-MM-DD` |
| `journal` | string | Yes | Journal name |
| `abstract` | string (JSON) | Yes | `{"cn":"...","en":"..."}` format |
| `importance` | integer | Yes | Importance level |
| `recallable` | boolean | Yes | Whether it can be recalled |
| `unableRecallEnMsg` | string | Yes | Non-recall reason (English) |
| `unableRecallZhMsg` | string | Yes | Non-recall reason (Chinese) |

### Delete Literature

```python
r = requests.post(f"{BASE}/file/delete_literature", headers=HEADERS_JSON, json={
    "resourceId": 12345
})
```

### Rename Literature

```python
r = requests.post(f"{BASE}/file/update_literature", headers=HEADERS_JSON, json={
    "resourceId": 12345,
    "name": "New Literature Name"
})
```

### Move Literature

```python
r = requests.post(f"{BASE}/file/move", headers=HEADERS_JSON, json={
    "resourceId": 12345,
    "targetFolderId": 789
})
```

### Search Literature Content

```python
r = requests.post(f"{BASE}/file/search", headers=HEADERS_JSON, json={
    "queryContent": "molecular dynamics simulation",
    "nodesId": 456,
    "knowledgeBaseId": 123
})
data = r.json()["data"]
print(f"Found {data['total']} results")
for f in data["Files"]:
    print(f"  [{f['userResourceId']}] {f['fileName']}: {f['content'][:100]}...")
```

**Response Fields:**

| Field | Description |
|-------|-------------|
| `total` | Total matches |
| `Files[].userResourceId` | Literature ID |
| `Files[].fileName` | File name |
| `Files[].content` | Matched content snippet |
| `Files[].knowledgeBaseName` | Knowledge base name |

---

## Tag Management

### List Tags

```python
r = requests.get(f"{BASE}/tag", headers=HEADERS,
    params={"keyword": ""})  # Optional keyword filter
data = r.json()["data"]
for tag in data["list"]:
    print(f"  [{tag['id']}] {tag['name']} ({tag['count']} docs)")
```

### Create Tag

```python
r = requests.post(f"{BASE}/tag", headers=HEADERS_JSON, json={
    "name": "Machine Learning"
})
tag = r.json()["data"]  # Note: API response field may be "daya" (known typo)
print(f"Created tag: {tag['id']} - {tag['name']}")
```

### Edit Tag

```python
r = requests.put(f"{BASE}/tag", headers=HEADERS_JSON, json={
    "tagId": 101,
    "name": "Deep Learning"
})
```

### Delete Tag

```python
r = requests.delete(f"{BASE}/tag", headers=HEADERS_JSON, json={
    "tagId": 101
})
```

### Tag Literature

```python
r = requests.post(f"{BASE}/file/tag", headers=HEADERS_JSON, json={
    "tagId": 101,
    "resourceId": 12345
})
```

### Untag Literature

```python
r = requests.post(f"{BASE}/file/untag", headers=HEADERS_JSON, json={
    "tagId": 101,
    "resourceId": 12345
})
```

### Literature Tag Statistics

```python
r = requests.get(f"{BASE}/file/tag", headers=HEADERS,
    params={
        "parentId": 456,       # Folder node ID (optional)
        "rootFolderId": 123,   # Knowledge base root folder ID (optional)
        "query": 2,            # 1=search by author, 2=search by keyword (optional)
        "keyword": "ML"        # Search keyword (optional)
    })
data = r.json()["data"]
print(f"Total docs: {data['allDocCount']}, Untagged: {data['noTagCount']}")
for tag in data["tags"]:
    print(f"  [{tag['id']}] {tag['name']}: {tag['count']} docs")
```

---

## Notes

### Get Note

```python
r = requests.get(f"{BASE}/note", headers=HEADERS,
    params={"resourceId": 12345})
note = r.json()["data"]
print(f"Note: {note['note']}")
```

### Create/Update Note

```python
r = requests.post(f"{BASE}/note", headers=HEADERS_JSON, json={
    "resourceId": 12345,
    "note": "This paper introduces a novel approach to..."
})
# {"code": 0}
```

---

## Literature Recall & Search

### View Literature Slices

View parsed slices of a specific paper:

```python
r = requests.post(f"{BASE}/box/search_by_md5_paper_id", headers=HEADERS_JSON, json={
    "md5": "abc123...",
    "paper_id": "paper_001",
    "page_num": 1,
    "page_size": 10
})
```

### Recall from Specific Papers

Perform semantic recall within specified papers:

```python
r = requests.post(f"{BASE}/recall/papers", headers=HEADERS_JSON, json={
    "query": "molecular dynamics force field",
    "paperIds": ["paper_001", "paper_002"],
    "topK": 5
})
```

### Hybrid Recall (Knowledge Base Level)

Perform hybrid semantic search across an entire knowledge base:

```python
r = requests.post(f"{BASE}/recall/hybrid", headers=HEADERS_JSON, json={
    "query": "deep potential energy surface",
    "knowledgeBaseId": 123,
    "topK": 10
})
```

---

## Permission Management

### List Permissions

```python
r = requests.get(f"{BASE}/account/acl", headers=HEADERS,
    params={"knowledgeBaseId": 123})
```

### Set Share Status

```python
r = requests.post(f"{BASE}/account/share_status", headers=HEADERS_JSON, json={
    "knowledgeBaseId": 123,
    "shareStatus": 1  # 1=enable sharing, 0=disable
})
```

### Update User Role

```python
r = requests.post(f"{BASE}/account/user_role", headers=HEADERS_JSON, json={
    "knowledgeBaseId": 123,
    "userId": 456,
    "role": 2  # See role reference below
})
```

### Remove User Permission

```python
r = requests.delete(f"{BASE}/account/user_role", headers=HEADERS_JSON, json={
    "knowledgeBaseId": 123,
    "userId": 456
})
```

### Batch Add Readers

```python
r = requests.post(f"{BASE}/account/batch_add_readers", headers=HEADERS_JSON, json={
    "knowledgeBaseId": 123,
    "userIds": [456, 789, 1011]
})
```

### Request to Join Knowledge Base

```python
r = requests.post(f"{BASE}/account/join_request", headers=HEADERS_JSON, json={
    "knowledgeBaseId": 123
})
```

### Query User Role

```python
r = requests.get(f"{BASE}/account/user_knowledge_base_role", headers=HEADERS,
    params={"knowledgeBaseId": 123})
```

---

## Permission Roles Reference

| Role Value | Role | Permissions |
|------------|------|------------|
| 1 | Owner | Full control: CRUD, permission management, delete knowledge base |
| 2 | Editor | CRUD literature, manage tags and folders |
| 3 | Reader | Read-only: view, download, search literature |

**Knowledge Base Visibility (privilege):**

| Value | Description |
|-------|-------------|
| 1 | Private — visible only to owner and authorized users |
| 2 | Public — discoverable and viewable by everyone |

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `code` is non-zero | API call error | Check the `message` field in the response for details |
| 401 Unauthorized | Invalid or expired accessKey | Verify ACCESS_KEY is correct |
| Knowledge base not found | Wrong ID used | `nodeId` (node ID) and `id` (knowledge base ID) are different; use the correct one per API |
| Literature search returns empty | Literature not yet indexed | Newly imported literature needs time for backend parsing and indexing |
| Edit literature name/abstract format error | JSON string required | `name` and `abstract` fields require JSON strings like `'{"cn":"...","en":"..."}'` |
| Create tag returns `daya` | Known API typo | `daya` in response equals `data`; use it directly |
| Folder operation permission error | Insufficient role | Requires Editor (2) or Owner (1) role to modify |
