"""대화 히스토리 렌더링과 사용자 질문 처리.

실제 답변 생성은 server.service.generate_answer 로만 위임한다.
(직접 OpenAI 호출이나 임베딩/검색을 이 프론트에서 수행하지 않는다.)
"""

import streamlit as st

SPINNER_TEXT = "관련 법령을 찾아 답변을 작성하고 있어요..."


def render_history() -> None:
    """세션에 쌓인 대화를 순서대로 그린다."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def _ask_server(question: str) -> str:
    """server 계층에 질문 + 이전 대화(history)를 넘겨 답변을 받는다.

    session_state.messages 의 마지막 항목은 방금 입력한 질문이므로 제외하고
    그 이전까지를 대화 맥락(history)으로 전달한다(기억 기능).
    """
    # 서버 의존성(langchain/chroma)은 첫 질문 때만 로드되도록 지연 import.
    from server.service import generate_answer

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]
    return generate_answer(question=question, history=history)


def handle_user_turn(user_input: str | None) -> None:
    """입력을 받아 같은 실행 안에서 질문 표시 → 로딩 → 답변을 순서대로 그린다.

    질문 말풍선을 먼저 그리고, 바로 아래 assistant 말풍선에서 스피너를 돌린 뒤
    같은 자리에 답변을 채운다. 화면 전환/점프 없이 "위에서 로딩 중 → 그대로 답변"이 된다.
    (레이아웃 모드는 app.py에서 입력 유무로 미리 결정하므로 여기서 rerun 하지 않는다.)
    """
    if not user_input:
        return

    # 방금 입력한 질문을 즉시 말풍선으로 표시.
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 바로 아래 assistant 말풍선에서 로딩 → 답변을 같은 자리에 채운다.
    with st.chat_message("assistant"):
        with st.spinner(SPINNER_TEXT):
            try:
                answer = _ask_server(user_input)
            except Exception as exc:  # noqa: BLE001 - 사용자에게는 안내, 콘솔에는 원인 출력
                print(f"[chat] 답변 생성 실패: {exc!r}")
                answer = (
                    "⚠️ 답변을 생성하는 중 문제가 발생했어요. "
                    "잠시 후 다시 시도해 주세요."
                )
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
