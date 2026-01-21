"""
액션 프레임 - 다이나믹 버튼들
"""

import customtkinter as ctk
from agents.ui_agent import UIAgent, DynamicButton


class ActionFrame(ctk.CTkFrame):
    """액션 버튼 프레임 (다이나믹 효과 적용)"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # UI Agent 초기화
        self.ui_agent = UIAgent(app)

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        # 버튼 컨테이너
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(fill="x", padx=10, pady=5)

        # 설정 저장 버튼 (다이나믹)
        self.save_btn = DynamicButton(
            btn_container,
            ui_agent=self.ui_agent,
            button_type='save',
            text="설정 저장",
            success_text="저장 완료 ✓",
            width=120,
            height=32,
            command=self._on_save_click
        )
        self.save_btn.pack(side="left", padx=(0, 10))

        # 포스팅 실행 버튼 (다이나믹)
        self.run_btn = DynamicButton(
            btn_container,
            ui_agent=self.ui_agent,
            button_type='run',
            text="포스팅 실행",
            loading_texts=['포스팅 중.', '포스팅 중..', '포스팅 중...'],
            width=120,
            height=32,
            command=self._on_run_click
        )
        self.run_btn.pack(side="left", padx=(0, 10))

        # 중지 버튼 (다이나믹)
        self.stop_btn = DynamicButton(
            btn_container,
            ui_agent=self.ui_agent,
            button_type='stop',
            text="중지",
            width=80,
            height=32,
            state="disabled",
            command=self._on_stop_click
        )
        self.stop_btn.pack(side="left")

    def _on_save_click(self):
        """설정 저장 버튼 클릭 핸들러"""
        self.app.save_config()
        # 성공 애니메이션
        self.save_btn.show_success(duration=1500)

    def _on_run_click(self):
        """포스팅 실행 버튼 클릭 핸들러"""
        self.app.start_posting()

    def _on_stop_click(self):
        """중지 버튼 클릭 핸들러"""
        self.app.stop_posting()

    def set_running_state(self, is_running: bool):
        """실행 상태에 따른 버튼 상태 변경 (애니메이션 포함)"""
        if is_running:
            # 실행 버튼 로딩 애니메이션 시작
            self.run_btn.start_loading()
            self.run_btn.configure(state="disabled")

            # 중지 버튼 활성화 애니메이션
            self.stop_btn.animate_enable()

            # 저장 버튼 비활성화 애니메이션
            self.save_btn.animate_disable()
        else:
            # 실행 버튼 로딩 애니메이션 중지
            self.run_btn.stop_loading()
            self.run_btn.configure(state="normal")

            # 중지 버튼 비활성화 애니메이션
            self.stop_btn.animate_disable()

            # 저장 버튼 활성화 애니메이션
            self.save_btn.animate_enable()

    def shake_run_button(self):
        """실행 버튼 흔들기 (에러 시)"""
        self.run_btn.shake()
