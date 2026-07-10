import os
from dotenv import load_dotenv

load_dotenv()

OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER_KEY")

if OPEN_ROUTER_KEY is None:
    raise ValueError("OPEN_ROUTER_KEY가 없습니다.")
