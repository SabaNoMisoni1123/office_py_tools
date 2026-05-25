from __future__ import annotations

import argparse

from mytools.common import arg_path
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml-path", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--no-show", action="store_true", default=False)
    parser.add_argument(
        "--mode",
        choices=[MAIL_MODE_NEW, MAIL_MODE_REPLY],
        help="new は新規メール、reply は Outlook で選択中のメールへの返信を作成します。",
    )
    parser.add_argument(
        "--reply-all",
        action="store_true",
        default=False,
        help="返信モードで全員に返信する下書きを作成します。",
    )
    parser.add_argument("args", nargs="*")
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )

    yaml_path = arg_path.resolve_cli_path(
        path_str=parsed_arg.yaml_path, base_dir=base_dir
    )

    try:
        data = load_yaml_file(yaml_path)
        mode = get_mail_mode(data, cli_mode=parsed_arg.mode)
        if mode == MAIL_MODE_REPLY:
            reply_def = parse_reply_mail_definition(
                data,
                attachment_base_dir=base_dir,
                cli_reply_all=parsed_arg.reply_all,
            )
            create_selected_reply_draft(reply_def, parsed_arg.no_show)
        else:
            mail_def = parse_mail_definition(data, attachment_base_dir=base_dir)
            create_outlook_draft(mail_def, parsed_arg.no_show)
        return 0
    except Exception as e:
        print(f"エラー: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
