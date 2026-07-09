import streamlit as st
from openai import OpenAI

# 1. 페이지 기본 설정 및 스타일 정의
st.set_page_config(page_title="법률/노무 AI 챗봇", page_icon="⚖️", layout="centered")

# Toss & Gemini 스타일 커스텀 CSS
st.markdown(
    """
    <style>
    /* 전체 배경 흰색 및 기본 폰트 설정 */
    .stApp {
        background-color: #FFFFFF;
        color: #191F28;
    }
    
    /* 상단 타이틀 및 안내 문구 스타일 */
    .chat-welcome {
        text-align: center;
        margin-top: 3rem;
        margin-bottom: 2rem;
    }
    .chat-welcome h1 {
        font-size: 2.2rem;
        font-weight: 700;
        color: #191F28;
        margin-bottom: 0.5rem;
    }
    .chat-welcome p {
        font-size: 1.1rem;
        color: #4E5968;
    }
    
    /* 토스 블루 포인트 컬러 적용 (아코디언 및 버튼 강조용) */
    div[data-testid="stExpander"] {
        border: 1px solid #E5E8EB !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02) !important;
        margin-bottom: 12px;
    }
    div[data-testid="stExpander"] summary {
        font-weight: 600 !important;
        color: #0184ff !important; /* 토스 아이덴티티 색상 */
    }
    div[data-testid="stExpander"] summary:hover {
        color: #3434e0 !important; /* 강한 포인트 색상 */
    }
    
    /* 하단 고정 입력창 영역 */
    .fixed-bottom-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: rgba(255, 255, 255, 0.95);
        padding: 20px 0;
        border-top: 1px solid #E5E8EB;
        z-index: 100;
    }
    
    /* 화면 하단 여백 설정 (고정창과 예시 질문이 겹치지 않도록 넓게 확보) */
    .main-content {
        margin-bottom: 280px;
    }
    .example-section {
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- [백엔드 연동 부분] ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    client = OpenAI(api_key="your-api-key-here") 

def search_law_database(query):
    law_db = {
        "근로계약": "근로기준법 제17조(근로조건의 명시): 사용자는 근로계약을 체결할 때에 근로자에게 임금, 소정근로시간, 휴일, 연차 유급휴가 등을 명시해야 하며, 서면으로 교부해야 한다.",
        "해고": "근로기준법 제23조(해고 등의 제한): 사용자는 근로자에게 정당한 이유 없이 해고, 휴직, 정직, 감봉, 그 밖의 징벌을 하지 못한다.",
        "퇴직금": "근로자퇴직급여 보장법 제4조: 사용자는 퇴직하는 근로자에게 급여를 지급하기 위하여 퇴직급여제도 중 하나 이상의 제도를 설정하여야 한다."
    }
    context = ""
    for key, val in law_db.items():
        if key in query:
            context += f"[{key} 관련 법령]\n{val}\n\n"
    return context if context else "관련된 명시적 법령 가이드가 DB에 없습니다. 일반적인 법률 지식을 기반으로 답변하세요."

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- [UI 렌더링 시작] ---

# 메인 콘텐츠 전체 레이아웃 감싸기
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# 1. 상단 웰컴 메시지
st.markdown(
    """
    <div class="chat-welcome">
        <h1>법률/노무에 대해 궁금한 점이 있으신가요?</h1>
    </div>
    """, 
    unsafe_allow_html=True
)

# 2. 채팅창 대화 기록 출력 영역 (질문과 답변이 쌓이는 곳)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. 채팅창 밑 + 입력창 위에 배치되는 예시 질문 카테고리
st.markdown('<div class="example-section"><strong>💡 자주 묻는 예시 질문</strong></div>', unsafe_allow_html=True)

with st.expander("📝 근로계약서 작성 시 반드시 포함해야 할 조항이 무엇인가요?"):
    st.markdown("""
    **법률/노무 AI 답변:** 근로기준법 제17조에 따라 **임금(구성항목, 계산방법, 지급방법), 소정근로시간, 휴일, 연차 유급휴가**는 반드시 서면으로 명시하고 근로자에게 교부해야 합니다.
    """)

with st.expander("💼 부당해고 구제신청은 어떻게 진행하나요?"):
    st.markdown("""
    **법률/노무 AI 답변:** 해고가 부당하다고 생각되시는 경우, 해고가 발생한 날로부터 **3개월 이내**에 회사 소재지 관할 **지방노동위원회**에 구제신청을 하실 수 있습니다. (상시 5인 이상 사업장 적용)
    """)

with st.expander("⏱️ 연장근로수당 계산 기준이 궁금합니다."):
    st.markdown("""
    **법률/노무 AI 답변:** 법정 근로시간(하루 8시간, 주 40시간)을 초과한 연장근로에 대해서는 **통상임금의 50% 이상**을 가산하여 지급해야 합니다.
    """)

st.markdown('</div>', unsafe_allow_html=True) # 메인 콘텐츠 끝

# 4. 최하단 고정형 입력창 바 (+버튼, 마이크버튼, 전송버튼)
st.markdown('<div class="fixed-bottom-container">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns([1, 1, 8, 2.0])

with col1: st.button("➕", key="btn_file")
with col2: st.button("🎤", key="btn_voice")
with col3: user_input = st.text_input("", placeholder="여기에 질문을 입력하세요...", key="user_message", label_visibility="collapsed")
with col4: send_triggered = st.button("➔", key="btn_send")

st.markdown('</div>', unsafe_allow_html=True)

# 5. [수정 완료] 데이터 처리 및 API 연동 로직 (들여쓰기 완성 블록)
if (send_triggered or user_input) and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("법률 데이터 검색 및 답변 생성 중..."):
        # 내부 DB에서 관련 법령 검색
        relevant_law_data = search_law_database(user_input)
        
        # ChatGPT 페르소나 및 데이터 결합 프롬프트 정의
        system_prompt = (
            "당신은 전문 법률 및 인사노무 전문 AI 챗봇입니다. "
            "반드시 아래 제공되는 [참고 법률 데이터]를 바탕으로 사용자의 질문에 정확하고 친절하게 답변하세요.\n\n"
            f"[참고 법률 데이터]\n{relevant_law_data}"
        )
        
        try:
            # OpenAI API 호출
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3
            )
            ai_response = response.choices[0].message.content
        except Exception as e:
            ai_response = f"⚠️ API 연결 중 오류가 발생했습니다: {str(e)}"
    
    # 생성된 답변을 대화 내역에 저장하고 화면 새로고침
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    st.rerun()