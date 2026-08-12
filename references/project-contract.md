# 项目契约

项目由 `scripts/project.py init` 创建：

~~~text
videos/中文视频标题/
├── project.json
├── INPUT.md
├── RESEARCH.md
├── SCRIPT.md
├── STORYBOARD.md
├── SOURCES.md
├── asset-manifest.json
├── assets/
│   ├── images/
│   └── real-video/
├── audio/
│   ├── voice/
│   └── music/
├── captions/
│   └── caption-receipt.json
├── renders/
├── qc/
└── 产出/
    ├── 中文视频标题.mp4
    ├── 封面-1920×1080.png
    ├── 封面-1080×1920.png
    └── 发布文案.md
~~~

## 原则

- 顶层项目名与最终 MP4 主文件名一致，方便长期归档。
- `产出/` 只放能直接上传或复制的四个文件。
- 素材、声音、渲染中间件、快照和报告留在过程目录。
- 不覆盖旧项目或旧凭据；重制版使用新的项目名。
- 删除缓存或过程文件前先列出目标、预计空间和可恢复性，并获得用户明确确认。

## project.json

`status` 可按进度更新为：

1. `initialized`
2. `researched`
3. `scripted`
4. `assets-ready`
5. `audio-aligned`
6. `rendered`
7. `packaged`
8. `verified`

不要仅修改状态掩盖缺失文件；最终以验证脚本为准。
