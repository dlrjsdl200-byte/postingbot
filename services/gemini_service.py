"""
Gemini API 서비스 - 블로그 콘텐츠 생성

사용 예시:
    from services.gemini_service import GeminiService

    service = GeminiService(api_key="YOUR_API_KEY")

    # 블로그 글 생성
    content = service.generate_blog_post(
        topic="파이썬 자동화",
        category="IT/테크",
        keywords=["파이썬", "업무 자동화", "효율"],
        use_emoji=True
    )
"""

import time
import re
from typing import Optional, List, Callable
from dataclasses import dataclass
from enum import Enum


class GeminiErrorType(Enum):
    """Gemini API 에러 종류"""
    API_KEY_INVALID = "api_key_invalid"
    QUOTA_EXCEEDED = "quota_exceeded"
    MODEL_NOT_FOUND = "model_not_found"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class BlogContent:
    """블로그 콘텐츠 데이터"""
    title: str
    content: str
    tags: List[str]
    summary: str


class GeminiService:
    """Google Gemini API 래퍼 (동적 모델 선택 지원)"""

    # Rate limiting 설정 (무료 플랜 기준: 15 RPM)
    # 안전하게 분당 10회 = 6초 간격
    RATE_LIMIT_DELAY = 6  # 요청 간 최소 대기 시간 (초)
    RPM_LIMIT = 10  # 분당 최대 요청 수
    RPM_WINDOW = 60  # RPM 윈도우 (초)

    def __init__(
        self,
        api_key: str,
        logger: Optional[Callable] = None
    ):
        """
        Args:
            api_key: Gemini API 키
            logger: 로그 출력 함수
        """
        self.api_key = api_key
        self.logger = logger or print
        self._genai = None
        self._last_request_time = 0
        self._request_times = []  # RPM 추적용
        self._working_model = None  # 성공한 모델 저장
        self._available_models = []  # 사용 가능한 모델 목록

        self._init_client()

    def _init_client(self):
        """Gemini 클라이언트 초기화"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._genai = genai
            self.logger("Gemini API 클라이언트 초기화 완료")

            # API 호출 없이 하드코딩된 모델 목록 사용 (RPM 절약)
            self._available_models = [
                "models/gemini-2.0-flash",
                "models/gemini-1.5-flash",
                "models/gemini-1.5-pro",
            ]
            self._working_model = "models/gemini-2.0-flash"  # 기본 모델 설정

        except ImportError:
            raise GeminiServiceError(
                "google-generativeai 패키지가 필요합니다. "
                "pip install google-generativeai"
            )
        except Exception as e:
            raise GeminiServiceError(f"Gemini 초기화 실패: {e}")

    def _fetch_available_models(self):
        """사용 가능한 모델 목록 조회"""
        try:
            self.logger("사용 가능한 모델 조회 중...")
            models = self._genai.list_models()

            # generateContent를 지원하는 모델만 필터링
            self._available_models = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name
                    self._available_models.append(model_name)

            if self._available_models:
                self.logger(f"사용 가능한 모델 {len(self._available_models)}개 발견")
                # 처음 3개만 로그에 표시
                for m in self._available_models[:3]:
                    self.logger(f"  - {m}")
                if len(self._available_models) > 3:
                    self.logger(f"  ... 외 {len(self._available_models) - 3}개")
            else:
                self.logger("사용 가능한 모델이 없습니다.")

        except Exception as e:
            self.logger(f"모델 목록 조회 실패: {e}")
            # 실패 시 기본 모델 목록 사용
            self._available_models = [
                "models/gemini-1.5-flash",
                "models/gemini-1.5-pro",
                "models/gemini-pro",
            ]

    def _rate_limit(self):
        """Rate limiting 적용 (RPM 제한 준수)"""
        current_time = time.time()

        # 1분 이내 요청 기록만 유지
        self._request_times = [
            t for t in self._request_times
            if current_time - t < self.RPM_WINDOW
        ]

        # RPM 제한 확인
        if len(self._request_times) >= self.RPM_LIMIT:
            # 가장 오래된 요청 이후 1분이 될 때까지 대기
            oldest_request = self._request_times[0]
            wait_time = self.RPM_WINDOW - (current_time - oldest_request) + 1
            if wait_time > 0:
                self.logger(f"RPM 제한 도달. {wait_time:.0f}초 대기 중...")
                time.sleep(wait_time)
                current_time = time.time()
                # 대기 후 다시 정리
                self._request_times = [
                    t for t in self._request_times
                    if current_time - t < self.RPM_WINDOW
                ]

        # 기본 요청 간격 유지
        elapsed = current_time - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - elapsed
            time.sleep(sleep_time)

        # 요청 시간 기록
        self._last_request_time = time.time()
        self._request_times.append(self._last_request_time)

    def _extract_retry_seconds(self, error_msg: str) -> Optional[int]:
        """에러 메시지에서 재시도 대기 시간 추출"""
        # "retry in X seconds" 또는 "Retry after X seconds" 패턴 찾기
        patterns = [
            r'retry\s+(?:in|after)\s+(\d+)\s*(?:seconds?|s)',
            r'(\d+)\s*(?:seconds?|s)\s+(?:until|before)',
            r'wait\s+(\d+)\s*(?:seconds?|s)',
            r'try again in (\d+)',
        ]

        error_lower = error_msg.lower()
        for pattern in patterns:
            match = re.search(pattern, error_lower)
            if match:
                return int(match.group(1))

        return None

    def _is_quota_error(self, error: Exception) -> bool:
        """할당량 초과 에러인지 확인"""
        error_msg = str(error).lower()
        quota_keywords = ['429', 'quota', 'rate limit', 'resource exhausted', 'too many requests']
        return any(keyword in error_msg for keyword in quota_keywords)

    def _is_rpm_error(self, error: Exception) -> bool:
        """RPM(분당 요청 수) 제한 에러인지 확인"""
        error_msg = str(error).lower()
        rpm_keywords = ['rpm', 'requests per minute', 'rate limit', 'too many requests']
        return any(keyword in error_msg for keyword in rpm_keywords)

    def _call_api(self, model_name: str, prompt: str, retry_count: int = 0) -> str:
        """특정 모델로 API 호출 (429/RPM 에러 시 자동 재시도)"""
        max_retries = 5  # RPM 제한 때문에 재시도 횟수 증가

        try:
            # Rate limiting 적용
            self._rate_limit()

            model = self._genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            error_msg = str(e)

            # 429 할당량/RPM 초과 에러 처리
            if self._is_quota_error(e) and retry_count < max_retries:
                # 에러 메시지에서 대기 시간 추출
                wait_seconds = self._extract_retry_seconds(error_msg)

                # RPM 에러인 경우 더 긴 대기 시간
                if self._is_rpm_error(e):
                    if wait_seconds is None or wait_seconds < 60:
                        wait_seconds = 60  # RPM 리셋을 위해 최소 1분 대기

                if wait_seconds is None:
                    # 기본 대기 시간 (지수 백오프, 더 보수적으로)
                    wait_seconds = min(45 * (2 ** retry_count), 180)

                self.logger(f"API 제한! {wait_seconds}초 후 재시도합니다... ({retry_count + 1}/{max_retries})")

                # 요청 기록 초기화 (RPM 윈도우 리셋)
                self._request_times = []

                # 대기 중 카운트다운 표시
                for remaining in range(wait_seconds, 0, -10):
                    if remaining > 10:
                        self.logger(f"  대기 중... {remaining}초 남음")
                    time.sleep(min(10, remaining))

                # 재시도
                return self._call_api(model_name, prompt, retry_count + 1)

            # 다른 에러는 그대로 raise
            raise

    def _get_sorted_models(self) -> List[str]:
        """우선순위에 따라 정렬된 모델 목록 반환"""
        if not self._available_models:
            self._fetch_available_models()

        def model_priority(model_name):
            name_lower = model_name.lower()
            # 2.5-flash > 2.0-flash > 1.5-flash > pro 순서
            if '2.5' in name_lower and 'flash' in name_lower:
                return (0, model_name)
            elif '2.0' in name_lower and 'flash' in name_lower:
                return (1, model_name)
            elif 'flash' in name_lower:
                return (2, model_name)
            elif 'pro' in name_lower and 'vision' not in name_lower:
                return (3, model_name)
            return (99, model_name)

        return sorted(self._available_models, key=model_priority)

    def find_available_model(self, skip_test: bool = False) -> Optional[str]:
        """
        할당량이 있는 사용 가능한 모델 찾기

        Args:
            skip_test: True면 테스트 없이 첫 번째 모델 반환 (RPM 절약)

        Returns:
            사용 가능한 모델명 또는 None
        """
        sorted_models = self._get_sorted_models()

        # 이미 성공한 모델이 있으면 그것 사용
        if self._working_model and self._working_model in sorted_models:
            self.logger(f"기존 모델 사용: {self._working_model}")
            return self._working_model

        # 테스트 건너뛰기 (RPM 절약)
        if skip_test and sorted_models:
            self._working_model = sorted_models[0]
            self.logger(f"기본 모델 선택: {self._working_model}")
            return self._working_model

        self.logger("사용 가능한 모델 검색 중...")

        for model in sorted_models[:3]:  # 상위 3개만 테스트 (RPM 절약)
            try:
                # Rate limiting 적용
                self._rate_limit()

                model_instance = self._genai.GenerativeModel(model)
                # 아주 간단한 테스트
                response = model_instance.generate_content("Hi")
                if response.text:
                    self.logger(f"사용 가능한 모델 발견: {model}")
                    self._working_model = model
                    return model
            except Exception as e:
                error_msg = str(e).lower()
                if self._is_quota_error(e):
                    # RPM 제한이면 잠시 대기 후 계속
                    if self._is_rpm_error(e):
                        self.logger(f"  {model}: RPM 제한 - 대기 후 계속")
                        time.sleep(15)  # 15초 대기
                        continue
                    self.logger(f"  {model}: 할당량 초과")
                elif '404' in error_msg or 'not found' in error_msg:
                    self.logger(f"  {model}: 모델 없음")
                else:
                    self.logger(f"  {model}: 오류 - {error_msg[:50]}")
                time.sleep(2)
                continue

        return None

    def _generate(self, prompt: str) -> str:
        """
        텍스트 생성 (동적 모델 선택)

        Args:
            prompt: 프롬프트

        Returns:
            생성된 텍스트
        """
        # 이전에 성공한 모델이 있으면 그것부터 시도
        if self._working_model:
            try:
                result = self._call_api(self._working_model, prompt)
                return result
            except Exception as e:
                # RPM 에러면 대기 후 같은 모델로 재시도
                if self._is_rpm_error(e):
                    self.logger(f"RPM 제한 발생. 60초 대기 후 재시도...")
                    time.sleep(60)
                    try:
                        result = self._call_api(self._working_model, prompt)
                        return result
                    except Exception:
                        pass
                self.logger(f"기존 모델 {self._working_model} 실패, 다른 모델 시도...")
                self._working_model = None

        sorted_models = self._get_sorted_models()

        # 모든 모델 순차적으로 시도
        last_error = None
        quota_errors = []  # 할당량 초과된 모델 추적

        for model in sorted_models[:5]:  # 상위 5개 모델만 시도
            try:
                self.logger(f"모델 시도 중: {model}")
                result = self._call_api(model, prompt)
                self._working_model = model
                self.logger(f"모델 {model} 사용 성공!")
                return result
            except Exception as e:
                error_msg = str(e)[:100]

                # 429 에러인 경우 (이미 _call_api에서 재시도 했음)
                if self._is_quota_error(e):
                    self.logger(f"모델 {model} 할당량/RPM 초과")
                    quota_errors.append(model)
                else:
                    self.logger(f"모델 {model} 실패: {error_msg}")

                last_error = e
                time.sleep(1)
                continue

        # 모든 모델이 할당량 초과인 경우 특별 메시지
        if len(quota_errors) == len(sorted_models):
            raise GeminiServiceError(
                "모든 모델의 API 할당량이 초과되었습니다. "
                "잠시 후 다시 시도하거나, API 할당량을 확인해주세요."
            )

        raise GeminiServiceError(f"모든 Gemini 모델 시도 실패. 마지막 오류: {last_error}")

    def generate_blog_post(
        self,
        topic: str,
        category: str = "",
        keywords: Optional[List[str]] = None,
        use_emoji: bool = True,
        min_length: int = 1500,
        max_length: int = 3000
    ) -> BlogContent:
        """
        블로그 포스트 생성

        Args:
            topic: 주제
            category: 카테고리
            keywords: 키워드 리스트
            use_emoji: 이모지 사용 여부
            min_length: 최소 글자 수
            max_length: 최대 글자 수

        Returns:
            BlogContent 객체
        """
        keywords_str = ", ".join(keywords) if keywords else topic
        emoji_instruction = "이모지를 적절히 사용해서" if use_emoji else "이모지 없이"

        prompt = f"""당신은 네이버 블로그 전문 작가입니다.
다음 조건에 맞는 블로그 글을 작성해주세요:

[주제] {topic}
[카테고리] {category}
[키워드] {keywords_str}

[작성 조건]
1. {emoji_instruction} 친근하고 읽기 쉬운 문체로 작성
2. 글 길이: {min_length}~{max_length}자
3. 서론, 본론, 결론 구조로 작성
4. 소제목(##)을 3-5개 사용하여 가독성 높이기
5. 실용적인 정보와 팁 포함
6. 독자가 공감할 수 있는 경험담이나 예시 포함
7. 마지막에 독자 참여를 유도하는 질문 추가

[출력 형식]
제목: (흥미로운 제목)

(본문 내용)

태그: (쉼표로 구분된 5-7개 태그)
"""

        self.logger(f"블로그 글 생성 중: {topic}")
        response = self._generate(prompt)

        # 응답 파싱
        return self._parse_blog_response(response, topic)

    def _parse_blog_response(self, response: str, default_topic: str) -> BlogContent:
        """블로그 응답 파싱"""
        lines = response.strip().split('\n')

        title = default_topic
        content_lines = []
        tags = []
        in_content = False

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith('제목:'):
                title = line_stripped[3:].strip()
            elif line_stripped.startswith('태그:'):
                tags_str = line_stripped[3:].strip()
                tags = [t.strip().replace('#', '') for t in tags_str.split(',')]
            elif line_stripped == '':
                if in_content:
                    content_lines.append('')
            else:
                if not line_stripped.startswith('제목:'):
                    in_content = True
                    content_lines.append(line)

        content = '\n'.join(content_lines).strip()

        # 태그가 없으면 기본 태그 생성
        if not tags:
            tags = [default_topic]

        # 요약 생성
        summary = content[:200] + "..." if len(content) > 200 else content

        return BlogContent(
            title=title,
            content=content,
            tags=tags,
            summary=summary
        )

    def generate_title_suggestions(
        self,
        topic: str,
        count: int = 5
    ) -> List[str]:
        """
        제목 제안 생성

        Args:
            topic: 주제
            count: 생성할 제목 수

        Returns:
            제목 리스트
        """
        prompt = f"""다음 주제에 대한 네이버 블로그 제목을 {count}개 제안해주세요.
클릭을 유도하는 매력적인 제목으로 작성해주세요.

주제: {topic}

형식: 번호. 제목
"""
        self.logger(f"제목 제안 생성 중: {topic}")
        response = self._generate(prompt)

        titles = []
        for line in response.split('\n'):
            line = line.strip()
            if line and line[0].isdigit():
                # "1. 제목" 형식에서 제목만 추출
                parts = line.split('.', 1)
                if len(parts) > 1:
                    titles.append(parts[1].strip())

        return titles[:count]

    def generate_image_prompt(
        self,
        topic: str,
        style: str = "modern, clean, professional"
    ) -> str:
        """
        이미지 생성용 프롬프트 생성

        Args:
            topic: 주제
            style: 이미지 스타일

        Returns:
            영문 이미지 프롬프트
        """
        prompt = f"""Create an English image generation prompt for the following topic.
The prompt should describe a visually appealing blog header image.

Topic: {topic}
Style: {style}

Requirements:
- Write in English only
- Be descriptive but concise (under 100 words)
- Focus on visual elements, colors, and composition
- No text or words in the image
- Professional blog quality

Output only the prompt, nothing else."""

        self.logger(f"이미지 프롬프트 생성 중: {topic}")
        return self._generate(prompt).strip()

    def improve_content(
        self,
        content: str,
        instruction: str = "더 자연스럽고 읽기 쉽게"
    ) -> str:
        """
        콘텐츠 개선

        Args:
            content: 원본 콘텐츠
            instruction: 개선 지시사항

        Returns:
            개선된 콘텐츠
        """
        prompt = f"""다음 블로그 글을 개선해주세요.

[개선 방향]
{instruction}

[원본 글]
{content}

[출력]
개선된 글만 출력 (설명 없이)"""

        self.logger("콘텐츠 개선 중...")
        return self._generate(prompt)

    def test_connection(self) -> bool:
        """
        API 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            response = self._generate("Say 'OK' if you can hear me.")
            return 'OK' in response.upper()
        except Exception:
            return False

    def get_working_model(self) -> Optional[str]:
        """현재 사용 중인 모델명 반환"""
        return self._working_model

    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록 반환"""
        return self._available_models.copy()

    def get_model_quota_status(self) -> List[dict]:
        """
        각 모델별 할당량 상태 확인

        Returns:
            모델별 상태 리스트 [{"model": str, "status": str, "available": bool}]
        """
        results = []

        # flash 모델 우선으로 정렬
        priority_models = []
        other_models = []

        for model in self._available_models:
            if 'flash' in model.lower():
                priority_models.append(model)
            elif 'pro' in model.lower() and 'vision' not in model.lower():
                other_models.append(model)

        # flash 모델만 + pro 모델 일부 (최대 5개)
        test_models = priority_models[:3] + other_models[:2]

        if not test_models:
            test_models = self._available_models[:5]

        for model in test_models:
            try:
                # 간단한 테스트 요청
                model_instance = self._genai.GenerativeModel(model)
                response = model_instance.generate_content("Hi")

                # 성공
                results.append({
                    "model": model,
                    "status": "사용 가능",
                    "available": True
                })

            except Exception as e:
                error_msg = str(e).lower()

                if self._is_quota_error(e):
                    # 할당량 초과
                    retry_seconds = self._extract_retry_seconds(str(e))
                    if retry_seconds:
                        results.append({
                            "model": model,
                            "status": f"할당량 초과 ({retry_seconds}초 후)",
                            "available": False
                        })
                    else:
                        results.append({
                            "model": model,
                            "status": "할당량 초과",
                            "available": False
                        })
                elif '404' in error_msg or 'not found' in error_msg:
                    results.append({
                        "model": model,
                        "status": "모델 없음",
                        "available": False
                    })
                elif 'api' in error_msg and 'key' in error_msg:
                    results.append({
                        "model": model,
                        "status": "API 키 오류",
                        "available": False
                    })
                else:
                    results.append({
                        "model": model,
                        "status": "오류",
                        "available": False
                    })

            # 요청 간 간격
            time.sleep(1)

        return results


class GeminiServiceError(Exception):
    """Gemini 서비스 예외"""

    def __init__(self, message: str, error_type: GeminiErrorType = GeminiErrorType.UNKNOWN, retry_seconds: int = 0):
        super().__init__(message)
        self.error_type = error_type
        self.retry_seconds = retry_seconds

    @classmethod
    def from_exception(cls, error: Exception) -> 'GeminiServiceError':
        """일반 예외에서 GeminiServiceError 생성"""
        error_msg = str(error).lower()
        original_msg = str(error)

        # API 키 무효
        if any(keyword in error_msg for keyword in [
            'api_key_invalid', 'invalid api key', 'api key not valid',
            'permission denied'
        ]) or ('api' in error_msg and 'key' in error_msg and ('invalid' in error_msg or 'expired' in error_msg)):
            return cls(original_msg, GeminiErrorType.API_KEY_INVALID, 0)

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

            return cls(original_msg, GeminiErrorType.QUOTA_EXCEEDED, retry_seconds)

        # 모델 없음
        if any(keyword in error_msg for keyword in [
            '404', 'not found', 'model not found', 'does not exist'
        ]):
            return cls(original_msg, GeminiErrorType.MODEL_NOT_FOUND, 0)

        # 네트워크 에러
        if any(keyword in error_msg for keyword in [
            'connection', 'timeout', 'network', 'unreachable'
        ]):
            return cls(original_msg, GeminiErrorType.NETWORK_ERROR, 0)

        # 기타
        return cls(original_msg, GeminiErrorType.UNKNOWN, 0)


# 독립 실행 테스트
if __name__ == "__main__":
    import os

    print("=== GeminiService 모듈 테스트 ===\n")

    # API 키 확인
    api_key = os.environ.get('GEMINI_API_KEY', '')

    if not api_key:
        print("테스트를 위해 GEMINI_API_KEY 환경변수를 설정하세요.")
        print("또는 아래 코드에서 직접 API 키를 입력하세요.\n")

        # 직접 입력 테스트용
        api_key = input("Gemini API Key 입력 (Enter로 스킵): ").strip()

        if not api_key:
            print("\nAPI 키 없이 모듈 구조만 테스트합니다.")
            print("- GeminiService 클래스: 정의됨")
            print("- BlogContent 데이터클래스: 정의됨")
            print("- GeminiServiceError 예외: 정의됨")
            exit(0)

    try:
        service = GeminiService(api_key=api_key)

        print("\n사용 가능한 모델 목록:")
        for model in service.get_available_models():
            print(f"  - {model}")

        # 1. 연결 테스트
        print("\n1. API 연결 테스트")
        connected = service.test_connection()
        print(f"   결과: {'성공' if connected else '실패'}")
        print(f"   사용 모델: {service.get_working_model()}\n")

        if not connected:
            print("API 연결 실패. 키를 확인해주세요.")
            exit(1)

        # 2. 제목 제안 테스트
        print("2. 제목 제안 테스트")
        titles = service.generate_title_suggestions("파이썬 자동화", count=3)
        for i, title in enumerate(titles, 1):
            print(f"   {i}. {title}")
        print()

        # 3. 이미지 프롬프트 테스트
        print("3. 이미지 프롬프트 생성 테스트")
        image_prompt = service.generate_image_prompt("파이썬 자동화")
        print(f"   프롬프트: {image_prompt[:100]}...\n")

        # 4. 블로그 글 생성 테스트 (시간이 걸림)
        print("4. 블로그 글 생성 테스트 (시간 소요)")
        blog = service.generate_blog_post(
            topic="파이썬으로 업무 자동화하기",
            category="IT/테크",
            keywords=["파이썬", "자동화", "업무효율"],
            use_emoji=True
        )
        print(f"   제목: {blog.title}")
        print(f"   태그: {', '.join(blog.tags)}")
        print(f"   글 길이: {len(blog.content)}자")
        print(f"   미리보기: {blog.summary[:100]}...\n")

        print("=== 모든 테스트 완료 ===")
        print(f"최종 사용 모델: {service.get_working_model()}")

    except GeminiServiceError as e:
        print(f"Gemini 서비스 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
