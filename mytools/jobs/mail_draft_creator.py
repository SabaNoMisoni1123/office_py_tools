from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mytools.common.file_utils import ensure_files_exist
from mytools.common.yaml_utils import get_required_str, get_str_list

try:
    import win32com.client  # type: ignore
except ImportError:
    win32com = None

OL_MAIL_ITEM = 0
OL_TO = 1
OL_CC = 2
OL_BCC = 3
OL_MAIL = 43

MAIL_MODE_NEW = "new"
MAIL_MODE_REPLY = "reply"
REPLY_TARGET_SELECTED = "selected"


@dataclass(frozen=True)
class MailDefinition:
    to: list[str]
    cc: list[str]
    bcc: list[str]
    subject: str
    body: str
    attachments: list[Path]


@dataclass(frozen=True)
class ReplyMailDefinition:
    body: str
    attachments: list[Path]
    target: str = REPLY_TARGET_SELECTED
    reply_all: bool = False


def get_mail_mode(data: dict[str, Any], *, cli_mode: str | None = None) -> str:
    mode = cli_mode if cli_mode is not None else data.get("mode", MAIL_MODE_NEW)
    if not isinstance(mode, str):
        raise ValueError("mode は文字列で指定してください。指定できる値は new または reply です。")
    if mode not in {MAIL_MODE_NEW, MAIL_MODE_REPLY}:
        raise ValueError(
            f"mode の値が不正です: {mode!r}。指定できる値は new または reply です。"
        )
    return mode


def parse_mail_definition(
    data: dict[str, Any], *, attachment_base_dir: Path | None = None
) -> MailDefinition:
    mail_def = MailDefinition(
        to=get_str_list(data, "to"),
        cc=get_str_list(data, "cc"),
        bcc=get_str_list(data, "bcc"),
        subject=get_required_str(data, "subject"),
        body=get_required_str(data, "body"),
        attachments=ensure_files_exist(
            get_str_list(data, "attachments"), base_dir=attachment_base_dir
        ),
    )

    validate_mail_definition(mail_def)
    return mail_def


def parse_reply_mail_definition(
    data: dict[str, Any],
    *,
    attachment_base_dir: Path | None = None,
    cli_reply_all: bool = False,
) -> ReplyMailDefinition:
    reply_def = ReplyMailDefinition(
        body=get_required_str(data, "body"),
        attachments=ensure_files_exist(
            get_str_list(data, "attachments"), base_dir=attachment_base_dir
        ),
        target=get_reply_target(data),
        reply_all=cli_reply_all or get_optional_bool(data, "reply_all", default=False),
    )

    validate_reply_mail_definition(reply_def)
    return reply_def


def validate_mail_definition(mail_def: MailDefinition) -> None:
    if not mail_def.to:
        raise ValueError(
            "新規メールを作成するには to に少なくとも 1 件の宛先が必要です。"
            "返信メールを作成したい場合は YAML に `mode: reply` を指定するか、"
            "CLI で `--mode reply` を指定してください。"
        )

    if not mail_def.subject.strip():
        raise ValueError("新規メールを作成するには subject に件名を指定してください。")


def validate_reply_mail_definition(reply_def: ReplyMailDefinition) -> None:
    if reply_def.target != REPLY_TARGET_SELECTED:
        raise ValueError(
            "返信先メールの指定方法は現在 selected のみ対応しています。"
            "Outlook で返信したいメールを 1 件だけ選択してから実行してください。"
        )


def get_reply_target(data: dict[str, Any]) -> str:
    value = data.get("reply_target", REPLY_TARGET_SELECTED)
    if not isinstance(value, str):
        raise ValueError("reply_target は文字列で指定してください。現在は selected のみ対応しています。")
    return value


def get_optional_bool(data: dict[str, Any], key: str, *, default: bool = False) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} は true または false で指定してください。")
    return value


def create_outlook_draft(mail_def: MailDefinition, is_not_show: bool = False) -> None:
    outlook = get_outlook_application()
    mail = outlook.CreateItem(OL_MAIL_ITEM)

    set_recipients(mail, mail_def)
    set_mail_content(mail, mail_def)
    add_attachments(mail, mail_def.attachments)
    resolve_recipients(mail)
    save_or_display_mail(mail, is_not_show)


def create_selected_reply_draft(
    reply_def: ReplyMailDefinition, is_not_show: bool = False
) -> None:
    outlook = get_outlook_application()
    original_mail = get_single_selected_mail(outlook)
    reply_mail = create_reply_mail(original_mail, reply_all=reply_def.reply_all)

    prepend_plain_text_body(reply_mail, reply_def.body)
    add_attachments(reply_mail, reply_def.attachments)
    resolve_recipients(reply_mail)
    save_or_display_mail(reply_mail, is_not_show)


def get_outlook_application():
    if win32com is None:
        raise RuntimeError("pywin32 がインストールされていません。")

    return win32com.client.Dispatch("Outlook.Application")


def get_single_selected_mail(outlook):
    explorer = outlook.ActiveExplorer()
    if explorer is None:
        raise ValueError(
            "Outlook で返信したいメールを 1 件だけ選択してから実行してください。"
        )

    selection = explorer.Selection
    selected_count = selection.Count
    if selected_count != 1:
        raise ValueError(
            f"Outlook で選択中のアイテムが {selected_count} 件あります。"
            "返信したいメールを 1 件だけ選択してから実行してください。"
        )

    selected_item = selection.Item(1)
    item_class = getattr(selected_item, "Class", None)
    if item_class is not None and item_class != OL_MAIL:
        raise ValueError(
            "選択中のアイテムはメールではありません。"
            "Outlook でメールを 1 件だけ選択してから実行してください。"
        )

    if not hasattr(selected_item, "Reply"):
        raise ValueError(
            "選択中のアイテムは返信できるメールではありません。"
            "Outlook でメールを 1 件だけ選択してから実行してください。"
        )

    return selected_item


def create_reply_mail(original_mail, *, reply_all: bool):
    try:
        if reply_all:
            return original_mail.ReplyAll()
        return original_mail.Reply()
    except Exception as e:
        raise ValueError(
            "選択中のメールから返信メールを作成できませんでした。"
            "Outlook で通常のメールアイテムを 1 件だけ選択しているか確認してください。"
        ) from e


def prepend_plain_text_body(mail, body: str) -> None:
    existing_body = mail.Body or ""
    separator = "\r\n\r\n" if existing_body else ""
    mail.Body = body + separator + existing_body


def set_recipients(mail, mail_def: MailDefinition) -> None:
    add_recipients(mail, mail_def.to, OL_TO)
    add_recipients(mail, mail_def.cc, OL_CC)
    add_recipients(mail, mail_def.bcc, OL_BCC)


def add_recipients(mail, addresses: list[str], recipient_type: int) -> None:
    for address in addresses:
        recipient = mail.Recipients.Add(address)
        recipient.Type = recipient_type


def set_mail_content(mail, mail_def: MailDefinition) -> None:
    mail.Subject = mail_def.subject
    mail.Body = mail_def.body


def add_attachments(mail, attachments: list[Path]) -> None:
    for path in attachments:
        mail.Attachments.Add(str(path))


def resolve_recipients(mail) -> None:
    if not mail.Recipients.ResolveAll():
        raise ValueError(
            "解決できない宛先があります。メールアドレスまたは Outlook の宛先候補を確認してください。"
        )


def save_or_display_mail(mail, is_not_show: bool) -> None:
    if is_not_show:
        mail.Save()
        print("Outlook の下書きに保存しました。")
    else:
        mail.Display()
        print("Outlook で下書きを表示しました。")
