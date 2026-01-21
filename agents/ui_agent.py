"""
UI Agent - UI 애니메이션 및 효과 전문 에이전트
버튼, 위젯의 다이나믹한 시각 효과를 담당
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
import threading
import time


class UIAgent:
    """UI 애니메이션 및 효과 전문 에이전트"""

    # 색상 테마
    COLORS = {
        'save': {
            'default': '#1f6aa5',
            'hover': '#144870',
            'active': '#17a2b8',
            'success': '#28a745',
            'pulse': '#4dabf7'
        },
        'run': {
            'default': '#28a745',
            'hover': '#218838',
            'active': '#20c997',
            'loading': '#ffc107',
            'pulse': '#51cf66'
        },
        'stop': {
            'default': '#dc3545',
            'hover': '#c82333',
            'active': '#ff6b6b',
            'pulse': '#ff8787'
        }
    }

    def __init__(self, root: ctk.CTk):
        """
        Args:
            root: 메인 CTk 앱 인스턴스 (after 메서드 사용을 위해)
        """
        self.root = root
        self._animation_running: Dict[int, bool] = {}

    def animate_button_click(self, button: ctk.CTkButton, button_type: str = 'save',
                            callback: Optional[Callable] = None):
        """
        버튼 클릭 시 시각적 피드백 애니메이션

        Args:
            button: 애니메이션 적용할 버튼
            button_type: 버튼 타입 ('save', 'run', 'stop')
            callback: 애니메이션 후 실행할 콜백
        """
        colors = self.COLORS.get(button_type, self.COLORS['save'])
        original_color = colors['default']
        active_color = colors['active']

        # 스케일 다운 효과 (누르는 느낌)
        original_height = button.cget("height")
        button.configure(height=int(original_height * 0.9))
        button.configure(fg_color=active_color)

        def restore():
            button.configure(height=original_height)
            button.configure(fg_color=original_color)
            if callback:
                callback()

        self.root.after(100, restore)

    def animate_success(self, button: ctk.CTkButton, button_type: str = 'save',
                       success_text: str = None, original_text: str = None,
                       duration: int = 1500):
        """
        성공 애니메이션 (체크마크 + 색상 변경)

        Args:
            button: 버튼
            button_type: 버튼 타입
            success_text: 성공 시 표시할 텍스트
            original_text: 원래 텍스트
            duration: 애니메이션 지속 시간 (ms)
        """
        colors = self.COLORS.get(button_type, self.COLORS['save'])

        if success_text:
            button.configure(text=success_text)
        button.configure(fg_color=colors.get('success', '#28a745'))

        def restore():
            if original_text:
                button.configure(text=original_text)
            button.configure(fg_color=colors['default'])

        self.root.after(duration, restore)

    def start_loading_animation(self, button: ctk.CTkButton, button_type: str = 'run',
                                loading_texts: list = None):
        """
        로딩 애니메이션 시작 (펄스 효과 + 텍스트 변경)

        Args:
            button: 버튼
            button_type: 버튼 타입
            loading_texts: 순환할 로딩 텍스트 리스트
        """
        btn_id = id(button)
        self._animation_running[btn_id] = True
        colors = self.COLORS.get(button_type, self.COLORS['run'])

        if loading_texts is None:
            loading_texts = ['실행 중.', '실행 중..', '실행 중...']

        text_index = [0]  # mutable container for closure

        def pulse():
            if not self._animation_running.get(btn_id, False):
                return

            # 텍스트 순환
            button.configure(text=loading_texts[text_index[0]])
            text_index[0] = (text_index[0] + 1) % len(loading_texts)

            # 펄스 색상 효과
            current_color = button.cget("fg_color")
            if current_color == colors['loading']:
                button.configure(fg_color=colors['pulse'])
            else:
                button.configure(fg_color=colors['loading'])

            self.root.after(400, pulse)

        # 초기 색상 설정
        button.configure(fg_color=colors['loading'])
        pulse()

    def stop_loading_animation(self, button: ctk.CTkButton, button_type: str = 'run',
                              original_text: str = None):
        """
        로딩 애니메이션 중지

        Args:
            button: 버튼
            button_type: 버튼 타입
            original_text: 복원할 원래 텍스트
        """
        btn_id = id(button)
        self._animation_running[btn_id] = False

        colors = self.COLORS.get(button_type, self.COLORS['run'])
        button.configure(fg_color=colors['default'])

        if original_text:
            button.configure(text=original_text)

    def animate_enable(self, button: ctk.CTkButton, button_type: str = 'stop'):
        """
        버튼 활성화 애니메이션 (페이드 인 + 스케일)

        Args:
            button: 버튼
            button_type: 버튼 타입
        """
        colors = self.COLORS.get(button_type, self.COLORS['stop'])

        # 밝은 색상에서 시작해서 원래 색상으로
        button.configure(fg_color=colors['pulse'])
        button.configure(state="normal")

        def to_normal():
            button.configure(fg_color=colors['default'])

        self.root.after(200, to_normal)

    def animate_disable(self, button: ctk.CTkButton):
        """
        버튼 비활성화 애니메이션 (페이드 아웃)

        Args:
            button: 버튼
        """
        # 점진적으로 어두워지면서 비활성화
        button.configure(fg_color='#555555')

        def disable():
            button.configure(state="disabled")

        self.root.after(150, disable)

    def shake_button(self, button: ctk.CTkButton, intensity: int = 5, duration: int = 300):
        """
        버튼 흔들기 효과 (에러 시)

        Args:
            button: 버튼
            intensity: 흔들림 강도 (픽셀)
            duration: 지속 시간 (ms)
        """
        original_x = button.winfo_x()
        shake_count = [0]

        def shake():
            if shake_count[0] >= 6:
                # 원위치로 복귀
                return

            offset = intensity if shake_count[0] % 2 == 0 else -intensity
            shake_count[0] += 1

            # padx 조정으로 흔들기 효과 시뮬레이션
            try:
                current_padx = button.pack_info().get('padx', (0, 0))
                if isinstance(current_padx, int):
                    current_padx = (current_padx, current_padx)
                new_padx = (current_padx[0] + offset, current_padx[1])
                button.pack_configure(padx=new_padx)
                self.root.after(50, lambda: button.pack_configure(padx=current_padx))
            except:
                pass

            self.root.after(50, shake)

        shake()


class DynamicButton(ctk.CTkButton):
    """다이나믹 효과가 내장된 버튼 클래스"""

    def __init__(self, parent, ui_agent: UIAgent, button_type: str = 'save',
                 success_text: str = None, loading_texts: list = None, **kwargs):
        """
        Args:
            parent: 부모 위젯
            ui_agent: UI 에이전트 인스턴스
            button_type: 버튼 타입 ('save', 'run', 'stop')
            success_text: 성공 시 표시할 텍스트
            loading_texts: 로딩 중 순환할 텍스트 리스트
            **kwargs: CTkButton에 전달할 추가 인자
        """
        # 버튼 타입에 따른 기본 색상 설정
        colors = UIAgent.COLORS.get(button_type, UIAgent.COLORS['save'])

        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = colors['default']
        if 'hover_color' not in kwargs:
            kwargs['hover_color'] = colors['hover']

        super().__init__(parent, **kwargs)

        self.ui_agent = ui_agent
        self.button_type = button_type
        self.success_text = success_text
        self.loading_texts = loading_texts
        self._original_text = kwargs.get('text', '')
        self._original_command = kwargs.get('command')

        # 클릭 애니메이션 래핑
        if self._original_command:
            self.configure(command=self._animated_command)

    def _animated_command(self):
        """애니메이션이 포함된 명령 실행"""
        self.ui_agent.animate_button_click(
            self,
            self.button_type,
            callback=self._original_command
        )

    def show_success(self, duration: int = 1500):
        """성공 애니메이션 표시"""
        self.ui_agent.animate_success(
            self,
            self.button_type,
            success_text=self.success_text,
            original_text=self._original_text,
            duration=duration
        )

    def start_loading(self):
        """로딩 애니메이션 시작"""
        self.ui_agent.start_loading_animation(
            self,
            self.button_type,
            loading_texts=self.loading_texts
        )

    def stop_loading(self):
        """로딩 애니메이션 중지"""
        self.ui_agent.stop_loading_animation(
            self,
            self.button_type,
            original_text=self._original_text
        )

    def animate_enable(self):
        """활성화 애니메이션"""
        self.ui_agent.animate_enable(self, self.button_type)

    def animate_disable(self):
        """비활성화 애니메이션"""
        self.ui_agent.animate_disable(self)

    def shake(self):
        """흔들기 효과"""
        self.ui_agent.shake_button(self)
