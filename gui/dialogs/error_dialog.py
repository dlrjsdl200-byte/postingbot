"""
에러 종류별 알림 다이얼로그
"""

import customtkinter as ctk
import webbrowser
from typing import Optional, Callable
from enum import Enum


class ErrorType(Enum):
    """에러 종류"""
    API_KEY_INVALID = "api_key_invalid"
    QUOTA_EXCEEDED = "quota_exceeded"
    MODEL_NOT_FOUND = "model_not_found"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class ErrorDialog(ctk.CTkToplevel):
    """에러 알림 다이얼로그"""

    GEMINI_API_KEY_URL = "https://aistudio.google.com/app/apikey"

    def __init__(
        self,
        parent,
        error_type: ErrorType,
        message: str = "",
        retry_seconds: int = 0,
        on_retry: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None
    ):
        super().__init__(parent)

        self.error_type = error_type
        self.retry_seconds = retry_seconds
        self.on_retry = on_retry
        self.on_cancel = on_cancel
        self.remaining_seconds = retry_seconds
        self.timer_id = None

        # 윈도우 설정
        self.title("알림")
        self.geometry("450x200")
        self.resizable(False, False)

        # 모달 설정
        self.transient(parent)
        self.grab_set()

        # 중앙 배치
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")

        # UI 생성
        self._create_ui(message)

        # 닫기 버튼 이벤트
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_ui(self, message: str):
        """에러 종류별 UI 생성"""
        # 메인 프레임
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        if self.error_type == ErrorType.API_KEY_INVALID:
            self._create_api_key_error_ui(main_frame, message)
        elif self.error_type == ErrorType.QUOTA_EXCEEDED:
            self._create_quota_error_ui(main_frame, message)
        elif self.error_type == ErrorType.MODEL_NOT_FOUND:
            self._create_model_error_ui(main_frame, message)
        else:
            self._create_generic_error_ui(main_frame, message)

    def _create_api_key_error_ui(self, parent, message: str):
        """API 키 에러 UI"""
        # 아이콘 및 메시지
        icon_label = ctk.CTkLabel(
            parent,
            text="❌",
            font=ctk.CTkFont(size=40)
        )
        icon_label.pack(pady=(0, 10))

        msg_label = ctk.CTkLabel(
            parent,
            text="API 키가 만료되었거나 무효합니다.\n새 API 키를 발급받아 입력해주세요.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        msg_label.pack(pady=(0, 20))

        # 버튼 프레임
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x")

        # API 키 발급 페이지 열기 버튼
        open_btn = ctk.CTkButton(
            btn_frame,
            text="API 키 발급 페이지 열기",
            command=self._open_api_key_page,
            fg_color="#4285F4",
            hover_color="#3367D6"
        )
        open_btn.pack(side="left", expand=True, padx=5)

        # 확인 버튼
        ok_btn = ctk.CTkButton(
            btn_frame,
            text="확인",
            command=self._on_close,
            fg_color="#666666",
            hover_color="#555555"
        )
        ok_btn.pack(side="right", expand=True, padx=5)

    def _create_quota_error_ui(self, parent, message: str):
        """할당량 초과 에러 UI"""
        # 아이콘 및 메시지
        icon_label = ctk.CTkLabel(
            parent,
            text="⏳",
            font=ctk.CTkFont(size=40)
        )
        icon_label.pack(pady=(0, 10))

        if self.retry_seconds > 0:
            minutes = self.retry_seconds // 60
            seconds = self.retry_seconds % 60
            if minutes > 0:
                time_str = f"{minutes}분 {seconds}초" if seconds > 0 else f"{minutes}분"
            else:
                time_str = f"{seconds}초"
            msg_text = f"API 할당량을 초과했습니다.\n{time_str} 후에 다시 시도해주세요."
        else:
            msg_text = "API 할당량을 초과했습니다.\n잠시 후 다시 시도해주세요."

        self.msg_label = ctk.CTkLabel(
            parent,
            text=msg_text,
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        self.msg_label.pack(pady=(0, 20))

        # 버튼 프레임
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x")

        # 자동 재시도 버튼
        if self.retry_seconds > 0 and self.on_retry:
            self.retry_btn = ctk.CTkButton(
                btn_frame,
                text=f"{self.retry_seconds}초 후 자동 재시도",
                command=self._start_auto_retry,
                fg_color="#FF9800",
                hover_color="#F57C00"
            )
            self.retry_btn.pack(side="left", expand=True, padx=5)

        # 취소 버튼
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="취소",
            command=self._on_cancel,
            fg_color="#666666",
            hover_color="#555555"
        )
        cancel_btn.pack(side="right", expand=True, padx=5)

    def _create_model_error_ui(self, parent, message: str):
        """모델 없음 에러 UI"""
        # 아이콘 및 메시지
        icon_label = ctk.CTkLabel(
            parent,
            text="⚠️",
            font=ctk.CTkFont(size=40)
        )
        icon_label.pack(pady=(0, 10))

        msg_label = ctk.CTkLabel(
            parent,
            text="사용 가능한 모델을 찾을 수 없습니다.\nAPI 키를 확인해주세요.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        msg_label.pack(pady=(0, 20))

        # 버튼 프레임
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x")

        # API 키 발급 페이지 열기 버튼
        open_btn = ctk.CTkButton(
            btn_frame,
            text="API 키 확인하기",
            command=self._open_api_key_page,
            fg_color="#4285F4",
            hover_color="#3367D6"
        )
        open_btn.pack(side="left", expand=True, padx=5)

        # 확인 버튼
        ok_btn = ctk.CTkButton(
            btn_frame,
            text="확인",
            command=self._on_close,
            fg_color="#666666",
            hover_color="#555555"
        )
        ok_btn.pack(side="right", expand=True, padx=5)

    def _create_generic_error_ui(self, parent, message: str):
        """일반 에러 UI"""
        # 아이콘 및 메시지
        icon_label = ctk.CTkLabel(
            parent,
            text="❗",
            font=ctk.CTkFont(size=40)
        )
        icon_label.pack(pady=(0, 10))

        # 메시지가 너무 길면 자르기
        if len(message) > 100:
            message = message[:100] + "..."

        msg_label = ctk.CTkLabel(
            parent,
            text=f"오류 발생:\n{message}",
            font=ctk.CTkFont(size=14),
            justify="center",
            wraplength=400
        )
        msg_label.pack(pady=(0, 20))

        # 확인 버튼
        ok_btn = ctk.CTkButton(
            parent,
            text="확인",
            command=self._on_close,
            fg_color="#666666",
            hover_color="#555555"
        )
        ok_btn.pack()

    def _open_api_key_page(self):
        """API 키 발급 페이지 열기"""
        webbrowser.open(self.GEMINI_API_KEY_URL)

    def _start_auto_retry(self):
        """자동 재시도 타이머 시작"""
        self.remaining_seconds = self.retry_seconds
        self._update_timer()

    def _update_timer(self):
        """타이머 업데이트"""
        if self.remaining_seconds > 0:
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            if minutes > 0:
                time_str = f"{minutes}분 {seconds}초"
            else:
                time_str = f"{seconds}초"

            self.msg_label.configure(text=f"API 할당량을 초과했습니다.\n{time_str} 후 자동 재시도...")
            self.retry_btn.configure(text=f"대기 중... ({self.remaining_seconds}초)", state="disabled")

            self.remaining_seconds -= 1
            self.timer_id = self.after(1000, self._update_timer)
        else:
            # 재시도 실행
            self._on_retry_execute()

    def _on_retry_execute(self):
        """재시도 실행"""
        if self.timer_id:
            self.after_cancel(self.timer_id)
        self.destroy()
        if self.on_retry:
            self.on_retry()

    def _on_cancel(self):
        """취소"""
        if self.timer_id:
            self.after_cancel(self.timer_id)
        self.destroy()
        if self.on_cancel:
            self.on_cancel()

    def _on_close(self):
        """닫기"""
        if self.timer_id:
            self.after_cancel(self.timer_id)
        self.destroy()


def show_error_dialog(
    parent,
    error_type: ErrorType,
    message: str = "",
    retry_seconds: int = 0,
    on_retry: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None
):
    """에러 다이얼로그 표시 헬퍼 함수"""
    dialog = ErrorDialog(
        parent,
        error_type,
        message,
        retry_seconds,
        on_retry,
        on_cancel
    )
    dialog.wait_window()


def classify_gemini_error(error: Exception) -> tuple[ErrorType, str, int]:
    """
    Gemini API 에러 분류

    Returns:
        (error_type, message, retry_seconds)
    """
    import re

    error_msg = str(error).lower()
    original_msg = str(error)

    # API 키 무효
    if any(keyword in error_msg for keyword in [
        'api_key_invalid', 'invalid api key', 'api key not valid',
        'expired', 'permission denied', '400'
    ]) and 'api' in error_msg and 'key' in error_msg:
        return ErrorType.API_KEY_INVALID, original_msg, 0

    # 할당량 초과
    if any(keyword in error_msg for keyword in [
        '429', 'quota', 'rate limit', 'resource exhausted', 'too many requests'
    ]):
        # retry 시간 추출
        retry_seconds = 0
        patterns = [
            r'retry\s+(?:in|after)\s+(\d+)\s*(?:seconds?|s)',
            r'(\d+)\s*(?:seconds?|s)\s+(?:until|before)',
            r'wait\s+(\d+)\s*(?:seconds?|s)',
            r'try again in (\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                retry_seconds = int(match.group(1))
                break

        if retry_seconds == 0:
            retry_seconds = 60  # 기본 1분

        return ErrorType.QUOTA_EXCEEDED, original_msg, retry_seconds

    # 모델 없음
    if any(keyword in error_msg for keyword in [
        '404', 'not found', 'model not found', 'does not exist'
    ]):
        return ErrorType.MODEL_NOT_FOUND, original_msg, 0

    # 네트워크 에러
    if any(keyword in error_msg for keyword in [
        'connection', 'timeout', 'network', 'unreachable'
    ]):
        return ErrorType.NETWORK_ERROR, original_msg, 0

    # 기타
    return ErrorType.UNKNOWN, original_msg, 0
