import os
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import httpx
from services.cache import redis_client

router = APIRouter(prefix = "/ws", tags = ["WebSocket Real-Time Feed"])

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
STREAM_INTERVAL_SECONDS = 5  # Frequency of price updates


@router.websocket("/prices/{symbol}")
async def websocket_price_stream(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint to stream real-time price updates for a given crypto or stock symbol.
    Automatically detects symbol type or fetches accordingly.
    """
    await websocket.accept()
    formatted_symbol = symbol.upper()
    
    # Simple heuristic: if it contains USDT or length > 5 assume crypto, else stock (or handle both)
    is_crypto = "USDT" in formatted_symbol or len(formatted_symbol) > 5

    async_client = httpx.AsyncClient()
    
    try:
        while True:
            current_price = None
            source = "live_api"

            if is_crypto:
                # Fetch from Binance
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={formatted_symbol}"
                response = await async_client.get(url)
                if response.status_code == 200:
                    current_price = float(response.json().get("price"))
            else:
                # Fetch from Finnhub for stocks
                if FINNHUB_API_KEY:
                    url = f"{FINNHUB_BASE_URL}/quote"
                    params = {"symbol": formatted_symbol, "token": FINNHUB_API_KEY}
                    response = await async_client.get(url, params = params)
                    if response.status_code == 200:
                        current_price = response.json().get("c")

            # Send data back to the client over WebSocket
            if current_price is not None:
                payload = {
                    "symbol": formatted_symbol,
                    "price": float(current_price),
                    "status": "success"
                }
                await websocket.send_json(payload)
            else:
                await websocket.send_json({
                    "symbol": formatted_symbol,
                    "error": "Failed to fetch current price data"
                })

            # Wait before the next tick
            await asyncio.sleep(STREAM_INTERVAL_SECONDS)

    except WebSocketDisconnect:
        print(f"Client disconnected from stream for symbol: {formatted_symbol}")
    finally:
        await async_client.aclose()