import httpx
from typing import Optional
from uuid import uuid4
from langchain_core.tools import tool

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