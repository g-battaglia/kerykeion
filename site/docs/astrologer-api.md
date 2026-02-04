---
title: 'Astrologer API'
description: 'Production-ready REST API for astrological calculations, SVG charts, and AI-powered interpretations. Skip the server setup and start building in minutes.'
category: 'API'
tags: ['docs', 'api', 'commercial', 'rest', 'production', 'kerykeion']
order: 1
---

# Astrologer API

The **Astrologer API** is a production-ready REST API that provides all Kerykeion features as cloud-hosted endpoints. It's the fastest way to add professional astrology features to your application.

> **[Get Started on RapidAPI](https://www.kerykeion.net/astrologer-api/subscribe)** | **[Full API Documentation](https://www.kerykeion.net/content/astrologer-api/)**

## Why Use the API?

| Feature | Kerykeion Library | Astrologer API |
|---------|-------------------|----------------|
| **Setup Time** | Install Python, dependencies, Swiss Ephemeris | Get API key, start calling |
| **Infrastructure** | You manage servers | Cloud-hosted, 99.9% uptime |
| **Licensing** | AGPL-3.0 (copyleft required) | Commercial-friendly |
| **Updates** | Manual pip upgrades | Automatic, zero downtime |
| **AI Interpretations** | Build your own LLM pipeline | Built-in `/context` endpoints |
| **Scaling** | Configure your own | Auto-scales with demand |

## Use Cases

The Astrologer API is ideal for:

- **SaaS Applications**: Build astrology features into your product without licensing concerns
- **Mobile Apps**: Call the API from iOS/Android without bundling Python
- **Prototyping**: Test ideas quickly without infrastructure setup
- **Commercial Projects**: Use in closed-source applications
- **High-Volume Workloads**: Let the API handle scaling

## Quick Start

### 1. Get Your API Key

Sign up at [RapidAPI](https://www.kerykeion.net/astrologer-api/subscribe) and subscribe to a plan. You'll receive an API key immediately.

### 2. Make Your First Call

```bash
curl -X POST "https://astrologer.p.rapidapi.com/api/v5/chart/natal" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -H "X-RapidAPI-Host: astrologer.p.rapidapi.com" \
  -d '{
    "subject": {
      "name": "Demo",
      "year": 1990, "month": 6, "day": 15,
      "hour": 14, "minute": 30,
      "city": "New York", "nation": "US"
    }
  }'
```

### 3. Use the Response

The API returns JSON with:
- `svg`: Ready-to-display SVG chart string
- `data`: Complete calculation data (positions, aspects, houses)

## Code Examples

### Python

```python
import requests

API_KEY = "your_rapidapi_key"
BASE_URL = "https://astrologer.p.rapidapi.com/api/v5"

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "astrologer.p.rapidapi.com",
    "Content-Type": "application/json"
}

# Natal Chart with SVG
response = requests.post(
    f"{BASE_URL}/chart/natal",
    headers=headers,
    json={
        "subject": {
            "name": "Alice",
            "year": 1990, "month": 6, "day": 15,
            "hour": 14, "minute": 30,
            "city": "London", "nation": "GB"
        }
    }
)

result = response.json()
print(result["svg"])  # SVG chart string
print(result["data"]["sun"]["sign"])  # "Gemini"
```

### JavaScript / TypeScript

```javascript
const API_KEY = "your_rapidapi_key";

const response = await fetch(
  "https://astrologer.p.rapidapi.com/api/v5/chart/natal",
  {
    method: "POST",
    headers: {
      "X-RapidAPI-Key": API_KEY,
      "X-RapidAPI-Host": "astrologer.p.rapidapi.com",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      subject: {
        name: "Alice",
        year: 1990, month: 6, day: 15,
        hour: 14, minute: 30,
        city: "London", nation: "GB",
      },
    }),
  }
);

const result = await response.json();
console.log(result.svg);  // SVG chart
console.log(result.data.sun.sign);  // "Gemini"
```

## Available Endpoints

### Data Endpoints (JSON)

Return raw calculation data without charts.

| Endpoint | Description |
|----------|-------------|
| `POST /api/v5/data/subject` | Calculate planetary positions for a subject |
| `POST /api/v5/data/now_subject` | Positions for the current moment |
| `POST /api/v5/data/compatibility_score` | Relationship compatibility score |
| `POST /api/v5/data/chart_data_natal` | Full natal chart data with aspects |
| `POST /api/v5/data/chart_data_synastry` | Synastry data between two subjects |
| `POST /api/v5/data/chart_data_composite` | Composite midpoint chart data |
| `POST /api/v5/data/chart_data_transit` | Transit chart data |
| `POST /api/v5/data/chart_data_solar_return` | Solar return data |
| `POST /api/v5/data/chart_data_lunar_return` | Lunar return data |

### Chart Endpoints (SVG)

Return both calculation data AND rendered SVG charts.

| Endpoint | Description |
|----------|-------------|
| `POST /api/v5/chart/natal` | Natal chart with SVG |
| `POST /api/v5/chart/now` | Current moment chart |
| `POST /api/v5/chart/synastry` | Synastry bi-wheel chart |
| `POST /api/v5/chart/composite` | Composite chart |
| `POST /api/v5/chart/transit` | Transit chart |
| `POST /api/v5/chart/solar_return` | Solar return chart |
| `POST /api/v5/chart/lunar_return` | Lunar return chart |

### AI Context Endpoints

Return AI-optimized text descriptions ready for LLM consumption.

| Endpoint | Description |
|----------|-------------|
| `POST /api/v5/context/subject` | Subject description |
| `POST /api/v5/context/natal` | Natal chart interpretation context |
| `POST /api/v5/context/synastry` | Relationship analysis context |
| `POST /api/v5/context/composite` | Composite chart context |
| `POST /api/v5/context/transit` | Transit forecast context |
| `POST /api/v5/context/solar_return` | Solar return context |
| `POST /api/v5/context/lunar_return` | Lunar return context |

## Pricing

Visit [RapidAPI Pricing](https://www.kerykeion.net/astrologer-api/subscribe) for current plans.

Typical tiers include:
- **Free**: Limited requests for testing
- **Basic**: For hobby projects and prototypes
- **Pro**: For production applications
- **Enterprise**: Custom volume and SLA

## API vs Library: Which Should I Use?

**Use the Kerykeion library if:**
- You're building an open-source project (AGPL-compatible)
- You need offline calculations without internet
- You want maximum customization of internals
- You're learning astrology programming

**Use the Astrologer API if:**
- You're building a commercial or closed-source product
- You want to avoid server/infrastructure management
- You need AI-powered interpretations out of the box
- You're building a mobile app or frontend-only project
- You want automatic updates and high availability

## Resources

- **[RapidAPI Dashboard](https://www.kerykeion.net/astrologer-api/subscribe)**: Subscribe and manage your API key
- **[Full API Documentation](https://www.kerykeion.net/content/astrologer-api/)**: Complete endpoint reference with examples
- **[Astrologer Studio](https://www.astrologerstudio.com/)**: Live demo application built with the API
