"""
이미지 에이전트 - Pollinations.ai를 활용한 이미지 생성

사용 예시:
    from agents.image_agent import ImageAgent

    agent = ImageAgent()
    image_path = agent.create_blog_image(
        topic="파이썬 프로그래밍",
        prompt="modern programming workspace"
    )
"""

import os
from typing import Optional, List, Callable
from dataclasses import dataclass

from services.pollinations_service import (
    PollinationsService,
    PollinationsServiceError,
    ImageResult
)


@dataclass
class BlogImage:
    """블로그 이미지 데이터"""
    path: str
    url: str
    prompt: str
    image_type: str  # header, thumbnail, content


class ImageAgent:
    """이미지 생성 에이전트"""

    # 카테고리별 이미지 스타일
    CATEGORY_STYLES = {
        "의료/약학": "medical healthcare clean professional blue white",
        "IT/테크": "technology digital modern blue purple gradient",
        "여행": "travel landscape scenic beautiful nature",
        "맛집/요리": "food delicious appetizing warm cozy restaurant",
        "육아/교육": "education children family warm friendly",
        "재테크/경제": "finance business professional green growth",
        "뷰티/패션": "beauty fashion elegant stylish pink pastel",
        "운동/다이어트": "fitness exercise healthy active energetic",
        "반려동물": "pets cute adorable warm friendly animals",
        "자기계발": "personal growth success motivation inspiring",
    }

    def __init__(
        self,
        save_dir: str = "data/images",
        logger: Optional[Callable] = None
    ):
        """
        Args:
            save_dir: 이미지 저장 디렉토리
            logger: 로그 출력 함수
        """
        self.save_dir = save_dir
        self.logger = logger or print
        self.pollinations = PollinationsService(save_dir=save_dir, logger=self.logger)

    def create_blog_image(
        self,
        topic: str,
        prompt: Optional[str] = None,
        category: Optional[str] = None,
        image_type: str = "header"
    ) -> BlogImage:
        """
        블로그 이미지 생성

        Args:
            topic: 블로그 주제
            prompt: 이미지 프롬프트 (없으면 자동 생성)
            category: 카테고리 (스타일 적용)
            image_type: 이미지 타입 (header, thumbnail, content)

        Returns:
            BlogImage 객체
        """
        self.logger(f"블로그 이미지 생성: {topic}")

        # 스타일 결정
        style = self._get_style(category)

        # 프롬프트 생성
        if not prompt:
            prompt = self._generate_prompt(topic, style)
        else:
            prompt = f"{prompt}, {style}"

        # 이미지 타입별 크기 설정
        size_config = {
            "header": (1200, 630),
            "thumbnail": (800, 800),
            "content": (1024, 768),
        }
        width, height = size_config.get(image_type, (1024, 768))

        try:
            result = self.pollinations.generate_image(
                prompt=prompt,
                width=width,
                height=height
            )

            self.logger(f"이미지 생성 완료: {result.path}")

            return BlogImage(
                path=result.path,
                url=result.url,
                prompt=prompt,
                image_type=image_type
            )

        except PollinationsServiceError as e:
            raise ImageAgentError(f"이미지 생성 실패: {e}")

    def create_header_image(
        self,
        topic: str,
        category: Optional[str] = None
    ) -> BlogImage:
        """블로그 헤더 이미지 생성"""
        return self.create_blog_image(
            topic=topic,
            category=category,
            image_type="header"
        )

    def create_thumbnail(
        self,
        topic: str,
        category: Optional[str] = None
    ) -> BlogImage:
        """썸네일 이미지 생성"""
        return self.create_blog_image(
            topic=topic,
            category=category,
            image_type="thumbnail"
        )

    def create_content_images(
        self,
        topics: List[str],
        category: Optional[str] = None
    ) -> List[BlogImage]:
        """
        여러 콘텐츠 이미지 생성

        Args:
            topics: 주제 리스트
            category: 카테고리

        Returns:
            BlogImage 리스트
        """
        images = []
        for topic in topics:
            try:
                image = self.create_blog_image(
                    topic=topic,
                    category=category,
                    image_type="content"
                )
                images.append(image)
            except ImageAgentError as e:
                self.logger(f"이미지 생성 실패 ({topic}): {e}")
                continue

        return images

    def create_from_prompt(
        self,
        prompt: str,
        image_type: str = "content"
    ) -> BlogImage:
        """
        프롬프트로 직접 이미지 생성

        Args:
            prompt: 영문 프롬프트
            image_type: 이미지 타입

        Returns:
            BlogImage 객체
        """
        return self.create_blog_image(
            topic="custom",
            prompt=prompt,
            image_type=image_type
        )

    def _get_style(self, category: Optional[str]) -> str:
        """카테고리에 맞는 스타일 반환"""
        base_style = "professional high quality blog illustration no text clean"

        if category and category in self.CATEGORY_STYLES:
            return f"{self.CATEGORY_STYLES[category]} {base_style}"

        return f"modern minimalist {base_style}"

    def _generate_prompt(self, topic: str, style: str) -> str:
        """주제와 스타일로 프롬프트 생성"""
        # 한글 주제를 영어로 간단 변환 (기본 매핑)
        topic_translations = {
            "프로그래밍": "programming coding",
            "파이썬": "python programming",
            "자동화": "automation technology",
            "여행": "travel journey",
            "맛집": "restaurant food",
            "요리": "cooking kitchen",
            "건강": "health wellness",
            "운동": "fitness exercise",
            "독서": "reading books",
            "공부": "studying learning",
        }

        english_topic = topic
        for kr, en in topic_translations.items():
            if kr in topic:
                english_topic = en
                break

        return f"{english_topic}, {style}"

    def test_connection(self) -> bool:
        """서비스 연결 테스트"""
        return self.pollinations.test_connection()

    def cleanup_old_images(self, days: int = 7) -> int:
        """오래된 이미지 정리"""
        return self.pollinations.clear_cache(older_than_days=days)


class ImageAgentError(Exception):
    """이미지 에이전트 예외"""
    pass


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== ImageAgent 모듈 테스트 ===\n")

    # 테스트용 디렉토리
    test_dir = "data/test_agent_images"

    try:
        agent = ImageAgent(save_dir=test_dir)

        # 1. 연결 테스트
        print("1. 서비스 연결 테스트")
        connected = agent.test_connection()
        print(f"   결과: {'성공' if connected else '실패'}\n")

        # 2. 헤더 이미지 생성
        print("2. 헤더 이미지 생성")
        header = agent.create_header_image(
            topic="파이썬 프로그래밍",
            category="IT/테크"
        )
        print(f"   경로: {header.path}")
        print(f"   타입: {header.image_type}")
        print(f"   프롬프트: {header.prompt[:50]}...\n")

        # 3. 썸네일 생성
        print("3. 썸네일 이미지 생성")
        thumbnail = agent.create_thumbnail(
            topic="맛집 탐방",
            category="맛집/요리"
        )
        print(f"   경로: {thumbnail.path}\n")

        # 4. 커스텀 프롬프트
        print("4. 커스텀 프롬프트 이미지")
        custom = agent.create_from_prompt(
            prompt="serene mountain landscape at golden hour, peaceful atmosphere"
        )
        print(f"   경로: {custom.path}\n")

        print("=== 테스트 완료 ===")
        print(f"\n생성된 이미지 위치: {test_dir}/")

        # 정리
        cleanup = input("\n테스트 이미지를 삭제할까요? (y/N): ").strip().lower()
        if cleanup == 'y':
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
            print("테스트 이미지 삭제 완료")

    except ImageAgentError as e:
        print(f"이미지 에이전트 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
