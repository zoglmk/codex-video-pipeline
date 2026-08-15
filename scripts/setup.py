#!/usr/bin/env python3
"""首次配置与只读环境检查；不安装软件，也不保存密钥。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime import python_command

SCRIPT_PATH = Path(__file__).resolve()
HYPERFRAMES_GITHUB = "https://github.com/heygen-com/hyperframes"
AGENT_REACH_GITHUB = "https://github.com/Panniantong/Agent-Reach"


def default_config_path() -> Path:
    override = os.environ.get("CODEX_VIDEO_PIPELINE_CONFIG")
    if override:
        return Path(override).expanduser()
    legacy = Path.home() / ".config" / "codex-video-pipeline" / "config.json"
    if platform.system() == "Windows" and os.environ.get("APPDATA"):
        windows_path = Path(os.environ["APPDATA"]) / "codex-video-pipeline" / "config.json"
        return legacy if legacy.exists() and not windows_path.exists() else windows_path
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return Path(xdg) / "codex-video-pipeline" / "config.json" if xdg else legacy


DEFAULT_CONFIG = default_config_path()


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def emit(data: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"{key}: {value}")
    else:
        print(data)


def executable(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    return {"ready": bool(path), "path": path}


def install_hint(tool: str) -> str:
    system = platform.system()
    if tool == "ffmpeg":
        if system == "Windows":
            return "经用户确认后可用 winget install Gyan.FFmpeg；完成后重开终端，确认 ffmpeg 和 ffprobe 都在 PATH"
        if system == "Darwin":
            return "经用户确认后可用 brew install ffmpeg，再确认 ffmpeg 和 ffprobe 都可执行"
        return "经用户确认后使用当前发行版的包管理器安装 FFmpeg，并确认 ffmpeg 和 ffprobe 都可执行"
    if system == "Windows":
        return "经用户确认后安装 Node.js LTS；完成后重开终端，确认 node、npm 和 npx 都在 PATH"
    return "经用户确认后安装 Node.js LTS，并确认 node、npm 和 npx 都在 PATH"


def module_ready(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def skill_candidates(name: str) -> list[Path]:
    home = Path.home()
    direct = [
        home / ".codex" / "skills" / name / "SKILL.md",
        home / ".agents" / "skills" / name / "SKILL.md",
        home / ".claude" / "skills" / name / "SKILL.md",
    ]
    plugin_root = home / ".codex" / "plugins" / "cache"
    if plugin_root.exists():
        direct.extend(plugin_root.glob(f"**/skills/{name}/SKILL.md"))
    return direct


def find_skill(name: str) -> dict[str, Any]:
    matches = sorted({path.resolve() for path in skill_candidates(name) if path.is_file()})
    return {"ready": bool(matches), "paths": [str(path) for path in matches]}


def load_config(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, "尚未创建配置"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"配置无法读取：{exc}"
    if not isinstance(data, dict):
        return None, "配置顶层必须是 JSON 对象"
    return data, None


def config_summary(config: dict[str, Any] | None) -> dict[str, Any] | None:
    if config is None:
        return None
    public_keys = (
        "schemaVersion",
        "renderer",
        "research",
        "imageProvider",
        "ttsProvider",
        "captionProvider",
        "realFootageProvider",
        "musicProvider",
    )
    return {key: config.get(key) for key in public_keys if key in config}


def doctor(args: argparse.Namespace) -> int:
    config_path = args.config.expanduser().resolve()
    config, config_error = load_config(config_path)
    hyperframes = find_skill("hyperframes")
    ffmpeg = executable("ffmpeg")
    ffprobe = executable("ffprobe")
    node = executable("node")
    npm = executable("npm")
    npx = executable("npx")
    python_ok = sys.version_info >= (3, 10)
    actions: list[dict[str, Any]] = []

    if not python_ok:
        actions.append(
            {
                "id": "upgrade-python",
                "required": "true",
                "message": "需要 Python 3.10 或更高版本；安装或切换解释器前先征得用户确认",
            }
        )

    if not hyperframes["ready"]:
        actions.append(
            {
                "id": "install-hyperframes",
                "required": "true",
                "for_codex": "在 Codex 插件页安装 HyperFrames",
                "for_other_agents": f"把 GitHub 链接交给 Agent 安装：{HYPERFRAMES_GITHUB}",
            }
        )
    if not ffmpeg["ready"] or not ffprobe["ready"]:
        actions.append(
            {
                "id": "install-ffmpeg",
                "required": "true",
                "message": "安装 FFmpeg（包含 ffprobe）；这是系统级变更，执行前先征得用户确认",
                "hint": install_hint("ffmpeg"),
            }
        )
    if not node["ready"] or not npm["ready"] or not npx["ready"]:
        actions.append(
            {
                "id": "install-node",
                "required": "true",
                "message": "安装 Node.js LTS（包含 npm 和 npx）；这是系统级变更，执行前先征得用户确认",
                "hint": install_hint("node"),
            }
        )
    if config_error:
        actions.append(
            {
                "id": "configure",
                "required": "true",
                "message": "使用当前 Python 解释器运行 setup.py configure --recommended",
                "command": python_command(SCRIPT_PATH, "configure", "--recommended", "--config", str(config_path)),
            }
        )

    report = {
        "schemaVersion": 1,
        "checkedAt": now_iso(),
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "python": {"ready": python_ok, "version": platform.python_version(), "executable": sys.executable},
        "core": {
            "hyperframes": hyperframes,
            "ffmpeg": ffmpeg,
            "ffprobe": ffprobe,
            "node": node,
            "npm": npm,
            "npx": npx,
            "git": executable("git"),
        },
        "optional": {
            "agentReach": find_skill("agent-reach"),
            "mlxWhisper": {"ready": module_ready("mlx_whisper")},
            "whisperCli": {
                "ready": bool(shutil.which("whisper") or shutil.which("whisper-cli")),
                "path": shutil.which("whisper") or shutil.which("whisper-cli"),
            },
            "pexelsApiKey": {"ready": bool(os.environ.get("PEXELS_API_KEY"))},
            "doubaoCredentials": {
                "ready": bool(
                    os.environ.get("VOLC_APP_ID")
                    and (os.environ.get("VOLC_ACCESS_TOKEN") or os.environ.get("VOLC_API_KEY"))
                )
            },
        },
        "config": {
            "ready": config is not None,
            "path": str(config_path),
            "error": config_error,
            "summary": config_summary(config),
        },
        "actions": actions,
        "readyForProduction": python_ok
        and hyperframes["ready"]
        and ffmpeg["ready"]
        and ffprobe["ready"]
        and node["ready"]
        and npm["ready"]
        and npx["ready"]
        and config is not None,
    }
    emit(report, args.json)
    return 0 if report["readyForProduction"] else 2


def configure(args: argparse.Namespace) -> int:
    config_path = args.config.expanduser().resolve()
    if config_path.exists() and not args.force:
        raise SystemExit(f"配置已存在：{config_path}；如需替换请明确使用 --force")

    recommended = {
        "schemaVersion": 1,
        "createdAt": now_iso(),
        "renderer": "hyperframes",
        "research": "agent-web",
        "imageProvider": "imagegen",
        "ttsProvider": "agent",
        "captionProvider": "auto-acoustic",
        "realFootageProvider": "pexels-optional",
        "musicProvider": "user-or-licensed",
        "defaults": {
            "language": "zh-CN",
            "platform": "douyin",
            "ratio": "16:9",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "minimumDurationSeconds": 80,
            "progressBar": "bottom",
        },
        "security": {
            "storeSecretsInProject": False,
            "allowUnattributedFootage": False,
            "requireActualAudioCaptionAlignment": True,
        },
    }
    if not args.recommended:
        recommended["ttsProvider"] = args.tts
        recommended["captionProvider"] = args.captions
        recommended["realFootageProvider"] = args.footage

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(recommended, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {
        "ok": True,
        "config": str(config_path),
        "secretsWritten": False,
        "next": [
            "重新运行 doctor",
            "Codex 直接使用原生 imagegen；其他 Agent 缺少原生图片能力时配置图像生成接口",
            "如需 Pexels，在环境变量或系统安全存储中配置 PEXELS_API_KEY",
            "如需第三方 TTS，在提供方控制台创建凭据并仅保存到环境或系统安全存储",
            "使用内置示例完成第一次端到端制作",
        ],
    }
    emit(result, args.json)
    return 0


def guide(args: argparse.Namespace) -> int:
    steps = {
        "title": "Codex Video Pipeline 首次安装顺序",
        "steps": [
            "把本仓库 GitHub 链接交给 AI Agent，让它按自身的 Skill 安装方式安装",
            "Codex 用户在插件页安装 HyperFrames；其他 Agent 使用 HyperFrames GitHub 链接",
            "按当前系统选择可用的 Python 3.10+ 解释器，不要把 python3 写死到 Windows 命令中",
            "让 Agent 运行 doctor，只处理报告里的缺失项",
            "运行 configure；配置文件只保存选择，不保存任何密钥",
            "Codex 直接使用 imagegen；其他 Agent 缺少原生图片能力时配置图像生成接口",
            "按需配置配音、声学字幕、Pexels 和有授权的音乐",
            "运行 examples/ai-meeting-notes 的完整示例并验收实际 MP4",
        ],
        "links": {
            "hyperframes": HYPERFRAMES_GITHUB,
            "agentReachOptional": AGENT_REACH_GITHUB,
        },
    }
    emit(steps, args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    doctor_parser = sub.add_parser("doctor", help="只读检查环境和配置")
    doctor_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    doctor_parser.add_argument("--json", action="store_true")
    doctor_parser.set_defaults(handler=doctor)

    configure_parser = sub.add_parser("configure", help="创建不含密钥的提供方配置")
    configure_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    configure_parser.add_argument("--recommended", action="store_true")
    configure_parser.add_argument("--tts", choices=("agent", "manual", "doubao"), default="agent")
    configure_parser.add_argument(
        "--captions",
        choices=("auto-acoustic", "agent-acoustic", "mlx-whisper", "whisper-cli", "external-json"),
        default="auto-acoustic",
    )
    configure_parser.add_argument("--footage", choices=("pexels-optional", "manual", "none"), default="pexels-optional")
    configure_parser.add_argument("--force", action="store_true")
    configure_parser.add_argument("--json", action="store_true")
    configure_parser.set_defaults(handler=configure)

    guide_parser = sub.add_parser("guide", help="打印适合人类或 Agent 的安装顺序")
    guide_parser.add_argument("--json", action="store_true")
    guide_parser.set_defaults(handler=guide)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
