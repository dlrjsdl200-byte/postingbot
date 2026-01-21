"""
API 프레임 - Gemini API Key 입력
"""

import customtkinter as ctk
import webbrowser


class ApiFrame(ctk.CTkFrame):
    """API 키 입력 프레임"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        # 헤더
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(5, 2))

        header = ctk.CTkLabel(
            header_frame,
            text="Gemini API",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        header.pack(side="left")

        # 자동저장 체크박스
        self.auto_save_var = ctk.BooleanVar(value=True)
        self.auto_save_checkbox = ctk.CTkCheckBox(
            header_frame,
            text="자동저장",
            variable=self.auto_save_var,
            width=80,
            checkbox_width=18,
            checkbox_height=18,
            font=ctk.CTkFont(size=12)
        )
        self.auto_save_checkbox.pack(side="right", padx=(0, 10))

        help_btn = ctk.CTkButton(
            header_frame,
            text="API 키 발급",
            width=80,
            height=25,
            font=ctk.CTkFont(size=11),
            command=self._open_api_guide
        )
        help_btn.pack(side="right")

        # 할당량 확인 버튼
        self.quota_btn = ctk.CTkButton(
            header_frame,
            text="할당량",
            width=60,
            height=25,
            font=ctk.CTkFont(size=11),
            fg_color="#6c757d",
            hover_color="#5a6268",
            command=self._show_quota_dialog
        )
        self.quota_btn.pack(side="right", padx=(0, 5))

        # API Key 입력
        key_frame = ctk.CTkFrame(self, fg_color="transparent")
        key_frame.pack(fill="x", padx=10, pady=(2, 5))

        key_label = ctk.CTkLabel(key_frame, text="API Key:", width=120, anchor="w")
        key_label.pack(side="left")

        self.api_entry = ctk.CTkEntry(
            key_frame,
            placeholder_text="Gemini API Key 입력",
            show="●"
        )
        self.api_entry.pack(side="left", fill="x", expand=True)

    def _open_api_guide(self):
        """API 키 발급 가이드 페이지 열기"""
        webbrowser.open("https://aistudio.google.com/apikey")

    def _show_quota_dialog(self):
        """할당량 확인 다이얼로그 표시"""
        api_key = self.get_api_key()
        if not api_key:
            self.app.logger.log("API 키를 먼저 입력해주세요.", "warning")
            return

        from gui.dialogs.quota_dialog import QuotaDialog
        QuotaDialog(self.app, api_key, self.app.logger.log)

    def get_api_key(self) -> str:
        """API Key 반환"""
        return self.api_entry.get().strip()

    def get_auto_save(self) -> bool:
        """자동저장 여부 반환"""
        return self.auto_save_var.get()

    def set_auto_save(self, value: bool):
        """자동저장 설정"""
        self.auto_save_var.set(value)

    def set_values(self, api_key: str):
        """값 설정"""
        self.api_entry.delete(0, "end")
        self.api_entry.insert(0, api_key)
