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

        # 참고 URL 입력
        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.pack(fill="x", padx=15, pady=5)

        url_label = ctk.CTkLabel(url_frame, text="참고 URL:", width=100, anchor="w")
        url_label.pack(side="left")

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="참고할 웹페이지 URL (선택사항)"
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.url_check_btn = ctk.CTkButton(
            url_frame,
            text="확인",
            width=50,
            command=self._check_url
        )
        self.url_check_btn.pack(side="right")

        # URL 상태 표시
        self.url_status = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        self.url_status.pack(fill="x", padx=15, pady=(0, 5))

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

        # 크롤링 결과 저장
        self._crawl_result = None

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

    def get_reference_url(self) -> str:
        """참고 URL 반환"""
        return self.url_entry.get().strip()

    def get_crawl_result(self):
        """크롤링 결과 반환"""
        return self._crawl_result

    def _check_url(self):
        """URL 확인 및 크롤링"""
        url = self.url_entry.get().strip()

        if not url:
            self.url_status.configure(text="URL을 입력해주세요.", text_color="orange")
            return

        # URL 형식 검사
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)

        self.url_status.configure(text="확인 중...", text_color="gray")
        self.url_check_btn.configure(state="disabled")
        self.update()

        # 별도 스레드에서 크롤링
        import threading
        thread = threading.Thread(target=self._do_crawl, args=(url,), daemon=True)
        thread.start()

    def _do_crawl(self, url: str):
        """크롤링 실행 (별도 스레드)"""
        try:
            from services.url_crawler import UrlCrawler

            crawler = UrlCrawler(logger=self.app.logger.log)
            result = crawler.crawl(url)

            # UI 업데이트는 메인 스레드에서
            self.after(0, lambda: self._on_crawl_complete(result))

        except Exception as e:
            self.after(0, lambda: self._on_crawl_error(str(e)))

    def _on_crawl_complete(self, result):
        """크롤링 완료 처리"""
        self.url_check_btn.configure(state="normal")

        if result.success:
            self._crawl_result = result
            title_preview = result.title[:40] + "..." if len(result.title) > 40 else result.title
            self.url_status.configure(
                text=f"✓ {title_preview} ({len(result.content)}자)",
                text_color="green"
            )
            self.app.logger.log(f"참고 URL 로드 완료: {result.title}")
        else:
            self._crawl_result = None
            self.url_status.configure(
                text=f"✗ {result.error_message}",
                text_color="red"
            )

    def _on_crawl_error(self, error: str):
        """크롤링 오류 처리"""
        self.url_check_btn.configure(state="normal")
        self._crawl_result = None
        self.url_status.configure(text=f"✗ 오류: {error[:50]}", text_color="red")
