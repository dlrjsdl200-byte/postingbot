"""
NaverBlogPoster - 메인 GUI 앱
"""

import customtkinter as ctk
from typing import Optional, List
import threading

from gui.frames import LoginFrame, CategoryFrame, ApiFrame, TopicFrame, ActionFrame, LogFrame
from core.config_manager import ConfigManager
from utils.logger import Logger


class NaverBlogPosterApp(ctk.CTk):
    """메인 앱 클래스"""

    def __init__(self):
        super().__init__()

        # 앱 설정
        self.title("NaverBlogPoster - 네이버 블로그 자동 포스팅")
        self.geometry("700x850")
        self.minsize(600, 750)

        # 테마 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 매니저 초기화
        self.config_manager = ConfigManager()
        self.logger = Logger(self)

        # 상태 변수
        self.is_running = False
        self.is_logged_in = False
        self.posting_thread: Optional[threading.Thread] = None
        self.login_thread: Optional[threading.Thread] = None
        self.naver_service = None  # 로그인 후 유지

        # UI 구성
        self._setup_ui()

        # 저장된 설정 불러오기
        self._load_saved_config()

        # 창 닫기 이벤트 바인딩 (자동저장)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 타이틀
        title_label = ctk.CTkLabel(
            self.main_container,
            text="NaverBlogPoster",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            self.main_container,
            text="네이버 블로그 자동 포스팅 도구",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 15))

        # 프레임들 생성 (순서: 로그인 → 카테고리 → API → 포스팅설정 → 액션 → 로그)
        self.login_frame = LoginFrame(self.main_container, self)
        self.login_frame.pack(fill="x", pady=(0, 10))

        self.category_frame = CategoryFrame(self.main_container, self)
        self.category_frame.pack(fill="x", pady=(0, 10))

        self.api_frame = ApiFrame(self.main_container, self)
        self.api_frame.pack(fill="x", pady=(0, 10))

        self.topic_frame = TopicFrame(self.main_container, self)
        self.topic_frame.pack(fill="x", pady=(0, 10))

        self.action_frame = ActionFrame(self.main_container, self)
        self.action_frame.pack(fill="x", pady=(0, 10))

        self.log_frame = LogFrame(self.main_container, self)
        self.log_frame.pack(fill="both", expand=True, pady=(0, 10))

        # 상태바
        self.status_bar = ctk.CTkLabel(
            self,
            text="준비됨 - 로그인 후 포스팅 가능",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))

    def _load_saved_config(self):
        """저장된 설정 불러오기"""
        config = self.config_manager.load_config()
        if config:
            self.login_frame.set_values(
                config.get('naver_id', ''),
                config.get('naver_pw', '')
            )
            self.api_frame.set_values(
                config.get('gemini_api_key', '')
            )
            self.topic_frame.set_values(
                config.get('category', '직접입력'),
                config.get('keywords', ''),
                config.get('use_image', True),
                config.get('use_emoji', True)
            )
            # 자동저장 설정 불러오기
            self.login_frame.set_auto_save(config.get('auto_save_credentials', True))
            self.api_frame.set_auto_save(config.get('auto_save_api_key', True))

            self.logger.log("저장된 설정을 불러왔습니다.")

    def _on_closing(self):
        """창 닫기 시 자동저장 및 리소스 정리"""
        self._auto_save_if_enabled()

        # NaverService 종료
        if self.naver_service:
            try:
                self.naver_service.close()
            except Exception:
                pass

        self.destroy()

    def _auto_save_if_enabled(self):
        """자동저장이 활성화되어 있으면 저장"""
        config = {
            'category': self.topic_frame.get_category(),
            'keywords': self.topic_frame.get_keywords(),
            'use_image': self.topic_frame.get_use_image(),
            'use_emoji': self.topic_frame.get_use_emoji(),
            'auto_save_credentials': self.login_frame.get_auto_save(),
            'auto_save_api_key': self.api_frame.get_auto_save()
        }

        # 네이버 계정 자동저장
        if self.login_frame.get_auto_save():
            config['naver_id'] = self.login_frame.get_naver_id()
            config['naver_pw'] = self.login_frame.get_naver_pw()
        else:
            config['naver_id'] = ''
            config['naver_pw'] = ''

        # API 키 자동저장
        if self.api_frame.get_auto_save():
            config['gemini_api_key'] = self.api_frame.get_api_key()
        else:
            config['gemini_api_key'] = ''

        self.config_manager.save_config(config)

    def save_config(self):
        """현재 설정 저장 (수동)"""
        config = {
            'naver_id': self.login_frame.get_naver_id(),
            'naver_pw': self.login_frame.get_naver_pw(),
            'gemini_api_key': self.api_frame.get_api_key(),
            'category': self.topic_frame.get_category(),
            'keywords': self.topic_frame.get_keywords(),
            'use_image': self.topic_frame.get_use_image(),
            'use_emoji': self.topic_frame.get_use_emoji(),
            'auto_save_credentials': self.login_frame.get_auto_save(),
            'auto_save_api_key': self.api_frame.get_auto_save()
        }
        self.config_manager.save_config(config)
        self.logger.log("설정이 저장되었습니다.")
        self.set_status("설정 저장 완료")

    def start_posting(self):
        """포스팅 시작"""
        if self.is_running:
            self.logger.log("이미 실행 중입니다.", "warning")
            return

        # 로그인 확인
        if not self.is_logged_in or not self.naver_service:
            self.logger.log("먼저 로그인을 해주세요.", "error")
            return

        # 카테고리 확인
        if not self.category_frame.is_ready():
            self.logger.log("카테고리를 불러와주세요.", "error")
            return

        # 필수 입력값 검증
        if not self.api_frame.get_api_key():
            self.logger.log("Gemini API Key를 입력해주세요.", "error")
            return

        # 자동저장 (포스팅 시작 전)
        self._auto_save_if_enabled()

        self.is_running = True
        self.action_frame.set_running_state(True)
        self.set_status("포스팅 실행 중...")

        # 별도 스레드에서 포스팅 실행
        self.posting_thread = threading.Thread(target=self._run_posting, daemon=True)
        self.posting_thread.start()

    def _run_posting(self):
        """포스팅 실행 (별도 스레드)"""
        try:
            from core.posting_engine import PostingEngine

            # 선택된 카테고리 정보
            selected_category = self.category_frame.get_selected_category()
            category_name = selected_category["name"] if selected_category else "전체"
            category_id = selected_category["id"] if selected_category else "0"

            engine = PostingEngine(
                naver_id=self.login_frame.get_naver_id(),
                naver_pw=self.login_frame.get_naver_pw(),
                gemini_api_key=self.api_frame.get_api_key(),
                category=self.topic_frame.get_category(),
                keywords=self.topic_frame.get_keywords(),
                use_image=self.topic_frame.get_use_image(),
                use_emoji=self.topic_frame.get_use_emoji(),
                logger=self.logger,
                naver_service=self.naver_service,  # 기존 로그인된 서비스 재사용
                blog_category_id=category_id,
                blog_category_name=category_name
            )

            engine.run()

        except Exception as e:
            self.logger.log(f"오류 발생: {str(e)}", "error")
        finally:
            self.is_running = False
            self.after(0, lambda: self.action_frame.set_running_state(False))
            self.after(0, lambda: self.set_status("로그인 완료 - 포스팅 준비됨"))

    def stop_posting(self):
        """포스팅 중지"""
        if not self.is_running:
            return

        self.is_running = False
        self.logger.log("포스팅이 중지되었습니다.", "warning")
        self.action_frame.set_running_state(False)
        self.set_status("준비됨")

    def set_status(self, text: str):
        """상태바 텍스트 설정"""
        self.status_bar.configure(text=text)

    def log(self, message: str, level: str = "info"):
        """로그 출력"""
        self.logger.log(message, level)

    def login_and_fetch_categories(self):
        """로그인 후 카테고리 불러오기"""
        if self.login_thread and self.login_thread.is_alive():
            self.logger.log("이미 로그인 중입니다.", "warning")
            return

        # 필수 입력값 검증
        if not self.login_frame.get_naver_id():
            self.logger.log("네이버 ID를 입력해주세요.", "error")
            return
        if not self.login_frame.get_naver_pw():
            self.logger.log("네이버 비밀번호를 입력해주세요.", "error")
            return

        # UI 상태 변경
        self.login_frame.set_login_button_state(False, "로그인 중...")
        self.set_status("로그인 중...")

        # 별도 스레드에서 로그인 실행
        self.login_thread = threading.Thread(target=self._run_login, daemon=True)
        self.login_thread.start()

    def _run_login(self):
        """로그인 실행 (별도 스레드)"""
        try:
            from services.naver_service import NaverService, NaverServiceError

            self.logger.log("네이버 로그인 시작...")

            # 기존 서비스가 있으면 종료
            if self.naver_service:
                try:
                    self.naver_service.close()
                except Exception:
                    pass

            # NaverService 초기화 및 로그인
            self.naver_service = NaverService(
                headless=False,
                logger=self.logger
            )

            login_success = self.naver_service.login(
                user_id=self.login_frame.get_naver_id(),
                password=self.login_frame.get_naver_pw()
            )

            if login_success:
                # 카테고리 가져오기
                self.logger.log("카테고리 불러오는 중...")
                categories = self.naver_service.get_categories()

                # UI 업데이트 (메인 스레드)
                self.after(0, lambda: self._on_login_success(categories))
            else:
                self.after(0, lambda: self._on_login_failure("로그인 실패: 아이디/비밀번호를 확인해주세요"))

        except NaverServiceError as e:
            self.after(0, lambda: self._on_login_failure(str(e)))
        except Exception as e:
            self.after(0, lambda: self._on_login_failure(f"오류 발생: {str(e)}"))

    def _on_login_success(self, categories: List[dict]):
        """로그인 성공 처리"""
        self.is_logged_in = True

        # 카테고리 설정
        self.category_frame.set_categories(categories)

        # UI 상태 업데이트
        self.login_frame.set_login_button_state(True, "✅ 로그인됨 (재로그인)")
        self.action_frame.set_posting_enabled(True)
        self.set_status("로그인 완료 - 포스팅 준비됨")

        self.logger.log(f"✅ 로그인 성공! 카테고리 {len(categories)}개 불러옴", "info")

    def _on_login_failure(self, error_message: str):
        """로그인 실패 처리"""
        self.is_logged_in = False

        # 서비스 정리
        if self.naver_service:
            try:
                self.naver_service.close()
            except Exception:
                pass
            self.naver_service = None

        # UI 상태 업데이트
        self.login_frame.set_login_button_state(True, "로그인 & 카테고리 불러오기")
        self.category_frame.reset()
        self.action_frame.set_posting_enabled(False)
        self.set_status("로그인 실패 - 다시 시도해주세요")

        self.logger.log(f"❌ {error_message}", "error")
