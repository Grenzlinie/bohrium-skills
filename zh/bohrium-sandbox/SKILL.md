---
name: bohrium-sandbox
description: "Bohrium 平台沙箱 (lbg sdbx CLI)：按需创建的临时云 VM，用于运行 shell / Python，可挂 GPU、可挂用户存储。Use when: 用户需要在隔离环境跑代码、调试脚本、做数据处理、跑 GPU 任务。NOT for: Bohrium 计算任务 (用 bohrium-job) 或长期开发机 (用 bohrium-node)。"
---

# SKILL: Bohrium Sandbox (`lbg sdbx`)

## 概述

Bohrium Sandbox 是平台提供的按需云 VM，通过 `lbg sdbx` CLI 操作。不是 E2B SDK、不需要 `E2B_API_KEY`、不走 `api.e2b.dev` —— 完全跑在 Bohrium 平台上，用 Bohrium AccessKey 鉴权。

**核心能力**：

- 从模板创建沙箱（CPU / GPU 都有）
- `exec` 跑命令（前台 / 后台 / PTY 三种模式）
- `files read/write` 上传下载文件或目录
- `terminal` 开 PTY 跑交互式工作流（REPL / TUI）
- 可挂用户个人盘 + share 盘
- 计费可走个人钱包或项目预算

**与其他 skill 的关系**：

| 场景 | 用什么 |
|------|--------|
| 跑一段脚本验证想法、调试、GPU 推理小批量 | **本 skill (bohrium-sandbox)** |
| 提交大规模批处理 / 长任务 | `bohrium-job` |
| 长期开发机（带 SSH / VSCode） | `bohrium-node` |

---

## 安装

`sdbx` 子命令目前只在 **prerelease (beta) 版本** 的 `lbg` 上有。稳定版的 `lbg` 没有 `sdbx`，会报 `invalid choice: 'sdbx'`。

```bash
# 必须装 prerelease，否则 lbg sdbx 不存在
pip install --pre --upgrade lbg

# 验证
lbg sdbx --help    # 应能看到 doctor / create / list / exec / files / terminal 等子命令
```

版本历史见 <https://pypi.org/project/lbg/#history>。当前 beta 形如 `4.0.0bNN`。

## 配置

需要 Bohrium AccessKey（不是 E2B）。两种方式：

```bash
# 1. 一次性登录（写入本地配置）
lbg login --ak "$BOHR_ACCESS_KEY"

# 2. 临时环境变量
export BOHR_ACCESS_KEY=<YOUR_BOHR_ACCESS_KEY>
```

验证：

```bash
lbg sdbx doctor --json   # 检查鉴权 / SDK / 网关
```

---

## 沙箱生命周期

### 创建

```bash
# 默认模板 sdbxagent（CPU），个人钱包计费，默认 12h 超时
lbg sdbx create --json

# 指定模板
lbg sdbx create my-template --json

# 改用项目预算计费
lbg sdbx create my-template --project-id <id> --json

# 改超时（秒）；0 = 不限
lbg sdbx create my-template --timeout 1800 --json
lbg sdbx create my-template --never-timeout --json

# 挂载个人存储 + share 盘
lbg sdbx create my-template --mount-user-storage --json
```

返回字段：`sandboxID`（后续命令都用它）、`templateID`、`state`、`cpuCount`、`memoryMB`、`metadata`。

> 注意：`templateID` 接收模板的 **name**（不是 SKU、不是数字 id）。用 `lbg sdbx template ls` 查。

### 查看 / 描述 / 进程

```bash
lbg sdbx list --json                                   # 列出我的沙箱
lbg sdbx describe <sandbox_id> --with-processes --json # 元信息 + 进程
lbg sdbx ps <sandbox_id> --json                        # 进程列表
```

`list` 默认带 `age` 列，超过 30 分钟的会高亮警告（提醒清理）。

### 销毁

```bash
lbg sdbx kill <sandbox_id> --json
```

安全机制：

- 没有进程在跑 → 静默 kill
- 有进程 + TTY → 交互确认
- 有进程 + 非 TTY（agent / CI / 管道） → **拒绝**，需 `--force` 显式确认

**销毁后无法读取文件 —— 重要产物必须先 `files read` 拉到本地再 kill。**

---

## 模板管理

```bash
lbg sdbx template ls              # 列我创建过的模板
lbg sdbx template ls --json
lbg sdbx template ls -q           # 仅 name，方便管道喂给 create

# 创建模板（需要 image path + SKU name）
lbg image ls                      # 找 image path
lbg sdbx machine list             # 找 SKU
lbg sdbx template create --name <name> --image <image-path> --sku-name <sku>

# 删除（TTY 交互确认；非 TTY 必须 --force）
lbg sdbx template rm <name>
lbg sdbx template rm <name> --force --json
```

GPU 工作流：用 GPU 模板快捷名（见 `platform-snapshot.md`），创建后 `exec nvidia-smi` 验证。

---

## 运行命令：`exec`

`exec` 把位置参数拼成一个 shell 字符串，送进 `bash -l -c`。shell 操作符（`&&` / `|` / `>`）直接写。

### 前台

```bash
lbg sdbx exec <sandbox_id> 'pwd' --json
lbg sdbx exec <sandbox_id> 'cd /workspace && python train.py'
lbg sdbx exec <sandbox_id> 'cat log.txt | grep ERROR | wc -l'
```

默认 `--timeout 60`（秒）。前台命令同步阻塞，返回 `stdout/stderr/exit_code`。**60 秒内能跑完的才用前台。**

### 后台

```bash
lbg sdbx exec --background <sandbox_id> 'python train.py > /workspace/out/run.log 2>&1'
# 返回 {"pid": N, ...}
```

后台模式：

- `--timeout` 默认 `0`（不限）。**不要传有限的 `--timeout`**，会到点把任务杀掉（CLI 会警告）
- 状态查询：`lbg sdbx ps <id>` 看 pid 是否还在；或 `files read` 看日志

### 长任务的"先取数据再 kill"标准流程

```bash
# 1) 把输出写到固定路径（约定 /workspace/out/）
lbg sdbx exec --background <id> 'mkdir -p /workspace/out && python train.py > /workspace/out/run.log 2>&1'

# 2) 轮询确认结束
lbg sdbx ps <id> --json
lbg sdbx files read <id> /workspace/out/run.log  # 边跑边瞄

# 3) 必须先拉文件再 kill —— 沙箱销毁后无法读文件
lbg sdbx files read <id> /workspace/out/run.log --output ./run.log
lbg sdbx files read <id> /workspace/out/model.bin --format bytes --output ./model.bin

# 4) 本地确认（大小 / 行数 / checksum）

# 5) 最后 kill
lbg sdbx kill <id>
```

---

## 文件传输：`files`

```bash
# 上传单个文件
lbg sdbx files write --source ./run.py <sandbox_id> /workspace/run.py --json

# 上传整个目录（一次批量，保留相对路径）
lbg sdbx files write --source ./project <sandbox_id> /workspace/project --json

# 下载到 stdout / 文件
lbg sdbx files read <sandbox_id> /workspace/result.csv
lbg sdbx files read <sandbox_id> /workspace/result.csv --output ./result.csv

# 二进制（避免 utf-8 解码）
lbg sdbx files read <sandbox_id> /workspace/model.bin --format bytes --output ./model.bin
```

> 大目录建议本地 tar 一下再 exec 解压：`lbg sdbx files write --source ./big.tar.gz <id> /tmp/big.tar.gz && lbg sdbx exec <id> 'tar -xzf /tmp/big.tar.gz -C /workspace'`

---

## PTY 终端：`terminal`

只在真需要 TTY 的场景用：REPL、TUI（`htop` / `vim`）、给卡住的进程发 Ctrl-C。**一般运行命令请用 `exec`。**

```bash
lbg sdbx terminal create <sandbox_id> --json              # 默认 timeout=0
lbg sdbx terminal create <sandbox_id> --cwd /workspace --user root --json
lbg sdbx terminal send   <sandbox_id> <pid> 'echo hi\n'   # 注意：要自己加 \n
lbg sdbx terminal send   <sandbox_id> <pid> $'\x03'       # Ctrl-C
lbg sdbx terminal kill   <sandbox_id> <pid> --json        # 只杀 pty，不杀沙箱
```

**重要**：`terminal send` 只返回 `sent_bytes`，**不会回传 PTY 的 stdout**。要拿输出，PTY 里把命令重定向到文件，再 `files read`：

```bash
lbg sdbx terminal send <id> <pid> $'cmd > /tmp/out 2>&1\n'
lbg sdbx files read <id> /tmp/out
```

---

## 网络（按需开关 HTTP 代理）

沙箱默认**没有出站代理**。镜像里的 `/etc/pip.conf` 是阿里云镜像，所以国内 PyPI 直接快。需要访问海外（pypi.org / GitHub / HuggingFace）才打开代理 `ga.dp.tech:8118`。

### 开代理

```bash
lbg sdbx exec <id> -- bash -c '
mkdir -p ~/.pip && cat > ~/.pip/pip.conf <<EOF
[global]
proxy=http://ga.dp.tech:8118
EOF
cat > ~/.condarc <<EOF
proxy_servers:
  http: http://ga.dp.tech:8118
  https: http://ga.dp.tech:8118
ssl_verify: false
EOF
cat > ~/.curlrc <<EOF
proxy = http://ga.dp.tech:8118
EOF
git config --global http.proxy http://ga.dp.tech:8118
git config --global https.proxy http://ga.dp.tech:8118
'
```

### 关代理（回到国内快路径）

```bash
lbg sdbx exec <id> -- bash -c '
rm -f ~/.pip/pip.conf ~/.condarc ~/.wgetrc ~/.curlrc
git config --global --unset http.proxy 2>/dev/null || true
git config --global --unset https.proxy 2>/dev/null || true
'
```

### 单次绕过代理

代理开着、但某个命令一直超时：

```bash
wget --no-proxy https://example.com/file
curl --noproxy '*' https://example.com/file
git -c http.proxy= -c https.proxy= clone <url>
pip install --proxy '' <pkg>
HTTP_PROXY= HTTPS_PROXY= http_proxy= https_proxy= <cmd>
```

代理打开时 `HuggingFace` / 大 `git clone` 偶尔 503/TLS 错，重试通常能过。**用完代理记得关，否则国内访问会变慢。**

> `apt` 在 user-mode 沙箱不可用（没 root）。系统包要在镜像构建期 bake，不能运行期装。

---

## 完整工作流示例

### A. 快速验证 Python

```bash
SID=$(lbg sdbx create --json | jq -r .sandboxID)
lbg sdbx files write --source ./check_torch.py $SID /workspace/check_torch.py
lbg sdbx exec $SID 'cd /workspace && python check_torch.py'
lbg sdbx kill $SID
```

### B. GPU 训练（后台 + 取结果再 kill）

```bash
SID=$(lbg sdbx create <gpu-template> --timeout 0 --json | jq -r .sandboxID)
lbg sdbx files write --source ./project $SID /workspace/project
lbg sdbx exec --background $SID 'cd /workspace/project && python train.py > /workspace/out/run.log 2>&1'

# 隔一会儿
lbg sdbx ps $SID --json
lbg sdbx files read $SID /workspace/out/run.log --output ./run.log
lbg sdbx files read $SID /workspace/out/model.pt --format bytes --output ./model.pt

lbg sdbx kill $SID
```

### C. 上手 HuggingFace（需要海外网）

```bash
SID=$(lbg sdbx create --json | jq -r .sandboxID)
# 开代理
lbg sdbx exec $SID -- bash -c '... 见上方"开代理" ...'
lbg sdbx exec $SID 'pip install -i https://pypi.org/simple/ transformers'
lbg sdbx exec $SID 'python -c "from transformers import AutoTokenizer; ..."'
# 关代理
lbg sdbx exec $SID -- bash -c '... 见上方"关代理" ...'
lbg sdbx kill $SID
```

---

## 最佳实践

- **复用而非每次新建**：先 `lbg sdbx list` 看有没有空闲的，重复短任务最好挂在同一个沙箱上。
- **超过 30 分钟未用要 kill**：`lbg sdbx list` 会高亮警告；长期沙箱仍在计费。
- **kill 前先取产物**：销毁后无法读文件。约定输出路径 `/workspace/out/`。
- **长任务用 `--background --timeout 0`**：前台默认 60s 会被杀。
- **GPU 任务用 GPU 模板**：CPU 模板上 `nvidia-smi` 会失败。
- **`--mount-user-storage` 不是默认**：要把个人盘 / share 盘挂进沙箱才需要加。

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `lbg: error: invalid choice: 'sdbx'` | 装的是稳定版 lbg，没有 sdbx 子命令 | `pip install --pre --upgrade lbg` 装 prerelease |
| `access key required` / 鉴权失败 | 没 `lbg login` 或 `BOHR_ACCESS_KEY` 没设 | `lbg login --ak "$BOHR_ACCESS_KEY"` 或导出该环境变量 |
| 前台命令超时被杀 | 默认 `--timeout 60` 太短 | 改 `--background --timeout 0` |
| 后台命令到点被杀 | 同时设了 `--background` 和有限 `--timeout` | 后台只配 `--timeout 0`（默认就是 0） |
| kill 后想取文件取不到 | 沙箱销毁后无法读文件 | 永远先 `files read` 再 `kill` |
| 海外包装不上 / git clone 拉不到 | 代理没开 | 开 `ga.dp.tech:8118` 代理；用完关闭 |
| `apt install` 报错 | user-mode 没 root | 在镜像构建期装；不能运行期装 |
| `templateID` 报无效 | 传了 SKU / 数字 id | 传模板 **name**；`lbg sdbx template ls` 查 |
| `terminal send` 没回显输出 | PTY 是流式的，send 只返回 sent_bytes | 命令里重定向到文件，再 `files read` |
| 非 TTY 下 kill 被拒 | 安全机制，避免误杀有进程的沙箱 | 加 `--force` |
| 沙箱被自动销毁 | 默认 12h 超时 | 创建时 `--timeout N` 或 `--never-timeout`（用完记得手动 kill） |

---

## 搭配使用

- **sandbox** 验证脚本可行 → **bohrium-job** 提交批处理
- **sandbox** 预处理数据 → 上传到 **bohrium-dataset**
- **sandbox** 调试镜像 → `lbg image ls` 找镜像；`lbg sdbx template create` 出新模板
