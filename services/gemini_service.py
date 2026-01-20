"""
Gemini API 서비스 - 블로그 콘텐츠 생성

사용 예시:
    from services.gemini_service import GeminiService

    service = GeminiService(api_key="YOUR_API_KEY")

    # 블로그 글 생성
    content = service.generate_blog_post(
        topic="파이썬 자동화",
        category="IT/테크",
        keywords=["파이썬", "업무 자동화", "효율"],
        use_emoji=True
    )
"""

import time
from typing import Optional, List, Callable
from dataclasses import dataclass


@dataclass
class BlogContent:
    """블로그 콘텐츠 데이터"""
    title: str
    content: str
    tags: List[str]
    summary: str


class GeminiService:
    """Google Gemini API 래퍼"""

    # Rate limiting 설정
    RATE_LIMIT_DELAY = 4  # 요청 간 최소 대기 시간 (초)
    MAX_RETRIES = 3

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash",
        logger: Optional[Callable] = None
    ):
        """
        Args:
            api_key: Gemini API 키
            model_name: 사용할 모델명
            logger: 로그 출력 함수
        """
        self.api_key = api_key
        self.model_name = model_name
        self.logger = logger or print
        self._model = None
        self._last_request_time = 0

        self._init_client()

    def _init_client(self):
        """Gemini 클라이언트 초기화"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
            self.logger("Gemini API 클라이언트 초기화 완료")

        except ImportError:
            raise GeminiServiceError(
                "google-generativeai 패키지가 필요합니다. "
                "pip install google-generativeai"
            )
        except Exception as e:
            raise GeminiServiceError(f"Gemini 초기화 실패: {e}")

    def _rate_limit(self):
        """Rate limiting 적용"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _generate(self, prompt: str, retry: int = 0) -> str:
        """
        텍스트 생성 (재시도 로직 포함)

        Args:
            prompt: 프롬프트
            retry: 현재 재시도 횟수

        Returns:
            생성된 텍스트
        """
        try:
            self._rate_limit()
            response = self._model.generate_content(prompt)
            return response.text

        except Exception as e:
            if retry < self.MAX_RETRIES:
                self.logger(f"Gemini API 오류, 재시도 중... ({retry + 1}/{self.MAX_RETRIES})")
                time.sleep(2 ** retry)  # 지수 백오프
                return self._generate(prompt, retry + 1)
            raise GeminiServiceError(f"텍스트 생성 실패: {e}")

    def generate_blog_post(
        self,
        topic: str,
        category: str = "",
        keywords: Optional[List[str]] = None,
        use_emoji: bool = True,
        min_length: int = 1500,
        max_length: int = 3000
    ) -> BlogContent:
        """
        블로그 포스트 생성

        Args:
            topic: 주제
            category: 카테고리
            keywords: 키워드 리스트
            use_emoji: 이모지 사용 여부
            min_length: 최소 글자 수
            max_length: 최대 글자 수

        Returns:
            BlogContent 객체
        """
        keywords_str = ", ".join(keywords) if keywords else topic
        emoji_instruction = "이모지를 적절히 사용해서" if use_emoji else "이모지 없이"

        prompt = f"""당신은 네이버 블로그 전문 작가입니다.
다음 조건에 맞는 블로그 글을 작성해주세요:

[주제] {topic}
[카테고리] {category}
[키워드] {keywords_str}

[작성 조건]
1. {emoji_instruction} 친근하고 읽기 쉬운 문체로 작성
2. 글 길이: {min_length}~{max_length}자
3. 서론, 본론, 결론 구조로 작성
4. 소제목(##)을 3-5개 사용하여 가독성 높이기
5. 실용적인 정보와 팁 포함
6. 독자가 공감할 수 있는 경험담이나 예시 포함
7. 마지막에 독자 참여를 유도하는 질문 추가

[출력 형식]
제목: (흥미로운 제목)

(본문 내용)

태그: (쉼표로 구분된 5-7개 태그)
"""

        self.logger(f"블로그 글 생성 중: {topic}")
        response = self._generate(prompt)

        # 응답 파싱
        return self._parse_blog_response(response, topic)

    def _parse_blog_response(self, response: str, default_topic: str) -> BlogContent:
        """블로그 응답 파싱"""
        lines = response.strip().split('\n')

        title = default_topic
        content_lines = []
        tags = []
        in_content = False

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith('제목:'):
                title = line_stripped[3:].strip()
            elif line_stripped.startswith('태그:'):
                tags_str = line_stripped[3:].strip()
                tags = [t.strip().replace('#', '') for t in tags_str.split(',')]
            elif line_stripped == '':
                if in_content:
                    content_lines.append('')
            else:
                if not line_stripped.startswith('제목:'):
                    in_content = True
                    content_lines.append(line)

        content = '\n'.join(content_lines).strip()

        # 태그가 없으면 기본 태그 생성
        if not tags:
            tags = [default_topic]

        # 요약 생성
        summary = content[:200] + "..." if len(content) > 200 else content

        return BlogContent(
            title=title,
            content=content,
            tags=tags,
            summary=summary
        )

    def generate_title_suggestions(
        self,
        topic: str,
        count: int = 5
    ) -> List[str]:
        """
        제목 제안 생성

        Args:
            topic: 주제
            count: 생성할 제목 수

        Returns:
            제목 리스트
        """
        prompt = f"""다음 주제에 대한 네이버 블로그 제목을 {count}개 제안해주세요.
클릭을 유도하는 매력적인 제목으로 작성해주세요.

주제: {topic}

형식: 번호. 제목
"""
        self.logger(f"제목 제안 생성 중: {topic}")
        response = self._generate(prompt)

        titles = []
        for line in response.split('\n'):
            line = line.strip()
            if line and line[0].isdigit():
                # "1. 제목" 형식에서 제목만 추출
                parts = line.split('.', 1)
                if len(parts) > 1:
                    titles.append(parts[1].strip())

        return titles[:count]

    def generate_image_prompt(
        self,
        topic: str,
        style: str = "modern, clean, professional"
    ) -> str:
        """
        이미지 생성용 프롬프트 생성

        Args:
            topic: 주제
            style: 이미지 스타일

        Returns:
            영문 이미지 프롬프트
        """
        prompt = f"""Create an English image generation prompt for the following topic.
The prompt should describe a visually appealing blog header image.

Topic: {topic}
Style: {style}

Requirements:
- Write in English only
- Be descriptive but concise (under 100 words)
- Focus on visual elements, colors, and composition
- No text or words in the image
- Professional blog quality

Output only the prompt, nothing else."""

        self.logger(f"이미지 프롬프트 생성 중: {topic}")
        return self._generate(prompt).strip()

    def improve_content(
        self,
        content: str,
        instruction: str = "더 자연스럽고 읽기 쉽게"
    ) -> str:
        """
        콘텐츠 개선

        Args:
            content: 원본 콘텐츠
            instruction: 개선 지시사항

        Returns:
            개선된 콘텐츠
        """
        prompt = f"""다음 블로그 글을 개선해주세요.

[개선 방향]
{instruction}

[원본 글]
{content}

[출력]
개선된 글만 출력 (설명 없이)"""

        self.logger("콘텐츠 개선 중...")
        return self._generate(prompt)

    def test_connection(self) -> bool:
        """
        API 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            response = self._generate("Say 'OK' if you can hear me.")
            return 'OK' in response.upper()
        except Exception:
            return False


class GeminiServiceError(Exception):
    """Gemini 서비스 예외"""
    pass


# 독립 실행 테스트
if __name__ == "__main__":
    import os

    print("=== GeminiService 모듈 테스트 ===\n")

    # API 키 확인
    api_key = os.environ.get('GEMINI_API_KEY', '')

    if not api_key:
        print("테스트를 위해 GEMINI_API_KEY 환경변수를 설정하세요.")
        print("또는 아래 코드에서 직접 API 키를 입력하세요.\n")

        # 직접 입력 테스트용
        api_key = input("Gemini API Key 입력 (Enter로 스킵): ").strip()

        if not api_key:
            print("\nAPI 키 없이 모듈 구조만 테스트합니다.")
            print("- GeminiService 클래스: 정의됨")
            print("- BlogContent 데이터클래스: 정의됨")
            print("- GeminiServiceError 예외: 정의됨")
            exit(0)

    try:
        service = GeminiService(api_key=api_key)

        # 1. 연결 테스트
        print("1. API 연결 테스트")
        connected = service.test_connection()
        print(f"   결과: {'성공' if connected else '실패'}\n")

        if not connected:
            print("API 연결 실패. 키를 확인해주세요.")
            exit(1)

        # 2. 제목 제안 테스트
        print("2. 제목 제안 테스트")
        titles = service.generate_title_suggestions("파이썬 자동화", count=3)
        for i, title in enumerate(titles, 1):
            print(f"   {i}. {title}")
        print()

        # 3. 이미지 프롬프트 테스트
        print("3. 이미지 프롬프트 생성 테스트")
        image_prompt = service.generate_image_prompt("파이썬 자동화")
        print(f"   프롬프트: {image_prompt[:100]}...\n")

        # 4. 블로그 글 생성 테스트 (시간이 걸림)
        print("4. 블로그 글 생성 테스트 (시간 소요)")
        blog = service.generate_blog_post(
            topic="파이썬으로 업무 자동화하기",
            category="IT/테크",
            keywords=["파이썬", "자동화", "업무효율"],
            use_emoji=True
        )
        print(f"   제목: {blog.title}")
        print(f"   태그: {', '.join(blog.tags)}")
        print(f"   글 길이: {len(blog.content)}자")
        print(f"   미리보기: {blog.summary[:100]}...\n")

        print("=== 모든 테스트 완료 ===")

    except GeminiServiceError as e:
        print(f"Gemini 서비스 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
