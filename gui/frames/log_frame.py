"""
로그 프레임 - 실행 로그 출력
"""

import customtkinter as ctk
from datetime import datetime


class LogFrame(ctk.CTkFrame):
    """로그 출력 프레임"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        # 헤더
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))

        header = ctk.CTkLabel(
            header_frame,
            text="실행 로그",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        header.pack(side="left")

        clear_btn = ctk.CTkButton(
            header_frame,
            text="로그 지우기",
            width=80,
            height=25,
            font=ctk.CTkFont(size=11),
            command=self.clear_log
        )
        clear_btn.pack(side="right")

        # 로그 텍스트박스
        self.log_textbox = ctk.CTkTextbox(
            self,
            height=200,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=(5, 10))
        self.log_textbox.configure(state="disabled")

    def add_log(self, message: str, level: str = "info"):
        """로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 레벨에 따른 prefix
        level_prefix = {
            "info": "[INFO]",
            "warning": "[WARN]",
            "error": "[ERROR]",
            "success": "[SUCCESS]"
        }.get(level, "[INFO]")

        log_line = f"[{timestamp}] {level_prefix} {message}\n"

        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", log_line)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def clear_log(self):
        """로그 지우기"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
