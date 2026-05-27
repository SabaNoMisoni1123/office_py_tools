# docx から Markdown への変換ツール 要件定義・設計

## 1. 目的

Word 文書（docx）を入力として Markdown ファイルへ変換する CLI ツールを追加する。
既存の Markdown 変換ツールと同様に、Python 3.10、Pandoc、名前付き CLI 引数、PowerShell / POSIX shell ラッパーを前提にする。

## 2. スコープ

### 2.1 対象範囲

- 単一 docx ファイルから単一 Markdown ファイルへの変換
- Pandoc による docx から Markdown への変換
- Markdown 方言の指定
- docx 内画像などのメディア抽出
- dry-run による変換予定確認
- 既存出力ファイルがある場合の上書き制御
- プロジェクト設定ファイルによる既定値管理

### 2.2 初期実装では対象外

- doc / dotx からの直接変換
- 複数 docx の一括変換
- Word の全スタイルを Markdown へ完全再現すること
- 脚注、コメント、変更履歴などの完全な表現保証
- Markdown 変換後の自動整形
- GUI
- MCP ツールとしての公開

## 3. CLI 要件

Python モジュール:

```powershell
python -m mytools.convert_docx_to_markdown --cwd (Get-Location).Path --input .\input.docx --output .\output.md
```

PowerShell ラッパー:

```powershell
.\scripts\convert_docx_to_markdown.ps1 .\input.docx --output .\output.md
```

POSIX shell ラッパー:

```sh
./scripts/convert_docx_to_markdown.sh ./input.docx --output ./output.md
```

Python 側の引数:

- `--cwd <dir>`: 呼び出し元ディレクトリ。ラッパーから必ず渡す。
- `--input <path>`: 入力 docx ファイル。
- `--output <path>`: 出力 Markdown ファイル。
- `--markdown-format <gfm|markdown|commonmark>`: 出力 Markdown 方言。既定は設定ファイルに従う。
- `--media-dir <dir>`: docx 内画像などの抽出先ディレクトリ。
- `--no-extract-media`: docx 内メディアを抽出しない。
- `--config <path>`: 変換設定 JSON。省略時は `config/docx_to_markdown.json` を使う。
- `--dry-run`: 変換せず、解決済みパスと変換予定を表示する。
- `--overwrite`: 出力先が存在する場合に上書きする。

ラッパーは既存方針どおり、位置引数を Python へ直接転送せず、名前付き引数へ組み立てて渡す。

## 4. 設定ファイル

プロジェクト既定の設定ファイルは `config/docx_to_markdown.json` とする。
設定ファイルに書かれたローカルパスは、設定ファイルの配置ディレクトリを基準に解決する。

基本形式:

```json
{
  "markdown_format": "gfm",
  "extract_media": true,
  "media_dir": null
}
```

- `markdown_format`: `gfm`、`markdown`、`commonmark` のいずれか。
- `extract_media`: 画像などを抽出するかどうか。
- `media_dir`: 既定のメディア抽出先。`null` の場合は出力 Markdown と同じ場所の `<出力ファイル名>_media` を使う。

CLI の `--markdown-format`、`--media-dir`、`--no-extract-media` は設定ファイルより優先する。

## 5. 入力検証

- `--input` は存在する通常ファイルであること。
- 入力拡張子は `.docx` であること。
- `--output` の親ディレクトリが存在すること。
- 出力拡張子は `.md` または `.markdown` を推奨する。異なる拡張子は初期実装ではエラーにする。
- 出力先が存在し、`--overwrite` がない場合はエラーにする。
- `--media-dir` の親ディレクトリが存在すること。
- `--no-extract-media` 指定時は `--media-dir` を指定しても使わない。

## 6. 変換設計

変換エンジンは Pandoc を使う。

Pandoc 呼び出し例:

```powershell
pandoc input.docx --from docx --to gfm --output output.md --extract-media output_media
```

メディア抽出時は、Pandoc を出力 Markdown の親ディレクトリを作業ディレクトリとして実行する。
これにより Markdown 内の画像リンクを相対パスに寄せる。

## 7. 追加ファイル構成案

```text
mytools/
  convert_docx_to_markdown.py
  jobs/
    docx_to_markdown_converter.py
  common/
    markdown/
      docx_config.py
scripts/
  convert_docx_to_markdown.ps1
  convert_docx_to_markdown.sh
config/
  docx_to_markdown.json
docs/
  docx_to_markdown_requirements_design.md
```

既存の `mytools/common/markdown/pandoc_runner.py` に docx から Markdown への Pandoc 実行関数を追加する。

## 8. エラーメッセージ方針

例:

- `入力 docx ファイルが見つかりません: <path>`
- `入力ファイルの拡張子は .docx にしてください: <path>`
- `出力先ファイルは既に存在します。上書きする場合は --overwrite を指定してください: <path>`
- `Markdown の出力形式は gfm, markdown, commonmark のいずれかにしてください。`
- `Pandoc が見つかりません。pandoc コマンドをインストールし、PATH に追加してください。`

## 9. 検証方針

最低限:

```powershell
python -m compileall mytools
```

Pandoc が利用可能な環境:

- dry-run
- docx から Markdown への実変換
- メディア抽出ありの実変換
- `--no-extract-media`
- PowerShell ラッパー経由の dry-run / 実変換
