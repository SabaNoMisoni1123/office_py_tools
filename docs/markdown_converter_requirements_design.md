# Markdown コンバートツール 要件定義・設計

## 1. 目的

Markdown ファイルを入力として、以下の形式へ変換する CLI ツールを追加する。

- HTML
- PDF
- Word 文書（docx）

HTML と PDF では、公開 URL またはローカルファイルで指定された CSS を反映できるようにする。
Word では、指定された Word テンプレート（dotx）またはそれに準じる参照文書を反映できるようにする。

このツールは `office_py_tools` の既存方針に合わせ、Python 3.10、Pipenv、名前付き CLI 引数、PowerShell / POSIX shell ラッパーを前提に設計する。

## 2. スコープ

### 2.1 対象範囲

- 単一 Markdown ファイルから単一出力ファイルへの変換
- 出力形式の明示指定
- 入力 Markdown のパス解決
- 出力ファイルのパス解決
- HTML 出力への CSS 適用
- PDF 出力への CSS 適用
- Word 出力へのテンプレート指定
- dry-run による変換予定内容の確認
- 既存出力ファイルがある場合の上書き制御
- 日本語ファイル名、日本語本文の扱い

### 2.2 初期実装では対象外

- 複数 Markdown ファイルの結合
- 目次、脚注、数式、図表番号などの高度な組版指定の完全対応
- Markdown 内リンクの網羅的な検証
- PDF の見た目の完全再現保証
- Word テンプレート内のマクロ実行
- Word テンプレート内の任意プレースホルダー差し込み
- GUI
- MCP ツールとしての公開

必要になった場合、上記は後続フェーズで拡張する。

## 3. 利用者要件

### 3.1 HTML 変換

利用者は Markdown を HTML に変換できる。

例:

```powershell
.\scripts\convert_markdown.ps1 .\input.md --format html
```

CSS を指定できる。

```powershell
.\scripts\convert_markdown.ps1 .\input.md --format html --css .\style.css
.\scripts\convert_markdown.ps1 .\input.md --format html --out-dir .\out --css https://example.com/style.css
```

### 3.2 PDF 変換

利用者は Markdown を PDF に変換できる。

```powershell
.\scripts\convert_markdown.ps1 .\input.md --format pdf
```

PDF 変換でも CSS を指定できる。

```powershell
.\scripts\convert_markdown.ps1 .\input.md --format pdf --out-dir .\out --css .\style.css
```

PDF ではページサイズや余白など、CSS のページメディア指定で制御することを基本とする。

### 3.3 Word 変換

利用者は Markdown を docx に変換できる。

```powershell
.\scripts\convert_markdown.ps1 .\input.md --format docx
```

Word テンプレートを指定できる。

```powershell
.\scripts\convert_markdown.ps1 .\input.md --format docx --out-dir .\out --template .\template.dotx
```

初期実装では、テンプレートは主に Word スタイルを反映するために使う。本文をテンプレート内の特定位置に差し込む用途は対象外とする。

## 4. 機能要件

### 4.1 CLI

Python モジュール:

```powershell
python -m mytools.convert_markdown --cwd (Get-Location).Path --input .\input.md --format pdf
```

PowerShell ラッパー:

```powershell
.\scripts\convert_markdown.ps1 .\input.md --format pdf
.\scripts\convert_markdown.ps1 .\input.md -f pdf --out-dir .\out
```

POSIX shell ラッパー:

```sh
./scripts/convert_markdown.sh ./input.md --format pdf --out-dir ./out
```

Python 側の引数:

- `--cwd <dir>`: 呼び出し元ディレクトリ。ラッパーから必ず渡す。
- `--input <path>`: 入力 Markdown ファイル。
- `--format <html|pdf|docx>`: 出力形式。
- `-f <html|pdf|docx>`: `--format` の短縮形。
- `--out-dir <dir>`: 出力先ディレクトリ。省略時は入力 Markdown ファイルと同じディレクトリ。出力ファイル名は入力ファイルの basename に出力形式の拡張子を付けたものとする。
- `--css <path-or-url>`: HTML / PDF 用 CSS。複数指定可能。
- `--template <path>`: Word 用テンプレート。dotx または docx を許可する。
- `--config <path>`: Markdown 変換設定 JSON。省略時は `config/markdown_converter.json` を使う。
- `--metadata <path>`: 任意。後続拡張用の YAML メタデータ。
- `--standalone`: HTML 出力時に完全な HTML 文書として出力する。既定は有効。
- `--no-default-css`: 設定ファイルの既定 CSS を使わない。
- `--no-default-template`: 設定ファイルの既定 Word テンプレートを使わない。
- `--dry-run`: 変換せず、解決済みパスと変換予定を表示する。
- `--overwrite`: 出力先が存在する場合に上書きする。

ラッパーは位置引数を Python へ直接転送せず、既存方針どおり名前付き引数へ組み立てて渡す。

### 4.1.1 設定ファイル

プロジェクト既定の設定ファイルは `config/markdown_converter.json` とする。
設定ファイルに書かれたローカルパスは、設定ファイルの配置ディレクトリを基準に解決する。

`--config` を指定しない場合は、次の順で設定ファイルを選択する。

1. 実行ディレクトリの `config/markdown_converter.json`
2. ホームディレクトリの `~/.config/markdown_converter.json`
3. プロジェクト既定の `config/markdown_converter.json`
4. 設定ファイルが見つからない場合は組み込みの既定値

`--config` を指定した場合は、上記より優先する。

基本形式:

```json
{
  "html": {
    "css": [],
    "standalone": true
  },
  "pdf": {
    "css": []
  },
  "docx": {
    "template": null
  }
}
```

CSS は HTML / PDF それぞれで既定値を持てる。CLI の `--css` は設定ファイルの CSS に追加される。
docx の `template` は既定テンプレートとして使われ、CLI の `--template` が指定された場合は CLI 指定を優先する。
既定値を使いたくない場合は `--no-default-css` または `--no-default-template` を指定する。

### 4.2 入力検証

- `--input` は存在する通常ファイルであること。
- 入力拡張子は `.md` または `.markdown` を推奨する。異なる拡張子は警告に留める。
- `--format` は `html`、`pdf`、`docx` のいずれか。
- `--out-dir` を指定した場合は、そのディレクトリが存在すること。省略時は入力ファイルと同じディレクトリを使うこと。
- 出力先が存在し、`--overwrite` がない場合はエラーにする。
- `--css` は `html` / `pdf` のときだけ有効。`docx` 指定時に渡された場合はエラーにする。
- `--template` は `docx` のときだけ有効。`html` / `pdf` 指定時に渡された場合はエラーにする。
- ローカル CSS は存在する通常ファイルであること。
- URL CSS は `http://` または `https://` のみ許可する。
- テンプレートは `.dotx` または `.docx` の通常ファイルであること。

### 4.3 Markdown 変換

Markdown 変換エンジンは Pandoc を第一候補とする。

理由:

- Markdown から HTML / PDF / docx への変換に広く対応している。
- docx の参照文書指定に対応しており、Word スタイルとの相性が比較的よい。
- CSS 適用や standalone HTML 出力の設計が単純になる。

Python 側では直接 Pandoc バイナリを呼ぶ構成を基本とする。`pypandoc` は Pandoc の導入やバイナリ管理を隠蔽できる一方、利用環境ごとの差分が増えやすいため、初期実装では必須依存にしない。

### 4.4 HTML 出力

- Pandoc で Markdown を HTML に変換する。
- `--standalone` が有効な場合、HTML 文書として出力する。
- CSS がローカルファイルの場合、既定では HTML から相対リンクとして参照する。
- CSS が URL の場合、`<link rel="stylesheet">` として参照する。
- 後続拡張として `--embed-css` を追加し、CSS 内容の埋め込みを可能にする。

### 4.5 PDF 出力

PDF 変換は以下の二段階を基本とする。

1. Markdown から HTML へ変換する。
2. HTML と CSS から PDF を生成する。

PDF 生成エンジンは WeasyPrint を第一候補とする。

理由:

- HTML + CSS から PDF を生成できる。
- CSS の反映経路が HTML 出力と揃う。
- Pandoc の PDF エンジン依存を LaTeX に寄せずに済む。

注意点:

- WeasyPrint は環境により追加のネイティブ依存が必要になる場合がある。
- Windows での配布・導入手順は README に明記する必要がある。
- 印刷向けの細かい制御は CSS 側で行う。

初期実装では PDF 作成に一時 HTML を使う。一時ファイルは `tempfile.TemporaryDirectory` 配下に作成し、通常終了時に削除する。

### 4.6 Word 出力

Word 出力は Pandoc の docx 変換を基本とする。

テンプレート指定の扱い:

- `.docx` は Pandoc の参照文書としてそのまま使う。
- `.dotx` は一時的な `.docx` 参照文書へ変換してから Pandoc に渡す。

`.dotx` から `.docx` への変換方法は二段構えにする。

1. Windows + Word COM が利用できる場合、Word で dotx から一時 docx を作成する。
2. Word COM が使えない場合は、dotx を Pandoc 参照文書として直接使えるか試すか、明確なエラーを返す。

初期実装の推奨動作は「dotx は Windows + Word COM が使える環境でサポート」と明記する。非 Windows でも docx 参照文書はサポート対象にする。

### 4.7 CSS 取得

CSS 指定は複数許可する。

```powershell
--css .\base.css --css https://example.com/theme.css
```

処理方針:

- ローカル CSS はパスを解決して存在確認する。
- URL CSS は URL 形式だけ検証し、HTML 出力ではリンクとしてそのまま出力する。
- PDF 出力では URL CSS を WeasyPrint に渡す。
- ネットワーク障害時の扱いは PDF 生成時のエラーとして利用者に返す。

公開 CSS を PDF に反映させる場合、オフライン環境では失敗する可能性があるため、必要に応じてローカル CSS を指定する運用を案内する。

### 4.8 出力

成功時:

- 出力ファイルパスを表示する。
- dry-run 時は出力予定パス、形式、CSS、テンプレート、上書き有無を表示する。

失敗時:

- 利用者が次に直すべき点が分かる日本語メッセージを出す。
- 変換エンジン由来の詳細は必要に応じて付加する。

終了コード:

- `0`: 成功
- `1`: 入力・オプション不正
- `2`: 変換エラー
- `3`: 外部依存不足

## 5. 非機能要件

### 5.1 互換性

- Python 3.10 で動作すること。
- Windows 以外でも import できること。
- Word COM 依存処理は Windows 専用モジュールまたは関数内 import に閉じ込めること。

### 5.2 セキュリティ

- ローカルファイルへの書き込みは、入力ファイルと同名・出力形式の拡張子で決まる出力ファイルに限定する。`--out-dir` 指定時も、そのディレクトリ配下に限定する。
- 出力先の上書きは `--overwrite` 指定時のみ許可する。
- URL CSS は `http` / `https` のみ許可する。
- Markdown 内の HTML を許可するかは Pandoc の既定動作に従う。厳格化が必要な場合は後続で `--safe` 相当のモードを検討する。

### 5.3 保守性

- CLI 固有処理と変換ロジックを分離する。
- パス解決は `mytools/common/arg_path.py` の既存方針に合わせる。
- 外部コマンド呼び出しは共通関数にまとめる。
- Windows 固有処理は `mytools/common/word_template.py` のような専用モジュールに分離する。

## 6. 基本設計

### 6.1 追加ファイル構成案

```text
mytools/
  convert_markdown.py
  jobs/
    markdown_converter.py
  common/
    markdown/
      __init__.py
      css.py
      pandoc_runner.py
      word_template.py
scripts/
  convert_markdown.ps1
  convert_markdown.sh
docs/
  markdown_converter_requirements_design.md
```

役割:

- `mytools/convert_markdown.py`: CLI エントリポイント。引数解析、終了コード制御。
- `mytools/jobs/markdown_converter.py`: ユースケース層。入力検証、変換フロー制御。
- `mytools/common/markdown/css.py`: CSS 指定の検証と解決。
- `mytools/common/markdown/pandoc_runner.py`: Pandoc 実行。
- `mytools/common/markdown/word_template.py`: dotx / docx テンプレート処理。
- `scripts/convert_markdown.ps1`: Windows PowerShell ラッパー。
- `scripts/convert_markdown.sh`: POSIX shell ラッパー。

### 6.2 主要データ構造

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class MarkdownConvertRequest:
    cwd: Path
    input_path: Path
    output_path: Path
    output_format: str
    css_sources: tuple[str, ...]
    template_path: Path | None
    standalone: bool
    dry_run: bool
    overwrite: bool

@dataclass(frozen=True)
class ResolvedCss:
    original: str
    kind: str  # "file" or "url"
    value: str

@dataclass(frozen=True)
class MarkdownConvertPlan:
    input_path: Path
    output_path: Path
    output_format: str
    css: tuple[ResolvedCss, ...]
    template_path: Path | None
    overwrite: bool
```

Python 3.10 互換を優先する場合、`Path | None` は利用可能だが、既存コードの書き方に合わせて `Optional[Path]` でもよい。

### 6.3 変換フロー

共通:

1. CLI 引数を解析する。
2. `--cwd` を基準に入力、出力、CSS、テンプレートのパスを解決する。
3. 入力検証を行う。
4. dry-run の場合は変換予定を表示して終了する。
5. 形式別の変換を実行する。
6. 成功メッセージを表示する。

HTML:

1. Pandoc で Markdown から HTML を生成する。
2. CSS 指定を Pandoc 引数に渡す。
3. 出力先へ保存する。

PDF:

1. 一時ディレクトリに中間 HTML を生成する。
2. CSS を反映して WeasyPrint で PDF を生成する。
3. 出力先へ保存する。

docx:

1. テンプレートが dotx の場合、一時 docx 参照文書を準備する。
2. Pandoc で Markdown から docx を生成する。
3. 参照文書がある場合は Pandoc の reference doc として渡す。

### 6.4 外部依存

追加候補:

- Pandoc: Python パッケージではなく外部コマンドとして扱う。
- WeasyPrint: PDF 生成用 Python パッケージ。

`Pipfile` / `requirements.txt` へ追加する候補:

```text
weasyprint
```

Pandoc は OS ごとのインストール手順が必要なため、Python 依存には含めない。起動時に `pandoc --version` を確認し、見つからない場合は外部依存不足としてエラーにする。

URL CSS の事前取得や検証を強化する場合は `requests` 追加を検討する。ただし初期実装では標準ライブラリの `urllib.parse` による URL 検証で足りる。

### 6.5 Pandoc 実行設計

Pandoc 呼び出し例:

HTML:

```powershell
pandoc input.md --from markdown --to html --standalone --css style.css --output output.html
```

docx:

```powershell
pandoc input.md --from markdown --to docx --reference-doc reference.docx --output output.docx
```

Python からは `subprocess.run([...], check=False, capture_output=True, text=True)` で実行し、戻り値を見てエラーを変換する。

shell=True は使わない。

### 6.6 WeasyPrint 実行設計

Python API を使う。

```python
from weasyprint import CSS, HTML

html = HTML(filename=str(html_path), base_url=str(base_dir))
stylesheets = [CSS(filename=str(css_path))]  # URL の場合は CSS(url=...)
html.write_pdf(str(output_path), stylesheets=stylesheets)
```

WeasyPrint の import は PDF 変換関数内で行い、HTML / docx だけ使う環境で import エラーにならないようにする。

### 6.7 Word テンプレート設計

`word_template.py` に以下を用意する。

- `prepare_reference_doc(template_path: Path, temp_dir: Path) -> Path`
- `.docx` の場合はそのまま返す。
- `.dotx` の場合は Windows + Word COM で一時 `.docx` を作る。
- 非 Windows または Word COM 不可の場合は明確な例外を出す。

COM 処理は関数内で `win32com.client` を import する。

例外メッセージ:

```text
dotx テンプレートを使うには Windows と Microsoft Word が必要です。非 Windows 環境では docx 参照文書を指定してください。
```

## 7. エラーメッセージ方針

例:

- `入力 Markdown ファイルが見つかりません: <path>`
- `出力先ファイルは既に存在します。上書きする場合は --overwrite を指定してください: <path>`
- `CSS は HTML または PDF 出力でのみ指定できます。`
- `テンプレートは docx 出力でのみ指定できます。`
- `Pandoc が見つかりません。pandoc コマンドをインストールし、PATH に追加してください。`
- `PDF 生成に必要な WeasyPrint を import できません。依存関係をインストールしてください。`

## 8. テスト方針

### 8.1 単体テスト

導入する場合は pytest を想定する。

対象:

- CLI 引数解析
- パス解決
- 出力形式ごとのオプション検証
- CSS の file / url 判定
- 上書き制御
- Pandoc 引数の組み立て
- dotx 非対応環境でのエラー

### 8.2 結合テスト

Pandoc が利用可能な環境:

- Markdown から HTML への変換
- Markdown から docx への変換
- CSS 指定付き HTML 変換

WeasyPrint が利用可能な環境:

- Markdown から PDF への変換
- ローカル CSS 指定付き PDF 変換

Windows + Word が利用可能な環境:

- dotx テンプレート指定付き docx 変換

### 8.3 最低限の検証

```powershell
pipenv run python -m compileall mytools
```

pytest 導入後:

```powershell
pipenv run pytest
```

## 9. 実装フェーズ案

### フェーズ 1: HTML 変換

- CLI 追加
- パス解決と入力検証
- Pandoc 存在確認
- HTML 出力
- ローカル / URL CSS 指定
- dry-run / overwrite
- PowerShell / shell ラッパー

### フェーズ 2: docx 変換

- Pandoc docx 出力
- docx 参照文書対応
- dotx の Windows + Word COM 変換対応
- テンプレート関連エラー整備

### フェーズ 3: PDF 変換

- WeasyPrint 導入
- 中間 HTML 生成
- CSS 反映
- PDF 出力
- Windows での導入手順整備

### フェーズ 4: 品質向上

- pytest 導入
- サンプル Markdown / CSS / テンプレート追加
- README 追記
- よくある失敗例と対処法の整理

## 10. 未決事項

- Pandoc をプロジェクトの必須外部依存として明記するか、HTML だけは Python Markdown ライブラリで代替するか。
- dotx を必須サポートにするか、docx 参照文書を推奨し dotx は Windows 限定サポートにするか。
- CSS を HTML にリンクするだけにするか、埋め込みオプションを初期実装に含めるか。
- PDF 出力の既定ページサイズ、余白、フォントをツール側で持つか、CSS に完全委譲するか。
- Markdown 方言を Pandoc Markdown に固定するか、GitHub Flavored Markdown 寄りにするか。

## 11. 推奨決定

初期実装では次の方針を推奨する。

- 変換エンジンは Pandoc を使う。
- PDF は Pandoc から直接 PDF を作らず、HTML を経由して WeasyPrint で作る。
- CSS は HTML / PDF 専用オプションとする。
- Word テンプレートは docx 参照文書を第一級サポートとし、dotx は Windows + Word COM が使える場合にサポートする。
- 最初の実装フェーズは HTML 変換に絞り、CLI とパス解決、CSS 指定、上書き制御を固める。
