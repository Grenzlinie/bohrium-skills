---
name: bohrium-matmaster
description: "MatMaster (材料大师) integration via open.bohrium.com. Use when: user asks about querying MatMaster user skills, managing material science tools, or interacting with MatMaster via Feishu/Lark integration. NOT for: general paper search (use bohrium-paper-search)."
---

# SKILL: Bohrium MatMaster (材料大师)

## 概述

通过 `open.bohrium.com` 的 MatMaster 端点，管理材料大师平台的用户 skill（工具/能力）和飞书集成。

**核心能力：**

| 端点模式 | 功能 |
|----------|------|
| `/v1/matmaster/users/:userId/skills` | 查询/管理用户的 MatMaster skills（工具列表） |
| `/v1/matmaster/integrations/feishu/*` | 飞书集成交互（消息推送、回调等） |

**适用场景：**

- 查询某用户可用的 MatMaster 工具/skill 列表
- 通过飞书与 MatMaster 交互
- 管理材料科学相关的 AI 工具能力

**不适用：**

- 论文搜索 → `bohrium-paper-search`
- 知识图谱 / 科学论断 → `bohrium-lkm`

**无 CLI 支持** — 通过 HTTP API 操作。

## 认证配置

```json
"bohrium-matmaster": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

## 通用代码模板

```python
import os, requests

AK = os.environ["ACCESS_KEY"]
BASE = "https://open.bohrium.com/openapi/v1/matmaster"
H = {"accessKey": AK, "Content-Type": "application/json"}
H_GET = {"accessKey": AK}
```

---

## 1. 查询用户 Skills — `/matmaster/users/:userId/skills`

获取指定用户在 MatMaster 上可用的工具/skill 列表。

```python
user_id = "12345"
r = requests.get(f"{BASE}/users/{user_id}/skills", headers=H_GET)
data = r.json()
for skill in data.get("data", []):
    print(f"  {skill.get('name')}: {skill.get('description')}")
    print(f"    Status: {skill.get('status')}")
```

---

## 2. 飞书集成 — `/matmaster/integrations/feishu/*`

### 发送消息/触发动作

```python
r = requests.post(f"{BASE}/integrations/feishu/send", headers=H, json={
    "action": "query",
    "content": "查询 LiFePO4 的晶体结构"
})
print(r.json())
```

### 查询集成状态

```python
r = requests.get(f"{BASE}/integrations/feishu/status", headers=H_GET)
print(r.json())
```

---

## 路径白名单

open-platform 对 MatMaster 路径做了严格限制，仅允许以下前缀：

- `/users/*/skills` — 用户 skill 相关操作
- `/integrations/feishu/*` — 飞书集成相关操作

其他路径会返回 404。

---

## curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 查询用户 skills
curl -s "https://open.bohrium.com/openapi/v1/matmaster/users/12345/skills" \
  -H "accessKey: $AK" | jq .

# 飞书集成状态
curl -s "https://open.bohrium.com/openapi/v1/matmaster/integrations/feishu/status" \
  -H "accessKey: $AK" | jq .
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 404 Not found | 路径不在白名单 | 仅 `/users/*/skills` 和 `/integrations/feishu/*` 可用 |
| 401 Unauthorized | AccessKey 无效或未传 | 检查 header 中的 `accessKey` |
| skills 列表为空 | 用户未配置任何 skill | 在 MatMaster 平台上先注册 skill |

## 搭配使用

- **matmaster** 查询可用工具 → 选择合适的工具执行材料科学任务
- **matmaster** 飞书集成 → 通过飞书触发材料查询 → **database** 获取结构数据
- **matmaster** skill 列表 → 了解当前可用能力 → 结合 **paper-search** 做文献调研
