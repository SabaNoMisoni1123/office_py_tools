from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from mytools.common import arg_path
from mytools.common.yaml_utils import load_yaml_file

MAIL_MODE_NEW = "new"
MAIL_MODE_REPLY = "reply"
TEMPLATE_ONLY_KEYS = {"defaults", "required_vars"}
PLACEHOLDER_RE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")


@dataclass(frozen=True)
class MailYamlGenerateRequest:
    cwd: Path
    template_path: Path
    output_path: Path
    variables: dict[str, str]
    vars_file: Path | None
    attachments: tuple[Path, ...]
    mode: str | None
    reply_all: bool
    dry_run: bool
    overwrite: bool
    create_dirs: bool


@dataclass(frozen=True)
class MailYamlGeneratePlan:
    template_path: Path
    output_path: Path
    mode: str
    to_count: int
    cc_count: int
    bcc_count: int
    attachment_paths: tuple[Path, ...]
    overwrite: bool
    data: dict[str, Any]


def generate_mail_yaml(request: MailYamlGenerateRequest) -> MailYamlGeneratePlan:
    plan = build_plan(request)
    if request.dry_run:
        return plan

    parent = arg_path.ensure_parent_dir(plan.output_path, create=request.create_dirs)
    if not parent.exists():
        raise FileNotFoundError(f"出力先の親ディレクトリが見つかりません: {parent}")
    if plan.output_path.exists() and not request.overwrite:
        raise FileExistsError(
            f"出力 YAML は既に存在します。上書きする場合は --overwrite を指定してください: {plan.output_path}"
        )

    with plan.output_path.open("w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(
            plan.data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
    return plan


def build_plan(request: MailYamlGenerateRequest) -> MailYamlGeneratePlan:
    validate_template_path(request.template_path)
    validate_output_path(
        request.output_path,
        overwrite=request.overwrite,
        create_dirs=request.create_dirs,
    )

    template = load_yaml_file(request.template_path)
    variables = build_variables(template, request)
    rendered = render_value(strip_template_only_keys(template), variables)

    if not isinstance(rendered, dict):
        raise ValueError("テンプレートのルートは YAML の辞書にしてください。")

    mode = request.mode or str(rendered.get("mode") or MAIL_MODE_NEW)
    if mode not in {MAIL_MODE_NEW, MAIL_MODE_REPLY}:
        raise ValueError("mode は new または reply を指定してください。")
    rendered["mode"] = mode
    if request.reply_all:
        rendered["reply_all"] = True

    attachments = list_string_field(rendered, "attachments")
    attachments.extend(str(path) for path in request.attachments)
    rendered["attachments"] = attachments

    validate_mail_yaml(rendered, base_dir=request.cwd)
    attachment_paths = tuple(
        arg_path.resolve_cli_path(item, base_dir=request.cwd) for item in attachments
    )

    return MailYamlGeneratePlan(
        template_path=request.template_path,
        output_path=request.output_path,
        mode=mode,
        to_count=len(list_string_field(rendered, "to")),
        cc_count=len(list_string_field(rendered, "cc")),
        bcc_count=len(list_string_field(rendered, "bcc")),
        attachment_paths=attachment_paths,
        overwrite=request.overwrite,
        data=rendered,
    )


def validate_template_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"メールテンプレートが見つかりません: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"メールテンプレートはファイルで指定してください: {path}")


def validate_output_path(path: Path, *, overwrite: bool, create_dirs: bool) -> None:
    parent = path.parent
    if not parent.exists() and not create_dirs:
        raise FileNotFoundError(f"出力先の親ディレクトリが見つかりません: {parent}")
    if parent.exists() and not parent.is_dir():
        raise NotADirectoryError(f"出力先の親パスはディレクトリではありません: {parent}")
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"出力 YAML は既に存在します。上書きする場合は --overwrite を指定してください: {path}"
        )


def build_variables(
    template: dict[str, Any], request: MailYamlGenerateRequest
) -> dict[str, str]:
    variables: dict[str, str] = {}
    defaults = template.get("defaults", {})
    if defaults is not None:
        if not isinstance(defaults, dict):
            raise ValueError("defaults はキーと値の辞書で指定してください。")
        variables.update({str(key): str(value) for key, value in defaults.items()})

    if request.vars_file is not None:
        variables.update(load_vars_file(request.vars_file))
    variables.update(request.variables)

    required = template.get("required_vars", [])
    if required is None:
        required = []
    if not isinstance(required, list):
        raise ValueError("required_vars は文字列配列で指定してください。")
    missing = [str(key) for key in required if str(key) not in variables]
    if missing:
        raise ValueError(f"必須変数が不足しています: {', '.join(missing)}")
    return variables


def load_vars_file(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"変数ファイルが見つかりません: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"変数ファイルはファイルで指定してください: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("変数ファイルのルートは辞書にしてください。")
    return {str(key): str(value) for key, value in data.items()}


def strip_template_only_keys(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if key not in TEMPLATE_ONLY_KEYS}


def render_value(value: Any, variables: dict[str, str]) -> Any:
    if isinstance(value, str):
        return render_string(value, variables)
    if isinstance(value, list):
        return [render_value(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: render_value(item, variables) for key, item in value.items()}
    return value


def render_string(value: str, variables: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise ValueError(f"未指定のテンプレート変数があります: {key}")
        return variables[key]

    rendered = PLACEHOLDER_RE.sub(replace, value)
    unresolved = PLACEHOLDER_RE.findall(rendered)
    if unresolved:
        raise ValueError(f"未置換のテンプレート変数があります: {', '.join(unresolved)}")
    return rendered


def validate_mail_yaml(data: dict[str, Any], *, base_dir: Path) -> None:
    mode = data.get("mode", MAIL_MODE_NEW)
    if mode == MAIL_MODE_NEW:
        if not list_string_field(data, "to"):
            raise ValueError("new モードでは to を 1 件以上指定してください。")
        require_non_empty_string(data, "subject")
        require_non_empty_string(data, "body")
    elif mode == MAIL_MODE_REPLY:
        require_non_empty_string(data, "body")
    else:
        raise ValueError("mode は new または reply を指定してください。")

    for key in ("to", "cc", "bcc", "attachments"):
        list_string_field(data, key)

    for attachment in list_string_field(data, "attachments"):
        path = arg_path.resolve_cli_path(attachment, base_dir=base_dir)
        if not path.exists():
            raise FileNotFoundError(f"添付ファイルが見つかりません: {path}")
        if not path.is_file():
            raise FileNotFoundError(f"添付ファイルはファイルで指定してください: {path}")


def require_non_empty_string(data: dict[str, Any], key: str) -> None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} は空でない文字列で指定してください。")


def list_string_field(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{key} は文字列配列で指定してください。")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(f"{key}[{index}] は文字列で指定してください。")
    return list(value)

