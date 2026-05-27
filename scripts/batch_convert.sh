#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage:"
    echo "  ./batch_convert.sh <input_dir> --kind <markdown|docx|pdf> -f <format> --output-dir <dir> [options]"
    exit 0
fi

INPUT_DIR="$1"
shift
PYTHON_ARGS=(--input-dir "$INPUT_DIR")

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run|--overwrite|--create-dirs|--continue-on-error|--allow-partial-success|--no-default-css|--no-default-template|--no-extract-media|--recursive|--no-recursive|--standalone|--no-standalone)
            PYTHON_ARGS+=("$1")
            shift
            ;;
        --output-dir|--kind|-f|--format|--glob|--config|--css|--template|--markdown-format|--media-dir|--quality|--summary-output|--summary-format)
            if [ "$#" -lt 2 ]; then
                echo "Error: $1 requires a value." >&2
                exit 1
            fi
            PYTHON_ARGS+=("$1" "$2")
            shift 2
            ;;
        *)
            echo "Error: Unsupported argument: $1" >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
CALL_DIR=$(pwd)

(
    cd -- "$PROJECT_ROOT" || exit 1
    python -m mytools.batch_convert --cwd "$CALL_DIR" "${PYTHON_ARGS[@]}"
)
