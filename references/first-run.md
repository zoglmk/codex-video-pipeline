# 第一次使用

目标不是把依赖全部装满，而是让用户用自己现有的 Agent 完成一条真实视频。每一步先解释“为什么需要”，再告诉用户怎么做。

开始前完整读取 [cross-platform.md](cross-platform.md)，先确认当前系统和实际可用的 Python 3.10+ 解释器。Windows 不得照抄 macOS 的 `python3`、Homebrew 或 Unix 路径。

## 1. 安装公开 Skill

让用户把本仓库 GitHub 链接交给自己的 AI Agent，并说：

> 请安装这个 Skill。安装后使用 `$codex-video-pipeline` 执行首次配置，不要替我安装系统软件或调用付费 API；发现缺失项时先解释并征得确认。最后用内置示例生成一条实际视频。

手动用户可以下载仓库并放入 Agent 支持的 Skill 目录。

## 2. 安装渲染插件

- Codex：在插件页搜索并安装 HyperFrames。
- 其他 Agent：把 <https://github.com/heygen-com/hyperframes> 交给 Agent，让它按自己的 Skill 安装机制处理。

安装后重新启动或刷新 Agent，确保它能发现 `hyperframes`。

## 3. 只读检查

macOS / Linux 运行：

~~~bash
python3 scripts/setup.py doctor --json
~~~

Windows PowerShell 运行：

~~~powershell
python scripts/setup.py doctor --json
~~~

Windows 没有 `python` 时尝试 `py -3`。已经由某个 Python 进程启动后，Skill 内部子脚本会自动复用当前解释器。

按 `actions` 逐项处理。不要为了让报告变绿就自动安装全部可选项：

- HyperFrames 是默认成片链路的必需项。
- Agent Reach、Pexels、豆包和特定 Whisper 实现都是可选项。
- Python 3.10 以上用于公开脚本。

## 4. 创建配置

macOS / Linux 运行：

~~~bash
python3 scripts/setup.py configure --recommended
~~~

Windows PowerShell 运行：

~~~powershell
python scripts/setup.py configure --recommended
~~~

这一步只写提供方选择，不写密钥。若用户已有明确方案，可改用：

~~~bash
python3 scripts/setup.py configure \
  --tts doubao \
  --captions mlx-whisper \
  --footage pexels-optional
~~~

Windows 使用同样的参数，把开头替换为 `python` 或 `py -3`；PowerShell 可以把命令写在一行，避免照抄 Bash 的反斜杠续行。

## 5. 逐项选择外部能力

### 图片

Codex 默认直接使用原生 `imagegen`，不需要额外配置。

其他 Agent 先检查是否有原生图片生成能力：有就直接使用；没有时，提醒用户接入一个图像生成接口，并说明需要准备的 API Key、调用地址和模型名称。密钥只保存到环境或系统安全存储，不写进项目。

### 旁白

按以下顺序选择：

1. Agent 已有且用户有权使用的语音能力；
2. 用户已经配置的 TTS；
3. 用户提供最终旁白文件。

不要在公开项目中保存语音服务密钥。使用克隆声音前确认声音所有者授权。

### 字幕

字幕必须从最终旁白音频做声学转写或对齐。可以使用 Agent 已有 ASR、MLX Whisper、Whisper CLI 或其他能输出时间戳 JSON 的工具。按字数估算只能预览。

### 真实视频

需要时才配置 Pexels。用户在 Pexels 申请 API Key 后，把它放到环境或系统安全存储：

macOS / Linux 当前终端：

~~~bash
export PEXELS_API_KEY="仅在当前终端使用的值"
~~~

Windows PowerShell 当前会话：

~~~powershell
$env:PEXELS_API_KEY = "仅在当前会话使用的值"
~~~

不要把真实值写入 `.env` 后提交到 GitHub。没有真实视频不影响内置示例完成。

### 音乐

公开仓库不附带默认 BGM。使用用户自有或有明确授权的音乐，也可以先制作无 BGM 版本。不要从其他工程复制一首“能播放但授权不明”的音乐。

### 封面

不需要额外安装封面 Skill。读取 [cover-system.md](cover-system.md)，Codex 使用原生 `imagegen` 生成无字主视觉；其他 Agent 使用原生图片能力或已配置的图像生成接口。再用 HyperFrames 完成准确的中文排版和横竖版重排。

## 6. 运行示例

macOS / Linux 使用 `python3 scripts/example.py --root videos`；Windows PowerShell 使用 `python scripts/example.py --root videos`，没有 `python` 时使用 `py -3`。

读取 [example-run.md](example-run.md)，继续到实际成片。首次示例完成后再让用户替换为自己的主题。

## 7. 首次完成标准

- `产出/` 中有实际可播放 MP4、横版封面、竖版封面和发布文案；
- 最终视频有音频轨；
- 字幕凭据通过 `caption_gate.py verify`；
- 项目通过 `project.py verify`；
- 用户知道怎样替换主题、旁白、素材提供方和平台规格；
- 用户没有把密钥或来源不明素材带入项目。
