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
| 1 | 创建会话 | `POST /v1/sigma-search/api/v4/ai_search/sessions` | 提交问题，获取 sessionId |
| 2 | SSE 流 | `GET /v1/sigma-search/api/v3/sse/ai_search/v1/{sessionId}/stream` | 实时接收推理结果 |
| 3 | 会话详情 | `GET /v1/sigma-search/api/v4/ai_search/sessions/{sessionId}` | 断线恢复/历史回显 |

鉴权方式：URL query 参数 `accessKey=<KEY>`。

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
3. `action=patch`：对 state 应用 JSON Patch（UI 状态，非文本内容）
4. `system.event.type=end` 时，`layout=main` 的 `text` key 为最终答案

---

## 完整编排脚本

```python
import os
import sys
import json
import uuid
import time
import requests

# ─── 配置 ───────────────────────────────────────────────

AK = os.environ.get("BOHR_ACCESS_KEY", "")
if not AK:
    print("ERROR: BOHR_ACCESS_KEY 未配置。")
    print("请在 ~/.openclaw/openclaw.json 中配置 bohrium-mentor.env.BOHR_ACCESS_KEY")
    sys.exit(1)

BASE = "https://open.bohrium.com/openapi/v1/sigma-search"

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
    print(f"\n[步骤 1/2] 创建会话...")

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

    url = f"{BASE}/api/v4/ai_search/sessions?accessKey={AK}"
    try:
        r = requests.post(url, json=payload, timeout=30)
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
    """订阅 SSE 流，合并事件，返回最终状态。"""
    print(f"\n[步骤 2/2] 订阅 SSE 流，等待推理结果...")

    url = f"{BASE}/api/v3/sse/ai_search/v1/{session_id}/stream?accessKey={AK}"

    state = {}  # {answerId: {layout: {key: accumulated_text}}}

    try:
        with requests.get(url, stream=True, timeout=180) as r:
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
                        return state

                    if event_type == "end":
                        print("  收到 end 事件，流结束。")
                        return state

                    # streaming 事件：合并内容
                    ui_info = ch.get("uiInfo") or {}
                    answer_id = ch.get("answerId", "default")
                    layout = ui_info.get("layout", "unknown")
                    action_list = ui_info.get("actionList") or []
                    content = ui_info.get("content") or {}

                    slot = state.setdefault(answer_id, {}).setdefault(layout, {})

                    for act in action_list:
                        action = act.get("action", "")
                        key = act.get("key", "")
                        if action in ("append", "delta") and key:
                            val = content.get(key, "")
                            if isinstance(val, str):
                                slot[key] = slot.get(key, "") + val
                        elif action == "patch":
                            pass  # JSON Patch for UI state, not needed for text extraction

                    event_count += 1
                    if event_count % 50 == 0:
                        print(f"  已接收 {event_count} 个事件...")

    except requests.exceptions.Timeout:
        print("  警告：SSE 流超时（180s），返回已接收内容")
    except requests.exceptions.RequestException as e:
        print(f"  错误：SSE 连接失败 - {e}")

    return state


# ─── Step 3: 格式化输出 ──────────────────────────────────

def format_output(state):
    """从合并后的状态中提取思考链和最终答案。"""
    thought_parts = []
    main_parts = []

    for answer_id, layouts in state.items():
        for layout, content in layouts.items():
            text = content.get("text", "")
            if not text:
                continue
            if layout == "preprocessor":
                thought_parts.append(text)
            elif layout == "main":
                main_parts.append(text)

    output_lines = []

    if thought_parts:
        output_lines.append("\n## 思考过程\n")
        for t in thought_parts:
            output_lines.append(t.strip())
        output_lines.append("")

    if main_parts:
        output_lines.append("\n## 最终答案\n")
        for m in main_parts:
            output_lines.append(m.strip())
    elif not thought_parts:
        output_lines.append("\n（未收到有效回复内容）")

    return "\n".join(output_lines)


# ─── 主流程 ──────────────────────────────────────────────

if __name__ == "__main__":
    session_id = create_session(QUERY, DISCIPLINE, JOURNAL_TYPE, MODEL)
    if not session_id:
        print("\n会话创建失败，无法继续。")
        sys.exit(1)

    state = subscribe_sse(session_id)

    result = format_output(state)
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

1. **首包延迟**：深度推理模型首次响应可能需要 30-60s，SSE 超时建议 ≥ 120s
2. **思考链**：`layout=preprocessor` 的内容展示了 Agent 的推理步骤（检索、分析、引用），有助于理解答案来源
3. **断线恢复**：如果 SSE 中断，可用 `GET sessions/{sessionId}` 获取已产出的完整结果
4. **限流**：高并发调用可能触发 429，建议单次调用或加指数退避
