import bcrypt


def _to_bytes(password: str) -> bytes:
    """Encode and truncate to bcrypt's 72-byte hard limit."""
    return password.encode("utf-8")[:72]


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    hashed = bcrypt.hashpw(_to_bytes(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored bcrypt hash."""
    return bcrypt.checkpw(_to_bytes(plain_password), hashed_password.encode("utf-8"))
