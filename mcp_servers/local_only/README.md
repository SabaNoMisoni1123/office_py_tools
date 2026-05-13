# local_only MCP server

MCP サーバーからのみ利用する新規プログラムを置くための最小サーバーです。

このサーバーは既存 CLI の機能を公開しません。今後 MCP 専用のツール、リソース、プロンプトを追加するときだけ、この配下へ実装します。

## 起動

Pipenv を使う場合:

```sh
pipenv run python -m mcp_servers.local_only.server
```

Pipenv を使わない場合:

```sh
python -m mcp_servers.local_only.server
```

## AI クライアント設定例

### Codex

Codex CLI / IDE 拡張は `~/.codex/config.toml` の `[mcp_servers]` に MCP サーバーを登録します。

```toml
[mcp_servers.office_py_tools_local_only]
command = "pipenv"
args = [
  "run",
  "python",
  "-m",
  "mcp_servers.local_only.server",
]
cwd = "/home/sabamiso/workspace/office_py_tools"
startup_timeout_sec = 20
tool_timeout_sec = 60
enabled_tools = ["get_japanese_date_info"]
```

Pipenv の PATH が通らない環境では、`command` に `pipenv` の絶対パス、または `pipenv --venv` で確認した仮想環境内の `python` を指定してください。

例:

```toml
[mcp_servers.office_py_tools_local_only]
command = "/path/to/.venv/bin/python"
args = [
  "-m",
  "mcp_servers.local_only.server",
]
cwd = "/home/sabamiso/workspace/office_py_tools"
startup_timeout_sec = 20
tool_timeout_sec = 60
enabled_tools = ["get_japanese_date_info"]
```

登録後の確認:

```sh
codex mcp list
```

### Claude Desktop

Claude Desktop でローカル MCP サーバーとして使う場合は、`claude_desktop_config.json` の `mcpServers` に登録します。

設定ファイルの標準的な場所:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

設定例:

```json
{
  "mcpServers": {
    "office_py_tools_local_only": {
      "command": "pipenv",
      "args": [
        "run",
        "python",
        "-m",
        "mcp_servers.local_only.server"
      ],
      "cwd": "/home/sabamiso/workspace/office_py_tools"
    }
  }
}
```

Pipenv を使わず仮想環境内の Python を直接指定する場合:

```json
{
  "mcpServers": {
    "office_py_tools_local_only": {
      "command": "/path/to/.venv/bin/python",
      "args": [
        "-m",
        "mcp_servers.local_only.server"
      ],
      "cwd": "/home/sabamiso/workspace/office_py_tools"
    }
  }
}
```

設定後は Claude Desktop を再起動してください。

### ChatGPT

ChatGPT のカスタム MCP Connector は、現在ローカル stdio サーバーへ直接接続できません。ChatGPT から使うには、このサーバーを HTTPS で到達可能なリモート MCP サーバーとして公開する必要があります。

現状の `mcp_servers.local_only.server` はローカル stdio 起動用です。ChatGPT 向けに使う場合は、別途 Streamable HTTP / SSE などのリモート公開用エントリポイントを追加し、公開 URL を ChatGPT の Connectors 設定に登録してください。

ChatGPT 側の設定手順:

1. ChatGPT の Settings で Connectors / Developer mode を有効にする。
2. Custom connector として、公開済みのリモート MCP サーバー URL を登録する。
3. Connectors タブで接続し、チャットの Tools / Use connectors から有効化する。

Responses API からリモート MCP サーバーを試す場合の設定例:

```json
{
  "type": "mcp",
  "server_label": "office_py_tools_local_only",
  "server_url": "https://example.com/mcp",
  "allowed_tools": [
    "get_japanese_date_info"
  ],
  "require_approval": "never"
}
```

ChatGPT の Custom Connector は OpenAI によって検証されたものではないため、公開 URL、認証、ログ、取り扱うデータの範囲を確認してから接続してください。

## 実装方針

- MCP 専用機能は `mcp_servers/local_only/tools/` に追加する。
- CLI としても使いたい機能は `mytools/` に置き、必要が出るまで MCP へ公開しない。
- 実ファイルを変更する MCP ツールを追加する場合は、既定を dry-run または確認前提にする。
- Windows 固有処理を追加する場合も、非 Windows 環境で import できる状態を維持する。

## 公開ツール

- `get_japanese_date_info`: `YYYY-MM-DD` の日付から曜日、日本の祝日名、土日判定、営業日可否を返します。

祝日判定には `jpholiday` を使います。内閣府が公表する国民の祝日データに基づくライブラリですが、将来年の春分の日・秋分の日などは公式公表前に変わる可能性があります。
