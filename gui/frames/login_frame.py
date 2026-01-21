"""
로그인 프레임 - 네이버 ID/PW 입력
"""

import customtkinter as ctk


class LoginFrame(ctk.CTkFrame):
    """네이버 로그인 정보 입력 프레임"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._show_password = False

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        # 헤더
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(5, 2))

        header = ctk.CTkLabel(
            header_frame,
            text="네이버 계정",
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
        self.auto_save_checkbox.pack(side="right")

        # ID 입력
        id_frame = ctk.CTkFrame(self, fg_color="transparent")
        id_frame.pack(fill="x", padx=10, pady=2)

        id_label = ctk.CTkLabel(id_frame, text="네이버 ID:", width=120, anchor="w")
        id_label.pack(side="left")

        self.id_entry = ctk.CTkEntry(id_frame, placeholder_text="아이디 입력")
        self.id_entry.pack(side="left", fill="x", expand=True)

        # PW 입력
        pw_frame = ctk.CTkFrame(self, fg_color="transparent")
        pw_frame.pack(fill="x", padx=10, pady=(2, 5))

        pw_label = ctk.CTkLabel(pw_frame, text="비밀번호:", width=120, anchor="w")
        pw_label.pack(side="left")

        self.pw_entry = ctk.CTkEntry(pw_frame, placeholder_text="비밀번호 입력", show="●")
        self.pw_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.toggle_pw_btn = ctk.CTkButton(
            pw_frame,
            text="보기",
            width=50,
            command=self._toggle_password
        )
        self.toggle_pw_btn.pack(side="right")

    def _toggle_password(self):
        """비밀번호 보기/숨기기 토글"""
        self._show_password = not self._show_password
        if self._show_password:
            self.pw_entry.configure(show="")
            self.toggle_pw_btn.configure(text="숨김")
        else:
            self.pw_entry.configure(show="●")
            self.toggle_pw_btn.configure(text="보기")

    def get_naver_id(self) -> str:
        """네이버 ID 반환"""
        return self.id_entry.get().strip()

    def get_naver_pw(self) -> str:
        """네이버 비밀번호 반환"""
        return self.pw_entry.get()

    def get_auto_save(self) -> bool:
        """자동저장 여부 반환"""
        return self.auto_save_var.get()

    def set_auto_save(self, value: bool):
        """자동저장 설정"""
        self.auto_save_var.set(value)

    def set_values(self, naver_id: str, naver_pw: str):
        """값 설정"""
        self.id_entry.delete(0, "end")
        self.id_entry.insert(0, naver_id)
        self.pw_entry.delete(0, "end")
        self.pw_entry.insert(0, naver_pw)
