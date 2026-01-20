"""
카테고리 프레임 - 블로그 카테고리 선택
"""

import customtkinter as ctk
from typing import List


class CategoryFrame(ctk.CTkFrame):
    """블로그 카테고리 선택 프레임"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._categories = []

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        # 헤더
        header = ctk.CTkLabel(
            self,
            text="블로그 카테고리",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=15, pady=(10, 5))

        # 카테고리 선택
        cat_frame = ctk.CTkFrame(self, fg_color="transparent")
        cat_frame.pack(fill="x", padx=15, pady=(5, 10))

        cat_label = ctk.CTkLabel(cat_frame, text="카테고리:", width=100, anchor="w")
        cat_label.pack(side="left")

        self.category_var = ctk.StringVar(value="로그인 후 선택 가능")
        self.category_dropdown = ctk.CTkComboBox(
            cat_frame,
            values=["로그인 후 선택 가능"],
            variable=self.category_var,
            width=300,
            state="disabled"
        )
        self.category_dropdown.pack(side="left", fill="x", expand=True)

    def set_categories(self, categories: List[dict]):
        """카테고리 목록 설정

        Args:
            categories: [{"name": "카테고리명", "id": "카테고리ID"}, ...]
        """
        self._categories = categories

        if categories:
            category_names = [cat["name"] for cat in categories]
            self.category_dropdown.configure(values=category_names, state="normal")
            self.category_var.set(category_names[0])
        else:
            self.category_dropdown.configure(values=["카테고리 없음"], state="disabled")
            self.category_var.set("카테고리 없음")

    def get_selected_category(self) -> dict:
        """선택된 카테고리 반환

        Returns:
            {"name": "카테고리명", "id": "카테고리ID"} 또는 None
        """
        selected_name = self.category_var.get()

        for cat in self._categories:
            if cat["name"] == selected_name:
                return cat

        return None

    def get_selected_category_name(self) -> str:
        """선택된 카테고리 이름 반환"""
        return self.category_var.get()

    def get_selected_category_id(self) -> str:
        """선택된 카테고리 ID 반환"""
        cat = self.get_selected_category()
        return cat["id"] if cat else ""

    def reset(self):
        """카테고리 초기화"""
        self._categories = []
        self.category_dropdown.configure(values=["로그인 후 선택 가능"], state="disabled")
        self.category_var.set("로그인 후 선택 가능")

    def is_ready(self) -> bool:
        """카테고리가 로드되었는지 확인"""
        return len(self._categories) > 0
