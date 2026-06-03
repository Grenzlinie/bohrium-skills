---
name: bohrium-node
description: "Manage Bohrium dev nodes (containers/VMs) via open.bohrium.com API. Use when: user asks about creating/querying dev machines on Bohrium, checking available resources and pricing, or managing node lifecycle. NOT for: job submission, image management, or project management."
---

# SKILL: Bohrium 开发机 (Node) 管理

## 概述

管理 Bohrium 平台的开发机（容器/虚拟机节点），通过 OpenAPI 完成查询和自动化操作。

开发机用于数据准备、编译调试、结果处理等场景，支持 Web Shell 和 SSH 两种连接方式。

## 认证配置

BOHR_ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"bohrium-node": {
  "enabled": true,
  "apiKey": "YOUR_BOHR_ACCESS_KEY",
  "env": {
    "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.BOHR_ACCESS_KEY` 注入到运行环境。Skill 只需要配置 `BOHR_ACCESS_KEY`；兼容旧 CLI 所需的映射由辅助脚本内部处理。

## 列出节点

```bash
python node_manager.py list
python node_manager.py list --page 1 --page-size 20
```

**JSON 输出字段：**

| 字段 | 说明 |
|------|------|
| `nodeId` | 节点 ID |
| `nodeName` | 节点名称 |
| `status` | Started / Paused / Pending / Waiting |
| `cpu` / `memory` / `gpu` | 资源配置 |
| `ip` | 公网 IP |
| `imageName` | 使用的镜像 |
| `cost` | 累计费用 |

---

## 创建节点

```bash
bohr node create
```

> 交互式创建，依次选择：项目 → 镜像 → 机器类型 → 节点名称 → 磁盘大小。

**注意**：`bohr node create` 是交互式的，在自动化脚本中需要通过 API 创建（见下方 API 补充）。

**推荐容器镜像：**

| 场景 | 镜像地址 |
|------|---------|
| CPU 基础开发 | `registry.dp.tech/dptech/ubuntu:20.04-py3.10` |
| CPU + Intel MPI | `registry.dp.tech/dptech/ubuntu:20.04-py3.10-intel2022` |
| GPU 基础开发 | `registry.dp.tech/dptech/ubuntu:20.04-py3.10-cuda11.6` |
| GPU + Intel MPI | `registry.dp.tech/dptech/ubuntu:20.04-py3.10-intel2022-cuda11.6` |

---

## 连接节点

### 免密 SSH（推荐）

```bash
bohr node connect 1431145       # 通过 nodeId 直接 SSH 连接
```

> 无需记忆 SSH 密码，bohr 自动处理认证。

### Web Shell

通过 Bohrium Web 界面连接，点击节点卡片 → Connect → Open Web Shell，自动以 root 登录。

### SSH（手动）

通过 API 获取节点详情可获得 `ip`、`nodeUser`、`nodePwd` 信息：
```bash
ssh root@<domain_name>
# 密码从 API 获取
```

---

## 停止/删除节点

```bash
bohr node stop 1431145          # 停止节点（不计费，数据保留）
bohr node delete 1431145        # 删除节点（不可逆）
```

> **重要**：节点启动后持续计费，不使用时请及时停止或删除。

---

## 节点存储与网络

| 项目 | 说明 |
|------|------|
| **系统盘** | 创建时选择的磁盘大小（最大 100G），存放系统软件包 |
| **个人数据盘 /personal** | 500GB/用户/项目，持久化存储，节点释放后数据保留 |
| **项目共享盘 /share** | 1TB/项目，项目成员共享读写 |
| **公网端口** | 50001-50005 默认开放公网访问 |
| **GPU 驱动** | 默认 v525，不可自行安装或升级 |
| **Docker** | 容器节点内**不支持**运行 Docker（安全限制） |

---

## 挂载数据集

创建容器节点时可选择挂载数据集，挂载后在节点内通过路径（如 `/bohr/my-dataset/v1`）直接访问。

- 挂载数据集会额外增加 2-4 秒启动延迟（无论数量多少）
- 通过 `df -a | grep bohr` 查看挂载点（`df -h` 会去重只显示一个）

---

## 启动时间与镜像缓存

| 场景 | 启动时间 |
|------|---------|
| 有镜像缓存的 CPU 机器 | ~20 秒 |
| 有镜像缓存的 GPU 机器 | ~40 秒 |
| 资源紧张时的 GPU 机器 | 1-5 分钟 |
| 无镜像缓存（新建/过期） | 10-30 分钟（拉取镜像） |

**镜像缓存规则：**
- 公共镜像有持久化缓存，启动无需额外拉取
- 自定义镜像构建后 10-30 分钟内缓存生成，建议等待后再使用
- 自定义镜像 30 天未使用则缓存过期，下次启动需重新拉取
- 计费从资源分配后开始，即使仍在拉取镜像

---

## API 补充（CLI 不支持的操作）

以下操作可通过 API 完成：

```python
import os, requests

AK = os.environ.get("BOHR_ACCESS_KEY", "")
BASE = "https://open.bohrium.com/openapi/v1/node"
HEADERS = {"Authorization": f"Bearer {AK}"}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}

# ── 程序化创建节点（非交互式） ──
r = requests.post(f"{BASE}/add", headers=HEADERS_JSON, json={
    "projectId": 154,
    "name": "my-node",
    "imageId": 2168,  # 从 bohr image list --json 获取
    "machineConfig": {"type": 0, "value": 388, "label": "c2_m4_cpu"},
    "diskSize": 20,
})
# 返回: {"code": 0, "data": {"machineId": 1427300}}

# ── 查询可用机器资源 ──
r = requests.get(f"{BASE}/resources", headers=HEADERS)
# 返回: {disks: [20,40,80,100], cpuList: [...], gpuList: [...]}
# 其中 value 即 skuId，用于创建节点和查询价格

# ── 查询资源价格 ──
r = requests.get(f"{BASE}/resources/price",
    headers=HEADERS, params={"skuId": 388, "projectId": 154})
# 返回: {"data": {"price": "0.4"}}  (元/小时)

# ── 获取节点详情（含 SSH 密码） ──
r = requests.get(f"{BASE}/{machine_id}", headers=HEADERS)
# 返回: {nodeId, nodeName, status, ip, nodeUser, nodePwd, domainName, ...}

# ── 重启节点（需先停止） ──
requests.post(f"{BASE}/restart/{machine_id}", headers=HEADERS)

# ── 修改节点名称 ──
requests.post(f"{BASE}/modify/{machine_id}", headers=HEADERS_JSON,
    json={"name": "new-name"})

# ── 查看/绑定数据集 ──
r = requests.get(f"{BASE}/ds", headers=HEADERS, params={"nodeId": node_id})
requests.post(f"{BASE}/ds/bind", headers=HEADERS_JSON,
    json={"nodeId": node_id, "datasetId": dataset_id})
```

---

## 节点状态码

| status | 含义 | bohr CLI 显示 |
|--------|------|---------------|
| 2 | 运行中 | Started |
| -1 | 已停止/已释放 | Paused |

## 资源配额

| 资源 | 限制 |
|------|------|
| 节点数量 | 4 / (用户 × 项目) |
| 系统盘 | 最大 100GB |
| 个人数据盘 | 500GB / (用户 × 项目) |
| 项目共享盘 | 1TB / 项目 |

## SSH 与 Web Shell 环境差异

| 连接方式 | 环境变量来源 |
|---------|-------------|
| Web Shell | 系统环境变量 + `/root/.bashrc` |
| SSH | 仅 `/root/.bashrc`（会覆盖全局变量） |

> 如果 SSH 和 Web Shell 中环境变量不一致，检查 `/root/.bashrc` 中的配置。

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `There is no resource for the selected machine` | 所选规格暂无库存 | 换一个规格或稍后重试 |
| `record not found` | machineId 不存在或已删除 | 先通过 `python node_manager.py list` 确认有效 ID |
| 重启失败 | 节点未处于 stopped 状态 | 先 `bohr node stop`，等变为 Paused 再用 API 重启 |
| `nodeId` vs `machineId` | 列表返回两个 ID 字段 | CLI 用 `nodeId`；API 详情/操作用 `machineId`；数据集接口用 `nodeId` |
| SSH 连接失败 | 镜像不含 SSH 组件 | DockerHub 公共镜像通常无 SSH，需手动安装 |
| 域名连接失败 | 停机超 7 天域名过期 | 重启后等待 10-30 分钟 DNS 生效，期间用 Web Shell |
| 终端响应慢 | VPN/网络问题或浏览器标签页内存 | 关闭 VPN 测试，刷新页面重连 |
| 无法运行 Docker | 容器节点安全限制 | 如需 Docker 开发，使用虚拟机镜像 `LBG_Common_v2` 创建 VM 节点 |
| 镜像拉取中 | 自定义镜像缓存未生成或已过期 | 等待 10-30 分钟缓存生成后再启动 |
