import os
from fastapi import APIRouter, HTTPException, Request
import httpx
from pydantic import BaseModel, Field
from services.cache import redis_client, CACHE_TTL_SECONDS
from services.limiter import limiter

router = APIRouter(prefix = "/stock", tags = ["Stocks"])

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class StockPriceResponse(BaseModel):
    """
    Response model for stock price endpoint.
    """
    symbol: str = Field(..., example = "AAPL", description = "The asset trading symbol.")
    price: float = Field(..., example = "185.92", description = "Current market price of the asset.")
    source: str = Field(..., example = "cache", description = "Origin of the data (cache or external API).")


@router.get("/price/{symbol}", response_model = StockPriceResponse)
@limiter.limit("10/minute")
async def get_stock_price(request: Request, symbol: str):
    """
    Fetch the current stock price from Finnhub API, 
    backed by Redis caching and protected by rate limiting.
    """
    if not FINNHUB_API_KEY:
        raise HTTPException(
            status_code = 500,
            detail = "Finnhub API key is not configured on the server."
        )

    formatted_symbol = symbol.upper()
    cache_key = f"stock:price:{formatted_symbol}"

    # Check Redis cache
    cached_price = await redis_client.get(cache_key)
    if cached_price:
        return StockPriceResponse(
            symbol = formatted_symbol,
            price = float(cached_price),
            source = "cache"
        )

    # Fetch from Finnhub API
    url = f"{FINNHUB_BASE_URL}/quote"
    params = {
        "symbol": formatted_symbol,
        "token": FINNHUB_API_KEY
    }
    
    async_client = httpx.AsyncClient()
    try:
        response = await async_client.get(url, params = params)
        response.raise_for_status()
        data = response.json()
        
        current_price = data.get("c")
        
        if current_price is None or current_price == 0:
            raise HTTPException(
                status_code = 404,
                detail = "Stock symbol not found or data unavailable."
            )

        # Save to Redis cache
        await redis_client.setex(cache_key, CACHE_TTL_SECONDS, current_price)

        return StockPriceResponse(
            symbol = formatted_symbol,
            price = float(current_price),
            source = "finnhub_api"
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code = e.response.status_code,
            detail = "Failed to fetch data from Finnhub API."
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code = 503,
            detail = "Finnhub service is currently unavailable."
        )
    finally:
        await async_client.aclose()