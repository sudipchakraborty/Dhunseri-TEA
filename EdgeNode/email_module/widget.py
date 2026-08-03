from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from .config import EmailConfigStore
from .dialog import EmailConfigDialog
from .sender import EmailSender


class _SendSignals(QObject):
    succeeded = Signal()
    failed = Signal(str)


class _SendTask(QRunnable):
    def __init__(self, sender, config, subject, message, attachments):
        super().__init__()
        self.sender = sender
        self.config = config
        self.subject = subject
        self.message = message
        self.attachments = attachments
        self.signals = _SendSignals()

    @Slot()
    def run(self):
        try:
            self.sender.send(
                self.config,
                subject=self.subject,
                message=self.message,
                attachments=self.attachments,
            )
        except Exception as error:
            self.signals.failed.emit(str(error))
        else:
            self.signals.succeeded.emit()


class EmailWidget(QWidget):
    """Drop-in buttons for configuration and asynchronous email sending."""

    status_changed = Signal(str)
    send_succeeded = Signal()
    send_failed = Signal(str)

    def __init__(
        self,
        parent=None,
        *,
        config_path=None,
        sender=None,
        payload_provider=None,
    ):
        super().__init__(parent)
        self.store = EmailConfigStore(config_path)
        self.sender = sender or EmailSender()
        self.payload_provider = payload_provider
        self.thread_pool = QThreadPool.globalInstance()
        self._active_tasks = set()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.config_button = QPushButton("Email Config")
        self.send_button = QPushButton("Send Email")
        layout.addWidget(self.config_button)
        layout.addWidget(self.send_button)

        self.config_button.clicked.connect(self.open_configuration)
        self.send_button.clicked.connect(self._send_from_button)

    @Slot()
    def open_configuration(self):
        if EmailConfigDialog(self.store, self).exec():
            self.status_changed.emit("Email configuration saved.")

    def set_payload_provider(self, provider):
        """Set a callback returning subject, message and attachments."""
        self.payload_provider = provider

    @Slot()
    def _send_from_button(self):
        payload = {}
        if self.payload_provider is not None:
            try:
                payload = self.payload_provider() or {}
            except (OSError, ValueError) as error:
                error_text = str(error)
                self.status_changed.emit(error_text)
                self.send_failed.emit(error_text)
                return
        self.send_email(
            subject=payload.get("subject"),
            message=payload.get("message"),
            attachments=payload.get("attachments"),
        )

    def send_email(
        self,
        *,
        subject=None,
        message=None,
        attachments=None,
    ):
        try:
            config = self.store.load()
            config.validate()
        except (OSError, ValueError) as error:
            error_text = str(error)
            self.status_changed.emit(error_text)
            self.send_failed.emit(error_text)
            return

        self.send_button.setEnabled(False)
        self.status_changed.emit("Sending email...")
        task = _SendTask(
            self.sender,
            config,
            subject,
            message,
            attachments or [],
        )
        self._active_tasks.add(task)
        task.signals.succeeded.connect(
            lambda: self._finish_send(task, None)
        )
        task.signals.failed.connect(
            lambda error: self._finish_send(task, error)
        )
        self.thread_pool.start(task)

    def _finish_send(self, task, error):
        self._active_tasks.discard(task)
        self.send_button.setEnabled(True)
        if error:
            self.status_changed.emit(f"Email failed: {error}")
            self.send_failed.emit(error)
            return
        self.status_changed.emit("Email sent successfully.")
        self.send_succeeded.emit()
