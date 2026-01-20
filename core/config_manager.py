"""
설정 관리자 - 설정 저장/불러오기 (암호화 포함)

사용 예시:
    from core.config_manager import ConfigManager

    manager = ConfigManager()

    # 설정 저장
    manager.save_config({
        'naver_id': 'my_id',
        'naver_pw': 'my_password',
        'gemini_api_key': 'API_KEY',
        'category': 'IT/테크',
        'keywords': '파이썬, 프로그래밍',
        'use_image': True,
        'use_emoji': True
    })

    # 설정 불러오기
    config = manager.load_config()
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field

from .encryption import Encryption, EncryptionError


@dataclass
class AppConfig:
    """앱 설정 데이터 클래스"""
    # 네이버 계정
    naver_id: str = ""
    naver_pw: str = ""

    # API 키
    gemini_api_key: str = ""

    # 포스팅 설정
    category: str = "직접입력"
    keywords: str = ""
    use_image: bool = True
    use_emoji: bool = True

    # 고급 설정
    post_delay: int = 5  # 포스팅 간 대기 시간 (초)
    max_retries: int = 3  # 재시도 횟수
    headless_browser: bool = False  # 브라우저 숨김 모드

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """딕셔너리에서 생성"""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class ConfigManager:
    """설정 저장/로드 관리 클래스"""

    # 암호화 대상 필드
    SENSITIVE_FIELDS = ['naver_pw', 'gemini_api_key']

    def __init__(
        self,
        config_file: str = "data/config.json",
        key_file: str = "data/.key"
    ):
        """
        Args:
            config_file: 설정 파일 경로
            key_file: 암호화 키 파일 경로
        """
        self.config_file = config_file
        self.encryption = Encryption(key_file=key_file)

    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        설정 저장 (민감 정보 암호화)

        Args:
            config: 저장할 설정 딕셔너리

        Returns:
            성공 여부
        """
        try:
            # AppConfig로 유효성 검증
            app_config = AppConfig.from_dict(config)
            config_dict = app_config.to_dict()

            # 민감한 데이터 암호화
            encrypted_config = config_dict.copy()
            for field in self.SENSITIVE_FIELDS:
                if field in encrypted_config and encrypted_config[field]:
                    encrypted_config[field] = self.encryption.encrypt(encrypted_config[field])

            # 디렉토리 생성
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)

            # 파일 저장
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_config, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"설정 저장 실패: {e}")
            return False

    def load_config(self) -> Optional[Dict[str, Any]]:
        """
        설정 불러오기 (복호화 포함)

        Returns:
            설정 딕셔너리 또는 None
        """
        try:
            if not os.path.exists(self.config_file):
                return None

            with open(self.config_file, 'r', encoding='utf-8') as f:
                encrypted_config = json.load(f)

            # 민감한 데이터 복호화
            config = encrypted_config.copy()
            for field in self.SENSITIVE_FIELDS:
                if field in config and config[field]:
                    try:
                        config[field] = self.encryption.decrypt(config[field])
                    except EncryptionError:
                        # 복호화 실패 시 빈 문자열
                        config[field] = ""

            return config

        except json.JSONDecodeError:
            print("설정 파일 형식 오류")
            return None
        except Exception as e:
            print(f"설정 로드 실패: {e}")
            return None

    def load_config_as_dataclass(self) -> AppConfig:
        """
        설정을 AppConfig 데이터클래스로 불러오기

        Returns:
            AppConfig 인스턴스
        """
        config = self.load_config()
        if config:
            return AppConfig.from_dict(config)
        return AppConfig()

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        특정 설정 값 가져오기

        Args:
            key: 설정 키
            default: 기본값

        Returns:
            설정 값 또는 기본값
        """
        config = self.load_config()
        if config:
            return config.get(key, default)
        return default

    def set_value(self, key: str, value: Any) -> bool:
        """
        특정 설정 값 저장하기

        Args:
            key: 설정 키
            value: 설정 값

        Returns:
            성공 여부
        """
        config = self.load_config() or {}
        config[key] = value
        return self.save_config(config)

    def delete_config(self) -> bool:
        """
        설정 파일 삭제

        Returns:
            성공 여부
        """
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            return True
        except Exception as e:
            print(f"설정 삭제 실패: {e}")
            return False

    def config_exists(self) -> bool:
        """설정 파일 존재 여부"""
        return os.path.exists(self.config_file)

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        설정 유효성 검사

        Args:
            config: 검사할 설정

        Returns:
            오류 메시지 리스트 (비어있으면 유효)
        """
        errors = []

        if not config.get('naver_id'):
            errors.append("네이버 ID가 필요합니다.")

        if not config.get('naver_pw'):
            errors.append("네이버 비밀번호가 필요합니다.")

        if not config.get('gemini_api_key'):
            errors.append("Gemini API Key가 필요합니다.")

        return errors

    def export_config(self, export_path: str, include_sensitive: bool = False) -> bool:
        """
        설정 내보내기 (백업용)

        Args:
            export_path: 내보낼 파일 경로
            include_sensitive: 민감 정보 포함 여부

        Returns:
            성공 여부
        """
        try:
            config = self.load_config()
            if not config:
                return False

            if not include_sensitive:
                for field in self.SENSITIVE_FIELDS:
                    config[field] = ""

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"설정 내보내기 실패: {e}")
            return False

    def import_config(self, import_path: str) -> bool:
        """
        설정 가져오기

        Args:
            import_path: 가져올 파일 경로

        Returns:
            성공 여부
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            return self.save_config(config)
        except Exception as e:
            print(f"설정 가져오기 실패: {e}")
            return False


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== ConfigManager 모듈 테스트 ===\n")

    # 테스트용 파일 경로
    test_config_file = "data/.test_config.json"
    test_key_file = "data/.test_config_key"

    try:
        manager = ConfigManager(
            config_file=test_config_file,
            key_file=test_key_file
        )

        # 1. 설정 저장 테스트
        print("1. 설정 저장 테스트")
        test_config = {
            'naver_id': 'test_user',
            'naver_pw': 'test_password_123!',
            'gemini_api_key': 'AIzaSyTest123456789',
            'category': 'IT/테크',
            'keywords': '파이썬, 자동화',
            'use_image': True,
            'use_emoji': False
        }
        save_result = manager.save_config(test_config)
        print(f"   저장 결과: {'성공' if save_result else '실패'}\n")

        # 2. 설정 불러오기 테스트
        print("2. 설정 불러오기 테스트")
        loaded_config = manager.load_config()
        print(f"   네이버 ID: {loaded_config.get('naver_id')}")
        print(f"   비밀번호 복호화: {loaded_config.get('naver_pw')}")
        print(f"   API 키 복호화: {loaded_config.get('gemini_api_key')[:10]}...")
        print(f"   카테고리: {loaded_config.get('category')}")
        match = (
            loaded_config.get('naver_id') == test_config['naver_id'] and
            loaded_config.get('naver_pw') == test_config['naver_pw']
        )
        print(f"   결과: {'성공' if match else '실패'}\n")

        # 3. 파일 암호화 확인
        print("3. 파일 내 암호화 확인")
        with open(test_config_file, 'r', encoding='utf-8') as f:
            raw_config = json.load(f)
        print(f"   저장된 비밀번호: {raw_config.get('naver_pw')[:30]}...")
        is_encrypted = raw_config.get('naver_pw') != test_config['naver_pw']
        print(f"   암호화 여부: {'예' if is_encrypted else '아니오'}\n")

        # 4. 데이터클래스 로드 테스트
        print("4. AppConfig 데이터클래스 테스트")
        app_config = manager.load_config_as_dataclass()
        print(f"   타입: {type(app_config).__name__}")
        print(f"   use_image: {app_config.use_image}")
        print(f"   post_delay (기본값): {app_config.post_delay}\n")

        # 5. 유효성 검사 테스트
        print("5. 유효성 검사 테스트")
        errors = manager.validate_config({'naver_id': '', 'naver_pw': 'test'})
        print(f"   빈 ID 검사: {errors}\n")

        # 6. 개별 값 조회/설정 테스트
        print("6. 개별 값 조회/설정 테스트")
        manager.set_value('custom_key', 'custom_value')
        custom = manager.get_value('custom_key')
        print(f"   커스텀 키 저장/조회: {custom}\n")

        print("=== 모든 테스트 완료 ===")

    finally:
        # 테스트 파일 정리
        for f in [test_config_file, test_key_file]:
            if os.path.exists(f):
                os.remove(f)
