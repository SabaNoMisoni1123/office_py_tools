#!/usr/bin/env bash

set -euo pipefail

show_help() {
    echo "使用方法: ./copy_folder.sh <source_dir> <destination_dir> [--skip-folder-containing <文字列>] [--force] [--dry-run]"
}

if [ "$#" -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

if [ "$#" -lt 2 ]; then
    show_help >&2
    exit 1
fi

SOURCE_DIR="$1"
DESTINATION_DIR="$2"
shift 2
PYTHON_ARGS=(--source-dir "$SOURCE_DIR" --destination-dir "$DESTINATION_DIR")

while [ "$#" -gt 0 ]; do
    case "$1" in
        --force|--dry-run)
            PYTHON_ARGS+=("$1")
            shift
            ;;
        --skip-folder-containing)
            if [ "$#" -lt 2 ]; then
                echo "エラー: --skip-folder-containing には文字列が必要です。" >&2
                show_help >&2
                exit 1
            fi
            PYTHON_ARGS+=("$1" "$2")
            shift 2
            ;;
        *)
            echo "エラー: 未対応のオプションです: $1" >&2
            show_help >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
CALL_DIR=$(pwd)

(
    cd -- "$PROJECT_ROOT" || exit 1
    python -m mytools.copy_folder --cwd "$CALL_DIR" "${PYTHON_ARGS[@]}"
)
