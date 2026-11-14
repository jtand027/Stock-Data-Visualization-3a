# Stock Data Visualizer (Project 3a)

A Flask web app that queries the [Alpha Vantage](https://www.alphavantage.co/) API and charts stock
data in the browser. Stock symbols in the drop-down are loaded from `stocks.csv` when the page loads.
The app runs in a Docker container started with docker-compose.

## Setup

1. Get a free API key from https://www.alphavantage.co/support/#api-key
2. Copy `.env.example` to `.env` and set `API_KEY` (same name as Project 3).

## Run with Docker

```bash
docker compose up --build
```

Then open http://localhost:5001

## Run without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_KEY=your_key
python app.py
```

Then open http://localhost:5000

## Input checking

- Symbol must be 1–10 characters of A-Z, 0-9, "." or "-" (Project 3 rule) and in `stocks.csv`
- Chart type must be 1 (Bar) or 2 (Line)
- Time series must be 1–4 (Intraday, Daily, Weekly, Monthly)
- Start and end dates must be valid `YYYY-MM-DD` dates and not in the future
- End date must be after the start date
- API errors (bad key, rate limit, no data in range) are shown as messages instead of crashing

## Files

- `app.py` – Flask app with the GET/POST route and form validation
- `stock_api.py` – Alpha Vantage query, date filtering, pygal chart building, CSV symbol loading
- `templates/` – Jinja templates for the form and chart
- `stocks.csv` – stock symbols for the drop-down
- `Dockerfile`, `docker-compose.yml` – container setup
