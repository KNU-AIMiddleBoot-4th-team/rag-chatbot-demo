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
    """페이지 로드 시 입력창 포커스 + FAQ/attach/전송버튼 위치를 입력창 실측 좌표에 맞게 동적 보정.

    기존 방식(고정 px, bottom: 70px 등)은 textarea가 줄바꿈으로 커질 때마다
    attach 버튼 위치가 어긋나는 원인이었다. 이제 stChatInput 자체의
    실제 렌더링 좌표(getBoundingClientRect)를 매번 측정해서
    attach 버튼, 전송 버튼, FAQ 영역을 그 좌표에 맞춰 절대 위치로 배치한다.
    입력창이 몇 줄이 되든, 화면 폭이 얼마든 항상 정확히 따라간다.

    전송 버튼(stChatInputSubmitButton)은 CSS position:relative 부모를
    찾는 방식이 라이브러리 내부 wrapper의 숨은 position 속성과 계속
    충돌해서, ➕ 버튼과 완전히 동일한 방식(JS 실측 좌표 + position:fixed)
    으로 전환했다. ➕ 버튼과 좌우 대칭이 되도록 같은 inset(14px)과
    같은 수직 중앙 정렬 공식을 사용한다.
    """
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

            /* ── 입력창 실측 좌표 기반으로 attach 버튼 + 전송 버튼 + FAQ 위치를 갱신 ──
               DOM을 이동시키지 않고 좌표(top/left/bottom)만 읽어서
               다른 고정 요소들의 style.left/top/bottom을 계산해 넣는다.
               셀렉터가 깨지거나 요소가 없으면 조용히 종료한다(앱 안 죽음). */
            function updatePositions() {
                try {
                    var chatInput = doc.querySelector('[data-testid="stChatInput"]');
                    var attach = doc.querySelector('.st-key-attach_area');
                    var submit = doc.querySelector('[data-testid="stChatInputSubmitButton"]');
                    var faq = doc.querySelector('.st-key-faq_area');
                    var bottomContainer = doc.querySelector('[data-testid="stBottomBlockContainer"]');
                    if (!chatInput) return;

                    var rect = chatInput.getBoundingClientRect();
                    var INSET = 14;     /* ➕ 버튼과 전송 버튼, 좌우 동일한 안쪽 여백 */
                    var BTN = 40;       /* 두 버튼 모두 40x40으로 통일, 수직 중앙 계산에 사용 */

                    /* ➕ 버튼: 입력창 왼쪽 안쪽, 세로 중앙에 맞춤 */
                    if (attach) {
                        attach.style.left = (rect.left + INSET) + 'px';
                        attach.style.top = (rect.top + rect.height / 2 - BTN / 2) + 'px';
                        attach.style.bottom = 'auto';
                    }

                    /* 전송 버튼: ➕ 버튼과 완전히 대칭 (같은 INSET, 같은 수직 중앙 공식).
                       setProperty(..., 'important') 로 넣어야 CSS !important 규칙과
                       충돌 없이 항상 JS 계산값이 최종 적용된다. */
                    if (submit) {
                        var submitLeft = rect.right - INSET - BTN;
                        var submitTop = rect.top + rect.height / 2 - BTN / 2;
                        submit.style.setProperty('left', submitLeft + 'px', 'important');
                        submit.style.setProperty('top', submitTop + 'px', 'important');
                        submit.style.setProperty('right', 'auto', 'important');
                        submit.style.setProperty('bottom', 'auto', 'important');
                    }

                    /* FAQ: 입력창 바로 위, 컨테이너 전체 높이 기준으로 배치 */
                    if (faq && bottomContainer) {
                        var containerH = bottomContainer.getBoundingClientRect().height;
                        faq.style.bottom = (containerH + 8) + 'px';

                        var faqH = faq.getBoundingClientRect().height;
                        var blockContainer = doc.querySelector('.block-container');
                        if (blockContainer) {
                            blockContainer.style.paddingBottom = (containerH + faqH + 24) + 'px';
                        }
                    }
                } catch (e) {}
            }

            function attachObservers() {
                try {
                    var chatInput = doc.querySelector('[data-testid="stChatInput"]');
                    var bottomContainer = doc.querySelector('[data-testid="stBottomBlockContainer"]');
                    if (!chatInput || typeof ResizeObserver === 'undefined') return;

                    var observer = new ResizeObserver(updatePositions);
                    observer.observe(chatInput);
                    if (bottomContainer) observer.observe(bottomContainer);

                    /* 창 크기 변경(반응형)에도 반응 */
                    window.parent.addEventListener('resize', updatePositions);

                    updatePositions(); /* 최초 1회 즉시 적용 */
                } catch (e) {}
            }

            /* DOM이 준비된 뒤 observer를 붙인다 */
            [100, 400, 900].forEach(function (d) { setTimeout(attachObservers, d); });
        })();
        </script>
        """,
        height=0,
    )