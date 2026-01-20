"""
URL 크롤링 서비스 - 웹 페이지 내용 추출

사용 예시:
    from services.url_crawler import UrlCrawler

    crawler = UrlCrawler()
    result = crawler.crawl("https://example.com/article")
    print(result.title)
    print(result.content)
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Callable, List
from dataclasses import dataclass
from urllib.parse import urlparse
import re


@dataclass
class CrawlResult:
    """크롤링 결과"""
    url: str
    title: str
    content: str
    summary: str
    keywords: List[str]
    success: bool
    error_message: Optional[str] = None


class UrlCrawler:
    """URL 크롤링 서비스"""

    # 요청 타임아웃
    TIMEOUT = 10

    # User-Agent (봇 차단 우회)
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    # 제거할 태그들
    REMOVE_TAGS = ['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']

    def __init__(self, logger: Optional[Callable] = None):
        """
        Args:
            logger: 로그 출력 함수
        """
        self.logger = logger or print

    def crawl(self, url: str) -> CrawlResult:
        """
        URL에서 내용 추출

        Args:
            url: 크롤링할 URL

        Returns:
            CrawlResult 객체
        """
        try:
            # URL 유효성 검사
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return CrawlResult(
                    url=url,
                    title="",
                    content="",
                    summary="",
                    keywords=[],
                    success=False,
                    error_message="유효하지 않은 URL입니다."
                )

            self.logger(f"URL 크롤링 중: {url}")

            # HTTP 요청
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()

            # 인코딩 처리
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding

            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            # 제목 추출
            title = self._extract_title(soup)

            # 본문 추출
            content = self._extract_content(soup)

            # 요약 생성
            summary = self._generate_summary(content)

            # 키워드 추출
            keywords = self._extract_keywords(soup, content)

            self.logger(f"크롤링 완료: {title[:50]}...")

            return CrawlResult(
                url=url,
                title=title,
                content=content,
                summary=summary,
                keywords=keywords,
                success=True
            )

        except requests.exceptions.Timeout:
            return CrawlResult(
                url=url,
                title="",
                content="",
                summary="",
                keywords=[],
                success=False,
                error_message="요청 시간이 초과되었습니다."
            )

        except requests.exceptions.RequestException as e:
            return CrawlResult(
                url=url,
                title="",
                content="",
                summary="",
                keywords=[],
                success=False,
                error_message=f"URL 요청 실패: {str(e)[:100]}"
            )

        except Exception as e:
            return CrawlResult(
                url=url,
                title="",
                content="",
                summary="",
                keywords=[],
                success=False,
                error_message=f"크롤링 오류: {str(e)[:100]}"
            )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """제목 추출"""
        # 우선순위: og:title > title > h1
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()

        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)

        return ""

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """본문 내용 추출"""
        # 불필요한 태그 제거
        for tag in soup.find_all(self.REMOVE_TAGS):
            tag.decompose()

        # 본문 영역 찾기 (우선순위)
        content_selectors = [
            # 네이버 블로그
            ('div', {'class': 'se-main-container'}),
            ('div', {'id': 'postViewArea'}),
            ('div', {'class': 'post-view'}),
            # 일반 블로그/뉴스
            ('article', {}),
            ('div', {'class': re.compile(r'(content|article|post|entry|body)', re.I)}),
            ('div', {'id': re.compile(r'(content|article|post|entry|body)', re.I)}),
            ('main', {}),
        ]

        content_text = ""

        for tag_name, attrs in content_selectors:
            elements = soup.find_all(tag_name, attrs)
            for elem in elements:
                text = elem.get_text(separator='\n', strip=True)
                if len(text) > len(content_text):
                    content_text = text

        # 본문을 찾지 못한 경우 body 전체 텍스트
        if not content_text or len(content_text) < 100:
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator='\n', strip=True)

        # 정리
        content_text = self._clean_text(content_text)

        return content_text

    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 연속 공백/줄바꿈 정리
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\t+', ' ', text)

        # 빈 줄 정리
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        # 최대 길이 제한 (5000자)
        if len(text) > 5000:
            text = text[:5000] + "..."

        return text

    def _generate_summary(self, content: str, max_length: int = 300) -> str:
        """요약 생성"""
        # 첫 몇 문장 추출
        sentences = re.split(r'[.!?]\s+', content)
        summary = ""

        for sentence in sentences:
            if len(summary) + len(sentence) > max_length:
                break
            summary += sentence + ". "

        return summary.strip()

    def _extract_keywords(self, soup: BeautifulSoup, content: str) -> List[str]:
        """키워드 추출"""
        keywords = []

        # meta keywords
        meta_keywords = soup.find('meta', {'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords.extend([k.strip() for k in meta_keywords['content'].split(',')])

        # og:keywords 또는 article:tag
        for meta in soup.find_all('meta', property=re.compile(r'(keywords|tag)', re.I)):
            if meta.get('content'):
                keywords.extend([k.strip() for k in meta['content'].split(',')])

        # 태그 클래스에서 추출
        tag_selectors = [
            ('a', {'class': re.compile(r'tag', re.I)}),
            ('span', {'class': re.compile(r'tag', re.I)}),
        ]

        for tag_name, attrs in tag_selectors:
            for elem in soup.find_all(tag_name, attrs):
                tag_text = elem.get_text(strip=True)
                if tag_text and len(tag_text) < 30:
                    keywords.append(tag_text.replace('#', ''))

        # 중복 제거 및 정리
        keywords = list(dict.fromkeys(keywords))  # 순서 유지하며 중복 제거
        keywords = [k for k in keywords if k and len(k) > 1]

        return keywords[:10]  # 최대 10개

    def crawl_multiple(self, urls: List[str]) -> List[CrawlResult]:
        """
        여러 URL 크롤링

        Args:
            urls: URL 리스트

        Returns:
            CrawlResult 리스트
        """
        results = []
        for url in urls:
            result = self.crawl(url)
            results.append(result)

        return results


class UrlCrawlerError(Exception):
    """URL 크롤러 예외"""
    pass


# 독립 실행 테스트
if __name__ == "__main__":
    print("=== UrlCrawler 모듈 테스트 ===\n")

    crawler = UrlCrawler()

    test_url = input("테스트할 URL 입력: ").strip()

    if test_url:
        result = crawler.crawl(test_url)

        print(f"\n성공: {result.success}")
        if result.success:
            print(f"제목: {result.title}")
            print(f"키워드: {', '.join(result.keywords)}")
            print(f"요약: {result.summary[:200]}...")
            print(f"본문 길이: {len(result.content)}자")
        else:
            print(f"오류: {result.error_message}")
    else:
        print("URL이 입력되지 않았습니다.")
