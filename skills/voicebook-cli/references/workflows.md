# 生成、恢复与验收

## 两阶段制作

1. 用 `inspect` 生成新 `.script`；部分书籍可在此处传入 `--chapters`。
2. 按 [script-format.md](script-format.md) 审查角色、章节、解析警告和 `[?]`；人工修订后保留这份脚本。
3. 用 `generate --chapters 1` 生成试听章，确认引擎、角色与音色。
4. 试听通过后扩大章节范围。Agent 执行时启用 JSONL 进度，并为任务分配唯一 cancel-file 和专用输出目录。
5. 按下文的 manifest 规则验收。

示例：

```bash
voicebook-tool inspect <novel.epub> -o <work-dir>/novel.script --chapters 1-3
voicebook-tool generate <work-dir>/novel.script -o <work-dir>/audio \
  --engine edgetts --chapters 1 --progress-format jsonl \
  --cancel-file <unique-cancel-path>
```

试听通过后，省略 `--chapters` 或改成期望范围继续生成。默认片段缓存会复用第一章中内容、引擎、音色与语速均相同的片段。

## 一键制作

用户明确表示无需先审查脚本时使用 `convert`。为它选择不含人工 `book.script` 的输出目录：

```bash
voicebook-tool convert <novel.epub> -o <new-output-dir> \
  --engine edgetts --progress-format jsonl \
  --cancel-file <unique-cancel-path>
```

`convert --chapters 1,3,8-12` 在解析阶段按原书章号筛选，并把这些原始章号写入 `book.script`；生成阶段直接处理脚本中的全部章节，不再重复筛选。

## 恢复与取消

- 恢复前读取 manifest，以书名、`script_sha256`、引擎和选中章节确认任务身份。
- 相同脚本、引擎和输出目录使用 `--resume`；已完成且 SHA-256 匹配的章节会跳过。
- 普通重跑会复用未变化的片段缓存；`--force` 专用于用户要求的全量重做。
- 取消时创建命令启动时传入的 cancel file。命令在片段/章节安全边界响应，退出码为 `3`，manifest 变为 `cancelled`。
- 保留 manifest、缓存和已完成 MP3 以支持恢复。全量重做优先选择新输出目录；用户选择复用原目录时使用 `--force`。

## 失败处理

- `缺少系统命令 ffmpeg/ffprobe`：暂停生成并报告缺少的依赖；`inspect` 仍可独立执行。
- EPUB/TXT 不可读或章节越界：报告输入和合法范围，等待用户修正目标。
- 脚本格式错误：定位到 frontmatter、角色表或正文标签，按格式约束做最小修复。
- TTS 首个探测片段失败：报告引擎与服务端原因，由用户选择重试或换引擎。
- 中途失败：manifest 状态为 `failed`，保留已完成章节；核对后由用户决定 `--resume`。
- Qwen 返回 429/5xx：客户端内部最多尝试三次；最终失败后报告服务端错误和可恢复状态。

## Manifest 验收

完成态必须同时满足：

1. 进程退出码为 `0`。
2. `manifest.v2.json` 的 `format` 为 `voicebook-project`、`version` 为 `2`、`status` 为 `completed`。
3. manifest 中每个成功章节对应的 MP3 和 timeline 均存在。
4. 成功章节数等于 `chapter_count`。

失败或取消时，从 manifest 报告状态、已完成章节和下一条安全恢复命令。
