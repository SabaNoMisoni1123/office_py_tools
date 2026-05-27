# office_py_tools 機能拡張計画

作成日: 2026-05-27

更新日: 2026-05-27

## 実装状況

2026-05-27 時点で、優先度 A として列挙した次の4ツールは初期実装済み。

- `generate_mail_yaml`: メール YAML テンプレート生成 CLI
- `audit_files`: ファイル棚卸し・整理計画 CLI
- `batch_convert`: PDF / docx / Markdown 変換バッチ CLI
- `generate_report`: Excel / CSV 集計レポート生成 CLI

関連する CLI、PowerShell / POSIX shell ラッパー、設定サンプル、テンプレート、依存関係はリポジトリへ追加済み。今後の優先作業は、優先度 B の文書品質チェック、Outlook 選択メール抽出、作業ログ・効果測定、MCP 拡張に移る。

補足:

- `generate_report` の `.xlsx` 対応のため `openpyxl` を依存に追加済み。
- `Pipfile.lock` は未更新。
- README には追加ツールの使用例を追記済み。

## 目的

本計画は、現在の `office_py_tools` に実装済みの Office 補助 CLI、PDF 処理、Markdown / Word 変換、ローカル MCP サーバーを土台に、今後作成すべき業務効率化ツールを整理するものです。

公開されている業務自動化の好事例では、次の傾向が確認できる。

- 定型作業を小さく切り出して自動化すると、短時間で大きな効果が出やすい。
- レポート生成、文書変換、データ集計、ファイル取得、確認作業の自動化は効果が測定しやすい。
- 自作ツールは、現場の業務フローに合わせてカスタマイズできる点が強い。
- 継続利用には、dry-run、ログ、エラー説明、設定ファイル、テンプレート化、効果測定が重要になる。
- AI クライアントや RPA 的な利用を広げる場合も、最初から広範な操作を公開するのではなく、安全な読み取り系や dry-run 可能な操作から始めるのが望ましい。

参考にした公開情報:

- Bayer LATAM / BotCity: Python を使った社内自動化により、180 件のプロジェクト、60,000 時間削減、社内開発者育成、中央統制を実現した事例。  
  https://botcity.cc/cases/bayer.html
- HGS: 銀行 IT 部門でパスワードリセットとアラート確認を RPA 化し、処理時間削減、14,000 時間超の削減、ロードマップ整備につなげた事例。  
  https://hgs.com/case-studies/freshly-implemented-rpa-increases-productivity-saving-international-bank-340k/
- Python.org / American Public Power Association: Python、Markdown、CSS、JupyterLab、CrossCompute により、3-6 か月かかる PDF レポート作成プロセスを自動化した事例。  
  https://www.python.org/success-stories/python-powered-crosscompute-report-automation-for-ereliability-tracker-leads-to-cost-and-time-savings-for-the-american-public-power-association-updated-20210526-0900/
- AINow: 業務効率化ツール自作では、目的明確化、セキュリティ、Office 連携、データ処理、テストと改善が重要と整理している記事。  
  https://ainow.jp/business-efficiency-tools/

## 現状の実装済みツール

現在の主な機能は次のとおり。

- YAML 定義から Outlook の新規メール下書きまたは返信下書きを作成する CLI
- 複数ファイルの basename / prefix / suffix 一括リネーム CLI
- Markdown から HTML / PDF / docx へ変換する CLI
- docx から Markdown へ変換する CLI
- PDF の各ページを PNG に変換する CLI
- 2 つの PDF をページごとに画像比較し、差分 PNG を出力する CLI
- 日本の曜日、祝日、営業日情報を返すローカル MCP サーバー
- PowerShell / POSIX shell ラッパーと、`--cwd` を基準にしたパス解決方針

この構成は、Office 文書、メール、PDF、ファイル操作を中心にした小型 CLI 群として一貫している。今後もこの方向を維持し、共通ロジックは `mytools/common/`、CLI は `mytools/`、AI クライアント専用機能は `mcp_servers/` に分離する。

## 拡張方針

1. 既存利用者の手作業をすぐ減らせる小型ツールを優先する。
2. ファイルを変更する機能は `--dry-run` を既定または必須に近い導線にする。
3. Outlook、Word、Excel など Windows / Office 固有処理は、非 Windows 環境でも import できる分離を維持する。
4. テンプレート、設定ファイル、ログ、実行結果サマリを整備し、同じ処理を繰り返し使えるようにする。
5. MCP 公開は、読み取り系、計画生成系、dry-run 系から段階的に始める。
6. 業務効果を説明できるように、削減見込み時間、処理件数、エラー件数を出せるツールを増やす。

## 優先度 A: 早期に作成すべきツール

### 1. Excel / CSV 集計レポート生成 CLI

概要: Excel または CSV を読み込み、集計表、グラフ用データ、Markdown / HTML / docx レポートを生成する。

背景: 公開事例では、月次報告、定型レポート、PDF レポート生成の自動化が大きな削減効果につながっている。既存の Markdown / PDF / docx 変換機能と相性がよく、本プロジェクトの自然な拡張になる。

想定機能:

- `--input` で Excel / CSV を指定
- `--config` で集計キー、対象列、出力形式を指定
- Markdown レポートを生成し、既存の Markdown 変換 CLI に渡せる構成にする
- `--dry-run` で読み込み対象、出力予定、集計条件を表示
- 欠損値、型不一致、想定外列を日本語で説明

候補モジュール:

- `mytools/generate_report.py`
- `mytools/jobs/report_generator.py`
- `mytools/common/tabular/`

追加依存候補:

- `pandas`
- `openpyxl`

優先理由: 既存の文書変換機能を活かせるうえ、月次・週次の報告業務に直接効く。

### 2. ファイル棚卸し・整理計画 CLI

概要: 指定フォルダ配下のファイルを走査し、拡張子、更新日、サイズ、命名規則、重複候補を一覧化する。必要に応じて整理・移動・リネーム計画を dry-run で出す。

背景: 現在のリネーム CLI と PDF 変換 CLI は、個別ファイル操作に強い。次の段階として、フォルダ全体の把握と整理計画を作ると、実務での探索・確認時間を減らせる。

想定機能:

- ファイル一覧を CSV / Markdown で出力
- 拡張子別、更新月別、サイズ別のサマリ
- 同名、類似名、同一サイズ、ハッシュ一致による重複候補検出
- 整理ルールを JSON / YAML で定義
- 移動・リネームは最初は dry-run のみにする

候補モジュール:

- `mytools/audit_files.py`
- `mytools/jobs/file_auditor.py`
- `mytools/common/file_inventory.py`

優先理由: ファイル名一括変更機能の延長で実装しやすく、誤操作防止の設計も既存方針に合う。

### 3. メール YAML テンプレート生成 CLI

概要: よく使うメール文面をテンプレート化し、宛先、件名、本文変数、添付ファイル候補から Outlook 下書き用 YAML を生成する。

背景: 既存の Outlook 下書き作成機能は、YAML を手で作る前提になっている。テンプレート生成を追加すると、非エンジニアでも定型メールを安全に再利用しやすくなる。

想定機能:

- `--template` と `--var key=value` で YAML を生成
- 宛先、cc、bcc、件名、本文、添付ファイルの変数埋め込み
- 添付ファイル存在確認
- 生成後に既存の `create_mail_draft` と連携可能
- 返信用テンプレート、全員返信用テンプレートにも対応

候補モジュール:

- `mytools/generate_mail_yaml.py`
- `mytools/jobs/mail_yaml_generator.py`
- `templates/mail/`

優先理由: 既存メール機能の利用障壁を下げ、定型文の属人化を減らせる。

### 4. PDF / docx / Markdown 変換バッチ CLI

概要: 複数ファイルをまとめて変換するバッチ処理を提供する。

背景: 現在の変換系 CLI は単一ファイル中心である。公開事例でも、大量ファイルの処理、レポート生成、反復作業の一括化が効率化の中心になっている。

想定機能:

- `--input-dir` と `--glob` で対象ファイルを選択
- 変換結果サマリを CSV / Markdown で出力
- 失敗ファイルを継続処理し、最後に一覧化
- `--dry-run` で対象ファイルと出力予定を確認
- 既存の単体変換ロジックを再利用

候補モジュール:

- `mytools/batch_convert.py`
- `mytools/jobs/batch_converter.py`

優先理由: 既存資産の組み合わせで作れるため、実装負荷に対して効果が大きい。

## 優先度 B: 次に作成が望ましいツール

### 5. Office 文書品質チェック CLI

概要: Markdown、docx、PDF、メール YAML を対象に、表記ゆれ、禁止語、未置換プレースホルダー、リンク切れ、添付漏れ、日付不整合を検査する。

想定機能:

- `{{name}}` のような未置換変数を検出
- メール YAML の宛先、件名、添付ファイル、本文長を検査
- Markdown 内リンク、ローカル画像、表記ルールを検査
- PDF 比較結果や変換結果と組み合わせた確認チェックリスト出力

候補モジュール:

- `mytools/check_documents.py`
- `mytools/jobs/document_checker.py`
- `config/document_check_rules.yml`

優先理由: 自動化した成果物の確認作業を減らし、業務リスクを下げられる。

### 6. Outlook 添付・受信メール情報の抽出補助 CLI

概要: Outlook で選択中のメールから、件名、送信者、受信日時、添付ファイル名を一覧化し、必要に応じて添付ファイルを保存する。

想定機能:

- 選択中メールのメタ情報を Markdown / CSV 出力
- 添付ファイル保存先の dry-run
- 保存ファイルのリネーム規則指定
- 非 Windows 環境では import 可能、実行時に明確なエラー

候補モジュール:

- `mytools/export_outlook_selection.py`
- `mytools/jobs/outlook_selection_exporter.py`

優先理由: Outlook 下書き作成と対になる機能で、メール起点のファイル整理・報告作成に使える。

### 7. 作業ログ・効果測定 CLI

概要: 各 CLI の実行結果から、処理件数、成功・失敗件数、削減見込み時間を記録し、週次・月次の効果測定レポートを作る。

想定機能:

- JSON Lines 形式の実行ログ出力
- ツール別、日別、月別の件数集計
- 手作業換算時間を設定して削減見込みを算出
- Markdown / CSV のサマリ生成

候補モジュール:

- `mytools/summarize_tool_usage.py`
- `mytools/common/run_log.py`

優先理由: 自作ツールの価値を説明しやすくなり、次に作るべき機能の判断材料になる。

### 8. ローカル MCP ツールの拡張

概要: AI クライアントから安全に呼び出せるローカル支援機能を増やす。

想定機能:

- ファイル棚卸しの読み取り専用サマリ
- メール YAML の検証
- Markdown / docx / PDF 変換の dry-run 計画生成
- 日本の営業日計算の範囲指定対応
- 実ファイル変更を伴う操作は公開しないか、dry-run のみに限定

候補モジュール:

- `mcp_servers/local_only/tools/file_inventory.py`
- `mcp_servers/local_only/tools/mail_yaml.py`
- `mcp_servers/local_only/tools/conversion_plan.py`

優先理由: 本プロジェクトの「AI クライアントから使うローカル MCP サーバー」という予定に沿い、安全に段階拡張できる。

## 優先度 C: 中長期で検討するツール

### 9. 画像 OCR / PDF テキスト抽出 CLI

概要: スキャン PDF や画像からテキストを抽出し、Markdown / CSV に保存する。

検討理由: 請求書、申請書、帳票の読み取り自動化は公開事例でも効果が大きい。ただし OCR エンジン、精度検証、機密情報の扱いが課題になるため中長期扱いとする。

### 10. Excel 更新・突合 CLI

概要: 2 つの Excel / CSV をキーで突合し、差分、追加、削除、変更セルをレポートする。

検討理由: PDF 比較機能の表データ版として需要が見込める。既存の比較系設計を活かせるが、Excel の書式、結合セル、複数シート対応に注意が必要。

### 11. Web / API 取得データの定期レポート化 CLI

概要: Web API や公開 CSV を取得し、整形して Markdown / PDF レポートを生成する。

検討理由: データ取得から報告までの自動化は効果が高い。ただしネットワーク、認証、利用規約、社内プロキシ対応が必要になるため、最初はローカルファイル入力のレポート生成を優先する。

### 12. 簡易 GUI / ランチャー

概要: 既存 CLI を選択して実行できる簡易ランチャーを提供する。

検討理由: 利用者が増える場合は CLI だけでは導入障壁が残る。まずは CLI と設定ファイルを安定させ、その後に GUI を検討する。

## 推奨ロードマップ

### フェーズ 1: 既存機能を活かす短期拡張

- メール YAML テンプレート生成 CLI
- PDF / docx / Markdown 変換バッチ CLI
- ファイル棚卸し・整理計画 CLI
- メール YAML と文書の品質チェック CLI の最小版

### フェーズ 2: レポート自動化

- Excel / CSV 集計レポート生成 CLI
- Markdown / HTML / PDF / docx 出力との連携
- 実行ログ・効果測定 CLI
- サンプル設定ファイルとテンプレートの整備

### フェーズ 3: AI クライアント連携

- MCP での読み取り専用ファイル棚卸し
- MCP でのメール YAML 検証
- MCP での変換 dry-run 計画生成
- 営業日計算ツールの範囲指定対応

### フェーズ 4: 高度化

- OCR / PDF テキスト抽出
- Excel / CSV 差分比較
- Outlook 添付保存と文書処理の連携
- 必要に応じた GUI / ランチャー

## 最初に着手する推奨順

1. `generate_mail_yaml`: 既存の Outlook 下書き機能をすぐ使いやすくする。
2. `audit_files`: 既存のリネーム、PDF 処理の前段として安全な棚卸しを提供する。
3. `batch_convert`: 既存の変換系 CLI をまとめて使えるようにする。
4. `generate_report`: Excel / CSV から Markdown レポートを生成し、文書変換へ接続する。
5. `check_documents`: 生成物の確認を自動化し、運用リスクを下げる。

## 実装時の共通要件

- Python 3.10 互換を維持する。
- PowerShell / POSIX shell ラッパーでは、位置引数を Python に直接転送せず、名前付き引数へ組み立てる。
- ファイル変更、移動、削除、上書きを伴う処理には `--dry-run` と `--overwrite` を用意する。
- パス解決は `--cwd` と `mytools/common/arg_path.py` の方針に合わせる。
- エラーメッセージは、利用者が次に直すべき内容が分かる日本語にする。
- Windows / Office COM 依存処理は関数内部 import に閉じ込め、非 Windows 環境でも import できるようにする。
- 依存追加時は `Pipfile`、`pyproject.toml`、`requirements.txt` の整合性を確認する。
- 可能な範囲で `python -m compileall mytools mcp_servers` を検証する。

## 判断保留事項

- Excel / CSV 処理に `pandas` を導入するか、まずは標準ライブラリ `csv` と `openpyxl` 中心で始めるか。
- 実行ログをプロジェクト配下に保存するか、利用者指定の出力先に限定するか。
- MCP から実ファイルを変更するツールを公開するか。初期方針としては、読み取り専用または dry-run のみに限定する。
- OCR を導入する場合、ローカルエンジンを使うか、クラウド OCR を許容するか。
- GUI を作る場合、Tkinter の簡易ランチャーにするか、Web UI にするか。
