from email.message import EmailMessage

import aiosmtplib

from core.config import settings


async def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> None:
    admin_email = settings.roles.admin_email

    message = EmailMessage()
    message["From"] = admin_email
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body, subtype="html")
    await aiosmtplib.send(
        message,
        sender=admin_email,
        recipients=[recipient],
        hostname=settings.mailing_cfg.hostname,
        port=settings.mailing_cfg.port,
    )
