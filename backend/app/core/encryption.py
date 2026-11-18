import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet

from backend.app.core.config import settings

# Derive a 32-byte URL-safe base64 key from settings.SECRET_KEY
_KEY_MATERIAL = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
_FERNET_KEY = base64.urlsafe_b64encode(_KEY_MATERIAL)
_cipher = Fernet(_FERNET_KEY)


def encrypt_message_content(plaintext: str) -> str:
    """
    Encrypt message plaintext using authenticated AES-128-CBC with HMAC-SHA256 (Fernet).
    Returns URL-safe base64-encoded ciphertext string.
    """
    if not plaintext:
        return ""
    encrypted_bytes = _cipher.encrypt(plaintext.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_message_content(ciphertext: str) -> str:
    """
    Decrypt message ciphertext. If decryption fails or payload is invalid,
    returns a safe placeholder without leaking raw storage.
    """
    if not ciphertext:
        return ""
    try:
        decrypted_bytes = _cipher.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception:
        return "[Undecryptable Message]"
