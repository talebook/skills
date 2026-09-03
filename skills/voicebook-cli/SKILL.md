---
name: voicebook-cli
version: "1.0.0"
display_name: "有声书创作助手"
display_name_en: "Voicebook CLI Assistant"
description: Voicebook CLI：安装或升级 voicebook-tool，将 EPUB/TXT 解析为可编辑的多角色 book.script，并生成、恢复或取消多音色、富有互动感的分章节 MP3 有声书任务。用于 CLI 安装、书籍处理、脚本审查、角色与音色设计和音频生成；Talebook 已发布音频的浏览与下载走 talebook Skill。
description_zh: "安装并操作 voicebook-tool，将 EPUB/TXT 处理为可编辑配音脚本，创作多角色、多音色、富有互动感的分章节有声书。"
description_en: "Install and operate voicebook-tool to turn EPUB/TXT books into editable voice scripts and engaging, multi-character, multi-voice chapter audiobooks."
compatibility: "需要 Python 3.11+、pip、ffmpeg 和 ffprobe；音频生成使用第三方云端 TTS。"
metadata:
  cliHelp: "voicebook-tool --help"
---

# 有声书创作助手

每次都从当前机器的实际状态出发，通过 `voicebook-tool` 的公开 CLI 完成任务。

## 1. 引导 CLI

运行 `voicebook-tool --version`。命令缺失、版本损坏，或用户要求安装/升级时，读取 [安装与命令参考](references/cli.md) 并从 PyPI 安装。生成音频前另行确认 `ffmpeg` 与 `ffprobe` 可用。

完成标准：`voicebook-tool --version` 和当前任务对应的 `--help` 均返回退出码 0；生成分支还要求两个 FFmpeg 命令可用。

## 2. 分流

| 意图 | 命令 | 继续读取 |
|---|---|---|
| EPUB/TXT 转可编辑脚本 | `inspect` | [脚本格式与审查](references/script-format.md) |
| 已审脚本转有声书 | `generate` | [生成、恢复与验收](references/workflows.md) |
| 原书直接转有声书 | `convert` | [生成、恢复与验收](references/workflows.md) |
| 查看音色 | `voices` | [安装与命令参考](references/cli.md) |
| 下载可选 CSI 模型 | `models download csi` | [安装与命令参考](references/cli.md) |

默认采用 `inspect` → 审查 `book.script` → `generate`。用户明确要求全自动或跳过审查时使用 `convert`。

完成标准：输入类型、命令、章节范围和引擎一一对应；实际参数以该子命令 `--help` 为准。

## 3. 保护目标

解析唯一输入文件，并为本书选择专用工作目录。已有 `.script` 视为人工产物：改用新文件名，或在用户确认后替换。已有音频目录只有在 manifest 与当前脚本、引擎相符时才作为恢复目标；其他情况使用新目录。

完成标准：输入存在且扩展名匹配；每个将被替换的文件都已获得明确授权，其余现有文件保持不变。

## 4. 披露云端边界

`inspect` 在本地处理文本。`generate` 和 `convert` 会把选中章节正文发送给所选 TTS：默认 `edgetts`，`--engine qwen3tts` 使用 qwen3ttsai.com。执行生成前说明引擎与章节范围；用户明确要求生成这本书的音频即构成授权。

下载 CSI 模型前说明目标目录及约 650 MB 下载量。`--force` 会重新发送并合成所有选中片段，只在用户选择全量重做时使用。引擎失败时保留原错误，由用户决定是否换引擎。

完成标准：实际外发内容限定为已授权书籍的已选章节，使用已告知的引擎。

## 5. 执行并观察

Agent 执行长任务时添加 `--progress-format jsonl`。需要取消能力时再传入一个启动时不存在的 `--cancel-file`；创建该文件即可在安全边界取消。恢复相同任务时使用 `--resume`。

退出码 `0` 表示命令结束，`1` 表示运行失败，`2` 表示参数错误，`3` 表示已取消。失败后先读取现有 manifest，再决定是否恢复；已完成片段由缓存复用。

完成标准：进程已经退出，并取得退出码、末端 JSONL 事件和现有 manifest 状态。

## 6. 验收

脚本任务验收 `.script` 的格式、章节、角色表、`[?]` 数量、解析警告以及封面/定位 sidecar。

音频任务只有同时满足以下条件才算完成：进程退出码为 `0`；`manifest.v2.json` 的 `format` 为 `voicebook-project`、`version` 为 `2`、`status` 为 `completed`；manifest 中每章的 MP3 与 timeline 均存在；成功章节数等于 `chapter_count`。交付时报告 CLI 版本、输入、脚本、引擎、章节范围、输出目录、章节数、总时长及失败/取消状态。
