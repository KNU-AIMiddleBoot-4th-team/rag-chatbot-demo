from langchain_core.documents import Document
from rag.retriever import retrieve
from server.chain import chain


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


def generate_answer(question: str, context: str = "") -> str:
    if not question.strip():
        raise ValueError("question은 비어 있을 수 없습니다.")

    if not context.strip():
        documents = retrieve(question, k=4)
        context = _format_context(documents)

    if not context.strip():
        return "제공된 문서에서 관련 내용을 확인할 수 없습니다."

    return chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )
