import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY=os.getenv("OPEN_API_KEY")

if OPENAI_API_KEY is None:
    raise ValueError("OPEN_API_KEY가 없습니다.")