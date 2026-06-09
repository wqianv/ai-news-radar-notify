#!/usr/bin/env python3
"""Render AI News Radar daily brief as a compact message."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _format_source(item: dict[str, Any]) -> str:
    source = _as_text(item.get("source")) or _as_text(item.get("source_name"))
    source_count = item.get("source_count")
    if isinstance(source_count, int) and source_count > 1:
        return f"{source} 等 {source_count} 个来源" if source else f"{source_count} 个来源"
    return source


def _format_reason(item: dict[str, Any]) -> str:
    label = _as_text(item.get("importance_label"))
    reasons = item.get("reasons")
    if label:
        return label
    if isinstance(reasons, list) and reasons:
        return ", ".join(_as_text(reason) for reason in reasons[:3] if _as_text(reason))
    return ""


def render_daily_brief(payload: dict[str, Any], *, limit: int = 10, include_links: bool = True) -> str:
    items = payload.get("items")
    if not isinstance(items, list):
        items = []
    items = [item for item in items if isinstance(item, dict)][: max(limit, 0)]

    generated_at = _as_text(payload.get("generated_at"))
    window_hours = payload.get("window_hours") or 24
    total_items = payload.get("total_items") or len(items)

    lines = [
        f"AI News Radar｜{window_hours}小时精选",
        f"共 {total_items} 条精选，以下是 Top {len(items)}：",
    ]
    if generated_at:
        lines.append(f"生成时间：{generated_at}")
    lines.append("")

    if not items:
        lines.append("本轮没有可推送的精选消息。")
        return "\n".join(lines).strip() + "\n"

    for index, item in enumerate(items, 1):
        title = _as_text(item.get("title")) or "未命名消息"
        source = _format_source(item)
        reason = _format_reason(item)
        url = _as_text(item.get("url")) or _as_text(item.get("primary_url"))
        score = item.get("score") or item.get("importance_score")

        lines.append(f"{index}. {title}")
        meta_parts = []
        if source:
            meta_parts.append(source)
        if reason:
            meta_parts.append(reason)
        if isinstance(score, (int, float)):
            meta_parts.append(f"score {score:.2f}")
        if meta_parts:
            lines.append(f"   {' · '.join(meta_parts)}")
        if include_links and url:
            lines.append(f"   {url}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def load_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Render data/daily-brief.json as a text message")
    parser.add_argument("--input", default="data/daily-brief.json", help="Path to daily-brief.json")
    parser.add_argument("--output", help="Optional path to write rendered message")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of brief items to include")
    parser.add_argument("--no-links", action="store_true", help="Omit URLs from the rendered message")
    args = parser.parse_args()

    message = render_daily_brief(
        load_payload(Path(args.input)),
        limit=args.limit,
        include_links=not args.no_links,
    )
    if args.output:
        Path(args.output).write_text(message, encoding="utf-8")
    else:
        print(message, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
