#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage:"
    echo "  ./generate_mail_yaml.sh <template_path> --output <output_path> [options]"
    exit 0
fi

TEMPLATE_PATH="$1"
shift
PYTHON_ARGS=(--template "$TEMPLATE_PATH")

while [ "$#" -gt 0 ]; do
    case "$1" in
        --reply-all|--dry-run|--overwrite|--create-dirs)
            PYTHON_ARGS+=("$1")
            shift
            ;;
        --output|--var|--vars-file|--attachment|--mode)
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
    python -m mytools.generate_mail_yaml --cwd "$CALL_DIR" "${PYTHON_ARGS[@]}"
)
