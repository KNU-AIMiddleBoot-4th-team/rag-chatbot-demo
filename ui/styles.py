"""페이지 전역 CSS. 화면 상태(시작 화면 / 대화 화면)에 따라 레이아웃만 달라진다."""

import streamlit as st


def inject_base_styles() -> None:
    """색상, 헤더, 입력창, FAQ 버튼 등 상태와 무관한 기본 스타일."""
    st.markdown(
        """
        <style>
        :root, .stApp { color-scheme: light only !important; }
        .stApp { background-color: #ffffff; }
        [data-testid="stHeader"] { background-color: transparent !important; }
        [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container { background-color: #ffffff !important; }
        .st-key-logo_header { position: fixed !important; top: 15px !important; left: 20px !important; z-index: 999999 !important; width: 340px; }
        .st-key-logo_header [data-testid="column"]:nth-child(2) { margin-left: -35px !important; }
        .st-key-logo_header [data-testid="stImage"] img { width: 45px !important; height: 45px !important; border-radius: 12px; object-fit: cover; }
        .st-key-logo_header span { font-size: 1.35rem; font-weight: 800; color: #0184ff; letter-spacing: -0.3px; white-space: nowrap; display: inline-block; margin-top: 5px; }
        .block-container { padding-top: 5.5rem; padding-bottom: 240px; }
        .chat-welcome { text-align: center; margin-top: 1rem; margin-bottom: 2.5rem; }
        .chat-welcome h1 { font-size: 2.1rem; font-weight: 700; color: #191F28; margin-bottom: 0.5rem; line-height: 1.35; }
        .chat-welcome p { font-size: 1.05rem; color: #4E5968; }
        .chat-welcome .brand-dot { color: #0184ff; }
        [data-testid="stBottomBlockContainer"] { pointer-events: none !important; z-index: 99990 !important; }
        [data-testid="stBottomBlockContainer"] * { pointer-events: auto; }
        .st-key-attach_area { width: 45px !important; height: 45px !important; z-index: 99995 !important; pointer-events: none !important; }
        .st-key-attach_area > div, .st-key-attach_area button { pointer-events: auto !important; }
        .st-key-attach_area button { width: 40px !important; height: 40px !important; background-color: transparent !important; border: none !important; color: #0184ff !important; font-size: 1.15rem !important; padding: 0 !important; margin-top: 2px !important; box-shadow: none !important; transition: all 0.15s ease; display: flex !important; justify-content: center !important; align-items: center !important; }
        .st-key-attach_area button:hover { color: #3434e0 !important; }
        .st-key-attach_area button svg, .st-key-attach_area button [data-testid="stIconMaterial"] { display: none !important; width: 0 !important; height: 0 !important; visibility: hidden !important; }
        [data-testid="stChatInput"] { background-color: #ffffff !important; border: 1.5px solid #0184ff !important; border-radius: 24px !important; box-shadow: 0 8px 24px rgba(1, 132, 255, 0.18) !important; overflow: visible !important; padding: 6px 18px !important; z-index: 99992 !important; pointer-events: auto !important; transition: all 0.2s ease !important; }
        [data-testid="stChatInput"]:focus-within { border-color: #3434e0 !important; box-shadow: 0 8px 32px rgba(52, 52, 224, 0.3) !important; }
        [data-testid="stChatInput"] > div, [data-testid="stChatInput"] > div > div { background-color: transparent !important; border: none !important; box-shadow: none !important; border-radius: 0 !important; overflow: visible !important; }
        [data-testid="stChatInput"] textarea { background-color: transparent !important; color: #191F28 !important; caret-color: #3434e0 !important; font-size: 1rem !important; padding-left: 55px !important; }
        [data-testid="stChatInputSubmitButton"] { background-color: transparent !important; border: none !important; box-shadow: none !important; }
        [data-testid="stChatInputSubmitButton"]:not(:disabled), [data-testid="stChatInputSubmitButton"]:not(:disabled) svg { color: #3434e0 !important; fill: #3434e0 !important; }
        [data-testid="stChatInputSubmitButton"]:not(:disabled):hover { background-color: rgba(52, 52, 224, 0.08) !important; opacity: 0.9 !important; }
        [data-testid="stChatInputSubmitButton"]:disabled, [data-testid="stChatInputSubmitButton"]:disabled svg, [data-testid="stChatInputSubmitButton"][aria-disabled="true"], [data-testid="stChatInputSubmitButton"][aria-disabled="true"] svg { color: #c0c4cc !important; fill: #c0c4cc !important; }
        .st-key-faq_area button { background-color: #ffffff !important; border: 1px solid #E5E8EB !important; color: #0184ff !important; border-radius: 12px !important; padding: 16px 20px !important; font-size: 0.85rem !important; font-weight: 600 !important; text-align: left !important; width: 100% !important; box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important; transition: all 0.15s ease !important; white-space: normal !important; height: auto !important; line-height: 1.4 !important; }
        .st-key-faq_area button:hover { border-color: #0184ff !important; color: #3434e0 !important; background-color: rgba(1, 132, 255, 0.03) !important; box-shadow: 0 4px 12px rgba(1, 132, 255, 0.1) !important; }
        .bottom-backdrop { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _empty_state_layout() -> str:
    """대화 시작 전: 입력창과 FAQ를 화면 중앙에 띄우는 레이아웃."""
    return """
        <style>
        [data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 45% !important;
            top: auto !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: min(800px, calc(100% - 40px)) !important;
            margin-left: 0 !important;
        }
        .st-key-attach_area {
            position: fixed !important;
            bottom: calc(45% + 8px) !important;
            top: auto !important;
            left: 50% !important;
            transform: none !important;
        }
        @media (min-width: 840px) { .st-key-attach_area { margin-left: -375px !important; } }
        @media (max-width: 839px) { .st-key-attach_area { margin-left: calc(-50vw + 40px) !important; } }
        .faq-fixed-label {
            position: fixed;
            bottom: calc(45% - 45px);
            top: auto;
            left: 50%;
            transform: translateX(-50%);
            width: min(800px, calc(100% - 40px));
            font-weight: 700;
            color: #3434e0;
            font-size: 0.85rem;
            z-index: 997;
        }
        .st-key-faq_area {
            position: fixed;
            bottom: calc(45% - 145px);
            top: auto;
            left: 50%;
            transform: translateX(-50%);
            width: min(800px, calc(100% - 40px));
            z-index: 997;
        }
        </style>
        """


def _chat_state_layout() -> str:
    """대화 중: 입력창을 하단에 고정하고 대화 내용이 위로 쌓이게 하는 레이아웃."""
    return """
        <style>
        [data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 120px !important;
            top: auto !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: min(800px, calc(100% - 40px)) !important;
            margin-left: 0 !important;
        }
        .st-key-attach_area {
            position: fixed !important;
            bottom: 128px !important;
            top: auto !important;
            left: 50% !important;
            transform: none !important;
        }
        @media (min-width: 840px) { .st-key-attach_area { margin-left: -375px !important; } }
        @media (max-width: 839px) { .st-key-attach_area { margin-left: calc(-50vw + 40px) !important; } }
        .faq-fixed-label {
            position: fixed;
            bottom: 90px;
            top: auto;
            left: 50%;
            transform: translateX(-50%);
            width: min(800px, calc(100% - 40px));
            font-weight: 700;
            color: #3434e0;
            font-size: 0.85rem;
            z-index: 997;
        }
        .st-key-faq_area {
            position: fixed;
            bottom: 10px;
            top: auto;
            left: 50%;
            transform: translateX(-50%);
            width: min(800px, calc(100% - 40px));
            z-index: 997;
        }
        .bottom-backdrop {
            display: block !important;
            position: fixed !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            height: 220px !important;
            background: linear-gradient(to top, #ffffff 82%, rgba(255, 255, 255, 0) 100%) !important;
            z-index: 900 !important;
            pointer-events: none !important;
        }
        </style>
        """


def inject_layout_styles(has_messages: bool) -> None:
    """대화 유무에 따라 입력창/FAQ 위치를 바꾸는 레이아웃 스타일을 주입한다."""
    st.markdown(
        _chat_state_layout() if has_messages else _empty_state_layout(),
        unsafe_allow_html=True,
    )
