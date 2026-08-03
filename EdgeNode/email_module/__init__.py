"""Drop-in email configuration and sending package."""

from .config import EmailConfig, EmailConfigStore
from .sender import EmailSender, EmailSendError
from .widget import EmailWidget

__all__ = [
    "EmailConfig",
    "EmailConfigStore",
    "EmailSender",
    "EmailSendError",
    "EmailWidget",
]
