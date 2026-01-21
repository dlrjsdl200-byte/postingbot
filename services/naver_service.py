"""
네이버 블로그 서비스 - 로그인 및 포스팅 (Selenium)

사용 예시:
    from services.naver_service import NaverService

    service = NaverService(headless=False)

    # 로그인
    service.login(user_id="your_id", password="your_pw")

    # 포스팅
    service.create_post(
        title="포스팅 제목",
        content="포스팅 내용",
        tags=["태그1", "태그2"]
    )

    # 종료
    service.close()
"""

import os
import time
import pyperclip
from typing import Optional, List, Callable
from dataclasses import dataclass


@dataclass
class PostResult:
    """포스팅 결과"""
    success: bool
    post_url: Optional[str] = None
    error_message: Optional[str] = None


class NaverService:
    """네이버 블로그 서비스 (Selenium 기반)"""

    # URL 상수
    NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"
    BLOG_HOME_URL = "https://blog.naver.com"
    BLOG_WRITE_URL = "https://blog.naver.com/{blog_id}?Redirect=Write"

    # 타임아웃 설정
    DEFAULT_TIMEOUT = 10
    PAGE_LOAD_WAIT = 3
    EDITOR_LOAD_WAIT = 5

    def __init__(
        self,
        headless: bool = False,
        logger: Optional[Callable] = None,
        blog_id: Optional[str] = None
    ):
        """
        Args:
            headless: 브라우저 숨김 모드
            logger: 로그 출력 함수
            blog_id: 블로그 ID (미리 알고 있는 경우)
        """
        self.headless = headless
        self.logger = logger or print
        self.driver = None
        self.blog_id = blog_id

        self._init_driver()

    def _init_driver(self):
        """Selenium WebDriver 초기화"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager

            options = Options()

            if self.headless:
                options.add_argument("--headless=new")

            # 기본 옵션
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")

            # User-Agent 설정
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )

            # 자동화 탐지 방지
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # 자동화 탐지 방지 스크립트
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    """
                }
            )

            self.logger("Chrome 브라우저 초기화 완료")

        except ImportError:
            raise NaverServiceError(
                "selenium과 webdriver-manager 패키지가 필요합니다.\n"
                "pip install selenium webdriver-manager"
            )
        except Exception as e:
            raise NaverServiceError(f"브라우저 초기화 실패: {e}")

    def login(self, user_id: str, password: str) -> bool:
        """
        네이버 로그인 (클립보드 방식)

        Args:
            user_id: 네이버 아이디
            password: 비밀번호

        Returns:
            로그인 성공 여부
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self.logger("네이버 로그인 시도 중...")

        # 네이버 ID를 블로그 ID로 사용
        if not self.blog_id:
            self.blog_id = user_id
            self.logger(f"블로그 ID 설정: {self.blog_id}")

        try:
            # 로그인 페이지 접속
            self.driver.get(self.NAVER_LOGIN_URL)
            time.sleep(self.PAGE_LOAD_WAIT)

            # ID 입력 (클립보드 방식 - 자동입력 탐지 우회)
            id_input = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "id"))
            )
            self._clipboard_paste(id_input, user_id)
            time.sleep(0.5)

            # PW 입력
            pw_input = self.driver.find_element(By.ID, "pw")
            self._clipboard_paste(pw_input, password)
            time.sleep(0.5)

            # 로그인 버튼 클릭
            login_btn = self.driver.find_element(By.ID, "log.login")
            login_btn.click()

            time.sleep(self.PAGE_LOAD_WAIT)

            # 로그인 성공 확인
            if self._is_logged_in():
                self.logger("로그인 성공")
                return True
            else:
                # 캡차나 2단계 인증 확인
                if "캡차" in self.driver.page_source or "보안" in self.driver.page_source:
                    self.logger("보안 인증이 필요합니다. 브라우저에서 직접 완료해주세요.")
                    input("인증 완료 후 Enter를 누르세요...")
                    if self._is_logged_in():
                        self.logger("로그인 성공")
                        return True

                raise NaverServiceError("로그인 실패: ID/PW를 확인해주세요")

        except NaverServiceError:
            raise
        except Exception as e:
            raise NaverServiceError(f"로그인 중 오류: {e}")

    def _clipboard_paste(self, element, text: str):
        """클립보드를 이용한 텍스트 입력 (자동입력 탐지 우회)"""
        from selenium.webdriver.common.keys import Keys

        # 클립보드에 복사
        pyperclip.copy(text)

        # 요소 클릭 후 붙여넣기
        element.click()
        time.sleep(0.1)
        element.send_keys(Keys.CONTROL, 'v')
        time.sleep(0.1)

    def _is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        try:
            current_url = self.driver.current_url

            if "nidlogin" in current_url:
                return False

            cookies = self.driver.get_cookies()
            cookie_names = [c['name'] for c in cookies]

            return 'NID_AUT' in cookie_names or 'NID_SES' in cookie_names

        except Exception:
            return False

    def create_post(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        images: Optional[List[str]] = None
    ) -> PostResult:
        """
        블로그 포스트 작성

        Args:
            title: 제목
            content: 내용 (HTML 또는 텍스트)
            tags: 태그 리스트
            category: 카테고리
            images: 이미지 파일 경로 리스트

        Returns:
            PostResult 객체
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self.logger("블로그 포스트 작성 중...")

        try:
            if not self.blog_id:
                raise NaverServiceError("블로그 ID를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")

            # 글쓰기 페이지로 이동
            write_url = self.BLOG_WRITE_URL.format(blog_id=self.blog_id)
            self.logger(f"글쓰기 페이지 이동: {write_url}")
            self.driver.get(write_url)
            time.sleep(self.PAGE_LOAD_WAIT)

            # 에디터 iframe으로 전환
            self._switch_to_editor()

            # 제목 입력
            self._input_title(title)

            # 이미지 업로드 (있는 경우)
            if images:
                for img_path in images:
                    self._upload_image(img_path)

            # 본문 입력
            self._input_content(content)

            # iframe에서 나오기 (발행 버튼은 iframe 바깥에 있음)
            self.driver.switch_to.default_content()
            self.logger("iframe에서 나옴")
            time.sleep(1)

            # 태그 입력 (iframe 바깥)
            if tags:
                self._input_tags(tags)

            # 발행
            post_url = self._publish_post()

            self.logger(f"포스팅 완료: {post_url}")

            return PostResult(
                success=True,
                post_url=post_url
            )

        except Exception as e:
            return PostResult(
                success=False,
                error_message=str(e)
            )

    def _switch_to_editor(self):
        """에디터 iframe으로 전환"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # 기본 프레임으로 초기화
        self.driver.switch_to.default_content()
        time.sleep(0.5)

        # iframe 전환 시도
        iframe_selectors = [
            (By.ID, "mainFrame"),
            (By.NAME, "mainFrame"),
            (By.CSS_SELECTOR, "iframe#mainFrame"),
            (By.CSS_SELECTOR, "iframe[name='mainFrame']"),
        ]

        for by, selector in iframe_selectors:
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.frame_to_be_available_and_switch_to_it((by, selector))
                )
                self.logger("에디터 iframe 전환 완료")
                time.sleep(self.EDITOR_LOAD_WAIT)
                return
            except Exception:
                continue

        self.logger("iframe 없이 직접 에디터 접근")

    def _input_title(self, title: str):
        """제목 입력"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            selectors = [
                (By.CSS_SELECTOR, "div.se-section-documentTitle p.se-text-paragraph"),
                (By.CSS_SELECTOR, ".se-documentTitle .se-text-paragraph"),
                (By.CSS_SELECTOR, "p.se-text-paragraph.se-text-paragraph-align-left"),
                (By.XPATH, "//div[contains(@class, 'se-section-documentTitle')]//p"),
            ]

            title_elem = None
            for by, selector in selectors:
                try:
                    title_elem = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    if title_elem and title_elem.is_displayed():
                        self.logger(f"제목 입력란 발견: {selector}")
                        break
                    title_elem = None
                except Exception:
                    continue

            if title_elem:
                # 요소 클릭
                title_elem.click()
                time.sleep(0.3)

                # Ctrl+A로 전체 선택
                title_elem.send_keys(Keys.CONTROL, 'a')
                time.sleep(0.1)

                # 클립보드에 복사 후 붙여넣기
                pyperclip.copy(title)
                title_elem.send_keys(Keys.CONTROL, 'v')
                time.sleep(0.3)

                self.logger(f"제목 입력 완료: {title}")
            else:
                self.logger("제목 입력란을 찾을 수 없습니다. 현재 URL: " + self.driver.current_url)
                raise NaverServiceError("제목 입력란을 찾을 수 없습니다")

        except NaverServiceError:
            raise
        except Exception as e:
            raise NaverServiceError(f"제목 입력 실패: {e}")

    def _input_content(self, content: str):
        """본문 입력"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            selectors = [
                (By.CSS_SELECTOR, "div[data-a11y-title='본문'] p.se-text-paragraph"),
                (By.CSS_SELECTOR, "div.se-component.se-text p.se-text-paragraph"),
                (By.CSS_SELECTOR, ".se-main-container p.se-text-paragraph"),
                (By.XPATH, "//div[@data-a11y-title='본문']//p"),
            ]

            content_elem = None
            for by, selector in selectors:
                try:
                    content_elem = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    if content_elem and content_elem.is_displayed():
                        self.logger(f"본문 입력란 발견: {selector}")
                        break
                    content_elem = None
                except Exception:
                    continue

            if content_elem:
                # 요소 클릭
                content_elem.click()
                time.sleep(0.3)

                # Ctrl+A로 전체 선택
                content_elem.send_keys(Keys.CONTROL, 'a')
                time.sleep(0.1)

                # 클립보드에 복사 후 붙여넣기
                pyperclip.copy(content)
                content_elem.send_keys(Keys.CONTROL, 'v')
                time.sleep(0.3)

                self.logger("본문 입력 완료")
            else:
                raise NaverServiceError("본문 입력란을 찾을 수 없습니다")

        except NaverServiceError:
            raise
        except Exception as e:
            raise NaverServiceError(f"본문 입력 실패: {e}")

    def _upload_image(self, image_path: str):
        """이미지 업로드"""
        from selenium.webdriver.common.by import By

        if not os.path.exists(image_path):
            self.logger(f"이미지 파일 없음: {image_path}")
            return

        try:
            img_btn = self.driver.find_element(
                By.CSS_SELECTOR, "[data-name='image']"
            )
            img_btn.click()
            time.sleep(1)

            file_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[type='file']"
            )
            file_input.send_keys(os.path.abspath(image_path))

            time.sleep(3)
            self.logger(f"이미지 업로드 완료: {image_path}")

        except Exception as e:
            self.logger(f"이미지 업로드 실패: {e}")

    def _input_tags(self, tags: List[str]):
        """태그 입력 (iframe 바깥에서 실행)"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            selectors = [
                (By.CSS_SELECTOR, "input[placeholder*='태그']"),
                (By.XPATH, "//input[contains(@placeholder, '태그')]"),
            ]

            tag_input = None
            for by, selector in selectors:
                try:
                    tag_input = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    if tag_input:
                        self.logger(f"태그 입력란 발견: {selector}")
                        break
                except Exception:
                    continue

            if tag_input:
                for tag in tags[:10]:
                    tag_input.send_keys(tag)
                    tag_input.send_keys(Keys.ENTER)
                    time.sleep(0.2)

                self.logger(f"태그 입력 완료: {', '.join(tags)}")
            else:
                self.logger("태그 입력란을 찾을 수 없습니다 (무시)")

        except Exception as e:
            self.logger(f"태그 입력 실패 (무시): {e}")

    def _publish_post(self) -> Optional[str]:
        """포스트 발행 (iframe 바깥에서 실행)"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            selectors = [
                (By.CSS_SELECTOR, "button[data-click-area='tpb.publish']"),
                (By.CSS_SELECTOR, "button[class*='publish_btn']"),
                (By.XPATH, "//button[contains(text(), '발행')]"),
            ]

            publish_btn = None
            for by, selector in selectors:
                try:
                    publish_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    if publish_btn:
                        self.logger(f"발행 버튼 발견: {selector}")
                        break
                except Exception:
                    continue

            if publish_btn:
                publish_btn.click()
                self.logger("발행 버튼 클릭")
                time.sleep(2)

                # 발행 확인 팝업 처리
                confirm_selectors = [
                    (By.CSS_SELECTOR, "button[data-click-area='pup.confirm']"),
                    (By.XPATH, "//button[contains(text(), '확인')]"),
                ]

                for by, selector in confirm_selectors:
                    try:
                        confirm_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        if confirm_btn:
                            confirm_btn.click()
                            self.logger("발행 확인 버튼 클릭")
                            time.sleep(2)
                            break
                    except Exception:
                        continue

                time.sleep(2)
                return self.driver.current_url

            raise NaverServiceError("발행 버튼을 찾을 수 없습니다")

        except NaverServiceError:
            raise
        except Exception as e:
            raise NaverServiceError(f"발행 실패: {e}")

    def get_recent_posts(self, count: int = 10) -> List[dict]:
        """최근 포스트 목록 가져오기"""
        return []

    def close(self):
        """브라우저 종료"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger("브라우저 종료")
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class NaverServiceError(Exception):
    """네이버 서비스 예외"""
    pass


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== NaverService 모듈 테스트 ===\n")
    print("주의: 이 테스트는 실제 네이버 로그인을 시도합니다.\n")

    print("테스트 옵션:")
    print("1. 브라우저 초기화만 테스트")
    print("2. 로그인 테스트 (ID/PW 필요)")
    print("3. 전체 포스팅 테스트")

    choice = input("\n선택 (1/2/3): ").strip()

    if choice == "1":
        print("\n브라우저 초기화 테스트...")
        try:
            service = NaverService(headless=False)
            print("브라우저 초기화 성공")
            time.sleep(2)
            service.close()
            print("테스트 완료")
        except NaverServiceError as e:
            print(f"오류: {e}")

    elif choice == "2":
        print("\n로그인 테스트...")
        naver_id = input("네이버 ID: ").strip()
        naver_pw = input("네이버 PW: ").strip()

        if not naver_id or not naver_pw:
            print("ID와 PW가 필요합니다.")
        else:
            try:
                with NaverService(headless=False) as service:
                    result = service.login(naver_id, naver_pw)
                    print(f"로그인 결과: {'성공' if result else '실패'}")
                    if result:
                        print(f"블로그 ID: {service.blog_id}")
                    input("Enter를 누르면 종료합니다...")
            except NaverServiceError as e:
                print(f"오류: {e}")

    elif choice == "3":
        print("\n전체 포스팅 테스트...")
        naver_id = input("네이버 ID: ").strip()
        naver_pw = input("네이버 PW: ").strip()

        if not naver_id or not naver_pw:
            print("ID와 PW가 필요합니다.")
        else:
            try:
                with NaverService(headless=False) as service:
                    if service.login(naver_id, naver_pw):
                        result = service.create_post(
                            title="[테스트] 자동 포스팅 테스트",
                            content="이 글은 NaverBlogPoster 테스트로 작성되었습니다.\n\n삭제해주세요.",
                            tags=["테스트", "자동포스팅"]
                        )

                        if result.success:
                            print(f"포스팅 성공: {result.post_url}")
                        else:
                            print(f"포스팅 실패: {result.error_message}")

                    input("Enter를 누르면 종료합니다...")

            except NaverServiceError as e:
                print(f"오류: {e}")

    else:
        print("\n모듈 구조 확인:")
        print("- NaverService 클래스: 정의됨")
        print("- PostResult 데이터클래스: 정의됨")
        print("- NaverServiceError 예외: 정의됨")
        print("- 주요 메서드: login, create_post, close")
