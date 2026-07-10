from langchain_openai import ChatOpenAI
from server.config import OPEN_ROUTER_KEY

llm=ChatOpenAI(
    model="openai/gpt-5.4",
    temperature=0,
    api_key=OPEN_ROUTER_KEY,
    base_url="https://openrouter.ai/api/v1",
)
