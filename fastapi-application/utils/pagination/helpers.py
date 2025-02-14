from cryptography.fernet import Fernet

from core.config import settings

SECRET_KEY = settings.pagination.secret_key


f = Fernet(SECRET_KEY)


def encode_id(identifier: int) -> str:
    encoded_identifier = f.encrypt(data=str(identifier).encode())

    return encoded_identifier.decode()


def decode_id(token: str) -> int:
    decoded_identifier = f.decrypt(token=token)

    return int(decoded_identifier.decode())
