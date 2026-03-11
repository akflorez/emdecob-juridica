import smtplib
from email.message import EmailMessage


def normalize_pass(p: str | None) -> str | None:
    if not p:
        return None
    # Quita espacios y saltos de línea (muy común en app passwords)
    return "".join(p.split())


def send_smtp_email(
    host: str,
    port: int,
    username: str,
    password: str,
    to_email: str,
    subject: str,
    body: str,
    from_email: str | None = None,
):
    if not host or not port or not username or not password:
        raise ValueError("SMTP incompleto: host/port/username/password requeridos")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email or username
    msg["To"] = to_email
    msg.set_content(body)

    # Gmail: 587 + STARTTLS
    with smtplib.SMTP(host, int(port), timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(msg)
