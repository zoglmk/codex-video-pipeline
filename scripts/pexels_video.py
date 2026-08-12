#!/usr/bin/env python3
"""搜索并下载 Pexels 视频，保存来源与文件指纹。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


API_URL = "https://api.pexels.com/v1/videos/search"
LICENSE_URL = "https://www.pexels.com/license/"
USER_AGENT = "codex-video-pipeline/1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def dump(data: Any, path: Path | None = None) -> None:
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def key() -> str:
    value = os.environ.get("PEXELS_API_KEY", "").strip()
    if not value:
        raise SystemExit("缺少 PEXELS_API_KEY；请保存到环境或系统安全存储，不要写入项目")
    return value


def pexels_url(value: str) -> bool:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == "pexels.com" or host.endswith(".pexels.com"))


def orientation(width: int, height: int) -> str:
    if width == height:
        return "square"
    return "landscape" if width > height else "portrait"


def choose_file(files: list[dict[str, Any]], width: int, height: int) -> dict[str, Any] | None:
    target_ratio = width / height
    valid = [
        item
        for item in files
        if int(item.get("width") or 0) > 0
        and int(item.get("height") or 0) > 0
        and pexels_url(str(item.get("link") or ""))
    ]
    if not valid:
        return None

    def score(item: dict[str, Any]) -> tuple[int, int, float, int]:
        w = int(item.get("width") or 0)
        h = int(item.get("height") or 0)
        return (
            int(orientation(w, h) == orientation(width, height)),
            int(w >= width and h >= height),
            -abs(w / h - target_ratio),
            -(abs(w - width) + abs(h - height)),
        )

    selected = max(valid, key=score)
    return {
        "id": selected.get("id"),
        "width": selected.get("width"),
        "height": selected.get("height"),
        "fps": selected.get("fps"),
        "quality": selected.get("quality"),
        "fileType": selected.get("file_type"),
        "url": selected.get("link"),
    }


def request_search(query: str, width: int, height: int, count: int) -> dict[str, Any]:
    params = urlencode(
        {
            "query": query,
            "orientation": orientation(width, height),
            "size": "medium",
            "per_page": min(max(count, 1), 80),
        }
    )
    request = Request(
        f"{API_URL}?{params}",
        headers={"Authorization": key(), "Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        message = {401: "Pexels API Key 无效", 429: "Pexels API 达到速率限制"}.get(exc.code, f"Pexels HTTP {exc.code}")
        raise SystemExit(message) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Pexels 请求失败：{exc}") from exc


def command_status(args: argparse.Namespace) -> int:
    dump({"ready": bool(os.environ.get("PEXELS_API_KEY")), "secretPrinted": False, "license": LICENSE_URL})
    return 0


def command_search(args: argparse.Namespace) -> int:
    candidates: dict[int, dict[str, Any]] = {}
    for query in args.query:
        payload = request_search(query, args.width, args.height, args.per_query)
        for rank, video in enumerate(payload.get("videos") or [], start=1):
            selected = choose_file(video.get("video_files") or [], args.width, args.height)
            if not selected:
                continue
            video_id = int(video.get("id") or 0)
            creator = video.get("user") or {}
            current = candidates.setdefault(
                video_id,
                {
                    "id": video_id,
                    "queries": [],
                    "bestRank": rank,
                    "durationSeconds": video.get("duration"),
                    "pageUrl": video.get("url"),
                    "previewUrl": video.get("image"),
                    "creator": {"name": creator.get("name"), "url": creator.get("url")},
                    "selectedFile": selected,
                },
            )
            current["queries"].append(query)
            current["bestRank"] = min(int(current["bestRank"]), rank)
    ordered = sorted(candidates.values(), key=lambda item: (item["bestRank"], -int(item["selectedFile"]["width"] or 0)))
    manifest = {
        "schemaVersion": 1,
        "provider": "Pexels",
        "createdAt": now_iso(),
        "queries": args.query,
        "target": {"width": args.width, "height": args.height},
        "license": LICENSE_URL,
        "candidates": ordered,
    }
    dump(manifest, args.manifest.expanduser().resolve())
    print(args.manifest.expanduser().resolve())
    return 0


def download(url: str, output: Path, max_bytes: int) -> tuple[int, str]:
    if not pexels_url(url):
        raise SystemExit("拒绝下载非 Pexels HTTPS 地址")
    if output.exists():
        raise SystemExit(f"目标已存在：{output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    total = 0
    temporary: Path | None = None
    try:
        with urlopen(request, timeout=120) as response:
            with tempfile.NamedTemporaryFile(dir=output.parent, prefix=f".{output.name}.", suffix=".part", delete=False) as handle:
                temporary = Path(handle.name)
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    total += len(block)
                    if total > max_bytes:
                        raise SystemExit("视频超过下载上限")
                    digest.update(block)
                    handle.write(block)
        if total == 0:
            raise SystemExit("下载结果为空")
        temporary.replace(output)
        temporary = None
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return total, digest.hexdigest()


def command_download(args: argparse.Namespace) -> int:
    manifest_path = args.manifest.expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates = manifest.get("candidates") or []
    selected = next((item for item in candidates if int(item.get("id") or 0) == args.id), None)
    if not selected:
        raise SystemExit(f"manifest 中没有候选 {args.id}")
    output = args.output.expanduser().resolve()
    file_info = selected["selectedFile"]
    total, file_hash = download(str(file_info["url"]), output, args.max_bytes)
    receipt = {
        "schemaVersion": 1,
        "provider": "Pexels",
        "downloadedAt": now_iso(),
        "asset": {
            "id": selected["id"],
            "creator": selected["creator"],
            "pageUrl": selected["pageUrl"],
            "license": LICENSE_URL,
        },
        "file": {"path": str(output), "bytes": total, "sha256": file_hash, "source": file_info},
    }
    receipt_path = output.with_suffix(output.suffix + ".source.json")
    dump(receipt, receipt_path)
    print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status")
    status.set_defaults(handler=command_status)
    search = sub.add_parser("search")
    search.add_argument("--query", action="append", required=True)
    search.add_argument("--width", type=int, default=1920)
    search.add_argument("--height", type=int, default=1080)
    search.add_argument("--per-query", type=int, default=12)
    search.add_argument("--manifest", type=Path, required=True)
    search.set_defaults(handler=command_search)
    download_parser = sub.add_parser("download")
    download_parser.add_argument("--manifest", type=Path, required=True)
    download_parser.add_argument("--id", type=int, required=True)
    download_parser.add_argument("--output", type=Path, required=True)
    download_parser.add_argument("--max-bytes", type=int, default=1_500_000_000)
    download_parser.set_defaults(handler=command_download)
    return parser


if __name__ == "__main__":
    parsed = build_parser().parse_args()
    raise SystemExit(parsed.handler(parsed))
