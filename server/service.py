from concurrent.futures import Future, ThreadPoolExecutor

from langchain_core.documents import Document
from rag.retriever import retrieve_with_score
from server.chain import chain
from server.query import expand_query, format_history, rewrite_question, suggest_followups

_suggest_executor = ThreadPoolExecutor(max_workers=1)


SEARCH_TOP_K_PER_QUERY = 3
MAX_CONTEXT_DOCUMENTS = 6
NO_RELEVANT_CONTEXT_MESSAGE = "제공된 문서에서 관련 내용을 확인할 수 없습니다."


def _get_metadata_value(document: Document, *keys: str) -> str:
    for key in keys:
        value = document.metadata.get(key)
        if value:
            return str(value)
    return ""


def _format_context(documents: list[Document]) -> str:
    context_blocks = []

    for document in documents:
        law_name = _get_metadata_value(document, "법령명")
        article_no = _get_metadata_value(document, "조문번호")
        article_title = _get_metadata_value(document, "조문제목")

        title = " ".join(part for part in [law_name, article_no, article_title] if part)
        if title:
            context_blocks.append(f"[{title}]\n{document.page_content}")
        else:
            context_blocks.append(document.page_content)

    return "\n\n---\n\n".join(context_blocks)


def _get_document_key(document: Document) -> tuple[str, str]:
    return (str(document.metadata), document.page_content[:120])


def _rank_documents_by_score(
    document_scores: list[tuple[Document, float]]
) -> list[Document]:
    best_documents: dict[tuple[str, str], tuple[Document, float]] = {}

    for document, score in document_scores:
        key = _get_document_key(document)
        current = best_documents.get(key)

        if current is None or score < current[1]:
            best_documents[key] = (document, score)

    ranked_documents = sorted(best_documents.values(), key=lambda item: item[1])
    return [document for document, _ in ranked_documents]


def _retrieve_documents(question: str) -> list[Document]:
    document_scores = []

    for query in expand_query(question):
        document_scores.extend(retrieve_with_score(query, k=SEARCH_TOP_K_PER_QUERY))

    return _rank_documents_by_score(document_scores)[:MAX_CONTEXT_DOCUMENTS]


def _build_chain_inputs(
    question: str,
    context: str = "",
    history: list[dict[str, str]] | None = None,
) -> tuple[dict[str, str] | None, str]:
    """chain 입력 dict와 확정된 context 문자열을 함께 반환한다."""
    if not question.strip():
        raise ValueError("question must not be empty.")

    if not context.strip():
        search_question = rewrite_question(question, history)
        documents = _retrieve_documents(search_question)
        context = _format_context(documents)

    if not context.strip():
        return None, ""

    return {
        "context": context,
        "question": question,
        "history": format_history(history),
    }, context


def generate_answer(
    question: str,
    context: str = "",
    history: list[dict[str, str]] | None = None,
) -> str:
    if not question.strip():
        raise ValueError("question은 비어 있을 수 없습니다.")

    if not context.strip():
        search_question = rewrite_question(question, history)
        documents = _retrieve_documents(search_question)
        context = _format_context(documents)

    if not context.strip():
        return NO_RELEVANT_CONTEXT_MESSAGE

    return chain.invoke(
        {
            "context": context,
            "question": question,
            "history": format_history(history),
        }
    )


def resolve_context(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """벡터 검색까지만 수행하고 context 문자열만 반환한다.

    UI에서 context를 미리 뽑아 start_suggest_followups에 넘길 때 사용한다.
    """
    search_question = rewrite_question(question, history)
    documents = _retrieve_documents(search_question)
    return _format_context(documents)


def generate_answer_stream(
    question: str,
    context: str = "",
    history: list[dict[str, str]] | None = None,
):
    chain_inputs, resolved_context = _build_chain_inputs(question, context, history)
    if chain_inputs is None:
        yield NO_RELEVANT_CONTEXT_MESSAGE
        return

    for chunk in chain.stream(chain_inputs):
        if chunk:
            yield str(chunk)


def start_suggest_followups(question: str, context: str) -> Future:
    """후속 추천 질문 생성을 백그라운드에서 시작하고 Future를 반환한다.

    답변 스트리밍과 동시에 실행되므로 응답 시간에 영향을 주지 않는다.
    caller가 Future.result()로 list[str]을 꺼내 쓴다.
    """
    return _suggest_executor.submit(suggest_followups, question, context)
