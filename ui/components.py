"""로고, 웰컴 문구, FAQ 버튼, 첨부 버튼 등 정적 UI 조각들."""

import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "Tori.png"

FAQ_QUESTIONS = [
    "📝 근로계약서 작성 시 반드시 포함해야 할 조항이 무엇인가요?",
    "💼 부당해고 구제신청은 어떻게 진행하나요?",
    "⏱️ 연장근로수당 계산 기준이 궁금합니다.",
]


def render_logo_header() -> None:
    """좌측 상단 고정 로고 + 서비스명."""
    if not LOGO_PATH.exists():
        return
    with st.container(key="logo_header"):
        col_logo, col_title = st.columns([1, 4])
        with col_logo:
            st.image(str(LOGO_PATH))
        with col_title:
            st.markdown("<span>법률/노무 AI 챗봇</span>", unsafe_allow_html=True)


def render_welcome() -> None:
    """대화 시작 전 중앙 안내 문구."""
    st.markdown(
        """
        <div class="chat-welcome">
            <h1>법률/노무에 대해 궁금한 점이 있으신가요<span class="brand-dot">?</span></h1>
            <p>근로계약 · 해고 · 임금 · 퇴직금 관련 법령을 근거로 답변해 드려요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_faq() -> None:
    """자주 묻는 질문 버튼. 대화 후에는 동적 추천 질문으로 교체된다."""
    questions = st.session_state.get("faq_questions") or FAQ_QUESTIONS
    with st.container(key="faq_area"):
        faq_cols = st.columns(3, gap="medium")
        for i, question in enumerate(questions):
            with faq_cols[i]:
                # 이모지 접두사가 없는 동적 질문은 그대로, 고정 질문은 이모지 제거
                label = question if question in FAQ_QUESTIONS else question
                if st.button(label, key=f"faq_{i}", use_container_width=True):
                    clean = question.split(" ", 1)[1] if question in FAQ_QUESTIONS else question
                    st.session_state.queued_question = clean
                    st.rerun()


def render_attach() -> None:
    """첨부(➕) 버튼. 현재는 UI 껍데기이며 서버로 전달되지 않는다."""
    with st.container(key="attach_area"):
        with st.popover("➕"):
            st.markdown("**첨부하기**")
            attach_type = st.radio(
                "첨부 유형",
                ["🖼️ 사진", "🎬 동영상", "📎 파일"],
                label_visibility="collapsed",
            )
            if attach_type == "🖼️ 사진":
                st.file_uploader("사진 선택", type=["png", "jpg", "jpeg", "heic"], key="up_img")
            elif attach_type == "🎬 동영상":
                st.file_uploader("동영상 선택", type=["mp4", "mov", "avi"], key="up_vid")
            else:
                st.file_uploader("파일 선택", type=["pdf", "docx", "hwp", "txt"], key="up_file")


def render_focus_script() -> None:
    """페이지 로드 시 입력창 포커스 + FAQ 위치를 입력창 높이에 맞게 동적 보정."""
    components.html(
        """
        <script>
        (function () {
            var doc = window.parent.document;

            /* ── 입력창 자동 포커스 ── */
            function focusChatInput() {
                try {
                    var ta = doc.querySelector('[data-testid="stChatInput"] textarea');
                    if (ta) ta.focus();
                } catch (e) {}
            }
            [50, 150, 350, 700].forEach(function (d) { setTimeout(focusChatInput, d); });

            /* ── FAQ bottom을 입력창 컨테이너 높이에 맞게 동적 계산 ──
               stBottomBlockContainer의 실제 렌더 높이를 읽어서
               FAQ 영역의 bottom 값에 그 높이 + 여백(8px)을 반영한다.
               DOM을 이동하지 않고 좌표만 조정하므로 안전하다.
               셀렉터가 깨지거나 ResizeObserver가 없으면 조용히 종료한다. */
            function attachFaqObserver() {
                try {
                    var bottomContainer = doc.querySelector('[data-testid="stBottomBlockContainer"]');
                    var faq = doc.querySelector('.st-key-faq_area');
                    if (!bottomContainer || !faq) return;
                    if (typeof ResizeObserver === 'undefined') return;

                    function updateFaqBottom() {
                        try {
                            var h = bottomContainer.getBoundingClientRect().height;
                            faq.style.bottom = (h + 8) + 'px';
                            /* 콘텐츠가 FAQ+입력창에 가리지 않도록 body padding-bottom도 갱신 */
                            var faqH = faq.getBoundingClientRect().height;
                            var blockContainer = doc.querySelector('.block-container');
                            if (blockContainer) {
                                blockContainer.style.paddingBottom = (h + faqH + 24) + 'px';
                            }
                        } catch (e) {}
                    }

                    var observer = new ResizeObserver(updateFaqBottom);
                    observer.observe(bottomContainer);
                    updateFaqBottom(); /* 최초 1회 즉시 적용 */
                } catch (e) {}
            }

            /* DOM이 준비된 뒤 observer를 붙인다 */
            [100, 400, 900].forEach(function (d) { setTimeout(attachFaqObserver, d); });
        })();
        </script>
        """,
        height=0,
    )
