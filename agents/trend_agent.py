"""
트렌드 에이전트 - 네이버 트렌드 키워드 수집

사용 예시:
    from agents.trend_agent import TrendAgent

    agent = TrendAgent()
    keywords = agent.get_trending_keywords(category="IT/테크")
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TrendKeyword:
    """트렌드 키워드 데이터"""
    keyword: str
    rank: int
    category: Optional[str] = None
    source: str = "naver"


class TrendAgent:
    """네이버 트렌드 키워드 수집 에이전트"""

    # 네이버 데이터랩 / 검색어 트렌드 관련 URL
    NAVER_SHOPPING_TREND_URL = "https://datalab.naver.com/shoppingInsight/sCategory.naver"
    NAVER_SEARCH_TREND_URL = "https://datalab.naver.com/keyword/realtimeList.naver"

    # 카테고리별 시그널 키워드
    CATEGORY_SIGNALS = {
        "의료/약학": ["건강", "영양제", "다이어트", "병원", "약국", "의사", "치료"],
        "IT/테크": ["앱", "프로그램", "AI", "코딩", "개발", "스마트폰", "노트북"],
        "여행": ["여행", "호텔", "항공", "관광", "맛집", "휴가", "펜션"],
        "맛집/요리": ["맛집", "레시피", "요리", "카페", "디저트", "배달", "음식점"],
        "육아/교육": ["육아", "교육", "학원", "공부", "아이", "유아", "학교"],
        "재테크/경제": ["주식", "투자", "부동산", "금리", "경제", "재테크", "코인"],
        "뷰티/패션": ["화장품", "패션", "옷", "뷰티", "메이크업", "스타일", "브랜드"],
        "운동/다이어트": ["운동", "헬스", "다이어트", "피트니스", "요가", "필라테스"],
        "반려동물": ["강아지", "고양이", "펫", "반려동물", "동물병원", "사료"],
        "자기계발": ["자기계발", "독서", "습관", "목표", "성공", "공부", "영어"],
    }

    def __init__(self, logger: Optional[Callable] = None):
        """
        Args:
            logger: 로그 출력 함수
        """
        self.logger = logger or print
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_trending_keywords(
        self,
        category: Optional[str] = None,
        count: int = 10
    ) -> List[TrendKeyword]:
        """
        트렌드 키워드 수집

        Args:
            category: 카테고리 필터
            count: 가져올 키워드 수

        Returns:
            TrendKeyword 리스트
        """
        self.logger("트렌드 키워드 수집 중...")

        keywords = []

        # 1. 네이버 실시간 검색어 (대체 소스들)
        keywords.extend(self._get_naver_blog_keywords())

        # 2. 카테고리 기반 키워드 추가
        if category and category in self.CATEGORY_SIGNALS:
            for signal in self.CATEGORY_SIGNALS[category][:3]:
                keywords.append(TrendKeyword(
                    keyword=signal,
                    rank=len(keywords) + 1,
                    category=category,
                    source="category_signal"
                ))

        # 3. 시즌/시기 기반 키워드
        keywords.extend(self._get_seasonal_keywords())

        # 중복 제거 및 정렬
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw.keyword not in seen:
                seen.add(kw.keyword)
                unique_keywords.append(kw)

        self.logger(f"총 {len(unique_keywords)}개 키워드 수집 완료")
        return unique_keywords[:count]

    def _get_naver_blog_keywords(self) -> List[TrendKeyword]:
        """네이버 블로그 인기 키워드 수집"""
        keywords = []

        try:
            # 네이버 블로그 메인에서 인기 키워드 추출 시도
            url = "https://section.blog.naver.com/BlogHome.naver"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 인기 글 제목에서 키워드 추출
                titles = soup.select('.title_post, .post_title, .tit')
                for i, title in enumerate(titles[:10]):
                    text = title.get_text(strip=True)
                    if text and len(text) > 2:
                        keywords.append(TrendKeyword(
                            keyword=text[:30],
                            rank=i + 1,
                            source="naver_blog"
                        ))

        except Exception as e:
            self.logger(f"네이버 블로그 키워드 수집 실패: {e}")

        return keywords

    def _get_seasonal_keywords(self) -> List[TrendKeyword]:
        """시즌/시기 기반 키워드"""
        now = datetime.now()
        month = now.month
        keywords = []

        # 월별 시즌 키워드
        seasonal_map = {
            1: ["신년", "새해", "다이어리", "계획"],
            2: ["발렌타인", "졸업", "입학준비"],
            3: ["봄", "벚꽃", "입학", "개강"],
            4: ["봄나들이", "피크닉", "꽃구경"],
            5: ["어버이날", "스승의날", "가정의달"],
            6: ["여름준비", "휴가계획", "장마"],
            7: ["휴가", "바캉스", "여름", "해수욕장"],
            8: ["피서", "여름휴가", "물놀이"],
            9: ["가을", "추석", "단풍"],
            10: ["할로윈", "가을여행", "단풍놀이"],
            11: ["수능", "블랙프라이데이", "김장"],
            12: ["크리스마스", "연말", "송년회", "겨울"],
        }

        if month in seasonal_map:
            for i, kw in enumerate(seasonal_map[month]):
                keywords.append(TrendKeyword(
                    keyword=kw,
                    rank=100 + i,
                    source="seasonal"
                ))

        return keywords

    def get_related_keywords(
        self,
        keyword: str,
        count: int = 5
    ) -> List[str]:
        """
        연관 키워드 수집

        Args:
            keyword: 기준 키워드
            count: 가져올 키워드 수

        Returns:
            연관 키워드 리스트
        """
        related = []

        try:
            # 네이버 자동완성 API 활용
            url = f"https://ac.search.naver.com/nx/ac"
            params = {
                'q': keyword,
                'con': '1',
                'frm': 'nv',
                'ans': '2',
                'r_format': 'json',
                't_koreng': '1',
                'run': '2',
                'rev': '4',
                'q_enc': 'UTF-8'
            }

            response = self.session.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    for item in data['items'][0][:count]:
                        if isinstance(item, list) and len(item) > 0:
                            related.append(item[0])

        except Exception as e:
            self.logger(f"연관 키워드 수집 실패: {e}")

        return related

    def suggest_topic(
        self,
        category: str,
        user_keywords: Optional[List[str]] = None
    ) -> str:
        """
        포스팅 주제 제안

        Args:
            category: 카테고리
            user_keywords: 사용자 지정 키워드

        Returns:
            제안된 주제
        """
        # 사용자 키워드가 있으면 우선 사용
        if user_keywords and len(user_keywords) > 0:
            return user_keywords[0]

        # 트렌드 키워드에서 선택
        trends = self.get_trending_keywords(category=category, count=5)
        if trends:
            return trends[0].keyword

        # 카테고리 시그널에서 선택
        if category in self.CATEGORY_SIGNALS:
            return self.CATEGORY_SIGNALS[category][0]

        return category


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== TrendAgent 모듈 테스트 ===\n")

    agent = TrendAgent()

    # 1. 트렌드 키워드 수집
    print("1. 전체 트렌드 키워드")
    keywords = agent.get_trending_keywords(count=10)
    for kw in keywords:
        print(f"   [{kw.rank}] {kw.keyword} ({kw.source})")
    print()

    # 2. 카테고리별 키워드
    print("2. IT/테크 카테고리 키워드")
    it_keywords = agent.get_trending_keywords(category="IT/테크", count=5)
    for kw in it_keywords:
        print(f"   [{kw.rank}] {kw.keyword}")
    print()

    # 3. 연관 키워드
    print("3. '파이썬' 연관 키워드")
    related = agent.get_related_keywords("파이썬")
    print(f"   {related}\n")

    # 4. 주제 제안
    print("4. 주제 제안")
    topic = agent.suggest_topic("IT/테크", ["자동화", "업무효율"])
    print(f"   제안 주제: {topic}\n")

    print("=== 테스트 완료 ===")
