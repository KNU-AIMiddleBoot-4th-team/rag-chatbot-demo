"""
preprocessor.py
collector.py가 가져온 법제처 JSON 원본을 파싱하여
조문 단위의 LangChain Document 리스트로 변환한다.

법제처 JSON 구조 (collector.py의 fetch_law_json 결과 기준):
  data["법령"]["조문"]["조문단위"] = [ {...}, {...}, ... ]

각 조문단위 항목:
  - 조문여부: "전문"(장/절 제목) 또는 "조문"(실제 조항)
  - 조문내용: 항/호가 없는 조문은 본문 전체(문자열 또는 list[str]),
      항/호가 있는 조문은 제목만 (예: "제2조(정의)")
  - 항: 없을 수도, dict 하나일 수도, list일 수도 있음
      - 항내용: 문자열 또는 list[str]로 올 수 있음
      - 호: 항과 마찬가지로 없음/dict/list 혼재
      - 호내용: 문자열 또는 list[str]로 올 수 있음
"""

from typing import Any, Union
from langchain_core.documents import Document


def _as_list(value: Union[dict, list, None]) -> list:
    """
    법제처 API는 하위 항목이 1개면 dict, 여러 개면 list로 반환한다.
    이 함수는 항상 list로 통일해서 다루기 쉽게 만든다.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _as_text(value: Any) -> str:
    """
    법제처 API는 '조문내용'/'항내용'/'호내용' 등이 문자열일 때도,
    여러 줄이 담긴 리스트(list[str])일 때도 있다. 어떤 형태로 오든
    하나의 문자열로 안전하게 합쳐준다 (리스트 중첩도 대비).
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(_as_text(v) for v in value if _as_text(v))
    return str(value).strip()


def _build_article_text(article: dict) -> str:
    """
    조문 하나(dict)를 받아 '항/호'까지 전부 합친 완전한 텍스트를 만든다.

    항/호가 없는 조문(예: 제1조)은 '조문내용'을 그대로 사용하고,
    항/호가 있는 조문(예: 제2조)은 '조문내용'(제목) + 각 항/호 내용을
    순서대로 이어붙인다.
    """
    lines = []

    base_text = _as_text(article.get("조문내용"))
    if base_text:
        lines.append(base_text)

    for hang in _as_list(article.get("항")):
        hang_text = _as_text(hang.get("항내용"))
        if hang_text:
            lines.append(hang_text)

        for ho in _as_list(hang.get("호")):
            ho_text = _as_text(ho.get("호내용"))
            if ho_text:
                lines.append(ho_text)

    return "\n".join(lines)


def parse_law_to_documents(law_name: str, raw_data: dict) -> list[Document]:
    """
    collector.py의 fetch_law_json() 결과 하나를 조문 단위 Document 리스트로 변환한다.

    Args:
        law_name: 법령명 (metadata 표기용, 예: "근로기준법")
        raw_data: fetch_law_json()이 반환한 dict (최상위 키 '법령' 포함)

    Returns:
        list[Document]: 조문 하나당 Document 하나.
            metadata: {법령명, 조문번호, 조문제목, 조문키, 소속장}
            '전문'(장/절 제목)은 Document로 만들지 않고, 이후 조문들의
            '소속장' metadata를 갱신하는 용도로만 사용한다.

    Raises:
        KeyError: 예상한 JSON 구조가 아닐 경우
    """
    try:
        article_list = raw_data["법령"]["조문"]["조문단위"]
    except (KeyError, TypeError) as e:
        raise KeyError(f"'{law_name}' 데이터에서 조문 구조를 찾을 수 없습니다: {e}") from e

    documents: list[Document] = []
    current_chapter = ""  # 가장 최근에 만난 '전문'(장/절 제목)

    for article in article_list:
        if article.get("조문여부") == "전문":
            current_chapter = _as_text(article.get("조문내용"))
            continue

        text = _build_article_text(article)
        if not text:
            continue

        doc = Document(
            page_content=text,
            metadata={
                "법령명": law_name,
                "조문번호": article.get("조문번호", ""),
                "조문제목": article.get("조문제목", ""),
                "조문키": article.get("조문키", ""),
                "소속장": current_chapter,
                "source": "법제처 Open API",
            },
        )
        documents.append(doc)

    return documents


def parse_multiple_laws(law_data_map: dict[str, dict]) -> list[Document]:
    """
    여러 법령의 원본 JSON을 한 번에 Document 리스트로 변환한다.
    (collector.py의 fetch_multiple_laws() 결과를 그대로 받을 수 있음)
    """
    all_documents: list[Document] = []
    for law_name, raw_data in law_data_map.items():
        try:
            docs = parse_law_to_documents(law_name, raw_data)
            all_documents.extend(docs)
            print(f"✅ '{law_name}' 조문 {len(docs)}개 파싱 완료")
        except KeyError as e:
            print(f"⚠️ '{law_name}' 파싱 실패: {e}")
    return all_documents


if __name__ == "__main__":
    try:
        from rag.collector import fetch_law_json
    except ImportError:
        from collector import fetch_law_json

    raw = fetch_law_json("최저임금법")
    docs = parse_law_to_documents("최저임금법", raw)

    print(f"✅ 총 {len(docs)}개 조문 Document 생성")
    print("\n--- 샘플 (제2조) ---")
    for doc in docs:
        if doc.metadata["조문번호"] == "2":
            print("metadata:", doc.metadata)
            print("content:\n", doc.page_content)
            break