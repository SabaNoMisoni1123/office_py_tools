#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "使い方:"
    echo "  ./convert_markdown.sh <markdown_path> -f <html|pdf|docx> --output <output_path> [options]"
    echo ""
    echo "Options:"
    echo "  --css <path-or-url>       HTML / PDF に適用する CSS。複数指定できます。"
    echo "  --template <path>         docx 出力で使う Word テンプレートまたは参照文書。"
    echo "  --config <path>           変換設定 JSON。省略時は config/markdown_converter.json。"
    echo "  --no-default-css          設定ファイルの既定 CSS を使いません。"
    echo "  --no-default-template     設定ファイルの既定 Word テンプレートを使いません。"
    echo "  --standalone              HTML を完全な文書として出力します。"
    echo "  --no-standalone           HTML を断片として出力します。"
    echo "  --dry-run                 変換せず、変換予定だけ表示します。"
    echo "  --overwrite               出力先が存在する場合に上書きします。"
    echo ""
    exit 0
fi

INPUT_PATH="$1"
shift

PYTHON_ARGS=(--input "$INPUT_PATH")

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run|--overwrite|--standalone|--no-standalone|--no-default-css|--no-default-template)
            PYTHON_ARGS+=("$1")
            shift
            ;;
        -f|--format|--output|--css|--template|--config)
            if [ "$#" -lt 2 ]; then
                echo "エラー: $1 には値が必要です。" >&2
                exit 1
            fi
            PYTHON_ARGS+=("$1" "$2")
            shift 2
            ;;
        --*)
            echo "エラー: 未対応のオプションです: $1" >&2
            exit 1
            ;;
        *)
            echo "エラー: Markdown パスは最初の引数に 1 つだけ指定してください。未対応の引数: $1" >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
CALL_DIR=$(pwd)

(
    cd -- "$PROJECT_ROOT" || exit 1
    python -m mytools.convert_markdown \
        --cwd "$CALL_DIR" \
        "${PYTHON_ARGS[@]}"
)
