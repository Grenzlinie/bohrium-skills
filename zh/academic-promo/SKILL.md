---
name: academic-promo
description: "Academic social media content generator from published papers. Use when: user has published a paper and wants to create promotional content for different channels (Twitter, LinkedIn, WeChat). NOT for: paper analysis (use paper-dissector), writing papers (use related-work-writer)."
---

# SKILL: 学术社交媒体内容 (Academic Promo)

## 概述

编排 `bohrium-pdf-parser` 和 `bohrium-web-search` 两个原子技能，从已发表论文自动生成适配不同社交媒体渠道的学术推广内容。解析论文 PDF 提取核心贡献与关键图表，再通过 Web 搜索了解领域内社交媒体讨论风格，最终为 Twitter、LinkedIn、微信公众号等渠道输出风格化的推广文案。

**编排流程：**

```
论文 PDF URL / DOI
        │
        ▼
┌─────────────────────┐
│  pdf-parser          │  解析全文 → 提取核心贡献、关键图表、摘要
│  POST trigger-url-   │
│  async + get-result  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  web-search          │  搜索该领域在社交媒体上的讨论风格
│  GET /v1/search/web  │  （Twitter 学术推文、LinkedIn 科研动态等）
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  内容生成引擎        │  结合解析结果和风格参考，生成多渠道内容
└────────┬────────────┘
         │
         ▼
   多渠道推广内容
   ├── Twitter 推文串（5-7 条）
   ├── LinkedIn 长帖
   ├── 微信公众号文章大纲
   └── 学术报告 PPT 大纲（可选）
```

**编排的原子技能：**

| 步骤 | 原子 Skill | 端点 | 功能 |
|------|-----------|------|------|
| 1 | `pdf-parser` | `POST /v1/parse/trigger-url-async` + `POST /v1/parse/get-result` | 解析论文 PDF，提取核心贡献和关键图表 |
| 2 | `web-search` | `GET /v1/search/web` | 搜索领域内社交媒体讨论风格 |

**适用场景：**

- 论文被接收/发表后，生成社交媒体推广文案
- 为会议 poster 或 oral 准备社交媒体预热内容
- 将技术论文转化为科普向的公众号文章
- 为课题组公众号提供论文解读素材

**不适用：**

- 深度拆解论文 → `paper-dissector`
- 撰写论文 Related Work → `related-work-writer`
- 文献综述 → `literature-review`
- 论文搜索 → `bohrium-paper-search`

**无 CLI 支持** — 全部通过 HTTP API 编排。

---

## 认证配置

ACCESS_KEY 从 OpenClaw 配置文件 `~/.openclaw/openclaw.json` 中读取：

```json
"academic-promo": {
  "enabled": true,
  "apiKey": "YOUR_ACCESS_KEY",
  "env": {
    "ACCESS_KEY": "YOUR_ACCESS_KEY"
  }
}
```

OpenClaw 会自动将 `env.ACCESS_KEY` 注入到运行环境。

---

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `paper` | string | 是 | — | 论文 PDF URL 或 DOI |
| `channels` | list | 否 | `["all"]` | 目标渠道：`twitter`、`linkedin`、`wechat`、`ppt`、`all` |
| `language` | string | 否 | `"zh"` | 输出语言：`zh`（中文）/ `en`（英文）/ `both`（双语） |
| `tone` | string | 否 | `"professional"` | 文案风格：`professional`（专业严谨）/ `accessible`（通俗易懂）/ `exciting`（激动人心） |

---

## 输出结构

### 1. Twitter 推文串（5-7 条）

按学术 Twitter 惯例组织的推文串，每条控制在 280 字符以内：

| 推文序号 | 内容 | 说明 |
|---------|------|------|
| 1/N | 论文一句话亮点 + 链接 | 开篇抓眼球，含论文链接 |
| 2/N | 研究问题与动机 | 为什么这个问题重要 |
| 3/N | 核心方法 | 方法创新点，配关键图 |
| 4/N | 主要结果 | 量化结果、性能对比 |
| 5/N | 关键图表 | 最有说服力的可视化 |
| 6/N | 影响与展望 | 对领域的意义 |
| 7/N | 致谢与链接 | 合作者、代码仓库、arXiv 链接 |

### 2. LinkedIn 长帖

专业向的 LinkedIn 帖子（800-1200 词），包含：
- 引导段（个人叙事 + 研究背景）
- 核心贡献（方法与结果）
- 行业影响分析
- 行动号召（CTA）

### 3. 微信公众号文章大纲

适配中文学术传播风格的文章结构：
- 标题（吸引点击的中文标题 + 期刊/会议信息）
- 导语（100 字以内的核心发现概述）
- 研究背景（为什么做这个研究）
- 方法亮点（用类比和图示解释核心方法）
- 主要结果（图表 + 解读）
- 意义与展望
- 论文信息（DOI、作者列表、通讯作者）

### 4. 学术报告 PPT 大纲（可选）

5-10 页的学术报告幻灯片大纲，用于组会汇报或会议报告预热。

---

## 内容质量控制

### 学术准确性（最高优先级）

传播内容**必须保持学术严谨性**，即使是面向大众的版本：
- 所有定量 claim 必须来自论文原文，不可夸大
- 方法描述可以简化但不能歪曲（类比需标注"类比，非精确描述"）
- 不能用"突破性/革命性/颠覆性"等词除非论文确实达到该水平

### 平台适配

不同平台的语言风格必须有实质差异：
- **Twitter**：简洁、重点突出、用数字说话
- **LinkedIn**：专业、含个人叙事、面向行业应用
- **微信公众号**：故事化、渐进式解释、照顾非专业读者

如果三个版本读起来只是翻译差异（同样内容的中英文版），说明适配不到位。

### 禁止的行为

- ❌ 夸大研究成果（如将"初步验证"描述为"完全解决"）
- ❌ 遗漏关键局限性（传播内容可以不强调但不能回避）
- ❌ 生成与论文实际内容不符的"吸引眼球"标题

---

## 通用代码模板

```python
import os, time, requests, json, re

AK = os.environ.get("ACCESS_KEY", "")
BASE_PARSE = "https://open.bohrium.com/openapi/v1/parse"
BASE_SEARCH = "https://open.bohrium.com/openapi/v1/search/web"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_AK = {"accessKey": AK}
```

---

## 步骤 1：PDF 解析 — 提取核心贡献与关键图表

调用 `pdf-parser` 解析论文 PDF，提取标题、摘要、核心贡献、方法创新点、关键结果和图表描述。

### Python 示例

```python
def parse_paper(pdf_url: str) -> dict:
    """
    解析论文 PDF，提取核心内容。

    Args:
        pdf_url: 论文 PDF 的 URL（如 arXiv PDF 链接）

    Returns:
        dict: {
            "title": 论文标题,
            "abstract": 摘要,
            "contributions": 核心贡献列表,
            "methods": 方法描述,
            "results": 主要结果,
            "figures": 关键图表描述列表,
            "content": 全文内容
        }
    """
    print(f"[步骤 1/2] 解析论文 PDF：{pdf_url}")

    # 提交解析任务
    payload = {
        "url": pdf_url,
        "sync": False,
        "textual": True,
        "table": True,
        "molecule": False,
        "chart": False,
        "figure": False,
        "expression": True,
        "equation": True,
        "timeout": 1800
    }

    try:
        r = requests.post(
            f"{BASE_PARSE}/trigger-url-async",
            headers=HEADERS_JSON,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("  错误：无法连接到 open.bohrium.com，请检查网络。")
        return {"status": "failed", "error": "连接失败"}
    except requests.exceptions.Timeout:
        print("  错误：提交请求超时。")
        return {"status": "failed", "error": "请求超时"}

    submit = r.json()
    if submit.get("code"):
        print(f"  提交失败：{submit.get('message', '未知错误')}")
        return {"status": "failed", "error": submit.get("message")}

    token = submit["token"]
    print(f"  已提交，token={token}")

    # 轮询结果（最多等 180 秒）
    for attempt in range(90):
        time.sleep(2)
        try:
            r = requests.post(
                f"{BASE_PARSE}/get-result",
                headers=HEADERS_JSON,
                json={
                    "token": token,
                    "content": True,
                    "objects": True,
                    "pages_dict": True
                },
                timeout=30
            )
            result = r.json()
        except Exception as e:
            print(f"  [{attempt+1}] 查询失败：{e}")
            continue

        status = result.get("status", "")
        proc_page = result.get("proc_page", 0)
        total_page = result.get("total_page", 0)

        if status == "success":
            content = result.get("content", "")
            print(f"  解析完成！共 {total_page} 页，内容长度 {len(content)} 字符")

            # 从解析内容中提取结构化信息
            extracted = extract_paper_structure(content)
            extracted["status"] = "success"
            extracted["content"] = content
            extracted["total_page"] = total_page
            return extracted

        elif status == "failed":
            desc = result.get("description", "未知错误")
            print(f"  解析失败：{desc}")
            return {"status": "failed", "error": desc}
        else:
            if attempt % 5 == 0:
                print(f"  [{attempt+1}] 解析中... ({proc_page}/{total_page} 页)")

    print("  超时：解析任务未在 180 秒内完成。")
    return {"status": "timeout", "error": "解析超时（180秒）"}


def extract_paper_structure(content: str) -> dict:
    """
    从 pdf-parser 返回的 LaTeX 标记文本中提取论文结构化信息。

    pdf-parser 返回的文本使用 LaTeX 风格标记：
    - \\begin{title} ... \\end{title}
    - \\begin{section} ... \\end{section}
    等。
    """
    result = {
        "title": "",
        "abstract": "",
        "contributions": [],
        "methods": "",
        "results": "",
        "figures": []
    }

    # 提取标题
    title_match = re.search(
        r'\\begin\{title\}(.*?)\\end\{title\}',
        content, re.DOTALL
    )
    if title_match:
        result["title"] = title_match.group(1).strip()

    # 提取摘要
    abstract_match = re.search(
        r'(?i)abstract[:\s]*(.*?)(?=\\begin\{section\}|\\begin\{subsection\}|introduction)',
        content, re.DOTALL
    )
    if abstract_match:
        result["abstract"] = abstract_match.group(1).strip()[:2000]

    # 按段落标记拆分
    sections = re.split(r'\\begin\{(?:section|subsection)\}', content)

    for section in sections:
        first_line = section.strip()[:300].lower()

        # 提取方法段落
        if re.search(r'(?i)(method|approach|proposed|framework|architecture)', first_line):
            result["methods"] = section.strip()[:3000]

        # 提取结果段落
        if re.search(r'(?i)(result|experiment|evaluation|performance)', first_line):
            result["results"] = section.strip()[:3000]

    # 提取核心贡献（通常出现在 Introduction 末尾）
    contribution_patterns = [
        r'[^.]*(?:our\s+(?:main\s+)?contributions?\s+(?:are|include))[^.]+\.',
        r'[^.]*(?:we\s+(?:propose|present|introduce|develop|design))\s+[^.]+\.',
        r'[^.]*(?:this\s+(?:paper|work)\s+(?:proposes?|presents?|introduces?))\s+[^.]+\.',
    ]
    for pattern in contribution_patterns:
        matches = re.findall(pattern, content[:10000], re.IGNORECASE)
        for m in matches:
            claim = m.strip()
            if 20 < len(claim) < 500:
                result["contributions"].append(claim)

    # 去重
    seen = set()
    unique = []
    for c in result["contributions"]:
        norm = c.lower().strip()
        if norm not in seen:
            seen.add(norm)
            unique.append(c)
    result["contributions"] = unique[:5]

    # 提取图表描述
    figure_patterns = [
        r'(?i)(?:figure|fig\.?)\s*(\d+)[.:]\s*([^.]+\.)',
        r'(?i)(?:table)\s*(\d+)[.:]\s*([^.]+\.)',
    ]
    for pattern in figure_patterns:
        matches = re.findall(pattern, content)
        for num, caption in matches:
            result["figures"].append({
                "number": num,
                "caption": caption.strip()[:200]
            })

    return result
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"
BASE="https://open.bohrium.com/openapi/v1/parse"

# 1. 提交解析任务
TOKEN=$(curl -s -X POST "$BASE/trigger-url-async" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d '{
    "url": "https://arxiv.org/pdf/2401.12345",
    "sync": false,
    "textual": true,
    "table": true,
    "chart": true,
    "figure": true,
    "expression": true,
    "equation": true,
    "timeout": 1800
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "Token: $TOKEN"

# 2. 轮询结果
sleep 10
curl -s -X POST "$BASE/get-result" \
  -H "Content-Type: application/json" \
  -H "accessKey: $AK" \
  -d "{\"token\": \"$TOKEN\", \"content\": true, \"objects\": true, \"pages_dict\": true}"
```

---

## 步骤 2：Web 搜索 — 了解领域社交媒体讨论风格

调用 `web-search` 搜索该论文所在领域在 Twitter/LinkedIn 等平台上的学术传播风格，为内容生成提供风格参考。

### Python 示例

```python
def search_field_style(title: str, field_keywords: list[str]) -> dict:
    """
    搜索该领域在社交媒体上的学术讨论风格。

    Args:
        title: 论文标题
        field_keywords: 从论文中提取的领域关键词

    Returns:
        dict: {
            "twitter_style": Twitter 讨论风格参考,
            "linkedin_style": LinkedIn 讨论风格参考,
            "wechat_style": 微信公众号讨论风格参考,
            "trending_hashtags": 热门话题标签
        }
    """
    print(f"\n[步骤 2/2] 搜索领域社交媒体讨论风格")

    style_info = {
        "twitter_style": [],
        "linkedin_style": [],
        "wechat_style": [],
        "trending_hashtags": []
    }

    # 搜索 Twitter 上的学术讨论风格
    queries = [
        f"twitter thread {' '.join(field_keywords[:3])} paper new research",
        f"linkedin post {' '.join(field_keywords[:3])} research publication",
        f"微信公众号 {' '.join(field_keywords[:2])} 论文解读",
    ]

    query_targets = ["twitter_style", "linkedin_style", "wechat_style"]

    for query, target in zip(queries, query_targets):
        try:
            r = requests.get(
                BASE_SEARCH,
                headers=HEADERS_AK,
                params={"q": query, "num": 5},
                timeout=15
            )
            r.raise_for_status()
            data = r.json()

            results = data.get("organic_results", [])
            print(f"  {target}：找到 {len(results)} 条参考")

            for hit in results:
                style_info[target].append({
                    "title": hit.get("title", ""),
                    "link": hit.get("link", ""),
                    "snippet": hit.get("snippet", "")[:300]
                })

        except Exception as e:
            print(f"  {target} 搜索失败：{e}")

    # 搜索领域热门话题标签
    try:
        hashtag_query = f"academic twitter hashtag {' '.join(field_keywords[:3])}"
        r = requests.get(
            BASE_SEARCH,
            headers=HEADERS_AK,
            params={"q": hashtag_query, "num": 3},
            timeout=15
        )
        data = r.json()
        for hit in data.get("organic_results", []):
            snippet = hit.get("snippet", "")
            # 提取 hashtag
            tags = re.findall(r'#\w+', snippet)
            style_info["trending_hashtags"].extend(tags)

        # 去重
        style_info["trending_hashtags"] = list(set(style_info["trending_hashtags"]))[:10]
        print(f"  热门标签：{style_info['trending_hashtags']}")

    except Exception as e:
        print(f"  标签搜索失败：{e}")

    return style_info
```

### curl 示例

```bash
AK="YOUR_ACCESS_KEY"

# 搜索 Twitter 学术讨论风格
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=twitter+thread+machine+learning+paper+new+research&num=5" \
  -H "accessKey: $AK" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for hit in data.get('organic_results', []):
    print(f\"[{hit.get('position', '')}] {hit['title']}\")
    print(f\"    {hit['link']}\")
    print(f\"    {hit.get('snippet', '')[:200]}\")
    print()
"

# 搜索微信公众号风格
curl -s "https://open.bohrium.com/openapi/v1/search/web?q=%E5%BE%AE%E4%BF%A1%E5%85%AC%E4%BC%97%E5%8F%B7+%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0+%E8%AE%BA%E6%96%87%E8%A7%A3%E8%AF%BB&num=5" \
  -H "accessKey: $AK" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for hit in data.get('organic_results', []):
    print(f\"  {hit['title']}: {hit.get('snippet', '')[:100]}\")
"
```

---

## 内容生成引擎

结合步骤 1（论文解析结果）和步骤 2（风格参考），生成多渠道推广内容。

### Python 示例

```python
def generate_twitter_thread(paper_info: dict, style_info: dict,
                            language: str = "en") -> list[str]:
    """
    生成 Twitter 推文串（5-7 条）。

    每条推文控制在 280 字符以内（中文约 140 字）。

    Args:
        paper_info: 论文结构化信息（来自步骤 1）
        style_info: 社交媒体风格参考（来自步骤 2）
        language: 输出语言

    Returns:
        list[str]: 推文列表
    """
    title = paper_info.get("title", "Our new paper")
    abstract = paper_info.get("abstract", "")
    contributions = paper_info.get("contributions", [])
    methods = paper_info.get("methods", "")
    results = paper_info.get("results", "")
    figures = paper_info.get("figures", [])
    hashtags = " ".join(style_info.get("trending_hashtags", [])[:3])

    tweets = []

    if language == "zh":
        # 推文 1：论文亮点
        tweet1 = f"我们的新论文发表了！\n\n"
        tweet1 += f"「{title[:80]}」\n\n"
        if contributions:
            tweet1 += f"{contributions[0][:100]}\n\n"
        tweet1 += f"论文链接：[URL]\n{hashtags}"
        tweets.append(("1/N 论文亮点", tweet1))

        # 推文 2：研究动机
        tweet2 = "为什么做这个研究？\n\n"
        # 从摘要前两句提取动机
        sentences = abstract.split(".")
        motivation = ". ".join(sentences[:2]).strip()
        tweet2 += f"{motivation[:200]}"
        tweets.append(("2/N 研究动机", tweet2))

        # 推文 3：核心方法
        tweet3 = "我们的核心方法：\n\n"
        if contributions and len(contributions) > 1:
            for i, c in enumerate(contributions[1:3], 1):
                tweet3 += f"  {i}. {c[:80]}\n"
        else:
            # 从方法段落提取关键句
            method_sentences = _extract_key_sentences(methods, 2)
            for s in method_sentences:
                tweet3 += f"  - {s[:100]}\n"
        tweets.append(("3/N 核心方法", tweet3))

        # 推文 4：主要结果
        tweet4 = "主要结果：\n\n"
        result_sentences = _extract_key_sentences(results, 3)
        for s in result_sentences:
            tweet4 += f"  - {s[:80]}\n"
        tweets.append(("4/N 主要结果", tweet4))

        # 推文 5：关键图表
        if figures:
            tweet5 = "关键图表一览：\n\n"
            for fig in figures[:3]:
                tweet5 += f"  Fig.{fig['number']}: {fig['caption'][:60]}\n"
            tweet5 += "\n（完整图表见论文）"
            tweets.append(("5/N 关键图表", tweet5))

        # 推文 6：影响与展望
        tweet6 = "这项工作的意义：\n\n"
        tweet6 += "[请补充：这项研究对领域的影响和未来方向]\n\n"
        tweet6 += "欢迎讨论和交流！"
        tweets.append(("6/N 影响与展望", tweet6))

        # 推文 7：致谢
        tweet7 = "感谢所有合作者的贡献！\n\n"
        tweet7 += "论文：[arXiv/DOI URL]\n"
        tweet7 += "代码：[GitHub URL（如有）]\n\n"
        tweet7 += f"{hashtags}"
        tweets.append(("7/N 致谢与链接", tweet7))

    else:  # English
        tweet1 = f"Excited to share our new paper!\n\n"
        tweet1 += f"\"{title[:100]}\"\n\n"
        if contributions:
            tweet1 += f"{contributions[0][:120]}\n\n"
        tweet1 += f"Paper: [URL]\n{hashtags}"
        tweets.append(("1/N Hook", tweet1))

        tweet2 = "Why does this matter?\n\n"
        sentences = abstract.split(".")
        motivation = ". ".join(sentences[:2]).strip()
        tweet2 += f"{motivation[:220]}"
        tweets.append(("2/N Motivation", tweet2))

        tweet3 = "Our key idea:\n\n"
        if contributions and len(contributions) > 1:
            for i, c in enumerate(contributions[1:3], 1):
                tweet3 += f"{i}. {c[:100]}\n"
        else:
            method_sentences = _extract_key_sentences(methods, 2)
            for s in method_sentences:
                tweet3 += f"- {s[:120]}\n"
        tweets.append(("3/N Method", tweet3))

        tweet4 = "Key results:\n\n"
        result_sentences = _extract_key_sentences(results, 3)
        for s in result_sentences:
            tweet4 += f"- {s[:100]}\n"
        tweets.append(("4/N Results", tweet4))

        if figures:
            tweet5 = "Visual highlights:\n\n"
            for fig in figures[:3]:
                tweet5 += f"Fig.{fig['number']}: {fig['caption'][:80]}\n"
            tweets.append(("5/N Figures", tweet5))

        tweet6 = "What's next?\n\n"
        tweet6 += "[Add: future directions and broader impact]\n\n"
        tweet6 += "We'd love to hear your thoughts!"
        tweets.append(("6/N Impact", tweet6))

        tweet7 = "Thanks to all co-authors!\n\n"
        tweet7 += "Paper: [arXiv/DOI URL]\n"
        tweet7 += "Code: [GitHub URL]\n\n"
        tweet7 += f"{hashtags}"
        tweets.append(("7/N Links", tweet7))

    return tweets


def generate_linkedin_post(paper_info: dict, style_info: dict,
                           language: str = "en") -> str:
    """
    生成 LinkedIn 长帖（800-1200 词）。

    Args:
        paper_info: 论文结构化信息
        style_info: 社交媒体风格参考
        language: 输出语言

    Returns:
        str: LinkedIn 帖子文本
    """
    title = paper_info.get("title", "Our new paper")
    abstract = paper_info.get("abstract", "")
    contributions = paper_info.get("contributions", [])
    methods = paper_info.get("methods", "")
    results = paper_info.get("results", "")
    hashtags = " ".join(style_info.get("trending_hashtags", [])[:5])

    if language == "zh":
        post = f"很高兴分享我们的最新研究成果！\n\n"
        post += f"**{title}**\n\n"
        post += f"---\n\n"
        post += f"**研究背景**\n\n"
        sentences = abstract.split(".")
        post += ". ".join(sentences[:3]).strip() + ".\n\n"
        post += f"**核心贡献**\n\n"
        for i, c in enumerate(contributions[:4], 1):
            post += f"{i}. {c[:200]}\n"
        post += f"\n**主要结果**\n\n"
        result_sentences = _extract_key_sentences(results, 4)
        for s in result_sentences:
            post += f"- {s[:150]}\n"
        post += f"\n**对行业的影响**\n\n"
        post += "[请补充：这项研究对行业和实际应用的潜在影响]\n\n"
        post += f"---\n\n"
        post += f"论文链接：[URL]\n"
        post += f"代码仓库：[GitHub URL（如有）]\n\n"
        post += f"欢迎讨论交流，也欢迎转发扩散！\n\n"
        post += hashtags
    else:
        post = f"Thrilled to share our latest research!\n\n"
        post += f"**{title}**\n\n"
        post += f"---\n\n"
        post += f"**Background**\n\n"
        sentences = abstract.split(".")
        post += ". ".join(sentences[:3]).strip() + ".\n\n"
        post += f"**Key Contributions**\n\n"
        for i, c in enumerate(contributions[:4], 1):
            post += f"{i}. {c[:200]}\n"
        post += f"\n**Main Results**\n\n"
        result_sentences = _extract_key_sentences(results, 4)
        for s in result_sentences:
            post += f"- {s[:150]}\n"
        post += f"\n**Industry Impact**\n\n"
        post += "[Add: potential impact on industry and practical applications]\n\n"
        post += f"---\n\n"
        post += f"Paper: [URL]\n"
        post += f"Code: [GitHub URL]\n\n"
        post += f"Would love to hear your thoughts! Feel free to share.\n\n"
        post += hashtags

    return post


def generate_wechat_outline(paper_info: dict, style_info: dict) -> str:
    """
    生成微信公众号文章大纲。

    Returns:
        str: 文章大纲（Markdown 格式）
    """
    title = paper_info.get("title", "")
    abstract = paper_info.get("abstract", "")
    contributions = paper_info.get("contributions", [])
    figures = paper_info.get("figures", [])

    outline = "# 微信公众号文章大纲\n\n"

    # 标题建议
    outline += "## 标题建议\n\n"
    outline += f"- 方案 A（学术向）：「{title}」—— [期刊/会议名] 最新成果\n"
    outline += f"- 方案 B（科普向）：[用一句通俗的话概括核心发现]\n"
    outline += f"- 方案 C（悬念式）：[提出引发好奇的问题]\n\n"

    # 导语
    outline += "## 导语（100 字以内）\n\n"
    sentences = abstract.split(".")
    if sentences:
        outline += f"> {'. '.join(sentences[:2]).strip()}.\n\n"

    # 研究背景
    outline += "## 一、研究背景\n\n"
    outline += "- 该领域面临的核心挑战是什么？\n"
    outline += "- 已有方法存在哪些不足？\n"
    outline += "- 为什么需要新的解决方案？\n\n"

    # 方法亮点
    outline += "## 二、方法亮点\n\n"
    if contributions:
        for i, c in enumerate(contributions[:3], 1):
            outline += f"### 亮点 {i}\n\n"
            outline += f"- 技术描述：{c[:150]}\n"
            outline += f"- 通俗类比：[请补充一个日常生活类比]\n"
            outline += f"- 配图建议：[方法示意图 / 流程图]\n\n"
    else:
        outline += "- [请从论文中提取 2-3 个方法亮点]\n\n"

    # 主要结果
    outline += "## 三、主要结果\n\n"
    outline += "- 定量结果：[性能数据、对比基线]\n"
    outline += "- 定性分析：[可视化结果、案例分析]\n"
    if figures:
        outline += "- 关键图表：\n"
        for fig in figures[:5]:
            outline += f"  - Fig.{fig['number']}: {fig['caption'][:80]}\n"
    outline += "\n"

    # 意义与展望
    outline += "## 四、意义与展望\n\n"
    outline += "- 学术意义：[对该领域理论的推动]\n"
    outline += "- 应用前景：[潜在的产业化应用]\n"
    outline += "- 未来方向：[作者计划的后续工作]\n\n"

    # 论文信息
    outline += "## 五、论文信息\n\n"
    outline += f"- 标题：{title}\n"
    outline += "- 作者：[作者列表]\n"
    outline += "- 期刊/会议：[发表场所]\n"
    outline += "- DOI：[DOI 链接]\n"
    outline += "- 代码：[GitHub 链接（如有）]\n"

    return outline


def generate_ppt_outline(paper_info: dict) -> str:
    """
    生成学术报告 PPT 大纲（5-10 页）。

    Returns:
        str: PPT 大纲（Markdown 格式）
    """
    title = paper_info.get("title", "")
    contributions = paper_info.get("contributions", [])
    figures = paper_info.get("figures", [])

    outline = "# 学术报告 PPT 大纲\n\n"

    outline += "## 第 1 页：封面\n\n"
    outline += f"- 标题：{title}\n"
    outline += "- 作者 & 单位\n"
    outline += "- 期刊/会议 & 日期\n\n"

    outline += "## 第 2 页：研究动机\n\n"
    outline += "- 领域核心问题（1-2 句话）\n"
    outline += "- 已有方法的不足（2-3 条要点）\n"
    outline += "- 本文目标（1 句话）\n\n"

    outline += "## 第 3 页：方法概览\n\n"
    outline += "- 整体框架图\n"
    if contributions:
        for c in contributions[:3]:
            outline += f"- {c[:100]}\n"
    outline += "\n"

    outline += "## 第 4-5 页：方法细节\n\n"
    outline += "- 模块 1：[核心创新点]\n"
    outline += "- 模块 2：[技术细节]\n"
    outline += "- 配图：方法示意图、公式推导\n\n"

    outline += "## 第 6 页：实验设置\n\n"
    outline += "- 数据集\n"
    outline += "- 基线方法\n"
    outline += "- 评估指标\n\n"

    outline += "## 第 7-8 页：实验结果\n\n"
    outline += "- 主实验结果表\n"
    outline += "- 消融实验\n"
    if figures:
        for fig in figures[:3]:
            outline += f"- Fig.{fig['number']}: {fig['caption'][:60]}\n"
    outline += "\n"

    outline += "## 第 9 页：分析与讨论\n\n"
    outline += "- 为什么有效？\n"
    outline += "- 局限性\n"
    outline += "- 可视化案例\n\n"

    outline += "## 第 10 页：总结与展望\n\n"
    outline += "- 核心贡献回顾（3 条要点）\n"
    outline += "- 未来方向\n"
    outline += "- 致谢\n"

    return outline


def _extract_key_sentences(text: str, n: int = 3) -> list[str]:
    """从文本中提取关键句子。"""
    if not text:
        return ["[请从论文中补充]"]

    sentences = re.split(r'(?<=[.!?])\s+', text)
    key = []

    # 优先选包含结果性关键词的句子
    priority_keywords = [
        "achieve", "outperform", "improve", "state-of-the-art",
        "significant", "demonstrate", "show that", "result",
        "accuracy", "performance", "比", "提升", "优于", "达到"
    ]

    for s in sentences:
        s_clean = s.strip()
        if len(s_clean) < 20 or len(s_clean) > 300:
            continue
        if any(kw in s_clean.lower() for kw in priority_keywords):
            key.append(s_clean)
        if len(key) >= n:
            break

    # 如果不够，补充普通句子
    if len(key) < n:
        for s in sentences:
            s_clean = s.strip()
            if 20 < len(s_clean) < 300 and s_clean not in key:
                key.append(s_clean)
            if len(key) >= n:
                break

    return key[:n] if key else ["[请从论文中补充]"]
```

---

## 完整编排脚本

以下是将全部步骤串联的端到端 Python 脚本：

```python
#!/usr/bin/env python3
"""
学术社交媒体内容生成器 (Academic Promo)
编排 pdf-parser + web-search，为论文生成多渠道社交媒体推广内容。

用法:
    export ACCESS_KEY="your_access_key"
    python3 academic_promo.py <PDF_URL|DOI> [channels] [language] [tone]

示例:
    python3 academic_promo.py https://arxiv.org/pdf/2401.12345
    python3 academic_promo.py https://arxiv.org/pdf/2401.12345 twitter,linkedin en
    python3 academic_promo.py 10.1038/s41586-024-00001-1 all zh professional
"""

import os
import re
import sys
import json
import time
import requests
from datetime import datetime

# ─── 配置 ───────────────────────────────────────────────

AK = os.environ.get("ACCESS_KEY", "")
if not AK:
    print("错误：未设置 ACCESS_KEY 环境变量。")
    print("请在 ~/.openclaw/openclaw.json 中配置 academic-promo.env.ACCESS_KEY")
    sys.exit(1)

BASE_PARSE = "https://open.bohrium.com/openapi/v1/parse"
BASE_SEARCH = "https://open.bohrium.com/openapi/v1/search/web"
HEADERS_JSON = {"accessKey": AK, "Content-Type": "application/json"}
HEADERS_AK = {"accessKey": AK}


# ─── 工具函数 ───────────────────────────────────────────

def doi_to_pdf_url(doi: str) -> str:
    """将 DOI 转换为 PDF URL。"""
    if doi.startswith("10.48550/arxiv."):
        arxiv_id = doi.replace("10.48550/arxiv.", "")
        return f"https://arxiv.org/pdf/{arxiv_id}"
    if "arxiv.org" in doi:
        return doi if doi.endswith(".pdf") else doi + ".pdf"
    return f"https://doi.org/{doi}"


def extract_field_keywords(title: str, abstract: str) -> list[str]:
    """从标题和摘要中提取领域关键词。"""
    keywords = set()

    # 提取多词术语（大写开头）
    terms = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', f"{title} {abstract}")
    keywords.update(terms[:5])

    # 提取方法/模型名
    models = re.findall(
        r'\b([A-Z][a-zA-Z]*(?:Net|GAN|BERT|GPT|Transformer|CNN|RNN|'
        r'GNN|VAE|Flow|Model|Method|Framework|Network))\b',
        f"{title} {abstract}"
    )
    keywords.update(models)

    # 提取标题中的关键名词短语
    title_words = [w for w in title.split() if len(w) > 3 and w[0].isupper()]
    keywords.update(title_words[:3])

    return list(keywords)[:8]


def _extract_key_sentences(text: str, n: int = 3) -> list[str]:
    """从文本中提取关键句子。"""
    if not text:
        return ["[请从论文中补充]"]

    sentences = re.split(r'(?<=[.!?])\s+', text)
    key = []

    priority_keywords = [
        "achieve", "outperform", "improve", "state-of-the-art",
        "significant", "demonstrate", "show that", "result",
        "accuracy", "performance", "比", "提升", "优于", "达到"
    ]

    for s in sentences:
        s_clean = s.strip()
        if len(s_clean) < 20 or len(s_clean) > 300:
            continue
        if any(kw in s_clean.lower() for kw in priority_keywords):
            key.append(s_clean)
        if len(key) >= n:
            break

    if len(key) < n:
        for s in sentences:
            s_clean = s.strip()
            if 20 < len(s_clean) < 300 and s_clean not in key:
                key.append(s_clean)
            if len(key) >= n:
                break

    return key[:n] if key else ["[请从论文中补充]"]


# ─── 步骤 1：PDF 解析 ──────────────────────────────────

def parse_paper(pdf_url: str) -> dict:
    """解析论文 PDF，提取核心内容。"""
    print(f"\n[步骤 1/2] 解析论文 PDF：{pdf_url}")

    payload = {
        "url": pdf_url,
        "sync": False,
        "textual": True,
        "table": True,
        "molecule": False,
        "chart": False,
        "figure": False,
        "expression": True,
        "equation": True,
        "timeout": 1800
    }

    try:
        r = requests.post(
            f"{BASE_PARSE}/trigger-url-async",
            headers=HEADERS_JSON,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("  错误：无法连接到 open.bohrium.com")
        return {"status": "failed", "error": "连接失败"}
    except requests.exceptions.Timeout:
        print("  错误：提交请求超时")
        return {"status": "failed", "error": "请求超时"}

    submit = r.json()
    if submit.get("code"):
        print(f"  提交失败：{submit.get('message', '未知错误')}")
        return {"status": "failed", "error": submit.get("message")}

    token = submit["token"]
    print(f"  已提交，token={token}")

    # 轮询结果
    for attempt in range(90):
        time.sleep(2)
        try:
            r = requests.post(
                f"{BASE_PARSE}/get-result",
                headers=HEADERS_JSON,
                json={
                    "token": token,
                    "content": True,
                    "objects": True,
                    "pages_dict": True
                },
                timeout=30
            )
            result = r.json()
        except Exception as e:
            if attempt % 10 == 0:
                print(f"  [{attempt+1}] 查询失败：{e}")
            continue

        status = result.get("status", "")
        proc_page = result.get("proc_page", 0)
        total_page = result.get("total_page", 0)

        if status == "success":
            content = result.get("content", "")
            print(f"  解析完成！共 {total_page} 页，{len(content)} 字符")
            extracted = extract_paper_structure(content)
            extracted["status"] = "success"
            extracted["content"] = content
            extracted["total_page"] = total_page
            return extracted

        elif status == "failed":
            desc = result.get("description", "未知错误")
            print(f"  解析失败：{desc}")
            return {"status": "failed", "error": desc}
        else:
            if attempt % 10 == 0:
                print(f"  [{attempt+1}] 解析中... ({proc_page}/{total_page} 页)")

    print("  超时：解析任务未在 180 秒内完成。")
    return {"status": "timeout", "error": "解析超时（180秒）"}


def extract_paper_structure(content: str) -> dict:
    """从解析结果中提取论文结构化信息。"""
    result = {
        "title": "",
        "abstract": "",
        "contributions": [],
        "methods": "",
        "results": "",
        "figures": []
    }

    # 提取标题
    title_match = re.search(
        r'\\begin\{title\}(.*?)\\end\{title\}',
        content, re.DOTALL
    )
    if title_match:
        result["title"] = title_match.group(1).strip()

    # 提取摘要
    abstract_match = re.search(
        r'(?i)abstract[:\s]*(.*?)(?=\\begin\{section\}|\\begin\{subsection\}|introduction)',
        content, re.DOTALL
    )
    if abstract_match:
        result["abstract"] = abstract_match.group(1).strip()[:2000]

    # 按段落拆分
    sections = re.split(r'\\begin\{(?:section|subsection)\}', content)
    for section in sections:
        first_line = section.strip()[:300].lower()
        if re.search(r'(?i)(method|approach|proposed|framework|architecture)', first_line):
            result["methods"] = section.strip()[:3000]
        if re.search(r'(?i)(result|experiment|evaluation|performance)', first_line):
            result["results"] = section.strip()[:3000]

    # 提取贡献
    contribution_patterns = [
        r'[^.]*(?:our\s+(?:main\s+)?contributions?\s+(?:are|include))[^.]+\.',
        r'[^.]*(?:we\s+(?:propose|present|introduce|develop|design))\s+[^.]+\.',
        r'[^.]*(?:this\s+(?:paper|work)\s+(?:proposes?|presents?|introduces?))\s+[^.]+\.',
    ]
    for pattern in contribution_patterns:
        matches = re.findall(pattern, content[:10000], re.IGNORECASE)
        for m in matches:
            claim = m.strip()
            if 20 < len(claim) < 500:
                result["contributions"].append(claim)

    seen = set()
    unique = []
    for c in result["contributions"]:
        norm = c.lower().strip()
        if norm not in seen:
            seen.add(norm)
            unique.append(c)
    result["contributions"] = unique[:5]

    # 提取图表描述
    figure_patterns = [
        r'(?i)(?:figure|fig\.?)\s*(\d+)[.:]\s*([^.]+\.)',
        r'(?i)(?:table)\s*(\d+)[.:]\s*([^.]+\.)',
    ]
    for pattern in figure_patterns:
        matches = re.findall(pattern, content)
        for num, caption in matches:
            result["figures"].append({
                "number": num,
                "caption": caption.strip()[:200]
            })

    return result


# ─── 步骤 2：Web 搜索领域风格 ─────────────────────────

def search_field_style(title: str, field_keywords: list[str]) -> dict:
    """搜索该领域在社交媒体上的讨论风格。"""
    print(f"\n[步骤 2/2] 搜索领域社交媒体讨论风格")

    style_info = {
        "twitter_style": [],
        "linkedin_style": [],
        "wechat_style": [],
        "trending_hashtags": []
    }

    queries = [
        (f"twitter thread {' '.join(field_keywords[:3])} paper new research",
         "twitter_style"),
        (f"linkedin post {' '.join(field_keywords[:3])} research publication",
         "linkedin_style"),
        (f"微信公众号 {' '.join(field_keywords[:2])} 论文解读",
         "wechat_style"),
    ]

    for query, target in queries:
        try:
            r = requests.get(
                BASE_SEARCH,
                headers=HEADERS_AK,
                params={"q": query, "num": 5},
                timeout=15
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("organic_results", [])
            print(f"  {target}：找到 {len(results)} 条参考")
            for hit in results:
                style_info[target].append({
                    "title": hit.get("title", ""),
                    "link": hit.get("link", ""),
                    "snippet": hit.get("snippet", "")[:300]
                })
        except Exception as e:
            print(f"  {target} 搜索失败：{e}")

    # 搜索话题标签
    try:
        r = requests.get(
            BASE_SEARCH,
            headers=HEADERS_AK,
            params={
                "q": f"academic twitter hashtag {' '.join(field_keywords[:3])}",
                "num": 3
            },
            timeout=15
        )
        data = r.json()
        for hit in data.get("organic_results", []):
            tags = re.findall(r'#\w+', hit.get("snippet", ""))
            style_info["trending_hashtags"].extend(tags)
        style_info["trending_hashtags"] = list(
            set(style_info["trending_hashtags"])
        )[:10]
        print(f"  热门标签：{style_info['trending_hashtags']}")
    except Exception as e:
        print(f"  标签搜索失败：{e}")

    return style_info


# ─── 内容生成 ─────────────────────────────────────────

def generate_twitter_thread(paper_info: dict, style_info: dict,
                            language: str = "en") -> list[tuple]:
    """生成 Twitter 推文串（5-7 条）。"""
    title = paper_info.get("title", "Our new paper")
    abstract = paper_info.get("abstract", "")
    contributions = paper_info.get("contributions", [])
    methods = paper_info.get("methods", "")
    results = paper_info.get("results", "")
    figures = paper_info.get("figures", [])
    hashtags = " ".join(style_info.get("trending_hashtags", [])[:3])

    tweets = []

    if language == "zh":
        tweets.append(("1/N 论文亮点",
            f"我们的新论文发表了！\n\n"
            f"「{title[:80]}」\n\n"
            f"{contributions[0][:100] if contributions else '[核心贡献]'}\n\n"
            f"论文链接：[URL]\n{hashtags}"))

        sentences = abstract.split(".")
        motivation = ". ".join(sentences[:2]).strip()
        tweets.append(("2/N 研究动机",
            f"为什么做这个研究？\n\n{motivation[:200]}"))

        tweet3 = "我们的核心方法：\n\n"
        if len(contributions) > 1:
            for i, c in enumerate(contributions[1:3], 1):
                tweet3 += f"  {i}. {c[:80]}\n"
        else:
            for s in _extract_key_sentences(methods, 2):
                tweet3 += f"  - {s[:100]}\n"
        tweets.append(("3/N 核心方法", tweet3))

        tweet4 = "主要结果：\n\n"
        for s in _extract_key_sentences(results, 3):
            tweet4 += f"  - {s[:80]}\n"
        tweets.append(("4/N 主要结果", tweet4))

        if figures:
            tweet5 = "关键图表一览：\n\n"
            for fig in figures[:3]:
                tweet5 += f"  Fig.{fig['number']}: {fig['caption'][:60]}\n"
            tweet5 += "\n（完整图表见论文）"
            tweets.append(("5/N 关键图表", tweet5))

        tweets.append(("6/N 影响与展望",
            "这项工作的意义：\n\n"
            "[请补充：这项研究对领域的影响和未来方向]\n\n"
            "欢迎讨论和交流！"))

        tweets.append(("7/N 致谢与链接",
            f"感谢所有合作者的贡献！\n\n"
            f"论文：[arXiv/DOI URL]\n"
            f"代码：[GitHub URL（如有）]\n\n{hashtags}"))

    else:
        tweets.append(("1/N Hook",
            f"Excited to share our new paper!\n\n"
            f"\"{title[:100]}\"\n\n"
            f"{contributions[0][:120] if contributions else '[Key contribution]'}\n\n"
            f"Paper: [URL]\n{hashtags}"))

        sentences = abstract.split(".")
        motivation = ". ".join(sentences[:2]).strip()
        tweets.append(("2/N Motivation",
            f"Why does this matter?\n\n{motivation[:220]}"))

        tweet3 = "Our key idea:\n\n"
        if len(contributions) > 1:
            for i, c in enumerate(contributions[1:3], 1):
                tweet3 += f"{i}. {c[:100]}\n"
        else:
            for s in _extract_key_sentences(methods, 2):
                tweet3 += f"- {s[:120]}\n"
        tweets.append(("3/N Method", tweet3))

        tweet4 = "Key results:\n\n"
        for s in _extract_key_sentences(results, 3):
            tweet4 += f"- {s[:100]}\n"
        tweets.append(("4/N Results", tweet4))

        if figures:
            tweet5 = "Visual highlights:\n\n"
            for fig in figures[:3]:
                tweet5 += f"Fig.{fig['number']}: {fig['caption'][:80]}\n"
            tweets.append(("5/N Figures", tweet5))

        tweets.append(("6/N Impact",
            "What's next?\n\n"
            "[Add: future directions and broader impact]\n\n"
            "We'd love to hear your thoughts!"))

        tweets.append(("7/N Links",
            f"Thanks to all co-authors!\n\n"
            f"Paper: [arXiv/DOI URL]\n"
            f"Code: [GitHub URL]\n\n{hashtags}"))

    return tweets


def generate_linkedin_post(paper_info: dict, style_info: dict,
                           language: str = "en") -> str:
    """生成 LinkedIn 长帖。"""
    title = paper_info.get("title", "Our new paper")
    abstract = paper_info.get("abstract", "")
    contributions = paper_info.get("contributions", [])
    results = paper_info.get("results", "")
    hashtags = " ".join(style_info.get("trending_hashtags", [])[:5])

    if language == "zh":
        post = f"很高兴分享我们的最新研究成果！\n\n"
        post += f"**{title}**\n\n---\n\n"
        post += f"**研究背景**\n\n"
        post += ". ".join(abstract.split(".")[:3]).strip() + ".\n\n"
        post += f"**核心贡献**\n\n"
        for i, c in enumerate(contributions[:4], 1):
            post += f"{i}. {c[:200]}\n"
        post += f"\n**主要结果**\n\n"
        for s in _extract_key_sentences(results, 4):
            post += f"- {s[:150]}\n"
        post += f"\n**对行业的影响**\n\n"
        post += "[请补充：这项研究对行业和实际应用的潜在影响]\n\n"
        post += f"---\n\n论文链接：[URL]\n代码仓库：[GitHub URL]\n\n"
        post += f"欢迎讨论交流，也欢迎转发扩散！\n\n{hashtags}"
    else:
        post = f"Thrilled to share our latest research!\n\n"
        post += f"**{title}**\n\n---\n\n"
        post += f"**Background**\n\n"
        post += ". ".join(abstract.split(".")[:3]).strip() + ".\n\n"
        post += f"**Key Contributions**\n\n"
        for i, c in enumerate(contributions[:4], 1):
            post += f"{i}. {c[:200]}\n"
        post += f"\n**Main Results**\n\n"
        for s in _extract_key_sentences(results, 4):
            post += f"- {s[:150]}\n"
        post += f"\n**Industry Impact**\n\n"
        post += "[Add: potential impact on industry and applications]\n\n"
        post += f"---\n\nPaper: [URL]\nCode: [GitHub URL]\n\n"
        post += f"Would love to hear your thoughts!\n\n{hashtags}"

    return post


def generate_wechat_outline(paper_info: dict, style_info: dict) -> str:
    """生成微信公众号文章大纲。"""
    title = paper_info.get("title", "")
    abstract = paper_info.get("abstract", "")
    contributions = paper_info.get("contributions", [])
    figures = paper_info.get("figures", [])

    outline = "# 微信公众号文章大纲\n\n"
    outline += "## 标题建议\n\n"
    outline += f"- 方案 A（学术向）：「{title}」—— [期刊/会议名] 最新成果\n"
    outline += f"- 方案 B（科普向）：[用一句通俗的话概括核心发现]\n"
    outline += f"- 方案 C（悬念式）：[提出引发好奇的问题]\n\n"

    outline += "## 导语（100 字以内）\n\n"
    sentences = abstract.split(".")
    if sentences:
        outline += f"> {'. '.join(sentences[:2]).strip()}.\n\n"

    outline += "## 一、研究背景\n\n"
    outline += "- 该领域面临的核心挑战是什么？\n"
    outline += "- 已有方法存在哪些不足？\n"
    outline += "- 为什么需要新的解决方案？\n\n"

    outline += "## 二、方法亮点\n\n"
    if contributions:
        for i, c in enumerate(contributions[:3], 1):
            outline += f"### 亮点 {i}\n\n"
            outline += f"- 技术描述：{c[:150]}\n"
            outline += f"- 通俗类比：[请补充一个日常生活类比]\n"
            outline += f"- 配图建议：[方法示意图 / 流程图]\n\n"

    outline += "## 三、主要结果\n\n"
    outline += "- 定量结果：[性能数据、对比基线]\n"
    outline += "- 定性分析：[可视化结果、案例分析]\n"
    if figures:
        outline += "- 关键图表：\n"
        for fig in figures[:5]:
            outline += f"  - Fig.{fig['number']}: {fig['caption'][:80]}\n"
    outline += "\n"

    outline += "## 四、意义与展望\n\n"
    outline += "- 学术意义：[对该领域理论的推动]\n"
    outline += "- 应用前景：[潜在的产业化应用]\n"
    outline += "- 未来方向：[作者计划的后续工作]\n\n"

    outline += "## 五、论文信息\n\n"
    outline += f"- 标题：{title}\n"
    outline += "- 作者：[作者列表]\n"
    outline += "- 期刊/会议：[发表场所]\n"
    outline += "- DOI：[DOI 链接]\n"
    outline += "- 代码：[GitHub 链接（如有）]\n"

    return outline


def generate_ppt_outline(paper_info: dict) -> str:
    """生成学术报告 PPT 大纲。"""
    title = paper_info.get("title", "")
    contributions = paper_info.get("contributions", [])
    figures = paper_info.get("figures", [])

    outline = "# 学术报告 PPT 大纲\n\n"
    outline += "## 第 1 页：封面\n\n"
    outline += f"- 标题：{title}\n- 作者 & 单位\n- 期刊/会议 & 日期\n\n"
    outline += "## 第 2 页：研究动机\n\n"
    outline += "- 领域核心问题\n- 已有方法的不足\n- 本文目标\n\n"
    outline += "## 第 3 页：方法概览\n\n- 整体框架图\n"
    for c in contributions[:3]:
        outline += f"- {c[:100]}\n"
    outline += "\n## 第 4-5 页：方法细节\n\n"
    outline += "- 模块 1：[核心创新点]\n- 模块 2：[技术细节]\n"
    outline += "- 配图：方法示意图、公式推导\n\n"
    outline += "## 第 6 页：实验设置\n\n"
    outline += "- 数据集\n- 基线方法\n- 评估指标\n\n"
    outline += "## 第 7-8 页：实验结果\n\n- 主实验结果表\n- 消融实验\n"
    for fig in figures[:3]:
        outline += f"- Fig.{fig['number']}: {fig['caption'][:60]}\n"
    outline += "\n## 第 9 页：分析与讨论\n\n"
    outline += "- 为什么有效？\n- 局限性\n- 可视化案例\n\n"
    outline += "## 第 10 页：总结与展望\n\n"
    outline += "- 核心贡献回顾\n- 未来方向\n- 致谢\n"

    return outline


# ─── 报告组装 ─────────────────────────────────────────

def assemble_output(paper_info: dict, style_info: dict,
                    channels: list[str], language: str) -> str:
    """组装所有渠道的内容为最终输出。"""
    output = []
    output.append("# 学术社交媒体推广内容\n")
    output.append(f"**论文**：{paper_info.get('title', 'N/A')}")
    output.append(f"**生成时间**：{datetime.now().isoformat()}")
    output.append(f"**目标渠道**：{', '.join(channels)}")
    output.append(f"**语言**：{language}\n")

    generate_all = "all" in channels

    # Twitter
    if generate_all or "twitter" in channels:
        output.append("---\n")
        output.append("## Twitter 推文串\n")
        tweets = generate_twitter_thread(paper_info, style_info, language)
        for label, text in tweets:
            output.append(f"### {label}\n")
            fence = chr(96) * 3
            output.append(f"{fence}\n{text}\n{fence}\n")

    # LinkedIn
    if generate_all or "linkedin" in channels:
        output.append("---\n")
        output.append("## LinkedIn 帖子\n")
        post = generate_linkedin_post(paper_info, style_info, language)
        output.append(post)

    # WeChat
    if generate_all or "wechat" in channels:
        output.append("\n---\n")
        wechat = generate_wechat_outline(paper_info, style_info)
        output.append(wechat)

    # PPT
    if generate_all or "ppt" in channels:
        output.append("\n---\n")
        ppt = generate_ppt_outline(paper_info)
        output.append(ppt)

    return "\n".join(output)


# ─── 主流程 ───────────────────────────────────────────

def academic_promo(paper_input: str, channels: list[str] = None,
                   language: str = "zh", tone: str = "professional"):
    """
    学术社交媒体内容生成主函数。

    Args:
        paper_input: PDF URL 或 DOI
        channels: 目标渠道列表（twitter, linkedin, wechat, ppt, all）
        language: 输出语言（zh/en/both）
        tone: 文案风格（professional/accessible/exciting）
    """
    if channels is None:
        channels = ["all"]

    print("=" * 60)
    print("  学术社交媒体内容生成器 (Academic Promo)")
    print(f"  输入：{paper_input}")
    print(f"  渠道：{', '.join(channels)}")
    print(f"  语言：{language}")
    print(f"  风格：{tone}")
    print("=" * 60)

    # 判断输入类型
    pdf_url = paper_input
    if paper_input.startswith("10."):
        pdf_url = doi_to_pdf_url(paper_input)
        print(f"\n检测到 DOI，转换为 URL：{pdf_url}")
    elif not paper_input.startswith("http"):
        print("错误：请提供 PDF URL 或 DOI。")
        return

    # 步骤 1：PDF 解析
    paper_info = parse_paper(pdf_url)
    if paper_info.get("status") != "success":
        error = paper_info.get("error", "未知错误")
        print(f"\nPDF 解析失败（{error}），无法继续。")
        print("可能的原因：")
        print("  1. PDF URL 不可直接下载 → 请提供直链")
        print("  2. 网络连接问题 → 检查网络后重试")
        print("  3. 解析超时 → 论文页数过多")
        return

    # 提取领域关键词
    field_keywords = extract_field_keywords(
        paper_info.get("title", ""),
        paper_info.get("abstract", "")
    )
    print(f"\n领域关键词：{field_keywords}")

    # 步骤 2：搜索领域风格
    style_info = search_field_style(
        paper_info.get("title", ""),
        field_keywords
    )

    # 生成内容
    print("\n" + "=" * 60)
    print("  生成推广内容...")
    print("=" * 60 + "\n")

    if language == "both":
        # 双语模式：分别生成中英文
        output_zh = assemble_output(paper_info, style_info, channels, "zh")
        output_en = assemble_output(paper_info, style_info, channels, "en")
        full_output = (
            "# 中文版\n\n" + output_zh +
            "\n\n---\n---\n\n# English Version\n\n" + output_en
        )
    else:
        full_output = assemble_output(paper_info, style_info, channels, language)

    print(full_output)

    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"academic_promo_{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_output)
    print(f"\n推广内容已保存到：{output_file}")

    return full_output


# ─── 入口 ─────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python academic_promo.py <PDF_URL|DOI> [channels] [language] [tone]")
        print()
        print("参数：")
        print("  PDF_URL|DOI   论文 PDF 的 URL 或 DOI")
        print("  channels      目标渠道，逗号分隔（twitter,linkedin,wechat,ppt,all）")
        print("  language      输出语言（zh/en/both）")
        print("  tone          文案风格（professional/accessible/exciting）")
        print()
        print("示例：")
        print("  python academic_promo.py https://arxiv.org/pdf/2401.12345")
        print("  python academic_promo.py https://arxiv.org/pdf/2401.12345 twitter,linkedin en")
        print("  python academic_promo.py 10.1038/s41586-024-00001-1 all zh professional")
        print("  python academic_promo.py https://arxiv.org/pdf/2401.12345 all both")
        sys.exit(1)

    paper = sys.argv[1]
    channels = sys.argv[2].split(",") if len(sys.argv) > 2 else ["all"]
    language = sys.argv[3] if len(sys.argv) > 3 else "zh"
    tone = sys.argv[4] if len(sys.argv) > 4 else "professional"

    if language not in ("zh", "en", "both"):
        print(f"未知语言：{language}，使用默认 zh")
        language = "zh"

    academic_promo(paper, channels, language, tone)
```

---

## 各步骤详解

### 步骤 1：PDF 解析 (`pdf-parser`)

调用 `trigger-url-async` 提交 PDF 解析任务，异步轮询 `get-result` 获取结果。与 `paper-dissector` 不同，本技能解析全文（不限制页数），并额外开启 `figure: true` 和 `chart: true` 以提取关键图表信息。

**解析选项差异：**

| 选项 | paper-dissector | academic-promo | 原因 |
|------|----------------|----------------|------|
| `figure` | `false` | `true` | 社交媒体内容需要图表描述 |
| `chart` | `true` | `true` | 都需要 |
| `pages` | `[0,1,2,3,4]`（quick 模式） | 全部 | 推广内容需要完整结果 |
| `objects` | `false` | `true` | 需要提取图表对象 |

**从解析结果中提取的信息：**

- **标题**：从 `\begin{title}...\end{title}` 标记提取
- **摘要**：从 Abstract 段落提取
- **核心贡献**：匹配 "we propose/present/introduce" 等模式
- **方法描述**：Method/Approach 段落
- **实验结果**：Results/Experiments 段落
- **图表描述**：匹配 "Figure N:" 和 "Table N:" 模式

---

### 步骤 2：Web 搜索领域风格 (`web-search`)

通过三组搜索查询了解该领域在不同平台上的学术传播风格：

1. **Twitter 风格**：搜索 `"twitter thread [领域关键词] paper new research"`
2. **LinkedIn 风格**：搜索 `"linkedin post [领域关键词] research publication"`
3. **微信风格**：搜索 `"微信公众号 [领域关键词] 论文解读"`
4. **话题标签**：搜索领域热门 hashtag

**风格搜索的作用：**

- 了解同领域学者在社交媒体上的表达习惯
- 发现热门话题标签（hashtag），提高内容可见度
- 参考优秀推文/帖子的结构和措辞

---

## 使用示例

### 示例 1：为 arXiv 论文生成全渠道内容

```bash
export ACCESS_KEY="your_access_key"
python academic_promo.py https://arxiv.org/pdf/2401.12345 all zh
```

### 示例 2：只生成 Twitter 英文推文串

```bash
python academic_promo.py https://arxiv.org/pdf/2401.12345 twitter en
```

### 示例 3：通过 DOI 生成双语内容

```bash
python academic_promo.py 10.1038/s41586-024-00001-1 all both
```

### 示例 4：只生成微信公众号大纲和 PPT 大纲

```bash
python academic_promo.py https://arxiv.org/pdf/2401.12345 wechat,ppt zh
```

### 命令行调用

```bash
# 全渠道中文（默认）
python academic_promo.py https://arxiv.org/pdf/2401.12345

# 全渠道英文
python academic_promo.py https://arxiv.org/pdf/2401.12345 all en

# 指定渠道
python academic_promo.py https://arxiv.org/pdf/2401.12345 twitter,linkedin en

# DOI 输入 + 双语
python academic_promo.py 10.1038/s41586-024-00001-1 all both professional
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `ACCESS_KEY` 未设置 | 环境变量未配置 | 在 `~/.openclaw/openclaw.json` 中配置 `academic-promo.env.ACCESS_KEY` |
| PDF 解析失败 | URL 不可直接下载 | 使用 arXiv PDF 直链（`https://arxiv.org/pdf/XXXX`），避免需要登录的出版商链接 |
| PDF 解析超时 | 论文页数较多 | 一般 180 秒足够，如超时可检查 PDF 是否可正常下载 |
| 未提取到贡献 | 论文使用非标准表述 | 手动补充 `contributions` 列表，脚本会使用摘要作为 fallback |
| 未提取到图表描述 | 图表标注格式不匹配 | 手动补充 `figures` 列表，或检查 PDF 解析结果中的原始内容 |
| Web 搜索无结果 | 领域关键词太窄 | 尝试使用更通用的英文关键词 |
| 话题标签为空 | 搜索结果中未包含 hashtag | 手动添加领域常用标签（如 `#MachineLearning`, `#AI`） |
| Twitter 推文超过 280 字符 | 提取的内容太长 | 生成的是草稿，发布前需手动精简到 280 字符以内 |
| LinkedIn 帖子格式问题 | Markdown 语法在 LinkedIn 不支持 | 发布时去掉 Markdown 标记，改为纯文本 |
| 微信文章大纲不完整 | 解析信息不够 | 大纲中的 `[请补充]` 占位符需要手动填写 |
| 401 Unauthorized | accessKey 无效 | 确认 ACCESS_KEY 正确，Header 名为 `accessKey`（注意大小写） |

---

## 搭配使用

- **academic-promo** 生成推广文案 → 人工润色后发布
- **paper-dissector** 深度拆解论文 → **academic-promo** 生成推广内容（拆解结果可作为输入参考）
- **academic-promo** 生成微信大纲 → 人工扩写为完整公众号文章
- **academic-promo** 生成 PPT 大纲 → 用于会议报告或组会汇报的框架
- **bohrium-paper-search** 搜索论文 → **academic-promo** 为找到的论文生成推广内容
