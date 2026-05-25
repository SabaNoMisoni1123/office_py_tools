# local_only MCP server

AI クライアントからローカル stdio MCP サーバーとして利用するための最小サーバーです。

このサーバーは既存 CLI の機能をそのまま公開しません。MCP 専用のツール、リソース、プロンプトを追加するときだけ、この配下へ実装します。

## 起動

Pipenv を使う場合:

```sh
pipenv run python -m mcp_servers.local_only.server
```

Pipenv を使わない場合:

```sh
python -m mcp_servers.local_only.server
```

editable install 済みの場合:

```sh
office-py-tools-mcp-local-only
```

## クライアント設定

設定例では `<REPOSITORY_ROOT>` を利用者が clone したプロジェクトルートに置き換えてください。

Windows 例:

```text
C:\path\to\office_py_tools
```

macOS / Linux 例:

```text
/path/to/office_py_tools
```

設定例は `examples/` に置いています。

- `examples/claude_desktop_config.pipenv.example.json`
- `examples/claude_desktop_config.python.example.json`
- `examples/codex_config.pipenv.example.toml`
- `examples/codex_config.python.example.toml`

従来の場所を参照している利用者向けに、`client_config.example.json` も残しています。ただし固有端末の絶対パスは含めず、`<REPOSITORY_ROOT>` のプレースホルダーを使います。

### 設定生成 CLI

現在の作業ディレクトリをプロジェクトルートとして、設定ファイルを生成できます。

Claude Desktop 用:

```sh
python -m mcp_servers.local_only.generate_client_config --client claude --runner pipenv
```

Codex 用:

```sh
python -m mcp_servers.local_only.generate_client_config --client codex --runner pipenv
```

出力先を指定する場合:

```sh
python -m mcp_servers.local_only.generate_client_config --client claude --runner python --output claude_desktop_config.json
```

editable install 済みの場合は、次のコマンドでも同じ生成 CLI を使えます。

```sh
office-py-tools-mcp-config --client codex --runner python
```

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
cwd = "<REPOSITORY_ROOT>"
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
      "cwd": "<REPOSITORY_ROOT>"
    }
  }
}
```

設定後は Claude Desktop を再起動してください。

### ChatGPT

ChatGPT のカスタム MCP Connector は、現在ローカル stdio サーバーへ直接接続できません。ChatGPT から使うには、このサーバーを HTTPS で到達可能なリモート MCP サーバーとして公開するための別エントリポイントが必要です。

現在の `mcp_servers.local_only.server` はローカル stdio 起動用です。ChatGPT 向けに使う場合は、別途 Streamable HTTP / SSE などのリモート公開用エントリポイントを追加し、公開 URL を ChatGPT の Connectors 設定に登録してください。

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

公開 URL、認証、ログ、取り扱うデータの範囲を確認してから接続してください。

## 実装方針

- MCP 専用機能は `mcp_servers/local_only/tools/` に追加する。
- CLI としても使いたい汎用機能は `mytools/` に置き、必要が出るまで MCP へ公開しない。
- 実ファイルを変更する MCP ツールを追加する場合は、既定を dry-run または確認前提にする。
- Windows 固有処理を追加する場合も、非 Windows 環境で import できる状態を維持する。

## 公開ツール

- `get_japanese_date_info`: `YYYY-MM-DD` の日付から曜日、日本の祝日名、休日判定、営業日可否を返します。

祝日判定には `jpholiday` を使います。内閣府が公表する国民の祝日データに基づくライブラリですが、将来年の春分の日・秋分の日などは公式発表前に変わる可能性があります。
