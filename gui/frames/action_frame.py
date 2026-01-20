"""
액션 프레임 - 버튼들
"""

import customtkinter as ctk


class ActionFrame(ctk.CTkFrame):
    """액션 버튼 프레임"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        # 버튼 컨테이너
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(fill="x", padx=15, pady=10)

        # 설정 저장 버튼
        self.save_btn = ctk.CTkButton(
            btn_container,
            text="설정 저장",
            width=150,
            height=40,
            command=self.app.save_config
        )
        self.save_btn.pack(side="left", padx=(0, 10))

        # 포스팅 실행 버튼
        self.run_btn = ctk.CTkButton(
            btn_container,
            text="포스팅 실행",
            width=150,
            height=40,
            fg_color="#28a745",
            hover_color="#218838",
            command=self.app.start_posting
        )
        self.run_btn.pack(side="left", padx=(0, 10))

        # 중지 버튼
        self.stop_btn = ctk.CTkButton(
            btn_container,
            text="중지",
            width=100,
            height=40,
            fg_color="#dc3545",
            hover_color="#c82333",
            state="disabled",
            command=self.app.stop_posting
        )
        self.stop_btn.pack(side="left")

    def set_running_state(self, is_running: bool):
        """실행 상태에 따른 버튼 상태 변경"""
        if is_running:
            self.run_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.save_btn.configure(state="disabled")
        else:
            self.run_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.save_btn.configure(state="normal")
