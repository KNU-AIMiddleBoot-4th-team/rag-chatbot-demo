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

        /* stBottomBlockContainer를 화면 전체 폭으로 확장한다. */
        [data-testid="stBottomBlockContainer"] {
            pointer-events: none !important;
            z-index: 99990 !important;
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            transform: none !important;
        }
        [data-testid="stBottomBlockContainer"] * { pointer-events: auto; }

        /* ============================================================
           입력창(stChatInput) 레이아웃 - 근본 재설계
           ------------------------------------------------------------
           문제였던 것: Streamlit이 내부적으로 만드는 div 깊이마다
           랜덤 클래스(st-emotion-cache-xxxxx)가 붙고, 각 flex 자식은
           기본적으로 min-width:auto 라서 텍스트 내용 크기 이하로는
           줄어들지 않는다. 특정 깊이 하나만 고치면 다른 깊이에서
           또 막히는 문제가 반복됐다.

           해결: 깊이를 특정하지 않고 stChatInput 내부의 "모든" div에
           min-width:0 을 무조건 건다. 어느 버전에서 구조가 바뀌어도
           이 규칙은 깨지지 않는다.
        ============================================================ */
        [data-testid="stChatInput"],
        [data-testid="stChatInput"] * {
            box-sizing: border-box !important;
        }
        [data-testid="stChatInput"] div {
            min-width: 0 !important;
        }

        /* 입력창 바깥 껍데기: 최대 800px, 중앙 정렬, 카드 스타일 */
        [data-testid="stChatInput"] {
            width: min(800px, calc(100% - 40px)) !important;
            margin-left: auto !important;
            margin-right: auto !important;
            background-color: #ffffff !important;
            border: 1.5px solid #0184ff !important;
            border-radius: 24px !important;
            box-shadow: 0 8px 24px rgba(1, 132, 255, 0.18) !important;
            overflow: visible !important;
            padding: 6px 18px !important;
            z-index: 99992 !important;
            pointer-events: auto !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: #3434e0 !important;
            box-shadow: 0 8px 32px rgba(52, 52, 224, 0.3) !important;
        }

        /* 입력창 내부 첫 번째 행: textarea + 전송버튼을 한 줄(row)로.
           전송 버튼은 이제 position:fixed + JS 실측 좌표 방식으로
           동작하므로(render_focus_script), 이 div에 position:relative를
           걸어 기준점으로 삼을 필요가 없다. 순수하게 레이아웃(flex)
           역할만 한다. */
        [data-testid="stChatInput"] > div {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            width: 100% !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            overflow: visible !important;
        }
        /* 그 안의 모든 중첩 div: 텍스트 영역을 감싸는 wrapper는 남는 폭을
           다 채우고(flex:1), 그 외에는 내용 크기만큼만(shrink 방지 X). */
        [data-testid="stChatInput"] > div > div {
            display: flex !important;
            flex: 1 1 auto !important;
            width: 100% !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            overflow: visible !important;
        }

        /* textarea 자체: 부모 폭을 정확히 채움 (padding 포함해서 계산)
           - padding-left: 45px -> 23px (➕ 버튼과 텍스트 사이 여백을 절반으로 축소)
           - padding-right: 44px -> 23px (좌우 똑같이, 텍스트 입력 가능 폭 총합은 그대로 유지)
           - width: 100% -> calc(100% - 50px) : 전송 버튼은 position:fixed로
             textarea 흐름과 무관하게 떠 있는데, textarea가 폭 100%를 꽉 채우면
             스크롤바(오른쪽 테두리에 붙어서 그려짐)가 버튼과 정확히 겹친다.
             textarea 자체의 오른쪽 끝(=스크롤바 위치)을 50px 왼쪽으로 당겨서
             버튼 영역을 피하도록 폭을 줄인다.
           - scrollbar-gutter: stable -> 스크롤바가 생기든 안 생기든 그 자리를
             항상 미리 예약해둬서, 스크롤바 등장 시점에 레이아웃이 흔들리는
             현상을 방지한다. */
        [data-testid="stChatInput"] textarea {
            width: calc(100% - 15px) !important;
            background-color: transparent !important;
            color: #191F28 !important;
            caret-color: #3434e0 !important;
            font-size: 1rem !important;
            padding-top: 8px !important;
            padding-left: 23px !important;
            padding-right: 23px !important;
            max-height: 120px !important;
            overflow-y: auto !important;
            scrollbar-gutter: stable !important;
            resize: none !important;
            white-space: pre-wrap !important;
            word-break: break-word !important;
        }
        /* 스크롤바를 얇고 은은하게: 예약된 공간 안에서도 시각적으로
           거슬리지 않도록 (webkit 계열 브라우저 전용) */
        [data-testid="stChatInput"] textarea::-webkit-scrollbar {
            width: 5px !important;
        }
        [data-testid="stChatInput"] textarea::-webkit-scrollbar-track {
            background: transparent !important;
        }
        [data-testid="stChatInput"] textarea::-webkit-scrollbar-thumb {
            background-color: rgba(1, 132, 255, 0.25) !important;
            border-radius: 4px !important;
        }

        /* 전송 버튼: CSS 캐스케이드(부모 position:relative 찾기, 라이브러리가
           몰래 건 position 등)와 계속 충돌해서, ➕ 버튼과 동일한 방식으로
           전환한다. position:fixed 로 완전히 flow/부모 컨텍스트에서 빼내고,
           실제 좌표(top/left)는 render_focus_script()의 JS가
           stChatInput의 실측 좌표를 읽어 ➕ 버튼과 대칭으로 매 프레임 계산해
           넣는다. 여기서는 크기·모양만 정의한다 (➕ 버튼과 동일한 40x40). */
        [data-testid="stChatInputSubmitButton"] {
            position: fixed !important;
            width: 40px !important;
            height: 40px !important;
            z-index: 99996 !important;
            margin: 0 !important;
            flex: none !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        [data-testid="stChatInputSubmitButton"]:not(:disabled),
        [data-testid="stChatInputSubmitButton"]:not(:disabled) svg { color: #3434e0 !important; fill: #3434e0 !important; }
        [data-testid="stChatInputSubmitButton"]:not(:disabled):hover { background-color: rgba(52, 52, 224, 0.08) !important; opacity: 0.9 !important; }
        [data-testid="stChatInputSubmitButton"]:disabled,
        [data-testid="stChatInputSubmitButton"]:disabled svg,
        [data-testid="stChatInputSubmitButton"][aria-disabled="true"],
        [data-testid="stChatInputSubmitButton"][aria-disabled="true"] svg { color: #c0c4cc !important; fill: #c0c4cc !important; }

        /* ============================================================
           ➕ 첨부 버튼
           ------------------------------------------------------------
           left/bottom을 고정 px로 계산하던 예전 방식은 textarea가
           줄바꿈으로 커질 때마다 어긋났다. 이제 위치 자체는
           render_focus_script()의 JS가 입력창의 실제 렌더 좌표를
           측정해서 매 프레임 갱신한다. 여기서는 크기·모양만 정의한다.
        ============================================================ */
        .st-key-attach_area {
            position: fixed !important;
            width: 45px !important;
            height: 45px !important;
            z-index: 99995 !important;
            pointer-events: none !important;
        }
        .st-key-attach_area > div, .st-key-attach_area button { pointer-events: auto !important; }
        .st-key-attach_area button {
            width: 40px !important; height: 40px !important;
            background-color: transparent !important; border: none !important;
            color: #0184ff !important; font-size: 1.15rem !important; padding: 0 !important;
            box-shadow: none !important; transition: all 0.15s ease;
            display: flex !important; justify-content: center !important; align-items: center !important;
        }
        .st-key-attach_area button:hover { color: #3434e0 !important; }
        .st-key-attach_area button svg, .st-key-attach_area button [data-testid="stIconMaterial"] { display: none !important; width: 0 !important; height: 0 !important; visibility: hidden !important; }

        /* 3개 카드 높이 통일 */
        .st-key-faq_area button { background-color: #ffffff !important; border: 1px solid #E5E8EB !important; color: #0184ff !important; border-radius: 12px !important; padding: 14px 20px !important; font-size: 0.85rem !important; font-weight: 600 !important; text-align: left !important; width: 100% !important; box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important; transition: all 0.15s ease !important; white-space: normal !important; height: 96px !important; line-height: 1.4 !important; display: flex !important; align-items: center !important; justify-content: flex-start !important; }
        .st-key-faq_area button:hover { border-color: #0184ff !important; color: #3434e0 !important; background-color: rgba(1, 132, 255, 0.03) !important; box-shadow: 0 4px 12px rgba(1, 132, 255, 0.1) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _empty_state_layout() -> str:
    """대화 시작 전: stBottomBlockContainer 전체를 화면 중앙에 배치."""
    return """
        <style>
        [data-testid="stBottomBlockContainer"] {
            bottom: 40% !important;
        }
        /* FAQ 폭/정렬/z-index만 지정. bottom/attach 위치는 JS가 계산. */
        .st-key-faq_area {
            position: fixed !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: min(800px, calc(100% - 40px)) !important;
            z-index: 997 !important;
            background: #ffffff !important;
            padding: 0 8px 12px 8px !important;
        }
        </style>
        """


def _chat_state_layout() -> str:
    """대화 중: 입력창은 Streamlit 기본 하단 고정, FAQ/attach는 JS가 위치를 맞춘다."""
    return """
        <style>
        .block-container { padding-bottom: 220px !important; }
        .st-key-faq_area {
            position: fixed !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: min(800px, calc(100% - 40px)) !important;
            z-index: 997 !important;
            background: #ffffff !important;
            padding: 0 8px 12px 8px !important;
        }
        </style>
        """


def inject_layout_styles(has_messages: bool) -> None:
    """대화 유무에 따라 입력창/FAQ 위치를 바꾸는 레이아웃 스타일을 주입한다."""
    st.markdown(
        _chat_state_layout() if has_messages else _empty_state_layout(),
        unsafe_allow_html=True,
    )