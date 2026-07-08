from langchain_core.output_parsers import StrOutputParser

from server.llm import llm
from server.prompt import prompt


parser = StrOutputParser()

chain = prompt | llm | parser