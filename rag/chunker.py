"""
chunker.py
preprocessor.py가 만든 조문 단위 Document 리스트를 받아,
검색(임베딩)에 적합한 크기로 청킹한다.

전략:
  - 조문(Document) 하나가 이미 문맥적으로 완결된 단위이므로,
    chunk_size보다 짧은 조문은 절대 쪼개지 않고 그대로 청크 하나로 사용한다.
  - chunk_size를 넘는 긴 조문(항/호가 많은 조문)만 RecursiveCharacterTextSplitter로
    쪼개되, separators를 ["\n\n", "\n", " ", ""] 순으로 두어
    항/호 사이의 줄바꿈(\n) 경계에서 우선 잘리도록 한다.
    (preprocessor.py에서 항/호를 \n으로 구분해서 이어붙였기 때문에 가능)
  - 쪼개진 청크에는 chunk_index/chunk_total metadata를 추가해
    원래 같은 조문이었음을 추적할 수 있게 한다.
"""

from langchain_core.documents import Document

# langchain 최신 버전(1.x)은 RecursiveCharacterTextSplitter가
# langchain_text_splitters 패키지로 분리되었고, 구버전은 langchain.text_splitter에 있다.
# 두 경우 모두 지원하기 위해 순서대로 시도한다.
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[Document]:
    """
    조문 단위 Document 리스트를 청킹한다.

    Args:
        documents: preprocessor.py의 parse_law_to_documents/parse_multiple_laws 결과
        chunk_size: 청크 최대 길이 (기본 800자 - 대부분의 조문이 안 잘리도록 넉넉하게 설정)
        chunk_overlap: 청크 간 겹치는 길이 (긴 조문이 쪼개질 때 문맥 유지용)

    Returns:
        list[Document]: 청킹된 Document 리스트.
            원본 metadata(법령명, 조문번호 등)를 그대로 유지하며,
            조문이 여러 청크로 쪼개진 경우 chunk_index/chunk_total이 추가된다.
            (쪼개지지 않은 조문은 chunk_index=0, chunk_total=1)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    result: list[Document] = []

    for doc in documents:
        # 조문 하나 자체가 chunk_size 이하면 쪼개지 않고 그대로 사용
        if len(doc.page_content) <= chunk_size:
            new_doc = Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, "chunk_index": 0, "chunk_total": 1},
            )
            result.append(new_doc)
            continue

        # chunk_size를 넘는 조문만 항/호 경계 우선으로 분할
        sub_texts = splitter.split_text(doc.page_content)
        for idx, sub_text in enumerate(sub_texts):
            new_doc = Document(
                page_content=sub_text,
                metadata={
                    **doc.metadata,
                    "chunk_index": idx,
                    "chunk_total": len(sub_texts),
                },
            )
            result.append(new_doc)

    return result


if __name__ == "__main__":
    from collector import fetch_law_json
    from preprocessor import parse_law_to_documents

    raw = fetch_law_json("최저임금법")
    articles = parse_law_to_documents("최저임금법", raw)
    chunks = chunk_documents(articles)

    print(f"✅ 조문 {len(articles)}개 → 청크 {len(chunks)}개")
    
    split_articles = [c for c in chunks if c.metadata["chunk_total"] > 1]
    print(f"   그 중 여러 청크로 쪼개진 조문 수: {len(set(c.metadata['조문키'] for c in split_articles))}개")

    if split_articles:
        sample_key = split_articles[0].metadata["조문키"]
        print(f"\n--- 쪼개진 조문 샘플 (조문키={sample_key}) ---")
        for c in chunks:
            if c.metadata["조문키"] == sample_key:
                print(f"[chunk {c.metadata['chunk_index']+1}/{c.metadata['chunk_total']}] {len(c.page_content)}자")
                print(c.page_content[:200], "...")
                print()