"""
collector.py
법제처 Open API에서 법령 원문 데이터를 가져오는 모듈.

법제처 API는 2단계 구조로 동작한다:
  1) lawSearch.do  : 법령명으로 검색 → 법령일련번호(MST) 확보
  2) lawService.do : MST로 본문(조문) 상세 조회

이 모듈은 '수집'만 담당하며, 파싱/정제는 preprocessor.py에서 처리한다.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

LAW_API_KEY = os.getenv("LAW_API_KEY")
SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
SERVICE_URL = "https://www.law.go.kr/DRF/lawService.do"


class LawApiError(Exception):
    """법제처 API 호출 관련 예외"""
    pass


def search_law_mst(law_name: str, timeout: int = 10) -> str:
    """
    법령명으로 검색하여 법령일련번호(MST)를 찾는다.
    검색 결과 중 법령명이 정확히 일치하는 항목을 우선 선택한다
    (예: "근로기준법" 검색 시 "근로기준법 시행령"이 잘못 선택되는 것 방지).

    Args:
        law_name: 검색할 법령명 (예: "근로기준법")
        timeout: 요청 타임아웃(초)

    Returns:
        str: 법령일련번호(MST)

    Raises:
        LawApiError: API 키 누락, 요청 실패, 검색 결과 없음 시
    """
    if not LAW_API_KEY:
        raise LawApiError("환경변수 LAW_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    params = {
        "OC": LAW_API_KEY,
        "target": "law",
        "query": law_name,
        "type": "JSON",
    }

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise LawApiError(f"법제처 검색 API 요청 실패: {e}") from e

    try:
        data = response.json()
    except ValueError as e:
        raise LawApiError(f"검색 결과 JSON 파싱 실패: {e}") from e

    law_list = data.get("LawSearch", {}).get("law")
    if not law_list:
        raise LawApiError(f"'{law_name}'에 대한 검색 결과가 없습니다.")

    # 결과가 1건이면 dict로 오므로 리스트로 통일
    if isinstance(law_list, dict):
        law_list = [law_list]

    # 법령명이 정확히 일치하는 항목을 우선 선택 (시행령/시행규칙 등 오매칭 방지)
    exact_match = next(
        (item for item in law_list if item.get("법령명한글") == law_name),
        None
    )
    target = exact_match or law_list[0]

    if exact_match is None:
        print(f"⚠️ '{law_name}'과 정확히 일치하는 법령이 없어 첫 번째 결과를 사용합니다: {target.get('법령명한글')}")

    mst = target.get("법령일련번호")
    if not mst:
        raise LawApiError(f"검색 결과에서 법령일련번호(MST)를 찾을 수 없습니다: {target}")

    return mst


def fetch_law_json(law_name: str, timeout: int = 10) -> dict:
    """
    법령명을 받아 검색(MST 확보) → 본문 조회까지 한 번에 수행한다.

    Args:
        law_name: 조회할 법령명 (예: "근로기준법")
        timeout: 요청 타임아웃(초)

    Returns:
        dict: 법령 본문 JSON 응답 (최상위 키는 '법령')

    Raises:
        LawApiError: 검색/조회 과정에서 실패 시
    """
    mst = search_law_mst(law_name, timeout=timeout)

    params = {
        "OC": LAW_API_KEY,
        "target": "law",
        "MST": mst,
        "type": "JSON",
    }

    print(f"🌐 법제처 서버에서 '{law_name}' 데이터를 요청하는 중...")

    try:
        response = requests.get(SERVICE_URL, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise LawApiError(f"법제처 본문 조회 API 요청 실패: {e}") from e

    try:
        data = response.json()
    except ValueError as e:
        raise LawApiError(f"본문 JSON 파싱 실패: {e}") from e

    return data


def fetch_multiple_laws(law_names: list[str], timeout: int = 10) -> dict[str, dict]:
    """
    여러 법령을 한 번에 수집할 때 사용.

    Args:
        law_names: 조회할 법령명 리스트 (예: ["근로기준법", "최저임금법"])
        timeout: 요청 타임아웃(초)

    Returns:
        dict[str, dict]: {법령명: 본문 JSON} 형태의 딕셔너리
        (개별 법령 수집 실패 시 해당 법령은 결과에서 제외되고 경고만 출력됨)
    """
    results = {}
    for name in law_names:
        try:
            results[name] = fetch_law_json(name, timeout=timeout)
        except LawApiError as e:
            print(f"⚠️ '{name}' 수집 실패: {e}")
    return results


if __name__ == "__main__":
    data = fetch_law_json("근로기준법")
    print(f"✅ 수신 완료. 조문 수: {len(data['법령']['조문']['조문단위'])}개")