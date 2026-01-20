# CLAUDE.md - NaverBlogPoster

## 프로젝트 개요
네이버 블로그 자동 포스팅 Desktop App (.exe)
- GUI: customtkinter
- LLM: Gemini 1.5 Flash (무료)
- 이미지: Pollinations.ai (무료)
- 포스팅: Selenium (네이버 로그인)

## 핵심 명령어
- python main.py : 앱 실행
- python build.py : .exe 빌드
- pip install -r requirements.txt : 의존성 설치

## 구조
- main.py: 진입점
- gui/app.py: 메인 GUI (customtkinter)
- gui/frames/: 각 UI 섹션
- core/config_manager.py: 설정 저장/로드 (암호화)
- core/posting_engine.py: 포스팅 메인 로직
- agents/: 트렌드, 콘텐츠, 이미지, 포스팅 에이전트
- services/: Gemini, Pollinations, Naver API 래퍼

## GUI 입력 필드
1. 네이버 ID/PW
2. Gemini API Key
3. 주제 카테고리 (드롭다운)
4. 세부 키워드
5. 옵션 체크박스 (이미지, 이모지)
6. 저장/실행 버튼

## 워크플로우
1. 트렌드 수집 → 2. 주제 선정 → 3. 글 작성 (Gemini)
→ 4. 이미지 생성 (Pollinations) → 5. 네이버 포스팅 (Selenium)

## 주요 의존성
customtkinter, google-generativeai, selenium, webdriver-manager,
beautifulsoup4, requests, Pillow, cryptography, pyinstaller

## 보안
- 비밀번호/API키: cryptography로 암호화 저장
- 설정파일: data/config.json

## 개발 규칙
- 모든 API 호출은 try-except 처리
- Gemini Rate Limit: 분당 15요청
- 로그는 GUI log_frame에 실시간 출력
- 포스팅 실행은 별도 스레드에서 처리
