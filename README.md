# office_py_tools

## create_mail_draft の返信モード

既定の動作は従来どおり、新規メールの下書き作成です。既存メールへの返信下書きを作る場合は、Outlook で返信したいメールを 1 件だけ選択してから、YAML に `mode: reply` を指定するか、CLI で `--mode reply` を指定してください。

返信モードでは `body` が必須、`attachments` が任意です。宛先と件名は Outlook の返信作成処理に任せるため、`to` と `subject` は不要です。

```yaml
mode: reply
body: |
  返信本文
attachments:
  - ./path/to/file.pdf
```

実行例:

```powershell
.\scripts\create_mail_draft.ps1 .\reply.yaml
.\scripts\create_mail_draft.ps1 .\reply.yaml --reply-all
```

`mode: reply` を YAML に書かない場合は、CLI で明示できます。

```powershell
.\scripts\create_mail_draft.ps1 .\reply.yaml --mode reply
```

返信対象の指定方法は現在 `selected` のみです。Outlook で複数アイテムを選択している場合や、メール以外を選択している場合はエラーにします。

Office 関連の作業を Python で補助するための小さな CLI ツール群です。

現在は次のツールを提供しています。順次追加を予定しています。

- YAML のメール定義から Outlook の下書きを作成するツール
- 複数ファイルのファイル名を一括変更するツール

## 動作環境

- Python 3.10
- Windows PowerShell、または POSIX 互換 shell
- 依存パッケージ
    - `PyYAML`
    - `pywin32`（Windows のみ）

Outlook 下書き作成ツールは Windows、Microsoft Outlook、`pywin32`、Outlook COM を前提にしています。Linux、macOS、WSL では Outlook COM を利用できないため、Outlook 下書き作成の実動作確認はできません。

## セットアップ

### 1. リポジトリへ移動

```powershell
cd "C:\path\to\py_tools"
```

以降のコマンドは、プロジェクトルートで実行する前提です。

### 2. Python バージョンを確認

```powershell
python --version
```

Python 3.10 系が使われていることを確認してください。

### 3. Windows で Python パッケージをインストールする参考手順

Windows では、Python インストール時に `py` ランチャーが利用できる場合があります。複数バージョンの Python が入っている環境では、次のように Python 3.10 を指定して `pip` を実行できます。

```powershell
py -3.10 -m pip --version
py -3.10 -m pip install -r requirements.txt
```

`python` コマンドが Python 3.10 を指している環境では、次の形式でも同じ依存パッケージをインストールできます。

```powershell
python -m pip install -r requirements.txt
```

このプロジェクトを直接利用するだけであれば、通常は `requirements.txt` からインストールすれば十分です。個別にインストールする場合は、次のパッケージが必要です。

```powershell
python -m pip install PyYAML
python -m pip install pywin32
```

`pywin32` は Windows + Outlook 連携で使用します。Windows 以外では `requirements.txt` の条件指定により `pywin32` はインストール対象外になります。

プロジェクトごとに依存関係を分けたい場合は、標準の仮想環境を作成してからインストールできます。

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

PowerShell の実行ポリシーにより仮想環境の有効化が止まる場合は、組織や端末の運用ルールに従って設定を確認してください。

### 4. 開発環境を用意する場合

Pipenv を使う場合は、開発用依存も含めてインストールします。

```powershell
pipenv install --dev
```

Python コマンドを Pipenv 環境内で実行する場合は、次のように `pipenv run` を付けます。

```powershell
pipenv run python -m compileall mytools
```

### 5. Pipenv を使わない実行環境を用意する場合

実行時依存だけをインストールします。

```powershell
python -m pip install -r requirements.txt
```

## ツール 1: Outlook 下書き作成

YAML ファイルに定義した宛先、件名、本文、添付ファイルから Outlook のメール下書きを作成します。

### YAML の形式

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
  - C:\path\to\file.pdf
```

必須項目:

- `to`: 1 件以上の文字列配列
- `subject`: 文字列
- `body`: 文字列

任意項目:

- `cc`: 文字列配列。省略時は空配列
- `bcc`: 文字列配列。省略時は空配列
- `attachments`: 文字列配列。省略時は空配列

添付ファイルは、存在する通常ファイルである必要があります。現行実装では、`attachments` の相対パスは Python プロセスのカレントディレクトリ基準で解釈されます。ラッパースクリプト利用時はプロジェクトルートへ移動してから Python を実行するため、添付ファイルには絶対パスを指定するのが確実です。

### PowerShell ラッパーで実行

```powershell
.\scripts\create_mail_draft.ps1 .\mail.yaml
```

下書きを画面表示せず Outlook の下書きへ保存する場合:

```powershell
.\scripts\create_mail_draft.ps1 .\mail.yaml --no-show
```

### POSIX shell ラッパーで実行

```sh
./scripts/create_mail_draft.sh ./mail.yaml
```

下書きを画面表示せず Outlook の下書きへ保存する場合:

```sh
./scripts/create_mail_draft.sh ./mail.yaml --no-show
```

### Python モジュールとして直接実行

```powershell
python -m mytools.create_mail_draft --yaml-path .\mail.yaml --cwd (Get-Location).Path
```

Pipenv 環境で実行する場合:

```powershell
pipenv run python -m mytools.create_mail_draft --yaml-path .\mail.yaml --cwd (Get-Location).Path
```

## ツール 2: ファイル名一括変更

複数ファイルに対して、次の 3 種類のリネーム操作を行えます。

- `basename`: 共通のベース名と連番でリネームする
- `prefix`: ファイル名の先頭に文字列を追加する
- `suffix`: 拡張子の前に文字列を追加する

実ファイルを変更するため、事前に `--dry-run` で変更予定を確認することを推奨します。

### basename

複数ファイルを `report_01.txt`、`report_02.txt` のようにリネームします。

PowerShell:

```powershell
.\scripts\rename_files.ps1 basename report .\a.txt .\b.txt --dry-run
.\scripts\rename_files.ps1 basename report .\a.txt .\b.txt
```

POSIX shell:

```sh
./scripts/rename_files.sh basename report ./a.txt ./b.txt --dry-run
./scripts/rename_files.sh basename report ./a.txt ./b.txt
```

Python モジュールとして直接実行:

```powershell
python -m mytools.rename_files --cwd (Get-Location).Path --operation basename --base-name report --path .\a.txt --path .\b.txt --dry-run
```

主なオプション:

- `--start <数値>`: 連番の開始値。既定値は `1`
- `--padding <桁数>`: 連番のゼロ埋め桁数。未指定時は複数ファイルの場合に自動設定
- `--separator <文字列>`: ベース名と連番の区切り文字。既定値は `_`

例:

```powershell
.\scripts\rename_files.ps1 basename report .\a.txt .\b.txt --start 3 --padding 3 --separator -
```

この場合、`report-003.txt`、`report-004.txt` のような名前になります。

### prefix

ファイル名の先頭に文字列を追加します。

```powershell
.\scripts\rename_files.ps1 prefix old_ .\a.txt --dry-run
.\scripts\rename_files.ps1 prefix old_ .\a.txt
```

Python モジュールとして直接実行:

```powershell
python -m mytools.rename_files --cwd (Get-Location).Path --operation prefix --prefix old_ --path .\a.txt --dry-run
```

### suffix

拡張子の前に文字列を追加します。

```powershell
.\scripts\rename_files.ps1 suffix _done .\a.txt --dry-run
.\scripts\rename_files.ps1 suffix _done .\a.txt
```

Python モジュールとして直接実行:

```powershell
python -m mytools.rename_files --cwd (Get-Location).Path --operation suffix --suffix _done --path .\a.txt --dry-run
```

### 上書きについて

変更後のファイル名がすでに存在する場合、既定ではエラーになります。既存ファイルを上書きする場合だけ `--overwrite` を指定してください。

```powershell
.\scripts\rename_files.ps1 prefix old_ .\a.txt --overwrite
```

## パス指定の考え方

ラッパースクリプトは、呼び出し元のカレントディレクトリを Python 側へ `--cwd` として渡します。そのため、メール YAML のパスやリネーム対象ファイルのパスは、基本的にコマンドを実行したディレクトリからの相対パスとして指定できます。

例:

```powershell
cd C:\work
C:\path\to\py_tools\scripts\rename_files.ps1 prefix old_ .\a.txt --dry-run
```

この場合、`.\a.txt` は `C:\work\a.txt` として解釈されます。

ただし、Outlook 下書き作成ツールの YAML 内に書く `attachments` は、現行実装では `--cwd` による解決対象ではありません。添付ファイルは絶対パスで指定することを推奨します。

## 動作確認

構文チェック:

```powershell
python -m compileall mytools
```

Pipenv 環境を使う場合:

```powershell
pipenv run python -m compileall mytools
```

ファイル名一括変更の動作確認:

```powershell
New-Item -ItemType File .\a.txt
New-Item -ItemType File .\b.txt
.\scripts\rename_files.ps1 basename report .\a.txt .\b.txt --dry-run
```

Outlook 下書き作成の実動作確認は、Windows、Outlook、`pywin32` が利用できる環境で行ってください。

## 既知の注意点

- 一部の Python ファイルや shell スクリプト内の日本語メッセージに文字化けがあります。ツールの利用手順は、この README のコマンド例を参照してください。
- Outlook 下書き作成は Outlook COM に依存するため、Windows 以外では実行できません。
- `Pipfile` は Python 3.10 を前提にしています。Python 3.11 以上を前提にした変更を行う場合は、互換性を確認してください。
