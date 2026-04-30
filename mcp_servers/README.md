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
    tools/
```

`local_only` は、今後 MCP 専用プログラムを追加するための最小サーバーです。現時点では業務機能を登録していません。

## 依存管理

MCP サーバー実装には Python SDK の `mcp` パッケージを使います。開発環境では Pipenv で管理します。

```sh
pipenv install --dev
```

Pipenv を使わない実行環境では、既存方針どおり `requirements.txt` からインストールします。

```sh
python -m pip install -r requirements.txt
```

Pipenv で管理すること自体に大きな問題はありません。ただし、AI クライアントが MCP サーバーを起動するときに `pipenv` コマンドへ PATH が通っていない環境では起動に失敗します。その場合は次のいずれかで対応してください。

- クライアント設定の `command` に `pipenv` の絶対パスを指定する。
- `pipenv --venv` で仮想環境の場所を確認し、仮想環境内の `python` を `command` に指定する。
- 運用環境では `python -m pip install -r requirements.txt` で通常環境へ依存を入れ、`python -m mcp_servers.local_only.server` で起動する。
