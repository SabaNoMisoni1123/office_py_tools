# MCP servers

このディレクトリは、Codex などの AI クライアントから MCP 経由で使うローカルサーバー専用の置き場所です。

既存の CLI アプリケーションとは用途を分けます。

- `mytools/`: 人がコマンドラインから直接実行する Python CLI
- `scripts/`: CLI 用の PowerShell / shell ラッパー
- `mcp_servers/`: MCP サーバーからのみ使う AI 向けローカル機能

既存の `mytools/` の関数を MCP ツールとして公開する前提ではありません。MCP 専用機能を追加する場合は、原則として `mcp_servers/<server_name>/` 配下に実装します。

## 現在の構成

```text
mcp_servers/
  local_only/
    server.py
    generate_client_config.py
    tools/
```

`local_only` は、MCP 専用プログラムを追加するための最小サーバーです。現在は、年月日から曜日と日本の祝日情報を返すツールを公開しています。

## 依存管理

MCP サーバーの実装には Python SDK の `mcp` パッケージを使います。開発環境では Pipenv で管理します。

```sh
pipenv install --dev
```

Pipenv を使わない実行環境では、従来どおり `requirements.txt` からインストールできます。

```sh
python -m pip install -r requirements.txt
```

配布用に editable install する場合は、`pyproject.toml` の console script も使えます。

```sh
python -m pip install -e .
office-py-tools-mcp-local-only
```

AI クライアントが MCP サーバーを起動するときに `pipenv` コマンドへ PATH が通っていない環境では、次のいずれかで対応してください。

- クライアント設定の `command` に `pipenv` の絶対パスを指定する。
- `pipenv --venv` で仮想環境の場所を確認し、仮想環境内の `python` を `command` に指定する。
- 通常環境へ `python -m pip install -r requirements.txt` または `python -m pip install -e .` で依存を入れ、`python -m mcp_servers.local_only.server` または `office-py-tools-mcp-local-only` で起動する。
