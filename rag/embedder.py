"""
embedder.py
pipeline.py가 만든 청크(Document) 리스트를 임베딩하여 ChromaDB에 저장한다.

역할 분담 기준:
  - 이 파일은 "벡터DB를 만드는" 스크립트다. 법령이 추가/개정될 때만 실행한다.
  - Server 팀은 이 파일을 직접 쓰지 않는다. Server 팀은 retriever.py를 통해
    이미 만들어진 벡터DB를 "검색"만 한다.

사용 예:
    from pipeline import build_chunks
    from embedder import build_vectorstore

    chunks = build_chunks(["근로기준법", "최저임금법", "근로자퇴직급여 보장법"])
    build_vectorstore(chunks)  # ./chroma_db 에 저장됨
"""

import os
import shutil

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")

# 벡터DB 경로는 실행 위치가 아니라 이 파일(rag/) 기준으로 고정한다.
# server를 repo 루트에서 띄워도 rag/chroma_db를 정확히 찾도록 하기 위함.
_RAG_DIR = os.path.dirname(os.path.abspath(__file__))
_persist_dir_env = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
PERSIST_DIR = (
    _persist_dir_env
    if os.path.isabs(_persist_dir_env)
    else os.path.normpath(os.path.join(_RAG_DIR, _persist_dir_env))
)
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "labor_law")


class EmbeddingError(Exception):
    """임베딩/벡터DB 저장 관련 예외"""
    pass


def get_embedding_function() -> OpenAIEmbeddings:
    """
    임베딩 함수를 생성한다. embedder.py와 retriever.py 양쪽에서
    동일한 임베딩 모델을 써야 검색이 정상 동작하므로 함수로 분리해둔다.

    임베딩은 OpenAI 직접 호출이 아니라 OpenRouter를 경유한다.
    모델명에는 provider 접두사(openai/)가 필요하다.

    Raises:
        EmbeddingError: OPENAI_API_KEY가 없을 경우
    """
    if not OPENAI_API_KEY:
        raise EmbeddingError(
            "환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다. "
            "임베딩은 OpenRouter를 경유하므로 OpenRouter API 키가 필요합니다. .env를 확인하세요."
        )
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


def build_vectorstore(
    chunks: list[Document],
    persist_dir: str = PERSIST_DIR,
    collection_name: str = COLLECTION_NAME,
    overwrite: bool = True,
    batch_size: int = 100,
) -> Chroma:
    """
    청크 리스트를 임베딩하여 ChromaDB에 저장한다.

    Args:
        chunks: chunker.py/pipeline.py가 만든 청크 리스트
        persist_dir: ChromaDB 저장 경로 (디스크에 남음)
        collection_name: Chroma 컬렉션 이름
        overwrite: True면 기존 persist_dir을 지우고 새로 만든다.
            False면 기존 DB에 추가(append)한다.
        batch_size: 한 번에 임베딩 요청할 청크 수
            (한꺼번에 너무 많이 보내면 API 타임아웃/속도제한 위험이 있어 나눠 보냄)

    Returns:
        Chroma: 저장된 벡터스토어 객체 (바로 검색 테스트도 가능)

    Raises:
        EmbeddingError: 청크가 비어있거나 API 키가 없을 경우
    """
    if not chunks:
        raise EmbeddingError("임베딩할 청크가 없습니다. build_chunks() 결과를 확인하세요.")

    embedding_fn = get_embedding_function()

    if overwrite and os.path.exists(persist_dir):
        print(f"🗑️ 기존 벡터DB 삭제: {persist_dir}")
        shutil.rmtree(persist_dir)

    print(f"🧠 {len(chunks)}개 청크 임베딩 시작 (모델: {EMBEDDING_MODEL})...")

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_fn,
        persist_directory=persist_dir,
    )

    # 배치로 나눠서 add (전체를 한 번에 보내면 타임아웃/속도제한 위험)
    total = len(chunks)
    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]
        vectorstore.add_documents(batch)
        print(f"  진행: {min(i + batch_size, total)}/{total}")

    print(f"✅ 벡터DB 저장 완료: {persist_dir} (컬렉션: {collection_name})")
    return vectorstore


def load_vectorstore(
    persist_dir: str = PERSIST_DIR,
    collection_name: str = COLLECTION_NAME,
) -> Chroma:
    """
    이미 만들어진 벡터DB를 불러온다. (retriever.py에서 사용할 함수)

    Args:
        persist_dir: ChromaDB 저장 경로
        collection_name: Chroma 컬렉션 이름

    Returns:
        Chroma: 벡터스토어 객체

    Raises:
        EmbeddingError: persist_dir이 존재하지 않을 경우 (아직 build_vectorstore를 안 돌린 상태)
    """
    if not os.path.exists(persist_dir):
        raise EmbeddingError(
            f"벡터DB가 존재하지 않습니다: {persist_dir}. "
            "먼저 build_vectorstore()를 실행해서 DB를 생성하세요."
        )

    embedding_fn = get_embedding_function()

    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding_fn,
        persist_directory=persist_dir,
    )


if __name__ == "__main__":
    from pipeline import build_chunks

    LAW_LIST = ["근로기준법", "최저임금법", "근로자퇴직급여 보장법"]

    chunks = build_chunks(LAW_LIST)
    vectorstore = build_vectorstore(chunks)

    # 저장 확인용 간단 검색 테스트
    print("\n--- 검색 테스트: '해고 예고 수당' ---")
    results = vectorstore.similarity_search("해고 예고 수당", k=3)
    for doc in results:
        print(f"[{doc.metadata['법령명']} {doc.metadata['조문번호']}조] {doc.metadata['조문제목']}")
        print(doc.page_content[:100], "...\n")