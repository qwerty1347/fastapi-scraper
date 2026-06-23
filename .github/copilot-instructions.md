Generate Python docstrings in Korean.

Use Google-style docstrings.

Requirements:
- Place opening triple quotes on a separate line.
- Write the summary on the line immediately after the opening triple quotes (no blank line).
- Write a short summary in Korean.
- Use Args:, Returns:, Raises: sections when applicable.
- Include parameter types in Args (format: name (type): description).
- Write all descriptions in Korean.
- Do not add unnecessary explanations.

Example:

1) Functions and Methods
def fetch_smalltable_rows(
    table_handle: smalltable.Table,
    keys: Sequence[bytes | str],
    require_all_keys: bool = False,
) -> Mapping[bytes, tuple[str, ...]]:
    """
    Smalltable 인스턴스에서 주어진 키에 해당하는 행을 조회한다.

    Args:
        table_handle (smalltable.Table): 열려 있는 Smalltable 인스턴스.
        keys (Sequence[bytes | str]): 조회할 각 행의 키 시퀀스. 문자열 키는 UTF-8로 인코딩된다.
        require_all_keys (bool): True이면 모든 키에 값이 있는 행만 반환한다. 기본값은 False.

    Returns:
        Mapping[bytes, tuple[str, ...]]: 키를 해당 행 데이터에 매핑한 딕셔너리.
            각 행은 문자열 튜플로 표현된다. keys 인자의 키가 딕셔너리에 없으면
            해당 행을 찾지 못한 것이다.

    Raises:
        IOError: Smalltable 접근 중 오류가 발생한 경우.
    """


2) Classes
class SampleClass:
    """
    클래스에 대한 한 줄 요약.

    Attributes:
        likes_spam (bool): SPAM을 좋아하는지 여부.
        eggs (int): 낳은 알의 개수.
    """

    def __init__(self, likes_spam: bool = False):
        """
        spam 선호 여부를 기준으로 인스턴스를 초기화한다.

        Args:
            likes_spam (bool): 인스턴스가 해당 선호를 갖는지 여부. 기본값은 False.
        """
        self.likes_spam = likes_spam
        self.eggs = 0

    @property
    def butter_sticks(self) -> int:
        """
        보유한 버터 스틱 개수.
        """


3) Generators
def count_up_to(limit: int) -> Iterator[int]:
    """
    0부터 limit 미만까지의 정수를 차례로 생성한다.

    Args:
        limit (int): 생성할 정수의 상한(미포함).

    Yields:
        int: 0 이상 limit 미만의 정수.

    Raises:
        ValueError: limit이 음수인 경우.
    """


4) Modules
"""
금융 뉴스 스크래핑 유틸리티 모음.

이 모듈은 외부 뉴스 사이트에 접속해 기사 목록을 수집하고
가공하는 함수들을 제공한다.

Typical usage example:

    scraper = FinanceNewsScrapService(pm)
    articles = await scraper.do_scraping()
"""
