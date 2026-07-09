import os
import sys
import json
import urllib.request
import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent
SERVER_DIR = ROOT_DIR / "server"

st.set_page_config(page_title="법률/노무 AI 챗봇", page_icon="⚖️", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "queued_question" not in st.session_state:
    st.session_state.queued_question = None


def get_secret_or_env(key: str, default=None):
    try:
        value = st.secrets.get(key, None)
    except Exception:
        value = None
    if value in (None, ""):
        value = os.environ.get(key, default)
    return value


OPEN_ROUTER_KEY = get_secret_or_env("OPEN_ROUTER_KEY")
LAW_API_KEY = get_secret_or_env("LAW_API_KEY")
LAW_SEARCH_URL = get_secret_or_env("LAW_SEARCH_URL")
LAW_SERVICE_URL = get_secret_or_env("LAW_SERVICE_URL")
EMBEDDING_MODEL = get_secret_or_env("EMBEDDING_MODEL", "openai/text-embedding-3-small")
CHROMA_PERSIST_DIR = get_secret_or_env("CHROMA_PERSIST_DIR", str(ROOT_DIR / "chroma_db"))
CHROMA_COLLECTION_NAME = get_secret_or_env("CHROMA_COLLECTION_NAME", "labor_law")
CHAT_MODEL = get_secret_or_env("CHAT_MODEL", "gpt-4o")

for _key, _value in {
    "OPEN_ROUTER_KEY": OPEN_ROUTER_KEY,
    "LAW_API_KEY": LAW_API_KEY,
    "LAW_SEARCH_URL": LAW_SEARCH_URL,
    "LAW_SERVICE_URL": LAW_SERVICE_URL,
    "EMBEDDING_MODEL": EMBEDDING_MODEL,
    "CHROMA_PERSIST_DIR": CHROMA_PERSIST_DIR,
    "CHROMA_COLLECTION_NAME": CHROMA_COLLECTION_NAME,
    "CHAT_MODEL": CHAT_MODEL,
}.items():
    if _value:
        os.environ[_key] = _value


def load_server_modules() -> dict[str, Any]:
    modules: dict[str, Any] = {}
    if not SERVER_DIR.exists():
        return modules

    for py_file in sorted(SERVER_DIR.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        module_name = f"server_{py_file.stem}_{abs(hash(py_file.resolve()))}"
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            modules[str(py_file)] = module
        except Exception:
            continue
    return modules


SERVER_MODULES = load_server_modules()


def call_server_function(candidate_names: list[str], *args, **kwargs):
    for module in SERVER_MODULES.values():
        for name in candidate_names:
            fn = getattr(module, name, None)
            if callable(fn):
                try:
                    return fn(*args, **kwargs)
                except TypeError:
                    try:
                        return fn(*args)
                    except Exception:
                        pass
                except Exception:
                    pass
    return None


def normalize_documents(value: Any) -> list[dict]:
    if isinstance(value, pd.DataFrame):
        cols = set(value.columns)
        if {"source", "content"} <= cols:
            return value[["source", "content"]].to_dict("records")
        return value.to_dict("records")

    if isinstance(value, list):
        docs: list[dict] = []
        for item in value:
            if isinstance(item, dict):
                docs.append(item)
            elif isinstance(item, tuple) and len(item) >= 2:
                docs.append({"source": item[0], "content": item[1]})
        return docs

    if isinstance(value, dict):
        for key in ("documents", "docs", "items"):
            if isinstance(value.get(key), list):
                return normalize_documents(value[key])

    return []


def _post_json(url: str, payload: dict):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_remote_search(query: str, docs: list[dict], top_k: int = 3):
    if not (LAW_SEARCH_URL or LAW_SERVICE_URL):
        return None

    payload = {
        "query": query,
        "top_k": top_k,
        "documents": docs,
        "api_key": LAW_API_KEY,
    }

    endpoints = []
    if LAW_SEARCH_URL:
        endpoints.append(LAW_SEARCH_URL)
        endpoints.append(f"{LAW_SEARCH_URL.rstrip('/')}/search")
        endpoints.append(f"{LAW_SEARCH_URL.rstrip('/')}/query")
    if LAW_SERVICE_URL:
        endpoints.append(LAW_SERVICE_URL)
        endpoints.append(f"{LAW_SERVICE_URL.rstrip('/')}/search")
        endpoints.append(f"{LAW_SERVICE_URL.rstrip('/')}/query")

    for endpoint in endpoints:
        try:
            result = _post_json(endpoint, payload)
            if isinstance(result, dict):
                if isinstance(result.get("documents"), list):
                    return normalize_documents(result["documents"])
                if isinstance(result.get("docs"), list):
                    return normalize_documents(result["docs"])
            if isinstance(result, list):
                return normalize_documents(result)
        except Exception:
            continue
    return None


def call_remote_answer(query: str, contexts: list[dict]):
    if not LAW_SERVICE_URL:
        return None

    payload = {
        "query": query,
        "contexts": contexts,
        "api_key": LAW_API_KEY,
    }

    endpoints = [
        LAW_SERVICE_URL,
        f"{LAW_SERVICE_URL.rstrip('/')}/chat",
        f"{LAW_SERVICE_URL.rstrip('/')}/answer",
    ]
    for endpoint in endpoints:
        try:
            result = _post_json(endpoint, payload)
            if isinstance(result, dict):
                if isinstance(result.get("answer"), str):
                    return result["answer"]
                if isinstance(result.get("content"), str):
                    return result["content"]
            if isinstance(result, str):
                return result
        except Exception:
            continue
    return None


@st.cache_resource
def get_client() -> OpenAI:
    api_key = OPEN_ROUTER_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPEN_ROUTER_KEY 또는 OPENAI_API_KEY가 설정되어야 합니다.")

    kwargs = {"api_key": api_key}
    if OPEN_ROUTER_KEY:
        kwargs["base_url"] = "https://openrouter.ai/api/v1"
    return OpenAI(**kwargs)


@st.cache_data
def load_law_documents() -> list[dict]:
    server_docs = call_server_function(
        [
            "load_law_documents",
            "load_documents",
            "get_law_documents",
            "get_documents",
            "load_data",
            "get_documents_from_service",
        ]
    )
    if server_docs is not None:
        docs = normalize_documents(server_docs)
        if docs:
            return docs

    try:
        df = pd.read_csv(ROOT_DIR / "data" / "law_data.csv")
        return df[["source", "content"]].to_dict("records")
    except Exception:
        return [
            {
                "source": "근로기준법 제17조(근로조건의 명시)",
                "content": "사용자는 근로계약을 체결할 때에 근로자에게 임금(구성항목·계산방법·지급방법), 소정근로시간, 휴일, 연차 유급휴가 등을 명시해야 하며, 서면(전자문서 포함) 교부해야 한다.",
            },
            {
                "source": "근로기준법 제23조(해고 등의 제한)",
                "content": "사용자는 근로자에게 정당한 이유 없이 해고, 휴직, 정직, 전직, 감봉, 그 밖의 징벌을 하지 못한다.",
            },
            {
                "source": "근로기준법 제26조(해고의 예고)",
                "content": "사용자는 근로자를 해고하려면 적어도 30일 전에 예고를 하여야 하고, 30일 전에 예고를 하지 아니하였을 때에는 30일분 이상의 통상임금을 지급하여야 한다.",
            },
            {
                "source": "근로기준법 제56조(연장·야간 및 휴일 근로)",
                "content": "사용자는 연장근로에 대하여 통상임금의 100분의 50 이상을 가산하여 근로자에게 지급하여야 한다. 야간근로(오후 10시부터 다음 날 오전 6시)에 대해서도 동일하게 가산한다.",
            },
            {
                "source": "근로자퇴직급여 보장법 제4조(퇴직급여제도의 설정)",
                "content": "사용자는 퇴직하는 근로자에게 급여를 지급하기 위하여 퇴직급여제도 중 하나 이상의 제도를 설정하여야 한다. 계속근로기간이 1년 미만인 근로자는 제외한다.",
            },
            {
                "source": "노동위원회법·근로기준법 제28조(부당해고 구제신청)",
                "content": "사용자가 근로자에게 부당해고 등을 하면 근로자는 노동위원회에 구제를 신청할 수 있다. 구제신청은 부당해고 등이 있었던 날부터 3개월 이내에 하여야 한다.",
            },
        ]


@st.cache_data
def embed_documents(texts: tuple[str, ...]) -> np.ndarray:
    server_result = call_server_function(
        ["embed_documents", "create_embeddings", "get_embeddings", "embed_texts"],
        list(texts),
    )
    if server_result is not None:
        arr = np.asarray(server_result)
        if arr.ndim == 2:
            return arr

    client = get_client()
    res = client.embeddings.create(model=EMBEDDING_MODEL, input=list(texts))
    return np.array([d.embedding for d in res.data])


def retrieve(query: str, docs: list[dict], top_k: int = 3) -> list[dict]:
    server_result = call_server_function(
        ["retrieve", "search_documents", "retrieve_documents", "vector_search", "query_documents"],
        query,
        docs,
        top_k,
    )
    if server_result is not None:
        normalized = normalize_documents(server_result)
        if normalized:
            return normalized[:top_k]

    remote_result = call_remote_search(query, docs, top_k=top_k)
    if remote_result:
        return remote_result[:top_k]

    try:
        doc_vecs = embed_documents(tuple(d["content"] for d in docs))
        q_res = get_client().embeddings.create(model=EMBEDDING_MODEL, input=[query])
        q_vec = np.array(q_res.data[0].embedding)
        sims = doc_vecs @ q_vec / (
            np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(q_vec) + 1e-9
        )
        idx = np.argsort(sims)[::-1][:top_k]
        return [docs[i] for i in idx if sims[i] > 0.2]
    except Exception:
        return [
            d
            for d in docs
            if any(w in d["content"] or w in d["source"] for w in query.split())
        ][:top_k]


def generate_answer(query: str, contexts: list[dict]):
    server_result = call_server_function(
        ["generate_answer", "answer_query", "generate_response", "run_chain"],
        query,
        contexts,
    )
    if isinstance(server_result, str):
        yield server_result
        return

    remote_result = call_remote_answer(query, contexts)
    if isinstance(remote_result, str):
        yield remote_result
        return

    context_text = "\n\n".join(f"[{c['source']}]\n{c['content']}" for c in contexts) or (
        "관련 법령이 DB에서 검색되지 않았습니다. 일반적인 법률 지식으로 답변하되, 그 사실을 명시하세요."
    )
    system_prompt = (
        "당신은 대한민국 법률 및 인사노무 전문 AI 챗봇입니다.\n"
        "반드시 아래 [참고 법령 데이터]를 근거로 답변하고, 인용한 조문의 출처를 밝히세요.\n"
        "데이터에 없는 내용은 추측하지 말고 '전문가 상담이 필요하다'고 안내하세요.\n"
        "답변 마지막에는 '※ 본 답변은 참고용이며 법적 효력이 없습니다.'를 붙이세요.\n\n"
        f"[참고 법령 데이터]\n{context_text}"
    )
    stream = get_client().chat.completions.create(
        model=CHAT_MODEL,
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

if not st.session_state.messages:
    st.markdown(
        """
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
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
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
            background: linear-gradient(to top, #ffffff 55%, rgba(255, 255, 255, 0.9) 75%, rgba(255, 255, 255, 0) 100%) !important;
            z-index: 900 !important;
            pointer-events: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
                    unsafe_allow_html=True,
                )
except Exception:
    pass

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

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📚 참고한 법령 보기"):
                for s in msg["sources"]:
                    st.markdown(f"**{s['source']}**\n{s['content']}")

st.markdown('<div class="bottom-backdrop"></div>', unsafe_allow_html=True)

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

components.html(
    """
    <script>
    (function () {
        function focusChatInput() {
            try {
                const doc = window.parent.document;
                const ta = doc.querySelector('[data-testid="stChatInput"] textarea');
                if (ta && doc.activeElement !== ta) {
                    ta.focus();
                }
            } catch (e) {}
        }
        setTimeout(focusChatInput, 200);
    })();
    </script>
    """,
    height=0,
)

user_input = st.chat_input("여기에 질문을 입력하세요...")

if st.session_state.queued_question:
    user_input = st.session_state.queued_question
    st.session_state.queued_question = None

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("관련 법령 검색 중..."):
            docs = load_law_documents()
            contexts = retrieve(user_input, docs, top_k=3)

        answer_chunks = []
        for chunk in generate_answer(user_input, contexts):
            answer_chunks.append(chunk)
            st.write(chunk)

        answer = "".join(answer_chunks)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": contexts}
    )
    st.rerun()