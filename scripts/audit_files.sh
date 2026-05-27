#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage:"
    echo "  ./audit_files.sh <root_dir> [options]"
    exit 0
fi

ROOT_DIR="$1"
shift
PYTHON_ARGS=(--root "$ROOT_DIR")

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run|--overwrite|--create-dirs)
            PYTHON_ARGS+=("$1")
            shift
            ;;
        --glob|--exclude-glob|--summary-output|--list-output|--format|--hash|--max-size-mb|--naming-regex|--config)
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
    python -m mytools.audit_files --cwd "$CALL_DIR" "${PYTHON_ARGS[@]}"
)
