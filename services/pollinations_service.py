"""
Pollinations.ai 이미지 생성 서비스 (무료)

사용 예시:
    from services.pollinations_service import PollinationsService

    service = PollinationsService()

    # 이미지 생성
    image_path = service.generate_image(
        prompt="A beautiful sunset over mountains",
        filename="sunset.png"
    )
"""

import os
import time
import hashlib
import requests
from typing import Optional, Callable
from urllib.parse import quote
from dataclasses import dataclass


@dataclass
class ImageResult:
    """이미지 생성 결과"""
    path: str
    url: str
    prompt: str
    width: int
    height: int


class PollinationsService:
    """Pollinations.ai 이미지 생성 서비스"""

    BASE_URL = "https://image.pollinations.ai/prompt"

    # 기본 설정
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 768
    DEFAULT_MODEL = "flux"  # flux, turbo 등

    def __init__(
        self,
        save_dir: str = "data/images",
        logger: Optional[Callable] = None
    ):
        """
        Args:
            save_dir: 이미지 저장 디렉토리
            logger: 로그 출력 함수
        """
        self.save_dir = save_dir
        self.logger = logger or print

        # 저장 디렉토리 생성
        os.makedirs(save_dir, exist_ok=True)

    def generate_image(
        self,
        prompt: str,
        filename: Optional[str] = None,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        model: str = DEFAULT_MODEL,
        seed: Optional[int] = None,
        enhance: bool = True,
        nologo: bool = True
    ) -> ImageResult:
        """
        이미지 생성

        Args:
            prompt: 이미지 설명 (영어 권장)
            filename: 저장할 파일명 (없으면 자동 생성)
            width: 이미지 너비
            height: 이미지 높이
            model: 사용할 모델
            seed: 랜덤 시드 (재현성용)
            enhance: 프롬프트 자동 개선
            nologo: 워터마크 제거

        Returns:
            ImageResult 객체
        """
        # 프롬프트 URL 인코딩
        encoded_prompt = quote(prompt)

        # URL 파라미터 구성
        params = [
            f"width={width}",
            f"height={height}",
            f"model={model}",
        ]

        if seed is not None:
            params.append(f"seed={seed}")
        if enhance:
            params.append("enhance=true")
        if nologo:
            params.append("nologo=true")

        # 캐시 방지를 위한 타임스탬프
        params.append(f"t={int(time.time())}")

        url = f"{self.BASE_URL}/{encoded_prompt}?{'&'.join(params)}"

        self.logger(f"이미지 생성 중: {prompt[:50]}...")

        try:
            # 이미지 요청
            response = requests.get(url, timeout=120)
            response.raise_for_status()

            # 파일명 생성
            if not filename:
                prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
                filename = f"image_{prompt_hash}_{int(time.time())}.png"

            # 확장자 확인
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filename += '.png'

            # 파일 저장
            filepath = os.path.join(self.save_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)

            self.logger(f"이미지 저장 완료: {filepath}")

            return ImageResult(
                path=filepath,
                url=url,
                prompt=prompt,
                width=width,
                height=height
            )

        except requests.Timeout:
            raise PollinationsServiceError("이미지 생성 시간 초과 (120초)")
        except requests.RequestException as e:
            raise PollinationsServiceError(f"이미지 다운로드 실패: {e}")
        except IOError as e:
            raise PollinationsServiceError(f"이미지 저장 실패: {e}")

    def generate_blog_header(
        self,
        topic: str,
        style: str = "modern minimalist blog header"
    ) -> ImageResult:
        """
        블로그 헤더 이미지 생성

        Args:
            topic: 블로그 주제
            style: 이미지 스타일

        Returns:
            ImageResult 객체
        """
        prompt = f"{topic}, {style}, professional, high quality, no text"
        return self.generate_image(
            prompt=prompt,
            width=1200,
            height=630  # 블로그 최적 비율
        )

    def generate_thumbnail(
        self,
        topic: str,
        style: str = "eye-catching thumbnail"
    ) -> ImageResult:
        """
        썸네일 이미지 생성

        Args:
            topic: 주제
            style: 스타일

        Returns:
            ImageResult 객체
        """
        prompt = f"{topic}, {style}, vibrant colors, clean design, no text"
        return self.generate_image(
            prompt=prompt,
            width=800,
            height=800  # 정사각형
        )

    def generate_with_korean_topic(
        self,
        korean_topic: str,
        additional_style: str = ""
    ) -> ImageResult:
        """
        한국어 주제로 이미지 생성 (자동 번역)

        Args:
            korean_topic: 한국어 주제
            additional_style: 추가 스타일

        Returns:
            ImageResult 객체
        """
        # 간단한 주제-영어 매핑 (실제로는 번역 API 사용 권장)
        topic_map = {
            "맛집": "delicious food restaurant",
            "여행": "beautiful travel destination",
            "카페": "cozy cafe interior",
            "요리": "home cooking food",
            "운동": "fitness exercise",
            "독서": "reading books",
            "음악": "music instruments",
            "영화": "cinema movie",
            "패션": "fashion style",
            "뷰티": "beauty cosmetics",
            "육아": "parenting family",
            "반려동물": "cute pets",
            "자기계발": "personal development growth",
            "재테크": "financial investment money",
            "IT": "technology digital",
            "건강": "health wellness",
        }

        # 매핑된 주제 찾기
        english_topic = korean_topic
        for kr, en in topic_map.items():
            if kr in korean_topic:
                english_topic = en
                break

        prompt = f"{english_topic}, {additional_style}, modern blog image, professional quality, no text"
        return self.generate_image(prompt=prompt)

    def test_connection(self) -> bool:
        """
        서비스 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            test_url = f"{self.BASE_URL}/test?width=64&height=64"
            response = requests.head(test_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> list:
        """사용 가능한 모델 목록"""
        return ["flux", "turbo", "flux-realism", "flux-anime", "flux-3d"]

    def clear_cache(self, older_than_days: int = 7) -> int:
        """
        오래된 캐시 이미지 삭제

        Args:
            older_than_days: 며칠 이상 된 파일 삭제

        Returns:
            삭제된 파일 수
        """
        import glob

        deleted = 0
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)

        for filepath in glob.glob(os.path.join(self.save_dir, "image_*.png")):
            if os.path.getmtime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                    deleted += 1
                except OSError:
                    pass

        self.logger(f"캐시 정리 완료: {deleted}개 파일 삭제")
        return deleted


class PollinationsServiceError(Exception):
    """Pollinations 서비스 예외"""
    pass


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== PollinationsService 모듈 테스트 ===\n")

    # 테스트용 디렉토리
    test_dir = "data/test_images"

    try:
        service = PollinationsService(save_dir=test_dir)

        # 1. 연결 테스트
        print("1. 서비스 연결 테스트")
        connected = service.test_connection()
        print(f"   결과: {'성공' if connected else '실패'}\n")

        # 2. 사용 가능한 모델 확인
        print("2. 사용 가능한 모델")
        models = service.get_available_models()
        print(f"   모델: {', '.join(models)}\n")

        # 3. 기본 이미지 생성 테스트
        print("3. 기본 이미지 생성 테스트")
        result = service.generate_image(
            prompt="A serene mountain landscape at sunset, peaceful atmosphere",
            width=512,
            height=512
        )
        print(f"   저장 경로: {result.path}")
        print(f"   크기: {result.width}x{result.height}")
        print(f"   URL: {result.url[:80]}...\n")

        # 4. 블로그 헤더 생성 테스트
        print("4. 블로그 헤더 생성 테스트")
        header = service.generate_blog_header(
            topic="Python programming automation"
        )
        print(f"   저장 경로: {header.path}")
        print(f"   크기: {header.width}x{header.height}\n")

        # 5. 한국어 주제 테스트
        print("5. 한국어 주제 이미지 생성 테스트")
        korean_result = service.generate_with_korean_topic(
            korean_topic="맛집 카페",
            additional_style="warm cozy atmosphere"
        )
        print(f"   저장 경로: {korean_result.path}\n")

        print("=== 모든 테스트 완료 ===")
        print(f"\n생성된 이미지 위치: {test_dir}/")

        # 테스트 후 정리 여부 확인
        cleanup = input("\n테스트 이미지를 삭제할까요? (y/N): ").strip().lower()
        if cleanup == 'y':
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
            print("테스트 이미지 삭제 완료")

    except PollinationsServiceError as e:
        print(f"Pollinations 서비스 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
