"""
NaverBlogPoster - 네이버 블로그 자동 포스팅 앱
메인 진입점
"""

import sys
import os

# 실행 파일 경로 설정 (PyInstaller 호환)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from gui.app import NaverBlogPosterApp


def main():
    """앱 실행"""
    app = NaverBlogPosterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
