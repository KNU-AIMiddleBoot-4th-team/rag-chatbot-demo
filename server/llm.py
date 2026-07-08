from langchain_openai import ChatOpenAI
from server.config import OPENAI_API_KEY

llm=ChatOpenAI(
    model="openai/gpt-4.1-mini",
    temperature=0,
    api_key=OPENAI_API_KEY
)