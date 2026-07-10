from langchain_core.documents import Document
from rag.retriever import retrieve_with_score
from server.chain import chain
from server.query import expand_query, format_history, rewrite_question


SEARCH_TOP_K_PER_QUERY = 3
MAX_CONTEXT_DOCUMENTS = 6


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
        return "제공된 문서에서 관련 내용을 확인할 수 없습니다."

    return chain.invoke(
        {
            "context": context,
            "question": question,
            "history": format_history(history),
        }
    )
