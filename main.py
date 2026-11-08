from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from routers import crypto, stock, stream
from services.limiter import limiter
from services.auth import verify_api_key, generate_api_key, revoke_api_key

load_dotenv()

app = FastAPI(
    title = "FastTrade Feed API",
    description = "Real-Time Stock & Crypto Analytics API with Per-Key Rate Limiting & Admin Controls",    
    version = "0.3.0"
)

# Set up slowapi rate limiter state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include all modular routers
app.include_router(crypto.router)
app.include_router(stock.router)
app.include_router(stream.router)


class KeyGenerationRequest(BaseModel):
    client_name: str = Field(..., example = "Acme Trading Corp", description = "Name of the client/organization.")


class KeyRevocationRequest(BaseModel):
    api_key: str = Field(..., example = "ftf_live_...", description = "The API key to revoke.")


@app.get("/")
async def root():
    """
    Root endpoint to verify if the API is up and running (public endpoint).
    """
    return {"message": "FastTrade Feed API is active 🚀"}


@app.post("/admin/generate-key", dependencies = [Depends(verify_api_key)], tags = ["Admin"])
async def create_api_key(payload: KeyGenerationRequest):
    """
    Admin endpoint to dynamically generate and store a new active API key in Redis.
    Requires an existing valid API key to execute.
    """
    new_key = await generate_api_key(payload.client_name)
    return {
        "client_name": payload.client_name,
        "api_key": new_key,
        "message": "Store this key safely. It will not be shown again."
    }


@app.post("/admin/revoke-key", dependencies = [Depends(verify_api_key)], tags = ["Admin"])
async def disable_api_key(payload: KeyRevocationRequest):
    """
    Admin endpoint to revoke/deactivate an existing API key immediately.
    """
    success = await revoke_api_key(payload.api_key)
    if not success:
        raise HTTPException(status_code = 404, detail = "API key not found in Redis store.")
        
    return {
        "api_key": payload.api_key,
        "status": "revoked",
        "message": "API key has been successfully deactivated."
    }