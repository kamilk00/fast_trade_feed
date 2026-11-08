from fastapi import FastAPI
from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from routers import crypto, stock, stream
from services.limiter import limiter

load_dotenv()

app = FastAPI(
    title = "FastTrade Feed API",
    description = "Real-Time Stock & Crypto Analytics API",
    version = "0.2.2"
)

# Set up slowapi rate limiter state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include all modular routers
app.include_router(crypto.router)
app.include_router(stock.router)
app.include_router(stream.router)


@app.get("/")
async def root():
    """
    Root endpoint to verify if the API is up and running.
    """
    return {"message": "FastTrade Feed API is active 🚀"}