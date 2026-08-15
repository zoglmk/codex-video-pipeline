#!/usr/bin/env python3
"""为基于真实语音的字幕生成防篡改凭据，并在发布前复核。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def duration(path: Path) -> float:
    if shutil.which("ffprobe") is None:
        raise SystemExit("缺少 ffprobe，无法验证音频时长")
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or "无法读取音频")
    return float(result.stdout.strip())


def read_items(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise SystemExit("字幕 JSON 必须是非空数组，或包含非空 items 数组")
    normalized = []
    last_start = -1.0
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise SystemExit(f"第 {index + 1} 条字幕不是对象")
        text = str(item.get("text") or "").strip()
        start = float(item.get("start") if item.get("start") is not None else -1)
        end = float(item.get("end") if item.get("end") is not None else -1)
        if not text or start < 0 or end <= start or start < last_start:
            raise SystemExit(f"第 {index + 1} 条字幕文本或时间无效")
        normalized.append({"text": text, "start": start, "end": end})
        last_start = start
    return normalized


def emit(data: dict[str, Any], path: Path | None, as_json: bool = False) -> None:
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise SystemExit(f"拒绝覆盖已有凭据：{path}")
        path.write_text(rendered, encoding="utf-8")
    if as_json or not path:
        print(rendered, end="")


def portable_path(path: Path, receipt_path: Path) -> tuple[str, str]:
    """优先保存相对路径，使整个项目移动到另一台电脑后仍可验证。"""

    try:
        relative = Path(os.path.relpath(path, receipt_path.parent))
    except ValueError:
        return str(path), "absolute"
    return relative.as_posix(), "receipt"


def resolve_recorded_path(receipt_path: Path, section: dict[str, Any]) -> Path:
    raw = str(section.get("path") or "")
    path = Path(raw)
    if section.get("pathBase") == "receipt" or not path.is_absolute():
        path = receipt_path.parent / path
    return path.expanduser().resolve()


def command_record(args: argparse.Namespace) -> int:
    audio = args.audio.expanduser().resolve()
    captions = args.captions.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not audio.is_file() or not captions.is_file():
        raise SystemExit("音频或字幕文件不存在")
    items = read_items(captions)
    audio_duration = duration(audio)
    if items[-1]["end"] > audio_duration + args.end_tolerance:
        raise SystemExit("最后一条字幕明显超过音频结尾")
    if args.provider.lower() in {"estimated", "character-count", "manual-estimate", "unknown"}:
        raise SystemExit("发布字幕不能使用字数估时或未知提供方")
    audio_path, audio_base = portable_path(audio, output)
    captions_path, captions_base = portable_path(captions, output)
    receipt = {
        "schemaVersion": 1,
        "method": "acoustic-alignment",
        "provider": args.provider,
        "createdAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "audio": {
            "path": audio_path,
            "pathBase": audio_base,
            "sha256": sha256(audio),
            "durationSeconds": audio_duration,
        },
        "captions": {
            "path": captions_path,
            "pathBase": captions_base,
            "sha256": sha256(captions),
            "count": len(items),
            "firstStart": items[0]["start"],
            "lastEnd": items[-1]["end"],
        },
    }
    emit(receipt, output, args.json)
    return 0


def command_verify(args: argparse.Namespace) -> int:
    receipt_path = args.receipt.expanduser().resolve()
    errors = []
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        receipt = {}
        errors.append(f"凭据无法读取：{exc}")
    audio_section = receipt.get("audio") or {}
    captions_section = receipt.get("captions") or {}
    audio = resolve_recorded_path(receipt_path, audio_section)
    captions = resolve_recorded_path(receipt_path, captions_section)
    if receipt.get("method") != "acoustic-alignment":
        errors.append("不是声学对齐凭据")
    for label, path, expected in (
        ("音频", audio, audio_section.get("sha256")),
        ("字幕", captions, captions_section.get("sha256")),
    ):
        if not path.is_file():
            errors.append(f"{label}文件不存在：{path}")
        elif sha256(path) != expected:
            errors.append(f"{label}文件在对齐后发生变化")
    report = {"ok": not errors, "receipt": str(receipt_path), "provider": receipt.get("provider"), "error": "; ".join(errors) if errors else None}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("PASS" if report["ok"] else f"FAIL: {report['error']}")
    return 0 if report["ok"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record")
    record.add_argument("--audio", type=Path, required=True)
    record.add_argument("--captions", type=Path, required=True)
    record.add_argument("--provider", required=True)
    record.add_argument("--output", type=Path, required=True)
    record.add_argument("--end-tolerance", type=float, default=1.0)
    record.add_argument("--json", action="store_true")
    record.set_defaults(handler=command_record)
    verify = sub.add_parser("verify")
    verify.add_argument("--receipt", type=Path, required=True)
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(handler=command_verify)
    return parser


if __name__ == "__main__":
    parsed = build_parser().parse_args()
    raise SystemExit(parsed.handler(parsed))
