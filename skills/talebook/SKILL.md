---
name: talebook
version: "1.0.0"
display_name: "Talebook 操作助手"
display_name_en: "Talebook Assistant"
description: 通过 Talebook 原有 HTTP API 操作自托管的 Talebook 电子书库（Calibre + Vue）。覆盖搜索、浏览、上传、下载、收藏书籍，管理书架、阅读状态与 Kindle/推送设备，列出、查看或下载已发布有声书，使用 Legado 网络书源与远程书库，执行用户、书源、OPDS、设置、日志等管理员操作，以及用 Docker Compose 部署或升级实例。只要用户提到 Talebook、自己的书库或藏书站点、TALEBOOK_URL，或要在自托管书库里找书、传书、下书、推送到 Kindle、管理书源，就使用本技能，即使没有点名 Talebook。不适用于 Calibre 桌面端或其他第三方书库软件。
description_zh: "通过 Talebook HTTP API 安全地浏览、操作、管理和部署自托管电子书库。"
description_en: "Safely browse, operate, administer, and deploy self-hosted Talebook libraries through the Talebook HTTP API."
---

# Talebook 操作助手

把每次请求走成一条受控链路：预检、风险门禁、执行、核验、交付。不要把“HTTP 请求已发送”当作完成。

## 1. 预检

1. 获取 Talebook 站点地址。优先使用用户本次提供的地址，其次使用 `TALEBOOK_URL`。地址没有 scheme 时按 HTTPS 处理。
2. 若用户提供账号，使用成对的 `TALEBOOK_USERNAME` 与 `TALEBOOK_PASSWORD`；两者均缺失时保持 guest。优先通过环境变量传递密码，避免命令历史和进程列表暴露凭据。
3. 下方“常用只读命令”能直接满足请求时不必再读参考文档。其余情况在调用前读取 [references/api.md](references/api.md)，选择已有命令并确认参数、权限和风险级别；多步书库、元数据、远程书源或管理员任务还要读取 [references/workflows.md](references/workflows.md)。
4. 首次连接或需要身份信息时执行：

   ```bash
   python3 scripts/talebook-cli.py me status
   ```

预检完成标准：已确定目标站点、当前身份、服务端公开权限，以及唯一匹配用户意图的 CLI 命令。

常用只读命令（其余命令查 api.md，参数以 `--help` 为准）：

| 意图 | 命令 |
|---|---|
| 站点、身份与权限 | `me status` |
| 按书名搜索 | `books search --name 三体` |
| 书籍详情与可用格式 | `books show --id 123` |
| 浏览列表 | `books list --view library`（另有 recent、hot、favorites、shelf、reading） |
| 已发布有声书 | `audios list [--keyword 三体]` |

## 2. 通过风险门禁

- 只读操作直接执行。
- 用户明确要求的上传、收藏、书架和阅读状态属于常规写入，可直接执行。
- 发送到邮箱或设备、管理员写入、删除和批量操作先展示目标、数量和影响，得到用户确认后才添加 `--confirmed`。
- CLI 报告需要确认时，原样展示预览；不要代替用户确认。
- 写入前先通过搜索和详情解析唯一书籍 ID，或通过列表解析唯一用户、书源与任务标识；不要猜测 ID。
- 服务器权限是最终边界。CLI 的身份检查通过不代表可以绕过 Talebook 返回的权限错误。

门禁完成标准：只读或常规写入已获用户原始请求授权；其他操作已有本次会话中的明确确认，且命令目标与预览一致。

## 3. 执行

所有操作走 skill 目录下的单体 CLI（Python 3，仅标准库，无需安装依赖）：

```bash
python3 scripts/talebook-cli.py [--site URL] [--user USER] [--password PASSWORD] <命令...>
```

本文中的 `scripts/talebook-cli.py` 是相对本 SKILL.md 所在目录的路径。当前工作目录通常不是 skill 目录，执行时请补成该目录下的绝对路径。站点与凭据优先通过 `TALEBOOK_URL`、`TALEBOOK_USERNAME`、`TALEBOOK_PASSWORD` 传入，省去每条命令重复 `--site`，也避免密码出现在命令历史里。

优先使用 CLI 的结构化命令，不自行拼装未记录的 API 请求。CLI 返回非零退出码时，读取 JSON 错误并处理：

- `auth.required`、`permission.not_admin`：说明当前身份和所需权限。
- `not_invited`、`captcha.invalid`、第三方登录或首次初始化：切换浏览器完成交互，再重新运行 `me status`。
- 连接、TLS 或超时错误：检查地址、scheme、端口和实例状态；保留 HTTPS 校验。
- Talebook 业务错误：展示服务端 `err` 与 `msg`，不要把失败包装成成功。
- 身份预检返回业务错误时立即停止，不继续调用受保护接口。
- 写操作失败时不要自动重试；先报告服务端错误并重新确认目标与当前状态。
- 组合编辑返回 `partial: true` 时，明确报告已经完成和失败的步骤；核验现状后再决定是否继续，不重放已完成步骤。

执行完成标准：CLI 返回零退出码，或浏览器中的目标操作显示成功；异步任务已取得任务标识或可查询状态。

## 4. 核验

写入后使用相应只读命令重新查询目标。例如收藏后读取收藏列表，管理员设置后再次读取设置，远程保存后查询保存状态。外发任务至少核对服务端已接受的目标、书籍和格式。有声书下载以流式临时文件写入，整本成功后才发布目标目录；完成后核对输出目录、章节数量、排序文件名和总字节数，不要把只有部分章节的目录报告为完成。

核验完成标准：重新查询的状态与用户请求一致；异步任务则明确报告已启动、当前进度入口和尚未完成的部分。

## 5. 更新提醒

CLI 成功输出可能包含 `_notice.update`。看到该字段时：

1. 先完成并核验用户当前请求，不要让更新提醒中断任务。
2. 除非用户正在询问版本或更新，否则只在结果末尾简短说明当前版本、最新版本和发布页；不要原样复制整段 `_notice`。
3. 不要自动升级实例。用户要求更新时，先确认当前部署方式；Docker Compose 实例读取 [references/docker-compose.md](references/docker-compose.md)，在正确的部署目录中推导更新步骤并获得相应授权。
4. 需要稳定 JSON 输出或不希望产生额外检查请求时，在命令前设置 `TALEBOOK_NO_UPDATE_NOTIFIER=1`。

管理员可用 `admin settings check-update` 读取服务端缓存，或在用户明确要求实时检查时添加 `--refresh`。普通命令的提醒只读缓存，不会主动访问 GitHub。

## 6. 部署分支

用户要求部署新实例时，不调用 CLI。读取 [references/docker-compose.md](references/docker-compose.md)，收集部署目录、端口和数据目录，生成 Compose 配置并执行文档中的启动与可访问性验证。首次初始化转到浏览器完成。

部署完成标准：`docker compose up -d` 成功，Talebook HTTP 入口可访问，并向用户提供明确地址和持久化数据目录。首次初始化完成后再运行 `me status` 验证连通性与身份。

## 7. 交付结果

报告实际执行的命令、目标站点、身份、Talebook 响应和核验结果。摘要展示有用字段并保留后续操作需要的 book、task、source 等 ID，不倾倒整段原始 JSON。CLI 已在 `admin settings show` 的输出边界递归隐藏密码、secret、token、API key、访问码及 URL 凭据；不得尝试恢复或绕过脱敏。隐藏登录密码与 Authorization；下载或日志文件报告本地路径，不把二进制内容写入对话。
