"""SMTP delivery for explicitly user-approved outreach emails."""
from email.message import EmailMessage
import smtplib
import ssl
from ..core.config import get_settings

class EmailDeliveryError(RuntimeError):
    pass

def send_email(to_email: str, subject: str, body: str) -> None:
    s = get_settings()
    if not all([s.smtp_host, s.smtp_username, s.smtp_password, s.smtp_from_email]):
        raise EmailDeliveryError("Email delivery is not configured. Set SMTP_* settings in .env.")
    msg = EmailMessage()
    msg["From"] = s.smtp_from_email
    msg["To"] = to_email
    msg["Subject"] = subject.strip() or "Hello"
    msg.set_content(body)
    try:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as server:
            server.ehlo()
            if s.smtp_use_tls:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            server.login(s.smtp_username, s.smtp_password)
            server.send_message(msg)
    except Exception as exc:
        raise EmailDeliveryError("The email provider rejected delivery. Check SMTP settings and sender permissions.") from exc
