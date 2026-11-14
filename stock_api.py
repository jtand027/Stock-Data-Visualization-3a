"""Alpha Vantage querying and chart building for the Stock Data Visualizer.

get_data() and make_chart() come from Project 3 (JK-5.py). The changes for the
web version are:
  - errors raise StockDataError (shown on the page) instead of print()
  - make_chart() returns the SVG so Flask can put it in the page, instead of
    writing chart.svg and opening a browser
"""

import csv
import os
import re
import time
from datetime import datetime

import pygal
import requests

API_URL = "https://www.alphavantage.co/query"

# form value -> label / pygal chart type used by make_chart()
CHART_TYPES = {
    "1": ("Bar", "bar"),
    "2": ("Line", "line"),
}

# form value -> (label, Alpha Vantage function)
TIME_SERIES = {
    "1": ("Intraday", "TIME_SERIES_INTRADAY"),
    "2": ("Daily", "TIME_SERIES_DAILY"),
    "3": ("Weekly", "TIME_SERIES_WEEKLY"),
    "4": ("Monthly", "TIME_SERIES_MONTHLY"),
}

# Same rule Project 3 used for the console input: 1-10 chars of A-Z, 0-9, "." or "-"
SYMBOL_PATTERN = re.compile(r"[A-Z0-9.-]{1,10}")


class StockDataError(Exception):
    """Raised when stock data can't be retrieved or charted."""


def load_symbols(csv_path):
    """Read stock symbols from a CSV file to fill the drop-down.

    Uses a column named Symbol/Ticker if the file has a header, otherwise the
    first column. Returns a sorted list of unique, upper-case symbols.
    """
    symbols = set()
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
    except OSError:
        return []
    if not rows:
        return []

    header = [h.strip().lower() for h in rows[0]]
    col = 0
    start = 0
    for name in ("symbol", "ticker"):
        if name in header:
            col = header.index(name)
            start = 1
            break

    for row in rows[start:]:
        if len(row) > col:
            sym = row[col].strip().upper()
            if SYMBOL_PATTERN.fullmatch(sym):
                symbols.add(sym)
    return sorted(symbols)


def _request(params):
    try:
        response = requests.get(API_URL, params=params, timeout=15)
        return response.json()
    except Exception as e:
        raise StockDataError("Could not get data from Alpha Vantage. Check your internet.") from e


def get_data(symbol, function):
    """Ask Alpha Vantage for the stock data and return it as a dictionary."""
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise StockDataError("No API key found. Put it in your .env file as API_KEY.")

    params = {
        "function": function,
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "full",
    }

    # needs an interval, the other functions do not
    if function == "TIME_SERIES_INTRADAY":
        params["interval"] = "60min"

    data = _request(params)

    # sends errors back inside the json, so check for them
    if "Error Message" in data:
        raise StockDataError("Symbol not found. Check the stock symbol.")

    # the free key may not allow the full 20 years, so try again with less data
    if "Information" in data and params["outputsize"] == "full":
        params["outputsize"] = "compact"
        time.sleep(2)  # free keys only allow 1 request per second
        data = _request(params)

    if "Note" in data or "Information" in data:
        # show what the API actually said so we know the real reason
        raise StockDataError("The API gave a message: " + (data.get("Note") or data.get("Information")))

    # the name of the data section changes depending on the function
    for key in data:
        if "Time Series" in key:
            return data[key]

    raise StockDataError("No time series data in the response.")


def make_chart(symbol, data, chart_type, start, end):
    """Make the chart for the dates between start and end and return it as SVG."""
    dates = []
    opens = []
    highs = []
    lows = []
    closes = []

    # go oldest to newest so the chart reads left to right
    for date in sorted(data.keys()):
        day = datetime.strptime(date[:10], "%Y-%m-%d").date()
        if start <= day <= end:
            dates.append(date)
            opens.append(float(data[date]["1. open"]))
            highs.append(float(data[date]["2. high"]))
            lows.append(float(data[date]["3. low"]))
            closes.append(float(data[date]["4. close"]))

    if len(dates) == 0:
        raise StockDataError("No data for those dates. Try a different date range or time series.")

    if chart_type == "bar":
        chart = pygal.Bar(x_label_rotation=45, width=1000, height=500)
    else:
        chart = pygal.Line(x_label_rotation=45, width=1000, height=500)

    chart.title = "Stock Data for " + symbol + ": " + str(start) + " to " + str(end)
    chart.x_labels = dates
    chart.x_labels_major_count = 10
    chart.show_minor_x_labels = False
    chart.add("Open", opens)
    chart.add("High", highs)
    chart.add("Low", lows)
    chart.add("Close", closes)

    return chart.render(is_unicode=True)


def show_stock_chart(symbol, chart_type, function, start, end):
    """Get the data and build the chart. start and end are date objects."""
    data = get_data(symbol.upper(), function)
    return make_chart(symbol.upper(), data, chart_type, start, end)
