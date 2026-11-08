from fastapi import APIRouter, HTTPException, Request
import httpx
from pydantic import BaseModel, Field
from services.cache import redis_client, CACHE_TTL_SECONDS
from services.limiter import limiter

router = APIRouter(prefix = "/crypto", tags = ["Crypto"])


class CryptoPriceResponse(BaseModel):
    """
    Response model for cryptocurrency price endpoint.
    """
    symbol: str = Field(..., example = "BTCUSDT", description = "The trading pair symbol.")
    price: float = Field(..., example = "92450.12", description = "Current market price of the asset.")
    source: str = Field(..., example = "cache", description = "Origin of the data (cache or external API).")


@router.get("/price/{symbol}", response_model = CryptoPriceResponse)
@limiter.limit("10/minute")
async def get_crypto_price(request: Request, symbol: str):
    """
    Fetch the current cryptocurrency price from Binance API, 
    backed by Redis caching and protected by rate limiting.
    """
    formatted_symbol = symbol.upper()
    cache_key = f"crypto:price:{formatted_symbol}"

    # Check Redis cache
    cached_price = await redis_client.get(cache_key)
    if cached_price:
        return CryptoPriceResponse(
            symbol = formatted_symbol,
            price = float(cached_price),
            source = "cache"
        )

    # Fetch from Binance API
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={formatted_symbol}"
    
    async_client = httpx.AsyncClient()
    try:
        response = await async_client.get(url)
        response.raise_for_status()
        data = response.json()
        
        price = float(data.get("price"))

        # Save to Redis cache
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