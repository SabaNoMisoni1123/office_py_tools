# Codex Commands

このプロジェクトでよく使うコマンドです。

## 状態確認

```sh
git status --short --branch
```

```sh
find mytools scripts -type f | sort
```

```sh
rg "python -m mytools|PYTHON_ARGS|PythonArgs" scripts mytools .codex AGENTS.md
```

## セットアップ

開発環境:

```sh
pipenv install --dev
```

Pipenv を使わない実行環境:

```sh
python -m pip install -r requirements.txt
```

## Outlook 下書き作成

開発環境:

```sh
pipenv run python -m mytools.create_mail_draft --yaml-path ./mytools/test/test.yaml --cwd "$PWD"
```

Pipenv を使わない実行環境:

```sh
python -m mytools.create_mail_draft --yaml-path ./mytools/test/test.yaml --cwd "$PWD"
```

ラッパー:

```sh
./scripts/create_mail_draft.sh ./mytools/test/test.yaml
```

```powershell
.\scripts\create_mail_draft.ps1 .\mytools\test\test.yaml
```

## ファイル名一括変更

Python へ直接渡す場合は、必ず名前付き引数を使います。
複数ファイルを渡す場合は `--path` を繰り返します。

ベースネーム変更:

```sh
python -m mytools.rename_files --cwd "$PWD" --operation basename --base-name report --path ./a.txt --path ./b.txt --dry-run
```

プレフィックス追加:

```sh
python -m mytools.rename_files --cwd "$PWD" --operation prefix --prefix old_ --path ./a.txt --dry-run
```

サフィックス追加:

```sh
python -m mytools.rename_files --cwd "$PWD" --operation suffix --suffix _done --path ./a.txt --dry-run
```

連番の開始番号、桁数、区切り文字を指定:

```sh
python -m mytools.rename_files --cwd "$PWD" --operation basename --base-name report --path ./a.txt --path ./b.txt --start 10 --padding 3 --separator - --dry-run
```

既存ファイルを上書き:

```sh
python -m mytools.rename_files --cwd "$PWD" --operation prefix --prefix old_ --path ./a.txt --overwrite
```

Bash ラッパー:

```sh
./scripts/rename_files.sh basename report ./a.txt ./b.txt --dry-run
```

```sh
./scripts/rename_files.sh prefix old_ ./a.txt --dry-run
```

```sh
./scripts/rename_files.sh suffix _done ./a.txt --dry-run
```

PowerShell ラッパー:

```powershell
.\scripts\rename_files.ps1 basename report .\a.txt .\b.txt --dry-run
```

```powershell
.\scripts\rename_files.ps1 prefix old_ .\a.txt --dry-run
```

```powershell
.\scripts\rename_files.ps1 suffix _done .\a.txt --dry-run
```

## ラッパー実装確認

ラッパーから Python を呼ぶ場合は、位置引数を直接転送せず、名前付き引数へ変換します。
`"$@"` や `@CliArgs` を Python コマンドへ直接渡していないか確認します。

```sh
rg '"\\$@"|@CliArgs|python -m mytools' scripts
```

`rename_files` ラッパーは `PYTHON_ARGS` / `$PythonArgs` に名前付き引数を組み立てます。

```sh
rg "PYTHON_ARGS|PythonArgs|--operation|--path" scripts/rename_files.*
```

## 構文確認

開発環境:

```sh
pipenv run python -m compileall mytools
```

Pipenv を使わない環境:

```sh
python -m compileall mytools
```

この環境で `.python-version` の Python が未導入の場合は、利用可能な pyenv バージョンを明示します。

```sh
PYENV_VERSION=3.13.3 PYTHONDONTWRITEBYTECODE=1 python -m compileall mytools
```

## テスト

現時点ではテストフレームワークが未導入です。
`pytest` を導入した場合は以下を標準コマンドにしてください。

```sh
pipenv run pytest
```

## Dry-run 動作確認

実ファイルを変更しない確認:

```sh
PYENV_VERSION=3.13.3 PYTHONDONTWRITEBYTECODE=1 python -m mytools.rename_files --cwd "$PWD" --operation basename --base-name sample --path mytools/__init__.py --path mytools/common/__init__.py --dry-run
```

ラッパー経由:

```sh
PYENV_VERSION=3.13.3 PYTHONDONTWRITEBYTECODE=1 ./scripts/rename_files.sh suffix _done mytools/__init__.py --dry-run
```
