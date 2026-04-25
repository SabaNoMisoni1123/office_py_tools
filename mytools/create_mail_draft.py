from __future__ import annotations

import sys
from pathlib import Path
import argparse

from mytools.common import arg_path
from mytools.common.yaml_utils import load_yaml_file
from mytools.jobs.mail_draft_creator import create_outlook_draft, parse_mail_definition


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml-path", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--no-show", action='store_true', default=False)
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
        mail_def = parse_mail_definition(data)
        create_outlook_draft(mail_def, parsed_arg.no_show)
        return 0
    except Exception as e:
        print(f"エラー: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
