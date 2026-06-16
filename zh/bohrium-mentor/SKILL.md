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
| 3 | 会话元数据 | `GET /v2/sigma-search/api/v4/ai_search/sessions/{sessionId}` | 查询会话状态/标题等元信息 |
| 4 | 会话历史 | `GET /v2/sigma-search/api/v4/{sessionId}/history` | 断线恢复/历史回显，含完整回答数据 |

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

## SNP2 流式协议

本技能的 SSE 流基于 Bohrium 的 **SNP2（Science Navigator Protocol 2）** 协议。外部接入者只需关注 `channel.uiInfo` 字段，它描述了消息内容、渲染区域和更新方式。

**消息外壳结构**：

```json
{
  "sessionId": "...",
  "channel": {
    "answerId": "...",     // 同一轮回答中保持一致
    "messageId": "...",    // 同一条消息更新时必须保持不变
    "role": "assistant",
    "uiInfo": {             // 消息内容和更新方式的描述本体
      "type": "ui",
      "layout": "main",
      "subType": "@bohrium-chat/common/markdown",
      "content": {"text": "...", "status": 1},
      "actionList": [{"key": "text", "action": "append"}]
    }
  },
  "system": {"event": {"type": "start"}}
}
```

**三种核心 action**（推荐只使用这三种）：

| action | 用途 | 说明 |
|--------|------|------|
| `append` | 首包创建消息 | 携带完整初始 `content`，后续同一 `messageId` 的消息通过 `patch` 更新 |
| `delta` | 流式文本追加 | `content.text` 为增量文本片段，需拼接到已有正文 |
| `patch` | 后续所有增量更新 | 使用 JSON Patch（RFC 6902），操作位于 `uiInfo.patches` 字段 |

**重要原则**：
- patch 路径相对于 `content` 根对象（如 `/text` 而非 `/content/text`）
- 同一条消息更新时 `messageId` 必须保持不变
- 完成时需同时：将 `content.status` 更新为 `1`，并发送 `system.event.type = "finish"`

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
| `system.event.type` | 消息生命周期：`start`（首包）/ `streaming`（中间更新）/ `finish`（完成）/ `error`（错误） |
| `channel.uiInfo.type` | 消息类型：`ui`（界面渲染）/ `data`（结构化数据）/ `error` / `custom` |
| `channel.uiInfo.layout` | 渲染区域：`preprocessor`（思考链）/ `main`（正文/数据）/ `sider`（侧边栏）/ `actions`（操作按钮）/ `postprocessor`（推荐问题） |
| `channel.uiInfo.subType` | 渲染器标识，如 `@bohrium-chat/common/markdown`、`@bohrium-chat/snp/cards-data` |
| `channel.uiInfo.actionList[].action` | 更新策略：`append`（首包创建）/ `delta`（流式文本追加）/ `patch`（JSON Patch 增量更新） |
| `channel.uiInfo.content` | 当前事件的内容。首包（append）携带完整内容，后续包（patch）通常为空对象 |
| `channel.uiInfo.patches` | JSON Patch 操作数组，路径相对于 `content` 根对象（如 `/text` 而非 `/content/text`） |
| `channel.answerId` | 回答标识，同一轮回答中所有消息保持一致 |
| `channel.messageId` | 消息标识，更新同一条消息时必须保持不变 |
| `content.status` | 消息状态：`0`=生成中，`1`=完成，`2`=失败 |

### 合并规则

1. 按 `answerId` + `layout` 维护累计状态
2. `action=append`：首包创建消息，`content` 携带完整初始内容
3. `action=delta`：流式文本追加，`text += content.text`
4. `action=patch`：应用 `uiInfo.patches` 中的 JSON Patch 操作，用于增量构建 resourceMap、sider tabs 和思考过程树
5. patch 路径始终相对于 `content` 根对象（如 `/text`、`/children/-`、`/data/resourceMap/<resourceId>`）
6. `system.event.type=finish` 时，该 `answerId` 下的所有消息已完成

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

### Stream 与 History 的关系

Stream 和 History 返回的**内容完全相同**，区别仅在于数据形态：

| 维度 | SSE Stream | History 接口 |
|------|------------|-------------|
| 数据形态 | 流式增量事件（中间态） | 聚合后的最终结果 |
| 正文 | `content.text` 为文本片段，需通过 `append`/`delta` 拼接 | `content.text` 已是完整文本 |
| 思考过程 | `uiInfo.patches` 为 JSON Patch 操作，需逐步应用构建树 | `content` 直接是完整的思考树结构 |
| 资源数据 | `layout=main, subType=@bohrium-chat/snp/cards-data` 通过 patch 增量构建 resourceMap | `content.data.resourceMap` 直接是完整字典 |
| 侧边栏 | `layout=sider` 通过 patch 增量构建 tabs | `content.tabs` 直接是完整数组 |
| 适用场景 | 实时展示推理过程 | 断线恢复、历史回显、离线分析 |

**简单理解**：History 就是把 Stream 中所有 `append`/`delta`/`patch` 操作全部应用后的最终状态。如果 SSE 流完整接收未中断，则无需再调用 History 接口；只有在 SSE 中断或需要回看历史会话时，才用 History 接口获取完整结果。

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


# ─── JSON Patch 工具函数（思考过程树）──────────────────────

def apply_all_patches(all_patch_batches):
    """收集所有 patch 批次，按优先级排序后统一应用到文档树。
    add 操作优先于 replace，确保节点创建后再更新状态。"""
    flat = []
    for batch in all_patch_batches:
        if isinstance(batch, list):
            flat.extend(batch)

    priority = {"add": 0, "replace": 1, "remove": 2}
    flat.sort(key=lambda p: priority.get(p.get("op", ""), 9))

    doc = {"children": [], "status": 0, "title": ""}
    failed = []
    for patch in flat:
        try:
            if _apply_one(doc, patch):
                continue
        except Exception:
            pass
        failed.append(patch)

    # 重试失败的 patch（最多 5 轮）
    for _ in range(5):
        if not failed:
            break
        still = []
        for patch in failed:
            try:
                if _apply_one(doc, patch):
                    continue
            except Exception:
                pass
            still.append(patch)
        failed = still
    return doc


def _apply_one(doc, patch):
    """应用单个 JSON Patch 操作，返回是否成功。"""
    op = patch.get("op", "")
    path = patch.get("path", "")
    value = patch.get("value")
    if not path or path == "/":
        return True
    parts = [p for p in path.split("/") if p != ""]
    current = doc
    for part in parts[:-1]:
        if isinstance(current, list):
            if part == "-":
                return False
            idx = int(part)
            if idx >= len(current):
                return False
            current = current[idx]
        elif isinstance(current, dict):
            if part not in current:
                current[part] = {}
            current = current[part]
        else:
            return False
    key = parts[-1]
    if op == "add":
        if isinstance(current, list):
            current.append(value) if key == "-" else current.insert(min(int(key), len(current)), value)
        elif isinstance(current, dict):
            current[key] = value
    elif op == "replace":
        if isinstance(current, list):
            idx = int(key)
            if idx >= len(current):
                return False
            current[idx] = value
        elif isinstance(current, dict):
            if key not in current:
                return False
            current[key] = value
    elif op == "remove":
        if isinstance(current, list):
            idx = int(key)
            if idx < len(current):
                current.pop(idx)
        elif isinstance(current, dict):
            current.pop(key, None)
    return True


# ─── Step 2: 订阅 SSE 流 ────────────────────────────────

def subscribe_sse(session_id):
    """订阅 SSE 流，合并事件，返回文本状态、resourceMap、sider tabs 和思考树。"""
    print(f"\n[步骤 2/3] 订阅 SSE 流，等待推理结果...")

    url = f"{BASE}/api/v3/sse/ai_search/v1/{session_id}/stream"

    text_state = {}  # {answerId: {layout: {key: accumulated_text}}}
    cards_state = {"data": {"interaction": {"summary": {}}, "resourceMap": {}}}
    sider_state = {}
    recommended_questions = []
    preprocessor_patch_batches = []  # 思考过程 JSON Patch 批次

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

                    if event_type in ("finish", "end"):
                        print("  收到 finish 事件，流结束。")
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

                    # ── JSON Patch 合并（resourceMap、sider tabs、思考过程树）──
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
                        elif layout == "preprocessor":
                            preprocessor_patch_batches.append(patches)

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
    thinking_tree = apply_all_patches(preprocessor_patch_batches)
    return text_state, resource_map, sider_state, recommended_questions, thinking_tree


# ─── Step 3: 格式化输出 ──────────────────────────────────

def print_thinking_tree(node, indent=0):
    """递归打印思考过程树。"""
    if not isinstance(node, dict):
        return
    title = node.get("title", "")
    status = node.get("status", "")
    desc = node.get("description", {})
    content = node.get("content", {})

    icon = "✅" if status == 1 else "⏳" if status == 0 else "❌"
    prefix = "  " * indent
    if title:
        print(f"{prefix}{icon} {title}")
    if isinstance(desc, dict) and desc.get("text"):
        print(f"{prefix}   {desc['text']}")
    if isinstance(content, dict):
        for q in content.get("queries", []):
            if isinstance(q, dict) and q.get("query"):
                print(f"{prefix}   🔍 {q['query']}")
    for child in node.get("children", []):
        print_thinking_tree(child, indent + 1)


def format_output(text_state, resource_map, sider_state, recommended_questions, thinking_tree):
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

    # ── 思考过程（树结构）──
    output_lines.append("\n## 思考过程\n")
    print_thinking_tree(thinking_tree)

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

    text_state, resource_map, sider_state, recommended_questions, thinking_tree = subscribe_sse(session_id)

    print(f"\n  资源统计：resourceMap {len(resource_map)} 条", end="")
    tabs = sider_state.get("tabs", [])
    for tab in tabs:
        print(f"，{tab.get('title', tab.get('id'))} {len(tab.get('items', []))} 条", end="")
    print()

    result = format_output(text_state, resource_map, sider_state, recommended_questions, thinking_tree)
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

## 断线恢复（History 接口）

SSE 流中断后，可通过 history 接口获取已产出的完整结果。

**请求**：`GET /v2/sigma-search/api/v4/{sessionId}/history`

**响应结构**：返回 `historyData` 数组，每条记录对应一个完整的消息事件：

| historyData[i] | role | layout | 说明 |
|----------------|------|--------|------|
| 用户提问 | `user` | `main` | 原始问题文本 |
| 思考过程 | `assistant` | `preprocessor` | `content` 字段直接包含完整的思考树（无需 JSON Patch） |
| 资源元数据 | `assistant` | `main` | `content.data.resourceMap` 包含完整文献元数据字典 |
| 正文答案 | `assistant` | `main` | `content.text` 包含最终 Markdown 答案 |
| 侧边栏 | `assistant` | `sider` | `content.tabs` 直接是完整的 References / All search results 数组 |
| 操作按钮 | `assistant` | `actions` | 操作按钮列表 |
| 推荐问题 | `assistant` | `postprocessor` | 后续推荐问题 |

**思考树结构**（preprocessor 的 `content` 字段）：

```json
{
  "title": "Thinking completed",
  "status": 1,
  "type": "thinking",
  "description": {"text": "28 citations · 183 sources"},
  "children": [
    {"title": "Intent understood and task plan determined", "status": 1, "type": "intention"},
    {"title": "Evidence search completed", "status": 1, "type": "search",
     "content": {"queries": [{"query": "...", "channel": [...], "retrieved": "Found 84 evidences"}], "result": "Called 12 tools, found 252 supporting evidences."}},
    {"title": "Read and organized related materials", "status": 1, "type": "read"},
    {"title": "Supplemental search completed", "status": 1, "type": "search"},
    {"title": "Accuracy and authenticity assessment completed", "status": 1, "type": "review"},
    {"title": "Answer completed", "status": 1, "type": "result"}
  ]
}
```

---

## 注意事项

1. **依赖**：需安装 `jsonpatch` 库（`pip install requests jsonpatch`）用于合并增量 patch 事件
2. **首包延迟**：深度推理模型首次响应可能需要 30-60s，SSE 超时建议 ≥ 120s（脚本设为 300s）
3. **思考链**：`layout=preprocessor` 通过 JSON Patch 增量构建思考树；history 接口返回的 `content` 直接是完整思考树
4. **参考文献**：通过 JSON Patch 增量传输，`layout=sider` 的 `tabs[0]`（id=used）为正文引用的文献，`tabs[1]`（id=all）为全部检索结果
5. **资源元数据**：`layout=main, subType=@bohrium-chat/snp/cards-data` 的 patches 携带每条资源的完整元数据（标题、作者、DOI、期刊等）
6. **断线恢复**：SSE 中断后，用 `GET api/v4/{sessionId}/history` 获取已产出的完整结果（注意：`sessions/{sessionId}` 仅返回元数据，不返回完整消息历史）
7. **append 与 patch 的区别**：首包（`action=append`）携带完整 `content`；后续包（`action=patch`）的 `content` 通常为空对象，更新数据在 `patches` 字段中
8. **patch 路径**：始终相对于 `content` 根对象。例如 `/text` 表示 `content.text`，`/data/resourceMap/<resourceId>` 表示 `content.data.resourceMap[<resourceId>]`。不要写成 `/content/text`
9. **完成信号**：流结束时应同时收到 `system.event.type = "finish"` 和 `content.status` 被 patch 更新为 `1`。如果只收到流断开但没有 `finish` 事件，说明可能异常中断，应使用 history 接口获取完整结果
10. **消息分组**：同一 `answerId` 下的所有消息属于同一轮回答；同一 `messageId` 的多个事件是对同一条消息的增量更新
11. **限流**：高并发调用可能触发 429，建议单次调用或加指数退避
