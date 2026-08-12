---
name: codex-video-pipeline
description: Orchestrate a complete AI-assisted self-media video workflow from topic and evidence through script, motion direction, assets, narration, captions, HyperFrames rendering, quality control, covers, and a publish-ready package. Use when a user wants to make an AI knowledge or application video, turn notes or a rough idea into a finished video, continue an unfinished video project, configure a reusable video workflow, or run the included first-project example.
license: MIT
---

# Codex Video Pipeline

把视频任务当作完整产品交付：从输入、调研与脚本开始，直到成片、封面、发布文案和来源记录都进入产出目录。不要在生成脚本、分镜或第一版 MP4 后提前结束。

## 第一次使用

先运行环境检查：

~~~bash
python3 scripts/setup.py doctor --json
~~~

如果没有配置文件，继续运行：

~~~bash
python3 scripts/setup.py configure --recommended
~~~

然后读取 [references/first-run.md](references/first-run.md)，逐项帮助用户完成配置。遵守以下规则：

- Codex 用户缺少 HyperFrames 时，优先提示在插件页点击安装；不要先让普通用户执行包管理命令。
- 其他 AI Agent 缺少 Skill 时，给出上游 GitHub 地址，让该 Agent 使用自己的 Skill 安装机制处理。
- 只检测密钥是否存在，绝不读取、回显或写入项目文件。
- 安装系统工具、Python/Node 依赖或调用付费 API 前，先说明影响并获得用户确认。
- 配置完成后运行内置示例；不要只告诉用户“安装成功”。

## 需要的能力

- **HyperFrames**：默认渲染引擎。调用前完整读取其路由 Skill，并按它的工作流选择 `faceless-explainer`、`media-use` 等能力。
- **网页检索**：优先使用 Agent 自带网页搜索；需要多平台补充时可选装 Agent Reach。
- **图片**：Codex 默认使用原生 `imagegen`。其他 Agent 先使用自己的原生图片生成能力；没有时，在首次配置中提醒用户接入图像生成接口。
- **配音、转写、真实素材**：通过当前 Agent 已有能力或用户在配置中选择的提供方完成，不强绑某一家服务。
- **封面**：使用本流水线自带的封面系统，不要求用户再安装封面 Skill。先生成无字主视觉，再用 HyperFrames 做准确的中文排版和横竖版重排。

## 默认工作方式

用户未明确覆盖时：

- 语言：中文。
- 定位：AI 知识、真实应用与实践经验；优先真实任务、可见结果和可迁移方法。
- 画幅：16:9，1920×1080，30fps。
- 时长：按内容确定；短视频通常 80 秒以上，教程或深度主题可更长。
- 视觉：Vox 启发的原创编辑型信息视觉；暗色是成熟默认候选，不是硬性要求。配色必须舒适、统一，文字在最复杂背景上仍清晰。
- 背景：有相关实拍素材时铺满作为动态底层并加适量遮罩；没有时使用抽象运动、界面、纹理、粒子、图表或生成素材，避免大面积空白 PPT。
- 信息层：文字、线条、数据、标注用于强化理解，不是装饰。
- 进度条：默认贴近底部安全边缘，整片连续从 0 增长到 100%；冲突时统一放顶部，不按场景重置。
- 字幕：完整短句稳定显示。英文 Skill、产品名和带连字符标识符不得拆成前后两条。
- 封面：同时生成 1920×1080 横版和 1080×1920 竖版。两种比例分别排版，不用同一张图直接裁切。
- 产出：最终 MP4、横竖封面、发布文案、素材来源说明。

## 项目初始化

在用户工作目录创建项目：

~~~bash
python3 scripts/project.py init \
  --root videos \
  --title "中文视频标题" \
  --platform douyin \
  --ratio 16:9 \
  --duration 90
~~~

不要覆盖已有文件。项目契约见 [references/project-contract.md](references/project-contract.md)。

## 完整流程

### 1. 锁定输入

明确主题、目标观众、平台、时长、画幅、事实准确度、可用素材和完成标准。信息足够时直接推进；只有缺少会改变方向的关键信息才询问。

### 2. 选题与研究

区分明确主题、候选选择和自主选题三种入口。自主选题时先联网研究，再根据受众价值、证据强度、视觉潜力、差异化和制作成本评分。

把事实、来源、日期、适用范围、不确定性和自己的推断分开写入 `RESEARCH.md`。时效性内容必须联网，技术检索优先官方文档和原始资料。详细规则见 [references/research-and-script.md](references/research-and-script.md)。

### 3. 脚本与动态叙事图

先写口语化旁白，再为每段建立动态叙事图：本段要让观众理解什么、哪个对象发生什么变化、画面如何承接上一段、文字承担什么角色、需要什么素材。

不要从“第一页、第二页”开始设计。连续三段不能只靠标题卡、淡入或平移。让对象状态、尺度、路径、对比、遮罩、镜头层级或数据关系真实发生变化。

### 4. 素材

图片在 Codex 中默认使用原生 `imagegen` 生成，也可以使用有明确授权的用户素材。其他 Agent 有原生图片生成能力时直接使用，没有时先帮助用户接入图像生成接口。真实视频可使用用户素材或 Pexels；使用 Pexels 时运行 `scripts/pexels_video.py` 并保留 manifest、创作者、素材页和下载回执。

不得抓取来源不明的短视频充当素材。不要把“可下载”误当成“可商用”。

### 5. 旁白与字幕

使用配置中的 TTS、Agent 已有语音能力或用户提供的旁白。最终字幕必须基于**成片实际使用的最终旁白音频**完成声学对齐；按字数估时只能用于预览。

字幕提供方完成对齐后，运行：

~~~bash
python3 scripts/caption_gate.py record \
  --audio path/to/final-voice.wav \
  --captions path/to/captions.json \
  --provider "实际使用的声学转写器" \
  --output path/to/caption-receipt.json
~~~

正式渲染前运行 `caption_gate.py verify`。没有通过时禁止发布。字幕 JSON 格式见 [references/captions.md](references/captions.md)。

### 6. HyperFrames 制作

完整读取 HyperFrames 路由 Skill，根据视频类型进入对应工作流。AI 解释型视频通常使用 `faceless-explainer`，音频与字幕按 `media-use` 处理。

构建前确认：旁白时长、场景边界、动态叙事图、素材清单、字幕来源和发布画幅已经锁定。先 lint/check 和预览，再渲染，不要把“能播放”当作完成。

### 7. 质量检查

至少检查：

- 开头 3 秒是否清楚承诺观众收益；
- 信息能否只听旁白理解，同时画面又提供额外证据；
- 动态对象与转场是否连续，是否退化成 PPT；
- 文字在最亮、最暗和最复杂背景上是否可读；
- 字幕是否与真实语音同步、没有拆开完整英文名称；
- 进度条是否连续；
- 真实素材是否语义匹配且来源可追溯；
- BGM 是否盖住人声，结尾是否自然退出；
- 观众可见画面是否误带内部备注、占位文案或版权提醒。

质量门完整清单见 [references/quality-gates.md](references/quality-gates.md)。

### 8. 生成封面

完整读取 [references/cover-system.md](references/cover-system.md)。本流水线自带封面生成流程：

1. 从成片提炼一个简短主标题、一个可选副标题和一个能够解释选题的主视觉；
2. 在 Codex 中使用原生 `imagegen` 分别制作横版、竖版无文字主视觉底图；其他 Agent 使用其原生图片生成能力或已配置的图像生成接口；
3. 使用 HyperFrames、HTML/CSS 或 SVG 做确定性中文排版，保证文字逐字准确且不变形；
4. 横竖版分别重排标题和主视觉，不拉伸、不粗暴裁切；
5. 查看完整尺寸和移动端缩略图，不通过就修改后再打包。

不要让图片模型生成关键中文，也不要把封面退化成固定白框、大字报或普通 PPT 模板。

### 9. 发布包

把最终文件打包到项目自己的 `产出/`：

~~~bash
python3 scripts/package_outputs.py \
  --project videos/中文视频标题 \
  --title "中文视频标题" \
  --video path/to/final.mp4 \
  --cover-horizontal path/to/cover-16x9.png \
  --cover-vertical path/to/cover-9x16.png \
  --copy path/to/发布文案.md
~~~

最后运行：

~~~bash
python3 scripts/project.py verify --project videos/中文视频标题 --json
~~~

所有硬门通过后才能宣布完成。

## 内置示例

首次安装后读取 [examples/ai-meeting-notes/INPUT.md](examples/ai-meeting-notes/INPUT.md) 和 [references/example-run.md](references/example-run.md)，带用户完成一条“让 AI 把杂乱会议记录变成行动清单”的视频。

示例必须走完整流程并产生实际 MP4；它不是文档阅读练习。若某个外部提供方未配置，明确指出缺失项并帮助用户选择替代方案，不静默跳过。
