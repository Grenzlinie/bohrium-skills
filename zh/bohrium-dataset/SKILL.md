---
name: bohrium-dataset
description: "Manage Bohrium datasets via bohr CLI or open.bohrium.com API. Use when: user asks about creating/listing/deleting datasets on Bohrium, uploading data, or managing dataset versions. NOT for: file management, job submission, or node management."
---

# SKILL: Bohrium 数据集 (Dataset) 管理

## 概述

管理 Bohrium 平台的数据集。**优先使用 `bohr` CLI**，仅在 CLI 不支持的高级操作（如版本管理、配额查询）时回退到 API。

`bohr dataset create` 相比 Web 上传有两个优势：**无大小限制**、**支持断点续传**。

数据集提供数据导入、下载、版本管理、数据共享和挂载能力，解决以下场景：
- 每次提交任务都需要等待文件打包上传 → 使用数据集挂载避免重复上传
- 输入文件很大，上传耗时 → 数据集无大小限制、支持断点续传
- 需要与他人共享数据 → 数据集支持项目内共享

## 认证配置

BOHR_ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"bohrium-dataset": {
  "enabled": true,
  "apiKey": "YOUR_BOHR_ACCESS_KEY",
  "env": {
    "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.BOHR_ACCESS_KEY` 注入到运行环境。Skill 只需要配置 `BOHR_ACCESS_KEY`；兼容旧 CLI 所需的映射由辅助脚本内部处理。

## 前置条件：安装 bohr CLI

```bash
# macOS
/bin/bash -c "$(curl -fsSL https://dp-public.oss-cn-beijing.aliyuncs.com/bohrctl/1.0.0/install_bohr_mac_curl.sh)"

# Linux
/bin/bash -c "$(curl -fsSL https://dp-public.oss-cn-beijing.aliyuncs.com/bohrctl/1.0.0/install_bohr_linux_curl.sh)"

source ~/.bashrc  # 或 source ~/.zshrc
export PATH="$HOME/.bohrium:$PATH"
export OPENAPI_HOST=https://open.bohrium.com
```

---

## 列出数据集

```bash
bohr dataset list                       # 默认最近 50 个
bohr dataset list -n 10 --json          # JSON 格式，前 10 个
bohr dataset list -p 154                # 按项目 ID 过滤
bohr dataset list -t "my-dataset"       # 按标题搜索
```

**JSON 输出字段：**

| 字段 | 说明 |
|------|------|
| `id` | 数据集 ID |
| `title` | 数据集名称 |
| `path` | 挂载路径（如 `/bohr/my-dataset/v1`） |
| `projectName` | 所属项目 |
| `creatorName` | 创建者 |
| `updateTime` | 更新时间 |
| `desc` | 描述 |

---

## 创建数据集（上传数据）

```bash
bohr dataset create \
  -n "my-dataset" \
  -p "my-dataset" \
  -i 154 \
  -l "/path/to/local/data"
```

**参数说明：**

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--name` | `-n` | 是 | 数据集名称 |
| `--path` | `-p` | 是 | 数据集路径标识（英文+数字） |
| `--pid` | `-i` | 是 | 项目 ID |
| `--lp` | `-l` | 是 | 本地数据目录路径 |
| `--comment` | `-m` | 否 | 数据集描述 |

> **断点续传**：如果上传中断（网络问题等），重新运行相同命令并输入 `y` 即可从断点继续上传。

---

## 使用数据集

### 在计算任务中挂载

在 `job.json` 中添加 `dataset_path` 字段：

```json
{
  "job_name": "DeePMD-kit test",
  "command": "cd se_e2_a && dp train input.json > tmp_log 2>&1",
  "project_id": 154,
  "machine_type": "c4_m15_1 * NVIDIA T4",
  "job_type": "container",
  "image_address": "registry.dp.tech/dptech/deepmd-kit:2.1.5-cuda11.6",
  "dataset_path": ["/bohr/my-dataset/v1", "/bohr/another-dataset/v2"]
}
```

> `dataset_path` 和 `-p`（输入文件目录）可同时使用。

### 在开发机节点中挂载

创建容器开发机时选择需要挂载的数据集版本，启动后通过路径（如 `/bohr/my-dataset/v1`）直接访问。

- 挂载数据集增加 2-4 秒启动延迟（无论数量）
- 用 `df -a | grep bohr` 查看挂载点

### 在 Notebook 中使用

1. 在 Notebook 编辑页面展开侧面板 → 选择已有数据集
2. 鼠标悬停数据集名称 → 点击复制按钮获取路径
3. 在代码中使用路径：`cd /bohr/testdataset-6xwt/v1/`

> 数据集必须在连接节点**之前**添加，之后添加需重启节点才生效。

---

## 版本管理

数据集支持多版本管理，每个版本创建后文件不可更改。

### 创建新版本

通过 Web 界面：
1. 进入数据集详情页 → 点击"新建版本"
2. 系统自动导入最新版本的文件，可增删文件
3. 创建后需等待准备时间（取决于文件大小和数量）

通过 API：
```python
requests.post(f"{BASE}/{dataset_id}/version", headers=HEADERS_JSON,
    json={"versionDesc": "v2 update"})
```

### 版本状态

| status | 含义 |
|--------|------|
| 准备中 | 文件正在复制，其他用户暂不可见 |
| 已发布 | 可用状态 |

> 大文件或大量文件的版本准备可能需要较长时间。

---

## 删除数据集

```bash
bohr dataset delete 138201              # 删除单个
bohr dataset delete 138201 108601       # 批量删除
```

> 删除的版本无法恢复。

---

## 数据集权限模型

| 权限类型 | 说明 | 默认拥有者 |
|---------|------|-----------|
| 可管理 | 编辑、删除、创建新版本 | 数据集创建者、项目创建者和管理员 |
| 可使用 | 查看和使用数据集 | 数据集所属项目的全部成员 |

> 可通过编辑数据集将"可使用"权限授予其他项目或用户。

---

## API 补充（CLI 不支持的操作）

以下操作 bohr CLI 不覆盖，需通过 API 完成：

```python
import os, requests

AK = os.environ.get("BOHR_ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi/v1/ds"
HEADERS = {"Authorization": f"Bearer {AK}"}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}

# ── 获取数据集详情 ──
r = requests.get(f"{BASE}/{dataset_id}", headers=HEADERS)
# 返回: {id, title, path, versionId, projectName, ...}

# ── 获取数据集版本列表 ──
r = requests.get(f"{BASE}/{dataset_id}/version", headers=HEADERS)
# 返回: [{version, totalCount, totalSize, downloadUri, datasetPath, ...}]

# ── 获取指定版本详情 ──
r = requests.get(f"{BASE}/{dataset_id}/version/{version_id}", headers=HEADERS)

# ── 通过 API 创建数据集（程序化） ──
r = requests.post(f"{BASE}/", headers=HEADERS_JSON, json={
    "title": "my-dataset",
    "projectId": 154,
    "identifier": "my-dataset",  # 必填，唯一标识（英文+数字）
})
# 返回: {datasetId, tiefbluePath, requestId}
# 然后用 tiefblue 上传文件，再调用 commit

# ── 提交数据集（上传文件后调用） ──
requests.put(f"{BASE}/commit", headers=HEADERS_JSON,
    json={"datasetId": dataset_id})

# ── 创建新版本 ──
requests.post(f"{BASE}/{dataset_id}/version", headers=HEADERS_JSON,
    json={"versionDesc": "v2 update"})

# ── 修改数据集信息 ──
requests.put(f"{BASE}/{dataset_id}", headers=HEADERS_JSON,
    json={"title": "new-title"})

# ── 删除数据集版本 ──
requests.delete(f"{BASE}/{dataset_id}/version/{version_id}", headers=HEADERS)

# ── 检查配额 ──
r = requests.get(f"{BASE}/quota/check", headers=HEADERS,
    params={"projectId": 154})
# 返回: {result: true, limit: 30, used: 5}

# ── 获取上传 Token（用于 tiefblue 上传） ──
r = requests.get(f"{BASE}/input/token", headers=HEADERS,
    params={"projectId": 154, "path": "/bohr/my-dataset"})
# 返回: {token, path, host}

# ── 查看数据集权限 ──
r = requests.get(f"{BASE}/{dataset_id}/permission", headers=HEADERS)

# ── 获取关联项目列表 ──
r = requests.get(f"{BASE}/project", headers=HEADERS)
```

**重要**：数据集列表 API 路径是 `GET /v1/ds/`（**带尾部斜杠**），不是 `/v1/ds/list`（`/list` 会被 `/:id` 路由捕获报错）。

---

## 数据集内容说明

| 字段 | 说明 | 示例 |
|------|------|------|
| 数据集名称 | 可随时修改 | `testdataset` |
| 数据集路径 | 唯一标识，系统自动生成版本路径 | `/bohr/testdataset-b2dh/v1` |
| 文件 | 支持上传本地文件或文件夹 | - |
| 项目 | 数据集所属项目，项目成员默认可用 | `testproject` |
| 描述 | 数据集描述信息 | `用于训练的数据` |

## 数据集状态码

| status | 含义 |
|--------|------|
| 1 | 创建中/未提交 |
| 2 | 已提交/可用 |

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 上传中断 | 网络不稳定 | 重新运行同一命令，输入 `y` 续传 |
| 数据集路径找不到 | 挂载路径错误 | 用 `bohr dataset list --json` 查看 `path` 字段 |
| Job 中无法访问数据集 | 未在 job.json 中配置 | 添加 `"dataset_path": ["/bohr/xxx/v1"]` |
| `/ds/list` 返回错误 | 路由被 `/:id` 捕获 | 使用 `GET /ds/`（根路径）获取列表 |
| 创建缺少 identifier 报错 | `identifier` 是必填字段 | 添加 `identifier` 字段（英文+数字） |
| 版本准备中（约5分钟） | 文件正在复制到新版本存储 | 大文件耐心等待，失败联系客服 |
| Notebook 中数据集不可用 | 连接节点后才添加的数据集 | 需重启节点才能生效 |
