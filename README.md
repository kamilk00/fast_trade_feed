# FastTrade Feed API 🚀

**FastTrade Feed** is a production-ready, high-performance asynchronous REST & WebSocket API built with **FastAPI**, **Pydantic v2**, and **Redis**. Designed for real-time stock and cryptocurrency market data tracking, it features enterprise-grade capabilities including hybrid API key authentication, per-key rate limiting, caching, and dynamic key lifecycle management.

---

## 🏗️ Architecture & Tech Stack

* **Framework:** FastAPI (Python 3.14+) with asynchronous route handlers (`async/def`)
* **Server:** Uvicorn (ASGI)
* **Data Validation:** Pydantic v2
* **HTTP Client:** `httpx` (Asynchronous external API integration)
* **Cache & Auth Store:** Redis (via `redis.asyncio`)
* **Rate Limiting:** `slowapi` configured with custom per-key tracking
* **Containerization:** Docker & Docker Compose

---

## 📂 Project Structure

```text
fast_trade_feed/
├── routers/
│   ├── crypto.py         # Binance price endpoints (cached & protected)
│   ├── stock.py          # Finnhub stock price endpoints (cached & protected)
│   └── stream.py         # Real-time WebSocket feed
├── services/
│   ├── auth.py           # Hybrid API key validation, generation & revocation
│   ├── cache.py          # Redis connection pool & TTL configurations
│   └── limiter.py        # Per-key rate limiting logic
├── main.py               # FastAPI application entry point & admin endpoints
├── Dockerfile            # Container definition
├── docker-compose.yml    # Multi-container orchestration
├── requirements.txt      # Project dependencies
└── .env                  # Environment configuration (ignored in git)
```

---

## ⚡ Key Features

1. **Hybrid API Key Authentication (`X-API-Key`)**: 
   * Validates requests against fast development keys defined in `.env`.
   * Dynamically checks active cryptographic tokens securely stored in Redis.
2. **Per-Key Rate Limiting**: 
   * Prevents API abuse by tracking request rates specifically per unique `X-API-Key` rather than shared client IP addresses.
3. **Redis Caching**: 
   * Reduces external exchange latency and API quota usage by caching ticker prices with configured TTL.
4. **Administrative Key Lifecycle Management**: 
   * Secure administrative endpoints (`/admin/generate-key`, `/admin/revoke-key`) to provision and instantly deactivate client access tokens in real-time.
5. **Real-Time Streaming**: 
   * WebSocket support for continuous asset price monitoring.

---

## ⚙️ Getting Started & Installation

### Prerequisites
* [Docker](https://www.docker.com/) and Docker Compose installed on your machine.
* A valid API key from [Finnhub](https://finnhub.io/) (for stock market data).

### 1. Clone the repository
```bash
git clone https://github.com/kamilk00/fast_trade_feed.git
cd fast_trade_feed
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory based on the following template:

```env
FINNHUB_API_KEY=your_finnhub_api_key_here
API_KEYS=secret_key_123,secret_key_abc
```

### 3. Run with Docker Compose
Build and start the application containers in detached mode:

```bash
docker-compose up --build -d
```

The application will be accessible at `http://localhost:8000`.

---

## 🔌 API Endpoints Reference

All protected endpoints require the `X-API-Key` header.

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Public root health check | No |
| `GET` | `/crypto/price/{symbol}` | Get current crypto price (e.g., `BTCUSDT`) | Yes (`X-API-Key`) |
| `GET` | `/stock/price/{symbol}` | Get current stock price (e.g., `AAPL`) | Yes (`X-API-Key`) |
| `WS` | `/ws/prices/{symbol}` | Stream real-time prices via WebSocket | No |
| `POST` | `/admin/generate-key` | Dynamically generate and store a new active API key | Yes (`X-API-Key`) |
| `POST` | `/admin/revoke-key` | Immediately deactivate an existing API key | Yes (`X-API-Key`) |

---

## 🧪 Testing with cURL / Postman

**1. Access Public Root:**
```bash
curl http://localhost:8000/
```

**2. Request Protected Data (Crypto):**
```bash
curl -H "X-API-Key: secret_key_123" http://localhost:8000/crypto/price/BTCUSDT
```

**3. Generate a New Dynamic Key:**
```bash
curl -X POST http://localhost:8000/admin/generate-key \
  -H "X-API-Key: secret_key_123" \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Partner Trading Bot"}'
```

---

## 🛡️ Versioning

Current Version: **0.3.0**

* **v0.1.x** – Initial setup, containerization, and modular layout.
* **v0.2.x** – WebSocket integration, Redis caching, and slowapi rate limiting.
* **v0.3.0** – API Key authentication middleware, Redis dynamic token storage, per-key rate limiting, and admin controls.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.