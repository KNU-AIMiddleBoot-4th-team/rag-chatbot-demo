"""
retriever.py
Server 팀이 매 사용자 질문마다 호출할 검색 인터페이스.

역할 분담 기준:
  - embedder.py가 만들어둔 ChromaDB(./chroma_db)를 "불러와서 검색만" 한다.
  - 여기서는 절대 법제처 API를 호출하거나 벡터DB를 새로 만들지 않는다.
    (수집/임베딩/저장은 collector.py~embedder.py가 1회성으로 담당)
  - Server 팀은 이 파일의 retrieve() 함수 하나만 import해서 쓰면 된다.
    법제처 JSON 구조나 임베딩 모델이 뭔지 몰라도 됨.

사용 예 (Server 팀 코드에서):
    from retriever import retrieve

    docs = retrieve("해고 예고 수당은 어떻게 되나요?", k=4)
    for doc in docs:
        print(doc.metadata["법령명"], doc.metadata["조문번호"], doc.page_content)
"""

from langchain_core.documents import Document

try:
    # server 등 외부에서 `from rag.retriever import retrieve`로 부를 때
    from rag.embedder import load_vectorstore, EmbeddingError
except ImportError:
    # rag 폴더에서 단독 실행할 때 (python -m rag.retriever가 아닌 경우)
    from embedder import load_vectorstore, EmbeddingError

# 벡터DB는 프로세스 시작 시 1번만 불러오고 재사용한다.
# (요청마다 새로 로드하면 매번 ChromaDB 연결 비용이 들어 비효율적)
_vectorstore = None


class RetrieverError(Exception):
    """검색 관련 예외"""
    pass


def _get_vectorstore():
    """
    벡터스토어를 lazy하게 1번만 로드해서 재사용한다.
    (모듈 import 시점이 아니라 첫 retrieve() 호출 시점에 로드 —
     Server 앱이 뜰 때 벡터DB 로드 실패로 전체가 죽는 것을 방지)
    """
    global _vectorstore
    if _vectorstore is None:
        try:
            _vectorstore = load_vectorstore()
        except EmbeddingError as e:
            raise RetrieverError(
                f"벡터DB 로드 실패: {e}. "
                "embedder.py를 먼저 실행해서 벡터DB를 생성했는지 확인하세요."
            ) from e
    return _vectorstore


def retrieve(query: str, k: int = 4) -> list[Document]:
    """
    질문을 받아 관련 법 조문 청크 k개를 반환한다.

    Args:
        query: 사용자 질문 (예: "해고 예고 수당은 어떻게 되나요?")
        k: 반환할 문서(청크) 개수 (기본 4개)

    Returns:
        list[Document]: 관련도 순으로 정렬된 청크 리스트.
            각 Document는 다음 metadata를 포함한다:
              - 법령명 (예: "근로기준법")
              - 조문번호 (예: "26")
              - 조문제목 (예: "해고의 예고")
              - 조문키
              - 소속장 (장/절 제목)
              - source ("법제처 Open API")
              - chunk_index, chunk_total (조문이 여러 청크로 쪼개진 경우)

    Raises:
        RetrieverError: 벡터DB가 없거나 검색 실패 시
        ValueError: query가 빈 문자열일 경우
    """
    if not query or not query.strip():
        raise ValueError("검색어(query)가 비어있습니다.")

    vectorstore = _get_vectorstore()

    try:
        results = vectorstore.similarity_search(query, k=k)
    except Exception as e:
        raise RetrieverError(f"벡터DB 검색 중 오류 발생: {e}") from e

    return results


def retrieve_with_score(query: str, k: int = 4) -> list[tuple[Document, float]]:
    """
    retrieve()와 동일하지만 유사도 점수(score)도 함께 반환한다.
    Server 팀이 "관련성이 너무 낮으면 답변 거부" 같은 임계값 로직을
    구현할 때 사용할 수 있다.

    Args:
        query: 사용자 질문
        k: 반환할 문서 개수

    Returns:
        list[tuple[Document, float]]: (문서, 거리 점수) 튜플 리스트.
            ChromaDB 기본값은 "거리(distance)"이므로 값이 작을수록 더 유사하다.

    Raises:
        RetrieverError: 벡터DB가 없거나 검색 실패 시
        ValueError: query가 빈 문자열일 경우
    """
    if not query or not query.strip():
        raise ValueError("검색어(query)가 비어있습니다.")

    vectorstore = _get_vectorstore()

    try:
        results = vectorstore.similarity_search_with_score(query, k=k)
    except Exception as e:
        raise RetrieverError(f"벡터DB 검색 중 오류 발생: {e}") from e

    return results


def retrieve_by_law(query: str, law_name: str, k: int = 4) -> list[Document]:
    """
    특정 법령으로 범위를 좁혀서 검색한다.
    (예: 최저임금법 관련 질문임이 명확할 때, 근로기준법 조문이 섞여 나오는 것을 방지)

    Args:
        query: 사용자 질문
        law_name: 검색 범위를 좁힐 법령명 (예: "최저임금법")
        k: 반환할 문서 개수

    Returns:
        list[Document]: 해당 법령 내에서 관련도 순으로 정렬된 청크 리스트

    Raises:
        RetrieverError: 벡터DB가 없거나 검색 실패 시
        ValueError: query가 빈 문자열일 경우
    """
    if not query or not query.strip():
        raise ValueError("검색어(query)가 비어있습니다.")

    vectorstore = _get_vectorstore()

    try:
        results = vectorstore.similarity_search(
            query, k=k, filter={"법령명": law_name}
        )
    except Exception as e:
        raise RetrieverError(f"벡터DB 검색 중 오류 발생: {e}") from e

    return results


if __name__ == "__main__":
    # 간단한 동작 확인용 (Server 팀 연동 전 로컬 테스트)
    test_queries = [
        "내일 날씨 어때요?",
        "무단결근 해도 되나요?",
        "퇴직금 지급 기한은 언제까지인가요?",
    ]

    for q in test_queries:
        print(f"\n{'='*50}")
        print(f"질문: {q}")
        print('='*50)
        docs = retrieve(q, k=3)
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata
            print(f"\n[{i}] {meta['법령명']} 제{meta['조문번호']}조 ({meta['조문제목']})")
            print(doc.page_content[:150], "...")