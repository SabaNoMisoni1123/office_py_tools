# Codex Project Context

このファイルは Codex などのエージェントが、作業前提を素早く把握するための補助メモです。
詳細な運用ルールはリポジトリルートの `AGENTS.md` を優先してください。

## 要約

`office_py_tools` は、Office 作業を補助する Python ツール群です。
現時点では、YAML ファイルに定義された宛先、件名、本文、添付ファイルを読み取り、Outlook のメール下書きを作成する機能が中心です。
加えて、複数ファイルのファイル名を一括変更する CLI も提供します。

## 重要な制約

- Python 3.10 を前提にする。
- 開発時の依存管理は Pipenv。
- 最終運用では仮想環境を使わない想定のため、実行時依存は `requirements.txt` にも記載する。
- `pywin32` は Windows のみ。
- Outlook 操作は Windows + Outlook の COM 環境でのみ動作する。
- 非 Windows 環境では Outlook 実操作を避け、パースや検証ロジックをテストする。
- 回答と説明は日本語。
- ラッパースクリプトから Python を呼ぶ場合は、位置引数を直接転送せず、必ず名前付き引数に変換して渡す。

## 主要ファイル

- `Pipfile`: Python と依存パッケージの定義
- `requirements.txt`: 最終運用環境向けの実行時依存
- `mytools/create_mail_draft.py`: CLI
- `mytools/rename_files.py`: ファイル名一括変更 CLI
- `mytools/jobs/mail_draft_creator.py`: メール定義の解析と Outlook 操作
- `mytools/common/file_renamer.py`: ファイル名変更の共通ロジック
- `mytools/common/arg_path.py`: CLI パス解決
- `mytools/common/file_utils.py`: ファイル存在確認
- `mytools/common/yaml_utils.py`: YAML 読み込みと値検証
- `mytools/test/test.yaml`: サンプル YAML
- `scripts/create_mail_draft.ps1`: PowerShell ラッパー
- `scripts/create_mail_draft.sh`: shell ラッパー
- `scripts/rename_files.ps1`: ファイル名一括変更用 PowerShell ラッパー
- `scripts/rename_files.sh`: ファイル名一括変更用 Bash shell ラッパー

## よくある調査観点

- YAML 内の相対パスが、ユーザーの呼び出し元ディレクトリ基準で解決されているか。
- Windows 以外で `mytools.jobs.mail_draft_creator` を import できるか。
- `to` が空のときに分かりやすいエラーになるか。
- `attachments` の存在確認が正しい基準ディレクトリで行われているか。
- PowerShell スクリプトの文字コードが UTF-8 として読めるか。
- `Pipfile` と `requirements.txt` の実行時依存がずれていないか。
- ファイル名一括変更の実行前に `--dry-run` で変更予定を確認できるか。

## 作業時の優先順位

1. 既存 CLI の互換性を保つ。
2. Windows 固有の Outlook 依存を、テスト可能なロジックから分離する。
3. エラーを日本語で分かりやすくする。
4. パス解決を一貫させる。
5. ラッパースクリプトでは Python へ渡す引数の対応関係を明確にする。
6. テストしやすい小さな関数単位に保つ。
7. コメント後を丁寧に付けることで、保守管理に資するコーディングとする。
