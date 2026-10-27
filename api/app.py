import httpx
from typing import Optional
from uuid import uuid4
from langchain_core.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://hopscotch-shop.vercel.app"

email = input("your shopping email: ").strip();

response = httpx.post(
    f"{API_URL}/auth/login",
    json={"email": email},
    timeout=30
)

response.raise_for_status()
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}


@tool
def get_cart() -> dict:
    """Inspect the signed-in customer's current cart.

    Use for questions about cart contents, quantities, and totals.
    Takes no arguments. Returns the current cart items and totals.
    Money values are integer paise: 100 paise equals INR 1.
    This tool only reads the cart; it cannot edit it or place an order.
    """
    response = httpx.get(f"{API_URL}/cart", headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


@tool
def get_orders(order_id: Optional[str] = None) -> dict:
    """List the signed-in customer's orders or inspect a specific order.

    Use for order questions and before cancelling an order item.
    Omit order_id to list orders; provide a real order_id to inspect one.
    Results contain order IDs, item IDs, original quantities, cancelled
    quantities, active quantities, statuses, and totals.
    Use these results to identify the real order_id and item_id and check
    the active quantity before requesting cancellation. Never guess IDs.
    Money values are integer paise: 100 paise equals INR 1.
    This tool only reads orders; it does not change them.

    Args:
        order_id: Optional real order identifier returned by this tool.
    """
    path = "/orders" if order_id is None else f"/orders/{order_id}"
    response = httpx.get(f"{API_URL}{path}", headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

@tool
def cancel_item(order_id: str, item_id: str, quantity: int) -> dict:
    """Cancel a selected whole-number quantity of an existing order item.

    Use only when the user explicitly requests cancellation and clearly
    identifies the order, item, and quantity.
    First call get_orders and read its tool result to discover the real
    order_id, item_id, and current active quantity. Do that prerequisite
    read before requesting this tool; never guess identifiers.
    Quantity must be an integer from 1 to 99 and must not exceed the item's
    active quantity. If the order, item, or quantity is ambiguous, explain
    what information is missing and do not cancel.
    Returns the updated order and operation details. Claim success only
    after receiving a successful API result. Money is in integer paise:
    100 paise equals INR 1.
    Each invocation creates a new cancellation request. Do not repeat it
    blindly after an error; inspect the order before taking further action.
    This tool cannot cancel an entire order, place orders, edit carts,
    process refunds, or search the web.

    Args:
        order_id: Real order identifier obtained from get_orders.
        item_id: Real item identifier within that order from get_orders.
        quantity: Number of active units the user explicitly wants cancelled.
    """
    response = httpx.post(
        f"{API_URL}/orders/{order_id}/items/{item_id}/cancel",
        headers=headers,
        json={"quantity": quantity, "operation_id": str(uuid4())},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()



from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

sysmsg = """
You are a helpful assistant for the Hopscotch online store.

You can help customers inspect their shopping cart, view or inspect their orders, and cancel items from their existing active orders.

Use your tools appropriately when a customer asks questions about their cart, orders, or requests a cancellation.
"""

llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
    temperature=0
)

llm_with_tools = llm.bind_tools(
    [get_cart, get_orders, cancel_item]
)

# sagarkadu17@gmail.com

system_message = SystemMessage(sysmsg)
user_query = input("Enter your message: ")
user_message = HumanMessage(user_query)
message_to_send = [system_message, user_message]
response = llm_with_tools.invoke(message_to_send)

from langchain_community.tools import DuckDuckGoSearchRun

@tool
def get_city_weather(city: str):
    """
    Fetches the current weather conditions for a specified city.

    Use this tool whenever a user asks about the weather, temperature,
    or humidity in a specific location.

    Args:
        city (str): The name of the city to check the weather for.
                    Examples: "Delhi", "Mumbai", "Bengaluru", "New York".

    Returns:
        dict: A dictionary containing the weather details with the following keys:
            - temperature (int): The current temperature in degrees Celsius.
            - humidity (int): The relative humidity percentage.
            - condition (str): A brief, readable description of the weather
                               (e.g., "Hot", "Humid", "Pleasant", "Unknown").
    """
    fake_weather_db = {
        "Delhi": {"temperature": 34, "humidity": 48, "condition": "Hot"},
        "Mumbai": {"temperature": 31, "humidity": 78, "condition": "Humid"},
        "Bengaluru": {"temperature": 27, "humidity": 60, "condition": "Pleasant"},
    }
    return fake_weather_db.get(
        city,
        {"temperature": 30, "humidity": 50, "condition": "Unknown"}
    )

duckduckgo_search = DuckDuckGoSearchRun()
duckduckgo_search.invoke({"query": "What is the situation in Goaright now?"})