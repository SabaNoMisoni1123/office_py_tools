#!/bin/sh

if [ "$#" -lt 1 ]; then
    echo "使い方:"
    echo "  ./create_mail_draft.sh <yaml_path> [その他の引数]"
    echo ""
    echo "例:"
    echo "  ./create_mail_draft.sh ./config.yaml"
    echo ""
    exit 0
fi

YAML_PATH="$1"
shift

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
CALL_DIR=$(pwd)

(
    cd -- "$PROJECT_ROOT" || exit 1
    python -m mytools.create_mail_draft \
        --yaml-path "$YAML_PATH" \
        "$@" \
        --cwd "$CALL_DIR"
)
