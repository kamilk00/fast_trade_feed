from fastapi import FastAPI, HTTPException
import httpx
import redis.asyncio as redis
from pydantic import BaseModel, Field

app = FastAPI(
    title = "FastTrade Feed API",
    description = "Real-Time Stock & Crypto Analytics API",
    version = "0.1.0"
)

# Initialize asynchronous Redis connection (running locally in Docker)
redis_client = redis.Redis(host = "localhost", port = 6379, decode_responses = True)

CACHE_TTL_SECONDS = 30  # Cache time-to-live in seconds


# --- Pydantic Models ---

class CryptoPriceResponse(BaseModel):
    """
    Response model for cryptocurrency price endpoint.
    """
    symbol: str = Field(..., example = "BTCUSDT", description = "The trading pair symbol.")
    price: str = Field(..., example = "92450.12", description = "Current market price of the asset.")
    source: str = Field(..., example = "cache", description = "Origin of the data (cache or binance_api).")


@app.get("/")
async def root():
    """
    Root endpoint to verify if the API is up and running.
    """
    return {"message": "FastTrade Feed API is active 🚀"}


@app.get("/crypto/price/{symbol}", response_model = CryptoPriceResponse)
async def get_crypto_price(symbol: str = "BTCUSDT"):
    """
    Fetch the current cryptocurrency price from Binance API, 
    backed by Redis caching to prevent rate-limiting.
    """
    formatted_symbol = symbol.upper()
    cache_key = f"crypto:price:{formatted_symbol}"

    # 1. Check if the price is already in Redis cache
    cached_price = await redis_client.get(cache_key)
    if cached_price:
        return CryptoPriceResponse(
            symbol = formatted_symbol,
            price = cached_price,
            source = "cache"
        )

    # 2. If not in cache, fetch data from external Binance API
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={formatted_symbol}"
    
    async_client = httpx.AsyncClient()
    try:
        response = await async_client.get(url)
        response.raise_for_status()
        data = response.json()
        
        price = data.get("price")

        # 3. Save the fetched price into Redis cache with a TTL
        await redis_client.setex(cache_key, CACHE_TTL_SECONDS, price)

        return CryptoPriceResponse(
            symbol = formatted_symbol,
            price = price,
            source = "binance_api"
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code = e.response.status_code,
            detail = "Failed to fetch data from the external exchange API."
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code = 503,
            detail = "External exchange service is currently unavailable."
        )
    finally:
        await async_client.aclose()