"""
할당량 확인 다이얼로그 - 모델별 API 할당량 상태 표시
"""

import customtkinter as ctk
import threading
from typing import Callable, Optional


class QuotaDialog(ctk.CTkToplevel):
    """모델별 할당량 상태 표시 다이얼로그"""

    def __init__(
        self,
        parent,
        api_key: str,
        logger: Optional[Callable] = None
    ):
        super().__init__(parent)

        self.api_key = api_key
        self.logger = logger or print
        self._status_labels = []

        # 창 설정
        self.title("API 할당량 확인")
        self.geometry("400x350")
        self.resizable(False, False)

        # 모달 설정
        self.transient(parent)
        self.grab_set()

        # UI 구성
        self._setup_ui()

        # 할당량 확인 시작
        self._check_quota()

        # 창 중앙 배치
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        """UI 구성"""
        # 헤더
        header = ctk.CTkLabel(
            self,
            text="Gemini API 모델별 할당량",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=(15, 5))

        subtitle = ctk.CTkLabel(
            self,
            text="각 모델의 현재 사용 가능 여부를 확인합니다",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 15))

        # 상태 표시 영역
        self.status_frame = ctk.CTkScrollableFrame(
            self,
            width=360,
            height=200
        )
        self.status_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # 로딩 표시
        self.loading_label = ctk.CTkLabel(
            self.status_frame,
            text="확인 중...",
            font=ctk.CTkFont(size=12)
        )
        self.loading_label.pack(pady=20)

        # 버튼 영역
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.refresh_btn = ctk.CTkButton(
            btn_frame,
            text="새로고침",
            width=100,
            state="disabled",
            command=self._check_quota
        )
        self.refresh_btn.pack(side="left")

        close_btn = ctk.CTkButton(
            btn_frame,
            text="닫기",
            width=100,
            command=self.destroy
        )
        close_btn.pack(side="right")

    def _check_quota(self):
        """할당량 확인 시작"""
        self.refresh_btn.configure(state="disabled")
        self.loading_label.configure(text="확인 중...")
        self.loading_label.pack(pady=20)

        # 기존 상태 레이블 제거
        for label_frame in self._status_labels:
            label_frame.destroy()
        self._status_labels = []

        # 별도 스레드에서 확인
        thread = threading.Thread(target=self._do_check_quota, daemon=True)
        thread.start()

    def _do_check_quota(self):
        """할당량 확인 실행 (별도 스레드)"""
        try:
            from services.gemini_service import GeminiService

            service = GeminiService(
                api_key=self.api_key,
                logger=lambda msg: None  # 로그 비활성화
            )

            results = service.get_model_quota_status()

            # UI 업데이트는 메인 스레드에서
            self.after(0, lambda: self._update_status(results))

        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))

    def _update_status(self, results: list):
        """상태 업데이트"""
        self.loading_label.pack_forget()

        for result in results:
            model_name = result["model"]
            status = result["status"]
            available = result["available"]

            # 모델명 간소화
            short_name = model_name.replace("models/", "")

            # 프레임 생성
            item_frame = ctk.CTkFrame(self.status_frame)
            item_frame.pack(fill="x", pady=2)

            # 상태 아이콘
            if available:
                icon = "●"
                icon_color = "#28a745"  # 녹색
            else:
                icon = "●"
                icon_color = "#dc3545"  # 빨간색

            icon_label = ctk.CTkLabel(
                item_frame,
                text=icon,
                font=ctk.CTkFont(size=14),
                text_color=icon_color,
                width=20
            )
            icon_label.pack(side="left", padx=(10, 5))

            # 모델명
            name_label = ctk.CTkLabel(
                item_frame,
                text=short_name,
                font=ctk.CTkFont(size=11),
                anchor="w",
                width=180
            )
            name_label.pack(side="left", padx=(0, 5))

            # 상태
            status_color = "#28a745" if available else "#dc3545"
            status_label = ctk.CTkLabel(
                item_frame,
                text=status,
                font=ctk.CTkFont(size=11),
                text_color=status_color,
                anchor="e"
            )
            status_label.pack(side="right", padx=10)

            self._status_labels.append(item_frame)

        # 요약
        available_count = sum(1 for r in results if r["available"])
        total_count = len(results)

        summary_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        summary_frame.pack(fill="x", pady=(10, 0))

        summary_label = ctk.CTkLabel(
            summary_frame,
            text=f"사용 가능: {available_count}/{total_count} 모델",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#28a745" if available_count > 0 else "#dc3545"
        )
        summary_label.pack()

        self._status_labels.append(summary_frame)

        self.refresh_btn.configure(state="normal")

    def _show_error(self, error: str):
        """에러 표시"""
        self.loading_label.configure(
            text=f"오류: {error[:50]}...",
            text_color="red"
        )
        self.refresh_btn.configure(state="normal")
