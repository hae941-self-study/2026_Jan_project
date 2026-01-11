"""
인스티즈 (Instiz) 트렌드 크롤링
- 인기 게시물에서 키워드 추출
- 실시간 이슈 분석
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
from collections import Counter
from typing import List, Dict
import json
import csv
from datetime import datetime
import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class InstizCrawler:
    """인스티즈 크롤러"""

    def __init__(self):
        """초기화"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.base_url = 'https://www.instiz.net'

    def get_ichart_trends(self, max_items: int = 50) -> List[Dict]:
        """
        인스티즈 아이차트 (실시간 차트) 가져오기

        Args:
            max_items: 수집할 항목 수

        Returns:
            차트 항목 리스트
        """
        # 여러 URL 시도
        urls_to_try = [
            f'{self.base_url}/pt',  # 전체 게시판
            f'{self.base_url}/pt/0',  # 인기글
            'https://www.instiz.net/name',  # 네임드
        ]

        for url in urls_to_try:
            try:
                print(f"   시도 중: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                response.encoding = 'utf-8'

                soup = BeautifulSoup(response.text, 'html.parser')
                items = []

                # 여러 선택자 시도
                selectors = [
                    '.postBtn',
                    '.post-list-item',
                    'tr.tr',
                    '.list-item',
                    'a[class*="subject"]',
                    'td.subject',
                    '.sbj'
                ]

                posts = []
                for selector in selectors:
                    posts = soup.select(selector)
                    if posts:
                        print(f"   ✓ 선택자 '{selector}' 발견: {len(posts)}개")
                        break

                if not posts:
                    print(f"   ✗ 게시물을 찾지 못함")
                    # 디버그: HTML 일부 출력
                    # print(f"   HTML 샘플: {soup.prettify()[:500]}")
                    continue

                for post in posts[:max_items]:
                    try:
                        # 여러 방법으로 제목 추출 시도
                        title = None

                        # 방법 1: .title 클래스
                        title_elem = post.select_one('.title')
                        if title_elem:
                            title = title_elem.text.strip()

                        # 방법 2: a 태그
                        if not title:
                            title_elem = post.select_one('a')
                            if title_elem:
                                title = title_elem.get('title', '') or title_elem.text.strip()

                        # 방법 3: 직접 텍스트
                        if not title:
                            title = post.text.strip()

                        if not title or len(title) < 2:
                            continue

                        # 댓글 수
                        comment_elem = post.select_one('.cmtnum') or post.select_one('[class*="cmt"]')
                        comments = 0
                        if comment_elem:
                            comment_text = comment_elem.text.strip()
                            comment_match = re.search(r'(\d+)', comment_text)
                            if comment_match:
                                comments = int(comment_match.group(1))

                        items.append({
                            'title': title,
                            'comments': comments,
                            'engagement': comments + 1
                        })

                    except Exception as e:
                        continue

                if items:
                    print(f"   ✓ {len(items)}개 게시물 수집 성공")
                    return items

            except requests.exceptions.RequestException as e:
                print(f"   ✗ 실패: {e}")
                continue

        print(f"❌ 모든 URL에서 데이터 수집 실패")
        return []

    def get_board_posts(self, board_id: str, max_pages: int = 5) -> List[Dict]:
        """
        특정 게시판의 게시물 가져오기

        Args:
            board_id: 게시판 ID
            max_pages: 크롤링할 페이지 수

        Returns:
            게시물 리스트
        """
        posts = []

        for page in range(1, max_pages + 1):
            url = f'{self.base_url}/bbs/{board_id}?page={page}'

            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                response.encoding = 'utf-8'

                soup = BeautifulSoup(response.text, 'html.parser')

                # 게시물 목록 파싱
                post_list = soup.select('.postBtn')

                for post in post_list:
                    try:
                        # 제목
                        title_elem = post.select_one('.title')
                        if not title_elem:
                            continue

                        title = title_elem.text.strip()

                        # 댓글 수
                        comment_elem = post.select_one('.cmtnum')
                        comments = 0
                        if comment_elem:
                            comment_text = comment_elem.text.strip()
                            comment_match = re.search(r'(\d+)', comment_text)
                            if comment_match:
                                comments = int(comment_match.group(1))

                        posts.append({
                            'title': title,
                            'comments': comments,
                            'engagement': comments
                        })

                    except Exception as e:
                        continue

                print(f"   페이지 {page}/{max_pages}: {len(post_list)}개 게시물 수집")

                # Rate limit 방지
                time.sleep(random.uniform(1, 2))

            except Exception as e:
                print(f"   ⚠️ 페이지 {page} 수집 실패: {e}")
                continue

        return posts

    def extract_keywords_from_posts(self, posts: List[Dict],
                                   min_length: int = 2) -> List[Dict]:
        """
        게시물에서 키워드 추출

        Args:
            posts: 게시물 리스트
            min_length: 최소 키워드 길이

        Returns:
            키워드와 빈도수
        """
        keyword_counter = Counter()
        keyword_engagement = {}

        # 불용어
        stopwords = {
            '인스티즈', '게시판', '게시글', '공지', '질문', '답변',
            '입니다', '합니다', '있습니다', '없습니다', '가능', '불가능',
            '이거', '저거', '그거', '이게', '저게', '그게',
            '오늘', '어제', '내일', '요즘', '지금', '이제', '그냥',
            '진짜', '정말', '완전', '너무', '엄청', '개', '매우',
            '있다', '없다', '하다', '되다', '이다', '아니다',
            '같다', '듯하다', '보이다', '싶다', '하고', '그리고',
            '또는', '그런데', '하지만', '그러나', '그래서', '때문에',
            '안녕하세요', '감사합니다', '수고하세요', '부탁드립니다'
        }

        for post in posts:
            title = post['title']
            engagement = post.get('engagement', 1)

            # 한글 키워드 추출 (2글자 이상)
            korean_words = re.findall(r'[가-힣]{2,}', title)

            # 영어 키워드 추출 (2글자 이상, 대소문자 구분)
            english_words = re.findall(r'\b[A-Z][a-z]+\b|\b[A-Z]{2,}\b', title)

            # 숫자+텍스트 조합
            mixed_words = re.findall(r'\d+[가-힣]+', title)

            all_words = korean_words + english_words + mixed_words

            for word in all_words:
                # 불용어 제거
                if word.lower() in stopwords or len(word) < min_length:
                    continue

                keyword_counter[word] += 1

                # 인기도 누적
                if word not in keyword_engagement:
                    keyword_engagement[word] = 0
                keyword_engagement[word] += engagement

        # 결과 정리
        keywords = []
        for word, count in keyword_counter.most_common(100):
            keywords.append({
                'keyword': word,
                'count': count,
                'total_engagement': keyword_engagement.get(word, 0),
                'avg_engagement': keyword_engagement.get(word, 0) / count if count > 0 else 0
            })

        return keywords


class InstizTrendAnalyzer:
    """인스티즈 트렌드 분석기"""

    def __init__(self):
        """초기화"""
        self.crawler = InstizCrawler()

    def analyze_ichart(self, max_items: int = 100) -> Dict:
        """
        아이차트 분석

        Args:
            max_items: 수집할 항목 수

        Returns:
            분석 결과
        """
        print(f"\n{'='*60}")
        print(f"📊 인스티즈 실시간 인기글 분석")
        print(f"{'='*60}")

        items = self.crawler.get_ichart_trends(max_items)

        if not items:
            print(f"⚠️ 데이터를 수집하지 못했습니다.")
            return {}

        print(f"📊 총 {len(items)}개 게시물 수집 완료")

        # 키워드 추출
        print(f"🔍 키워드 추출 중...")
        keywords = self.crawler.extract_keywords_from_posts(items)

        print(f"✅ {len(keywords)}개 키워드 추출 완료")

        return {
            'source': '인스티즈 실시간 인기글',
            'total_posts': len(items),
            'keywords': keywords,
            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def analyze_boards(self, boards: List[Dict], max_pages: int = 5) -> Dict:
        """
        여러 게시판 분석

        Args:
            boards: [{'id': 'board_id', 'name': 'board_name'}, ...]
            max_pages: 게시판당 크롤링할 페이지 수

        Returns:
            전체 분석 결과
        """
        results = {}

        for board in boards:
            board_id = board['id']
            board_name = board['name']

            print(f"\n{'='*60}")
            print(f"📱 {board_name} 크롤링 중...")
            print(f"{'='*60}")

            posts = self.crawler.get_board_posts(board_id, max_pages)

            if not posts:
                print(f"⚠️ {board_name}: 게시물을 수집하지 못했습니다.")
                continue

            print(f"📊 총 {len(posts)}개 게시물 수집 완료")

            # 키워드 추출
            print(f"🔍 키워드 추출 중...")
            keywords = self.crawler.extract_keywords_from_posts(posts)

            print(f"✅ {len(keywords)}개 키워드 추출 완료")

            results[board_id] = {
                'board_name': board_name,
                'total_posts': len(posts),
                'keywords': keywords,
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 게시판별 Top 10 출력
            print(f"\n🏆 {board_name} Top 10 키워드:")
            print("-" * 70)
            for i, kw in enumerate(keywords[:10], 1):
                print(f"{i:2d}. {kw['keyword']:20s} | "
                      f"출현: {kw['count']:3d}회 | "
                      f"인기도: {kw['total_engagement']:5d}")

            # 게시판 사이 대기
            time.sleep(random.uniform(2, 3))

        return results

    def save_results(self, results: Dict, filename: str = 'instiz_trends.json'):
        """결과 저장 (JSON)"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과가 {filename}에 저장되었습니다.")

    def save_results_to_csv(self, results: Dict, filename: str = 'instiz_trends.csv'):
        """결과 저장 (CSV)"""
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['출처', '순위', '키워드', '출현횟수', '총_인기도', '평균_인기도'])

            for key, result in results.items():
                source_name = result.get('board_name', result.get('source', key))
                for i, kw in enumerate(result['keywords'], 1):
                    writer.writerow([
                        source_name,
                        i,
                        kw['keyword'],
                        kw['count'],
                        kw.get('total_engagement', 0),
                        round(kw.get('avg_engagement', 0), 2)
                    ])

        print(f"💾 CSV 결과가 {filename}에 저장되었습니다.")


# 실행
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 인스티즈 트렌드 크롤링")
    print("="*80)
    print("\n📊 인스티즈에서 실시간 트렌드를 수집합니다.")
    print("⚠️  크롤링 속도 제한을 준수하며, 공개 게시판만 수집합니다.\n")

    # 분석기 초기화
    analyzer = InstizTrendAnalyzer()

    try:
        # 실시간 인기글 분석
        result = analyzer.analyze_ichart(max_items=100)

        if result:
            # 결과를 딕셔너리 형태로 변환 (저장용)
            results = {'ichart': result}

            # 결과 저장
            analyzer.save_results(results, 'instiz_trends_2025.json')
            analyzer.save_results_to_csv(results, 'instiz_trends_2025.csv')

            # Top 20 키워드 출력
            print("\n" + "="*80)
            print("📊 인스티즈 실시간 트렌드 Top 20")
            print("="*80)

            keywords = result['keywords'][:20]
            for i, kw in enumerate(keywords, 1):
                print(f"{i:2d}. {kw['keyword']:20s} | "
                      f"출현: {kw['count']:3d}회 | "
                      f"인기도: {kw['total_engagement']:5d}")

            print(f"\n✅ 크롤링 완료!")
            print(f"📅 수집 시간: {result['crawled_at']}")

        else:
            print("\n❌ 수집된 데이터가 없습니다.")

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
