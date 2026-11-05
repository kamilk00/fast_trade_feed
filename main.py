from fastapi import FastAPI
from dotenv import load_dotenv
from routers import crypto, stock

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title = "FastTrade Feed API",
    description = "Real-Time Stock & Crypto Analytics API",
    version = "0.2.0"
)

# Include routers for modular architecture
app.include_router(crypto.router)
app.include_router(stock.router)


@app.get("/")
async def root():
    """
    Root endpoint to verify if the API is up and running.
    """
    return {"message": "FastTrade Feed API is active 🚀"}