"""
콘텐츠 에이전트 - Gemini를 활용한 블로그 콘텐츠 생성

사용 예시:
    from agents.content_agent import ContentAgent

    agent = ContentAgent(api_key="YOUR_GEMINI_API_KEY")
    content = agent.create_blog_content(
        topic="파이썬 자동화",
        category="IT/테크",
        use_emoji=True
    )
"""

from typing import Optional, List, Callable
from dataclasses import dataclass

from services.gemini_service import GeminiService, BlogContent, GeminiServiceError


@dataclass
class GeneratedContent:
    """생성된 콘텐츠"""
    title: str
    content: str
    tags: List[str]
    summary: str
    image_prompt: str


class ContentAgent:
    """블로그 콘텐츠 생성 에이전트"""

    def __init__(
        self,
        api_key: str,
        logger: Optional[Callable] = None
    ):
        """
        Args:
            api_key: Gemini API 키
            logger: 로그 출력 함수
        """
        self.logger = logger or print
        self.gemini = GeminiService(api_key=api_key, logger=self.logger)

    def create_blog_content(
        self,
        topic: str,
        category: str = "",
        keywords: Optional[List[str]] = None,
        use_emoji: bool = True,
        min_length: int = 1500,
        max_length: int = 3000
    ) -> GeneratedContent:
        """
        블로그 콘텐츠 생성

        Args:
            topic: 주제
            category: 카테고리
            keywords: 키워드 리스트
            use_emoji: 이모지 사용 여부
            min_length: 최소 글자 수
            max_length: 최대 글자 수

        Returns:
            GeneratedContent 객체
        """
        self.logger(f"콘텐츠 생성 시작: {topic}")

        try:
            # 1. 블로그 글 생성
            blog = self.gemini.generate_blog_post(
                topic=topic,
                category=category,
                keywords=keywords,
                use_emoji=use_emoji,
                min_length=min_length,
                max_length=max_length
            )

            # 2. 이미지 프롬프트 생성
            image_prompt = self.gemini.generate_image_prompt(
                topic=topic,
                style="modern minimalist blog illustration"
            )

            self.logger(f"콘텐츠 생성 완료: {blog.title}")

            return GeneratedContent(
                title=blog.title,
                content=blog.content,
                tags=blog.tags,
                summary=blog.summary,
                image_prompt=image_prompt
            )

        except GeminiServiceError as e:
            self.logger(f"콘텐츠 생성 실패: {e}")
            raise ContentAgentError(f"콘텐츠 생성 실패: {e}")

    def generate_titles(
        self,
        topic: str,
        count: int = 5
    ) -> List[str]:
        """
        제목 후보 생성

        Args:
            topic: 주제
            count: 생성할 제목 수

        Returns:
            제목 리스트
        """
        self.logger(f"제목 후보 생성: {topic}")
        return self.gemini.generate_title_suggestions(topic, count)

    def improve_content(
        self,
        content: str,
        style: str = "more engaging"
    ) -> str:
        """
        콘텐츠 개선

        Args:
            content: 원본 콘텐츠
            style: 개선 스타일

        Returns:
            개선된 콘텐츠
        """
        instruction_map = {
            "more engaging": "더 흥미롭고 독자의 관심을 끌 수 있게",
            "more professional": "더 전문적이고 신뢰감 있게",
            "more casual": "더 친근하고 대화하듯이",
            "shorter": "핵심만 간결하게",
            "longer": "더 자세하고 풍부하게",
            "seo": "SEO에 최적화되도록 키워드를 자연스럽게 포함해서",
        }

        instruction = instruction_map.get(style, style)
        return self.gemini.improve_content(content, instruction)

    def generate_for_category(
        self,
        category: str,
        user_keywords: Optional[List[str]] = None,
        use_emoji: bool = True
    ) -> GeneratedContent:
        """
        카테고리 기반 콘텐츠 자동 생성

        Args:
            category: 카테고리
            user_keywords: 사용자 키워드
            use_emoji: 이모지 사용

        Returns:
            GeneratedContent 객체
        """
        # 카테고리별 기본 주제 설정
        category_topics = {
            "의료/약학": "건강 관리 팁",
            "IT/테크": "유용한 IT 정보",
            "여행": "추천 여행지",
            "맛집/요리": "맛집 탐방",
            "육아/교육": "육아 노하우",
            "재테크/경제": "재테크 정보",
            "뷰티/패션": "뷰티 트렌드",
            "운동/다이어트": "운동 팁",
            "반려동물": "반려동물 케어",
            "자기계발": "자기계발 방법",
        }

        # 주제 결정
        if user_keywords:
            topic = user_keywords[0]
            keywords = user_keywords
        else:
            topic = category_topics.get(category, category)
            keywords = [topic]

        return self.create_blog_content(
            topic=topic,
            category=category,
            keywords=keywords,
            use_emoji=use_emoji
        )

    def test_connection(self) -> bool:
        """API 연결 테스트"""
        return self.gemini.test_connection()


class ContentAgentError(Exception):
    """콘텐츠 에이전트 예외"""
    pass


# 독립 실행 테스트
if __name__ == "__main__":
    import os

    print("=== ContentAgent 모듈 테스트 ===\n")

    api_key = os.environ.get('GEMINI_API_KEY', '')

    if not api_key:
        api_key = input("Gemini API Key 입력 (Enter로 스킵): ").strip()

    if not api_key:
        print("\nAPI 키 없이 모듈 구조만 확인:")
        print("- ContentAgent 클래스: 정의됨")
        print("- GeneratedContent 데이터클래스: 정의됨")
        print("- 주요 메서드: create_blog_content, generate_titles, improve_content")
        exit(0)

    try:
        agent = ContentAgent(api_key=api_key)

        # 1. 연결 테스트
        print("1. API 연결 테스트")
        connected = agent.test_connection()
        print(f"   결과: {'성공' if connected else '실패'}\n")

        if not connected:
            print("API 연결 실패")
            exit(1)

        # 2. 제목 생성
        print("2. 제목 후보 생성")
        titles = agent.generate_titles("파이썬 업무 자동화", count=3)
        for i, title in enumerate(titles, 1):
            print(f"   {i}. {title}")
        print()

        # 3. 콘텐츠 생성
        print("3. 콘텐츠 생성 (시간 소요)")
        content = agent.create_blog_content(
            topic="파이썬으로 업무 자동화하기",
            category="IT/테크",
            keywords=["파이썬", "자동화", "업무효율"],
            use_emoji=True
        )
        print(f"   제목: {content.title}")
        print(f"   태그: {', '.join(content.tags)}")
        print(f"   글 길이: {len(content.content)}자")
        print(f"   이미지 프롬프트: {content.image_prompt[:50]}...\n")

        print("=== 테스트 완료 ===")

    except ContentAgentError as e:
        print(f"콘텐츠 에이전트 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
