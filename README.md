# office_py_tools

Office 文書・PDF・表データ・メール作成を補助する Python 3.10 向けの CLI 集です。人が保守できることを優先し、CLI は `mytools/`、再利用可能な処理は `mytools/common/`、ユースケース単位の処理は `mytools/jobs/` に分離しています。

Windows と Linux の双方を対象にしています。ただし Outlook COM を使うメール下書き作成だけは Windows 専用です。

## できること

| コマンド | 用途 | 主な出力 | Windows | Linux |
| --- | --- | --- | --- | --- |
| `create_mail_draft` | YAML から Outlook の新規／返信下書きを作成 | Outlook 下書き | ○（Outlook 必須） | × |
| `generate_mail_yaml` | テンプレートからメール YAML を生成 | YAML | ○ | ○ |
| `rename_files` | ファイル名の連番化・接頭辞・接尾辞付与 | ファイル名 | ○ | ○ |
| `pdf_to_png` | PDF 全ページを PNG 化 | PNG | ○ | ○ |
| `compare_pdfs` | PDF のページ画像を比較 | 差分 PNG | ○ | ○ |
| `convert_markdown` | Markdown を HTML / PDF / docx に変換 | 文書 | ○ | ○ |
| `convert_docx_to_markdown` | docx を Markdown に変換 | Markdown・画像 | ○ | ○ |
| `audit_files` | フォルダ内のファイルを棚卸し | Markdown / JSON / CSV | ○ | ○ |
| `batch_convert` | Markdown・docx・PDF を一括変換 | 変換結果・一覧 | ○ | ○ |
| `generate_report` | CSV / xlsx から Markdown レポートを生成 | Markdown・CSV | ○ | ○ |
| `mcp_servers.local_only` | ローカル AI クライアント向け MCP サーバー | stdio MCP | ○ | ○ |

`○` は Python 依存と後述の外部プログラムを整えた場合です。PDF 関連は PyMuPDF、xlsx 読み込みは openpyxl を使います。

## 配布後のセットアップ

ここでは Python **3.10** がすでに利用できることを前提にします。必ずプロジェクトのルートで実行してください。

```powershell
cd C:\path\to\office_py_tools
py -3.10 --version
```

Linux では `py -3.10` を `python3.10` に読み替えます。

### 方法 A: 配布・利用向け（推奨）

仮想環境を作成すると、OS や案件ごとの依存関係を混ぜずに利用できます。

Windows PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux (bash):

```sh
python3.10 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` には実行時依存だけを記載しています。Windows では条件付きで `pywin32` も入ります。ソースを Python パッケージとしても使う、または MCP のコマンド名を登録したい場合は、続けて次を実行します。

```sh
python -m pip install -e .
```

### 方法 B: 開発向け（Pipenv）

Pipenv を使う場合は、リポジトリの `Pipfile` を唯一の開発環境定義として使います。

```sh
python -m pip install pipenv
pipenv --python 3.10
pipenv install --dev
pipenv run python -m compileall mytools mcp_servers
```

依存を追加・変更するときは、`Pipfile`、`pyproject.toml`、`requirements.txt` の三つを同時に確認してください。`Pipfile.lock` の扱いを変更する場合は、プロジェクトの運用ルールに従ってください。

## OS ごとの前提と機能差

### Windows

- Outlook 下書き作成には、デスクトップ版 Microsoft Outlook と、同じユーザーで利用できる Outlook プロファイルが必要です。`pywin32` 経由で COM を呼び出すため、WSL からは実行できません。
- PowerShell ラッパーは `scripts/*.ps1` です。実行ポリシーで止まる場合は、組織のルールに従ってスコープを限定して許可してください。ポリシーの恒久的な変更は不要です。
- Markdown から PDF を作る WeasyPrint は、環境によって追加のネイティブ DLL が必要になることがあります。エラー時は [WeasyPrint の公式インストール手順](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) に従ってください。

### Linux

- `create_mail_draft` は利用できません。Outlook COM は Windows のデスクトップ Outlook 専用です。メール YAML の生成だけは利用できます。
- Markdown/docx 変換には後述の Pandoc を OS のパッケージマネージャー等で別途導入します。
- WeasyPrint がライブラリ不足で起動しない場合は、ディストリビューションの Cairo、Pango、GDK-PixBuf などの依存パッケージを導入してください。必要な組合せはディストリビューションと WeasyPrint のバージョンで異なります。
- shell ラッパーを実行する前に必要なら `chmod +x scripts/*.sh` を行います。

### 共通の外部依存

`convert_markdown` と `convert_docx_to_markdown`、およびそれらを含む `batch_convert` は、Python パッケージとは別に **Pandoc** コマンドを必要とします。導入後、次で確認します。

```sh
pandoc --version
```

PDF 出力には Pandoc と WeasyPrint が必要です。`pypandoc` は Python 側から Pandoc を扱うためのパッケージであり、Pandoc 本体の代わりにはなりません。

## 実行方法の共通ルール

すべての Python CLI はモジュールとして起動します。

```sh
python -m mytools.<command> --cwd "実行時の基準ディレクトリ" ...
```

`--cwd` は相対パスを解決する基準です。ラッパーは、呼び出した場所を自動で `--cwd` に渡します。直接 Python を実行する場合は必ず明示してください。ファイルを変更・生成するコマンドは、まず `--dry-run` で計画を確認することを推奨します。

各コマンドの完全な引数は次で確認できます。

```sh
python -m mytools.rename_files --help
```

## CLI の使用例

以下の例では `.` が作業ディレクトリです。Windows ではパス区切りを `\` に読み替えて構いません。

### Outlook 下書き（Windows のみ）

```yaml
# mail.yaml
to:
  - user@example.com
subject: 件名
body: |
  本文です。
attachments:
  - ./attachment.pdf
```

```powershell
.\scripts\create_mail_draft.ps1 .\mail.yaml
# または
python -m mytools.create_mail_draft --cwd (Get-Location).Path --yaml-path .\mail.yaml
```

新規メールは `mode: new`（既定値）、Outlook で選択中のメールへの返信は `mode: reply` を YAML に指定します。返信では Outlook 上で対象メールをちょうど 1 件選択してから実行してください。

### メール YAML の生成

```sh
python -m mytools.generate_mail_yaml --cwd "$PWD" \
  --template templates/mail/sample_new.yaml --output mail.yaml \
  --var to=user@example.com --var user_name="山田太郎" --dry-run
```

`--var key=value` と `--vars-file`（YAML / JSON）でテンプレート変数を指定できます。出力するには `--dry-run` を外し、既存ファイルを置き換える場合だけ `--overwrite` を指定します。

### ファイル名の一括変更

```sh
python -m mytools.rename_files --cwd "$PWD" --operation basename \
  --base-name report --path ./a.txt --path ./b.txt --dry-run
python -m mytools.rename_files --cwd "$PWD" --operation prefix \
  --prefix old_ --path ./a.txt
python -m mytools.rename_files --cwd "$PWD" --operation suffix \
  --suffix _done --path ./a.txt
```

`basename` は複数ファイルで `report_01.txt` のように連番化します。衝突は既定でエラーになり、`--overwrite` を付けた場合だけ既存の対象を置き換えます。

### PDF の画像化・比較

```sh
python -m mytools.pdf_to_png --cwd "$PWD" --pdf-path ./sample.pdf --dry-run
python -m mytools.compare_pdfs --cwd "$PWD" \
  --left-pdf ./old.pdf --right-pdf ./new.pdf --quality high --threshold 5
```

品質は `low` (150 DPI)、`medium` (300 DPI、既定)、`high` (600 DPI) です。比較コマンドの終了コードは、差分なしが 0、差分ありが 1、実行エラーが 2 です。自動検査ではこの違いを利用できます。

### Markdown / docx の変換

```sh
python -m mytools.convert_markdown --cwd "$PWD" --input ./document.md --format html --dry-run
python -m mytools.convert_markdown --cwd "$PWD" --input ./document.md --format pdf --out-dir ./out
python -m mytools.convert_docx_to_markdown --cwd "$PWD" --input ./document.docx --output ./document.md
```

設定ファイルは `config/markdown_converter.json` と `config/docx_to_markdown.json` です。CSS、Word テンプレート、メディア抽出の設定はここで管理します。CLI 引数は設定値より優先されます。

### 棚卸し・一括変換・レポート

```sh
python -m mytools.audit_files --cwd "$PWD" --root ./docs --glob "*.md" --summary-output ./audit.md --dry-run
python -m mytools.batch_convert --cwd "$PWD" --input-dir ./docs --kind markdown --format html --output-dir ./out --dry-run
python -m mytools.generate_report --cwd "$PWD" --input ./data.csv --config ./config/report_generator.json --output ./report.md --dry-run
```

サンプル設定は `config/`、レポートテンプレートは `templates/reports/` にあります。実運用ではコピーして案件ごとの名前に変更し、リポジトリ既定の設定を直接壊さないでください。

## ラッパースクリプト

人が直接使う場合は `scripts/` のラッパーも利用できます。ラッパーは位置引数を受け取り、Python 側には名前付き引数として渡す責務を持ちます。

| 機能 | PowerShell | shell |
| --- | --- | --- |
| メール YAML / 下書き | `generate_mail_yaml.ps1`, `create_mail_draft.ps1` | `.sh` あり |
| リネーム | `rename_files.ps1` | `.sh` あり |
| PNG 化 | `pdf2png.ps1` | なし |
| PDF 比較 | `compare_pdfs.ps1` | なし |
| Markdown / docx 変換 | `convert_markdown.ps1`, `convert_docx_to_markdown.ps1` | `.sh` あり |
| 棚卸し・一括変換・レポート | `.ps1` あり | `.sh` あり |

Linux で PowerShell 専用の 2 機能を使う場合は、上記の Python モジュールを直接実行してください。

## 構成と保守方針

```text
mytools/
  <command>.py       # argparse、表示、終了コードのみを担当する CLI
  common/            # パス・PDF・Markdown・表などの再利用ライブラリ
  jobs/              # ユースケースごとの Request / Plan / 実行処理
scripts/             # OS シェル向けの薄いラッパー
config/              # 既定の JSON 設定
templates/           # メール・レポートのテンプレート
mcp_servers/         # AI クライアント用の stdio MCP サーバー
```

新機能は、まず `common/` に副作用の少ない小さなライブラリとして置き、次に `jobs/` に入力データクラス・検証・計画・実行を組み立て、最後に CLI を薄く追加してください。ファイルを変更する処理には `dry_run` と衝突検証を用意してください。Windows 固有の依存は import 時ではなく実行時に扱い、Linux 上でもモジュールを import できる状態を維持します。

## MCP サーバー

ローカル MCP サーバーは現在、日本の日付・祝日情報を返す読み取り専用ツール `get_japanese_date_info` を公開します。

```sh
python -m mcp_servers.local_only.server
python -m mcp_servers.local_only.generate_client_config --client codex --runner python
```

`pip install -e .` 済みなら `office-py-tools-mcp-local-only` と `office-py-tools-mcp-config` も使えます。生成された設定中のリポジトリパスは、配布先の絶対パスへ置き換えてください。

## 検証

変更後の最小検証は次です。

```sh
python -m compileall mytools mcp_servers
python -m mytools.rename_files --help
python -m mytools.pdf_to_png --help
```

Outlook 実連携は Windows・Outlook がある環境でのみ確認します。それ以外の OS では、YAML の検証、パス解決、PDF・変換処理、COM オブジェクトを使わないロジックを中心に検証してください。
