import os
import secrets
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from services.cache import redis_client

API_KEY_HEADER_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name = API_KEY_HEADER_NAME, auto_error = False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Validates the provided X-API-Key against legacy env variables and dynamic Redis keys.
    """
    if not api_key:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Missing API Key. Provide 'X-API-Key' header."
        )

    # Check environment variables (legacy/dev keys)
    raw_keys = os.getenv("API_KEYS", "")
    allowed_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    if api_key in allowed_keys:
        return api_key

    # Check dynamic keys stored in Redis
    redis_key = f"apikey:{api_key}"
    key_data = await redis_client.hgetall(redis_key)

    if not key_data or key_data.get("status") != "active":
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Invalid or inactive API Key provided."
        )

    return api_key


async def generate_api_key(client_name: str) -> str:
    """
    Generates a secure, cryptographically random API key with a prefix,
    and stores it in Redis associated with a client name.
    """
    random_token = secrets.token_hex(32)
    api_key = f"ftf_live_{random_token}"
    
    redis_key = f"apikey:{api_key}"
    await redis_client.hset(redis_key, mapping = {
        "client_name": client_name,
        "status": "active"
    })
    
    return api_key


async def revoke_api_key(api_key: str) -> bool:
    """
    Revokes an active API key by changing its status to 'revoked' in Redis.
    """
    redis_key = f"apikey:{api_key}"
    key_data = await redis_client.hgetall(redis_key)
    
    if not key_data:
        return False
        
    await redis_client.hset(redis_key, "status", "revoked")
    return True