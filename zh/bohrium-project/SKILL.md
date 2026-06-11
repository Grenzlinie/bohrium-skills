---
name: bohrium-project
description: "Manage Bohrium projects via bohr CLI or open.bohrium.com API. Use when: user asks about creating/listing/deleting projects on Bohrium, managing project members, or setting cost limits. NOT for: job submission, node management, or image management."
---

# SKILL: Bohrium 项目 (Project) 管理

## 概述

管理 Bohrium 平台的项目。**优先使用 `bohr` CLI**，仅在 CLI 不支持的操作（如成员管理、费用设置、重命名）时回退到 API。

项目是 Node/Job/Image/Dataset 等资源的组织容器，也是团队协作和费用管理的基本单元。

## 认证配置

BOHR_ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"bohrium-project": {
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
```

---

## 列出项目

```bash
bohr project list               # 表格格式
bohr project list --json        # JSON 格式
bohr project list --csv         # CSV 格式
```

**JSON 输出字段：**

| 字段 | 说明 |
|------|------|
| `projectId` | 项目 ID |
| `name` | 项目名称 |

---

## 创建项目

```bash
bohr project create -n "my-experiment"
bohr project create -n "my-experiment" -m 5000          # 设置月费上限
bohr project create -n "my-experiment" -t 10000         # 设置总费上限
```

**参数说明：**

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--name` | `-n` | 是 | 项目名称（默认 "default"） |
| `--month_cost_limit` | `-m` | 否 | 月费用上限 |
| `--total_cost_limit` | `-t` | 否 | 总费用上限 |

---

## 删除项目

```bash
bohr project delete YOUR_PROJECT_ID
```

> **警告**：删除项目是**不可逆操作**，会删除项目下所有任务和镜像，且无法恢复。

---

## 项目角色与权限

Bohrium 项目有 3 种角色：

| 角色 | 说明 |
|------|------|
| 创建者 | 创建项目的用户，每个项目有且仅有一个，不可转让或删除 |
| 管理员 | 由创建者指定，可有多个，可随时任命或撤销 |
| 成员 | 被添加到项目的用户，默认角色 |

### 详细权限矩阵

| 功能模块 | 权限内容 | 创建者 | 管理员 | 成员 |
|---------|---------|:------:|:------:|:----:|
| 项目管理 | 修改项目名称 | ✓ | ✓ | ✗ |
| 项目管理 | 删除项目 | ✓ | ✗ | ✗ |
| 成员管理 | 添加/删除项目成员 | ✓ | ✓ | ✗ |
| 成员管理 | 任命/撤销管理员 | ✓ | ✗ | ✗ |
| 预算管理 | 查看/调整项目和个人预算 | ✓ | ✓ | ✗ |
| 节点管理 | 查看/操作项目内所有节点 | ✓ | ✓ | ✗ |
| 任务管理 | 查看/操作项目内所有任务 | ✓ | ✓ | ✗ |
| 镜像管理 | 查看/操作项目内所有镜像 | ✓ | ✓ | ✗ |
| 费用账单 | 查看/下载项目消费账单 | ✓ | ✓ | ✗ |

> **重要**：成员在项目中产生的费用直接消耗项目创建者钱包余额。

---

## 预算管理

### 项目预算

创建者和管理员可设置项目总预算（非必填）。不设置则默认"无限"。

当项目总费用超过预算时，成员将无法提交新任务或启动新节点。

### 成员预算

可为每个成员单独分配消费额度：
- "平均分配"：将项目总预算均分给所有成员
- "统一配置"：为每个成员设定相同额度
- 手动为不同成员设置不同额度

通过 API 设置项目费用上限：
```python
requests.post(f"{BASE}/set_cost_limit", headers=HEADERS_JSON,
    json={"projectId": YOUR_PROJECT_ID, "costLimit": 5000})
```

---

## 共享资源

### 共享文件盘 (/share)

每个项目有 1TB 免费共享空间，所有成员有读写权限。

- 通过 Web Shell 或文件管理页面访问 `/share` 目录
- 数据持久化存储，节点释放后数据保留
- 可购买额外容量

### 共享镜像

项目内所有成员可在 Bohrium 镜像中心 → 自定义镜像 看到其他成员创建的镜像，方便统一开发环境。

---

## 计费说明

| 计费项 | 说明 |
|--------|------|
| 计算资源 | 按任务使用计算资源的时长计费，价格随配置动态变化 |
| 开发机节点 | 启动后持续计费，不使用请及时停止或删除 |
| 个人存储 (/personal) | 500GB 免费，超出需购买 |
| 项目存储 (/share) | 1TB 免费，超出需购买 |

- 账户余额每 5 分钟扣款一次
- 余额低于警告阈值（默认 ¥100）时发送提醒邮件
- 余额归零后无法提交新任务

---

## 资源配额

| 资源 | 限制 |
|------|------|
| 项目数量 | 4 / 用户（仅自己创建的，参与的不计） |
| 节点数量 | 4 / (用户 × 项目) |
| 同时运行任务 | 100 / 用户 |
| 自定义镜像 | 10 / 项目 |
| 项目共享盘 | 1TB / 项目 |
| 个人数据盘 | 500GB / (用户 × 项目) |

> 如需增加配额，联系 Bohrium 客服。

---

## API 补充（CLI 不支持的操作）

以下操作 bohr CLI 不覆盖，需通过 API 完成：

```python
import os, requests

AK = os.environ.get("BOHR_ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi/v2/project"
HEADERS = {"Authorization": f"Bearer {AK}"}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}

# ── 获取详细项目列表（含费用、成员数等） ──
r = requests.get(f"{BASE}/list", headers=HEADERS)
# 返回: {items: [{id, name, totalCost, monthCost, userCount, projectRole, ...}]}

# ── 精简项目列表（仅 id+name） ──
r = requests.get(f"{BASE}/lite_list", headers=HEADERS)

# ── 重命名项目 ──
requests.post(f"{BASE}/set_name", headers=HEADERS_JSON,
    json={"projectId": YOUR_PROJECT_ID, "name": "new-name"})

# ── 设置费用上限 ──
requests.post(f"{BASE}/set_cost_limit", headers=HEADERS_JSON,
    json={"projectId": YOUR_PROJECT_ID, "costLimit": 5000})

# ── 查看项目成员 ──
r = requests.get(f"{BASE}/YOUR_PROJECT_ID/users", headers=HEADERS)
# 返回: {items: [{userId, userName, email, projectRole, cost, ...}]}

# ── 添加成员（通过 email） ──
requests.post(f"{BASE}/add_user", headers=HEADERS_JSON,
    json={"projectId": YOUR_PROJECT_ID, "email": "user@example.com"})

# ── 删除成员 ──
requests.post(f"{BASE}/del_user", headers=HEADERS_JSON,
    json={"projectId": YOUR_PROJECT_ID, "userId": 12345})

# ── 添加/删除管理员 ──
requests.post(f"{BASE}/manager/add", headers=HEADERS_JSON,
    json={"projectId": YOUR_PROJECT_ID, "userId": 12345})
requests.post(f"{BASE}/manager/del", headers=HEADERS_JSON,
    json={"projectId": YOUR_PROJECT_ID, "userId": 12345})

# ── 恢复已删除成员 ──
requests.put(f"{BASE}/YOUR_PROJECT_ID/recovery_user", headers=HEADERS_JSON,
    json={"userId": 12345})
```

### 项目角色 API 值

| projectRole | 含义 |
|-------------|------|
| 1 | 创建者/管理员 |
| 3 | 普通成员 |

---

## 不可用端点

以下端点通过 openapi auth 方式**无法访问**（返回 404）：

| 端点 | 原因 |
|------|------|
| `POST /project/join` | 路由转发路径不匹配 |
| `POST /project/share_status` | 同上 |
| `GET /project/available` | 注册在上游 AK v2 Group，openapi 网关 auth 不可达 |

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 创建项目后找不到 | 新项目在列表末尾 | `bohr project list --json` 查看全部 |
| 删除成员失败 | userId 错误 | 先通过 API `/{id}/users` 获取 userId |
| 添加成员无效 | email 不存在 | 确保目标用户已在 Bohrium 注册 |
| 项目数量达上限 | 每用户最多 4 个自建项目 | 删除不用的项目或联系客服增加配额 |
| 成员无法提交任务 | 项目或个人预算超限 | 创建者/管理员调整预算额度 |
| 余额不足 | 账户余额归零 | 充值后可恢复使用 |
