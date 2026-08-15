#!/usr/bin/env python3
"""把已验收文件复制到项目的中文产出目录。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import uuid
from pathlib import Path

from runtime import safe_title



def source(path: Path, label: str) -> Path:
    value = path.expanduser().resolve()
    if not value.is_file() or value.stat().st_size == 0:
        raise SystemExit(f"{label}不存在或为空：{value}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--cover-horizontal", type=Path, required=True)
    parser.add_argument("--cover-vertical", type=Path, required=True)
    parser.add_argument("--copy", type=Path, required=True, dest="publish_copy")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    try:
        title = safe_title(args.title)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    project = args.project.expanduser().resolve()
    manifest = project / "project.json"
    if not manifest.is_file():
        raise SystemExit(f"不是有效项目：{project}")
    project_title = str(json.loads(manifest.read_text(encoding="utf-8")).get("title") or "")
    if project_title != title:
        raise SystemExit(f"标题与项目不一致：项目为 {project_title}，参数为 {title}")
    output = project / "产出"
    output.mkdir(parents=True, exist_ok=True)
    mapping = [
        (source(args.video, "视频"), output / f"{title}.mp4"),
        (source(args.cover_horizontal, "横版封面"), output / "封面-1920×1080.png"),
        (source(args.cover_vertical, "竖版封面"), output / "封面-1080×1920.png"),
        (source(args.publish_copy, "发布文案"), output / "发布文案.md"),
    ]
    for _, dst in mapping:
        if dst.exists() and not args.overwrite:
            raise SystemExit(f"目标已存在：{dst}；如确需替换请明确使用 --overwrite")

    staged: list[tuple[Path, Path]] = []
    try:
        for src, dst in mapping:
            temporary = dst.with_name(f".{dst.name}.{uuid.uuid4().hex}.tmp")
            shutil.copy2(src, temporary)
            staged.append((temporary, dst))
        for temporary, dst in staged:
            os.replace(temporary, dst)
    finally:
        for temporary, _ in staged:
            if temporary.exists():
                temporary.unlink()
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
