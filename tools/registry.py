"""
Central registry for all mock tools.

Each tool entry contains:
- name
- description
- input schema
- implementation function

The agent and tool schema builder use this registry to determine
which tools are available for a task.
"""

from tools.impls import (
    get_weather,
    search_web,
    currency_convert,
    get_stock_price,
    send_email,
    book_flight,
    get_calendar_events,
    create_calendar_event,
    translate_text,
    get_stock_price_v2,
    calculator,
    get_news,
    search_documents,
    summarize_text,
    get_current_time,
    lookup_contact,
)

TOOLS = {

    "get_weather": {
        "description": "Retrieve the current weather for a city.",
        "parameters": {
            "city": {
                "type": "string",
                "required": True
            }
        },
        "function": get_weather
    },

    "search_web": {
        "description": "Search the web for information.",
        "parameters": {
            "query": {
                "type": "string",
                "required": True
            }
        },
        "function": search_web
    },

    "currency_convert": {
        "description": "Convert an amount between two currencies.",
        "parameters": {
            "amount": {
                "type": "number",
                "required": True
            },
            "from_currency": {
                "type": "string",
                "required": True
            },
            "to_currency": {
                "type": "string",
                "required": True
            }
        },
        "function": currency_convert
    },

    "get_stock_price": {
        "description": "Retrieve a stock's latest market price.",
        "parameters": {
            "ticker": {
                "type": "string",
                "required": True
            }
        },
        "function": get_stock_price
    },

    "send_email": {
        "description": "Send an email to a recipient.",
        "parameters": {
            "recipient": {
                "type": "string",
                "required": True
            },
            "subject": {
                "type": "string",
                "required": True
            },
            "body": {
                "type": "string",
                "required": True
            }
        },
        "function": send_email
    },

    "book_flight": {
        "description": "Book a flight between two cities.",
        "parameters": {
            "origin": {
                "type": "string",
                "required": True
            },
            "destination": {
                "type": "string",
                "required": True
            },
            "date": {
                "type": "string",
                "required": True
            }
        },
        "function": book_flight
    },

    "get_calendar_events": {
        "description": "Retrieve calendar events for a given date.",
        "parameters": {
            "date": {
                "type": "string",
                "required": True
            }
        },
        "function": get_calendar_events
    },

    "create_calendar_event": {
        "description": "Create a calendar event.",
        "parameters": {
            "title": {
                "type": "string",
                "required": True
            },
            "date": {
                "type": "string",
                "required": True
            },
            "time": {
                "type": "string",
                "required": True
            }
        },
        "function": create_calendar_event
    },

    "translate_text": {
        "description": "Translate text into another language.",
        "parameters": {
            "text": {
                "type": "string",
                "required": True
            },
            "target_language": {
                "type": "string",
                "required": True
            }
        },
        "function": translate_text
    },

    "get_stock_price_v2": {
        "description": "Retrieve stock price using symbol and exchange. Similar to get_stock_price.",
        "parameters": {
            "symbol": {
                "type": "string",
                "required": True
            },
            "exchange": {
                "type": "string",
                "required": False
            }
        },
        "function": get_stock_price_v2
    },

    "calculator": {
        "description": "Perform a basic arithmetic operation.",
        "parameters": {
            "operation": {
                "type": "string",
                "required": True
            },
            "a": {
                "type": "number",
                "required": True
            },
            "b": {
                "type": "number",
                "required": True
            }
        },
        "function": calculator
    },

    "get_news": {
        "description": "Retrieve recent news articles for a topic.",
        "parameters": {
            "topic": {
                "type": "string",
                "required": True
            }
        },
        "function": get_news
    },

    "search_documents": {
        "description": "Search an internal document collection.",
        "parameters": {
            "query": {
                "type": "string",
                "required": True
            }
        },
        "function": search_documents
    },

    "summarize_text": {
        "description": "Summarize a block of text.",
        "parameters": {
            "text": {
                "type": "string",
                "required": True
            },
            "max_sentences": {
                "type": "integer",
                "required": False
            }
        },
        "function": summarize_text
    },

    "get_current_time": {
        "description": "Retrieve the current time for a timezone.",
        "parameters": {
            "timezone": {
                "type": "string",
                "required": False
            }
        },
        "function": get_current_time
    },

    "lookup_contact": {
        "description": "Look up a person's contact information.",
        "parameters": {
            "name": {
                "type": "string",
                "required": True
            }
        },
        "function": lookup_contact
    }

}


def get_tool(name: str):
    """Return a single tool definition."""
    return TOOLS.get(name)


def list_tools():
    """Return all registered tools."""
    return list(TOOLS.keys())


def get_tool_subset(tool_names: list[str]) -> dict:
    """
    Return a subset of the tool registry.

    Raises
    ------
    ValueError
        If any requested tool does not exist.
    """

    subset = {}

    for name in tool_names:

        if name not in TOOLS:
            raise ValueError(
                f"Unknown tool '{name}'. "
                f"Available tools: {', '.join(TOOLS.keys())}"
            )

        subset[name] = TOOLS[name]

    return subset

def execute_tool(
    name: str,
    arguments: dict,
):
    """
    Execute a registered tool.

    Parameters
    ----------
    name
        Tool name.

    arguments
        Keyword arguments passed to the tool.

    Returns
    -------
    Any
        Tool output.
    """

    tool = get_tool(name)

    if tool is None:
        raise ValueError(
            f"Unknown tool '{name}'."
        )

    return tool["function"](**arguments)