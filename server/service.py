from server.chain import chain


def generate_answer(question: str, context: str) -> str:
    if not question.strip():
        raise ValueError("question은 비어 있을 수 없습니다.")

    if not context.strip():
        return "제공된 문서에서 관련 내용을 확인할 수 없습니다."

    answer = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    return answer
