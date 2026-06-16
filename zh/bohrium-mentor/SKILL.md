---
name: bohrium-mentor
description: "AI science tutor powered by Bohrium's adk_science_navigator agent. Submits a research question, subscribes to SSE stream, and returns a structured Markdown answer with thought chain. Use when: user wants an AI-guided explanation of a scientific topic, research progress summary, or methodology comparison. NOT for: paper search (use bohrium-paper-search), literature review (use literature-review)."
---

# SKILL: AI 科学小导师 (Science Navigator)

## 概述

**AI 科学小导师**通过调用 Bohrium 平台的 `adk_science_navigator` Agent，为用户提供基于深度推理的科学问答能力。系统会自动检索文献、推理分析，并以结构化 Markdown 形式返回包含思考过程和最终答案的完整回复。

**调用流程：**

```
用户输入科学问题
  │
  ├─ Step 1: 创建会话 (POST sessions)
  │           → 获取 sessionId
  │
  ├─ Step 2: 订阅 SSE 流 (GET stream)
  │           → 实时接收思考链 + 正文流
  │
  └─ Step 3: 合并事件，输出最终答案
  │
  ▼
  输出：思考过程 + 结构化 Markdown 答案（含文献引用）
```

**适用场景：**

- 科学主题深度问答（如"CRISPR-Cas9 近三年在基因治疗的进展"）
- 研究方法对比与评估
- 某领域最新研究进展总结
- 跨学科概念解释

**不适用：**

- 特定论文检索 → 用 `bohrium-paper-search`
- 系统性文献综述 → 用 `literature-review`
- 学者信息查询 → 用 `bohrium-scholar-search`

**无 CLI 支持** — 通过 Python 脚本调用 SSE 接口完成。

## 认证配置

```json
"bohrium-mentor": {
  "enabled": true,
  "apiKey": "YOUR_BOHR_ACCESS_KEY",
  "env": {
    "BOHR_ACCESS_KEY": "YOUR_BOHR_ACCESS_KEY"
  }
}
```

BOHR_ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取。

## API 接口

本技能使用以下接口：

| # | 接口 | 方法与路径 | 用途 |
|---|------|-----------|------|
| 1 | 创建会话 | `POST /v2/sigma-search/api/v4/ai_search/sessions` | 提交问题，获取 sessionId |
| 2 | SSE 流 | `GET /v2/sigma-search/api/v3/sse/ai_search/v1/{sessionId}/stream` | 实时接收推理结果 |
| 3 | 会话详情 | `GET /v2/sigma-search/api/v4/ai_search/sessions/{sessionId}` | 断线恢复/历史回显 |

鉴权方式：`Authorization: Bearer <BOHR_ACCESS_KEY>` 请求头。

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 科学问题，如"量子计算在药物发现中的应用前景" |
| `discipline` | string | 否 | 学科过滤：`All`（默认）、`Physics`、`Chemistry`、`Biology` 等 |
| `journal_type` | string | 否 | `foreign`（默认）/ `chinese` |
| `model` | string | 否 | `reason`（默认，深度推理） |

## 输出格式

| 字段 | 说明 |
|------|------|
| 思考过程 | Agent 的推理链（layout=preprocessor），展示检索和分析步骤 |
| 最终答案 | 结构化 Markdown（layout=main），含标题、段落、文献引用 |
| 参考文献 | 正文引用的论文/网页列表（layout=sider, tab id=used），含标题、作者、期刊、DOI |
| 全部搜索结果 | 所有检索到的资源列表（layout=sider, tab id=all），含论文和网页 |
| 相关问题推荐 | 后处理推荐问题（layout=postprocessor） |

---

## SSE 事件协议

### 事件结构

每个 SSE 事件格式为：

```
event:data
data:{"channel":{...},"system":{...},"sessionId":"..."}
```

### 关键字段

| 路径 | 说明 |
|------|------|
| `system.event.type` | `start` / `streaming` / `end` / `error` |
| `channel.uiInfo.layout` | `preprocessor`（思考链）/ `main`（最终答案） |
| `channel.uiInfo.subType` | 内容类型标识 |
| `channel.uiInfo.actionList[].action` | `append`：追加内容 / `delta`：增量流式文本 / `patch`：JSON Patch 合并 |
| `channel.uiInfo.content` | 当前事件的内容片段 |
| `channel.answerId` | 消息标识，同一 answerId 的事件属于同一段输出 |

### 合并规则

1. 按 `answerId` + `layout` 维护累计状态
2. `action=append` 或 `action=delta`：`state[key] += event.content[key]`（delta 为流式文本增量）
3. `action=patch`：应用 JSON Patch（`uiInfo.patches` 数组），用于增量构建 resourceMap 和 sider tabs
4. `system.event.type=end` 时，`layout=main` 的 `text` key 为最终答案

### 资源与引用数据（JSON Patch 传输）

文献元数据和引用列表通过 `action=patch` 增量传输，需应用 JSON Patch (RFC 6902) 合并：

| 数据 | 来源 | Patch 路径示例 |
|------|------|---------------|
| 文献元数据 | `layout=main, subType=@bohrium-chat/snp/cards-data` | `/data/resourceMap/<resourceId>` |
| 参考文献列表 | `layout=sider, subType=@bohrium-chat/snp/sider-tab/v2` | `/tabs/0/items/-`（References tab） |
| 全部搜索结果 | `layout=sider, subType=@bohrium-chat/snp/sider-tab/v2` | `/tabs/1/items/-`（All tab） |

**resourceMap 资源类型：**

- `@bohrium/card-type/paper`：学术论文，含 title, authors, journal, doi, citationNums, impactFactor, jcrZone, url, abstract
- `@bohrium/card-type/web`：网页资源，含 title, url, source, snippet, date

**sider tabs 结构：**

```json
{
  "tabs": [
    {"id": "used", "title": "References", "items": [{"resourceId": "@bohrium:doi:xxx", "@bohrium-type": "..."}]},
    {"id": "all", "title": "All search results", "items": [...]}
  ]
}
```

---

## 完整编排脚本

依赖：`pip install requests jsonpatch`

```python
import os
import sys
import json
import uuid
import requests
import jsonpatch

# ─── 配置 ───────────────────────────────────────────────

AK = os.environ.get("BOHR_ACCESS_KEY", "")
if not AK:
    print("ERROR: BOHR_ACCESS_KEY 未配置。")
    print("请在 ~/.openclaw/openclaw.json 中配置 bohrium-mentor.env.BOHR_ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi/v2/sigma-search"

# ─── 输入参数 ────────────────────────────────────────────

QUERY = sys.argv[1] if len(sys.argv) > 1 else "CRISPR-Cas9 近三年在基因治疗领域的最新进展"
DISCIPLINE = sys.argv[2] if len(sys.argv) > 2 else "All"
JOURNAL_TYPE = sys.argv[3] if len(sys.argv) > 3 else "foreign"
MODEL = "reason"

print("=" * 60)
print("  AI 科学小导师 (Science Navigator)")
print(f"  问题：{QUERY}")
print(f"  学科：{DISCIPLINE}")
print(f"  期刊类型：{JOURNAL_TYPE}")
print(f"  模型：{MODEL}")
print("=" * 60)


# ─── Step 1: 创建会话 ───────────────────────────────────

def create_session(query, discipline, journal_type, model):
    """创建 AI 搜索会话，返回 sessionId。"""
    print(f"\n[步骤 1/3] 创建会话...")

    message_id = str(uuid.uuid4())
    answer_id = str(uuid.uuid4())

    payload = {
        "query": query,
        "model": model,
        "discipline": discipline,
        "scene": "adk_science_navigator",
        "journal_type": journal_type,
        "snp_version": "1.0.0",
        "resource_id_list": [],
        "SNPReq": {
            "sessionId": "",
            "channel": {
                "schema": "fe",
                "version": "v1",
                "role": "user",
                "auth": 1,
                "messageId": message_id,
                "answerId": answer_id,
                "uiInfo": {
                    "layout": "main",
                    "type": "ui",
                    "subType": "@bohrium-chat/common/markdown",
                    "content": {"text": query},
                    "actionList": [{"key": "text", "action": "append"}]
                },
                "entities": [],
                "state": {},
                "meta": {}
            },
            "system": {
                "payload": {
                    "model": model,
                    "agentId": "science_navigator",
                    "sessionId": "",
                    "scene": "adk_science_navigator",
                    "streaming": True,
                    "biz": {
                        "uploadList": [],
                        "sn": {
                            "discipline": discipline,
                            "journal_type": journal_type,
                            "model": model
                        }
                    }
                }
            }
        }
    }

    url = f"{BASE}/api/v4/ai_search/sessions"
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {AK}"}, json=payload, timeout=30)
        r.raise_for_status()
    except requests.exceptions.Timeout:
        print("  错误：创建会话超时")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  错误：请求失败 - {e}")
        return None

    data = r.json()
    if data.get("code") != 0:
        print(f"  错误：{data.get('message', '未知错误')} (code={data.get('code')})")
        return None

    session_id = data["data"]["sessionId"]
    print(f"  会话已创建：{session_id}")
    return session_id


# ─── Step 2: 订阅 SSE 流 ────────────────────────────────

def subscribe_sse(session_id):
    """订阅 SSE 流，合并事件，返回文本状态、resourceMap 和 sider tabs。"""
    print(f"\n[步骤 2/3] 订阅 SSE 流，等待推理结果...")

    url = f"{BASE}/api/v3/sse/ai_search/v1/{session_id}/stream"

    text_state = {}  # {answerId: {layout: {key: accumulated_text}}}
    cards_state = {"data": {"interaction": {"summary": {}}, "resourceMap": {}}}
    sider_state = {}
    recommended_questions = []

    try:
        with requests.get(url, headers={"Authorization": f"Bearer {AK}"}, stream=True, timeout=300) as r:
            r.raise_for_status()
            buf = b""
            event_count = 0
            started = False

            for chunk in r.iter_content(chunk_size=4096):
                if not chunk:
                    continue
                buf += chunk

                while b"\n\n" in buf:
                    raw_bytes, buf = buf.split(b"\n\n", 1)
                    raw = raw_bytes.decode("utf-8", errors="replace")
                    lines = [l for l in raw.splitlines() if l.startswith("data:")]
                    if not lines:
                        continue

                    try:
                        evt = json.loads(lines[0][5:])
                    except json.JSONDecodeError:
                        continue

                    ch = evt.get("channel", {})
                    sys_evt = evt.get("system", {})
                    event_type = sys_evt.get("event", {}).get("type", "")

                    if event_type == "start":
                        if not started:
                            print("  收到 start 事件，开始接收...")
                            started = True
                        continue

                    if event_type == "error":
                        err_msg = sys_evt.get("event", {}).get("message", "未知错误")
                        print(f"  错误：{err_msg}")
                        break

                    if event_type == "end":
                        print("  收到 end 事件，流结束。")
                        break

                    ui_info = ch.get("uiInfo") or {}
                    answer_id = ch.get("answerId", "default")
                    layout = ui_info.get("layout", "unknown")
                    subtype = ui_info.get("subType", "")
                    action_list = ui_info.get("actionList") or []
                    content = ui_info.get("content") or {}
                    patches = ui_info.get("patches") or []

                    # ── 文本内容合并（append/delta）──
                    if any(a.get("action") in ("append", "delta") for a in action_list):
                        if layout in ("preprocessor", "main") and subtype == "@bohrium-chat/common/markdown":
                            slot = text_state.setdefault(answer_id, {}).setdefault(layout, {})
                            for act in action_list:
                                action = act.get("action", "")
                                key = act.get("key", "")
                                if action in ("append", "delta") and key:
                                    val = content.get(key, "")
                                    if isinstance(val, str):
                                        slot[key] = slot.get(key, "") + val

                        # sider 初始化（第一个 append 事件携带完整 tabs 结构）
                        if layout == "sider" and isinstance(content, dict) and "tabs" in content:
                            sider_state = content

                        # cards-data 初始化
                        if subtype == "@bohrium-chat/snp/cards-data" and isinstance(content, dict):
                            if "data" in content and isinstance(content["data"], dict):
                                rm = content["data"].get("resourceMap", {})
                                if rm:
                                    cards_state["data"]["resourceMap"].update(rm)

                    # ── JSON Patch 合并（resourceMap 和 sider tabs）──
                    if patches:
                        if subtype == "@bohrium-chat/snp/cards-data":
                            try:
                                patch = jsonpatch.JsonPatch(patches)
                                cards_state = patch.apply(cards_state)
                            except Exception:
                                pass
                        elif layout == "sider":
                            try:
                                patch = jsonpatch.JsonPatch(patches)
                                sider_state = patch.apply(sider_state)
                            except Exception:
                                pass

                    # ── 推荐问题 ──
                    if layout == "postprocessor" and subtype == "@bohrium-chat/common/relevant-search":
                        if isinstance(content, dict) and "data" in content:
                            data_list = content["data"]
                            if isinstance(data_list, list):
                                recommended_questions = data_list

                    event_count += 1
                    if event_count % 50 == 0:
                        print(f"  已接收 {event_count} 个事件...")
                else:
                    continue
                break

    except requests.exceptions.Timeout:
        print("  警告：SSE 流超时（300s），返回已接收内容")
    except requests.exceptions.RequestException as e:
        print(f"  错误：SSE 连接失败 - {e}")

    resource_map = cards_state.get("data", {}).get("resourceMap", {})
    return text_state, resource_map, sider_state, recommended_questions


# ─── Step 3: 格式化输出 ──────────────────────────────────

def format_output(text_state, resource_map, sider_state, recommended_questions):
    """从合并后的状态中提取完整结果。"""
    thought_parts = []
    main_parts = []

    for answer_id, layouts in text_state.items():
        for layout, content in layouts.items():
            text = content.get("text", "")
            if not text:
                continue
            if layout == "preprocessor":
                thought_parts.append(text)
            elif layout == "main":
                main_parts.append(text)

    output_lines = []

    # ── 思考过程 ──
    if thought_parts:
        output_lines.append("\n## 思考过程\n")
        for t in thought_parts:
            output_lines.append(t.strip())
        output_lines.append("")

    # ── 最终答案 ──
    if main_parts:
        output_lines.append("\n## 最终答案\n")
        for m in main_parts:
            output_lines.append(m.strip())
    elif not thought_parts:
        output_lines.append("\n（未收到有效回复内容）")

    # ── 参考文献 ──
    tabs = sider_state.get("tabs", [])
    ref_tab = next((t for t in tabs if t.get("id") == "used"), None)
    if ref_tab and ref_tab.get("items"):
        output_lines.append("\n\n## 参考文献\n")
        for idx, item in enumerate(ref_tab["items"], 1):
            rid = item.get("resourceId", "")
            res = resource_map.get(rid, {})
            btype = res.get("@bohrium-type", item.get("@bohrium-type", ""))
            if btype == "@bohrium/card-type/paper":
                title = res.get("title", res.get("titleEn", rid))
                authors = res.get("authors", [])
                author_str = ", ".join(authors[:3])
                if len(authors) > 3:
                    author_str += " et al."
                journal = res.get("journal", "")
                doi = res.get("doi", "")
                citation = res.get("citationNums", "")
                jcr = res.get("jcrZone", "")
                impact = res.get("impactFactor", "")
                url = res.get("url", "")
                line = f"{idx}. **{title}**"
                if author_str:
                    line += f"\n   - 作者: {author_str}"
                if journal:
                    meta_parts = [journal]
                    if jcr:
                        meta_parts.append(f"JCR {jcr}")
                    if impact:
                        meta_parts.append(f"IF {impact}")
                    line += f"\n   - 期刊: {' | '.join(meta_parts)}"
                if doi:
                    line += f"\n   - DOI: {doi}"
                if citation:
                    line += f"\n   - 引用数: {citation}"
                if url:
                    line += f"\n   - URL: {url}"
                output_lines.append(line)
            else:
                title = res.get("title", rid)
                url = res.get("url", "")
                source = res.get("source", "")
                line = f"{idx}. **{title}**"
                if url:
                    line += f"\n   - URL: {url}"
                if source:
                    line += f"\n   - 来源: {source}"
                output_lines.append(line)

    # ── 全部搜索结果 ──
    all_tab = next((t for t in tabs if t.get("id") == "all"), None)
    if all_tab and all_tab.get("items"):
        papers = []
        webs = []
        for item in all_tab["items"]:
            rid = item.get("resourceId", "")
            res = resource_map.get(rid, {})
            btype = res.get("@bohrium-type", item.get("@bohrium-type", ""))
            if btype == "@bohrium/card-type/paper":
                papers.append((rid, res))
            else:
                webs.append((rid, res))

        output_lines.append("\n\n## 全部搜索结果\n")
        output_lines.append(f"共 {len(all_tab['items'])} 条结果（论文 {len(papers)} 篇，网页 {len(webs)} 条）\n")

        if papers:
            output_lines.append("### 论文\n")
            for idx, (rid, res) in enumerate(papers, 1):
                title = res.get("title", res.get("titleEn", rid))
                authors = res.get("authors", [])
                author_str = ", ".join(authors[:3])
                if len(authors) > 3:
                    author_str += " et al."
                journal = res.get("journal", "")
                doi = res.get("doi", "")
                line = f"{idx}. **{title}**"
                if author_str:
                    line += f" — {author_str}"
                if journal:
                    line += f" | {journal}"
                if doi:
                    line += f" | DOI: {doi}"
                output_lines.append(line)

        if webs:
            output_lines.append("\n### 网页资源\n")
            for idx, (rid, res) in enumerate(webs, 1):
                title = res.get("title", rid)
                url = res.get("url", "")
                line = f"{idx}. {title}"
                if url:
                    line += f" — {url}"
                output_lines.append(line)

    # ── 推荐问题 ──
    if recommended_questions:
        output_lines.append("\n\n## 相关问题推荐\n")
        for idx, q in enumerate(recommended_questions, 1):
            output_lines.append(f"{idx}. {q}")

    return "\n".join(output_lines)


# ─── 主流程 ──────────────────────────────────────────────

if __name__ == "__main__":
    session_id = create_session(QUERY, DISCIPLINE, JOURNAL_TYPE, MODEL)
    if not session_id:
        print("\n会话创建失败，无法继续。")
        sys.exit(1)

    text_state, resource_map, sider_state, recommended_questions = subscribe_sse(session_id)

    print(f"\n  资源统计：resourceMap {len(resource_map)} 条", end="")
    tabs = sider_state.get("tabs", [])
    for tab in tabs:
        print(f"，{tab.get('title', tab.get('id'))} {len(tab.get('items', []))} 条", end="")
    print()

    result = format_output(text_state, resource_map, sider_state, recommended_questions)
    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)
```

---

## 使用示例

### 示例 1：基因治疗进展

```bash
export BOHR_ACCESS_KEY="your_key"
python3 science_navigator.py "CRISPR-Cas9 近三年在基因治疗领域的最新进展"
```

### 示例 2：指定学科和期刊类型

```bash
python3 science_navigator.py "固态电池中锂枝晶抑制的最新策略" "Chemistry" "foreign"
```

### 示例 3：中文期刊范围

```bash
python3 science_navigator.py "深度学习在蛋白质结构预测中的应用" "Biology" "chinese"
```

---

## 注意事项

1. **依赖**：需安装 `jsonpatch` 库（`pip install jsonpatch`）用于合并增量 patch 事件
2. **首包延迟**：深度推理模型首次响应可能需要 30-60s，SSE 超时建议 ≥ 120s（脚本设为 300s）
3. **思考链**：`layout=preprocessor` 的内容展示了 Agent 的推理步骤（检索、分析、引用），有助于理解答案来源
4. **参考文献**：通过 JSON Patch 增量传输，`layout=sider` 的 `tabs[0]`（id=used）为正文引用的文献，`tabs[1]`（id=all）为全部检索结果
5. **资源元数据**：`layout=main, subType=@bohrium-chat/snp/cards-data` 的 patches 携带每条资源的完整元数据（标题、作者、DOI、期刊等）
6. **断线恢复**：如果 SSE 中断，可用 `GET sessions/{sessionId}` 获取会话基本信息（注意：该接口目前不返回完整消息历史）
7. **限流**：高并发调用可能触发 429，建议单次调用或加指数退避
