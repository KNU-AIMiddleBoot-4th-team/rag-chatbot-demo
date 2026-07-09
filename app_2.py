"""
법률/노무 AI 챗봇 — RAG 기반 상담 서비스
=========================================
브랜드 컬러 (이 3색만 사용):
  - 강조:       #3434e0
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

st.markdown(
    """
    <style>
    /* ===== 전역: 흰색 배경 ===== */
    .stApp {
        background-color: #ffffff;
    }

    /* ===== 상단 웰컴 타이틀 ===== */
    .chat-welcome {
        text-align: center;
        margin-top: 2rem;
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

    /* ===== FAQ + 입력창 통합 박스 ===== */
    .input-container {
        border: 1.5px solid #0184ff;
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(1, 132, 255, 0.18);
        background-color: #ffffff;
        padding: 20px;
        margin-bottom: 2rem;
        transition: all 0.15s ease;
    }
    .input-container:focus-within {
        border-color: #3434e0;
        box-shadow: 0 8px 32px rgba(52, 52, 224, 0.25);
    }

    /* ===== FAQ 라벨 및 버튼 ===== */
    .faq-label {
        font-weight: 700;
        color: #3434e0;
        margin-bottom: 12px;
        font-size: 0.9rem;
    }
    
    /* 개별 FAQ 버튼 래퍼 */
    .faq-item {
        margin-bottom: 10px;
    }
    .faq-item:last-child {
        margin-bottom: 16px;
    }
    
    .faq-item button {
        background-color: transparent !important;
        border: 1px solid #0184ff !important;
        color: #0184ff !important;
        border-radius: 10px !important;
        padding: 10px 12px !important;
        font-size: 0.85rem;
        font-weight: 500;
        text-align: left;
        width: 100% !important;
        box-shadow: none !important;
        transition: all 0.15s ease;
        white-space: normal !important;
        height: auto !important;
        line-height: 1.4;
    }
    .faq-item button:hover {
        border-color: #3434e0 !important;
        color: #3434e0 !important;
        background-color: rgba(1, 132, 255, 0.04) !important;
    }

    /* ===== 질문 입력창 (st.text_input) — 채팅창 스타일 ===== */
    [data-testid="stTextInput"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    [data-testid="stTextInput"] input {
        background-color: transparent !important;
        color: #191F28 !important;
        caret-color: #3434e0 !important;
        border: none !important;
        padding: 0 8px 0 0 !important;
        font-size: 0.95rem !important;
    }
    
    [data-testid="stTextInput"] input::placeholder {
        color: #A0A5B8 !important;
    }

    /* ===== ➕ 첨부 버튼 (입력 박스 내 왼쪽) ===== */
    .popover-button-area {
        display: inline-block;
        margin-right: 12px;
        margin-bottom: 0;
    }
    
    .popover-button-area button {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background-color: #ffffff !important;
        border: 1.5px solid #0184ff !important;
        color: #0184ff !important;
        font-size: 1rem;
        padding: 0 !important;
        box-shadow: none !important;
        transition: all 0.15s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .popover-button-area button:hover {
        border-color: #3434e0 !important;
        color: #3434e0 !important;
        background-color: rgba(1, 132, 255, 0.04) !important;
    }

    /* 채팅 여백 조정 */
    .block-container {
        padding-bottom: 2rem;
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
        # CSV가 없으면 샘플 데이터로 동작 (데모용)
        return [
            {"source": "근로기준법 제17조(근로조건의 명시)",
             "content": "사용자는 근로계약을 체결할 때에 근로자에게 임금(구성항목·계산방법·지급방법), 소정근로시간, 휴일, 연차 유급휴가 등을 명시해야 하며, 서면(전자문서 포함)으로 교부해야 한다."},
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
    """질문과 가장 관련 있는 법령 조문 top_k개 반환"""
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
        # 임베딩 API 실패 시 단순 키워드 매칭으로 폴백
        return [d for d in docs if any(w in d["content"] or w in d["source"]
                                       for w in query.split())][:top_k]


def generate_answer(query: str, contexts: list[dict]):
    """gpt-4o 스트리밍 응답 생성"""
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
# 5. 세션 상태
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "queued_question" not in st.session_state:
    st.session_state.queued_question = None

# ─────────────────────────────────────────────
# 6. UI 렌더링
# ─────────────────────────────────────────────

# 6-1. 헤더: 로고 + 서비스명
logo_path = "UI/Tori.png"
try:
    if os.path.exists(logo_path):
        col_logo, col_title = st.columns([1, 10])
        with col_logo:
            st.image(logo_path, width=36)
        with col_title:
            st.markdown(
                '<span style="font-size:0.95rem; font-weight:700; color:#0184ff; display:inline-block; padding-top:8px;">법률/노무 AI 챗봇</span>',
                unsafe_allow_html=True
            )
except Exception as e:
    st.caption(f"⚠️ 로고 로드 실패: {e}")

# 6-2. 웰컴 메시지 (대화 없을 때만 표시)
if not st.session_state.messages:
    st.markdown(
        """
        <div class="chat-welcome">
            <h1>법률/노무에 대해<br>궁금한 점이 있으신가요<span class="brand-dot">?</span></h1>
            <p>근로계약 · 해고 · 임금 · 퇴직금 관련 법령을 근거로 답변해 드려요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 6-3. 채팅 대화 기록
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📚 참고한 법령 보기"):
                for s in msg["sources"]:
                    st.markdown(f"**{s['source']}**  \n{s['content']}")

# 6-4. 하단 고정: FAQ + 입력창 통합
st.markdown(
    """
    <div style="margin-bottom: 180px;"></div>
    """,
    unsafe_allow_html=True
)

# 6-4-1. FAQ 라벨 및 버튼들 (위쪽 라운드)
st.markdown(
    """
    <div style="
        background-color: #ffffff;
        border: 1.5px solid #0184ff;
        border-radius: 20px 20px 0 0;
        border-bottom: none;
        padding: 20px 20px 12px 20px;
        box-shadow: 0 8px 24px rgba(1, 132, 255, 0.18);
        margin-bottom: 0;
    ">
        <div style="font-weight: 700; color: #3434e0; margin-bottom: 12px; font-size: 0.9rem;">
            💡 자주 묻는 예시 질문
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

FAQ_QUESTIONS = [
    "📝 근로계약서 작성 시 반드시 포함해야 할 조항이 무엇인가요?",
    "💼 부당해고 구제신청은 어떻게 진행하나요?",
    "⏱️ 연장근로수당 계산 기준이 궁금합니다.",
]

faq_cols = st.columns([1, 1, 1], gap="small")
for i, q in enumerate(FAQ_QUESTIONS):
    with faq_cols[i]:
        if st.button(q, key=f"faq_{i}", use_container_width=True):
            st.session_state.queued_question = q.split(" ", 1)[1]

# 6-4-2. 입력 영역 (➕ 버튼 + 질문 입력창) — 아래쪽 라운드로 연결
st.markdown(
    """
    <div style="
        background-color: #ffffff;
        border: 1.5px solid #0184ff;
        border-radius: 0 0 20px 20px;
        border-top: none;
        padding: 12px 20px;
        box-shadow: 0 8px 24px rgba(1, 132, 255, 0.18);
        margin-bottom: 2rem;
        margin-top: -1.5px;
    ">
    """,
    unsafe_allow_html=True
)

col_attach, col_input = st.columns([0.85, 10], gap="small")

with col_attach:
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

with col_input:
    user_input = st.text_input(
        "message",
        placeholder="여기에 질문을 입력하세요...",
        label_visibility="collapsed",
        key="chat_input"
    )

st.markdown(
    """
    </div>
    """,
    unsafe_allow_html=True
)

# FAQ 버튼 클릭 시 대기 중인 질문 처리
if st.session_state.queued_question:
    user_input = st.session_state.queued_question
    st.session_state.queued_question = None

# ─────────────────────────────────────────────
# 7. 질문 처리 → RAG 검색 → gpt-4o 답변 생성
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