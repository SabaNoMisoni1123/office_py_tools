#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "使い方:"
    echo "  ./convert_docx_to_markdown.sh <docx_path> --output <markdown_path> [options]"
    echo ""
    echo "Options:"
    echo "  --markdown-format <gfm|markdown|commonmark>  出力 Markdown 方言。"
    echo "  --media-dir <dir>                            メディア抽出先ディレクトリ。"
    echo "  --no-extract-media                           メディアを抽出しません。"
    echo "  --config <path>                              変換設定 JSON。"
    echo "  --dry-run                                    変換せず、変換予定だけ表示します。"
    echo "  --overwrite                                  出力先が存在する場合に上書きします。"
    echo ""
    exit 0
fi

INPUT_PATH="$1"
shift

PYTHON_ARGS=(--input "$INPUT_PATH")

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run|--overwrite|--no-extract-media)
            PYTHON_ARGS+=("$1")
            shift
            ;;
        --output|--markdown-format|--media-dir|--config)
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
            echo "エラー: docx パスは最初の引数に 1 つだけ指定してください。未対応の引数: $1" >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
CALL_DIR=$(pwd)

(
    cd -- "$PROJECT_ROOT" || exit 1
    python -m mytools.convert_docx_to_markdown \
        --cwd "$CALL_DIR" \
        "${PYTHON_ARGS[@]}"
)
