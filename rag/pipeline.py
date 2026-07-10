"""
pipeline.py
collector.py → preprocessor.py → chunker.py 를 순서대로 실행하는 단일 진입점.

다른 팀원(백엔드)은 이 파일의 build_chunks() 함수 하나만 호출하면
법령명 리스트를 넘겨서 바로 임베딩/벡터DB에 넣을 수 있는
청크(Document) 리스트를 받을 수 있다.

사용 예:
    from pipeline import build_chunks

    chunks = build_chunks(["근로기준법", "최저임금법", "근로자퇴직급여 보장법"])
    # chunks: list[Document] -> 임베딩 후 ChromaDB 등에 저장
"""

from langchain_core.documents import Document

try:
    # server 등 외부에서 `from rag.pipeline import build_chunks`로 부를 때
    from rag.collector import fetch_law_json, fetch_multiple_laws, LawApiError
    from rag.preprocessor import parse_law_to_documents, parse_multiple_laws
    from rag.chunker import chunk_documents
except ImportError:
    # rag 폴더에서 단독 실행할 때
    from collector import fetch_law_json, fetch_multiple_laws, LawApiError
    from preprocessor import parse_law_to_documents, parse_multiple_laws
    from chunker import chunk_documents


def build_chunks(
    law_names: list[str],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[Document]:
    """
    법령명 리스트를 받아 수집 → 전처리 → 청킹까지 한 번에 수행한다.

    Args:
        law_names: 수집할 법령명 리스트 (예: ["근로기준법", "최저임금법"])
        chunk_size: chunker.py에 전달할 청크 최대 길이
        chunk_overlap: chunker.py에 전달할 청크 간 겹침 길이

    Returns:
        list[Document]: 임베딩/벡터DB 저장에 바로 쓸 수 있는 청크 리스트.
            개별 법령 수집/파싱 실패 시 해당 법령만 건너뛰고 나머지는 정상 처리된다.
    """
    print(f"📚 총 {len(law_names)}개 법령 파이프라인 시작: {law_names}")

    # 1) 수집 (여러 법령 한 번에, 실패한 법령은 내부에서 경고 후 제외)
    raw_data_map = fetch_multiple_laws(law_names)

    if not raw_data_map:
        print("⚠️ 수집된 법령이 하나도 없습니다. 빈 리스트를 반환합니다.")
        return []

    # 2) 전처리 (조문 단위 Document 생성)
    articles = parse_multiple_laws(raw_data_map)

    if not articles:
        print("⚠️ 파싱된 조문이 하나도 없습니다. 빈 리스트를 반환합니다.")
        return []

    # 3) 청킹
    chunks = chunk_documents(articles, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    print(f"✅ 파이프라인 완료: 조문 {len(articles)}개 → 청크 {len(chunks)}개")
    return chunks


def build_chunks_single(
    law_name: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[Document]:
    """
    법령 하나만 빠르게 처리하고 싶을 때 사용하는 편의 함수.
    (내부적으로 build_chunks(["법령명"])와 동일하게 동작하지만,
     단일 법령 실패 시 예외를 그대로 위로 던져서 원인을 바로 알 수 있게 한다.)

    Args:
        law_name: 법령명 (예: "근로기준법")
        chunk_size: 청크 최대 길이
        chunk_overlap: 청크 간 겹침 길이

    Returns:
        list[Document]: 청크 리스트

    Raises:
        LawApiError: 수집 실패 시
        KeyError: 전처리 실패 시 (예상 못한 JSON 구조)
    """
    raw_data = fetch_law_json(law_name)
    articles = parse_law_to_documents(law_name, raw_data)
    chunks = chunk_documents(articles, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunks


if __name__ == "__main__":
    # 노무 상담 챗봇에 필요할 만한 법령들을 넉넉하게 수집하는 예시.
    # 팀 논의 후 목록을 조정하면 된다.
    LAW_LIST = [
        "근로기준법",
        "최저임금법",
        "근로자퇴직급여 보장법",
    ]

    chunks = build_chunks(LAW_LIST)

    print(f"\n총 청크 수: {len(chunks)}개")
    print("\n--- 법령별 청크 개수 ---")
    counts: dict[str, int] = {}
    for c in chunks:
        name = c.metadata.get("법령명", "알 수 없음")
        counts[name] = counts.get(name, 0) + 1
    for name, count in counts.items():
        print(f"  {name}: {count}개")

    print("\n--- 샘플 청크 1개 ---")
    if chunks:
        print("metadata:", chunks[0].metadata)
        print("content:\n", chunks[0].page_content[:300])