"""
포스팅 에이전트 - 네이버 블로그 자동 포스팅

사용 예시:
    from agents.posting_agent import PostingAgent

    agent = PostingAgent(headless=False)
    result = agent.post(
        naver_id="your_id",
        naver_pw="your_pw",
        title="포스팅 제목",
        content="포스팅 내용",
        tags=["태그1", "태그2"],
        images=["path/to/image.png"]
    )
"""

from typing import Optional, List, Callable
from dataclasses import dataclass

from services.naver_service import NaverService, NaverServiceError, PostResult


@dataclass
class PostingResult:
    """포스팅 결과"""
    success: bool
    post_url: Optional[str] = None
    error_message: Optional[str] = None
    title: Optional[str] = None


class PostingAgent:
    """네이버 블로그 포스팅 에이전트"""

    def __init__(
        self,
        headless: bool = False,
        logger: Optional[Callable] = None
    ):
        """
        Args:
            headless: 브라우저 숨김 모드
            logger: 로그 출력 함수
        """
        self.headless = headless
        self.logger = logger or print
        self._naver_service: Optional[NaverService] = None
        self._logged_in = False

    def _ensure_service(self):
        """NaverService 인스턴스 확인"""
        if self._naver_service is None:
            self._naver_service = NaverService(
                headless=self.headless,
                logger=self.logger
            )

    def login(self, naver_id: str, naver_pw: str) -> bool:
        """
        네이버 로그인

        Args:
            naver_id: 네이버 아이디
            naver_pw: 비밀번호

        Returns:
            로그인 성공 여부
        """
        self._ensure_service()

        try:
            self._logged_in = self._naver_service.login(naver_id, naver_pw)
            return self._logged_in
        except NaverServiceError as e:
            self.logger(f"로그인 실패: {e}")
            self._logged_in = False
            return False

    def post(
        self,
        naver_id: str,
        naver_pw: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        images: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> PostingResult:
        """
        블로그 포스팅 (로그인부터 포스팅까지 전체 프로세스)

        Args:
            naver_id: 네이버 아이디
            naver_pw: 비밀번호
            title: 제목
            content: 내용
            tags: 태그 리스트
            images: 이미지 경로 리스트
            category: 블로그 카테고리

        Returns:
            PostingResult 객체
        """
        self.logger("포스팅 프로세스 시작...")

        try:
            # 1. 로그인
            if not self._logged_in:
                self.logger("네이버 로그인 중...")
                if not self.login(naver_id, naver_pw):
                    return PostingResult(
                        success=False,
                        error_message="로그인 실패",
                        title=title
                    )

            # 2. 포스팅
            self.logger(f"포스팅 작성 중: {title}")
            result = self._naver_service.create_post(
                title=title,
                content=content,
                tags=tags,
                category=category,
                images=images
            )

            if result.success:
                self.logger(f"포스팅 성공: {result.post_url}")
                return PostingResult(
                    success=True,
                    post_url=result.post_url,
                    title=title
                )
            else:
                return PostingResult(
                    success=False,
                    error_message=result.error_message,
                    title=title
                )

        except NaverServiceError as e:
            return PostingResult(
                success=False,
                error_message=str(e),
                title=title
            )
        except Exception as e:
            return PostingResult(
                success=False,
                error_message=f"예상치 못한 오류: {e}",
                title=title
            )

    def post_with_retry(
        self,
        naver_id: str,
        naver_pw: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        images: Optional[List[str]] = None,
        max_retries: int = 3
    ) -> PostingResult:
        """
        재시도 로직이 포함된 포스팅

        Args:
            naver_id: 네이버 아이디
            naver_pw: 비밀번호
            title: 제목
            content: 내용
            tags: 태그 리스트
            images: 이미지 경로 리스트
            max_retries: 최대 재시도 횟수

        Returns:
            PostingResult 객체
        """
        import time

        for attempt in range(max_retries):
            self.logger(f"포스팅 시도 {attempt + 1}/{max_retries}")

            result = self.post(
                naver_id=naver_id,
                naver_pw=naver_pw,
                title=title,
                content=content,
                tags=tags,
                images=images
            )

            if result.success:
                return result

            self.logger(f"시도 {attempt + 1} 실패: {result.error_message}")

            if attempt < max_retries - 1:
                # 재시도 전 대기
                wait_time = 5 * (attempt + 1)
                self.logger(f"{wait_time}초 후 재시도...")
                time.sleep(wait_time)

                # 서비스 재초기화
                self.close()
                self._naver_service = None
                self._logged_in = False

        return PostingResult(
            success=False,
            error_message=f"{max_retries}회 시도 후 실패",
            title=title
        )

    def batch_post(
        self,
        naver_id: str,
        naver_pw: str,
        posts: List[dict],
        delay: int = 60
    ) -> List[PostingResult]:
        """
        여러 포스트 일괄 등록

        Args:
            naver_id: 네이버 아이디
            naver_pw: 비밀번호
            posts: 포스트 정보 리스트 [{'title': ..., 'content': ..., 'tags': ...}, ...]
            delay: 포스트 간 대기 시간 (초)

        Returns:
            PostingResult 리스트
        """
        import time

        results = []

        # 먼저 로그인
        if not self.login(naver_id, naver_pw):
            return [PostingResult(
                success=False,
                error_message="로그인 실패"
            )]

        for i, post_data in enumerate(posts):
            self.logger(f"포스팅 {i + 1}/{len(posts)}")

            result = self.post(
                naver_id=naver_id,
                naver_pw=naver_pw,
                title=post_data.get('title', '제목 없음'),
                content=post_data.get('content', ''),
                tags=post_data.get('tags'),
                images=post_data.get('images')
            )

            results.append(result)

            # 마지막이 아니면 대기
            if i < len(posts) - 1:
                self.logger(f"{delay}초 대기 중...")
                time.sleep(delay)

        return results

    def close(self):
        """리소스 정리"""
        if self._naver_service:
            self._naver_service.close()
            self._naver_service = None
            self._logged_in = False
            self.logger("브라우저 종료")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class PostingAgentError(Exception):
    """포스팅 에이전트 예외"""
    pass


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== PostingAgent 모듈 테스트 ===\n")
    print("주의: 이 테스트는 실제 네이버 로그인과 포스팅을 시도합니다.\n")

    print("테스트 옵션:")
    print("1. 모듈 구조만 확인")
    print("2. 브라우저 초기화 테스트")
    print("3. 로그인 테스트")
    print("4. 전체 포스팅 테스트")

    choice = input("\n선택 (1/2/3/4): ").strip()

    if choice == "1":
        print("\n모듈 구조:")
        print("- PostingAgent 클래스: 정의됨")
        print("- PostingResult 데이터클래스: 정의됨")
        print("- 주요 메서드: login, post, post_with_retry, batch_post, close")

    elif choice == "2":
        print("\n브라우저 초기화 테스트...")
        try:
            with PostingAgent(headless=False) as agent:
                agent._ensure_service()
                print("브라우저 초기화 성공")
                input("Enter를 누르면 종료합니다...")
        except Exception as e:
            print(f"오류: {e}")

    elif choice == "3":
        print("\n로그인 테스트...")
        naver_id = input("네이버 ID: ").strip()
        naver_pw = input("네이버 PW: ").strip()

        if naver_id and naver_pw:
            try:
                with PostingAgent(headless=False) as agent:
                    result = agent.login(naver_id, naver_pw)
                    print(f"로그인 결과: {'성공' if result else '실패'}")
                    input("Enter를 누르면 종료합니다...")
            except Exception as e:
                print(f"오류: {e}")
        else:
            print("ID와 PW가 필요합니다.")

    elif choice == "4":
        print("\n전체 포스팅 테스트...")
        naver_id = input("네이버 ID: ").strip()
        naver_pw = input("네이버 PW: ").strip()

        if naver_id and naver_pw:
            try:
                with PostingAgent(headless=False) as agent:
                    result = agent.post(
                        naver_id=naver_id,
                        naver_pw=naver_pw,
                        title="[테스트] PostingAgent 테스트",
                        content="이 글은 PostingAgent 테스트로 작성되었습니다.\n\n테스트 후 삭제해주세요.",
                        tags=["테스트", "자동포스팅"]
                    )

                    if result.success:
                        print(f"포스팅 성공: {result.post_url}")
                    else:
                        print(f"포스팅 실패: {result.error_message}")

                    input("Enter를 누르면 종료합니다...")
            except Exception as e:
                print(f"오류: {e}")
        else:
            print("ID와 PW가 필요합니다.")

    else:
        print("잘못된 선택입니다.")
