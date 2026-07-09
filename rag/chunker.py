"""
chunker.py
preprocessor.py가 만든 조문 단위 Document 리스트를 받아,
검색(임베딩)에 적합한 크기로 청킹한다.

전략 (항 단위 청킹):
  - 조문 하나를 통째로 임베딩하면 여러 항(①연장 ②휴일 ③야간)이 뭉쳐
    세부 항의 신호가 조문 평균 벡터에 희석되어, "몇 시부터", "몇 %" 같은
    구체 질문의 검색이 실패한다. 이를 막기 위해 항(項)을 독립 청크로 쪼갠다.
  - 항 마커(①-⑳)로 시작하는 줄이 항의 경계다.
    (preprocessor.py가 조 제목 + 각 항/호를 \n으로 이어붙였기 때문에 가능)
  - 항이 있는 조문: 첫 줄(조 제목)을 헤더로 추출하고, 항별로 쪼갠 뒤
    각 청크 앞에 헤더를 프리픽스로 붙여 "무슨 법 몇 조인지" 맥락을 보존한다.
  - 항이 없는 조문(예: 제1조): 이미 한 문장으로 완결되고 본문에 조 제목이
    포함돼 있으므로 쪼개지 않고 그대로 청크 하나로 사용한다.
  - 항 하나가 여전히 chunk_size를 넘으면 RecursiveCharacterTextSplitter로
    추가 분할하되, 각 조각에도 헤더 프리픽스를 유지한다.
  - 모든 청크에 chunk_index/chunk_total metadata를 부여해
    원래 같은 조문이었음을 추적할 수 있게 한다.
"""

import re

from langchain_core.documents import Document

# langchain 최신 버전(1.x)은 RecursiveCharacterTextSplitter가
# langchain_text_splitters 패키지로 분리되었고, 구버전은 langchain.text_splitter에 있다.
# 두 경우 모두 지원하기 위해 순서대로 시도한다.
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter


# 항(項) 마커: 원문자 ①②③... (유니코드 CIRCLED DIGIT 1~20)
_HANG_MARKER = re.compile(r"^\s*[①-⑳]")


def _split_into_hang(body_lines: list[str]) -> list[str]:
    """
    조 제목(헤더)을 제외한 본문 줄 리스트를, 항(項) 마커(①②③...) 경계로 묶는다.

    각 항에 딸린 호(1. 2. ...)나 마커 없는 이어지는 줄은 직전 항에 포함시킨다.
    첫 항 마커 앞에 마커 없는 줄이 있으면(단서 문장 등) 하나의 그룹으로 유지한다.

    Returns:
        list[str]: 항별로 묶인 텍스트 그룹 리스트
    """
    groups: list[list[str]] = []

    for line in body_lines:
        if _HANG_MARKER.match(line) or not groups:
            # 새 항 시작이거나 아직 그룹이 없으면 새 그룹 생성
            groups.append([line])
        else:
            # 호/이어지는 줄은 직전 항에 붙임
            groups[-1].append(line)

    return ["\n".join(group).strip() for group in groups if "\n".join(group).strip()]


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[Document]:
    """
    조문 단위 Document 리스트를 항(項) 단위로 청킹한다.

    Args:
        documents: preprocessor.py의 parse_law_to_documents/parse_multiple_laws 결과
        chunk_size: 항 하나가 이 길이를 넘으면 추가 분할한다 (기본 800자)
        chunk_overlap: 긴 항이 추가 분할될 때 청크 간 겹치는 길이 (문맥 유지용)

    Returns:
        list[Document]: 청킹된 Document 리스트.
            원본 metadata(법령명, 조문번호 등)를 그대로 유지하며,
            조문이 여러 청크로 쪼개진 경우 chunk_index/chunk_total이 부여된다.
            (항이 없어 쪼개지지 않은 조문은 chunk_index=0, chunk_total=1)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    result: list[Document] = []

    for doc in documents:
        lines = doc.page_content.split("\n")
        has_hang = any(_HANG_MARKER.match(line) for line in lines)

        # 항이 없는 조문(예: 제1조)은 이미 완결된 한 덩어리 → 그대로 청크 1개
        if not has_hang:
            result.append(
                Document(
                    page_content=doc.page_content,
                    metadata={**doc.metadata, "chunk_index": 0, "chunk_total": 1},
                )
            )
            continue

        # 항이 있는 조문: 첫 줄(조 제목)을 헤더로 두고 항별로 분할
        header = lines[0].strip()
        hang_groups = _split_into_hang(lines[1:])

        # 각 항을 헤더 프리픽스와 조립. 긴 항은 추가 분할하되 헤더는 유지.
        pieces: list[str] = []
        for hang_text in hang_groups:
            combined = f"{header}\n{hang_text}"
            if len(combined) <= chunk_size:
                pieces.append(combined)
            else:
                for sub in splitter.split_text(hang_text):
                    pieces.append(f"{header}\n{sub}")

        total = len(pieces)
        for idx, piece in enumerate(pieces):
            result.append(
                Document(
                    page_content=piece,
                    metadata={
                        **doc.metadata,
                        "chunk_index": idx,
                        "chunk_total": total,
                    },
                )
            )

    return result


if __name__ == "__main__":
    try:
        from rag.collector import fetch_law_json
        from rag.preprocessor import parse_law_to_documents
    except ImportError:
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