"""
포스팅 엔진 - 전체 워크플로우 관리

워크플로우:
1. 트렌드 수집 (TrendAgent)
2. 주제 선정
3. 콘텐츠 생성 (ContentAgent + Gemini)
4. 이미지 생성 (ImageAgent + Pollinations)
5. 네이버 포스팅 (PostingAgent + Selenium)

사용 예시:
    from core.posting_engine import PostingEngine

    engine = PostingEngine(
        naver_id="your_id",
        naver_pw="your_pw",
        gemini_api_key="your_api_key",
        category="IT/테크",
        keywords="파이썬, 자동화",
        use_image=True,
        use_emoji=True,
        logger=print
    )

    result = engine.run()
"""

import time
from typing import Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum


class PostingStatus(Enum):
    """포스팅 상태"""
    PENDING = "pending"
    COLLECTING_TRENDS = "collecting_trends"
    SELECTING_TOPIC = "selecting_topic"
    GENERATING_CONTENT = "generating_content"
    GENERATING_IMAGE = "generating_image"
    POSTING = "posting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PostingProgress:
    """포스팅 진행 상황"""
    status: PostingStatus = PostingStatus.PENDING
    current_step: int = 0
    total_steps: int = 5
    message: str = ""
    topic: Optional[str] = None
    title: Optional[str] = None
    content_length: int = 0
    image_path: Optional[str] = None
    post_url: Optional[str] = None
    error: Optional[str] = None


@dataclass
class EngineResult:
    """엔진 실행 결과"""
    success: bool
    post_url: Optional[str] = None
    title: Optional[str] = None
    topic: Optional[str] = None
    content_length: int = 0
    image_path: Optional[str] = None
    error_message: Optional[str] = None
    elapsed_time: float = 0.0


class PostingEngine:
    """포스팅 메인 엔진 - 전체 워크플로우 관리"""

    def __init__(
        self,
        naver_id: str,
        naver_pw: str,
        gemini_api_key: str,
        category: str = "직접입력",
        keywords: str = "",
        use_image: bool = True,
        use_emoji: bool = True,
        headless: bool = False,
        logger: Optional[Callable] = None,
        progress_callback: Optional[Callable[[PostingProgress], None]] = None
    ):
        """
        Args:
            naver_id: 네이버 아이디
            naver_pw: 네이버 비밀번호
            gemini_api_key: Gemini API 키
            category: 주제 카테고리
            keywords: 세부 키워드 (쉼표 구분)
            use_image: 이미지 자동 생성 여부
            use_emoji: 이모지 사용 여부
            headless: 브라우저 숨김 모드
            logger: 로그 출력 함수
            progress_callback: 진행 상황 콜백
        """
        self.naver_id = naver_id
        self.naver_pw = naver_pw
        self.gemini_api_key = gemini_api_key
        self.category = category
        self.keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        self.use_image = use_image
        self.use_emoji = use_emoji
        self.headless = headless
        self.logger = logger or print
        self.progress_callback = progress_callback

        # 진행 상황
        self.progress = PostingProgress()

        # 에이전트들 (지연 초기화)
        self._trend_agent = None
        self._content_agent = None
        self._image_agent = None
        self._posting_agent = None

        # 중단 플래그
        self._stop_requested = False

    def _update_progress(
        self,
        status: PostingStatus,
        step: int,
        message: str,
        **kwargs
    ):
        """진행 상황 업데이트"""
        self.progress.status = status
        self.progress.current_step = step
        self.progress.message = message

        for key, value in kwargs.items():
            if hasattr(self.progress, key):
                setattr(self.progress, key, value)

        self.logger(f"[{step}/5] {message}")

        if self.progress_callback:
            self.progress_callback(self.progress)

    def _check_stop(self):
        """중단 요청 확인"""
        if self._stop_requested:
            raise PostingEngineError("사용자에 의해 중단됨")

    def stop(self):
        """포스팅 중단 요청"""
        self._stop_requested = True
        self.logger("포스팅 중단 요청됨...")

    def run(self) -> EngineResult:
        """
        포스팅 워크플로우 실행

        Returns:
            EngineResult 객체
        """
        start_time = time.time()
        self._stop_requested = False

        try:
            # 1단계: 트렌드 수집
            self._update_progress(
                PostingStatus.COLLECTING_TRENDS, 1,
                "트렌드 키워드 수집 중..."
            )
            self._check_stop()
            trending_keywords = self._collect_trends()

            # 2단계: 주제 선정
            self._update_progress(
                PostingStatus.SELECTING_TOPIC, 2,
                "포스팅 주제 선정 중..."
            )
            self._check_stop()
            topic = self._select_topic(trending_keywords)
            self._update_progress(
                PostingStatus.SELECTING_TOPIC, 2,
                f"주제 선정 완료: {topic}",
                topic=topic
            )

            # 3단계: 콘텐츠 생성
            self._update_progress(
                PostingStatus.GENERATING_CONTENT, 3,
                "블로그 글 작성 중... (Gemini AI)"
            )
            self._check_stop()
            content_result = self._generate_content(topic)
            self._update_progress(
                PostingStatus.GENERATING_CONTENT, 3,
                f"글 작성 완료: {content_result.title}",
                title=content_result.title,
                content_length=len(content_result.content)
            )

            # 4단계: 이미지 생성 (선택)
            image_path = None
            if self.use_image:
                self._update_progress(
                    PostingStatus.GENERATING_IMAGE, 4,
                    "이미지 생성 중... (Pollinations AI)"
                )
                self._check_stop()
                image_path = self._generate_image(topic, content_result.image_prompt)
                self._update_progress(
                    PostingStatus.GENERATING_IMAGE, 4,
                    "이미지 생성 완료",
                    image_path=image_path
                )
            else:
                self._update_progress(
                    PostingStatus.GENERATING_IMAGE, 4,
                    "이미지 생성 건너뜀 (비활성화)"
                )

            # 5단계: 네이버 포스팅
            self._update_progress(
                PostingStatus.POSTING, 5,
                "네이버 블로그에 포스팅 중..."
            )
            self._check_stop()
            post_result = self._post_to_naver(
                title=content_result.title,
                content=content_result.content,
                tags=content_result.tags,
                image_path=image_path
            )

            # 완료
            elapsed = time.time() - start_time
            self._update_progress(
                PostingStatus.COMPLETED, 5,
                f"포스팅 완료! ({elapsed:.1f}초 소요)",
                post_url=post_result.post_url
            )

            return EngineResult(
                success=True,
                post_url=post_result.post_url,
                title=content_result.title,
                topic=topic,
                content_length=len(content_result.content),
                image_path=image_path,
                elapsed_time=elapsed
            )

        except PostingEngineError as e:
            elapsed = time.time() - start_time
            self._update_progress(
                PostingStatus.FAILED, self.progress.current_step,
                f"오류 발생: {e}",
                error=str(e)
            )
            return EngineResult(
                success=False,
                error_message=str(e),
                elapsed_time=elapsed,
                title=self.progress.title,
                topic=self.progress.topic
            )

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"예상치 못한 오류: {e}"
            self._update_progress(
                PostingStatus.FAILED, self.progress.current_step,
                error_msg,
                error=error_msg
            )
            return EngineResult(
                success=False,
                error_message=error_msg,
                elapsed_time=elapsed
            )

        finally:
            self._cleanup()

    def _collect_trends(self) -> List[str]:
        """트렌드 키워드 수집"""
        from agents.trend_agent import TrendAgent

        if self._trend_agent is None:
            self._trend_agent = TrendAgent(logger=self.logger)

        keywords = self._trend_agent.get_trending_keywords(
            category=self.category,
            count=10
        )

        return [kw.keyword for kw in keywords]

    def _select_topic(self, trending: List[str]) -> str:
        """주제 선정"""
        # 사용자 키워드 우선
        if self.keywords:
            return self.keywords[0]

        # 트렌드 키워드에서 선택
        if trending:
            # 카테고리와 관련된 키워드 찾기
            for kw in trending:
                if self.category != "직접입력" and self.category.split('/')[0] in kw:
                    return kw
            return trending[0]

        # 기본값
        return self.category if self.category != "직접입력" else "일상"

    def _generate_content(self, topic: str):
        """콘텐츠 생성"""
        from agents.content_agent import ContentAgent, ContentAgentError

        if self._content_agent is None:
            self._content_agent = ContentAgent(
                api_key=self.gemini_api_key,
                logger=self.logger
            )

        try:
            return self._content_agent.create_blog_content(
                topic=topic,
                category=self.category,
                keywords=self.keywords if self.keywords else [topic],
                use_emoji=self.use_emoji
            )
        except ContentAgentError as e:
            raise PostingEngineError(f"콘텐츠 생성 실패: {e}")

    def _generate_image(self, topic: str, prompt: str) -> Optional[str]:
        """이미지 생성"""
        from agents.image_agent import ImageAgent, ImageAgentError

        if self._image_agent is None:
            self._image_agent = ImageAgent(logger=self.logger)

        try:
            result = self._image_agent.create_blog_image(
                topic=topic,
                prompt=prompt,
                category=self.category,
                image_type="header"
            )
            return result.path
        except ImageAgentError as e:
            self.logger(f"이미지 생성 실패 (계속 진행): {e}")
            return None

    def _post_to_naver(
        self,
        title: str,
        content: str,
        tags: List[str],
        image_path: Optional[str]
    ):
        """네이버 블로그 포스팅"""
        from agents.posting_agent import PostingAgent, PostingAgentError

        if self._posting_agent is None:
            self._posting_agent = PostingAgent(
                headless=self.headless,
                logger=self.logger
            )

        images = [image_path] if image_path else None

        result = self._posting_agent.post(
            naver_id=self.naver_id,
            naver_pw=self.naver_pw,
            title=title,
            content=content,
            tags=tags,
            images=images
        )

        if not result.success:
            raise PostingEngineError(f"포스팅 실패: {result.error_message}")

        return result

    def _cleanup(self):
        """리소스 정리"""
        if self._posting_agent:
            try:
                self._posting_agent.close()
            except Exception:
                pass
            self._posting_agent = None

    def test_gemini_connection(self) -> bool:
        """Gemini API 연결 테스트"""
        from agents.content_agent import ContentAgent

        try:
            agent = ContentAgent(
                api_key=self.gemini_api_key,
                logger=self.logger
            )
            return agent.test_connection()
        except Exception:
            return False


class PostingEngineError(Exception):
    """포스팅 엔진 예외"""
    pass


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== PostingEngine 모듈 테스트 ===\n")
    print("이 테스트는 전체 포스팅 워크플로우를 실행합니다.\n")

    print("테스트 옵션:")
    print("1. 모듈 구조만 확인")
    print("2. Gemini 연결 테스트")
    print("3. 전체 워크플로우 테스트 (실제 포스팅)")

    choice = input("\n선택 (1/2/3): ").strip()

    if choice == "1":
        print("\n모듈 구조:")
        print("- PostingEngine 클래스")
        print("- PostingStatus 열거형")
        print("- PostingProgress 데이터클래스")
        print("- EngineResult 데이터클래스")
        print("\n워크플로우:")
        print("1. 트렌드 수집 (TrendAgent)")
        print("2. 주제 선정")
        print("3. 콘텐츠 생성 (ContentAgent)")
        print("4. 이미지 생성 (ImageAgent)")
        print("5. 네이버 포스팅 (PostingAgent)")

    elif choice == "2":
        api_key = input("Gemini API Key: ").strip()
        if api_key:
            engine = PostingEngine(
                naver_id="test",
                naver_pw="test",
                gemini_api_key=api_key,
                logger=print
            )
            result = engine.test_gemini_connection()
            print(f"Gemini 연결: {'성공' if result else '실패'}")
        else:
            print("API 키가 필요합니다.")

    elif choice == "3":
        print("\n경고: 실제 네이버 블로그에 포스팅됩니다!")
        confirm = input("계속하시겠습니까? (yes/no): ").strip().lower()

        if confirm == "yes":
            naver_id = input("네이버 ID: ").strip()
            naver_pw = input("네이버 PW: ").strip()
            api_key = input("Gemini API Key: ").strip()
            category = input("카테고리 (예: IT/테크): ").strip() or "IT/테크"
            keywords = input("키워드 (쉼표 구분): ").strip() or "테스트"

            if naver_id and naver_pw and api_key:
                def progress_callback(progress):
                    print(f"  상태: {progress.status.value} - {progress.message}")

                engine = PostingEngine(
                    naver_id=naver_id,
                    naver_pw=naver_pw,
                    gemini_api_key=api_key,
                    category=category,
                    keywords=keywords,
                    use_image=True,
                    use_emoji=True,
                    headless=False,
                    logger=print,
                    progress_callback=progress_callback
                )

                print("\n포스팅 시작...\n")
                result = engine.run()

                print("\n" + "=" * 50)
                if result.success:
                    print(f"성공!")
                    print(f"제목: {result.title}")
                    print(f"URL: {result.post_url}")
                    print(f"소요 시간: {result.elapsed_time:.1f}초")
                else:
                    print(f"실패: {result.error_message}")
            else:
                print("모든 정보가 필요합니다.")
        else:
            print("취소됨")

    else:
        print("잘못된 선택")
