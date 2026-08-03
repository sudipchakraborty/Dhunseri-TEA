from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
)

from .config import EmailConfig, EmailConfigStore


class EmailConfigDialog(QDialog):
    """Editor for SMTP settings and the recipient email collection."""

    def __init__(self, store: EmailConfigStore, parent=None):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Email Configuration")
        self.setMinimumWidth(520)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.smtp_host = QLineEdit()
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.use_tls = QCheckBox("Use STARTTLS")
        self.use_ssl = QCheckBox("Use SSL")
        security_layout = QHBoxLayout()
        security_layout.addWidget(self.use_tls)
        security_layout.addWidget(self.use_ssl)

        self.sender_email = QLineEdit()
        self.sender_name = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.recipients = QPlainTextEdit()
        self.recipients.setPlaceholderText(
            "One address per line, or separate addresses with commas"
        )
        self.recipients.setMaximumHeight(90)
        self.subject = QLineEdit()
        self.message = QPlainTextEdit()
        self.message.setMaximumHeight(110)

        form.addRow("SMTP server", self.smtp_host)
        form.addRow("SMTP port", self.smtp_port)
        form.addRow("Security", security_layout)
        form.addRow("Sender email", self.sender_email)
        form.addRow("Sender name", self.sender_name)
        form.addRow("Password / app password", self.password)
        form.addRow("Recipient emails", self.recipients)
        form.addRow("Default subject", self.subject)
        form.addRow("Default message", self.message)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self) -> None:
        try:
            config = self.store.load()
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Email configuration", str(error))
            config = EmailConfig()

        self.smtp_host.setText(config.smtp_host)
        self.smtp_port.setValue(config.smtp_port)
        self.use_tls.setChecked(config.use_tls)
        self.use_ssl.setChecked(config.use_ssl)
        self.sender_email.setText(config.sender_email)
        self.sender_name.setText(config.sender_name)
        self.password.setText(config.password)
        self.recipients.setPlainText("\n".join(config.recipients))
        self.subject.setText(config.subject)
        self.message.setPlainText(config.message)

    def _save(self) -> None:
        recipient_text = self.recipients.toPlainText().replace(",", "\n")
        config = EmailConfig(
            smtp_host=self.smtp_host.text().strip(),
            smtp_port=self.smtp_port.value(),
            use_tls=self.use_tls.isChecked(),
            use_ssl=self.use_ssl.isChecked(),
            sender_email=self.sender_email.text().strip(),
            sender_name=self.sender_name.text().strip(),
            password=self.password.text(),
            recipients=[
                address.strip()
                for address in recipient_text.splitlines()
                if address.strip()
            ],
            subject=self.subject.text().strip(),
            message=self.message.toPlainText(),
        )
        try:
            self.store.save(config)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Invalid email configuration", str(error))
            return
        self.accept()
