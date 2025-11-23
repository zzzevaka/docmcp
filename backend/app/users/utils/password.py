"""Password hashing utilities."""
import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Truncate password to 72 bytes if necessary (bcrypt limitation)
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    # Truncate password to 72 bytes if necessary (bcrypt limitation)
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
