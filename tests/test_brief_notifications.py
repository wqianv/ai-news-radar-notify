import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.render_daily_brief import render_daily_brief
from scripts.send_weixin_brief import build_hermes_prompt, send_with_hermes


def test_render_daily_brief_formats_top_items():
    payload = {
        "generated_at": "2026-06-08T16:00:00Z",
        "window_hours": 24,
        "total_items": 2,
        "items": [
            {
                "title": "OpenAI releases a model update",
                "url": "https://example.com/openai",
                "source": "OpenAI News",
                "source_count": 2,
                "importance_label": "官方更新",
                "score": 0.91,
            },
            {
                "title": "Developer tool adds agent workflow",
                "primary_url": "https://example.com/tool",
                "source_name": "Tool Blog",
                "reasons": ["agent_workflow", "developer_tool"],
                "importance_score": 0.72,
            },
        ],
    }

    message = render_daily_brief(payload, limit=2)

    assert "AI News Radar｜24小时精选" in message
    assert "共 2 条精选，以下是 Top 2" in message
    assert "1. OpenAI releases a model update" in message
    assert "OpenAI News 等 2 个来源 · 官方更新 · score 0.91" in message
    assert "https://example.com/tool" in message


def test_render_daily_brief_can_omit_links():
    payload = {"items": [{"title": "Only title", "url": "https://example.com"}]}

    message = render_daily_brief(payload, include_links=False)

    assert "Only title" in message
    assert "https://example.com" not in message


def test_render_script_cli_writes_output(tmp_path):
    payload_path = tmp_path / "daily-brief.json"
    output_path = tmp_path / "brief.txt"
    payload_path.write_text(json.dumps({"items": [{"title": "CLI item"}]}), encoding="utf-8")

    subprocess.run(
        [
            "python",
            "scripts/render_daily_brief.py",
            "--input",
            str(payload_path),
            "--output",
            str(output_path),
        ],
        check=True,
    )

    assert "CLI item" in output_path.read_text(encoding="utf-8")


def test_send_prompt_preserves_message():
    prompt = build_hermes_prompt("hello\n", "微信")

    assert "发送到微信" in prompt
    assert "hello" in prompt
    assert "不要改写" in prompt


def test_send_with_hermes_raises_when_delivery_fails():
    result = subprocess.CompletedProcess(
        args=["hermes"],
        returncode=0,
        stdout="微信发送失败：iLink sendmessage 被限流",
    )
    with patch("scripts.send_weixin_brief.shutil.which", return_value="hermes"):
        with patch("scripts.send_weixin_brief.subprocess.run", return_value=result):
            with pytest.raises(RuntimeError, match="delivery failure"):
                send_with_hermes("hello", target="微信", hermes_bin="hermes")
