from __future__ import annotations

import argparse
from pathlib import Path

from mytools.common import arg_path
from mytools.jobs.mail_yaml_generator import (
    MAIL_MODE_NEW,
    MAIL_MODE_REPLY,
    MailYamlGeneratePlan,
    MailYamlGenerateRequest,
    generate_mail_yaml,
)


def main() -> int:
    parser = build_parser()
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )
    template_path = arg_path.resolve_cli_path(parsed_arg.template_path, base_dir=base_dir)
    output_path = arg_path.resolve_cli_path(parsed_arg.output_path, base_dir=base_dir)
    vars_file = (
        arg_path.resolve_cli_path(parsed_arg.vars_file, base_dir=base_dir)
        if parsed_arg.vars_file is not None
        else None
    )
    attachments = tuple(
        arg_path.resolve_cli_path(path, base_dir=base_dir)
        for path in parsed_arg.attachments or ()
    )

    try:
        request = MailYamlGenerateRequest(
            cwd=Path(base_dir),
            template_path=template_path,
            output_path=output_path,
            variables=parse_variables(parsed_arg.variables or ()),
            vars_file=vars_file,
            attachments=attachments,
            mode=parsed_arg.mode,
            reply_all=parsed_arg.reply_all,
            dry_run=parsed_arg.dry_run,
            overwrite=parsed_arg.overwrite,
            create_dirs=parsed_arg.create_dirs,
        )
        plan = generate_mail_yaml(request)
        print_plan(plan, dry_run=parsed_arg.dry_run)
        return 0
    except (ValueError, FileNotFoundError, FileExistsError, NotADirectoryError) as e:
        print(f"エラー: {e}")
        return 1
    except OSError as e:
        print(f"エラー: {e}")
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="メールテンプレートから Outlook 下書き作成用 YAML を生成します。"
    )
    parser.add_argument("--cwd", required=True, help="相対パス解決の基準ディレクトリ")
    parser.add_argument("--template", dest="template_path", required=True)
    parser.add_argument("--output", dest="output_path", required=True)
    parser.add_argument("--var", dest="variables", action="append", help="key=value 形式の変数")
    parser.add_argument("--vars-file", help="変数定義 YAML/JSON ファイル")
    parser.add_argument("--attachment", dest="attachments", action="append")
    parser.add_argument("--mode", choices=[MAIL_MODE_NEW, MAIL_MODE_REPLY])
    parser.add_argument("--reply-all", action="store_true", default=False)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--overwrite", action="store_true", default=False)
    parser.add_argument("--create-dirs", action="store_true", default=False)
    return parser


def parse_variables(items: tuple[str, ...]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"--var は key=value 形式で指定してください: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"--var のキーが空です: {item}")
        variables[key] = value
    return variables


def print_plan(plan: MailYamlGeneratePlan, *, dry_run: bool) -> None:
    title = "メール YAML 生成予定" if dry_run else "メール YAML 生成結果"
    print(f"{title}:")
    print(f"- テンプレート: {plan.template_path}")
    print(f"- 出力: {plan.output_path}")
    print(f"- mode: {plan.mode}")
    print(f"- 宛先: {plan.to_count} 件")
    print(f"- CC: {plan.cc_count} 件")
    print(f"- BCC: {plan.bcc_count} 件")
    print(f"- 添付: {len(plan.attachment_paths)} 件")
    print(f"- 上書き: {'する' if plan.overwrite else 'しない'}")


if __name__ == "__main__":
    raise SystemExit(main())

