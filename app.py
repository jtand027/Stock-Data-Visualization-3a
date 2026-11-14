"""Flask web app for the Stock Data Visualizer (Project 3a)."""

import os
from datetime import date, datetime

from flask import Flask, flash, render_template, request
from markupsafe import Markup

from stock_api import (
    CHART_TYPES,
    SYMBOL_PATTERN,
    TIME_SERIES,
    StockDataError,
    load_symbols,
    show_stock_chart,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

SYMBOLS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stocks.csv")


def parse_choice(value, minimum, maximum, label, errors):
    """Same check as Project 3: must be an integer between minimum and maximum."""
    if not value:
        errors.append(f"Please select a {label}.")
        return None
    try:
        number = int(value)
    except ValueError:
        errors.append(f"Error: {label.capitalize()} is not a valid integer.")
        return None
    if not minimum <= number <= maximum:
        errors.append(f"Error: {label.capitalize()} must be between {minimum} and {maximum}.")
        return None
    return str(number)


def parse_date(value, label, errors):
    """Same check as Project 3: must be a real date in YYYY-MM-DD format."""
    if not value:
        errors.append(f"Please enter a {label}.")
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        errors.append(f"Error: Invalid {label} or format. Please use the YYYY-MM-DD format.")
        return None
    if parsed > date.today():
        errors.append(f"Error: {label.capitalize()} cannot be in the future.")
        return None
    return parsed


def validate(form, symbols):
    """Check every form field. Returns (errors, cleaned_values)."""
    errors = []

    # Stock symbol
    symbol = form.get("symbol", "").strip().upper()
    if not symbol:
        errors.append("Please select a stock symbol.")
    elif not SYMBOL_PATTERN.fullmatch(symbol):
        errors.append('Invalid input. Stock symbol must be between 1 and 10 characters '
                      'and only contain A-Z, 0-9, "." or "-".')
    elif symbol not in symbols:
        errors.append(f"'{symbol}' is not in the list of available stock symbols.")

    # Chart type (1-2) and time series (1-4)
    chart_type = parse_choice(form.get("chart_type", ""), 1, len(CHART_TYPES), "chart type", errors)
    time_series = parse_choice(form.get("time_series", ""), 1, len(TIME_SERIES), "time series", errors)

    # Start and end dates
    start_date = parse_date(form.get("start_date", ""), "start date", errors)
    end_date = parse_date(form.get("end_date", ""), "end date", errors)
    if start_date and end_date and end_date <= start_date:
        errors.append("End date must be after Start date.")

    return errors, {
        "symbol": symbol,
        "chart_type": chart_type,
        "time_series": time_series,
        "start_date": start_date,
        "end_date": end_date,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    symbols = load_symbols(SYMBOLS_CSV)
    if not symbols:
        flash("Could not load stock symbols from stocks.csv.", "error")

    chart = None
    selected = {}

    if request.method == "POST":
        selected = request.form.to_dict()
        errors, values = validate(request.form, symbols)
        if errors:
            for err in errors:
                flash(err, "error")
        else:
            try:
                svg = show_stock_chart(
                    values["symbol"],
                    CHART_TYPES[values["chart_type"]][1],
                    TIME_SERIES[values["time_series"]][1],
                    values["start_date"],
                    values["end_date"],
                )
                chart = Markup(svg)
            except StockDataError as e:
                flash(str(e), "error")
            except Exception:  # never crash the page
                app.logger.exception("Unexpected error building chart")
                flash("Something went wrong while building the chart. Please try again.", "error")

    return render_template(
        "index.html",
        symbols=symbols,
        chart_types={k: v[0] for k, v in CHART_TYPES.items()},
        time_series={k: v[0] for k, v in TIME_SERIES.items()},
        selected=selected,
        chart=chart,
        today=date.today().isoformat(),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
