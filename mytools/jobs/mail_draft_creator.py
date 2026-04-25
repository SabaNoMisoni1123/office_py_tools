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

@dataclass(frozen=True)
class MailDefinition:
    to: list[str]
    cc: list[str]
    bcc: list[str]
    subject: str
    body: str
    attachments: list[Path]


def parse_mail_definition(data: dict[str, Any]) -> MailDefinition:
    mail_def = MailDefinition(
        to=get_str_list(data, "to"),
        cc=get_str_list(data, "cc"),
        bcc=get_str_list(data, "bcc"),
        subject=get_required_str(data, "subject"),
        body=get_required_str(data, "body"),
        attachments=ensure_files_exist(get_str_list(data, "attachments")),
    )

    validate_mail_definition(mail_def)
    return mail_def


def validate_mail_definition(mail_def: MailDefinition) -> None:
    if not mail_def.to:
        raise ValueError("to には少なくとも1件の宛先が必要です。")


def create_outlook_draft(mail_def: MailDefinition, is_not_show: bool = False) -> None:
    outlook = get_outlook_application()
    mail = outlook.CreateItem(OL_MAIL_ITEM)

    set_recipients(mail, mail_def)
    set_mail_content(mail, mail_def)
    add_attachments(mail, mail_def.attachments)

    if not mail.Recipients.ResolveAll():
        raise ValueError(
            "解決できない宛先があります。メールアドレスを確認してください。"
        )

    if is_not_show:
        mail.Save()
        print("Outlookの下書きに保存しました。")
    else:
        mail.Display()
        print("Outlookで下書きを表示しました。")


def get_outlook_application():
    if win32com is None:
        raise RuntimeError("pywin32 がインストールされていません。")

    return win32com.client.Dispatch("Outlook.Application")


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
