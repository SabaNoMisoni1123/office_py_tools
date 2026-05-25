from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SERVER_NAME = "office_py_tools_local_only"
MODULE_NAME = "mcp_servers.local_only.server"
TOOL_NAME = "get_japanese_date_info"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="local_only MCP サーバーのクライアント設定例を生成します。"
    )
    parser.add_argument(
        "--client",
        choices=("claude", "codex"),
        required=True,
        help="生成する設定の対象クライアント。",
    )
    parser.add_argument(
        "--runner",
        choices=("pipenv", "python"),
        default="pipenv",
        help="MCP サーバーの起動方法。既定は pipenv。",
    )
    parser.add_argument(
        "--repository-root",
        default=None,
        help="設定に書き込むプロジェクトルート。省略時は現在の作業ディレクトリ。",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="出力先ファイル。省略時は標準出力。",
    )

    args = parser.parse_args()
    repository_root = Path(args.repository_root or Path.cwd()).resolve()

    if args.client == "claude":
        content = _build_claude_config(args.runner, repository_root)
        text = json.dumps(content, ensure_ascii=False, indent=2) + "\n"
    else:
        text = _build_codex_config(args.runner, repository_root)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _build_claude_config(runner: str, repository_root: Path) -> dict[str, Any]:
    return {
        "mcpServers": {
            SERVER_NAME: {
                "command": _command_for(runner),
                "args": _args_for(runner),
                "cwd": str(repository_root),
            }
        }
    }


def _build_codex_config(runner: str, repository_root: Path) -> str:
    args_text = "\n".join(f'  "{arg}",' for arg in _args_for(runner))
    return (
        f"[mcp_servers.{SERVER_NAME}]\n"
        f'command = "{_command_for(runner)}"\n'
        "args = [\n"
        f"{args_text}\n"
        "]\n"
        f'cwd = "{_toml_string(str(repository_root))}"\n'
        "startup_timeout_sec = 20\n"
        "tool_timeout_sec = 60\n"
        f'enabled_tools = ["{TOOL_NAME}"]\n'
    )


def _command_for(runner: str) -> str:
    if runner == "pipenv":
        return "pipenv"
    return "python"


def _args_for(runner: str) -> list[str]:
    if runner == "pipenv":
        return ["run", "python", "-m", MODULE_NAME]
    return ["-m", MODULE_NAME]


def _toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


if __name__ == "__main__":
    main()
