from langchain_core.documents import Document
from rag.retriever import retrieve
from server.chain import chain
from server.query import expand_query


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


def _deduplicate_documents(documents: list[Document]) -> list[Document]:
    unique_documents = []
    seen = set()

    for document in documents:
        key = (
            _get_metadata_value(document, "법령명"),
            _get_metadata_value(document, "조문번호"),
            document.page_content[:120],
        )
        if key in seen:
            continue

        seen.add(key)
        unique_documents.append(document)

    return unique_documents


def _retrieve_documents(question: str) -> list[Document]:
    documents = []

    for query in expand_query(question):
        documents.extend(retrieve(query, k=SEARCH_TOP_K_PER_QUERY))

    return _deduplicate_documents(documents)[:MAX_CONTEXT_DOCUMENTS]


def generate_answer(question: str, context: str = "") -> str:
    if not question.strip():
        raise ValueError("question은 비어 있을 수 없습니다.")

    if not context.strip():
        documents = _retrieve_documents(question)
        context = _format_context(documents)

    if not context.strip():
        return "제공된 문서에서 관련 내용을 확인할 수 없습니다."

    return chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )
