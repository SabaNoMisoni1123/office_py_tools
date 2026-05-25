# office_py_tools

Office 関連の作業を Python で補助するための小さな CLI ツール群です。

現在は次の機能を提供しています。

- YAML のメール定義から Outlook の下書きを作成する
- Outlook で選択中のメールへの返信下書きを作成する
- 複数ファイルのファイル名を一括変更する
- PDF の各ページを PNG 画像へ変換する
- 2 つの PDF をページごとに画像比較し、差分 PNG を出力する
- AI クライアント向けのローカル MCP サーバーで日本の曜日・祝日情報を返す

## 動作環境

- Python 3.10 以上
- Windows PowerShell、または POSIX 互換 shell
- 依存パッケージ
    - `PyYAML`
    - `PyMuPDF`
    - `jpholiday`
    - `mcp`
    - `pywin32`（Windows のみ）

Outlook 下書き作成ツールは Windows、Microsoft Outlook、`pywin32`、Outlook COM を前提にしています。Linux、macOS、WSL では Outlook COM を利用できないため、Outlook 下書き作成の実動作確認はできません。

PDF 変換と PDF 比較には `PyMuPDF` を使います。

MCP サーバーには `mcp` と `jpholiday` を使います。詳細は [mcp_servers/README.md](mcp_servers/README.md) と [mcp_servers/local_only/README.md](mcp_servers/local_only/README.md) を参照してください。

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

Python 3.10 以上が使われていることを確認してください。`Pipfile` は Python 3.10 を前提にしています。

### 3. Windows で Python パッケージをインストールする参考手順

Windows では、Python インストール時に `py` ランチャーが利用できる場合があります。複数バージョンの Python が入っている環境では、次のように Python 3.10 を指定して `pip` を実行できます。

```powershell
py -3.10 -m pip --version
py -3.10 -m pip install -r requirements.txt
```

`python` コマンドが利用したい Python を指している環境では、次の形式でも同じ依存パッケージをインストールできます。

```powershell
python -m pip install -r requirements.txt
```

このプロジェクトを直接利用するだけであれば、通常は `requirements.txt` からインストールすれば十分です。個別にインストールする場合は、主に次のパッケージが必要です。

```powershell
python -m pip install PyYAML PyMuPDF jpholiday mcp
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
pipenv run python -m compileall mytools mcp_servers
```

### 5. Pipenv を使わない実行環境を用意する場合

実行時依存だけをインストールします。

```powershell
python -m pip install -r requirements.txt
```

editable install して MCP 用の console script を使う場合は、次のようにインストールします。

```powershell
python -m pip install -e .
```

## ツール 1: Outlook 下書き作成

YAML ファイルに定義した宛先、件名、本文、添付ファイルから Outlook のメール下書きを作成します。

### 新規メールの YAML

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
- `mode`: `new` または `reply`。省略時は `new`

添付ファイルは、存在する通常ファイルである必要があります。ラッパースクリプトまたは `--cwd` を使って実行する場合、YAML 内の `attachments` の相対パスはコマンドを実行したディレクトリ基準で解釈されます。

### 返信メールの YAML

既存メールへの返信下書きを作る場合は、Outlook で返信したいメールを 1 件だけ選択してから、YAML に `mode: reply` を指定するか、CLI で `--mode reply` を指定してください。

返信モードでは `body` が必須、`attachments` が任意です。宛先と件名は Outlook の返信作成処理に任せるため、`to` と `subject` は不要です。

```yaml
mode: reply
body: |
  返信本文
attachments:
  - ./path/to/file.pdf
```

全員に返信する場合は、YAML に `reply_all: true` を指定できます。

```yaml
mode: reply
reply_all: true
body: |
  返信本文
```

返信対象の指定方法は現在 `selected` のみです。Outlook で複数アイテムを選択している場合や、メール以外を選択している場合はエラーになります。

### PowerShell ラッパーで実行

```powershell
.\scripts\create_mail_draft.ps1 .\mail.yaml
```

下書きを画面表示せず Outlook の下書きへ保存する場合:

```powershell
.\scripts\create_mail_draft.ps1 .\mail.yaml --no-show
```

返信モードを CLI で明示する場合:

```powershell
.\scripts\create_mail_draft.ps1 .\reply.yaml --mode reply
.\scripts\create_mail_draft.ps1 .\reply.yaml --mode reply --reply-all
```

### POSIX shell ラッパーで実行

```sh
./scripts/create_mail_draft.sh ./mail.yaml
./scripts/create_mail_draft.sh ./mail.yaml --no-show
```

### Python モジュールとして直接実行

```powershell
python -m mytools.create_mail_draft --yaml-path .\mail.yaml --cwd (Get-Location).Path
python -m mytools.create_mail_draft --yaml-path .\reply.yaml --cwd (Get-Location).Path --mode reply
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

## ツール 3: PDF を PNG へ変換

PDF の全ページを PNG 画像に変換します。既定の出力先は、PDF と同じ場所に作られる `img_<PDF名>` ディレクトリです。

PowerShell:

```powershell
.\scripts\pdf2png.ps1 .\sample.pdf --dry-run
.\scripts\pdf2png.ps1 .\sample.pdf
```

出力先や画質を指定する場合:

```powershell
.\scripts\pdf2png.ps1 .\sample.pdf --output-dir .\images --quality high
```

Python モジュールとして直接実行:

```powershell
python -m mytools.pdf_to_png --cwd (Get-Location).Path --pdf-path .\sample.pdf --dry-run
```

主なオプション:

- `--quality <low|medium|high>`: 変換品質。`low=150DPI`、`medium=300DPI`、`high=600DPI`。既定値は `medium`
- `--output-dir <dir>`: PNG 画像の出力先ディレクトリ
- `--dry-run`: 実際には作成せず、作成予定の PNG ファイルを表示する
- `--overwrite`: 出力先 PNG が既に存在する場合に上書きする

## ツール 4: PDF 比較

2 つの PDF をページごとに画像化して比較し、差分があるページの PNG を出力します。既定の出力先は、比較元 PDF と同じ場所に作られる `diff_<left>__<right>` ディレクトリです。差分画像は `diff_pages` 配下に出力されます。

PowerShell:

```powershell
.\scripts\compare_pdfs.ps1 .\old.pdf .\new.pdf
```

画質、許容差、出力先を指定する場合:

```powershell
.\scripts\compare_pdfs.ps1 .\old.pdf .\new.pdf --quality high --threshold 5 --output-dir .\pdf_diff
```

Python モジュールとして直接実行:

```powershell
python -m mytools.compare_pdfs --cwd (Get-Location).Path --left-pdf .\old.pdf --right-pdf .\new.pdf
```

主なオプション:

- `--quality <low|medium|high>`: 比較時の画像化品質。`low=150DPI`、`medium=300DPI`、`high=600DPI`。既定値は `medium`
- `--threshold <0-255>`: RGB 各チャンネルの差分許容値。`0` は完全一致比較
- `--output-dir <dir>`: 差分画像の出力先ディレクトリ
- `--overwrite`: 出力先 PNG が既に存在する場合に上書きする

終了コード:

- `0`: 差分なし
- `1`: 差分あり
- `2`: 実行エラー

## ツール 5: ローカル MCP サーバー

`mcp_servers/local_only` には、AI クライアントからローカル stdio MCP サーバーとして利用するための機能があります。現在は `get_japanese_date_info` ツールを公開しています。

`get_japanese_date_info` は `YYYY-MM-DD` の日付から、曜日、日本の祝日名、休日判定、営業日可否を返します。

Pipenv を使う場合:

```powershell
pipenv run python -m mcp_servers.local_only.server
```

Pipenv を使わない場合:

```powershell
python -m mcp_servers.local_only.server
```

editable install 済みの場合:

```powershell
office-py-tools-mcp-local-only
```

Claude Desktop や Codex 向けの設定例を生成する場合:

```powershell
python -m mcp_servers.local_only.generate_client_config --client claude --runner pipenv
python -m mcp_servers.local_only.generate_client_config --client codex --runner pipenv
```

editable install 済みの場合は、次のコマンドでも設定例を生成できます。

```powershell
office-py-tools-mcp-config --client codex --runner python
```

クライアントごとの詳しい設定は [mcp_servers/local_only/README.md](mcp_servers/local_only/README.md) を参照してください。

## パス指定の考え方

ラッパースクリプトは、呼び出し元のカレントディレクトリを Python 側へ `--cwd` として渡します。そのため、メール YAML のパス、YAML 内の添付ファイル、リネーム対象ファイル、PDF ファイル、出力先ディレクトリは、基本的にコマンドを実行したディレクトリからの相対パスとして指定できます。

例:

```powershell
cd C:\work
C:\path\to\py_tools\scripts\rename_files.ps1 prefix old_ .\a.txt --dry-run
```

この場合、`.\a.txt` は `C:\work\a.txt` として解釈されます。

## 動作確認

構文チェック:

```powershell
python -m compileall mytools mcp_servers
```

Pipenv 環境を使う場合:

```powershell
pipenv run python -m compileall mytools mcp_servers
```

ファイル名一括変更の動作確認:

```powershell
New-Item -ItemType File .\a.txt
New-Item -ItemType File .\b.txt
.\scripts\rename_files.ps1 basename report .\a.txt .\b.txt --dry-run
```

PDF 変換の動作確認:

```powershell
.\scripts\pdf2png.ps1 .\sample.pdf --dry-run
```

Outlook 下書き作成の実動作確認は、Windows、Outlook、`pywin32` が利用できる環境で行ってください。

## 既知の注意点

- Outlook 下書き作成は Outlook COM に依存するため、Windows 以外では実行できません。
- PDF 変換と PDF 比較は PDF のページを画像化して処理します。`--quality high` は出力画像が大きくなり、処理時間も長くなります。
- PDF 比較は画像比較のため、見た目が同じであれば内部構造の違いは検出しません。
- `Pipfile` は Python 3.10 を前提にしています。Python 3.11 以上で使う場合は、依存パッケージの互換性を確認してください。
