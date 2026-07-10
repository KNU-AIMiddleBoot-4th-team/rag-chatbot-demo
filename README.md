# 프로젝트 개요
RAG 기반 기업 맞춤형 스마트 사내위키 - 법률/노무 문서 검색 챗봇
## 요구 사항

- Python 3.10 이상
- **OpenRouter API 키** (`OPEN_ROUTER_KEY`) — LLM 답변 생성 및 임베딩에 사용 (OpenAI가 아니라 OpenRouter 경유)
- **법제처 Open API 키** (`LAW_API_KEY`) — 벡터DB 최초 생성 시 법령 수집에 사용

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

### 4. 환경 변수(.env) 설정

`.env.example`을 복사해 `.env`를 만들고 키를 채웁니다. (`.env`는 `.gitignore`에 포함되어 커밋되지 않습니다.)

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
cp .env.example .env
```

`.env`에서 최소 아래 두 값을 실제 키로 입력합니다.

```
OPEN_ROUTER_KEY=발급받은 OpenRouter 키
LAW_API_KEY=발급받은 법제처 Open API 키
```

### 5. 벡터DB 생성 (최초 1회)

법령을 수집·임베딩하여 `rag/chroma_db`에 벡터DB를 만듭니다. **벡터DB가 이미 있으면 생략**합니다.

```bash
python -m rag.embedder
```

- 기본 수집 법령: 근로기준법 · 최저임금법 · 근로자퇴직급여 보장법
- 이 단계는 `OPEN_ROUTER_KEY`(임베딩)와 `LAW_API_KEY`(법령 수집)가 모두 필요합니다.
- `chroma_db/`는 `.gitignore` 대상이라 클론에는 포함되지 않으므로, 새로 받은 환경에서는 이 단계를 한 번 실행해야 합니다.

## 실행 방법

```bash
streamlit run app.py
```

실행 후 브라우저에서 `http://localhost:8501` 로 접속합니다.
(질문에 답이 나오려면 위 4·5단계가 완료돼 있어야 합니다.)

## 주요 패키지

| 패키지 | 버전 | 역할 |
|--------|------|------|
| streamlit | 1.59.0 | 웹 UI |
| langchain | 1.3.11 | RAG 파이프라인 |
| langchain-openai | 1.3.3 | OpenAI 연동 |
| langchain-chroma | 1.1.0 | 벡터스토어 연동 |
| chromadb | 1.5.9 | 벡터 데이터베이스 |
| requests | 2.34.2 | 법제처 Open API 호출 |

## 프로젝트 구조

UI / Data / Server 3계층으로 관심사를 분리합니다.

```
rag-chatbot-demo/
├── app.py              # 진입점 (streamlit run app.py)
├── ui/                 # 🎨 UI 계층 - Streamlit 화면
├── rag/                # 📚 Data 계층 - 법령 수집·청킹·임베딩·검색 (RAG)
│   └── chroma_db/      # 벡터DB (rag.embedder 로 생성, git 제외)
├── server/             # ⚙️ Server 계층 - LLM 호출·체인·설정
├── requirements.txt    # 의존성 목록
├── .gitignore
├── .env.example        # 환경 변수 템플릿 (복사해서 .env 생성)
├── .env                # API 키 (직접 생성, git 제외)
└── README.md
```

| 계층 | 폴더 | 역할 |
|------|------|------|
| UI | `ui/` | 화면 그리기, 사용자 입력/출력 |
| Data | `rag/` | 문서 → 청크 → 임베딩 → 검색 |
| Server | `server/` | LLM 호출, RAG 체인 조립, 설정 |

## 팀원별 담당 파트

| 이름 | 담당 파트 | 폴더 |
|------|-----------|------|
| 김상연 | UI (Streamlit 화면) | `ui/` |
| 김태현 | Data (RAG 파이프라인) | `rag/` |
| 장윤선 | Server (LLM·체인·설정) | `server/` |
| 김성환 | PM · 저장소 관리 · 아키텍처 설계 | `전체` |

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
