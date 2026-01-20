"""
PyInstaller 빌드 스크립트
"""

import os
import subprocess
import sys


def build():
    """exe 파일 빌드"""
    print("=" * 50)
    print("NaverBlogPoster 빌드 시작...")
    print("=" * 50)

    # data, assets 폴더 생성 (없으면)
    os.makedirs("data", exist_ok=True)
    os.makedirs("assets", exist_ok=True)

    # PyInstaller 명령어
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=NaverBlogPoster",
        "--onefile",
        "--windowed",
        "--noconfirm",
        # Hidden imports
        "--hidden-import=customtkinter",
        "--hidden-import=google.generativeai",
        "--hidden-import=selenium",
        "--hidden-import=selenium.webdriver",
        "--hidden-import=selenium.webdriver.chrome",
        "--hidden-import=selenium.webdriver.chrome.service",
        "--hidden-import=selenium.webdriver.chrome.options",
        "--hidden-import=webdriver_manager",
        "--hidden-import=webdriver_manager.chrome",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=cryptography",
        "--hidden-import=cryptography.fernet",
        "--hidden-import=requests",
        "--hidden-import=bs4",
        "--hidden-import=pyperclip",
        # Collect all for customtkinter (has assets)
        "--collect-all=customtkinter",
        # Main script
        "main.py"
    ]

    # 아이콘 파일이 있으면 추가
    if os.path.exists("assets/icon.ico"):
        cmd.insert(-1, "--icon=assets/icon.ico")

    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 50)
        print("빌드 완료!")
        print("=" * 50)
        print(f"\n실행 파일 위치: {os.path.abspath('dist/NaverBlogPoster.exe')}")
        print("\n주의: 첫 실행 시 Windows Defender가 검사할 수 있습니다.")
    except subprocess.CalledProcessError as e:
        print(f"\n빌드 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()
