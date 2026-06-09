#!/usr/bin/env python3
"""Send AI News Radar daily brief through Hermes Weixin."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from render_daily_brief import load_payload, render_daily_brief
except ModuleNotFoundError:
    from scripts.render_daily_brief import load_payload, render_daily_brief


HERMES_FAILURE_MARKERS = (
    "send failed",
    "发送失败",
    "rate limit",
    "限流",
)


def build_hermes_prompt(message: str, target: str) -> str:
    return (
        "请把下面这段 AI News Radar 日报原文发送到"
        f"{target}，不要改写，不要添加解释。\n\n"
        "--- AI News Radar 日报开始 ---\n"
        f"{message}"
        "--- AI News Radar 日报结束 ---\n"
    )


def send_with_hermes(message: str, *, target: str, hermes_bin: str) -> None:
    if not shutil.which(hermes_bin):
        raise RuntimeError(f"Cannot find Hermes CLI: {hermes_bin}")
    result = subprocess.run(
        [hermes_bin, "chat", "-q", build_hermes_prompt(message, target)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.stdout:
        print(result.stdout, end="")
    output_lower = (result.stdout or "").lower()
    if result.returncode != 0:
        raise RuntimeError(f"Hermes CLI exited with {result.returncode}")
    if any(marker in output_lower for marker in HERMES_FAILURE_MARKERS):
        raise RuntimeError("Hermes reported a delivery failure")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render daily-brief.json and send it through Hermes Weixin")
    parser.add_argument("--input", default="data/daily-brief.json", help="Path to daily-brief.json")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of brief items to send")
    parser.add_argument("--target", default="微信", help="Human-readable Hermes delivery target")
    parser.add_argument("--hermes-bin", default="hermes", help="Hermes CLI executable")
    parser.add_argument("--dry-run", action="store_true", help="Print message instead of sending")
    args = parser.parse_args()

    message = render_daily_brief(load_payload(Path(args.input)), limit=args.limit)
    if args.dry_run:
        print(message, end="")
        return 0
    try:
        send_with_hermes(message, target=args.target, hermes_bin=args.hermes_bin)
    except Exception as exc:
        print(f"Failed to send daily brief: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
