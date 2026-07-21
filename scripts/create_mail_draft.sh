#!/usr/bin/env sh
# Outlook 下書き作成 CLI の POSIX shell 用ラッパー。
# Outlook 自体は Windows 専用のため、Linux では Python 側が利用不可を返します。

set -eu

usage() {
    echo "Usage: $0 <yaml-path> [--no-show] [--mode <new|reply>] [--reply-all]"
}

if [ "$#" -lt 1 ]; then
    usage
    exit 0
fi

YAML_PATH=$1
shift
NO_SHOW=false
REPLY_ALL=false
MODE=""

# 引数を明示的に解析し、許可した名前付き引数だけを Python に渡す。
while [ "$#" -gt 0 ]; do
    case "$1" in
        --no-show|--reply-all)
            if [ "$1" = "--no-show" ]; then
                NO_SHOW=true
            else
                REPLY_ALL=true
            fi
            shift
            ;;
        --mode)
            if [ "$#" -lt 2 ]; then
                echo "Error: --mode requires new or reply." >&2
                exit 1
            fi
            case "$2" in
                new|reply) MODE=$2 ;;
                *) echo "Error: --mode must be new or reply." >&2; exit 1 ;;
            esac
            shift 2
            ;;
        *)
            echo "Error: unsupported option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
CALL_DIR=$(pwd)

cd -- "$PROJECT_ROOT"

# 解析済みの値だけを、名前付き引数として組み立てて渡す。
if [ "$NO_SHOW" = true ] && [ "$REPLY_ALL" = true ] && [ -n "$MODE" ]; then
    python -m mytools.create_mail_draft --cwd "$CALL_DIR" --yaml-path "$YAML_PATH" --no-show --reply-all --mode "$MODE"
elif [ "$NO_SHOW" = true ] && [ "$REPLY_ALL" = true ]; then
    python -m mytools.create_mail_draft --cwd "$CALL_DIR" --yaml-path "$YAML_PATH" --no-show --reply-all
elif [ "$NO_SHOW" = true ] && [ -n "$MODE" ]; then
    python -m mytools.create_mail_draft --cwd "$CALL_DIR" --yaml-path "$YAML_PATH" --no-show --mode "$MODE"
elif [ "$REPLY_ALL" = true ] && [ -n "$MODE" ]; then
    python -m mytools.create_mail_draft --cwd "$CALL_DIR" --yaml-path "$YAML_PATH" --reply-all --mode "$MODE"
elif [ "$NO_SHOW" = true ]; then
    python -m mytools.create_mail_draft --cwd "$CALL_DIR" --yaml-path "$YAML_PATH" --no-show
elif [ "$REPLY_ALL" = true ]; then
    python -m mytools.create_mail_draft --cwd "$CALL_DIR" --yaml-path "$YAML_PATH" --reply-all
elif [ -n "$MODE" ]; then
    python -m mytools.create_mail_draft --cwd "$CALL_DIR" --yaml-path "$YAML_PATH" --mode "$MODE"
else
    python -m mytools.create_mail_draft --cwd "$CALL_DIR" --yaml-path "$YAML_PATH"
fi
