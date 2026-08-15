#!/usr/bin/env python3
"""跨平台运行辅助：复用当前 Python，并生成安全文件名。"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Sequence


INVALID_TITLE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def safe_title(value: str, *, limit: int = 80) -> str:
    """把标题转换为 macOS、Windows 和 Linux 都能使用的文件名。"""

    title = unicodedata.normalize("NFC", value).strip()
    title = INVALID_TITLE.sub("-", title)
    title = re.sub(r"-{2,}", "-", title).rstrip(" .-")
    if not title or title in {".", ".."}:
        raise ValueError("标题不能为空或只包含文件系统保留字符")
    if title.split(".", 1)[0].upper() in WINDOWS_RESERVED:
        title = f"_{title}"
    title = title[:limit].rstrip(" .-")
    if not title:
        raise ValueError("标题转换后为空")
    return title


def utf8_environment() -> dict[str, str]:
    """让子 Python 在 Windows 控制台中也稳定使用 UTF-8。"""

    environment = os.environ.copy()
    environment.setdefault("PYTHONUTF8", "1")
    environment.setdefault("PYTHONIOENCODING", "utf-8")
    return environment


def run_python(
    script: Path,
    arguments: Sequence[str],
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """使用当前解释器运行同一 Skill 内的 Python 脚本。"""

    options: dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "check": False,
        "env": utf8_environment(),
    }
    options.update(kwargs)
    return subprocess.run([sys.executable, str(script), *arguments], **options)


def python_command(script: Path, *arguments: str) -> list[str]:
    """返回适合诊断报告展示和程序执行的参数数组。"""

    return [sys.executable, str(script), *arguments]
