import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from server.llm import llm


MAX_EXPANDED_QUERIES = 5
MAX_HISTORY_MESSAGES = 10
SUGGEST_COUNT = 3

suggest_prompt = ChatPromptTemplate.from_template(
    """
사용자 질문: {question}
참고한 법 조문: {context}

위 질문과 법 조문을 바탕으로 사용자가 이어서 물어볼 만한 후속 질문 {count}개를 제안한다.

규칙:
- 질문은 짧고 자연스러운 한국어 구어체로 작성한다 (20자 이내 권장).
- 법률/노무 주제를 벗어나지 않는다.
- 각 질문은 한 줄에 하나씩만 작성한다.
- 번호, 따옴표, 설명은 쓰지 않는다.
"""
)

suggest_chain = suggest_prompt | llm | StrOutputParser()

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

rewrite_prompt = ChatPromptTemplate.from_template(
    """
이전 대화를 참고하여 현재 질문을 법률 문서 검색에 적합한 완전한 질문으로 다시 작성한다.

이전 대화:
{history}

현재 질문:
{question}

규칙:
- 현재 질문이 이미 완전하면 그대로 둔다.
- "그럼 예외는?", "그건 언제까지야?"처럼 이전 대화가 필요한 질문은 맥락을 보완한다.
- 법률 문서 검색에 필요한 핵심 법률 용어를 포함한다.
- 답변하지 말고, 검색에 사용할 질문 한 문장만 작성한다.
"""
)

rewrite_chain = rewrite_prompt | llm | StrOutputParser()


def format_history(history: list[dict[str, str]] | None) -> str:
    if not history:
        return "이전 대화 없음"

    lines = []
    for message in history[-MAX_HISTORY_MESSAGES:]:
        role = message.get("role", "")
        content = message.get("content", "").strip()
        if not content:
            continue

        speaker = "사용자" if role == "user" else "챗봇"
        lines.append(f"{speaker}: {content}")

    return "\n".join(lines) if lines else "이전 대화 없음"


def _normalize_query(line: str) -> str:
    query = line.strip()
    query = re.sub(r"^\s*[-*]\s*", "", query)
    query = re.sub(r"^\s*\d+[\).]\s+", "", query)
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


def suggest_followups(question: str, context: str) -> list[str]:
    """질문과 검색된 법 조문을 바탕으로 후속 추천 질문 3개를 반환한다."""
    if not question.strip():
        return []

    try:
        result = suggest_chain.invoke({
            "question": question,
            "context": context[:1500],
            "count": SUGGEST_COUNT,
        })
    except Exception:
        return []

    suggestions = []
    for line in result.splitlines():
        q = _normalize_query(line)
        if q:
            suggestions.append(q)
        if len(suggestions) >= SUGGEST_COUNT:
            break

    return suggestions


def rewrite_question(question: str, history: list[dict[str, str]] | None = None) -> str:
    if not question.strip() or not history:
        return question

    try:
        result = rewrite_chain.invoke(
            {
                "history": format_history(history),
                "question": question,
            }
        )
    except Exception:
        return question

    rewritten_question = _normalize_query(result.splitlines()[0] if result else "")
    return rewritten_question or question
