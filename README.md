# Bohrium Skill Hub

Bohrium 平台 AI 技能集合，为 [OpenClaw](https://github.com/openclaw) 和 [Claude Code](https://claude.com/claude-code) 提供结构化的 SKILL.md 文件。每个 skill 描述一个独立能力（API 调用、Agent 工作流等），供 AI 编码助手在对话中按需加载。

[English](#english) | [中文](#中文)

---

## Claude Code 插件安装

本仓库同时是一个 Claude Code plugin marketplace。在 Claude Code 中：

```
/plugin marketplace add dptech-corp/bohrium-skills
/plugin install bohrium-skills@bohrium
```

装完会得到 15 个 Bohrium skill（英文版）。认证：

```bash
export ACCESS_KEY="YOUR_BOHRIUM_ACCESS_KEY"
```

---

## 中文

### 目录结构

```
bohrium-skill-hub/
├── zh/                          # 中文版
│   ├── bohrium-job/SKILL.md
│   ├── bohrium-node/SKILL.md
│   └── ...
├── en/                          # English version
│   ├── bohrium-job/SKILL.md
│   └── ...
└── README.md
```

### Skill 列表

#### 平台 API Skills

通过 `bohr` CLI 或 `open.bohrium.com` HTTP API 操作 Bohrium 平台资源。

| Skill | 说明 |
|-------|------|
| [bohrium-job](zh/bohrium-job/SKILL.md) | 计算任务管理 — 提交、查询、终止、删除任务 |
| [bohrium-node](zh/bohrium-node/SKILL.md) | 开发节点管理 — 创建、启停、删除容器/虚拟机 |
| [bohrium-dataset](zh/bohrium-dataset/SKILL.md) | 数据集管理 — 创建、上传、下载、版本控制 |
| [bohrium-image](zh/bohrium-image/SKILL.md) | 容器镜像管理 — 查询、拉取、创建、删除镜像 |
| [bohrium-project](zh/bohrium-project/SKILL.md) | 项目管理 — 创建项目、管理成员、设置额度 |
| [bohrium-knowledge-base](zh/bohrium-knowledge-base/SKILL.md) | 知识库管理 — 文献管理、标签、笔记、召回搜索 |
| [bohrium-paper-search](zh/bohrium-paper-search/SKILL.md) | 论文与专利搜索 — RAG 引擎关键词+语义检索 |
| [bohrium-pdf-parser](zh/bohrium-pdf-parser/SKILL.md) | PDF 解析 — 提取文本、表格、图表、公式 |
| [bohrium-scholar-search](zh/bohrium-scholar-search/SKILL.md) | 学者搜索与画像 — 按姓名/机构检索，查看发文/引用/h-index/研究方向 |
| [bohrium-wiki](zh/bohrium-wiki/SKILL.md) | 科学百科 — 按层级浏览科学词条 |
| [bohrium-web-search](zh/bohrium-web-search/SKILL.md) | 网页搜索 — 代理 searchapi.io 做开放互联网检索 |
| [bohrium-sandbox](zh/bohrium-sandbox/SKILL.md) | 云沙箱 — 按需创建临时云 VM，运行 shell/Python |
| [bohrium-lkm](zh/bohrium-lkm/SKILL.md) | 大知识模型 — 知识图谱搜索、论断验证、变量关系、批量 OCR |

### 认证配置

API Skills 需要 ACCESS_KEY，在 `~/.openclaw/openclaw.json` 中配置：

```json
{
  "skills": {
    "<skill-name>": {
      "enabled": true,
      "apiKey": "YOUR_ACCESS_KEY",
      "env": {
        "ACCESS_KEY": "YOUR_ACCESS_KEY"
      }
    }
  }
}
```

### SKILL.md 格式规范

每个 SKILL.md 包含：

```yaml
---
name: skill-name
description: "一行描述。Use when: ... NOT for: ..."
---
```

- **Frontmatter** — `name` + `description`（含使用场景和排除场景）
- **正文** — 功能说明、API 端点、参数表、返回字段、代码示例、错误处理
- **代码示例** — 使用 Python `requests` 风格，不硬编码密钥

---

## English

### Skill List

#### Platform API Skills

Operate Bohrium platform resources via `bohr` CLI or `open.bohrium.com` HTTP API.

| Skill | Description |
|-------|------------|
| [bohrium-job](en/bohrium-job/SKILL.md) | Compute job management — submit, list, kill, delete jobs |
| [bohrium-node](en/bohrium-node/SKILL.md) | Dev node management — create, start, stop, delete containers/VMs |
| [bohrium-dataset](en/bohrium-dataset/SKILL.md) | Dataset management — create, upload, download, version control |
| [bohrium-image](en/bohrium-image/SKILL.md) | Container image management — list, pull, create, delete images |
| [bohrium-project](en/bohrium-project/SKILL.md) | Project management — create projects, manage members, set budgets |
| [bohrium-knowledge-base](en/bohrium-knowledge-base/SKILL.md) | Knowledge base management — literature, tags, notes, recall search |
| [bohrium-paper-search](en/bohrium-paper-search/SKILL.md) | Paper & patent search — RAG engine keyword + semantic retrieval |
| [bohrium-pdf-parser](en/bohrium-pdf-parser/SKILL.md) | PDF parsing — extract text, tables, charts, formulas |
| [bohrium-scholar-search](en/bohrium-scholar-search/SKILL.md) | Scholar search & profile — find scholars by name/affiliation, view papers/citations/h-index/research directions |
| [bohrium-wiki](en/bohrium-wiki/SKILL.md) | SciencePedia — browse scientific topics by hierarchy |
| [bohrium-web-search](en/bohrium-web-search/SKILL.md) | Web search — proxy to searchapi.io for open internet search |
| [bohrium-sandbox](en/bohrium-sandbox/SKILL.md) | Cloud sandbox — on-demand temp VM for running shell/Python |
| [bohrium-lkm](en/bohrium-lkm/SKILL.md) | Large Knowledge Model — knowledge graph search, claim verification, variable relationships, batch OCR |

### Authentication

API Skills require ACCESS_KEY, configured in `~/.openclaw/openclaw.json`:

```json
{
  "skills": {
    "<skill-name>": {
      "enabled": true,
      "apiKey": "YOUR_ACCESS_KEY",
      "env": {
        "ACCESS_KEY": "YOUR_ACCESS_KEY"
      }
    }
  }
}
```

### SKILL.md Format

Each SKILL.md contains:

- **Frontmatter** — `name` + `description` (with "Use when" / "NOT for" guidance)
- **Body** — Feature description, API endpoints, parameter tables, response fields, code examples, error handling
- **Code examples** — Python `requests` style, no hardcoded secrets

---

## License

MIT
