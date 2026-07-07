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

### 4. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 만들고 OpenAI API 키를 넣습니다.

```env
OPENAI_API_KEY=sk-여기에-본인-키-입력
```

> ⚠️ `.env` 파일은 `.gitignore`에 등록되어 있어 git에 올라가지 않습니다. **API 키를 절대 커밋하지 마세요.**

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

```
rag-chatbot-demo/
├── app.py              # Streamlit 메인 앱
├── requirements.txt    # 의존성 목록
├── .gitignore
├── .env                # API 키 (직접 생성, git 제외)
└── README.md
```
