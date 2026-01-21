"""
네이버 블로그 서비스 - 로그인 및 포스팅 (Selenium)
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

    NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"
    BLOG_WRITE_URL = "https://blog.naver.com/{blog_id}?Redirect=Write"

    DEFAULT_TIMEOUT = 10
    PAGE_LOAD_WAIT = 3
    EDITOR_LOAD_WAIT = 5

    def __init__(
        self,
        headless: bool = False,
        logger: Optional[Callable] = None,
        blog_id: Optional[str] = None
    ):
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

            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
            )
            self.logger("Chrome 브라우저 초기화 완료")

        except ImportError:
            raise NaverServiceError("selenium과 webdriver-manager 패키지가 필요합니다.")
        except Exception as e:
            raise NaverServiceError(f"브라우저 초기화 실패: {e}")

    def login(self, user_id: str, password: str) -> bool:
        """네이버 로그인"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self.logger("네이버 로그인 시도 중...")
        if not self.blog_id:
            self.blog_id = user_id

        try:
            self.driver.get(self.NAVER_LOGIN_URL)
            time.sleep(self.PAGE_LOAD_WAIT)

            # ID 입력
            id_input = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "id"))
            )
            pyperclip.copy(user_id)
            id_input.click()
            id_input.send_keys(Keys.CONTROL, 'v')
            time.sleep(0.5)

            # PW 입력
            pw_input = self.driver.find_element(By.ID, "pw")
            pyperclip.copy(password)
            pw_input.click()
            pw_input.send_keys(Keys.CONTROL, 'v')
            time.sleep(0.5)

            # 로그인 버튼 클릭
            self.driver.find_element(By.ID, "log.login").click()
            time.sleep(self.PAGE_LOAD_WAIT)

            # 로그인 확인
            if self._is_logged_in():
                self.logger("로그인 성공")
                return True
            else:
                raise NaverServiceError("로그인 실패: ID/PW를 확인해주세요")

        except NaverServiceError:
            raise
        except Exception as e:
            raise NaverServiceError(f"로그인 중 오류: {e}")

    def _is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        try:
            if "nidlogin" in self.driver.current_url:
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
        images: Optional[List[str]] = None
    ) -> PostResult:
        """블로그 포스트 작성"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self.logger("블로그 포스트 작성 중...")

        try:
            if not self.blog_id:
                raise NaverServiceError("블로그 ID가 없습니다.")

            # 글쓰기 페이지로 이동
            write_url = self.BLOG_WRITE_URL.format(blog_id=self.blog_id)
            self.logger(f"글쓰기 페이지 이동: {write_url}")
            self.driver.get(write_url)
            time.sleep(self.PAGE_LOAD_WAIT)

            # iframe 전환
            self._switch_to_editor()

            # ★ 핵심: 제목을 먼저 입력! (순서 변경)
            self._input_title(title)
            time.sleep(1)
            
            # 본문 입력
            self._input_content(content)
            time.sleep(1)

            # 발행
            post_url = self._publish_post()
            self.logger(f"포스팅 완료: {post_url}")

            return PostResult(success=True, post_url=post_url)

        except Exception as e:
            return PostResult(success=False, error_message=str(e))

    def _switch_to_editor(self):
        """에디터 iframe으로 전환"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self.driver.switch_to.default_content()
        time.sleep(0.5)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
            )
            self.logger("mainFrame iframe 전환 완료")
        except Exception as e:
            self.logger(f"mainFrame 전환 실패: {e}")

        time.sleep(self.EDITOR_LOAD_WAIT)

    def _input_title(self, title: str):
        """
        제목 입력 - 클릭 후 키보드 입력 (에디터 인식 가능하도록)
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        try:
            self.logger("제목 입력 시작...")
            
            # 페이지 맨 위로 스크롤
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            # 제목 영역 찾기
            title_elem = None
            
            # 방법 1: data-a11y-title="제목" 내의 p 태그
            try:
                title_div = self.driver.find_element(
                    By.CSS_SELECTOR, "div[data-a11y-title='제목']"
                )
                title_elem = title_div.find_element(
                    By.CSS_SELECTOR, "p.se-text-paragraph"
                )
                self.logger("제목 요소 발견: data-a11y-title='제목'")
            except Exception:
                pass

            # 방법 2: se-documentTitle 클래스
            if not title_elem:
                try:
                    title_elem = self.driver.find_element(
                        By.CSS_SELECTOR, "div.se-documentTitle p.se-text-paragraph"
                    )
                    self.logger("제목 요소 발견: se-documentTitle")
                except Exception:
                    pass

            if not title_elem:
                raise NaverServiceError("제목 입력란을 찾을 수 없습니다")

            # 제목 요소로 스크롤
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", title_elem
            )
            time.sleep(0.5)

            # ★ 핵심: 제목 영역 클릭하여 포커스
            title_elem.click()
            time.sleep(0.5)
            
            # 기존 텍스트 전체 선택 후 삭제
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            time.sleep(0.2)
            
            # ★ 핵심: send_keys로 직접 타이핑 (에디터가 인식함)
            actions = ActionChains(self.driver)
            actions.send_keys(title).perform()
            time.sleep(0.5)

            self.logger(f"제목 입력 완료: {title}")

        except NaverServiceError:
            raise
        except Exception as e:
            raise NaverServiceError(f"제목 입력 실패: {e}")

    def _input_content(self, content: str):
        """
        본문 입력 - 본문 영역을 정확히 클릭 후 키보드 입력
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        try:
            self.logger("본문 입력 시작...")
            
            # ★ 먼저 제목에서 포커스 해제 (ESC 키)
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)

            content_elem = None

            # 방법 1: data-a11y-title="본문" 속성으로 정확히 특정
            try:
                content_div = self.driver.find_element(
                    By.CSS_SELECTOR, "div[data-a11y-title='본문']"
                )
                content_elem = content_div.find_element(
                    By.CSS_SELECTOR, "p.se-text-paragraph"
                )
                self.logger("본문 요소 발견: data-a11y-title='본문'")
            except Exception:
                pass

            # 방법 2: se-component se-text 클래스
            if not content_elem:
                try:
                    content_elem = self.driver.find_element(
                        By.CSS_SELECTOR, "div.se-component.se-text p.se-text-paragraph"
                    )
                    self.logger("본문 요소 발견: se-component.se-text")
                except Exception:
                    pass

            if not content_elem:
                raise NaverServiceError("본문 입력란을 찾을 수 없습니다")

            # 본문 요소로 스크롤
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", content_elem
            )
            time.sleep(0.5)

            # ★ 핵심: 본문 영역 클릭하여 포커스 이동
            content_elem.click()
            time.sleep(0.5)
            
            # 기존 텍스트 전체 선택 후 삭제 (placeholder 제거)
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            time.sleep(0.2)
            
            # ★ 핵심: send_keys로 직접 타이핑
            actions = ActionChains(self.driver)
            actions.send_keys(content).perform()
            time.sleep(0.5)

            self.logger("본문 입력 완료")

        except NaverServiceError:
            raise
        except Exception as e:
            raise NaverServiceError(f"본문 입력 실패: {e}")

    def _publish_post(self) -> Optional[str]:
        """포스트 발행"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            self.logger("발행 버튼 찾는 중...")

            # 발행 버튼 선택자들
            selectors = [
                "button[data-click-area='tpb.publish']",
                "button[class*='publish_btn']",
                "button.publish_btn__m9KHH",
            ]

            publish_btn = None
            for selector in selectors:
                try:
                    publish_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if publish_btn:
                        self.logger(f"발행 버튼 발견: {selector}")
                        break
                except Exception:
                    continue

            if not publish_btn:
                raise NaverServiceError("발행 버튼을 찾을 수 없습니다")

            # 발행 버튼 클릭
            self.driver.execute_script("arguments[0].click();", publish_btn)
            self.logger("발행 버튼 클릭")
            time.sleep(3)

            # 두 번째 발행 확인 버튼 찾기
            confirm_selectors = [
                "button[data-testid='seOnePublishBtn']",
                "button[class*='confirm_btn']",
                "button.confirm_btn__WEaBq",
            ]

            for selector in confirm_selectors:
                try:
                    confirm_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if confirm_btn:
                        self.driver.execute_script("arguments[0].click();", confirm_btn)
                        self.logger("발행 확인 버튼 클릭")
                        break
                except Exception:
                    continue

            time.sleep(5)
            self.driver.switch_to.default_content()
            return self.driver.current_url

        except NaverServiceError:
            raise
        except Exception as e:
            raise NaverServiceError(f"발행 실패: {e}")

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


# 테스트
if __name__ == "__main__":
    print("=== NaverService 테스트 ===\n")
    naver_id = input("네이버 ID: ").strip()
    naver_pw = input("네이버 PW: ").strip()

    if naver_id and naver_pw:
        try:
            with NaverService(headless=False) as service:
                if service.login(naver_id, naver_pw):
                    result = service.create_post(
                        title="[테스트] 자동 포스팅",
                        content="테스트 본문입니다.\n\n삭제해주세요.",
                    )
                    if result.success:
                        print(f"성공: {result.post_url}")
                    else:
                        print(f"실패: {result.error_message}")
                input("Enter를 누르면 종료...")
        except Exception as e:
            print(f"오류: {e}")
