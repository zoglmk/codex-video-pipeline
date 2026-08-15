from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def run(*args: str, expect: int = 0, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=False, env=env)
    if result.returncode != expect:
        raise AssertionError(
            f"expected {expect}, got {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def make_wav(path: Path, seconds: int = 2) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b"\x00\x00" * 16000 * seconds)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def make_png(path: Path, width: int, height: int) -> None:
    row = b"\x00" + b"\x10\x2a\x43" * width
    payload = b"\x89PNG\r\n\x1a\n"
    payload += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    payload += png_chunk(b"IDAT", zlib.compress(row * height, level=1))
    payload += png_chunk(b"IEND", b"")
    path.write_bytes(payload)


class PipelineScriptsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="codex-video-pipeline-test-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_setup_configure_does_not_write_secrets(self) -> None:
        config = self.root / "config.json"
        result = run(
            PYTHON,
            str(ROOT / "scripts" / "setup.py"),
            "configure",
            "--recommended",
            "--config",
            str(config),
            "--json",
        )
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        text = config.read_text(encoding="utf-8").lower()
        self.assertEqual(json.loads(config.read_text(encoding="utf-8"))["imageProvider"], "imagegen")
        self.assertNotIn("api_key", text)
        self.assertNotIn("token", text)

    def test_python_children_do_not_depend_on_python3_command(self) -> None:
        empty_path = self.root / "empty-bin"
        empty_path.mkdir()
        environment = os.environ.copy()
        environment["PATH"] = str(empty_path)
        result = run(
            PYTHON,
            str(ROOT / "scripts" / "example.py"),
            "--root",
            str(self.root / "带 空格的 videos"),
            "--title",
            "会议:复盘?",
            env=environment,
        )
        project = Path(result.stdout.strip())
        self.assertEqual(project.name, "会议-复盘")
        self.assertTrue((project / "assets" / "meeting-notes.txt").is_file())

    def test_windows_reserved_title_is_sanitized(self) -> None:
        result = run(
            PYTHON,
            str(ROOT / "scripts" / "project.py"),
            "init",
            "--root",
            str(self.root / "videos"),
            "--title",
            "CON",
        )
        self.assertEqual(Path(result.stdout.strip()).name, "_CON")

    def test_no_python3_literal_is_used_for_child_processes(self) -> None:
        for path in (ROOT / "scripts").glob("*.py"):
            body = "\n".join(path.read_text(encoding="utf-8").splitlines()[1:])
            self.assertNotRegex(body, r"[\"']python3[\"']", msg=str(path))

    def test_package_preflight_prevents_partial_copy(self) -> None:
        title = "打包测试"
        result = run(
            PYTHON,
            str(ROOT / "scripts" / "project.py"),
            "init",
            "--root",
            str(self.root / "videos"),
            "--title",
            title,
        )
        project = Path(result.stdout.strip())
        sources = []
        for name in ("video.mp4", "horizontal.png", "vertical.png", "copy.md"):
            path = self.root / name
            path.write_bytes(b"test")
            sources.append(path)
        existing = project / "产出" / f"{title}.mp4"
        existing.write_bytes(b"existing")
        run(
            PYTHON,
            str(ROOT / "scripts" / "package_outputs.py"),
            "--project",
            str(project),
            "--title",
            title,
            "--video",
            str(sources[0]),
            "--cover-horizontal",
            str(sources[1]),
            "--cover-vertical",
            str(sources[2]),
            "--copy",
            str(sources[3]),
            expect=1,
        )
        self.assertEqual(existing.read_bytes(), b"existing")
        self.assertEqual(list((project / "产出").iterdir()), [existing])

    @unittest.skipUnless(shutil.which("ffprobe"), "需要 ffprobe")
    def test_caption_receipt_survives_project_move(self) -> None:
        project = self.root / "原项目"
        audio = project / "audio" / "voice.wav"
        captions = project / "captions" / "captions.json"
        receipt = project / "captions" / "caption-receipt.json"
        audio.parent.mkdir(parents=True)
        captions.parent.mkdir(parents=True)
        make_wav(audio)
        captions.write_text(
            json.dumps({"items": [{"text": "可移动字幕", "start": 0.05, "end": 1.8}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        run(
            PYTHON,
            str(ROOT / "scripts" / "caption_gate.py"),
            "record",
            "--audio",
            str(audio),
            "--captions",
            str(captions),
            "--provider",
            "test-acoustic",
            "--output",
            str(receipt),
        )
        data = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(data["audio"]["pathBase"], "receipt")
        moved = self.root / "移动 后的项目"
        shutil.move(str(project), moved)
        run(
            PYTHON,
            str(ROOT / "scripts" / "caption_gate.py"),
            "verify",
            "--receipt",
            str(moved / "captions" / "caption-receipt.json"),
            "--json",
        )

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "需要 FFmpeg")
    def test_end_to_end_gates(self) -> None:
        title = "测试视频"
        videos = self.root / "videos"
        result = run(
            PYTHON,
            str(ROOT / "scripts" / "project.py"),
            "init",
            "--root",
            str(videos),
            "--title",
            title,
            "--duration",
            "2",
        )
        project = Path(result.stdout.strip())
        audio = project / "audio" / "voice" / "final.wav"
        make_wav(audio)
        captions = project / "captions" / "captions.json"
        captions.write_text(
            json.dumps({"items": [{"text": "这是一条测试字幕", "start": 0.05, "end": 1.8}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        receipt = project / "captions" / "caption-receipt.json"
        run(
            PYTHON,
            str(ROOT / "scripts" / "caption_gate.py"),
            "record",
            "--audio",
            str(audio),
            "--captions",
            str(captions),
            "--provider",
            "test-acoustic",
            "--output",
            str(receipt),
        )

        final_video = project / "renders" / "final.mp4"
        run(
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x102a43:s=1920x1080:r=30:d=2",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=mono",
            "-t",
            "2",
            "-shortest",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(final_video),
        )
        horizontal = project / "renders" / "cover-horizontal.png"
        vertical = project / "renders" / "cover-vertical.png"
        make_png(horizontal, 1920, 1080)
        make_png(vertical, 1080, 1920)
        publish_copy = project / "renders" / "发布文案.md"
        publish_copy.write_text("# 测试视频\n\n这是发布文案。\n", encoding="utf-8")
        run(
            PYTHON,
            str(ROOT / "scripts" / "package_outputs.py"),
            "--project",
            str(project),
            "--title",
            title,
            "--video",
            str(final_video),
            "--cover-horizontal",
            str(horizontal),
            "--cover-vertical",
            str(vertical),
            "--copy",
            str(publish_copy),
        )
        verify = run(
            PYTHON,
            str(ROOT / "scripts" / "project.py"),
            "verify",
            "--project",
            str(project),
            "--json",
        )
        self.assertTrue(json.loads(verify.stdout)["ok"])

        audio.write_bytes(audio.read_bytes() + b"tampered")
        failed = run(
            PYTHON,
            str(ROOT / "scripts" / "caption_gate.py"),
            "verify",
            "--receipt",
            str(receipt),
            "--json",
            expect=2,
        )
        self.assertFalse(json.loads(failed.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
