"""
Mock implementations for all tools used by the evaluation harness.

Every tool accepts an optional fail_mode argument that allows the
mutation engine to simulate failures.

Supported fail modes:

None            -> normal response
timeout         -> raises TimeoutError
malformed       -> malformed output
wrong_data      -> logically incorrect output
empty           -> empty response
"""

from datetime import datetime
import random


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def _handle_fail_mode(tool_name: str, fail_mode: str | None):

    if fail_mode is None:
        return None

    if fail_mode == "timeout":
        raise TimeoutError(f"{tool_name} timed out")

    if fail_mode == "malformed":
        return {
            "status": "malformed",
            "raw": "{{{broken json"
        }

    if fail_mode == "wrong_data":
        return "__WRONG_DATA__"

    if fail_mode == "empty":
        return {}

    return None

# ---------------------------------------------------------
# Weather
# ---------------------------------------------------------

def get_weather(city: str,
                fail_mode: str | None = None):

    failure = _handle_fail_mode("get_weather", fail_mode)

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "city": city,
                "temperature_c": 999,
                "condition": "volcanic eruption"
            }

        return failure

    return {
        "city": city,
        "temperature_c": 29,
        "condition": "Humid",
        "rain_probability": 0.72
    }

# ---------------------------------------------------------
# Search Web
# ---------------------------------------------------------

def search_web(query: str,
               fail_mode: str |None = None,
               injection_text: str | None = None):

    failure = _handle_fail_mode("search_web", fail_mode)

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "query": query,
                "results": [
                    {
                        "title": "Completely Incorrect",
                        "content": "The Moon is made of cheese."
                    }
                ]
            }

        return failure

    content = f"Search results about {query}"

    if injection_text:
        content += "\n\n" + injection_text

    return {
        "query": query,
        "results": [
            {
                "title": query.title(),
                "content": content
            }
        ]
    }

# ---------------------------------------------------------
# Currency Converter
# ---------------------------------------------------------

def currency_convert(
        amount: float,
        from_currency: str,
        to_currency: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "currency_convert",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "converted_amount": amount * 100
            }

        return failure

    fake_rates = {
        ("USD", "INR"): 83.4,
        ("INR", "USD"): 0.012,
        ("EUR", "USD"): 1.08
    }

    rate = fake_rates.get(
        (from_currency, to_currency),
        1.0
    )

    return {
        "rate": rate,
        "converted_amount": round(amount * rate, 2)
    }

# ---------------------------------------------------------
# Stock Price
# ---------------------------------------------------------

def get_stock_price(
        ticker: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "get_stock_price",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "ticker": ticker,
                "price": -100
            }

        return failure

    fake_prices = {
        "AAPL": 212.51,
        "GOOG": 185.72,
        "MSFT": 492.31,
        "NVDA": 160.18
    }

    return {
        "ticker": ticker,
        "price": fake_prices.get(ticker.upper(), 100.00)
    }

# ---------------------------------------------------------
# Send Email
# ---------------------------------------------------------

def send_email(
        recipient: str,
        subject: str,
        body: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "send_email",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "status": "sent",
                "recipient": "wrong@email.com"
            }

        return failure

    return {
        "status": "sent",
        "recipient": recipient,
        "subject": subject,
        "timestamp": datetime.utcnow().isoformat()
    }

# ---------------------------------------------------------
# Book Flight
# ---------------------------------------------------------

def book_flight(
        origin: str,
        destination: str,
        date: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "book_flight",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "booking_id": None,
                "status": "confirmed"
            }

        return failure

    return {
        "booking_id": f"FLT-{random.randint(10000,99999)}",
        "origin": origin,
        "destination": destination,
        "date": date,
        "status": "confirmed"
    }

# ---------------------------------------------------------
# Calendar Events
# ---------------------------------------------------------

def get_calendar_events(
        date: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "get_calendar_events",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "events": [
                    {
                        "title": "Wrong Event",
                        "time": "25:00"
                    }
                ]
            }

        return failure

    return {
        "date": date,
        "events": [
            {
                "title": "Team Meeting",
                "time": "10:00"
            },
            {
                "title": "Project Review",
                "time": "15:00"
            }
        ]
    }

# ---------------------------------------------------------
# Create Calendar Event
# ---------------------------------------------------------

def create_calendar_event(
        title: str,
        date: str,
        time: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "create_calendar_event",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "event_id": None,
                "status": "created"
            }

        return failure

    return {
        "event_id": f"EVT-{random.randint(1000,9999)}",
        "title": title,
        "date": date,
        "time": time,
        "status": "created"
    }

# ---------------------------------------------------------
# Translate Text
# ---------------------------------------------------------

def translate_text(
        text: str,
        target_language: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "translate_text",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "translated_text": text[::-1],
                "language": target_language
            }

        return failure

    fake_translations = {
        ("hello", "spanish"): "hola",
        ("good morning", "french"): "bonjour",
        ("thank you", "german"): "danke"
    }

    translated = fake_translations.get(
        (text.lower(), target_language.lower()),
        f"[{target_language}] {text}"
    )

    return {
        "translated_text": translated,
        "language": target_language
    }

# ---------------------------------------------------------
# Stock Price V2 (Near Duplicate)
# ---------------------------------------------------------

def get_stock_price_v2(
        symbol: str,
        exchange: str = "NASDAQ",
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "get_stock_price_v2",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "symbol": symbol,
                "exchange": exchange,
                "last_price": 0.0
            }

        return failure

    prices = {
        "AAPL": 212.51,
        "GOOG": 185.72,
        "MSFT": 492.31,
        "NVDA": 160.18
    }

    return {
        "symbol": symbol.upper(),
        "exchange": exchange,
        "last_price": prices.get(symbol.upper(), 100.0),
        "currency": "USD"
    }

# ---------------------------------------------------------
# Calculator
# ---------------------------------------------------------

def calculator(
        operation: str,
        a: float,
        b: float,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "calculator",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "result": 999999
            }

        return failure

    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else None
    }

    return {
        "operation": operation,
        "result": operations.get(operation)
    }

# ---------------------------------------------------------
# Get News
# ---------------------------------------------------------

def get_news(
        topic: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "get_news",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "articles": [
                    {
                        "headline": "Fake News",
                        "summary": "This never happened."
                    }
                ]
            }

        return failure

    return {
        "topic": topic,
        "articles": [
            {
                "headline": f"Latest developments in {topic}",
                "summary": f"Recent updates regarding {topic}."
            },
            {
                "headline": f"{topic} market analysis",
                "summary": "Expert opinions and forecasts."
            }
        ]
    }

# ---------------------------------------------------------
# Search Documents
# ---------------------------------------------------------

def search_documents(
        query: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "search_documents",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "matches": []
            }

        return failure

    return {
        "query": query,
        "matches": [
            {
                "document": "employee_handbook.pdf",
                "snippet": f"Relevant section about '{query}'."
            },
            {
                "document": "project_spec.md",
                "snippet": f"Another occurrence of '{query}'."
            }
        ]
    }

# ---------------------------------------------------------
# Summarize Text
# ---------------------------------------------------------

def summarize_text(
        text: str,
        max_sentences: int = 2,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "summarize_text",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "summary": text
            }

        return failure

    words = text.split()

    summary = " ".join(
        words[: min(len(words), max_sentences * 10)]
    )

    return {
        "summary": summary
    }

# ---------------------------------------------------------
# Get Time
# ---------------------------------------------------------

def get_current_time(
        timezone: str = "UTC",
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "get_current_time",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "time": "99:99:99"
            }

        return failure

    return {
        "timezone": timezone,
        "time": datetime.utcnow().strftime("%H:%M:%S")
    }

# ---------------------------------------------------------
# Lookup Contact
# ---------------------------------------------------------

def lookup_contact(
        name: str,
        fail_mode: str | None = None
):

    failure = _handle_fail_mode(
        "lookup_contact",
        fail_mode
    )

    if failure is not None:

        if failure == "__WRONG_DATA__":
            return {
                "name": "Unknown",
                "email": "invalid@email.com"
            }

        return failure

    contacts = {
        "alice": "alice@example.com",
        "bob": "bob@example.com",
        "charlie": "charlie@example.com"
    }

    return {
        "name": name,
        "email": contacts.get(
            name.lower(),
            "not_found@example.com"
        )
    }
