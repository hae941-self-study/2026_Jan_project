"""
클리앙 (Clien) 트렌드 크롤링
- 인기 게시물에서 키워드 추출
- 월간 베스트 게시판 지원
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


class ClienCrawler:
    """클리앙 크롤러"""

    def __init__(self):
        """초기화"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.base_url = 'https://www.clien.net'

    def get_board_posts(self, board_type: str = 'park', max_pages: int = 5) -> List[Dict]:
        """
        게시판의 게시물 가져오기

        Args:
            board_type: 게시판 타입
                - 'park': 모두의공원 (자유게시판)
                - 'jirum': 알뜰구매
                - 'cm_car': 자동차
                - 'cm_vcam': 영상기기
                - 'lecture': 강좌
            max_pages: 크롤링할 페이지 수

        Returns:
            게시물 리스트
        """
        posts = []

        for page in range(0, max_pages):
            url = f'{self.base_url}/service/board/{board_type}'

            params = {
                'od': 'T31',  # 인기순
                'po': page * 15  # 15개씩 페이지네이션
            }

            try:
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                response.raise_for_status()
                response.encoding = 'utf-8'

                soup = BeautifulSoup(response.text, 'html.parser')

                # 게시물 목록 파싱
                post_list = soup.select('.list_item')

                for post in post_list:
                    try:
                        # 제목
                        title_elem = post.select_one('.subject_fixed')
                        if not title_elem:
                            title_elem = post.select_one('.list_subject')

                        if not title_elem:
                            continue

                        title = title_elem.text.strip()

                        # 댓글 수
                        comment_elem = post.select_one('.comment_count')
                        comments = 0
                        if comment_elem:
                            comment_text = comment_elem.text.strip()
                            comment_match = re.search(r'\[(\d+)\]', comment_text)
                            if comment_match:
                                comments = int(comment_match.group(1))

                        # 조회수
                        hit_elem = post.select_one('.hit')
                        hits = 0
                        if hit_elem:
                            hit_text = hit_elem.text.strip()
                            hits = int(hit_text) if hit_text.isdigit() else 0

                        # 추천수
                        symph_elem = post.select_one('.symph_count')
                        symphs = 0
                        if symph_elem:
                            symph_text = symph_elem.text.strip()
                            symphs = int(symph_text) if symph_text.isdigit() else 0

                        posts.append({
                            'title': title,
                            'comments': comments,
                            'hits': hits,
                            'symphs': symphs,
                            'engagement': comments * 5 + symphs * 10  # 가중치
                        })

                    except Exception as e:
                        continue

                if len(posts) > 0:
                    print(f"   ✅ 현재까지 총 {len(posts)}개 게시물 수집")
                else:
                    print(f"   ⚠️ 수집된 게시물 없음")

                # Rate limit 방지
                time.sleep(random.uniform(1, 2))

            except requests.exceptions.HTTPError as e:
                print(f"   ⚠️ HTTP 에러: {e}")
                continue
            except Exception as e:
                print(f"   ⚠️ 페이지 {page + 1} 수집 실패: {e}")
                continue

        print(f"\n📊 전체 수집 완료: 총 {len(posts)}개 게시물")
        return posts

    def get_monthly_best(self, max_pages: int = 10) -> List[Dict]:
        """
        월간 베스트 게시판 가져오기 (모두의공원 인기글)

        Args:
            max_pages: 크롤링할 페이지 수

        Returns:
            게시물 리스트
        """
        posts = []

        # 모두의공원(park) 게시판의 인기글로 변경
        for page in range(0, max_pages):
            url = f'{self.base_url}/service/board/park'

            params = {
                'od': 'T31',  # 인기순
                'po': page * 15
            }

            try:
                print(f"   페이지 {page + 1}/{max_pages} 요청 중: {url}")
                response = requests.get(url, params=params, headers=self.headers, timeout=10)

                print(f"   응답 코드: {response.status_code}")

                if response.status_code == 404:
                    print(f"   ⚠️ 404 에러 - URL을 찾을 수 없습니다")
                    continue

                response.raise_for_status()
                response.encoding = 'utf-8'

                soup = BeautifulSoup(response.text, 'html.parser')

                # 게시물 목록 파싱 (여러 선택자 시도)
                post_list = soup.select('.list_item')

                if not post_list:
                    post_list = soup.select('div[class*="list"]')

                if not post_list:
                    print(f"   ⚠️ 게시물을 찾을 수 없습니다")
                    continue

                print(f"   ✓ {len(post_list)}개 게시물 발견")

                for post in post_list:
                    try:
                        # 제목
                        title_elem = post.select_one('.subject_fixed') or post.select_one('.list_subject')
                        if not title_elem:
                            continue

                        title = title_elem.text.strip()

                        # 댓글 수
                        comment_elem = post.select_one('.comment_count')
                        comments = 0
                        if comment_elem:
                            comment_text = comment_elem.text.strip()
                            comment_match = re.search(r'\[(\d+)\]', comment_text)
                            if comment_match:
                                comments = int(comment_match.group(1))

                        # 추천수
                        symph_elem = post.select_one('.symph_count')
                        symphs = 0
                        if symph_elem:
                            symph_text = symph_elem.text.strip()
                            symphs = int(symph_text) if symph_text.isdigit() else 0

                        posts.append({
                            'title': title,
                            'comments': comments,
                            'symphs': symphs,
                            'engagement': comments * 5 + symphs * 10
                        })

                    except Exception as e:
                        continue

                if len(posts) > 0:
                    print(f"   ✅ 현재까지 총 {len(posts)}개 게시물 수집")
                else:
                    print(f"   ⚠️ 수집된 게시물 없음")

                # Rate limit 방지
                time.sleep(random.uniform(1, 2))

            except requests.exceptions.HTTPError as e:
                print(f"   ⚠️ HTTP 에러: {e}")
                continue
            except Exception as e:
                print(f"   ⚠️ 페이지 {page + 1} 수집 실패: {e}")
                continue

        print(f"\n📊 전체 수집 완료: 총 {len(posts)}개 게시물")
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
            '클리앙', '게시판', '게시글', '공지', '질문', '답변',
            '입니다', '합니다', '있습니다', '없습니다', '가능', '불가능',
            '이거', '저거', '그거', '이게', '저게', '그게',
            '오늘', '어제', '내일', '요즘', '지금', '이제', '그냥',
            '진짜', '정말', '완전', '너무', '엄청', '개', '매우',
            '있다', '없다', '하다', '되다', '이다', '아니다',
            '같다', '듯하다', '보이다', '싶다', '하고', '그리고',
            '또는', '그런데', '하지만', '그러나', '그래서', '때문에',
            '안녕하세요', '감사합니다', '수고하세요', '부탁드립니다',
            '모두의공원', '알뜰구매', '자동차', '영상기기'
        }

        for post in posts:
            title = post['title']
            engagement = post.get('engagement', 1)

            # 한글 키워드 추출 (2글자 이상)
            korean_words = re.findall(r'[가-힣]{2,}', title)

            # 영어 키워드 추출 (2글자 이상)
            english_words = re.findall(r'\b[A-Za-z]{2,}\b', title)

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


class ClienTrendAnalyzer:
    """클리앙 트렌드 분석기"""

    def __init__(self):
        """초기화"""
        self.crawler = ClienCrawler()

    def analyze_boards(self, boards: List[Dict], max_pages: int = 5) -> Dict:
        """
        여러 게시판 분석

        Args:
            boards: [{'type': 'board_type', 'name': 'board_name'}, ...]
            max_pages: 게시판당 크롤링할 페이지 수

        Returns:
            전체 분석 결과
        """
        results = {}

        for board in boards:
            board_type = board['type']
            board_name = board['name']

            print(f"\n{'='*60}")
            print(f"📱 {board_name} 크롤링 중...")
            print(f"{'='*60}")

            posts = self.crawler.get_board_posts(board_type, max_pages)

            if not posts:
                print(f"⚠️ {board_name}: 게시물을 수집하지 못했습니다.")
                continue

            print(f"📊 총 {len(posts)}개 게시물 수집 완료")

            # 키워드 추출
            print(f"🔍 키워드 추출 중...")
            keywords = self.crawler.extract_keywords_from_posts(posts)

            print(f"✅ {len(keywords)}개 키워드 추출 완료")

            results[board_type] = {
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
                      f"인기도: {kw['total_engagement']:6d}")

            # 게시판 사이 대기
            time.sleep(random.uniform(2, 3))

        return results

    def analyze_monthly_best(self, max_pages: int = 10) -> Dict:
        """
        월간 베스트 분석

        Args:
            max_pages: 크롤링할 페이지 수

        Returns:
            분석 결과
        """
        print(f"\n{'='*60}")
        print(f"📊 클리앙 월간 베스트 분석")
        print(f"{'='*60}")

        posts = self.crawler.get_monthly_best(max_pages)

        if not posts:
            print(f"⚠️ 데이터를 수집하지 못했습니다.")
            return {}

        print(f"📊 총 {len(posts)}개 게시물 수집 완료")

        # 키워드 추출
        print(f"🔍 키워드 추출 중...")
        keywords = self.crawler.extract_keywords_from_posts(posts)

        print(f"✅ {len(keywords)}개 키워드 추출 완료")

        return {
            'source': '클리앙 월간 베스트',
            'total_posts': len(posts),
            'keywords': keywords,
            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def save_results(self, results: Dict, filename: str = 'clien_trends.json'):
        """결과 저장 (JSON)"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과가 {filename}에 저장되었습니다.")

    def save_results_to_csv(self, results: Dict, filename: str = 'clien_trends.csv'):
        """결과 저장 (CSV)"""
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['게시판', '순위', '키워드', '출현횟수', '총_인기도', '평균_인기도'])

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
    print("🚀 클리앙 트렌드 크롤링")
    print("="*80)
    print("\n📱 클리앙에서 트렌드 키워드를 수집합니다.")
    print("⚠️  크롤링 속도 제한을 준수하며, 공개 게시판만 수집합니다.\n")

    # 분석기 초기화
    analyzer = ClienTrendAnalyzer()

    try:
        # ===== 옵션 1: 월간 베스트 분석 (추천!) =====
        print("✅ 월간 베스트 게시판 분석 모드")

        result = analyzer.analyze_monthly_best(max_pages=10)

        if result:
            results = {'monthly_best': result}

            # 결과 저장
            analyzer.save_results(results, 'clien_trends_2025.json')
            analyzer.save_results_to_csv(results, 'clien_trends_2025.csv')

            # Top 20 키워드 출력
            print("\n" + "="*80)
            print("📊 클리앙 월간 베스트 Top 20 키워드")
            print("="*80)

            keywords = result['keywords'][:20]
            for i, kw in enumerate(keywords, 1):
                print(f"{i:2d}. {kw['keyword']:20s} | "
                      f"출현: {kw['count']:3d}회 | "
                      f"인기도: {kw['total_engagement']:6d}")

            print(f"\n✅ 크롤링 완료!")
            print(f"📅 수집 시간: {result['crawled_at']}")

        # ===== 옵션 2: 여러 게시판 분석 =====
        # 여러 게시판을 분석하려면 아래 주석을 해제하세요
        """
        boards = [
            {'type': 'park', 'name': '모두의공원'},
            {'type': 'jirum', 'name': '알뜰구매'},
            {'type': 'cm_car', 'name': '자동차'},
        ]

        results = analyzer.analyze_boards(boards, max_pages=5)

        if results:
            analyzer.save_results(results, 'clien_trends_2025.json')
            analyzer.save_results_to_csv(results, 'clien_trends_2025.csv')
        """

        if not result:
            print("\n❌ 수집된 데이터가 없습니다.")

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
