"""
포스팅 엔진 - 메인 포스팅 로직
"""

from typing import List, Optional


class PostingEngine:
    """포스팅 메인 엔진"""

    def __init__(
        self,
        naver_id: str,
        naver_pw: str,
        gemini_api_key: str,
        category: str,
        keywords: str,
        use_image: bool,
        use_emoji: bool,
        logger
    ):
        self.naver_id = naver_id
        self.naver_pw = naver_pw
        self.gemini_api_key = gemini_api_key
        self.category = category
        self.keywords = keywords
        self.use_image = use_image
        self.use_emoji = use_emoji
        self.logger = logger

    def run(self):
        """포스팅 실행"""
        self.logger.log("포스팅 엔진 시작...")

        try:
            # 1. 트렌드 키워드 수집
            self.logger.log("1단계: 트렌드 키워드 수집 중...")
            trending_keywords = self._collect_trends()

            # 2. 주제 선정
            self.logger.log("2단계: 주제 선정 중...")
            topic = self._select_topic(trending_keywords)

            # 3. 콘텐츠 생성
            self.logger.log("3단계: 블로그 글 작성 중...")
            content = self._generate_content(topic)

            # 4. 이미지 생성 (옵션)
            image_path = None
            if self.use_image:
                self.logger.log("4단계: 이미지 생성 중...")
                image_path = self._generate_image(topic)

            # 5. 네이버 포스팅
            self.logger.log("5단계: 네이버 블로그에 포스팅 중...")
            self._post_to_naver(topic, content, image_path)

            self.logger.log("포스팅이 완료되었습니다!", "success")

        except Exception as e:
            self.logger.log(f"포스팅 중 오류 발생: {str(e)}", "error")
            raise

    def _collect_trends(self) -> List[str]:
        """트렌드 키워드 수집"""
        # TODO: trend_agent 구현
        self.logger.log("  - 트렌드 수집 기능은 추후 구현 예정")
        return []

    def _select_topic(self, trending: List[str]) -> str:
        """주제 선정"""
        # 사용자 키워드 우선
        if self.keywords:
            keywords = [k.strip() for k in self.keywords.split(',')]
            return keywords[0] if keywords else self.category
        return self.category

    def _generate_content(self, topic: str) -> str:
        """콘텐츠 생성"""
        # TODO: content_agent 구현
        self.logger.log("  - 콘텐츠 생성 기능은 추후 구현 예정")
        return f"# {topic}\n\n테스트 콘텐츠입니다."

    def _generate_image(self, topic: str) -> Optional[str]:
        """이미지 생성"""
        # TODO: image_agent 구현
        self.logger.log("  - 이미지 생성 기능은 추후 구현 예정")
        return None

    def _post_to_naver(self, title: str, content: str, image_path: Optional[str]):
        """네이버 블로그 포스팅"""
        # TODO: posting_agent 구현
        self.logger.log("  - 네이버 포스팅 기능은 추후 구현 예정")
