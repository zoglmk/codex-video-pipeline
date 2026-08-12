#!/usr/bin/env python3
"""准备内置首次项目，不生成伪造的完成结果。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("videos"))
    parser.add_argument("--title", default="让AI把杂乱会议记录变成行动清单")
    args = parser.parse_args()

    skill = Path(__file__).resolve().parent.parent
    project_script = skill / "scripts" / "project.py"
    result = subprocess.run(
        [
            "python3",
            str(project_script),
            "init",
            "--root",
            str(args.root),
            "--title",
            args.title,
            "--platform",
            "douyin",
            "--ratio",
            "16:9",
            "--duration",
            "90",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or result.stdout.strip())
    project = Path(result.stdout.strip()).resolve()
    source = skill / "examples" / "ai-meeting-notes"
    shutil.copy2(source / "INPUT.md", project / "INPUT.md")
    shutil.copy2(source / "source" / "meeting-notes.txt", project / "assets" / "meeting-notes.txt")
    print(project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
