#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "使い方:"
    echo "  ./rename_files.sh basename <base_name> <file_path...> [options]"
    echo "  ./rename_files.sh prefix <prefix> <file_path...> [options]"
    echo "  ./rename_files.sh suffix <suffix> <file_path...> [options]"
    echo ""
    echo "例:"
    echo "  ./rename_files.sh basename report ./a.txt ./b.txt --dry-run"
    echo "  ./rename_files.sh prefix old_ ./a.txt"
    echo "  ./rename_files.sh suffix _done ./a.txt"
    echo ""
    exit 0
fi

OPERATION="$1"
shift

PYTHON_ARGS=()

case "$OPERATION" in
    basename)
        if [ "$#" -lt 2 ]; then
            echo "エラー: basename には <base_name> と <file_path...> が必要です。" >&2
            exit 1
        fi
        BASE_NAME="$1"
        shift
        PYTHON_ARGS+=(--operation "$OPERATION" --base-name "$BASE_NAME")
        ;;
    prefix)
        if [ "$#" -lt 2 ]; then
            echo "エラー: prefix には <prefix> と <file_path...> が必要です。" >&2
            exit 1
        fi
        PREFIX="$1"
        shift
        PYTHON_ARGS+=(--operation "$OPERATION" --prefix "$PREFIX")
        ;;
    suffix)
        if [ "$#" -lt 2 ]; then
            echo "エラー: suffix には <suffix> と <file_path...> が必要です。" >&2
            exit 1
        fi
        SUFFIX="$1"
        shift
        PYTHON_ARGS+=(--operation "$OPERATION" --suffix "$SUFFIX")
        ;;
    *)
        echo "エラー: 未対応の操作です: $OPERATION" >&2
        exit 1
        ;;
esac

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run|--overwrite)
            PYTHON_ARGS+=("$1")
            shift
            ;;
        --start|--padding|--separator)
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
            PYTHON_ARGS+=(--path "$1")
            shift
            ;;
    esac
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
CALL_DIR=$(pwd)

(
    cd -- "$PROJECT_ROOT" || exit 1
    python -m mytools.rename_files \
        --cwd "$CALL_DIR" \
        "${PYTHON_ARGS[@]}"
)
