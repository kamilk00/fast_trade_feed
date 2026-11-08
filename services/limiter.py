from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize Limiter using Redis as the storage backend
limiter = Limiter(
    key_func = get_remote_address,
    storage_uri = "redis://redis:6379"
)