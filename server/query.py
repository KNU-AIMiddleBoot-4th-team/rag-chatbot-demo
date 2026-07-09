import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from server.llm import llm


MAX_EXPANDED_QUERIES = 5

query_prompt = ChatPromptTemplate.from_template(
    """
사용자의 질문을 법률 문서 검색에 적합한 검색어로 확장한다.

사용자 질문:
{question}

관련 법률 용어, 유사 표현, 상위 개념을 포함하여
검색 질의 5개를 생성한다.

각 검색 질의는 한 줄에 하나씩만 작성한다.
번호, 따옴표, 설명은 쓰지 않는다.
"""
)

query_chain = query_prompt | llm | StrOutputParser()


def _normalize_query(line: str) -> str:
    query = line.strip()
    query = re.sub(r"^\s*[-*]\s*", "", query)
    query = re.sub(r"^\s*\d+[\).\s-]*", "", query)
    query = query.strip().strip("\"'")
    return query.strip()


def expand_query(question: str) -> list[str]:
    if not question.strip():
        return []

    try:
        result = query_chain.invoke({"question": question})
    except Exception:
        return [question]

    queries = [question]
    seen = {question}

    for line in result.splitlines():
        query = _normalize_query(line)
        if not query or query in seen:
            continue

        seen.add(query)
        queries.append(query)

        if len(queries) >= MAX_EXPANDED_QUERIES + 1:
            break

    return queries
