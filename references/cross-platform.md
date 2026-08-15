# 跨平台运行

本 Skill 支持 macOS、Windows 和 Linux。Agent 必须先确认当前系统和实际可用命令，不能因为作者使用 macOS 就把 `python3`、Homebrew 或 Unix 路径直接套到 Windows。

## Python 解释器

需要 Python 3.10 或更高版本。

- macOS / Linux：优先尝试 `python3`，不可用时再尝试 `python`。
- Windows：优先使用当前 Codex 已提供的 `python.exe`；普通终端依次尝试 `py -3`、`python`。
- Python 脚本调用同仓库的另一个 Python 脚本时，必须使用 `sys.executable`，不得写死 `python3` 或 `python`。
- 命令、项目路径和文件名必须作为独立参数传递，不拼接成一条 Shell 字符串；这样才能正确处理空格、中文和 Windows 反斜杠。

下面的文档分别给出 macOS/Linux 与 Windows 命令。Agent 只执行与当前系统匹配的一组。

## FFmpeg

`doctor` 只检查当前进程的 `PATH`。安装完成不代表当前 Agent 已经能发现它。

- macOS 可在用户确认后使用 Homebrew 安装。
- Windows 可在用户确认后使用 `winget install Gyan.FFmpeg`，或使用用户认可的其他发行版。
- Linux 使用当前发行版的包管理器。

安装后重新打开终端或刷新 Agent，再分别确认：

~~~text
ffmpeg -version
ffprobe -version
~~~

Windows 若刚刚解压 FFmpeg，可以先把实际 `bin` 目录加入当前 PowerShell 会话的 `$env:Path` 做验证；不要假设下载目录或版本号固定，也不要覆盖用户已有的系统 PATH。

## Node.js 与 HyperFrames

需要 Node.js LTS，并确保 `node`、`npm` 和 `npx` 都能从当前进程找到。Codex 用户优先从插件页安装 HyperFrames；其他 Agent 按自己的 Skill 安装机制处理 HyperFrames GitHub 仓库。

## 配置路径

- Windows 默认保存到 `%APPDATA%\codex-video-pipeline\config.json`。
- macOS / Linux 默认保存到 `$XDG_CONFIG_HOME/codex-video-pipeline/config.json`，未设置时使用 `~/.config/codex-video-pipeline/config.json`。
- 可以通过 `CODEX_VIDEO_PIPELINE_CONFIG` 明确覆盖位置。
- 已在 Windows 旧版位置 `~/.config/codex-video-pipeline/config.json` 创建配置的用户会继续沿用旧文件，不强制迁移。

配置文件只保存提供方选择，不保存 API Key、Token 或 Cookie。

## 环境变量

macOS / Linux 当前终端：

~~~bash
export PEXELS_API_KEY="仅在当前终端使用的值"
~~~

Windows PowerShell 当前会话：

~~~powershell
$env:PEXELS_API_KEY = "仅在当前会话使用的值"
~~~

不要把真实密钥提交到仓库。需要长期保存时使用操作系统安全存储或用户已有的密钥管理方式。

## 文件名与项目移动

- 项目初始化器会把 `<>:"/\|?*`、控制字符、结尾空格/句点和 `CON`、`NUL` 等 Windows 保留名称转换为安全文件名。
- 最终目录仍使用中文标题，但 `project.json` 中的标题与实际目录名必须一致。
- 新生成的字幕凭据优先保存相对路径；整个项目移动到另一台电脑后，只要音频和字幕仍在项目内，验证仍然有效。
- 旧版绝对路径字幕凭据继续支持，但移动项目后需要重新生成凭据。

## 最小验证

在每个平台至少运行：

1. `setup.py doctor --json`；
2. `setup.py configure --recommended`，使用临时配置路径；
3. `example.py`，项目根目录同时包含空格和中文；
4. `python -m unittest discover -s tests -v`（解释器命令按当前系统替换）；
5. 有 FFmpeg 时运行完整音视频质量门测试。
