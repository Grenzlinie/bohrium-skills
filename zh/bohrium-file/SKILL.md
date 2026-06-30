---
name: bohrium-file
description: "Manage Bohrium personal/share disk files via open.bohrium.com OpenAPI. Use when: user asks to list, inspect, download, upload, create directories, move, copy, delete, decompress, or search files in Bohrium personal disk or project share disk. NOT for: dataset management, compute jobs, dev nodes, images, knowledge bases, or appJob workspace browsing unless an appJob id is explicitly provided."
---

# SKILL: Bohrium 文件盘管理

## 概述

通过新版 `open-platform` 网关管理 Bohrium 文件盘：

```text
https://open.bohrium.com/openapi
```

常规文件盘分两类：

| 文件盘 | 路径前缀 | 必要 ID |
|---|---|---|
| 个人盘 | `personal/` | `userId`；当前用户个人盘通常可用 `projectId=0` |
| 项目共享盘 | `share/` | 真实 `projectId` + `userId`；需要项目权限 |

普通 personal/share 文件管理使用 **v1 file API**。不要用 `/v2/file/iterate` 或 `/v2/file/download` 操作 personal/share。

## 认证

从环境变量 `BOHR_ACCESS_KEY` 读取 AccessKey，不要打印或硬编码：

```bash
AK="${BOHR_ACCESS_KEY:?missing BOHR_ACCESS_KEY}"
BASE="${BOHR_OPENAPI_BASE:-https://open.bohrium.com/openapi}"
```

默认使用仓库内其他 Bohrium skills 一致的 Bearer 写法：

```bash
-H "Authorization: Bearer $AK"
```

`accessKey: $AK` header 也兼容，但新 skill 示例统一使用 `Authorization: Bearer $BOHR_ACCESS_KEY`。不要把 `BOHR_ACCESS_KEY: $AK` 当作 HTTP header 传给公开网关；虽然 open-platform 代码层支持该别名，生产入口可能过滤带下划线的 header。`BOHR_ACCESS_KEY` 只作为本地环境变量名使用。

先解析当前身份：

```bash
curl -sS "$BASE/v1/ak/get" -H "Authorization: Bearer $AK"
```

返回中使用 `data.user_id` 作为后续 `userId`。

## 路由选择

| 动作 | 路由 | 说明 |
|---|---|---|
| 当前用户 | `GET /v1/ak/get` | 获取 `user_id` / `orgId` |
| 列目录 | `POST /v1/file/iterate` | 字段是 `prefix`，不是 `path` |
| 文件信息 | `GET /v1/file/stat/{path}` | 查询参数带 `projectId`、`userId` |
| 元数据 | `GET /v1/file/meta/{path}` | 查询参数带 `projectId`、`userId` |
| 下载 | `GET /v1/file/download/{path}` | 可能重定向，curl 用 `-L` |
| 建目录 | `POST /v1/file/mkdir` | body: `path`, `projectId`, `userId` |
| 移动/重命名 | `POST /v1/file/move` / `/mover` | body: `sourcePath`, `destinationPath` |
| 复制 | `POST /v1/file/copy` / `/copyr` | body: `sourcePath`, `destinationPath` |
| 删除 | `DELETE /v1/file/delete/{path}` / `/deleter/{path}` | 查询参数带 `projectId`、`userId` |
| 解压 | `POST /v1/file/decompress` | body: `filePath`, `dirName` |
| 上传凭证 | `GET /v2/file/upload/binary` | 推荐；返回 storage host + 上传凭证 |
| 直接上传 | `POST /v1/file/upload/binary` | 老接口；返回 307，curl 必须 `-L` |

`/v2/file/iterate` 和 `/v2/file/download` 仅用于 appJob 工作区：

```json
{"pathType": "appJob", "pathKey": 12345}
```

这里的 `pathKey` 是 appJob id。当前上游不支持 `pathType: "personal"` 或 `"share"`，会返回 `path type not found`。

## 列目录

列个人盘根目录：

```bash
curl -sS -X POST "$BASE/v1/file/iterate" \
  -H "Authorization: Bearer $AK" \
  -H "Content-Type: application/json" \
  -d '{"prefix":"personal/","projectId":0,"userId":27071,"dirSpace":"personal","maxObjects":100,"nextToken":""}'
```

列项目共享盘：

```bash
curl -sS -X POST "$BASE/v1/file/iterate" \
  -H "Authorization: Bearer $AK" \
  -H "Content-Type: application/json" \
  -d '{"prefix":"share/","projectId":154,"userId":27071,"dirSpace":"share","maxObjects":100,"nextToken":""}'
```

如果响应 `data.hasNext=true`，用返回的 `data.nextToken` 继续请求下一页。

## 读操作

查看路径是否存在：

```bash
curl -sS "$BASE/v1/file/stat/personal/input.txt?projectId=0&userId=27071" \
  -H "Authorization: Bearer $AK"
```

获取元数据：

```bash
curl -sS "$BASE/v1/file/meta/personal/input.txt?projectId=0&userId=27071" \
  -H "Authorization: Bearer $AK"
```

下载文件：

```bash
curl -L "$BASE/v1/file/download/personal/input.txt?projectId=0&userId=27071" \
  -H "Authorization: Bearer $AK" \
  -o input.txt
```

路径包含空格或特殊字符时，对 URL path 做百分号编码。

## 写操作

创建目录：

```bash
curl -sS -X POST "$BASE/v1/file/mkdir" \
  -H "Authorization: Bearer $AK" \
  -H "Content-Type: application/json" \
  -d '{"path":"personal/new-folder","projectId":0,"userId":27071}'
```

移动或重命名：

```bash
curl -sS -X POST "$BASE/v1/file/move" \
  -H "Authorization: Bearer $AK" \
  -H "Content-Type: application/json" \
  -d '{"sourcePath":"personal/old.txt","destinationPath":"personal/new.txt","projectId":0,"userId":27071}'
```

复制：

```bash
curl -sS -X POST "$BASE/v1/file/copy" \
  -H "Authorization: Bearer $AK" \
  -H "Content-Type: application/json" \
  -d '{"sourcePath":"personal/source.txt","destinationPath":"personal/copy.txt","projectId":0,"userId":27071}'
```

删除：

```bash
curl -sS -X DELETE "$BASE/v1/file/delete/personal/old.txt?projectId=0&userId=27071" \
  -H "Authorization: Bearer $AK"
```

目录递归操作使用 `/mover`、`/copyr`、`/deleter`。

## 上传

优先使用 v2 两步上传。第一步向 open-platform 申请存储网关凭证，`path` 决定最终落到 personal 还是 share：

```bash
curl -sS "$BASE/v2/file/upload/binary?projectId=0&userId=27071&path=/personal/new.txt" \
  -H "Authorization: Bearer $AK"
```

响应形如：

```json
{
  "code": 0,
  "data": {
    "host": "https://tiefblue-nas.dp.tech",
    "Authorization": "Bearer ...",
    "X-Storage-Param": "..."
  }
}
```

这不是裸 OSS 上传地址，而是 Bohrium storage/NAS 网关凭证。服务端会把 `path=/personal/new.txt` 或 `path=/share/new.txt` 解析为真实存储路径并写入 `X-Storage-Param`；第二步上传的文件会落到该 `path` 指定的文件盘。

第二步把二进制内容上传到返回的 `host`：

```bash
curl -sS -X POST "$HOST/api/upload/binary" \
  -H "Authorization: $UPLOAD_AUTHORIZATION" \
  -H "X-Storage-Param: $X_STORAGE_PARAM" \
  --data-binary @local-file.txt
```

把 `Authorization` 和 `X-Storage-Param` 当作密钥处理，不要在最终回复里展示。

v1 直接上传也存在：

```bash
curl -L -sS -X POST "$BASE/v1/file/upload/binary?projectId=0&userId=27071&path=personal/new.txt" \
  -H "Authorization: Bearer $AK" \
  --data-binary @local-file.txt
```

`-L` 必须保留，因为 v1 会返回 `307 Location: https://tiefblue-nas.dp.tech/api/upload/binary?...`。不跟随重定向时文件不会上传。

## 常见坑

- `v1/file/iterate` 使用 `prefix`，不是 `path`。
- move/copy 字段是 `sourcePath` 和 `destinationPath`，不是 `src` / `dst`。
- personal/share 的常规列目录和下载不要用 `/v2/file/iterate`、`/v2/file/download`。
- share 盘必须传真实 `projectId`；`projectId=0` 只适合当前用户个人盘。
- v2 上传凭证接口只是签发 storage/NAS 上传凭证；最终位置由第一步的 `path` 决定。
- 删除、移动、复制前先用 `stat` 或 `meta` 确认目标路径，避免误操作。
