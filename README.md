# Bohrium Skill Hub

Bohrium 平台 AI 技能集合，为 [OpenClaw](https://github.com/openclaw) 和 [Claude Code](https://claude.com/claude-code) 提供结构化的 SKILL.md 文件。每个 skill 描述一个独立能力（API 调用、Agent 工作流等），供 AI 编码助手在对话中按需加载。

[English](README_EN.md)

---

## 认证配置

所有 API Skills 需要 Bohrium AccessKey 作为鉴权凭证。

### 获取 AccessKey

1. 注册 [Bohrium](https://www.bohrium.com/)（机构用户请联系深势科技商务 bd@dp.tech 开通机构账号）
2. 登录后进入 [用户设置 → 账号页面](https://www.bohrium.com/settings/account)，复制 AccessKey

![获取 AccessKey](docs/images/access-key-settings.png)

### 配置方式

根据运行环境选择其一：

**环境变量**（Claude Code / 通用）：

```bash
export BOHR_ACCESS_KEY="your_access_key_here"
```

**OpenClaw 配置文件** `~/.openclaw/openclaw.json`：

```json
{
  "skills": {
    "<skill-name>": {
      "enabled": true,
      "apiKey": "YOUR_BOHR_ACCESS_KEY",
      "env": {
        "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY"
      }
    }
  }
}
```

---

## Claude Code 插件安装

本仓库同时是一个 Claude Code plugin marketplace：

```
/plugin marketplace add dptech-corp/bohrium-skills
/plugin install bohrium-skills@bohrium
```

装完会得到 17 个 Bohrium skill（英文版）。

## CLI 安装与更新

推荐用 `bohrium-skills-cli` 管理本仓库的整套 skills。CLI 发布包内嵌 `zh/` 和 `en/` 两套 skill，默认安装中文版，并同步到：

- `~/.agents/skills`
- `~/.claude/skills`
- `~/.codex/skills`

使用 CLI 的好处：

- **不用反复下载和手动替换目录**：安装或更新 CLI 后，内嵌的最新版 skills 会自动同步到常用 agent 目录。
- **版本一致**：CLI 版本和内嵌 skill set 绑定，排查问题时可以通过 `status` 看到本地同步状态。
- **安全可恢复**：替换同名官方 skill 前会自动备份，误覆盖时可以从备份目录找回。
- **不影响自定义 skills**：同步只管理官方 `bohrium-*` skills，不会触碰其他自定义目录。
- **适合多工具共用**：一次同步即可覆盖 OpenAI Codex、Claude Code、agents 等常见 skill 目录。

### 方式一：npm 安装

```bash
npm install -g bohrium-skills-cli
```

npm 安装完成后会自动运行：

```bash
bohrium-skills-cli install --lang zh --json
```

如需跳过安装后的自动同步（例如 CI 或只想下载二进制）：

```bash
BOHRIUM_SKILLS_CLI_NO_POSTINSTALL_SYNC=1 npm install -g bohrium-skills-cli
```

如需测试本地打包产物的 postinstall 下载逻辑，可临时覆盖 release 仓库地址：

```bash
BOHRIUM_SKILLS_CLI_RELEASE_REPO=https://github.com/OWNER/REPO npm install -g ./bohrium-skills-cli-0.1.0.tgz
```

### 方式二：GitHub Release 二进制安装

如果只想使用 GitHub Release 发布的单文件二进制，可以手动下载对应平台的 release asset：

```bash
# macOS Apple Silicon
curl -L -o bohrium-skills-cli \
  https://github.com/dptech-corp/bohrium-skills/releases/download/v0.1.0/bohrium-skills-cli_darwin_arm64

chmod +x bohrium-skills-cli
mkdir -p ~/.local/bin
mv bohrium-skills-cli ~/.local/bin/bohrium-skills-cli
export PATH="$HOME/.local/bin:$PATH"

bohrium-skills-cli version
bohrium-skills-cli list
bohrium-skills-cli install
bohrium-skills-cli status
```

不同平台的二进制文件名：

```text
macOS Apple Silicon: bohrium-skills-cli_darwin_arm64
macOS Intel:         bohrium-skills-cli_darwin_amd64
Linux x86_64:        bohrium-skills-cli_linux_amd64
Linux ARM64:         bohrium-skills-cli_linux_arm64
Windows x86_64:      bohrium-skills-cli_windows_amd64.exe
Windows ARM64:       bohrium-skills-cli_windows_arm64.exe
```

手动二进制安装不会自动同步 skills，需要显式运行：

```bash
bohrium-skills-cli install
```

如果是 GitHub Release 二进制手动安装，`bohrium-skills-cli update` 不会自动替换当前二进制；它会提示新版本 Release 地址，并同步当前二进制内嵌的 skills。自动更新二进制主要用于 npm 安装路径。

### 更新

```bash
bohrium-skills-cli update
```

如果 CLI 是通过 npm 安装的，`update` 会先更新 `bohrium-skills-cli` 二进制，再用新版本内嵌的 skills 同步本地三处目录。如果不是 npm 安装，则会提示 GitHub Release 下载地址，并同步当前二进制内嵌的 skills。

常用命令：

```bash
bohrium-skills-cli status
# 查看当前 CLI 版本、本地 skills 同步版本、语言、状态文件和目标目录安装情况。

bohrium-skills-cli list
# 列出当前 CLI 内嵌的官方 skills；默认显示 zh 版本的 17 个 bohrium-* skills。

bohrium-skills-cli install --force
# 强制重新安装默认 zh 版本的全部官方 skills；适合恢复被手动删除或改坏的 skill。

bohrium-skills-cli install --lang en
# 安装英文版 skills；会同步 en/ 下的同名 bohrium-* skills 到三处目标目录。

bohrium-skills-cli update --check --json
# 只检查 npm 上是否有新版 CLI，并以 JSON 输出结果；不会更新二进制，也不会写入 skills 目录。
```

同步只管理官方 `bohrium-*` skills，不会触碰其他自定义 skills。替换同名 skill 前会备份到：

```text
~/.config/bohrium-skills-cli/backups/<timestamp>/
```

---

## Skill 列表

### 平台 API Skills

通过 `bohr` CLI 或 `open.bohrium.com` HTTP API 操作 Bohrium 平台资源。

| Skill | 说明 |
|-------|------|
| [bohrium-job](zh/bohrium-job/SKILL.md) | 计算任务管理 — 提交、查询、终止、删除任务 |
| [bohrium-node](zh/bohrium-node/SKILL.md) | 开发节点管理 — 创建、启停、删除容器/虚拟机 |
| [bohrium-dataset](zh/bohrium-dataset/SKILL.md) | 数据集管理 — 创建、上传、下载、版本控制 |
| [bohrium-file](zh/bohrium-file/SKILL.md) | 文件盘管理 — 列出、上传、下载、移动、复制、删除 personal/share 盘文件 |
| [bohrium-database](zh/bohrium-database/SKILL.md) | 私有数据库 — 查询库表结构、增删改查数据、新建表和修改表结构 |
| [bohrium-image](zh/bohrium-image/SKILL.md) | 容器镜像管理 — 查询、拉取、创建、删除镜像 |
| [bohrium-project](zh/bohrium-project/SKILL.md) | 项目管理 — 创建项目、管理成员、设置额度 |
| [bohrium-knowledge-base](zh/bohrium-knowledge-base/SKILL.md) | 知识库管理 — 文献管理、标签、笔记、召回搜索 |
| [bohrium-paper-search](zh/bohrium-paper-search/SKILL.md) | 论文与专利搜索 — RAG 引擎关键词+语义检索 |
| [bohrium-pdf-parser](zh/bohrium-pdf-parser/SKILL.md) | PDF 解析 — 提取文本、表格、图表、公式 |
| [bohrium-scholar-search](zh/bohrium-scholar-search/SKILL.md) | 学者搜索与画像 — 按姓名/机构检索，查看发文/引用/h-index/研究方向 |
| [bohrium-sciencepedia](zh/bohrium-sciencepedia/SKILL.md) | 科学百科 — 搜词条/关键词拿简介与链接、浏览领域课程、看课程章节知识点、查主题知识图谱 |
| [bohrium-tools](zh/bohrium-tools/SKILL.md) | 科学工具库 — 按领域/子领域浏览、混合检索工具、查看工具详情与分类 |
| [bohrium-web-search](zh/bohrium-web-search/SKILL.md) | 网页搜索 — 代理 searchapi.io 做开放互联网检索 |
| [bohrium-sandbox](zh/bohrium-sandbox/SKILL.md) | 云沙箱 — 按需创建临时云 VM，运行 shell/Python |
| [bohrium-lkm](zh/bohrium-lkm/SKILL.md) | 大知识模型 — 知识节点检索、推理链检索、论文知识图谱、追溯 claim 依据、批量节点水合、提交反馈 |
| [bohrium-mentor](zh/bohrium-mentor/SKILL.md) | AI 科学小导师 — 基于深度推理的科学问答，自动检索文献并结构化作答 |

---

## 计费说明

以下 Skill 按调用扣账户余额，可在 [科研资产](https://www.bohrium.com/assets) 查看余额与账单：

| Skill | 类型 | 价格 |
|-------|------|------|
| bohrium-paper-search | 论文搜索（keyword） | type 0 = 0.05 元/次；type 1 = 0.1 元/次 |
| bohrium-paper-search | 专利搜索（patent） | type 0 = 0.1 元/次；type 1 = 0.3 元/次；type 2 = 0.5 元/次 |
| bohrium-pdf-parser | PDF 解析 | 0.05 元/页（触发解析时扣，查询结果免费） |

---

## 目录结构

```
bohrium-skill-hub/
├── zh/                          # 中文版
│   ├── bohrium-job/SKILL.md
│   ├── bohrium-node/SKILL.md
│   └── ...
├── en/                          # English version
│   ├── bohrium-job/SKILL.md
│   └── ...
├── docs/images/                 # 文档图片
├── README.md                    # 中文说明（本文件）
└── README_EN.md                 # English README
```

## SKILL.md 格式规范

每个 SKILL.md 至少包含：

```yaml
---
name: skill-name
description: "一行描述。Use when: ... NOT for: ..."
---
```

- **Frontmatter** — `name` + `description`（含使用场景和排除场景）；可选添加 `version`、`metadata.openclaw.primaryEnv`
- **正文** — 功能说明、API 端点、参数表、返回字段、代码示例、错误处理
- **代码示例** — 使用 Python `requests` 风格，优先通过 `os.environ.get("BOHR_ACCESS_KEY")` 读取密钥，不硬编码

---

## License

MIT
