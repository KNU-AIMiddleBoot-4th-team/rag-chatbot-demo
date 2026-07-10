"""법률/노무 AI 챗봇 — Streamlit 프론트엔드 진입점.

이 파일은 화면을 조립하고 사용자 입력을 받는 역할만 한다.
- 답변 생성: server.service.generate_answer 로 위임 (직접 LLM/임베딩 호출 없음)
- UI 조각: ui 패키지(styles / components / chat)에 분리
"""

import streamlit as st

from ui.styles import inject_base_styles, inject_layout_styles
from ui.components import (
    render_attach,
    render_faq,
    render_focus_script,
    render_logo_header,
    render_welcome,
)
from ui.chat import handle_user_turn, render_history

st.set_page_config(page_title="법률/노무 AI 챗봇", page_icon="⚖️", layout="centered")

# ── 세션 상태 초기화 ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []          # [{"role": "user"|"assistant", "content": str}]
if "queued_question" not in st.session_state:
    st.session_state.queued_question = None  # FAQ 버튼으로 예약된 질문

# ── 입력 먼저 읽기 ───────────────────────────────
# 이번 렌더가 "대화 화면"인지 입력 유무로 미리 판단해야 레이아웃이 튀지 않고,
# 첫 질문이 중앙 입력창에 가려지지 않는다.
user_input = st.chat_input("여기에 질문을 입력하세요...")
if st.session_state.queued_question:
    user_input = st.session_state.queued_question
    st.session_state.queued_question = None

chat_mode = bool(st.session_state.messages) or bool(user_input)

# ── 스타일 ──────────────────────────────────────
inject_base_styles()
inject_layout_styles(chat_mode)

# ── 화면 구성 ────────────────────────────────────
render_logo_header()
if not chat_mode:
    render_welcome()

render_history()
# 추천질문(FAQ)은 시작 화면과 대화 화면 모두에서 노출한다(위치만 레이아웃에서 달라짐).
render_faq()
render_attach()
render_focus_script()

# ── 입력 처리 (질문 표시 → 로딩 → 답변, 같은 자리) ──
handle_user_turn(user_input)
