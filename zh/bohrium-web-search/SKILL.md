---
name: bohrium-web-search
description: "Web search via Bohrium's open-platform proxy (backed by searchapi.io). Use when: user needs to search the open web for research papers, documentation, tutorials, news, or general information. NOT for: academic database search (use bohrium-paper-search / bohrium-scholar-search), Bohrium knowledge base search."
---

# SKILL: Bohrium Web 搜索

## 概述

通过 `open.bohrium.com` 的 `/v1/search/web` 端点代理到 searchapi.io，对**开放互联网**做关键词搜索，返回包含标题、链接、摘要的结果列表。

**典型场景**：找一个软件的官网、搜一篇博客、快速核实某个术语、获取新闻报道。

**不适用**：

- 学术论文检索 → 用 `bohrium-paper-search` 或 `bohrium-scholar-search`
- Bohrium 知识库内搜索 → 用 `bohrium-knowledge-base`

**无 CLI 支持** — 通过 HTTP API 操作；`bohr` CLI 内置了对应的 `BohrWebSearch` 工具，会自动走这个端点。

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"bohrium-web-search": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.ACCESS_KEY` 注入到运行环境。

## API

```
GET https://open.bohrium.com/openapi/v1/search/web?q=QUERY&num=N
Header: accessKey: $ACCESS_KEY
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `q` | string | 必填 | 搜索关键词 |
| `num` | int | `3` | 返回结果数，范围 `1-10` |

## Python 示例

```python
import os, requests

AK = os.environ["ACCESS_KEY"]
BASE = "https://open.bohrium.com/openapi/v1/search/web"

r = requests.get(BASE,
    headers={"accessKey": AK},
    params={"q": "graphene synthesis CVD", "num": 5})
data = r.json()

for i, hit in enumerate(data.get("organic_results", []), 1):
    print(f"[{i}] {hit['title']}")
    print(f"    {hit['link']}")
    print(f"    {hit.get('snippet', '')[:200]}")
    print()
```

**响应字段：**

| 字段 | 说明 |
|------|------|
| `organic_results` | 主要结果列表 |
| `organic_results[].title` | 页面标题 |
| `organic_results[].link` | 页面 URL |
| `organic_results[].snippet` | 摘要片段 |
| `organic_results[].position` | 搜索排序位置 |

## curl 示例

```bash
AK="YOUR_ACCESS_KEY"
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=deepmd-kit&num=5" \
  -H "accessKey: $AK" | jq '.organic_results[] | {title, link, snippet}'
```

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `No organic_results` | 查询无结果 | 换关键词；英文一般比中文命中更多 |
| `401` | ACCESS_KEY 错误 | 确认 `accessKey` 大小写正确；别用 `Authorization: Bearer` |
| `num` 被忽略 | 超出范围 | `num` 限制在 `1-10`，超出上限会截断或忽略 |

## 搭配使用

- 用 **web-search** 找一个软件的官网 → 再用 **bohrium-job** 提交用该软件的计算任务
- 用 **web-search** 快速核实一个方法学名词 → 再用 **bohrium-paper-search** 查相关文献
- 搜索最近的 arxiv 预印本 URL → 交给 **bohrium-pdf-parser** 解析全文
