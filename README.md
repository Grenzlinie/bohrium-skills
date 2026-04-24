# Bohrium Skill Hub

Bohrium 平台 AI 技能集合，为 [OpenClaw](https://github.com/openclaw) 和 [Claude Code](https://claude.com/claude-code) 提供结构化的 SKILL.md 文件。每个 skill 描述一个独立能力（API 调用、Agent 工作流等），供 AI 编码助手在对话中按需加载。

[English](#english) | [中文](#中文)

---

## Claude Code 插件安装

本仓库同时是一个 Claude Code plugin marketplace。在 Claude Code 中：

```
/plugin marketplace add dingzhaohan/bohrium-skill-hub
/plugin install bohrium-skills@bohrium
```

装完会得到 14 个 Bohrium skill（英文版）。认证：

```bash
export ACCESS_KEY="YOUR_BOHRIUM_ACCESS_KEY"
# sandbox 需要 E2B_API_KEY；viking-memory 需要 OPENVIKING_API_KEY 等
```

---

## 中文

### 目录结构

```
bohrium-skill-hub/
├── zh/                          # 中文版
│   ├── bohrium-job/SKILL.md
│   ├── bohrium-node/SKILL.md
│   ├── ...
│   └── scoring-agent/SKILL.md
├── en/                          # English version
│   ├── bohrium-job/SKILL.md
│   ├── ...
│   └── scoring-agent/SKILL.md
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
| [bohrium-scholar](zh/bohrium-scholar/SKILL.md) | 学者检索 — 按姓名/机构/研究方向查学者，论文列表、共同作者 |
| [bohrium-wiki](zh/bohrium-wiki/SKILL.md) | SciencePedia 百科 — 按大类/分级/领域浏览词条，获取正文 |
| [bohrium-mol-search](zh/bohrium-mol-search/SKILL.md) | 分子检索 — SMILES 查论文，子结构/相似度匹配，分子结构查询 |
| [bohrium-web-search](zh/bohrium-web-search/SKILL.md) | Web 搜索 — 通过 open-platform 代理 searchapi.io |
| [bohrium-sandbox](zh/bohrium-sandbox/SKILL.md) | 沙箱 — 临时 E2B 云 VM 执行命令、读写文件（需 `E2B_API_KEY`） |
| [bohrium-viking-memory](zh/bohrium-viking-memory/SKILL.md) | 长期记忆 — OpenViking 语义 / 关键词召回，跨会话保存上下文 |

#### 论文复现 Agent Skills

论文复现工作流中的四个阶段性 Agent，按顺序配合使用：

```
diagnose → proposal → preparation → scoring
  诊断        规划        准备          评分
```

| Skill | 说明 |
|-------|------|
| [diagnose-agent](zh/diagnose-agent/SKILL.md) | 复现可行性诊断 — 评估可复现性、成本、风险，输出诊断报告 |
| [proposal-agent](zh/proposal-agent/SKILL.md) | 复现方案规划 — 拆解 R0/R1/R2 三级复现计划 |
| [preparation-agent](zh/preparation-agent/SKILL.md) | 环境准备 — 下载代码、数据、模型，安装依赖 |
| [scoring-agent](zh/scoring-agent/SKILL.md) | 复现评分 — 4C 维度系统化评分（完整性/正确性/清晰度/成本） |

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
| [bohrium-scholar](en/bohrium-scholar/SKILL.md) | Scholar lookup — by name/affiliation/research tag, papers, coauthors |
| [bohrium-wiki](en/bohrium-wiki/SKILL.md) | SciencePedia — browse majors/levels/fields, fetch article bodies |
| [bohrium-mol-search](en/bohrium-mol-search/SKILL.md) | Molecular search — SMILES-in-paper, substructure/similarity, structure lookup |
| [bohrium-web-search](en/bohrium-web-search/SKILL.md) | Web search — proxied through open-platform (searchapi.io) |
| [bohrium-sandbox](en/bohrium-sandbox/SKILL.md) | Sandbox — ephemeral E2B cloud VM for exec/read/write (needs `E2B_API_KEY`) |
| [bohrium-viking-memory](en/bohrium-viking-memory/SKILL.md) | Long-term memory — OpenViking semantic/keyword recall across sessions |

#### Paper Reproduction Agent Skills

Four sequential agents in the paper reproduction workflow:

```
diagnose → proposal → preparation → scoring
```

| Skill | Description |
|-------|------------|
| [diagnose-agent](en/diagnose-agent/SKILL.md) | Reproducibility diagnosis — assess feasibility, cost, risks |
| [proposal-agent](en/proposal-agent/SKILL.md) | Reproduction planning — break down R0/R1/R2 plans |
| [preparation-agent](en/preparation-agent/SKILL.md) | Environment preparation — download code, data, models, install deps |
| [scoring-agent](en/scoring-agent/SKILL.md) | Reproduction scoring — 4C dimension scoring (completeness/correctness/clarity/cost) |

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
