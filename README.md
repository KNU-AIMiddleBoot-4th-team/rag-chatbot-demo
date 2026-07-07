# RAG Chatbot Demo

LangChain · OpenAI · ChromaDB · Streamlit 기반 RAG(문서 기반 질의응답) 챗봇 데모입니다.

## 요구 사항

- Python 3.10 이상
- OpenAI API 키

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/KNU-AIMiddleBoot-4th-team/rag-chatbot-demo.git
cd rag-chatbot-demo
```

### 2. 가상환경 생성 및 활성화

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

## 실행 방법

```bash
streamlit run app.py
```

실행 후 브라우저에서 `http://localhost:8501` 로 접속합니다.

## 주요 패키지

| 패키지 | 버전 | 역할 |
|--------|------|------|
| streamlit | 1.59.0 | 웹 UI |
| langchain | 1.3.11 | RAG 파이프라인 |
| langchain-openai | 1.3.3 | OpenAI 연동 |
| chromadb | 1.5.9 | 벡터 데이터베이스 |
| pypdf | 6.14.2 | PDF 문서 로드 |

## 프로젝트 구조

UI / Data / Server 3계층으로 관심사를 분리합니다.

```
rag-chatbot-demo/
├── app.py              # 진입점 (streamlit run app.py)
├── ui/                 # 🎨 UI 계층 - Streamlit 화면
├── rag/                # 📚 Data 계층 - 문서 로드·청킹·벡터DB (RAG)
├── server/             # ⚙️ Server 계층 - LLM 호출·체인·설정
├── data/               # 원본 문서 (PDF 등)
├── requirements.txt    # 의존성 목록
├── .gitignore
├── .env                # API 키 (직접 생성, git 제외)
└── README.md
```

| 계층 | 폴더 | 역할 |
|------|------|------|
| UI | `ui/` | 화면 그리기, 사용자 입력/출력 |
| Data | `rag/` | 문서 → 청크 → 임베딩 → 검색 |
| Server | `server/` | LLM 호출, RAG 체인 조립, 설정 |

## 커밋 컨벤션

커밋 메시지는 아래 5가지 타입만 사용합니다.

```
type: 설명
```

| 타입 | 용도 |
|------|------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `chore` | 설정, 패키지, 빌드 등 잡일 |
| `docs` | 문서 수정 (README 등) |
| `refactor` | 기능 변경 없는 코드 구조 개선 |

**예시**

```
feat: PDF 업로드 기능 추가
fix: 벡터 검색 결과 중복 제거
docs: 설치 방법 보완
```
