---
name: bohrium-image
description: "Manage Bohrium container images via bohr CLI or open.bohrium.com API. Use when: user asks about listing/pulling/creating/deleting Docker images on Bohrium, or finding available public images. NOT for: node management, job submission, or project management."
---

# SKILL: Bohrium 镜像 (Image) 管理

## 概述

管理 Bohrium 平台的容器镜像。**优先使用 `bohr` CLI**，仅在 CLI 不支持的操作（如从 Dockerfile 构建、搜索公共镜像版本）时回退到 API。

自 2023 年起，Bohrium 不再支持提交虚拟机任务，必须使用容器镜像。

## 认证配置

BOHR_ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"bohrium-image": {
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

## 列出镜像

```bash
# 列出自定义镜像（默认）
bohr image list                 # 表格格式
bohr image list --json          # JSON 格式

# 列出公共镜像（按类型）
bohr image list -t "Basic Image"
bohr image list -t "DeePMD-kit"
bohr image list -t "LAMMPS"
bohr image list -t "ABACUS"
bohr image list -t "CP2K"
bohr image list -t "GROMACS"
bohr image list -t "Uni-Mol"
```

**JSON 输出字段：**

| 字段 | 说明 |
|------|------|
| `imageId` | 镜像 ID |
| `name` | 镜像名称 |
| `url` | 完整镜像地址（`registry.dp.tech/...`） |
| `status` | 状态（available / building） |
| `creatorName` | 创建者 |

---

## 常用公共镜像速查

### 基础镜像

| 场景 | 镜像地址 |
|------|---------|
| CPU 基础 | `registry.dp.tech/dptech/ubuntu:20.04-py3.10` |
| CPU + Intel MPI | `registry.dp.tech/dptech/ubuntu:20.04-py3.10-intel2022` |
| GPU 基础 | `registry.dp.tech/dptech/ubuntu:20.04-py3.10-cuda11.6` |
| GPU + Intel MPI | `registry.dp.tech/dptech/ubuntu:20.04-py3.10-intel2022-cuda11.6` |

### 科学计算软件镜像

| 软件 | 容器镜像地址 |
|------|-------------|
| DeePMD-kit | `registry.dp.tech/dptech/deepmd-kit:2.1.5-cuda11.6` |
| DPGEN | `registry.dp.tech/dptech/dpgen:0.10.6` |
| LAMMPS | `registry.dp.tech/dptech/lammps:29Sep2021` |
| GROMACS | `registry.dp.tech/dptech/gromacs:2022.2` |
| Quantum-Espresso | `registry.dp.tech/dptech/quantum-espresso:7.1` |
| CP2K | `registry.dp.tech/dptech/cp2k:7.1` |
| ABACUS | `registry.dp.tech/dptech/abacus:3.0.0` |

### 所有 Bohrium 公共镜像预装软件

| 类别 | 预装软件 |
|------|---------|
| Python | python3.10, pip, Anaconda, Jupyter Lab |
| 文件管理 | wget, curl, unzip, rsync, tree, git |
| 编辑器 | emacs, vim |
| 编译工具 | cmake, build-essential (GNU) |
| 系统监控 | htop, ncdu, net-tools |
| DP 系列 | Bohrium CLI, DP-Dispatcher, dpdata |

---

## 容器镜像与虚拟机镜像映射

如果从虚拟机镜像迁移到容器镜像，可查阅此映射表：

| 虚拟机镜像 | 容器镜像地址 |
|-----------|-------------|
| `LBG_DeePMD-kit_2.1.4_v1` | `registry.dp.tech/dptech/deepmd-kit:2.1.5-cuda11.6` |
| `LBG_DP-GEN_0.10.6_v3` | `registry.dp.tech/dptech/dpgen:0.10.6` |
| `LBG_LAMMPS_stable_23Jun2022_v1` | `registry.dp.tech/dptech/lammps:29Sep2021` |
| `gromacs-dp:2020.2` | `registry.dp.tech/dptech/gromacs:2022.2` |
| `LBG_Quantum-Espresso_7.1` | `registry.dp.tech/dptech/quantum-espresso:7.1` |
| `LBG_Common_v1/v2` | `registry.dp.tech/dptech/ubuntu:20.04-py3.10-cuda11.6` |
| `LBG_oneapi_2021_v1` | `registry.dp.tech/dptech/ubuntu:20.04-py3.10-intel2022-cuda11.6` |

---

## 拉取镜像到本地

```bash
bohr image pull registry.dp.tech/dptech/deepmd-kit:3.0.0b3-cuda12.1
```

> **前提**：本地需要先启动 Docker。仅支持公共镜像和自己的自定义镜像。

### 手动 Docker Pull（替代方案）

需要将域名改为 `registry.bohrium.dp.tech`（不能用 `registry.dp.tech`）：

```bash
# 1. 登录（使用 Bohrium 账号密码）
docker login registry.bohrium.dp.tech

# 2. 拉取
docker pull registry.bohrium.dp.tech/dptech/ubuntu:22.04-py3.10-intel2022

# 注意：不支持 push 操作
```

---

## 删除自定义镜像

```bash
bohr image delete 121510                # 删除单个
bohr image delete 121510 121395         # 批量删除
```

---

## 镜像缓存机制

| 场景 | 说明 |
|------|------|
| 公共镜像 | 有持久化缓存，启动无需额外拉取 |
| 新建自定义镜像 | 构建后 10-30 分钟缓存生成，建议等待后再使用 |
| 30 天未使用的自定义镜像 | 缓存过期，下次使用需重新拉取（10-30分钟） |
| 缓存命中时的启动时间 | CPU ~20秒，GPU ~40秒 |
| 无缓存时的启动时间 | 需额外 10-30 分钟拉取镜像 |

---

## API 补充（CLI 不支持的操作）

### 搜索公共镜像版本

```python
import os, requests

AK = os.environ.get("BOHR_ACCESS_KEY", "")
HEADERS = {"Authorization": f"Bearer {AK}"}

# 搜索公共镜像版本（关键词）
r = requests.get("https://open.bohrium.com/openapi/v2/image/public/version/search",
    headers=HEADERS,
    params={"keyword": "deepmd", "page": 1, "pageSize": 5})
# 返回: {items: [{version, resourceType, size, url, imageName}, ...]}
```

### 公共镜像浏览

```python
# 公共镜像分类列表
r = requests.get("https://open.bohrium.com/openapi/v2/image/public",
    headers=HEADERS, params={"page": 1, "pageSize": 10})

# 公共镜像版本列表
r = requests.get(f"https://open.bohrium.com/openapi/v2/image/public/{image_id}/version",
    headers=HEADERS, params={"page": 1, "pageSize": 10})
```

### 从 Dockerfile 构建镜像

```python
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}

# 创建私有镜像（Dockerfile 构建）
# 注意：dockerfile 字段必须是 base64 编码的字符串
import base64
dockerfile_content = "FROM ubuntu:22.04\nRUN apt-get update && apt-get install -y python3"
dockerfile_b64 = base64.b64encode(dockerfile_content.encode()).decode()

r = requests.post("https://open.bohrium.com/openapi/v2/image/private",
    headers=HEADERS_JSON, json={
        "name": "my-image",
        "projectId": 154,
        "device": "container",
        "desc": "Custom training image",
        "buildType": 1,
        "dockerfile": dockerfile_b64,
    })

# 修改镜像描述
requests.put(f"https://open.bohrium.com/openapi/v2/image/private/{image_id}",
    headers=HEADERS_JSON, json={"desc": "updated"})

# 检查 Dockerfile 合法性（同样需要 base64 编码）
check_b64 = base64.b64encode(b"FROM ubuntu:22.04\nRUN apt-get update").decode()
requests.post("https://open.bohrium.com/openapi/v2/image/dockerfile/check",
    headers=HEADERS_JSON, json={"dockerfile": check_b64})

# 获取上次使用的镜像
r = requests.get("https://open.bohrium.com/openapi/v2/image/last_used",
    headers=HEADERS, params={"type": "public"})
```

### 私有镜像管理

```python
# 私有镜像列表（必须传 device 和 type 参数）
r = requests.get("https://open.bohrium.com/openapi/v2/image/private",
    headers=HEADERS,
    params={"device": "container", "type": "private", "page": 1, "pageSize": 10})
# 返回: {items: [{id, name, url, status, buildType, creatorName, projectName, ...}]}

# 私有镜像详情
r = requests.get(f"https://open.bohrium.com/openapi/v2/image/private/{image_id}",
    headers=HEADERS)

# 分享/取消分享（项目成员可见）
requests.post(f"https://open.bohrium.com/openapi/v2/image/{image_id}/share",
    headers=HEADERS_JSON)
requests.delete(f"https://open.bohrium.com/openapi/v2/image/{image_id}/share?device=container",
    headers=HEADERS)
```

---

## 自定义镜像制作

在容器开发机上安装好所需软件后，可将当前节点环境保存为自定义镜像：

1. 在 Bohrium Web 界面节点列表找到目标节点
2. 点击"保存镜像"按钮
3. 填写镜像名称和描述
4. 等待镜像构建完成

> 保存镜像时仅保存系统盘数据，`/personal` 和 `/share` 中的数据不会包含在镜像中。

## 资源配额

| 资源 | 限制 |
|------|------|
| 自定义镜像数 | 10 / 项目 |

## 不可用端点

| 端点 | 版本 | 原因 |
|------|------|------|
| `GET v1/image/public` | v1 | 路径被 `/:imageId` 路由捕获 |
| `GET v1/image/private` | v1 | 同上 |
| `POST v2/image/version/add` | v2 | bohrium-api 未注册此路由 |
| `DELETE v2/image/version/{versionId}` | v2 | 同上 |

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `bohr image pull` 失败 | Docker 未启动 | 先启动 Docker Desktop |
| v2 private 返回参数错误 | 缺少必填参数 | 加上 `device=container&type=private` 参数 |
| `no permission` | 非镜像创建者 | 只能操作自己创建的镜像 |
| v1 `/public` 返回解析错误 | 路由冲突 | 改用 v2 接口 |
| 镜像地址不对 | 用了镜像名而非完整地址 | 必须用 `registry.dp.tech/dptech/xxx:tag` 格式 |
| 自定义镜像缓存慢 | 缓存需 10-30 分钟生成 | 构建后等待 30 分钟再使用 |
| 容器节点不支持 Docker | 安全限制 | 如需 Docker 开发，用 VM 镜像 `LBG_Common_v2` |
| 创建镜像返回 decode err | dockerfile 未 base64 编码 | 使用 `base64.b64encode(content.encode()).decode()` 编码 |
