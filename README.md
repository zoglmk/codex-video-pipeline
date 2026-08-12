# Codex Video Pipeline

一个面向普通创作者的 AI 视频生产流水线：把一个主题或一份原始资料，推进为可发布的 MP4、横竖封面、发布文案与来源记录。

它把多个 AI 能力串成一条完整流程：渲染交给 HyperFrames，图片默认使用 Codex 原生 `imagegen`，检索、配音和声学字幕使用当前 Agent 已有的能力或自选提供方。

## 它能做什么

- 选题与权威资料核验
- 口语脚本与动态叙事图
- 图片、真实视频和来源追溯
- 配音、基于真实语音的字幕对齐
- HyperFrames 动效视频制作
- 自带横竖版封面生成系统
- 反 PPT、可读性、音视频和版权检查
- 最终 MP4、横竖封面与发布文案打包
- 首次配置向导与一条完整练习项目

## 安装

### 方法一：交给 AI Agent（推荐）

把本仓库的 GitHub 链接发给你的 AI Agent：

> 请安装这个 Skill，并使用 `$codex-video-pipeline` 帮我完成首次配置。每一步告诉我缺什么、为什么需要、怎样安全配置；配置完成后，用内置示例带我走完一次从输入到最终 MP4 和发布包的全过程。

Agent 应使用自身支持的 Skill 安装机制处理这个 GitHub 仓库。无需先研究包管理命令。

### 方法二：手动安装

1. 下载或克隆本仓库。
2. 把整个仓库放入你的 Agent 能识别的 Skill 目录，目录名保持 `codex-video-pipeline`。
3. 在对话中调用 `$codex-video-pipeline`，让 Agent 执行首次配置。

不同 Agent 的 Skill 目录和安装方式不同，以对应产品文档为准。

## HyperFrames

Codex 用户直接在插件页安装 **HyperFrames**。其他 Agent 可以把 [HyperFrames GitHub 仓库](https://github.com/heygen-com/hyperframes) 交给 Agent 安装。

## 首次配置

Agent 会依次完成：

1. 运行只读环境检查，确认基本环境、HyperFrames 和配置状态。
2. 创建不含密钥的提供方配置。
3. Codex 默认使用原生 `imagegen`；其他 Agent 没有原生图片生成能力时，再引导接入图像生成接口。同时选择配音、声学字幕、真实视频与音乐方案。
4. 缺少外部能力时逐项解释，不自动安装系统软件或调用付费 API。
5. 运行内置示例，最终交付实际 MP4、两张封面和发布文案。

你也可以在仓库目录运行：

~~~bash
python3 scripts/setup.py doctor --json
python3 scripts/setup.py guide
python3 scripts/setup.py configure --recommended
~~~

配置文件只记录提供方选择，默认位于 `~/.config/codex-video-pipeline/config.json`；API Key、Token 和 Cookie 不会写入项目或仓库。

## 内置示例

示例主题是“让 AI 把杂乱会议记录变成行动清单”。它会检验整个链路，而不是只生成一个脚本：

~~~bash
python3 scripts/example.py --root videos
~~~

然后把终端返回的项目路径交给 Agent：

> 使用 `$codex-video-pipeline` 继续这个项目，走完研究、脚本、动态叙事图、配音、真实语音字幕、HyperFrames 制作、封面、发布文案和验收，直到 `产出/` 中出现可发布文件。

完整说明见 [首次运行指南](references/first-run.md)。

## 自带封面系统

流水线会从成片中提炼封面标题和主视觉，先分别生成横版、竖版无字底图，再用 HyperFrames 做准确的中文排版。两种比例分别重排，不会把一张图直接拉伸或裁切。

输出前还会检查移动端缩略图，确保标题看得清、主视觉能解释选题、画面没有乱码和无关装饰。使用方法见 [封面系统](references/cover-system.md)。

## 安全与版权

- 不把 API Key、Token、Cookie 或登录凭据写入项目。
- 不把“网络上能下载”当作“可以使用”。
- 默认不抓取其他创作者的短视频作为素材。
- Pexels 素材也保留创作者、素材页、许可证和文件指纹。
- 最终字幕必须来自成片实际使用的旁白音频；字数估时只能预览。
- 任何系统安装、付费 API 或大规模下载，都应先取得用户确认。

## 参考

需要补充多平台检索时，可以使用 [Agent Reach](https://github.com/Panniantong/Agent-Reach)。连续运动和反 PPT 检查的部分参考了 [rn-motion-director](https://github.com/Pluviobyte/rnskill/tree/main/skills/rn-motion-director)。

## 许可证

本仓库使用 [MIT License](LICENSE)。
