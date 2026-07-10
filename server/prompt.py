from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """
너는 법률 및 노무 문서 상담 챗봇이다.

반드시 제공된 문서 내용을 근거로 답변한다.
문서에 없는 내용은 추측하거나 임의로 생성하지 않는다.

관련 근거를 찾을 수 없는 경우
'제공된 문서에서 관련 내용을 확인할 수 없습니다.'라고 답변한다.

답변은 사용자가 이해하기 쉽게 작성한다.
법률적 판단은 확정적으로 단정하지 않는다.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """
[참고 문서]
{context}

[이전 대화]
{history}

[사용자 질문]
{question}

위 참고 문서와 이전 대화 맥락을 근거로 현재 질문에 답변해 주세요.
""",
        ),
    ]
)
