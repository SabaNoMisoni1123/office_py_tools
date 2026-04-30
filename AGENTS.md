# AGENTS.md

このリポジトリで作業するエージェント向けの前提条件と運用ルールです。
回答、コメント、説明は原則として日本語で行ってください。

## プロジェクト概要

- プロジェクト名: `office_py_tools`
- 目的: Office 関連の作業を Python で補助するための小さなツール群
- 現在の主機能: YAML のメール定義から Outlook の下書きを作成する CLI
- 追加機能: 複数ファイルのファイル名を一括変更する CLI
- 追加予定: Codex などの AI クライアントから使うローカル MCP サーバー
- 主なコード:
  - `mytools/create_mail_draft.py`: CLI エントリポイント
  - `mytools/rename_files.py`: ファイル名一括変更 CLI
  - `mytools/jobs/mail_draft_creator.py`: Outlook 下書き作成ロジック
  - `mytools/common/`: パス、ファイル、YAML、リネーム関連の共通処理
  - `mcp_servers/`: MCP サーバーからのみ使う AI 向けローカル機能
  - `scripts/create_mail_draft.ps1`: Windows PowerShell 向け起動スクリプト
  - `scripts/create_mail_draft.sh`: POSIX shell 向け起動スクリプト
  - `scripts/rename_files.ps1`: ファイル名一括変更用 PowerShell ラッパー
  - `scripts/rename_files.sh`: ファイル名一括変更用 Bash shell ラッパー

## 実行環境の前提

- Python は `Pipfile` に合わせて 3.10 を前提にしてください。
- 依存管理は Pipenv を前提にしてください。
- YAML 読み込みには `PyYAML` を使います。
- Outlook 連携は Windows + Outlook + `pywin32` + COM を前提にしています。
- Linux/macOS/WSL では Outlook COM が使えないため、Outlook 連携部分の実動作確認はできません。
- Windows 以外で検証する場合は、YAML パース、入力検証、パス解決、COM オブジェクトのモックテストを中心にしてください。

## 仮想環境

- 開発時は Pipenv を用いた仮想環境によってパッケージを管理します。
- 最終的には仮想環境を使わない運用を想定しています。
- 実行環境向けの依存は `requirements.txt` にも記載します。
- 依存を追加、削除、更新する場合は、`Pipfile` と `requirements.txt` の整合性を確認してください。
- ラッパーとなる PowerShell スクリプトや shell スクリプトは、Pipenv を使わず `python` コマンドから始まるコマンド設計とします。
- 開発用依存は `Pipfile` の `[dev-packages]` に限定し、`requirements.txt` には実行時依存のみを記載してください。

## セットアップ

開発環境:

```sh
pipenv install --dev
```

最終運用環境、または Pipenv を使わない環境:

```sh
python -m pip install -r requirements.txt
```

Windows で Outlook 下書き作成を開発環境から実行する場合:

```powershell
pipenv run python -m mytools.create_mail_draft --yaml-path .\mytools\test\test.yaml --cwd (Get-Location).Path
```

PowerShell ラッパーを使う場合:

```powershell
.\scripts\create_mail_draft.ps1 .\mytools\test\test.yaml
```

POSIX shell ラッパーを使う場合:

```sh
./scripts/create_mail_draft.sh ./mytools/test/test.yaml
```

ファイル名一括変更 CLI の例:

```sh
python -m mytools.rename_files --cwd "$PWD" --operation basename --base-name report --path ./a.txt --path ./b.txt --dry-run
python -m mytools.rename_files --cwd "$PWD" --operation prefix --prefix old_ --path ./a.txt
python -m mytools.rename_files --cwd "$PWD" --operation suffix --suffix _done --path ./a.txt
```

MCP サーバーの開発起動例:

```sh
pipenv run python -m mcp_servers.local_only.server
```

AI クライアント向けの stdio サーバーとして使う場合も、原則として同じ Python モジュールを起動してください。

## YAML メール定義

基本形式:

```yaml
to:
  - user@example.com
cc:
  - cc@example.com
bcc:
  - bcc@example.com
subject: |
  件名
body: |
  本文
attachments:
  - ./path/to/file.pdf
```

必須項目:

- `to`: 1 件以上の文字列配列
- `subject`: 文字列
- `body`: 文字列

任意項目:

- `cc`: 文字列配列。省略時は空配列
- `bcc`: 文字列配列。省略時は空配列
- `attachments`: 文字列配列。省略時は空配列

## 既知の注意点

- `mytools/common/arg_path.py` のコメントには Python 3.11+ と書かれていますが、`Pipfile` は Python 3.10 指定です。修正時は Python 3.10 互換を優先してください。
- `scripts/create_mail_draft.ps1` の表示文字列は文字化けしている可能性があります。編集時は UTF-8 に統一してください。
- 現状、テストフレームワークは明示的に導入されていません。テストを追加する場合は `pytest` の導入を検討してください。
- Outlook COM に依存する処理は直接実行せず、可能な限りモックで検証してください。
- ラッパースクリプトはプロジェクトルートへ移動してから Python を起動します。相対パスの基準が変わる不具合に注意してください。
- 相対パスの解決方法として、Python スクリプト実行時にラッパーからコマンド実行したディレクトリを `--cwd` 引数で渡すこととします。

## ラッパースクリプト設計方針

- PowerShell スクリプトや shell スクリプトは、利用者向けの入力を受け取ったうえで、Python スクリプトへ渡す引数を明示的に組み立ててください。
- ラッパーから Python スクリプトを呼び出すときは、位置引数をそのまま転送しないでください。
- Python スクリプトへ渡す実行時引数は、必ず `--cwd`、`--yaml-path`、`--operation`、`--base-name`、`--path` のような名前付き引数にしてください。
- 複数値を渡す場合は、`--path file1 --path file2` のように、各値の直前に対応する引数名を繰り返してください。
- ラッパー内では、Python へ渡す引数配列を `PYTHON_ARGS` や `$PythonArgs` のような専用変数に組み立て、どの入力がどの Python 引数に対応するかを読める状態にしてください。
- `"$@"` や `@CliArgs` を Python コマンドへ直接渡す実装は避けてください。使う場合でも、事前に解析して名前付き引数へ変換してください。
- 新しい CLI を作る場合、Python 側もラッパーから名前付き引数だけで呼び出せるインターフェースを用意してください。

## MCP サーバー設計方針

- MCP サーバーからのみ利用する新規機能は `mcp_servers/` 配下に置いてください。
- 既存の CLI は、明示的な要件がない限り MCP ツールとして公開しないでください。
- `mytools/` は人がコマンドラインから実行する CLI と共通処理の置き場、`mcp_servers/` は AI クライアント向け stdio MCP サーバーの置き場として分離してください。
- MCP 専用機能を追加する場合は、`mcp_servers/<server_name>/tools/` のようにサーバー単位で分けてください。
- 実ファイルを変更する MCP ツールを追加する場合は、既定を dry-run または確認前提にしてください。
- MCP サーバーの依存は Pipenv で管理し、実行時に必要な依存は `requirements.txt` にも記載してください。

## コーディング方針

- 既存の構成を尊重し、変更範囲を必要最小限にしてください。
- 公開 API や CLI 引数を変更する場合は、互換性への影響を明記してください。
- エラーメッセージは利用者が次に直すべき点を理解できる日本語にしてください。
- パス処理は `mytools/common/arg_path.py` のユーティリティを優先して使ってください。
- YAML の値検証は `mytools/common/yaml_utils.py` の既存関数に合わせてください。
- 添付ファイルなど外部ファイルを扱う場合は、存在確認と「ファイルであること」の確認を行ってください。
- Windows 固有処理を追加する場合は、非 Windows 環境で import できる状態を維持してください。
- ファイル名一括変更のような汎用ロジックは `mytools/common` に置き、CLI 固有の処理はトップレベルのエントリポイントに分離してください。
- 実ファイルを変更する CLI には、可能な限り `--dry-run` を用意してください。

## 検証方針

可能な範囲で以下を確認してください。

```sh
pipenv run python -m compileall mytools
```

`pytest` を導入済みの場合:

```sh
pipenv run pytest
```

依存が未インストールの環境では、少なくとも標準ライブラリだけで import できる範囲と構文を確認してください。
ただし `yaml` が未インストールの場合、YAML 関連モジュールの import は失敗します。

## Git 作業ルール

- ユーザーが明示しない限り、既存変更を勝手に戻さないでください。
- 作業前後に `git status --short --branch` を確認してください。
- 生成物、キャッシュ、仮想環境はコミット対象にしないでください。
- `Pipfile.lock` は現在リポジトリに存在しますが、`.gitignore` にも記載されています。扱いを変える場合はユーザーに確認してください。
- 依存関係を変更した場合は、`Pipfile`、`Pipfile.lock`、`requirements.txt` の扱いを明記してください。
