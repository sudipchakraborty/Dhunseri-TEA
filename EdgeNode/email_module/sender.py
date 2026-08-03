from __future__ import annotations

from email.message import EmailMessage
import mimetypes
from pathlib import Path
import smtplib

from .config import EmailConfig


class EmailSendError(RuntimeError):
    """Raised when an email cannot be delivered."""


class EmailSender:
    """Reusable SMTP sender independent of the user interface."""

    def send(
        self,
        config: EmailConfig,
        *,
        subject: str | None = None,
        message: str | None = None,
        attachments: list[str | Path] | None = None,
    ) -> None:
        config.validate()

        email_message = EmailMessage()
        email_message["From"] = (
            f"{config.sender_name} <{config.sender_email}>"
            if config.sender_name.strip()
            else config.sender_email
        )
        email_message["To"] = ", ".join(config.recipients)
        email_message["Subject"] = subject or config.subject
        email_message.set_content(message or config.message)

        for attachment in attachments or []:
            path = Path(attachment)
            if not path.is_file():
                raise EmailSendError(f"Attachment was not found: {path}")
            mime_type, _ = mimetypes.guess_type(path.name)
            main_type, sub_type = (
                mime_type.split("/", 1)
                if mime_type
                else ("application", "octet-stream")
            )
            try:
                content = path.read_bytes()
            except OSError as error:
                raise EmailSendError(
                    f"Could not read attachment {path}: {error}"
                ) from error
            email_message.add_attachment(
                content,
                maintype=main_type,
                subtype=sub_type,
                filename=path.name,
            )

        smtp_class = smtplib.SMTP_SSL if config.use_ssl else smtplib.SMTP
        try:
            with smtp_class(
                config.smtp_host,
                config.smtp_port,
                timeout=30,
            ) as smtp:
                if config.use_tls:
                    smtp.starttls()
                if config.password:
                    smtp.login(config.sender_email, config.password)
                smtp.send_message(email_message)
        except (OSError, smtplib.SMTPException) as error:
            raise EmailSendError(str(error)) from error
