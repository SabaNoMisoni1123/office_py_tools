# 優先度 A ツール詳細仕様

作成日: 2026-05-27

更新日: 2026-05-27

## 実装状況

本仕様で定義した優先度 A の4ツールは、2026-05-27 時点で初期実装済み。

- `mytools.generate_mail_yaml`
- `mytools.audit_files`
- `mytools.batch_convert`
- `mytools.generate_report`

PowerShell / POSIX shell ラッパー、設定サンプル、テンプレートも追加済み。検証では `python -m compileall mytools mcp_servers` と主要 CLI の dry-run を確認済み。

仕様との差分:

- `generate_report` は `.xlsx` 対応のため `openpyxl` を依存に追加した。
- `batch_convert --config` は CLI 互換のため受け付けるが、初期実装では設定ファイルの内容をまだ反映していない。
- `batch_convert --no-default-css` と `--no-default-template` は引数として受け付けるが、初期実装では既定設定の読み込み自体を行っていないため実質的な効果はない。
- pytest は未導入。現時点の検証は compileall と CLI dry-run / 小規模出力確認で行っている。

## 目的

`docs/feature_expansion_plan.md` で優先度 A とした次の4ツールについて、実装前に動作仕様を定義する。

- メール YAML テンプレート生成 CLI
- ファイル棚卸し・整理計画 CLI
- PDF / docx / Markdown 変換バッチ CLI
- Excel / CSV 集計レポート生成 CLI

本仕様は、既存 CLI の設計方針に合わせ、Python 側では名前付き引数を使い、ラッパースクリプトでは位置引数を解析して名前付き引数へ変換する前提とする。

## 共通仕様

### 共通方針

- Python 3.10 互換とする。
- CLI エントリポイントは `mytools/` 直下に置く。
- 業務ロジックは `mytools/jobs/` に置く。
- 複数ツールから再利用する処理は `mytools/common/` に置く。
- パス解決は `--cwd` を基準にし、`mytools/common/arg_path.py` の既存ユーティリティを使う。
- ファイル作成、上書き、移動、リネームを伴う処理は `--dry-run` と `--overwrite` を持つ。
- dry-run では実ファイルを変更せず、入力、出力予定、処理件数、警告を表示する。
- エラーメッセージは日本語で、利用者が次に直すべき内容を含める。
- 標準出力は人間が読む簡潔な結果表示とし、機械処理用の詳細結果は `--summary-output` などでファイル出力する。

### 終了コード

既存の変換系 CLI に合わせ、原則として次の終了コードを使う。

- `0`: 正常終了
- `1`: 入力値、パス、設定ファイル、オプション組み合わせのエラー
- `2`: 処理中エラー
- `3`: 外部依存不足

バッチ処理で一部ファイルだけ失敗した場合は、処理自体は完了していても終了コード `2` とする。ただし、`--allow-partial-success` を指定した場合は終了コード `0` とし、失敗一覧をサマリへ出力する。

### 出力ファイルの上書き

- 出力先が既存で `--overwrite` がない場合はエラーにする。
- 出力先ディレクトリが存在しない場合は原則エラーにする。
- ただし、明示的に `--create-dirs` を指定した場合は親ディレクトリを作成する。
- ディレクトリ全体を削除する動作は実装しない。

### 設定ファイル

設定ファイルは JSON を基本とする。既存の `config/markdown_converter.json` と同じく、プロジェクト既定の設定ファイルを `config/` 配下へ置ける設計にする。

YAML を扱う既存機能との相性はよいが、設定ファイル形式を増やしすぎると運用が複雑になるため、初期実装では JSON を優先する。メール本文テンプレートなど、人が編集する内容は Markdown / text / YAML を許容する。

### 予定ファイル構成

```text
mytools/
  generate_mail_yaml.py
  audit_files.py
  batch_convert.py
  generate_report.py
  jobs/
    mail_yaml_generator.py
    file_auditor.py
    batch_converter.py
    report_generator.py
  common/
    templates.py
    file_inventory.py
    tabular/
      __init__.py
      reader.py
      summarizer.py
scripts/
  generate_mail_yaml.ps1
  generate_mail_yaml.sh
  audit_files.ps1
  audit_files.sh
  batch_convert.ps1
  batch_convert.sh
  generate_report.ps1
  generate_report.sh
config/
  file_audit.json
  batch_convert.json
  report_generator.json
templates/
  mail/
    sample_new.yaml
    sample_reply.yaml
  reports/
    simple_summary.md
```

## 1. メール YAML テンプレート生成 CLI

### 概要

メール文面テンプレートと変数を入力し、既存の `mytools.create_mail_draft` が読める YAML ファイルを生成する。

このツールは Outlook COM を使わない。生成した YAML を別途 `create_mail_draft` へ渡すことで Outlook 下書きを作成する。

### CLI 名

Python:

```powershell
python -m mytools.generate_mail_yaml --cwd (Get-Location).Path --template .\templates\mail\sample_new.yaml --output .\mail.yaml --var user_name=山田
```

PowerShell:

```powershell
.\scripts\generate_mail_yaml.ps1 .\templates\mail\sample_new.yaml --output .\mail.yaml --var user_name=山田
```

POSIX shell:

```sh
./scripts/generate_mail_yaml.sh ./templates/mail/sample_new.yaml --output ./mail.yaml --var user_name=山田
```

### 入力

必須引数:

- `--cwd <dir>`: 相対パス解決の基準ディレクトリ
- `--template <path>`: メールテンプレート YAML
- `--output <path>`: 生成するメール YAML

任意引数:

- `--var <key=value>`: 変数。複数指定可
- `--vars-file <path>`: 変数定義 JSON
- `--attachment <path>`: 添付ファイル。複数指定可。テンプレートの添付に追加する
- `--mode <new|reply>`: テンプレートの `mode` を上書き
- `--reply-all`: `reply_all: true` を強制
- `--dry-run`: 生成予定を表示し、ファイルを書き込まない
- `--overwrite`: 出力 YAML が既存の場合に上書き
- `--create-dirs`: 出力先の親ディレクトリがない場合に作成

### テンプレート形式

テンプレートは YAML とし、既存メール YAML の項目を拡張する。

```yaml
mode: new
to:
  - "{{to}}"
cc: []
bcc: []
subject: "【{{project_name}}】資料送付"
body: |
  {{user_name}} 様

  {{project_name}} の資料を送付します。

  よろしくお願いいたします。
attachments:
  - "{{attachment_path}}"
defaults:
  project_name: "案件名"
required_vars:
  - to
  - user_name
```

仕様:

- `{{name}}` 形式を変数プレースホルダーとする。
- `defaults` はテンプレート処理用であり、生成後 YAML には出力しない。
- `required_vars` はテンプレート処理用であり、生成後 YAML には出力しない。
- CLI の `--var` は `defaults` より優先する。
- `--vars-file` は `defaults` より優先し、`--var` より低い優先度にする。
- 未置換プレースホルダーが残る場合はエラーにする。ただし `--allow-unresolved` を将来追加する余地は残す。

### 出力

生成後 YAML は既存の `create_mail_draft` が読める形式にする。

```yaml
mode: new
to:
  - user@example.com
cc: []
bcc: []
subject: "【案件A】資料送付"
body: |
  山田 様

  案件A の資料を送付します。

  よろしくお願いいたします。
attachments:
  - C:\work\file.pdf
```

### 検証

- テンプレートファイルが存在し、通常ファイルであること。
- テンプレート YAML が辞書であること。
- `mode` は `new` または `reply`。
- `mode: new` の場合、`to`、`subject`、`body` が生成後に有効であること。
- `mode: reply` の場合、`body` が生成後に有効であること。
- `to`、`cc`、`bcc`、`attachments` は文字列配列であること。
- 添付ファイルは存在し、通常ファイルであること。
- `--output` の親ディレクトリが存在すること。ただし `--create-dirs` 指定時は作成する。

### dry-run 表示

```text
メール YAML 生成予定:
- テンプレート: C:\work\templates\mail\sample_new.yaml
- 出力: C:\work\mail.yaml
- mode: new
- 宛先: 1 件
- 添付: 1 件
- 上書き: しない
```

### データ型案

```python
@dataclass(frozen=True)
class MailYamlGenerateRequest:
    cwd: Path
    template_path: Path
    output_path: Path
    variables: dict[str, str]
    vars_file: Path | None
    attachments: tuple[Path, ...]
    mode: str | None
    reply_all: bool
    dry_run: bool
    overwrite: bool
    create_dirs: bool

@dataclass(frozen=True)
class MailYamlGeneratePlan:
    template_path: Path
    output_path: Path
    mode: str
    to_count: int
    cc_count: int
    bcc_count: int
    attachment_paths: tuple[Path, ...]
    overwrite: bool
```

## 2. ファイル棚卸し・整理計画 CLI

### 概要

指定ディレクトリ配下のファイルを走査し、ファイル一覧、拡張子別サマリ、更新月別サマリ、重複候補、命名規則違反候補を出力する。

初期実装では、実ファイルの移動・リネームは行わない。整理計画の生成までに限定する。

### CLI 名

Python:

```powershell
python -m mytools.audit_files --cwd (Get-Location).Path --root .\docs --summary-output .\file_audit.md --format markdown
```

PowerShell:

```powershell
.\scripts\audit_files.ps1 .\docs --summary-output .\file_audit.md --format markdown
```

POSIX shell:

```sh
./scripts/audit_files.sh ./docs --summary-output ./file_audit.md --format markdown
```

### 入力

必須引数:

- `--cwd <dir>`: 相対パス解決の基準ディレクトリ
- `--root <dir>`: 棚卸し対象ディレクトリ

任意引数:

- `--glob <pattern>`: 対象ファイルパターン。既定は `**/*`
- `--exclude-glob <pattern>`: 除外パターン。複数指定可
- `--summary-output <path>`: サマリ出力先
- `--list-output <path>`: 詳細一覧 CSV 出力先
- `--format <markdown|json>`: サマリ形式。既定は `markdown`
- `--hash <none|sha256>`: ハッシュ計算。既定は `none`
- `--max-size-mb <number>`: ハッシュ計算対象の最大サイズ。既定は `100`
- `--naming-regex <regex>`: 命名規則。違反候補を出す
- `--config <path>`: 設定 JSON
- `--dry-run`: 走査対象と出力予定だけ表示する。ファイル走査は行うが出力ファイルは作らない
- `--overwrite`: 出力ファイル上書き
- `--create-dirs`: 出力先の親ディレクトリを作成

### 設定ファイル形式

```json
{
  "glob": "**/*",
  "exclude_globs": [
    "**/.git/**",
    "**/__pycache__/**",
    "**/.venv/**"
  ],
  "hash": "none",
  "max_size_mb": 100,
  "naming_regex": "^[A-Za-z0-9_.-]+$"
}
```

CLI 引数は設定ファイルより優先する。

### 走査対象

- 通常ファイルのみを対象にする。
- ディレクトリは一覧に含めない。
- シンボリックリンクは初期実装では追跡しない。
- `.git`、`.venv`、`__pycache__` は既定で除外する。
- 隠しファイルは除外しない。ただし除外したい場合は `--exclude-glob` で指定する。

### 詳細一覧 CSV

`--list-output` 指定時、次の列を出力する。

```text
path,relative_path,name,stem,suffix,size_bytes,modified_at,extension,sha256,naming_ok
```

仕様:

- `modified_at` は ISO 8601 形式。
- `sha256` は `--hash sha256` 指定時のみ値を入れ、未計算の場合は空文字。
- `naming_ok` は命名規則指定がない場合は空文字。

### Markdown サマリ

`--summary-output` 指定時、次のセクションを出力する。

- 概要
- 対象条件
- 件数サマリ
- 拡張子別サマリ
- 更新月別サマリ
- 大きいファイル上位
- 重複候補
- 命名規則違反候補

### 重複候補の判定

初期実装では次の2段階とする。

- 同一ファイル名候補: `name` が同じ
- 同一ハッシュ候補: `--hash sha256` 指定時に `sha256` が同じ

類似名判定は初期実装では対象外とする。将来、標準ライブラリ `difflib` による類似度判定を追加する。

### dry-run 表示

```text
ファイル棚卸し予定:
- 対象ディレクトリ: C:\work\docs
- 対象パターン: **/*
- 除外パターン: **/.git/**, **/__pycache__/**, **/.venv/**
- ハッシュ計算: none
- サマリ出力: C:\work\file_audit.md
- 詳細一覧出力: なし
- 上書き: しない
```

### データ型案

```python
@dataclass(frozen=True)
class FileAuditRequest:
    cwd: Path
    root_dir: Path
    glob_pattern: str
    exclude_globs: tuple[str, ...]
    summary_output_path: Path | None
    list_output_path: Path | None
    summary_format: str
    hash_algorithm: str
    max_size_mb: int
    naming_regex: str | None
    dry_run: bool
    overwrite: bool
    create_dirs: bool

@dataclass(frozen=True)
class FileInventoryItem:
    path: Path
    relative_path: str
    name: str
    stem: str
    suffix: str
    size_bytes: int
    modified_at: str
    sha256: str | None
    naming_ok: bool | None
```

## 3. PDF / docx / Markdown 変換バッチ CLI

### 概要

既存の単体変換 CLI を複数ファイルに対して実行するバッチ CLI。初期実装では、既存ジョブ関数を直接呼び出す方式を基本とし、外部プロセスとして既存 CLI を起動しない。

対象変換:

- Markdown から `html` / `pdf` / `docx`
- docx から Markdown
- PDF から PNG

PDF 比較は入力が2ファイル必要でバッチ選択規則が複雑なため、初期実装の対象外とする。

### CLI 名

Python:

```powershell
python -m mytools.batch_convert --cwd (Get-Location).Path --input-dir .\docs --glob "*.md" --kind markdown --format pdf --output-dir .\out --dry-run
```

PowerShell:

```powershell
.\scripts\batch_convert.ps1 .\docs --glob "*.md" --kind markdown --format pdf --output-dir .\out --dry-run
```

POSIX shell:

```sh
./scripts/batch_convert.sh ./docs --glob "*.md" --kind markdown --format pdf --output-dir ./out --dry-run
```

### 入力

必須引数:

- `--cwd <dir>`: 相対パス解決の基準ディレクトリ
- `--input-dir <dir>`: 入力ディレクトリ
- `--kind <markdown|docx|pdf>`: 入力種別
- `--output-dir <dir>`: 出力ディレクトリ

任意引数:

- `--glob <pattern>`: 対象パターン。既定は `kind` に応じる
- `--format <html|pdf|docx|markdown|png>`: 出力形式
- `--recursive` / `--no-recursive`: 再帰走査。既定は `--recursive`
- `--config <path>`: バッチ変換設定 JSON
- `--summary-output <path>`: 実行サマリ CSV または Markdown
- `--summary-format <csv|markdown|json>`: サマリ形式。既定は `csv`
- `--dry-run`: 変換せず、対象ファイルと出力予定を表示
- `--overwrite`: 出力ファイルまたは出力ディレクトリの既存を許可
- `--create-dirs`: 出力先ディレクトリを作成
- `--continue-on-error`: 途中で失敗しても残りを処理
- `--allow-partial-success`: 一部失敗時も終了コード `0` にする

Markdown 変換へ渡す任意引数:

- `--css <path-or-url>`: 複数指定可
- `--template <path>`: docx 出力用
- `--standalone` / `--no-standalone`
- `--no-default-css`
- `--no-default-template`

docx から Markdown 変換へ渡す任意引数:

- `--markdown-format <gfm|markdown|commonmark>`
- `--media-dir <dir>`
- `--no-extract-media`

PDF から PNG 変換へ渡す任意引数:

- `--quality <low|medium|high>`

### 既定の glob

- `--kind markdown`: `**/*.md`
- `--kind docx`: `**/*.docx`
- `--kind pdf`: `**/*.pdf`

`--no-recursive` 指定時は、それぞれ `*.md`、`*.docx`、`*.pdf` と同等に扱う。

### 出力パス規則

相対パス構造は維持する。

例:

```text
input-dir/
  a.md
  sub/b.md
output-dir/
  a.pdf
  sub/b.pdf
```

PDF から PNG の場合は、既存 `pdf_to_png` と同じく PDF ごとにディレクトリを作る。

```text
output-dir/
  sample/
    page_001.png
    page_002.png
```

同名ファイルが衝突する場合:

- `--overwrite` がない場合は該当ファイルを失敗扱いにする。
- `--continue-on-error` がない場合はそこで停止する。

### サマリ CSV

```text
status,input_path,output_path,kind,format,message
```

`status` は次のいずれか。

- `planned`: dry-run 時の予定
- `success`: 成功
- `failed`: 失敗
- `skipped`: 対象外または上書き不可によるスキップ

### dry-run 表示

```text
バッチ変換予定:
- 入力ディレクトリ: C:\work\docs
- 対象: 12 件
- 入力種別: markdown
- 出力形式: pdf
- 出力ディレクトリ: C:\work\out
- 上書き: しない

予定:
- C:\work\docs\a.md -> C:\work\out\a.pdf
- C:\work\docs\sub\b.md -> C:\work\out\sub\b.pdf
```

### データ型案

```python
@dataclass(frozen=True)
class BatchConvertRequest:
    cwd: Path
    input_dir: Path
    output_dir: Path
    kind: str
    output_format: str
    glob_pattern: str
    recursive: bool
    dry_run: bool
    overwrite: bool
    create_dirs: bool
    continue_on_error: bool
    allow_partial_success: bool

@dataclass(frozen=True)
class BatchConvertItemPlan:
    input_path: Path
    output_path: Path
    kind: str
    output_format: str

@dataclass(frozen=True)
class BatchConvertItemResult:
    plan: BatchConvertItemPlan
    status: str
    message: str
```

## 4. Excel / CSV 集計レポート生成 CLI

### 概要

Excel / CSV を読み込み、設定ファイルに基づいて集計し、Markdown レポートと CSV 集計結果を出力する。

初期実装の主出力は Markdown とする。HTML / PDF / docx への変換は、既存 `convert_markdown` または `batch_convert` に委ねる。

### CLI 名

Python:

```powershell
python -m mytools.generate_report --cwd (Get-Location).Path --input .\data.csv --config .\config\report_generator.json --output .\report.md --dry-run
```

PowerShell:

```powershell
.\scripts\generate_report.ps1 .\data.csv --config .\config\report_generator.json --output .\report.md --dry-run
```

POSIX shell:

```sh
./scripts/generate_report.sh ./data.csv --config ./config/report_generator.json --output ./report.md --dry-run
```

### 入力

必須引数:

- `--cwd <dir>`: 相対パス解決の基準ディレクトリ
- `--input <path>`: 入力 Excel / CSV
- `--config <path>`: レポート設定 JSON
- `--output <path>`: Markdown レポート出力先

任意引数:

- `--sheet <name>`: Excel のシート名。CSV では指定不可
- `--encoding <name>`: CSV の文字コード。既定は `utf-8-sig`
- `--summary-csv-output <path>`: 集計結果 CSV 出力先
- `--title <text>`: レポートタイトルを上書き
- `--template <path>`: Markdown テンプレート。未指定時は内蔵テンプレート
- `--dry-run`: 読み込みと設定検証まで行い、出力しない
- `--overwrite`: 出力ファイル上書き
- `--create-dirs`: 出力先の親ディレクトリを作成

### 対応入力形式

初期実装:

- `.csv`
- `.xlsx`

対象外:

- `.xls`
- `.xlsm`
- パスワード付き Excel
- 複数シート一括集計

### 依存関係方針

初期実装では次を推奨する。

- CSV: 標準ライブラリ `csv`
- Excel: `openpyxl`

`pandas` は便利だが依存が大きくなるため、最初の実装では必須にしない。複雑な集計が必要になった段階で導入を検討する。

`openpyxl` を導入する場合は、`Pipfile`、`pyproject.toml`、`requirements.txt` に追加する。

### 設定ファイル形式

```json
{
  "title": "月次集計レポート",
  "input": {
    "header_row": 1
  },
  "columns": {
    "date": "日付",
    "group": "部署",
    "value": "金額"
  },
  "filters": [
    {
      "column": "ステータス",
      "operator": "equals",
      "value": "完了"
    }
  ],
  "group_by": [
    "部署"
  ],
  "metrics": [
    {
      "name": "件数",
      "type": "count"
    },
    {
      "name": "金額合計",
      "type": "sum",
      "column": "金額"
    },
    {
      "name": "金額平均",
      "type": "avg",
      "column": "金額"
    }
  ],
  "sort": [
    {
      "column": "金額合計",
      "direction": "desc"
    }
  ],
  "top_n": 20
}
```

### 対応集計

初期実装で対応する集計:

- `count`: 件数
- `sum`: 合計
- `avg`: 平均
- `min`: 最小
- `max`: 最大

初期実装で対応するフィルタ:

- `equals`
- `not_equals`
- `contains`
- `not_empty`
- `empty`

数値比較、日付範囲、複数条件の AND / OR は将来拡張とする。初期実装では `filters` は AND 条件で処理する。

### Markdown レポート出力

既定テンプレートは次の構成にする。

```markdown
# 月次集計レポート

## 概要

- 入力ファイル: ...
- 対象行数: ...
- 集計後行数: ...
- 作成日時: ...

## 集計結果

| 部署 | 件数 | 金額合計 | 金額平均 |
|---|---:|---:|---:|
| A部 | 10 | 100000 | 10000 |
```

### summary CSV

`--summary-csv-output` 指定時は、集計結果表と同じ内容を CSV 出力する。

### dry-run 表示

```text
レポート生成予定:
- 入力: C:\work\data.csv
- 設定: C:\work\config\report_generator.json
- 出力: C:\work\report.md
- 入力行数: 120
- フィルタ後行数: 95
- 集計キー: 部署
- 指標: 件数, 金額合計, 金額平均
- 上書き: しない
```

### 検証

- 入力ファイルが存在し、通常ファイルであること。
- 入力拡張子が `.csv` または `.xlsx` であること。
- CSV の場合、`--sheet` が指定されていないこと。
- Excel の場合、指定シートが存在すること。
- 設定ファイルが JSON として読めること。
- `group_by` と `metrics[].column` で参照する列が入力に存在すること。
- 数値集計対象列は数値として解釈できること。解釈できない値はエラーにする。
- 出力先の親ディレクトリが存在すること。ただし `--create-dirs` 指定時は作成する。

### データ型案

```python
@dataclass(frozen=True)
class ReportGenerateRequest:
    cwd: Path
    input_path: Path
    config_path: Path
    output_path: Path
    sheet_name: str | None
    encoding: str
    summary_csv_output_path: Path | None
    title: str | None
    template_path: Path | None
    dry_run: bool
    overwrite: bool
    create_dirs: bool

@dataclass(frozen=True)
class ReportGeneratePlan:
    input_path: Path
    output_path: Path
    title: str
    row_count: int
    filtered_row_count: int
    group_by: tuple[str, ...]
    metric_names: tuple[str, ...]
    summary_csv_output_path: Path | None
    overwrite: bool
```

## 実装順序

推奨する実装順序は次のとおり。

1. メール YAML テンプレート生成 CLI
2. ファイル棚卸し・整理計画 CLI
3. PDF / docx / Markdown 変換バッチ CLI
4. Excel / CSV 集計レポート生成 CLI

理由:

- メール YAML テンプレート生成は依存追加なしで実装でき、既存メール機能の利用性をすぐ改善できる。
- ファイル棚卸しは標準ライブラリ中心で実装でき、後続のバッチ変換や整理作業の安全確認に使える。
- バッチ変換は既存ジョブ層の再利用で作れるが、複数ツールのエラー集約が必要なため、棚卸し後がよい。
- 集計レポート生成は追加依存や設定仕様が重いため、最後に実装する。

## 最小検証方針

実装後は、各ツールについて最低限次を確認する。

- `python -m compileall mytools mcp_servers`
- dry-run がファイルを書き込まないこと
- 出力先既存時に `--overwrite` なしで失敗すること
- 相対パスが `--cwd` 基準で解決されること
- PowerShell ラッパーが Python に名前付き引数で渡すこと
- POSIX shell ラッパーが Python に名前付き引数で渡すこと

pytest を導入する場合は、少なくとも各 job 層の plan 生成と入力検証を単体テスト対象にする。

## 未決事項

- `generate_report` で初期から `openpyxl` を導入するか。`.xlsx` 対応を優先するなら導入する。
- `batch_convert` の `--format` を `--kind` から自動決定できるケースで省略可能にするか。初期実装では明示指定を推奨する。
- `audit_files` のハッシュ計算を既定で無効にするか。初期実装では処理時間を避けるため `none` とする。
- メールテンプレートで Jinja2 を使うか。初期実装では追加依存を避け、単純な `{{name}}` 置換に限定する。
