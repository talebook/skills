# Talebook & Voicebook Skills

面向 AI 编程与自动化 Agent 的 Talebook / Voicebook Skill 集合。

## Skills

- `talebook`：通过 Talebook HTTP API 安全地搜索、浏览、上传、下载和管理书籍，操作有声书与远程书库，执行管理员任务，以及通过 Docker Compose 部署 Talebook。
- `voicebook-cli`（有声书创作助手）：安装并操作 `voicebook-tool`，把 EPUB/TXT 处理成可编辑的多角色配音脚本，并生成多音色、富有互动感的分章节 MP3 有声书。

## 环境要求

- `talebook`：Python 3（仅使用标准库）以及一个可访问的 Talebook 实例。
- `voicebook-cli`：Python 3.11+、`pip`、`ffmpeg` 和 `ffprobe`；运行时从 PyPI 安装 `voicebook-tool`。

## 安装

列出仓库中的 Skill：

```bash
npx skills add talebook/skills --list
```

安装 Talebook Skill：

```bash
npx skills add talebook/skills --skill talebook
```

安装 Voicebook CLI Skill：

```bash
npx skills add talebook/skills --skill voicebook-cli
```

也可以直接从本地仓库验证：

```bash
npx skills add . --list
```

## Talebook 配置

通过环境变量提供站点和登录信息，避免密码进入命令历史。只读浏览可以不配置账号，以 guest 身份访问：

```bash
export TALEBOOK_URL="https://books.example.com"
export TALEBOOK_USERNAME="your-username"
export TALEBOOK_PASSWORD="your-password"
```

## 使用

安装后直接用自然语言提出任务，Skill 会自动触发：

```text
帮我在书库里搜一下《三体》，把找到的那本加入收藏。

把 novel.epub 的前 3 章生成配音脚本，检查完角色后再生成有声书。
```

在 Claude Code 中也可以用 `/talebook` 或 `/voicebook-cli` 显式调用。

Talebook 写操作前会先解析出唯一目标；发送到设备、管理员写入、删除和批量操作会先展示影响并请求确认，执行后再查询状态核验。

Voicebook 的 EPUB/TXT 脚本解析在本地完成；`generate` 和 `convert` 会把选中章节正文发送到指定的 EdgeTTS 或 Qwen3TTS 云端服务。

## 开发

`skills/talebook/evals/` 下有 6 条评测用例和一个纯标准库的假 Talebook 实例，用于在没有真实服务器的情况下验证 Skill 的行为（ID 解析、确认门禁、异步任务汇报、凭据脱敏等）。运行方式见 [evals/README.md](skills/talebook/evals/README.md) 。

`skills/voicebook-cli/evals/` 覆盖本地安装、EPUB 脚本生成、断点续跑和一键生成四类行为。

## 许可证

[BSD 2-Clause License](LICENSE)
