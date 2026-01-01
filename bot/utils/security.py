"""
Security utilities for hashing and validation
"""
import bcrypt
from config.settings import settings

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def verify_admin_secret(provided_secret: str) -> bool:
    """Verify admin secret against stored secret"""
    # In a real implementation, you'd hash the admin secret and compare
    # For now, we'll do a simple comparison (you should hash ADMIN_SECRET in production)
    return provided_secret == settings.admin_secret

