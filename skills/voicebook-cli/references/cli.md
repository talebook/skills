# 安装与命令参考

## 从空白环境安装

`voicebook-tool` 发布在 PyPI，包名与命令名相同。它要求 Python 3.11+；MP3 生成还依赖系统命令 `ffmpeg` 和 `ffprobe`。

先确定 Python 启动器及 pip：

```bash
python3 --version
python3 -m pip --version
```

Windows 可使用 `py -3.11` 替代 `python3`。版本低于 3.11 时，先安装合适的 Python，再用同一个解释器执行后续 `-m pip` 命令。

再检查当前解释器中是否已经安装，以及命令是否在 `PATH`：

```bash
python3 -m pip show voicebook-tool
voicebook-tool --version
```

`pip show` 有结果而命令不可用，通常表示脚本目录尚未进入 `PATH`；沿用下文的用户级脚本目录处理即可。

已激活虚拟环境时，安装到当前环境：

```bash
python3 -m pip install --upgrade voicebook-tool
```

没有虚拟环境时，可安装到当前用户：

```bash
python3 -m pip install --user --upgrade voicebook-tool
python3 -m site --user-base
```

若命令安装成功但 shell 找不到它，将第二条命令返回目录下的 `bin`（Unix/macOS）或 `Scripts`（Windows）加入 `PATH`，然后开启新 shell。当前任务也可以直接调用该目录中的 `voicebook-tool` 可执行文件。

若 pip 报告 `No matching distribution found`，依次核对两个条件：

```bash
python3 --version
python3 -m pip config list
```

- Python 低于 3.11：换用 3.11+ 解释器。
- Python 已满足要求、当前索引未收录该包：遵守组织的软件源策略；允许访问官方 PyPI 时显式指定索引后重试：

  ```bash
  python3 -m pip install --index-url https://pypi.org/simple --upgrade voicebook-tool
  ```

强制使用镜像的环境应报告“镜像未同步 voicebook-tool”，由用户或管理员决定同步包或改用允许的软件源。用户级安装时在重试命令中保留 `--user`。

遇到 `externally-managed-environment`，在用户选择的目录创建专用环境：

```bash
python3 -m venv <tool-environment>
<tool-environment>/bin/python -m pip install --upgrade voicebook-tool
<tool-environment>/bin/voicebook-tool --version
```

Windows 对应的可执行文件位于 `<tool-environment>\Scripts\`。如果用户偏好隔离式 CLI 管理且机器已安装相应工具，也可选择 `pipx install voicebook-tool` 或 `uv tool install voicebook-tool`；默认方案仍是 `python -m pip`。

验证安装：

```bash
voicebook-tool --version
voicebook-tool --help
voicebook-tool inspect --help
voicebook-tool generate --help
```

升级时沿用安装所用的 Python、软件源和作用域。

## FFmpeg

先检查：

```bash
ffmpeg -version
ffprobe -version
```

两者通常由同一个 FFmpeg 系统包提供。根据系统选择包管理器；涉及 `sudo` 或系统范围写入时先展示命令并取得授权：

```bash
# macOS（Homebrew）
brew install ffmpeg

# Debian / Ubuntu
sudo apt-get update
sudo apt-get install ffmpeg

# Windows（winget）
winget install Gyan.FFmpeg
```

## 可选 CSI 模型

CSI 说话人识别需要额外 Python 依赖。使用与主程序相同的环境安装 extra：

```bash
python3 -m pip install --upgrade "voicebook-tool[csi]"
voicebook-tool models download csi -o <model-dir>
```

用户级安装时在 pip 命令中保持 `--user`。模型下载约 650 MB，会访问 Hugging Face；先确认目标目录和下载量。

## 命令面

| 命令 | 输入 | 主要输出 | 关键选项 |
|---|---|---|---|
| `inspect` | `.epub` / `.txt` | `.script`、可选封面、`.locators.json` | `--chapters`、`--csi-model` |
| `generate` | voicebook-script v1 | 分章 MP3、manifest、timelines、缓存 | `--engine`、`--chapters`、`--resume`、`--force` |
| `convert` | `.epub` / `.txt` | `book.script` 及全部音频产物 | 同 `generate`，另有 `--csi-model` |
| `voices` | 无 | 音色目录 | `--engine`、`--format`、`--include-paths` |
| `models download csi` | 模型名 | 本地模型目录 | `-o/--output` |

每次安装或升级后以对应子命令的 `--help` 为参数事实来源。

### `inspect`

```bash
voicebook-tool inspect <book.epub-or-txt> -o <book.script> \
  [--chapters 1,3,8-12] [--csi-model <dir>] \
  [--progress-format human|jsonl] [--cancel-file <path>]
```

它读取 EPUB spine、导航标题、元数据和封面，识别章节、角色及对白归属，并原子写入 voicebook-script v1。存在源定位时写 `<book.script>.locators.json`；存在封面时写同 stem 的封面文件。`--chapters` 按原书章节编号筛选。

### `generate`

```bash
voicebook-tool generate <book.script> -o <output-dir> \
  [--engine edgetts|qwen3tts] [--chapters 1,3,8-12] \
  [--resume] [--force] [--progress-format human|jsonl] \
  [--cancel-file <path>]
```

默认引擎是 `edgetts`。默认复用内容、引擎、音色和语速均未变化的片段缓存；`--resume` 还会复用 manifest 中校验通过的完整章节；`--force` 重新合成所有选中片段。

输出目录包含 `manifest.v2.json`、`chapters/NNNN.mp3`、`timelines/NNNN.json` 与 `.voicebook/` 缓存。每章 MP3 带 title、album、artist、track 元数据；存在封面时嵌入封面。

### `convert`

```bash
voicebook-tool convert <book.epub-or-txt> -o <output-dir> \
  [--engine edgetts|qwen3tts] [--chapters 1,3,8-12] \
  [--resume] [--force] [--csi-model <dir>] \
  [--progress-format human|jsonl] [--cancel-file <path>]
```

它先把选中章节写为 `<output-dir>/book.script`，再生成音频。该脚本是完整产物，应与音频一起交付。

### `voices`

```bash
voicebook-tool voices --engine edgetts|qwen3tts|all --format human|json [--include-paths]
```

`preview_available` 表示安装包内是否有该音色的试听资产。`--include-paths` 仅在需要打开本地试听文件时使用。

## 机器进度与退出码

`--progress-format jsonl` 输出 schema 为 `voicebook-progress.v1` 的逐行 JSON。事件包括 `phase_started`、`chapter_started`、`segment_completed`、`chapter_completed`、`completed`、`failed`、`cancelled`。

| 退出码 | 含义 |
|---:|---|
| `0` | 命令结束；继续核验产物。 |
| `1` | 输入、依赖、TTS、FFmpeg 或其他运行错误。 |
| `2` | 参数错误。 |
| `3` | cancel file 已在安全边界取消任务。 |

生成异常或取消时，manifest 保留状态和已完成章节；恢复前以它为依据。
