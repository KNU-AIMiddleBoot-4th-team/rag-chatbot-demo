"""
법률/노무 AI 챗봇 — RAG 기반 상담 서비스
=========================================
브랜드 컬러 (이 3색만 사용):
  - 강조:        #3434e0
  - 아이덴티티:  #0184ff
  - 배경/흰색:   #ffffff

실행 전 준비:
  pip install streamlit openai numpy pandas
  .streamlit/secrets.toml 에 아래 추가:
      OPENAI_API_KEY = "sk-..."
  실행: streamlit run app.py
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
from openai import OpenAI

# ─────────────────────────────────────────────
# 1. 페이지 설정 + 커스텀 CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title="법률/노무 AI 챗봇", page_icon="⚖️", layout="centered")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "queued_question" not in st.session_state:
    st.session_state.queued_question = None

# 공통/전역 CSS
st.markdown(
    """
    <style>
    /* ===== 전역: 흰색 배경 ===== */
    .stApp {
        background-color: #ffffff;
    }

    /* ===== 로고 유지 (최상단, 여백 축소) ===== */
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    .st-key-logo_header {
        position: fixed !important;
        top: 15px !important;
        left: 20px !important;
        z-index: 999999 !important; 
        width: 340px;
    }
    .st-key-logo_header [data-testid="column"]:nth-child(2) {
        margin-left: -35px !important;
    }
    .st-key-logo_header [data-testid="stImage"] img {
        width: 45px !important;
        height: 45px !important;
        border-radius: 12px;
        object-fit: cover;
    }
    .st-key-logo_header span {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0184ff;
        letter-spacing: -0.3px;
        white-space: nowrap;
        display: inline-block;
        margin-top: 5px;
    }

    .block-container {
        padding-top: 5.5rem;
        padding-bottom: 240px;
    }

    /* ===== 상단 웰컴 타이틀 ===== */
    .chat-welcome {
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 2.5rem;
    }
    .chat-welcome h1 {
        font-size: 2.1rem;
        font-weight: 700;
        color: #191F28;
        margin-bottom: 0.5rem;
        line-height: 1.35;
    }
    .chat-welcome p {
        font-size: 1.05rem;
        color: #4E5968;
    }
    .chat-welcome .brand-dot { color: #0184ff; }

    /* =========================================================================
       채팅창 컨테이너 & ➕ 버튼 관련 스타일
       ========================================================================= */
    [data-testid="stBottomBlockContainer"] {
        pointer-events: none !important;
        z-index: 99990 !important;
    }
    [data-testid="stBottomBlockContainer"] * {
        pointer-events: auto;
    }

    .st-key-attach_area {
        width: 45px !important; 
        height: 45px !important;
        z-index: 99995 !important;
        pointer-events: none !important; 
    }
    .st-key-attach_area > div,
    .st-key-attach_area button {
        pointer-events: auto !important;
    }
    
    .st-key-attach_area button {
        width: 40px !important;
        height: 40px !important;
        background-color: transparent !important;
        border: none !important;
        color: #0184ff !important;
        font-size: 1.15rem;
        padding: 0 !important;
        margin-top: 2px !important;
        box-shadow: none !important;
        transition: all 0.15s ease;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    .st-key-attach_area button:hover {
        color: #3434e0 !important;
    }
    
    /* ➕ 버튼 옆 아래 화살표 완벽 제거 */
    .st-key-attach_area button svg,
    .st-key-attach_area button [data-testid="stIconMaterial"] {
        display: none !important; 
        width: 0 !important; 
        height: 0 !important;
        visibility: hidden !important;
    }

    /* =========================================================================
       채팅창 디자인 & 입력 버튼(전송 버튼) 색상 제어
       ========================================================================= */
    [data-testid="stChatInput"] {
        background-color: #ffffff !important;
        border: 1.5px solid #0184ff !important;
        border-radius: 24px !important;
        box-shadow: 0 8px 24px rgba(1, 132, 255, 0.18) !important;
        overflow: visible !important; 
        
        /* 전송 버튼 안쪽 밀기 (상하 6px, 좌우 18px) */
        padding: 6px 18px !important; 
        
        z-index: 99992 !important;
        pointer-events: auto !important; 
        transition: all 0.2s ease !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #3434e0 !important;
        box-shadow: 0 8px 32px rgba(52, 52, 224, 0.3) !important;
    }

    [data-testid="stChatInput"] > div, 
    [data-testid="stChatInput"] > div > div {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        overflow: visible !important;
    }
    
    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #191F28 !important;
        caret-color: #3434e0 !important;
        font-size: 1rem !important;
        
        /* ➕ 버튼 여백 확보 */
        padding-left: 55px !important; 
    }

    /* [수정됨] 전송 버튼이 빨갛게 변하는 원인 및 수정 방법
       ─────────────────────────────────────────────────────────
       Streamlit은 글자가 입력되면 전송 버튼을 kind="primary" 버튼으로 취급해서
       테마의 primaryColor(기본값이 빨간 계열 #FF4B4B)를 "배경색"으로 칠합니다.
       기존 코드는 color/fill(글자·아이콘 색)만 덮어썼을 뿐 background-color는
       그대로 둬서 빨간 배경이 남아있었던 것입니다. 아래처럼 background-color와
       border까지 함께 !important로 덮어써야 완전히 사라집니다.
       ※ 요청하신 "#343e0"은 6자리가 아니라 자동 보정이 필요한 값이라
         브랜드 강조색인 #3434e0(맨 위 주석의 '강조' 컬러)으로 적용했습니다.
         다른 값을 원하시면 아래 3곳의 #3434e0 를 원하는 6자리 hex로 바꾸면 됩니다. */

    /* 버튼 자체의 배경/테두리를 항상 투명하게 (primary 배경색이 못 끼어들게 차단) */
    [data-testid="stChatInputSubmitButton"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 활성화(글자 입력됨) 상태 → 브랜드 강조색
       [주의] svg path 레벨까지 색을 칠하면, 화살표 아이콘 뒤에 깔린 배경 사각형(surface)
       path까지 같은 색으로 칠해져서 화살표가 배경에 파묻혀 "네모"로 보이는 문제가
       생깁니다. 그래서 svg 루트 레벨에만 색을 지정합니다 (path는 건드리지 않음). */
    [data-testid="stChatInputSubmitButton"]:not(:disabled),
    [data-testid="stChatInputSubmitButton"]:not(:disabled) svg {
        color: #3434e0 !important; 
        fill: #3434e0 !important;
    }
    [data-testid="stChatInputSubmitButton"]:not(:disabled):hover {
        background-color: rgba(52, 52, 224, 0.08) !important; /* 옅은 강조색 호버 */
        opacity: 0.9 !important;
    }

    /* 비활성화(빈칸) 상태일 때의 회색 처리
       일부 스트림릿 버전은 disabled 대신 aria-disabled="true" 속성을 쓰기 때문에
       그 경우까지 같이 잡아줘야 안전합니다. */
    [data-testid="stChatInputSubmitButton"]:disabled,
    [data-testid="stChatInputSubmitButton"]:disabled svg,
    [data-testid="stChatInputSubmitButton"][aria-disabled="true"],
    [data-testid="stChatInputSubmitButton"][aria-disabled="true"] svg {
        color: #c0c4cc !important; 
        fill: #c0c4cc !important;
    }

    /* FAQ 버튼 공통 스타일 */
    .st-key-faq_area button {
        background-color: #ffffff !important;
        border: 1px solid #E5E8EB !important;
        color: #0184ff !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        font-size: 0.85rem;
        font-weight: 600;
        text-align: left;
        width: 100% !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
        transition: all 0.15s ease;
        white-space: normal !important;
        height: auto !important;
        line-height: 1.4;
    }
    .st-key-faq_area button:hover {
        border-color: #0184ff !important;
        color: #3434e0 !important;
        background-color: rgba(1, 132, 255, 0.03) !important;
        box-shadow: 0 4px 12px rgba(1, 132, 255, 0.1) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# [핵심] 레이아웃 간격 및 위치 조정 (겹침 완벽 해결)
# ─────────────────────────────────────────────
if not st.session_state.messages:
    # --- 초기 화면 ---
    # 채팅창과 FAQ의 기준점을 화면 중앙(top: 50%)이 아닌 '바닥(bottom)'으로 고정했습니다.
    # 이렇게 하면 글을 여러 줄 입력할 때 위로만 늘어나게 되어 FAQ를 침범하지 않습니다.
    st.markdown(
        """
        <style>
        [data-testid="stChatInput"] {
            position: fixed !important;
            
            /* [위치 조정] 바닥을 기준으로 높이 설정 (초기화면 대략 화면 중간 높이) */
            bottom: 45% !important; 
            
            top: auto !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: min(800px, calc(100% - 40px)) !important;
            margin-left: 0 !important;
        }
        
        .st-key-attach_area {
            position: fixed !important;
            
            /* 채팅창 바닥(45%)에서 살짝 위로 올려 높이를 맞춤 */
            bottom: calc(45% + 8px) !important; 
            
            top: auto !important;
            left: 50% !important;
            transform: none !important;
        }
        
        /* ➕ 버튼 좌우 위치 (안쪽으로 밀기) */
        @media (min-width: 840px) { .st-key-attach_area { margin-left: -375px !important; } }
        @media (max-width: 839px) { .st-key-attach_area { margin-left: calc(-50vw + 40px) !important; } }

        .faq-fixed-label {
            position: fixed;
            
            /* [위치 조정] 💡자주 묻는 질문 텍스트 위치: 채팅창(45%)보다 45px 아래로 배치 */
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
            
            /* [수정됨] 💡버튼 블록 위치: 채팅창(45%)보다 145px 아래로 배치
               라벨(45% - 45px)과 버튼(45% - 145px)의 차이 = 100px 간격
               (기존 115px → 145px로 30px 늘려서, 기존 70px 간격을 100px로 넓혔습니다)
               간격을 더/덜 벌리고 싶으면 이 145px 숫자만 조절하면 됩니다.
               (라벨 쪽 45px 값은 그대로 두고 이 값만 바꾸면 라벨-버튼 간격만 바뀝니다) */
            bottom: calc(45% - 145px); 
            
            top: auto;
            left: 50%;
            transform: translateX(-50%);
            width: min(800px, calc(100% - 40px));
            z-index: 997;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    # --- 대화 진행 중 화면 ---
    st.markdown(
        """
        <style>
        [data-testid="stChatInput"] {
            position: fixed !important;
            
            /* 대화 중 채팅창 바닥 높이 (고정되어 위로만 늘어남) */
            bottom: 120px !important; 
            
            top: auto !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: min(800px, calc(100% - 40px)) !important;
            margin-left: 0 !important;
        }
        
        .st-key-attach_area {
            position: fixed !important;
            
            /* 대화 중 ➕ 버튼 높이 (채팅창 바닥 120px + 8px) */
            bottom: 128px !important; 
            
            top: auto !important;
            left: 50% !important;
            transform: none !important;
        }
        
        /* ➕ 버튼 좌우 위치 (초기화면과 동일) */
        @media (min-width: 840px) { .st-key-attach_area { margin-left: -375px !important; } }
        @media (max-width: 839px) { .st-key-attach_area { margin-left: calc(-50vw + 40px) !important; } }

        .faq-fixed-label {
            position: fixed;
            
            /* [수정됨] 대화 중 FAQ 라벨 높이: 70px → 90px (살짝 위로 올림) */
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
            
            /* [수정됨] 대화 중 FAQ 버튼 높이: 15px → 10px (살짝 아래로 내림)
               라벨(90px)과 버튼(10px)의 차이 = 80px 간격
               (기존 라벨70px/버튼15px → 간격 55px에서 80px로 넓혔습니다)
               채팅창(120px)과 라벨(90px) 사이 여백도 30px 남아있어 안전합니다.
               간격을 더 벌리고 싶으면 라벨의 90px을 더 키우거나 버튼의 10px을 더 줄이면 됩니다. */
            bottom: 10px; 
            
            top: auto;
            left: 50%;
            transform: translateX(-50%);
            width: min(800px, calc(100% - 40px));
            z-index: 997;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# 2. OpenAI 클라이언트
# ─────────────────────────────────────────────
@st.cache_resource
def get_client() -> OpenAI:
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# ─────────────────────────────────────────────
# 3. RAG — 법률 데이터 로드
# ─────────────────────────────────────────────
@st.cache_data
def load_law_documents() -> list[dict]:
    try:
        df = pd.read_csv("data/law_data.csv")
        return df[["source", "content"]].to_dict("records")
    except Exception:
        return [
            {"source": "근로기준법 제17조(근로조건의 명시)",
             "content": "사용자는 근로계약을 체결할 때에 근로자에게 임금(구성항목·계산방법·지급방법), 소정근로시간, 휴일, 연차 유급휴가 등을 명시해야 하며, 서면(전자문서 포함) 교부해야 한다."},
            {"source": "근로기준법 제23조(해고 등의 제한)",
             "content": "사용자는 근로자에게 정당한 이유 없이 해고, 휴직, 정직, 전직, 감봉, 그 밖의 징벌을 하지 못한다."},
            {"source": "근로기준법 제26조(해고의 예고)",
             "content": "사용자는 근로자를 해고하려면 적어도 30일 전에 예고를 하여야 하고, 30일 전에 예고를 하지 아니하였을 때에는 30일분 이상의 통상임금을 지급하여야 한다."},
            {"source": "근로기준법 제56조(연장·야간 및 휴일 근로)",
             "content": "사용자는 연장근로에 대하여 통상임금의 100분의 50 이상을 가산하여 근로자에게 지급하여야 한다. 야간근로(오후 10시부터 다음 날 오전 6시)에 대해서도 동일하게 가산한다."},
            {"source": "근로자퇴직급여 보장법 제4조(퇴직급여제도의 설정)",
             "content": "사용자는 퇴직하는 근로자에게 급여를 지급하기 위하여 퇴직급여제도 중 하나 이상의 제도를 설정하여야 한다. 계속근로기간이 1년 미만인 근로자는 제외한다."},
            {"source": "노동위원회법·근로기준법 제28조(부당해고 구제신청)",
             "content": "사용자가 근로자에게 부당해고 등을 하면 근로자는 노동위원회에 구제를 신청할 수 있다. 구제신청은 부당해고 등이 있었던 날부터 3개월 이내에 하여야 한다."},
        ]


# ─────────────────────────────────────────────
# 4. RAG — 임베딩 기반 검색
# ─────────────────────────────────────────────
@st.cache_data
def embed_documents(texts: tuple[str, ...]) -> np.ndarray:
    client = get_client()
    res = client.embeddings.create(model="text-embedding-3-small", input=list(texts))
    return np.array([d.embedding for d in res.data])


def retrieve(query: str, docs: list[dict], top_k: int = 3) -> list[dict]:
    try:
        doc_vecs = embed_documents(tuple(d["content"] for d in docs))
        q_res = get_client().embeddings.create(
            model="text-embedding-3-small", input=[query]
        )
        q_vec = np.array(q_res.data[0].embedding)
        sims = doc_vecs @ q_vec / (
            np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(q_vec) + 1e-9
        )
        idx = np.argsort(sims)[::-1][:top_k]
        return [docs[i] for i in idx if sims[i] > 0.2]
    except Exception:
        return [d for d in docs if any(w in d["content"] or w in d["source"]
                                       for w in query.split())][:top_k]


def generate_answer(query: str, contexts: list[dict]):
    context_text = "\n\n".join(
        f"[{c['source']}]\n{c['content']}" for c in contexts
    ) or "관련 법령이 DB에서 검색되지 않았습니다. 일반적인 법률 지식으로 답변하되, 그 사실을 명시하세요."

    system_prompt = (
        "당신은 대한민국 법률 및 인사노무 전문 AI 챗봇입니다.\n"
        "반드시 아래 [참고 법령 데이터]를 근거로 답변하고, 인용한 조문의 출처를 밝히세요.\n"
        "데이터에 없는 내용은 추측하지 말고 '전문가 상담이 필요하다'고 안내하세요.\n"
        "답변 마지막에는 '※ 본 답변은 참고용이며 법적 효력이 없습니다.'를 붙이세요.\n\n"
        f"[참고 법령 데이터]\n{context_text}"
    )
    stream = get_client().chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        stream=True,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


# ─────────────────────────────────────────────
# 5. UI 렌더링
# ─────────────────────────────────────────────

# 5-1. 헤더: 로고 + 서비스명 (화면 좌상단 고정)
logo_path = "UI/Tori.png"
try:
    if os.path.exists(logo_path):
        with st.container(key="logo_header"):
            col_logo, col_title = st.columns([1, 4])
            with col_logo:
                st.image(logo_path)
            with col_title:
                st.markdown(
                    '<span>법률/노무 AI 챗봇</span>',
                    unsafe_allow_html=True
                )
except Exception as e:
    st.caption(f"⚠️ 로고 로드 실패: {e}")

# 5-2. 웰컴 메시지 (대화 없을 때만 표시)
if not st.session_state.messages:
    st.markdown(
        """
        <div class="chat-welcome">
            <h1>법률/노무에 대해 궁금한 점이 있으신가요<span class="brand-dot">?</span></h1>
            <p>근로계약 · 해고 · 임금 · 퇴직금 관련 법령을 근거로 답변해 드려요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 5-3. 채팅 대화 기록
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📚 참고한 법령 보기"):
                for s in msg["sources"]:
                    st.markdown(f"**{s['source']}** \n{s['content']}")

# 5-4. 자주 묻는 질문
st.markdown('<div class="faq-fixed-label">💡 자주 묻는 예시 질문</div>', unsafe_allow_html=True)

FAQ_QUESTIONS = [
    "📝 근로계약서 작성 시 반드시 포함해야 할 조항이 무엇인가요?",
    "💼 부당해고 구제신청은 어떻게 진행하나요?",
    "⏱️ 연장근로수당 계산 기준이 궁금합니다.",
]
with st.container(key="faq_area"):
    faq_cols = st.columns(3, gap="medium")
    for i, q in enumerate(FAQ_QUESTIONS):
        with faq_cols[i]:
            if st.button(q, key=f"faq_{i}", use_container_width=True):
                st.session_state.queued_question = q.split(" ", 1)[1]

# 5-5. ➕ 첨부 버튼 — 채팅창 안쪽에 시각적으로 병합
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

# 5-6. 진짜 작동하는 채팅창 — st.chat_input
user_input = st.chat_input("여기에 질문을 입력하세요...")

# FAQ 버튼 클릭 시 대기 중인 질문 처리
if st.session_state.queued_question:
    user_input = st.session_state.queued_question
    st.session_state.queued_question = None

# ─────────────────────────────────────────────
# 6. 질문 처리 → RAG 검색 → gpt-4o 답변 생성
# ─────────────────────────────────────────────
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("관련 법령 검색 중..."):
            docs = load_law_documents()
            contexts = retrieve(user_input, docs, top_k=3)
        try:
            answer = st.write_stream(generate_answer(user_input, contexts))
        except Exception as e:
            answer = f"⚠️ API 연결 중 오류가 발생했습니다: {e}"
            st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": contexts}
    )
    st.rerun()