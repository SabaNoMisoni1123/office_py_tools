#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage:"
    echo "  ./generate_report.sh <input_path> --config <config_path> --output <output_path> [options]"
    exit 0
fi

INPUT_PATH="$1"
shift
PYTHON_ARGS=(--input "$INPUT_PATH")

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run|--overwrite|--create-dirs)
            PYTHON_ARGS+=("$1")
            shift
            ;;
        --config|--output|--sheet|--encoding|--summary-csv-output|--title|--template)
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
    python -m mytools.generate_report --cwd "$CALL_DIR" "${PYTHON_ARGS[@]}"
)
