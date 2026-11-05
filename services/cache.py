import os
import redis.asyncio as redis

# Read Redis host from environment variable (default to localhost for local dev)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize asynchronous Redis connection
redis_client = redis.Redis(host = REDIS_HOST, port = REDIS_PORT, decode_responses = True)

CACHE_TTL_SECONDS = 30  # Cache time-to-live in seconds