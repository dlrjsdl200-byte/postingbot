"""
PyInstaller 빌드 스크립트
"""

import os
import subprocess
import sys


def build():
    """exe 파일 빌드"""
    print("NaverBlogPoster 빌드 시작...")

    # PyInstaller 명령어
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=NaverBlogPoster",
        "--onefile",
        "--windowed",
        "--add-data=data;data",
        "--add-data=assets;assets",
        "--hidden-import=customtkinter",
        "--hidden-import=google.generativeai",
        "--hidden-import=selenium",
        "--hidden-import=PIL",
        "--collect-all=customtkinter",
        "main.py"
    ]

    # 아이콘 파일이 있으면 추가
    if os.path.exists("assets/icon.ico"):
        cmd.insert(-1, "--icon=assets/icon.ico")

    try:
        subprocess.run(cmd, check=True)
        print("\n빌드 완료!")
        print("실행 파일 위치: dist/NaverBlogPoster.exe")
    except subprocess.CalledProcessError as e:
        print(f"빌드 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()
