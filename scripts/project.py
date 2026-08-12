#!/usr/bin/env python3
"""初始化视频项目，并验证最终发布包。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SAFE_TITLE = re.compile(r"^[^/\\\x00-\x1f]+$")
REQUIRED_PROCESS_FILES = ("INPUT.md", "RESEARCH.md", "SCRIPT.md", "STORYBOARD.md", "SOURCES.md")
TARGET_DIMENSIONS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def dump_json(data: Any, path: Path | None = None) -> None:
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if path is None:
        print(rendered, end="")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_title(title: str) -> str:
    value = title.strip()
    if not value or value in {".", ".."} or not SAFE_TITLE.fullmatch(value):
        raise SystemExit("标题不能为空，也不能包含路径分隔符或控制字符")
    if len(value) > 80:
        raise SystemExit("标题不宜超过 80 个字符")
    return value


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"拒绝覆盖已有文件：{path}")
    path.write_text(content, encoding="utf-8")


def command_init(args: argparse.Namespace) -> int:
    title = validate_title(args.title)
    root = args.root.expanduser().resolve()
    project = root / title
    if project.exists():
        raise SystemExit(f"项目已存在：{project}")

    for directory in (
        project,
        project / "assets" / "images",
        project / "assets" / "real-video",
        project / "audio" / "voice",
        project / "audio" / "music",
        project / "captions",
        project / "renders",
        project / "qc",
        project / "产出",
    ):
        directory.mkdir(parents=True, exist_ok=False if directory == project else True)

    manifest = {
        "schemaVersion": 1,
        "title": title,
        "createdAt": now_iso(),
        "platform": args.platform,
        "ratio": args.ratio,
        "width": TARGET_DIMENSIONS[args.ratio][0],
        "height": TARGET_DIMENSIONS[args.ratio][1],
        "targetDurationSeconds": args.duration,
        "status": "initialized",
        "captionReceipt": "captions/caption-receipt.json",
    }
    dump_json(manifest, project / "project.json")
    dump_json({"schemaVersion": 1, "assets": []}, project / "asset-manifest.json")
    write_new(
        project / "INPUT.md",
        f"# 输入\n\n- 主题：{title}\n- 平台：{args.platform}\n- 画幅：{args.ratio}\n- 目标时长：{args.duration} 秒\n- 目标观众：\n- 希望观众带走什么：\n- 已有素材：\n- 约束：\n",
    )
    write_new(project / "RESEARCH.md", "# 研究\n\n## 已核实事实\n\n## 推断与判断\n\n## 风险与不确定性\n")
    write_new(project / "SCRIPT.md", "# 旁白脚本\n\n> 先写真实口语，再进入视觉实现。\n")
    write_new(
        project / "STORYBOARD.md",
        "# 动态叙事图\n\n| 段落 | 旁白任务 | 对象状态变化 | 连续运动 | 文字角色 | 素材 | PPT 风险 |\n|---|---|---|---|---|---|---|\n",
    )
    write_new(project / "SOURCES.md", "# 来源\n\n| 事实/素材 | 来源 | 日期 | 适用范围 | 授权/许可证 |\n|---|---|---|---|---|\n")
    print(project)
    return 0


def probe_video(path: Path) -> dict[str, Any]:
    if shutil.which("ffprobe") is None:
        return {"ok": False, "error": "缺少 ffprobe"}
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip() or "ffprobe 失败"}
    data = json.loads(result.stdout)
    streams = data.get("streams") or []
    video_streams = [item for item in streams if item.get("codec_type") == "video"]
    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    video = video_streams[0] if video_streams else {}
    return {
        "ok": bool(video_streams and audio_streams),
        "durationSeconds": float((data.get("format") or {}).get("duration") or 0),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "frameRate": video.get("r_frame_rate"),
        "videoCodec": video.get("codec_name"),
        "audioTracks": len(audio_streams),
    }


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", header[16:24])


def receipt_status(project: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    receipt = project / str(manifest.get("captionReceipt") or "captions/caption-receipt.json")
    if not receipt.is_file():
        return {"ok": False, "path": str(receipt), "error": "缺少字幕声学对齐凭据"}
    script = Path(__file__).resolve().parent / "caption_gate.py"
    result = subprocess.run(
        ["python3", str(script), "verify", "--receipt", str(receipt), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"ok": False, "error": result.stderr.strip() or result.stdout.strip()}
    return data


def command_verify(args: argparse.Namespace) -> int:
    project = args.project.expanduser().resolve()
    errors: list[str] = []
    manifest_path = project / "project.json"
    if not manifest_path.is_file():
        raise SystemExit(f"缺少项目清单：{manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    title = validate_title(str(manifest.get("title") or ""))

    missing_process = [name for name in REQUIRED_PROCESS_FILES if not (project / name).is_file()]
    if missing_process:
        errors.append(f"缺少过程文件：{', '.join(missing_process)}")

    output = project / "产出"
    expected = {
        "video": output / f"{title}.mp4",
        "coverHorizontal": output / "封面-1920×1080.png",
        "coverVertical": output / "封面-1080×1920.png",
        "publishCopy": output / "发布文案.md",
    }
    for label, path in expected.items():
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"缺少最终文件 {label}：{path}")

    media = probe_video(expected["video"]) if expected["video"].is_file() else {"ok": False}
    if expected["video"].is_file() and not media.get("ok"):
        errors.append("最终视频缺少有效视频流或音频流")
    if media.get("ok"):
        target_width = int(manifest.get("width") or 0)
        target_height = int(manifest.get("height") or 0)
        target_duration = float(manifest.get("targetDurationSeconds") or 0)
        if (int(media.get("width") or 0), int(media.get("height") or 0)) != (target_width, target_height):
            errors.append(
                f"最终视频尺寸应为 {target_width}×{target_height}，实际为 {media.get('width')}×{media.get('height')}"
            )
        if target_duration > 0 and float(media.get("durationSeconds") or 0) < target_duration * 0.9:
            errors.append("最终视频明显短于项目目标时长")

    for label, size in (("coverHorizontal", (1920, 1080)), ("coverVertical", (1080, 1920))):
        path = expected[label]
        if path.is_file() and png_dimensions(path) != size:
            errors.append(f"{label} 必须是 {size[0]}×{size[1]} PNG")
    caption = receipt_status(project, manifest)
    if not caption.get("ok"):
        errors.append(f"字幕门未通过：{caption.get('error', '未知错误')}")

    unexpected = []
    if output.is_dir():
        expected_paths = {path.resolve() for path in expected.values()}
        unexpected = [str(path) for path in output.iterdir() if path.resolve() not in expected_paths]
        if unexpected:
            errors.append("产出目录包含非交付文件")

    report = {
        "ok": not errors,
        "project": str(project),
        "title": title,
        "errors": errors,
        "media": media,
        "captions": caption,
        "unexpectedOutputFiles": unexpected,
        "files": {key: {"path": str(path), "sha256": sha256(path) if path.is_file() else None} for key, path in expected.items()},
    }
    if args.json:
        dump_json(report)
    else:
        print("PASS" if report["ok"] else "FAIL")
        for error in errors:
            print(f"- {error}")
    return 0 if report["ok"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--root", type=Path, default=Path("videos"))
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--platform", default="douyin")
    init_parser.add_argument("--ratio", choices=("16:9", "9:16", "1:1"), default="16:9")
    init_parser.add_argument("--duration", type=int, default=90)
    init_parser.set_defaults(handler=command_init)

    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--project", type=Path, required=True)
    verify_parser.add_argument("--json", action="store_true")
    verify_parser.set_defaults(handler=command_verify)
    return parser


if __name__ == "__main__":
    parsed = build_parser().parse_args()
    raise SystemExit(parsed.handler(parsed))
