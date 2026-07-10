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
if "faq_questions" not in st.session_state:
    st.session_state.faq_questions = None    # 동적 추천 질문 (None이면 고정 FAQ 사용)
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False   # 질문 처리 중이면 True

# ── 입력 먼저 읽기 ───────────────────────────────
# 이번 렌더가 "대화 화면"인지 입력 유무로 미리 판단해야 레이아웃이 튀지 않고,
# 첫 질문이 중앙 입력창에 가려지지 않는다.
user_input = st.chat_input("여기에 질문을 입력하세요...")
if st.session_state.queued_question:
    user_input = st.session_state.queued_question
    st.session_state.queued_question = None

chat_mode = bool(st.session_state.messages) or bool(user_input)

# 입력이 들어온 순간 처리 중으로 표시 — render_faq() 전에 세팅해야 이번 렌더에 반영됨
if user_input:
    st.session_state.is_processing = True

# ── 스타일 ──────────────────────────────────────
inject_base_styles()
inject_layout_styles(chat_mode)

# ── 화면 구성 ────────────────────────────────────
render_logo_header()
if not chat_mode:
    render_welcome()

render_history()
# 처리 중이 아닐 때만 FAQ 렌더: 초기 화면은 고정 FAQ, 답변 후엔 동적 추천
if not st.session_state.is_processing:
    render_faq()
render_attach()
render_focus_script()

# ── 입력 처리 (질문 표시 → 로딩 → 답변, 같은 자리) ──
handle_user_turn(user_input)
