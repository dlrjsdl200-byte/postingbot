"""
주제 프레임 - 카테고리 및 키워드 설정
"""

import customtkinter as ctk


class TopicFrame(ctk.CTkFrame):
    """주제/키워드 설정 프레임"""

    CATEGORIES = [
        "직접입력",
        "의료/약학",
        "IT/테크",
        "여행",
        "맛집/요리",
        "육아/교육",
        "재테크/경제",
        "뷰티/패션",
        "운동/다이어트",
        "반려동물",
        "자기계발"
    ]

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        # 헤더
        header = ctk.CTkLabel(
            self,
            text="포스팅 설정",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=15, pady=(10, 5))

        # 카테고리 선택
        cat_frame = ctk.CTkFrame(self, fg_color="transparent")
        cat_frame.pack(fill="x", padx=15, pady=5)

        cat_label = ctk.CTkLabel(cat_frame, text="주제 카테고리:", width=100, anchor="w")
        cat_label.pack(side="left")

        self.category_var = ctk.StringVar(value="직접입력")
        self.category_dropdown = ctk.CTkComboBox(
            cat_frame,
            values=self.CATEGORIES,
            variable=self.category_var,
            width=200
        )
        self.category_dropdown.pack(side="left", fill="x", expand=True)

        # 키워드 입력
        kw_frame = ctk.CTkFrame(self, fg_color="transparent")
        kw_frame.pack(fill="x", padx=15, pady=5)

        kw_label = ctk.CTkLabel(kw_frame, text="세부 키워드:", width=100, anchor="w")
        kw_label.pack(side="left")

        self.keyword_entry = ctk.CTkEntry(
            kw_frame,
            placeholder_text="쉼표로 구분 (예: 서울맛집, 강남카페, 브런치)"
        )
        self.keyword_entry.pack(side="left", fill="x", expand=True)

        # 옵션 체크박스
        opt_frame = ctk.CTkFrame(self, fg_color="transparent")
        opt_frame.pack(fill="x", padx=15, pady=(5, 10))

        self.use_image_var = ctk.BooleanVar(value=True)
        self.image_checkbox = ctk.CTkCheckBox(
            opt_frame,
            text="이미지 자동 생성",
            variable=self.use_image_var
        )
        self.image_checkbox.pack(side="left", padx=(0, 20))

        self.use_emoji_var = ctk.BooleanVar(value=True)
        self.emoji_checkbox = ctk.CTkCheckBox(
            opt_frame,
            text="이모지 사용",
            variable=self.use_emoji_var
        )
        self.emoji_checkbox.pack(side="left")

    def get_category(self) -> str:
        """선택된 카테고리 반환"""
        return self.category_var.get()

    def get_keywords(self) -> str:
        """키워드 반환"""
        return self.keyword_entry.get().strip()

    def get_use_image(self) -> bool:
        """이미지 사용 여부 반환"""
        return self.use_image_var.get()

    def get_use_emoji(self) -> bool:
        """이모지 사용 여부 반환"""
        return self.use_emoji_var.get()

    def set_values(self, category: str, keywords: str, use_image: bool, use_emoji: bool):
        """값 설정"""
        if category in self.CATEGORIES:
            self.category_var.set(category)
        self.keyword_entry.delete(0, "end")
        self.keyword_entry.insert(0, keywords)
        self.use_image_var.set(use_image)
        self.use_emoji_var.set(use_emoji)
