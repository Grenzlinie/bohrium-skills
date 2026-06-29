---
name: bohrium-database
description: "Operate Bohrium custom/private databases with bohrium-open-sdk. Use when: the user asks to list Bohrium databases, inspect tables or schemas, query/filter/export rows, insert/update/delete records, create tables, or alter table columns using db_ak/table_ak IDs. NOT for: internal shrimp PostgreSQL operations, general file storage, datasets, or compute jobs."
metadata:
  openclaw:
    primaryEnv: BOHR_ACCESS_KEY
---

# SKILL: Bohrium 自定义数据库

## 概述

使用 `bohrium-open-sdk` 操作用户有权限访问的 Bohrium 自定义数据库。常见对象：

- `db_ak`：数据库访问标识，例如 `669ng`
- `table_ak`：数据表访问标识，例如 `669ng00`

优先使用本目录的 `database_manager.py` 执行常用操作；需要复杂条件、数据清洗或批量导出时，再在临时 Python 脚本中直接调用 SDK。

## 认证与安装

读取环境变量 `BOHR_ACCESS_KEY`，不要打印、记录或硬编码密钥。

```bash
test -n "$BOHR_ACCESS_KEY" || echo "BOHR_ACCESS_KEY is missing"
python3 -m pip install "bohrium-open-sdk>=1.0.5" -q
```

如果 `BOHR_ACCESS_KEY` 不存在，先提示用户配置 AccessKey，不要继续调用 API。

## 快速 CLI

以下命令在 skill 目录内执行，或将脚本路径替换为实际路径：

```bash
python3 database_manager.py list-dbs
python3 database_manager.py list-tables 669ng          # 默认每张表最多显示 30 个字段
python3 database_manager.py detail 669ng00
```

查询数据：

```bash
python3 database_manager.py query 669ng00 \
  --where '[{"field":"名称","op":"LIKE","value":"张"}]' \
  --order-by createTime --desc --page 1 --page-size 20
```

插入数据：

```bash
python3 database_manager.py insert 669ng00 \
  --rows '[{"名称":"新样品","数值a":1.5,"数值b":2.3}]'
```

更新或删除前默认只预览影响范围；确认后加 `--yes`：

```bash
python3 database_manager.py update 669ng00 \
  --where '[{"field":"名称","op":"EQ","value":"旧值"}]' \
  --set '{"名称":"新值","数值a":99}' \
  --yes

python3 database_manager.py delete 669ng00 \
  --where '[{"field":"名称","op":"EQ","value":"要删除的"}]' \
  --yes
```

新建表或修改表结构：

```bash
python3 database_manager.py create-table 669ng "新数据表" \
  --schema '[{"title":"样品名","dataType":"str"},{"title":"分子量","dataType":"num"}]'

python3 database_manager.py alter-table 669ng00 \
  --schema '[{"title":"样品名","dataType":"str"},{"title":"分子量","dataType":"num"},{"title":"新增列","dataType":"str"}]' \
  --yes
```

`--rows`、`--where`、`--set`、`--schema` 都支持 JSON 字符串，也支持 `@/path/to/file.json`。

## 直接 SDK 模板

```python
import os
from bohrium_open_sdk.db import SQLClient

client = SQLClient("", os.environ["BOHR_ACCESS_KEY"], "https://openapi.dp.tech")
```

### 列出数据库

```python
data = client.base().Dbs()
for db in data.get("list", []):
    print(db["name"], db["ak"], db.get("createTime", ""))
```

### 列出表与结构

```python
result = client.db_with_ak("669ng").Tables()
for table in result.get("tables", []):
    fields = ", ".join(f"{f['name']}({f['type']})" for f in table.get("fields", []))
    print(table["name"], table["tableAk"], fields)

detail = client.table_with_ak("669ng00").Detail()
for field in detail.get("fields", []):
    print(field["name"], field["type"])
```

### 查询

```python
from bohrium_open_sdk.db import Op, Where

count, rows = (
    client.table_with_ak("669ng00")
    .Where("价格", Op.GTE, 10)
    .And(Where("名称", Op.LIKE, "样品"))
    .order(key="价格", is_asc=False)
    .page(1)
    .page_size(20)
    .Find()
)
print(count, rows[:20])
```

### 全量导出

```python
from bohrium_open_sdk.db.func import db_query_full

table = client.db_with_ak("669ng")
table.table_ak = "669ng00"
count, df = db_query_full(table, batch_size=1000)
df.to_csv("bohrium_table_export.csv", index=False)
print(f"exported {count} rows")
```

## 条件格式

`database_manager.py --where` 使用数组，每个条件包含：

| 字段 | 必填 | 说明 |
|------|------|------|
| `field` | 是 | 列名，区分大小写 |
| `op` | 是 | 操作符，见下表 |
| `value` | 是 | 查询值 |
| `join` | 否 | 从第二个条件开始可用，`AND` 或 `OR`，默认 `AND` |

操作符：

| 操作符 | 含义 | 值类型 |
|--------|------|--------|
| `EQ` | 等于 | 字符串或数值 |
| `NEQ` | 不等于 | 字符串或数值 |
| `GT` / `GTE` | 大于 / 大于等于 | 数值 |
| `LT` / `LTE` | 小于 / 小于等于 | 数值 |
| `BETWEEN` | 闭区间 | `"1,100"` 或 `[1, 100]` |
| `LIKE` | 字符串包含 | 字符串 |
| `IN` / `NIN` | 包含 / 不包含 | 数组 |
| `ELEMENTMATCHOFNUM` | 数组元素范围 | `{"min":0,"max":10}` |

## 列类型

创建表或修改表结构时，schema 项使用 `{"title": "列名", "dataType": "类型"}`。

| 类型 | 说明 |
|------|------|
| `str` | 字符串 |
| `num` | 数值 |
| `smiles` | SMILES 分子式 |
| `img` | 图片对象，通常需先上传到 Tiefblue |
| `file` | 文件对象，通常需先上传到 Tiefblue |
| `file_arr` | 数组 |

修改表结构要提交修改后的完整 schema。遗漏已有列通常表示删除该列，可能导致数据丢失。

## 安全规则

- 删除、更新、修改表结构前，先用相同条件查询预览目标行或目标 schema。
- 大批量插入、更新、删除超过 100 行时，先向用户说明影响范围并确认。
- 查询结果超过 20 行时，默认只展示前 20 行和总数；用户要求导出时再保存 CSV/JSON。
- 表字段很多时，先用 `list-tables --max-fields 30` 获取概览，再用 `detail` 查看指定表的完整结构。
- 宽表或大表查询尽量带过滤条件；无条件扫描可能触发服务端超时。需要全量数据时用 `export`。
- 图片、文件列只展示 `name` 等短字段，不展示完整签名 URL。
- 默认隐藏 `_id`、`audit_id`、`createTime/create_time`、`updateTime/update_time`、`authors`、`owner_id`、`status` 以及平台内部审计/权限字段，除非用户明确要求。
- 不要暴露完整 API 响应，响应中可能包含内部 ID、临时路径或签名链接。

## 错误处理

| 错误信号 | 处理 |
|----------|------|
| `BOHR_ACCESS_KEY` 不存在 | 提示用户配置 AccessKey |
| 401 / 403 / `code: 2000` | 提示 AccessKey 无效或无权限 |
| 列名 `KeyError` 或查询为空但预期有数据 | 先执行 `detail` 查看准确列名和类型 |
| 表或库不存在 | 用 `list-dbs`、`list-tables` 重新确认 `db_ak` / `table_ak` |
| 网络超时 | 脚本会重试一次；仍失败时建议缩小条件、分页或改用 `export` |
