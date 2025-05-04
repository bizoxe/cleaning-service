from core.config import settings
from utils.mailing.helpers import create_url_safe_token
from utils.mailing.send_email import send_email


async def send_verify_email(email: str) -> None:
    token = create_url_safe_token(email=email)
    link = f"{settings.mailing_cfg.base_url}api/v1/auth/verify-email/{token}"
    html_message = f"""
    <h3>Confirm your email</h3>
    <p>Please click this <a href="{link}">link</a> to confirm your email</p>
    """
    await send_email(
        recipient=email,
        subject="[Cleaning service] Email verification",
        body=html_message,
    )
