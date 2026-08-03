from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from email_module import EmailConfig, EmailConfigStore, EmailSender


def valid_config() -> EmailConfig:
    return EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        use_tls=True,
        sender_email="sender@example.com",
        password="app-password",
        recipients=["first@example.com", "second@example.com"],
        subject="Test subject",
        message="Test message",
    )


class EmailConfigStoreTests(unittest.TestCase):
    def test_round_trip_preserves_recipient_collection(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EmailConfigStore(Path(directory) / "email.json")
            store.save(valid_config())

            loaded = store.load()

            self.assertEqual(
                loaded.recipients,
                ["first@example.com", "second@example.com"],
            )
            self.assertEqual(loaded.smtp_host, "smtp.example.com")


class EmailSenderTests(unittest.TestCase):
    @patch("email_module.sender.smtplib.SMTP")
    def test_sends_to_every_configured_recipient(self, smtp_class):
        smtp = smtp_class.return_value.__enter__.return_value

        EmailSender().send(valid_config())

        smtp.starttls.assert_called_once_with()
        smtp.login.assert_called_once_with(
            "sender@example.com",
            "app-password",
        )
        sent_message = smtp.send_message.call_args.args[0]
        self.assertEqual(
            sent_message["To"],
            "first@example.com, second@example.com",
        )
        self.assertEqual(sent_message["Subject"], "Test subject")

    @patch("email_module.sender.smtplib.SMTP")
    def test_adds_image_attachment(self, smtp_class):
        smtp = smtp_class.return_value.__enter__.return_value
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "sample.jpg"
            image_path.write_bytes(b"test-image")

            EmailSender().send(
                valid_config(),
                attachments=[image_path],
            )

        sent_message = smtp.send_message.call_args.args[0]
        attachments = list(sent_message.iter_attachments())
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].get_filename(), "sample.jpg")
        self.assertEqual(attachments[0].get_content_type(), "image/jpeg")


if __name__ == "__main__":
    unittest.main()
