"""Runtime secret selection without a shared development fallback."""
import secrets


_PLACEHOLDERS = {
    'your-secret-key-here', 'change-me-to-a-random-secret',
    'change-me-to-a-random-jwt-secret',
}


def resolve_flask_secret(configured: str | None) -> str:
    if not configured or not configured.strip():
        return secrets.token_hex(32)
    if configured.strip().lower() in _PLACEHOLDERS:
        raise ValueError('SECRET_KEY must be replaced with a private random value')
    return configured


def require_jwt_secret(configured: str | None) -> str:
    if not configured or not configured.strip() or configured.strip().lower() in _PLACEHOLDERS:
        raise ValueError('JWT_SECRET must be configured with a private random value')
    return configured
