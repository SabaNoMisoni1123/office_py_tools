"""YAML のメール定義から Outlook の下書きを作成する Windows 専用 CLI。"""

from __future__ import annotations

import argparse

from mytools.common import arg_path
from mytools.common.cli import add_cwd_argument, print_error, resolve_base_dir
from mytools.common.yaml_utils import load_yaml_file
from mytools.jobs.mail_draft_creator import (
    MAIL_MODE_NEW,
    MAIL_MODE_REPLY,
    create_outlook_draft,
    create_selected_reply_draft,
    get_mail_mode,
    parse_mail_definition,
    parse_reply_mail_definition,
)


def main() -> int:
    """メール定義を検証し、Outlook の下書きを保存または表示する。"""
    parsed = build_parser().parse_args()
    try:
        base_dir = resolve_base_dir(parsed.cwd, entry_file=__file__)
        yaml_path = arg_path.resolve_cli_path(parsed.yaml_path, base_dir=base_dir)
        data = load_yaml_file(yaml_path)
        mode = get_mail_mode(data, cli_mode=parsed.mode)

        if mode == MAIL_MODE_REPLY:
            definition = parse_reply_mail_definition(
                data,
                attachment_base_dir=base_dir,
                cli_reply_all=parsed.reply_all,
            )
            create_selected_reply_draft(definition, parsed.no_show)
        else:
            definition = parse_mail_definition(data, attachment_base_dir=base_dir)
            create_outlook_draft(definition, parsed.no_show)
    except (ImportError, OSError, ValueError, FileNotFoundError) as error:
        print_error(error)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    """この CLI の引数定義を構築する。"""
    parser = argparse.ArgumentParser(
        description="YAML のメール定義から Outlook の下書きを作成します（Windows 専用）。"
    )
    add_cwd_argument(parser)
    parser.add_argument("--yaml-path", required=True, help="メール定義 YAML")
    parser.add_argument("--no-show", action="store_true", help="下書きを表示せず保存する")
    parser.add_argument(
        "--mode", choices=[MAIL_MODE_NEW, MAIL_MODE_REPLY],
        help="new: 新規メール、reply: Outlook で選択したメールへ返信",
    )
    parser.add_argument("--reply-all", action="store_true", help="返信時に全員へ返信する")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
