# Bohrium Skill Hub

A collection of AI skills for the Bohrium platform, providing structured SKILL.md files for [OpenClaw](https://github.com/openclaw) and [Claude Code](https://claude.com/claude-code). Each skill describes a standalone capability (API calls, Agent workflows, etc.) that AI coding assistants can load on demand during conversations.

[中文](README.md)

---

## Authentication

All API Skills require a Bohrium AccessKey for authentication.

### Get your AccessKey

1. Register on [Bohrium](https://www.bohrium.com/) (enterprise users should contact DP Technology sales at bd@dp.tech)
2. Log in and go to [Settings → Account](https://www.bohrium.com/settings/account), copy your AccessKey

![Get AccessKey](docs/images/access-key-settings.png)

### Configuration

Choose one based on your runtime environment:

**Environment variable** (Claude Code / general):

```bash
export BOHR_ACCESS_KEY="your_access_key_here"
```

**OpenClaw config** `~/.openclaw/openclaw.json`:

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

## Claude Code Plugin Install

This repo is also a Claude Code plugin marketplace:

```
/plugin marketplace add dptech-corp/bohrium-skills
/plugin install bohrium-skills@bohrium
```

This installs 15 Bohrium skills (English versions).

---

## Skill List

### Platform API Skills

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
| [bohrium-tools](en/bohrium-tools/SKILL.md) | Scientific Tools library — browse by domain/subdomain, hybrid-search tools, view tool details & taxonomy |
| [bohrium-web-search](en/bohrium-web-search/SKILL.md) | Web search — proxy to searchapi.io for open internet search |
| [bohrium-sandbox](en/bohrium-sandbox/SKILL.md) | Cloud sandbox — on-demand temp VM for running shell/Python |
| [bohrium-lkm](en/bohrium-lkm/SKILL.md) | Large Knowledge Model — knowledge graph search, claim verification, variable relationships, batch OCR |
| [bohrium-mentor](en/bohrium-mentor/SKILL.md) | AI Science Mentor — deep-reasoning scientific Q&A with automatic literature retrieval, structured Markdown answers |

---

## Billing

The following skills are charged to your account balance per call. Check your balance and bills on the [Research Assets](https://www.bohrium.com/en/assets):

| Skill | Type | Price |
|-------|------|-------|
| bohrium-paper-search | Paper search (keyword) | type 0 = ¥0.4/call; type 1 = ¥0.8/call |
| bohrium-paper-search | Patent search (patent) | type 0 = ¥0.1/call; type 1 = ¥0.6/call; type 2 = ¥1/call |
| bohrium-pdf-parser | PDF parsing | ¥0.05/page (charged on trigger; fetching results is free) |

---

## Directory Structure

```
bohrium-skill-hub/
├── zh/                          # Chinese version
│   ├── bohrium-job/SKILL.md
│   ├── bohrium-node/SKILL.md
│   └── ...
├── en/                          # English version
│   ├── bohrium-job/SKILL.md
│   └── ...
├── docs/images/                 # Documentation images
├── README.md                    # Chinese README
└── README_EN.md                 # English README (this file)
```

## SKILL.md Format

Each SKILL.md contains at least:

```yaml
---
name: skill-name
description: "One-line description. Use when: ... NOT for: ..."
---
```

- **Frontmatter** — `name` + `description` (with use/exclusion scenarios); optionally `version` and `metadata.openclaw.primaryEnv`
- **Body** — Feature description, API endpoints, parameter tables, response fields, code examples, error handling
- **Code examples** — Python `requests` style, preferring `os.environ.get("BOHR_ACCESS_KEY")`, never hardcoded

---

## License

MIT
