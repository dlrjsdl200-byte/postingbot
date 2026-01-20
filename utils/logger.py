"""
로거 유틸리티 - GUI 로그 출력
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui.app import NaverBlogPosterApp


class Logger:
    """GUI 로그 출력 클래스"""

    def __init__(self, app: 'NaverBlogPosterApp'):
        self.app = app

    def log(self, message: str, level: str = "info"):
        """로그 출력 (메인 스레드에서 실행)"""
        # GUI 업데이트는 메인 스레드에서 해야 함
        self.app.after(0, lambda: self._log_to_gui(message, level))

    def _log_to_gui(self, message: str, level: str):
        """GUI에 로그 출력"""
        if hasattr(self.app, 'log_frame'):
            self.app.log_frame.add_log(message, level)
