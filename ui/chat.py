"""대화 히스토리 렌더링과 사용자 질문 처리.

실제 검색·답변 생성은 server.service.generate_answer_stream 으로 위임한다.
(직접 OpenAI 호출이나 임베딩/검색을 이 프론트에서 수행하지 않는다.)
"""

import itertools
import time

import streamlit as st

SPINNER_TEXT = "관련 법령을 찾고 있어요..."
# 타자기처럼 자연스럽게 출력하기 위한 글자당 지연(초). 키우면 더 천천히 나온다.
STREAM_CHAR_DELAY = 0.015


def render_history() -> None:
    """세션에 쌓인 대화를 순서대로 그린다."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def _history_payload() -> list[dict[str, str]]:
    """현재 질문 직전까지의 대화를 server 에 넘길 history 로 변환한다(기억 기능).

    session_state.messages 의 마지막 항목은 방금 입력한 질문이라 제외한다.
    """
    return [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]


def _typewriter(chunks):
    """토큰 조각들을 글자 단위로 잘게 나눠 타자기처럼 흘려준다.

    LLM 이 뱉는 속도 그대로면 너무 빨라서, 글자마다 짧은 지연을 준다.
    """
    for chunk in chunks:
        for char in chunk:
            yield char
            if STREAM_CHAR_DELAY:
                time.sleep(STREAM_CHAR_DELAY)


def handle_user_turn(user_input: str | None) -> None:
    """입력을 받아 질문 표시 → (검색 스피너) → 답변 스트리밍을 순서대로 그린다.

    질문 말풍선을 먼저 그리고, 바로 아래 assistant 말풍선에서 검색 동안 스피너를 돌린 뒤
    최종 답변을 토큰 단위로 실시간 출력한다.
    답변 스트리밍 시작과 동시에 후속 추천 질문을 백그라운드에서 생성한다.
    (레이아웃 모드는 app.py에서 입력 유무로 미리 결정하므로 여기서 rerun 하지 않는다.)
    """
    if not user_input:
        return

    # 방금 입력한 질문을 즉시 말풍선으로 표시.
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            from server.service import generate_answer_stream, resolve_context, start_suggest_followups

            history = _history_payload()

            # 검색(context 확정)까지 스피너로 대기
            with st.spinner(SPINNER_TEXT):
                context = resolve_context(user_input, history)
                # context가 확정된 순간 백그라운드에서 추천 질문 생성 시작
                suggest_future = start_suggest_followups(user_input, context)
                stream = generate_answer_stream(question=user_input, context=context, history=history)
                first_chunk = next(stream, "")

            # 답변 스트리밍 (추천 질문은 이 사이에 백그라운드에서 완성됨)
            answer = st.write_stream(
                _typewriter(itertools.chain([first_chunk], stream))
            )

            # 답변 저장 → 추천 질문 수집 → 처리 완료 → FAQ 영역 복원
            st.session_state.messages.append({"role": "assistant", "content": answer})
            suggestions = suggest_future.result(timeout=10)
            if suggestions:
                st.session_state.faq_questions = suggestions
            st.session_state.is_processing = False
            st.rerun()

        except Exception as exc:  # noqa: BLE001
            print(f"[chat] 답변 생성 실패: {exc!r}")
            answer = "⚠️ 답변을 생성하는 중 문제가 발생했어요. 잠시 후 다시 시도해 주세요."
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.is_processing = False
            st.rerun()
