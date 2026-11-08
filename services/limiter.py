from fastapi import Request
from slowapi import Limiter

async def get_rate_limit_key(request: Request) -> str:
    """
    Extracts the API key from headers to enforce rate limiting per API key.
    Falls back to remote IP address if no API key header is present.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"
    return request.client.host if request.client else "unknown"

# Initialize Limiter using Redis as storage backend and API key as rate-limit key
limiter = Limiter(
    key_func = get_rate_limit_key,
    storage_uri = "redis://redis:6379"
)