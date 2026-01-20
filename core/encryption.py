"""
암호화 모듈 - 비밀번호 및 API 키 암호화

사용 예시:
    from core.encryption import Encryption

    enc = Encryption()
    encrypted = enc.encrypt("my_secret_password")
    decrypted = enc.decrypt(encrypted)
    print(decrypted)  # "my_secret_password"
"""

import os
import base64
import secrets
import hashlib
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Encryption:
    """암호화/복호화 클래스 (Fernet 기반)"""

    def __init__(self, key_file: str = "data/.key"):
        """
        Args:
            key_file: 암호화 키 저장 파일 경로
        """
        self.key_file = key_file
        self._fernet: Optional[Fernet] = None
        self._init_key()

    def _init_key(self):
        """암호화 키 초기화 또는 로드"""
        key_dir = os.path.dirname(self.key_file)

        if os.path.exists(self.key_file):
            # 기존 키 로드
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                self._fernet = Fernet(key)
            except Exception:
                # 키 파일이 손상된 경우 새로 생성
                self._create_new_key(key_dir)
        else:
            # 새 키 생성
            self._create_new_key(key_dir)

    def _create_new_key(self, key_dir: str):
        """새 암호화 키 생성 및 저장"""
        if key_dir:
            os.makedirs(key_dir, exist_ok=True)

        key = Fernet.generate_key()

        with open(self.key_file, 'wb') as f:
            f.write(key)

        self._fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """
        문자열 암호화

        Args:
            data: 암호화할 문자열

        Returns:
            암호화된 문자열 (base64 인코딩)
        """
        if not data:
            return ""

        try:
            encrypted = self._fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise EncryptionError(f"암호화 실패: {e}")

    def decrypt(self, encrypted_data: str) -> str:
        """
        암호화된 문자열 복호화

        Args:
            encrypted_data: 복호화할 문자열

        Returns:
            복호화된 원본 문자열
        """
        if not encrypted_data:
            return ""

        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise EncryptionError("복호화 실패: 잘못된 키 또는 손상된 데이터")
        except Exception as e:
            raise EncryptionError(f"복호화 실패: {e}")

    def is_encrypted(self, data: str) -> bool:
        """데이터가 암호화되어 있는지 확인"""
        if not data:
            return False

        try:
            decoded = base64.urlsafe_b64decode(data.encode('utf-8'))
            self._fernet.decrypt(decoded)
            return True
        except Exception:
            return False

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """
        비밀번호 해싱 (단방향, 검증용)

        Args:
            password: 해싱할 비밀번호
            salt: 솔트 (없으면 자동 생성)

        Returns:
            (해시값, 솔트) 튜플
        """
        if salt is None:
            salt = secrets.token_bytes(32)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )

        key = kdf.derive(password.encode('utf-8'))
        hash_value = base64.urlsafe_b64encode(key).decode('utf-8')
        salt_str = base64.urlsafe_b64encode(salt).decode('utf-8')

        return hash_value, salt_str

    @staticmethod
    def verify_password(password: str, hash_value: str, salt_str: str) -> bool:
        """
        비밀번호 검증

        Args:
            password: 검증할 비밀번호
            hash_value: 저장된 해시값
            salt_str: 저장된 솔트

        Returns:
            일치 여부
        """
        try:
            salt = base64.urlsafe_b64decode(salt_str.encode('utf-8'))
            new_hash, _ = Encryption.hash_password(password, salt)
            return secrets.compare_digest(new_hash, hash_value)
        except Exception:
            return False


class EncryptionError(Exception):
    """암호화 관련 예외"""
    pass


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== Encryption 모듈 테스트 ===\n")

    # 테스트용 임시 키 파일
    test_key_file = "data/.test_key"

    try:
        enc = Encryption(key_file=test_key_file)

        # 1. 암호화/복호화 테스트
        print("1. 암호화/복호화 테스트")
        original = "my_secret_password_123!"
        encrypted = enc.encrypt(original)
        decrypted = enc.decrypt(encrypted)

        print(f"   원본: {original}")
        print(f"   암호화: {encrypted[:50]}...")
        print(f"   복호화: {decrypted}")
        print(f"   결과: {'성공' if original == decrypted else '실패'}\n")

        # 2. 빈 문자열 테스트
        print("2. 빈 문자열 테스트")
        empty_encrypted = enc.encrypt("")
        empty_decrypted = enc.decrypt("")
        print(f"   빈 문자열 암호화: '{empty_encrypted}'")
        print(f"   빈 문자열 복호화: '{empty_decrypted}'")
        print(f"   결과: {'성공' if empty_encrypted == '' and empty_decrypted == '' else '실패'}\n")

        # 3. 한글 테스트
        print("3. 한글 암호화 테스트")
        korean = "안녕하세요! 테스트입니다."
        korean_encrypted = enc.encrypt(korean)
        korean_decrypted = enc.decrypt(korean_encrypted)
        print(f"   원본: {korean}")
        print(f"   복호화: {korean_decrypted}")
        print(f"   결과: {'성공' if korean == korean_decrypted else '실패'}\n")

        # 4. 암호화 여부 확인 테스트
        print("4. 암호화 여부 확인 테스트")
        print(f"   암호화된 데이터: {enc.is_encrypted(encrypted)}")
        print(f"   일반 문자열: {enc.is_encrypted('plain_text')}\n")

        # 5. 비밀번호 해싱 테스트
        print("5. 비밀번호 해싱 테스트")
        password = "user_password"
        hash_val, salt = Encryption.hash_password(password)
        verify_result = Encryption.verify_password(password, hash_val, salt)
        wrong_verify = Encryption.verify_password("wrong_password", hash_val, salt)

        print(f"   비밀번호: {password}")
        print(f"   해시: {hash_val[:30]}...")
        print(f"   올바른 비밀번호 검증: {verify_result}")
        print(f"   잘못된 비밀번호 검증: {wrong_verify}")
        print(f"   결과: {'성공' if verify_result and not wrong_verify else '실패'}\n")

        print("=== 모든 테스트 완료 ===")

    finally:
        # 테스트 키 파일 정리
        if os.path.exists(test_key_file):
            os.remove(test_key_file)
