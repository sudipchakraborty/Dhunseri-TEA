from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

from SciCam.app_paths import application_root


DEFAULT_CONFIG_PATH = application_root() / "config" / "email_config.json"


@dataclass
class EmailConfig:
    """Serializable SMTP settings and recipient collection."""

    smtp_host: str = ""
    smtp_port: int = 587
    use_tls: bool = True
    use_ssl: bool = False
    sender_email: str = ""
    sender_name: str = ""
    password: str = ""
    recipients: list[str] = field(default_factory=list)
    subject: str = "Application notification"
    message: str = "This is an automated notification."

    def validate(self) -> None:
        if not self.smtp_host.strip():
            raise ValueError("SMTP server is required.")
        if not 1 <= int(self.smtp_port) <= 65535:
            raise ValueError("SMTP port must be between 1 and 65535.")
        if "@" not in self.sender_email:
            raise ValueError("A valid sender email address is required.")
        if not self.recipients:
            raise ValueError("At least one recipient email is required.")
        invalid = [address for address in self.recipients if "@" not in address]
        if invalid:
            raise ValueError(f"Invalid recipient email: {invalid[0]}")
        if self.use_tls and self.use_ssl:
            raise ValueError("TLS and SSL cannot both be enabled.")


class EmailConfigStore:
    """JSON-backed configuration store with a replaceable path."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else DEFAULT_CONFIG_PATH

    def load(self) -> EmailConfig:
        if not self.path.exists():
            return EmailConfig()
        with self.path.open("r", encoding="utf-8") as config_file:
            data = json.load(config_file)
        allowed = EmailConfig.__dataclass_fields__.keys()
        return EmailConfig(**{
            key: value for key, value in data.items() if key in allowed
        })

    def save(self, config: EmailConfig) -> None:
        config.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary_path.open("w", encoding="utf-8") as config_file:
            json.dump(asdict(config), config_file, indent=2)
        temporary_path.replace(self.path)
