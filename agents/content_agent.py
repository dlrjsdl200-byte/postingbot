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
        max_length: int = 3000,
        reference_content: Optional[str] = None,
        reference_title: Optional[str] = None
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
            reference_content: 참고 자료 내용
            reference_title: 참고 자료 제목

        Returns:
            GeneratedContent 객체
        """
        self.logger(f"콘텐츠 생성 시작: {topic}")

        try:
            # 참고 자료가 있는 경우 별도 프롬프트 사용
            if reference_content:
                self.logger("참고 자료 기반으로 글 작성 중...")
                blog = self._generate_with_reference(
                    topic=topic,
                    category=category,
                    keywords=keywords,
                    use_emoji=use_emoji,
                    min_length=min_length,
                    max_length=max_length,
                    reference_content=reference_content,
                    reference_title=reference_title
                )
            else:
                # 기존 방식
                blog = self.gemini.generate_blog_post(
                    topic=topic,
                    category=category,
                    keywords=keywords,
                    use_emoji=use_emoji,
                    min_length=min_length,
                    max_length=max_length
                )

            # 2. 이미지 프롬프트 생성 (API 호출 없이 템플릿 사용)
            image_prompt = self._create_image_prompt_template(topic, category)

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

    def _generate_with_reference(
        self,
        topic: str,
        category: str,
        keywords: Optional[List[str]],
        use_emoji: bool,
        min_length: int,
        max_length: int,
        reference_content: str,
        reference_title: Optional[str]
    ):
        """참고 자료 기반 콘텐츠 생성"""
        from services.gemini_service import BlogContent

        keywords_str = ", ".join(keywords) if keywords else topic
        emoji_instruction = "이모지를 적절히 사용해서" if use_emoji else "이모지 없이"

        # 참고 내용이 너무 길면 자르기
        ref_content = reference_content[:3000] if len(reference_content) > 3000 else reference_content

        prompt = f"""당신은 네이버 블로그 전문 작가입니다.
아래 참고 자료를 바탕으로 새로운 블로그 글을 작성해주세요.

[참고 자료]
제목: {reference_title or '없음'}
내용:
{ref_content}

[작성 주제] {topic}
[카테고리] {category}
[키워드] {keywords_str}

[레이아웃 규칙 - 매우 중요!]
1. 한 줄 길이: 15~22자 (한글 기준)
2. 한 문장 최대: 55자 이내
3. 문단 사이 빈 줄: 2줄
4. 소제목/소블록 사이 빈 줄: 1줄
5. 글 시작: 흥미로운 질문이나 공감 문장으로 시작
6. 각 문단은 짧은 줄들로 구성 (모바일 가독성)

[작성 조건]
1. 참고 자료의 핵심 정보를 활용하되, 완전히 새로운 글로 재구성
2. {emoji_instruction} 친근하고 읽기 쉬운 문체로 작성
3. 글 길이: {min_length}~{max_length}자
4. 서론, 본론, 결론 구조로 작성
5. 소제목(##)을 3-5개 사용하여 가독성 높이기
6. 참고 자료에 없는 추가 정보나 팁도 포함
7. 독자가 공감할 수 있는 개인적인 의견 추가
8. 마지막에 독자 참여를 유도하는 질문 추가

[중요]
- 참고 자료를 그대로 복사하지 말고, 자신만의 언어로 재해석
- 출처를 밝히지 않아도 됨 (블로그 글이므로)
- 더 풍부하고 유용한 정보 제공

[글 구조 예시]
혹시 여러분도
이런 경험 있으신가요?

저도 처음에는
정말 막막했어요.


## 첫 번째 소제목

짧은 문장으로 시작합니다.
핵심 내용을 전달해요.

부가 설명이 이어집니다.
독자가 쉽게 이해할 수 있도록요.


## 두 번째 소제목

...

[출력 형식]
제목: (참고 자료와 다른 새로운 제목)

(본문 내용 - 위 레이아웃 규칙 준수)

태그: (쉼표로 구분된 5-7개 태그)
"""

        self.logger("참고 자료 기반 글 생성 중...")
        response = self.gemini._generate(prompt)

        # 응답 파싱
        return self.gemini._parse_blog_response(response, topic)

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

    def _create_image_prompt_template(self, topic: str, category: str) -> str:
        """
        이미지 프롬프트 템플릿 생성 (API 호출 없이)

        Args:
            topic: 주제
            category: 카테고리

        Returns:
            영문 이미지 프롬프트
        """
        # 카테고리별 스타일 매핑
        category_styles = {
            "IT/테크": "modern technology, digital, futuristic, blue tones, clean design",
            "의료/약학": "medical, healthcare, clean white, professional, trust",
            "여행": "travel, adventure, scenic landscape, vibrant colors, exploration",
            "맛집/요리": "food photography, delicious, warm lighting, appetizing",
            "육아/교육": "family, children, warm, caring, soft colors, education",
            "재테크/경제": "finance, money, growth chart, professional, green tones",
            "뷰티/패션": "beauty, fashion, elegant, stylish, aesthetic",
            "운동/다이어트": "fitness, healthy lifestyle, energetic, dynamic",
            "반려동물": "cute pets, animals, warm, loving, cozy",
            "자기계발": "motivation, success, growth, inspiration, bright",
        }

        style = category_styles.get(category, "modern, clean, professional, minimalist")

        return f"Blog header image about {topic}, {style}, high quality illustration, no text, visually appealing"

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
