"""
NaverBlogPoster - 메인 GUI 앱
"""

import customtkinter as ctk
from typing import Optional
import threading

from gui.frames import LoginFrame, ApiFrame, TopicFrame, ActionFrame, LogFrame
from core.config_manager import ConfigManager
from utils.logger import Logger


class NaverBlogPosterApp(ctk.CTk):
    """메인 앱 클래스"""

    def __init__(self):
        super().__init__()

        # 앱 설정
        self.title("NaverBlogPoster - 네이버 블로그 자동 포스팅")
        self.geometry("700x800")
        self.minsize(600, 700)

        # 테마 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 매니저 초기화
        self.config_manager = ConfigManager()
        self.logger = Logger(self)

        # 상태 변수
        self.is_running = False
        self.posting_thread: Optional[threading.Thread] = None

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

        # 프레임들 생성
        self.login_frame = LoginFrame(self.main_container, self)
        self.login_frame.pack(fill="x", pady=(0, 10))

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
            text="준비됨",
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
        """창 닫기 시 자동저장"""
        self._auto_save_if_enabled()
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

        # 필수 입력값 검증
        if not self.login_frame.get_naver_id():
            self.logger.log("네이버 ID를 입력해주세요.", "error")
            return
        if not self.login_frame.get_naver_pw():
            self.logger.log("네이버 비밀번호를 입력해주세요.", "error")
            return
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

            # 참고 URL 크롤링 결과 가져오기
            crawl_result = self.topic_frame.get_crawl_result()
            reference_content = None
            reference_title = None

            if crawl_result and crawl_result.success:
                reference_content = crawl_result.content
                reference_title = crawl_result.title
                self.logger.log(f"참고 자료 사용: {reference_title}")

            engine = PostingEngine(
                naver_id=self.login_frame.get_naver_id(),
                naver_pw=self.login_frame.get_naver_pw(),
                gemini_api_key=self.api_frame.get_api_key(),
                category=self.topic_frame.get_category(),
                keywords=self.topic_frame.get_keywords(),
                use_image=self.topic_frame.get_use_image(),
                use_emoji=self.topic_frame.get_use_emoji(),
                logger=self.logger,
                reference_content=reference_content,
                reference_title=reference_title
            )

            result = engine.run()

            # 실패 시 에러 팝업 표시
            if not result.success and result.error_type:
                self.after(0, lambda: self._show_error_popup(
                    result.error_type,
                    result.error_message or "알 수 없는 오류",
                    result.retry_seconds
                ))

        except Exception as e:
            self.logger.log(f"오류 발생: {str(e)}", "error")
        finally:
            self.is_running = False
            self.after(0, lambda: self.action_frame.set_running_state(False))
            self.after(0, lambda: self.set_status("준비됨"))

    def _show_error_popup(self, error_type: str, message: str, retry_seconds: int):
        """에러 팝업 표시"""
        from gui.dialogs.error_dialog import ErrorDialog, ErrorType

        # 문자열을 ErrorType으로 변환
        type_map = {
            'api_key_invalid': ErrorType.API_KEY_INVALID,
            'quota_exceeded': ErrorType.QUOTA_EXCEEDED,
            'model_not_found': ErrorType.MODEL_NOT_FOUND,
            'network_error': ErrorType.NETWORK_ERROR,
            'unknown': ErrorType.UNKNOWN
        }

        err_type = type_map.get(error_type, ErrorType.UNKNOWN)

        # 재시도 콜백
        def on_retry():
            self.start_posting()

        ErrorDialog(
            self,
            error_type=err_type,
            message=message,
            retry_seconds=retry_seconds,
            on_retry=on_retry if retry_seconds > 0 else None
        )

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
