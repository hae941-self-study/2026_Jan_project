"""
뽐뿌 (PPOMPPU) 트렌드 크롤링
- 핫딜/쇼핑 트렌드 키워드 추출
- 베스트 게시판 지원
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


class PpomppuCrawler:
    """뽐뿌 크롤러"""

    def __init__(self):
        """초기화"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.base_url = 'https://www.ppomppu.co.kr'

    def get_board_posts(self, board_id: str, max_pages: int = 5) -> List[Dict]:
        """
        게시판의 게시물 가져오기

        Args:
            board_id: 게시판 ID
                - 'zboard/zboard.php?id=ppomppu': 자유게시판
                - 'zboard/zboard.php?id=ppomppu4': 유머/이슈
                - 'zboard/zboard.php?id=humor': 유머게시판
                - 'zboard/zboard.php?id=freeboard': 자유게시판
            max_pages: 크롤링할 페이지 수

        Returns:
            게시물 리스트
        """
        posts = []

        for page in range(1, max_pages + 1):
            url = f'{self.base_url}/{board_id}&page={page}'

            try:
                print(f"   페이지 {page}/{max_pages} 요청 중...")
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                response.encoding = 'euc-kr'  # 뽐뿌는 euc-kr 인코딩

                soup = BeautifulSoup(response.text, 'html.parser')

                # 게시물 목록 파싱
                post_list = soup.select('tr[class*="list"]')

                if not post_list:
                    post_list = soup.select('table.board_table tr')

                print(f"   ✓ {len(post_list)}개 항목 발견")

                for post in post_list:
                    try:
                        # 제목
                        title_elem = post.select_one('a[class*="list_title"]') or post.select_one('td.list_title a')
                        if not title_elem:
                            title_elem = post.select_one('a.title') or post.select_one('td a')

                        if not title_elem:
                            continue

                        title = title_elem.text.strip()

                        # 공지사항 제외
                        if '공지' in title or '알림' in title:
                            continue

                        # 조회수
                        hit_elem = post.select_one('td.hit') or post.select_one('td[class*="hit"]')
                        hits = 0
                        if hit_elem:
                            hit_text = hit_elem.text.strip()
                            hits = int(hit_text) if hit_text.isdigit() else 0

                        # 추천수
                        recommend_elem = post.select_one('td.recommend') or post.select_one('td[class*="rec"]')
                        recommends = 0
                        if recommend_elem:
                            rec_text = recommend_elem.text.strip()
                            recommends = int(rec_text) if rec_text.isdigit() else 0

                        posts.append({
                            'title': title,
                            'hits': hits,
                            'recommends': recommends,
                            'engagement': hits + recommends * 10
                        })

                    except Exception as e:
                        continue

                if len(posts) > 0:
                    print(f"   ✅ 현재까지 총 {len(posts)}개 게시물 수집")

                # Rate limit 방지
                time.sleep(random.uniform(1, 2))

            except Exception as e:
                print(f"   ⚠️ 페이지 {page} 수집 실패: {e}")
                continue

        print(f"\n📊 전체 수집 완료: 총 {len(posts)}개 게시물")
        return posts

    def get_hotdeal_posts(self, max_pages: int = 10) -> List[Dict]:
        """
        핫딜 게시판 가져오기

        Args:
            max_pages: 크롤링할 페이지 수

        Returns:
            게시물 리스트
        """
        posts = []

        for page in range(1, max_pages + 1):
            # 뽐뿌 핫딜 게시판
            url = f'{self.base_url}/zboard/zboard.php?id=ppomppu&page={page}'

            try:
                print(f"   페이지 {page}/{max_pages} 요청 중: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                print(f"   응답 코드: {response.status_code}")
                response.raise_for_status()
                response.encoding = 'euc-kr'

                soup = BeautifulSoup(response.text, 'html.parser')

                # 게시판 테이블 찾기
                tables = soup.find_all('table')

                board_table = soup.find('table', {'class': 'board_list'}) or \
                             soup.find('table', {'class': 'list_table'}) or \
                             soup.find('table', id='revolution_main_table')

                if not board_table and tables:
                    # 가장 큰 테이블 사용
                    board_table = max(tables, key=lambda t: len(str(t)))

                if not board_table:
                    print(f"   ⚠️ 게시판 테이블을 찾지 못함")
                    continue

                # 게시물 행 찾기
                post_list = board_table.find_all('tr')

                # 유효한 게시물만 필터링 (공백 행 제외)
                valid_posts = [tr for tr in post_list if tr.find('td', class_='list_vspace') is None]

                if not valid_posts:
                    print(f"   ⚠️ 유효한 게시물을 찾지 못함")
                    continue

                post_list = valid_posts

                successful_posts = 0
                for post in post_list:
                    try:
                        # 제목 찾기 - baseList-title 클래스를 가진 링크
                        title_elem = post.find('a', class_='baseList-title')

                        if not title_elem or not title_elem.text.strip():
                            continue

                        title = title_elem.text.strip()

                        # 공지/알림 제외
                        if any(word in title for word in ['공지', '알림', '광고', '이벤트', '안내']):
                            continue

                        # 조회수 - baseList-views 클래스
                        hits = 0
                        hit_elem = post.find('td', class_='baseList-views')
                        if hit_elem:
                            hit_text = hit_elem.text.strip()
                            hits = int(hit_text) if hit_text.isdigit() else 0

                        # 추천수 - baseList-rec 클래스 (형식: "4 - 0")
                        recommends = 0
                        rec_elem = post.find('td', class_='baseList-rec')
                        if rec_elem:
                            rec_text = rec_elem.text.strip()
                            # "4 - 0" 형식에서 첫 번째 숫자 추출
                            import re
                            match = re.search(r'(\d+)', rec_text)
                            if match:
                                recommends = int(match.group(1))

                        posts.append({
                            'title': title,
                            'hits': hits,
                            'recommends': recommends,
                            'engagement': hits + recommends * 10
                        })

                        successful_posts += 1

                    except Exception as e:
                        continue

                if len(posts) > 0:
                    print(f"   ✅ 현재까지 총 {len(posts)}개 게시물 수집")

                # Rate limit 방지
                time.sleep(random.uniform(1, 2))

            except Exception as e:
                print(f"   ⚠️ 페이지 {page} 수집 실패: {e}")
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
            '뽐뿌', '게시판', '게시글', '공지', '질문', '답변',
            '입니다', '합니다', '있습니다', '없습니다', '가능', '불가능',
            '이거', '저거', '그거', '이게', '저게', '그게',
            '오늘', '어제', '내일', '요즘', '지금', '이제', '그냥',
            '진짜', '정말', '완전', '너무', '엄청', '개', '매우',
            '있다', '없다', '하다', '되다', '이다', '아니다',
            '같다', '듯하다', '보이다', '싶다', '하고', '그리고',
            '또는', '그런데', '하지만', '그러나', '그래서', '때문에',
            '안녕하세요', '감사합니다', '수고하세요', '부탁드립니다',
            '핫딜', '특가', '할인', '최저가', '무료배송', '쿠폰'
        }

        for post in posts:
            title = post['title']
            engagement = post.get('engagement', 1)

            # 한글 키워드 추출 (2글자 이상)
            korean_words = re.findall(r'[가-힣]{2,}', title)

            # 영어 키워드 추출 (2글자 이상)
            english_words = re.findall(r'\b[A-Za-z]{2,}\b', title)

            # 숫자+텍스트 조합 (가격, 날짜 등)
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


class PpomppuTrendAnalyzer:
    """뽐뿌 트렌드 분석기"""

    def __init__(self):
        """초기화"""
        self.crawler = PpomppuCrawler()

    def analyze_hotdeal(self, max_pages: int = 10) -> Dict:
        """
        핫딜 게시판 분석

        Args:
            max_pages: 크롤링할 페이지 수

        Returns:
            분석 결과
        """
        print(f"\n{'='*60}")
        print(f"🔥 뽐뿌 핫딜 게시판 분석")
        print(f"{'='*60}")

        posts = self.crawler.get_hotdeal_posts(max_pages)

        if not posts:
            print(f"⚠️ 데이터를 수집하지 못했습니다.")
            return {}

        print(f"📊 총 {len(posts)}개 게시물 수집 완료")

        # 키워드 추출
        print(f"🔍 키워드 추출 중...")
        keywords = self.crawler.extract_keywords_from_posts(posts)

        print(f"✅ {len(keywords)}개 키워드 추출 완료")

        return {
            'source': '뽐뿌 핫딜',
            'total_posts': len(posts),
            'keywords': keywords,
            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def save_results(self, results: Dict, filename: str = 'ppomppu_trends.json'):
        """결과 저장 (JSON)"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과가 {filename}에 저장되었습니다.")

    def save_results_to_csv(self, results: Dict, filename: str = 'ppomppu_trends.csv'):
        """결과 저장 (CSV)"""
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['게시판', '순위', '키워드', '출현횟수', '총_인기도', '평균_인기도'])

            for key, result in results.items():
                source_name = result.get('source', key)
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
    print("🚀 뽐뿌 트렌드 크롤링")
    print("="*80)
    print("\n🛒 뽐뿌에서 쇼핑/핫딜 트렌드 키워드를 수집합니다.")
    print("⚠️  크롤링 속도 제한을 준수하며, 공개 게시판만 수집합니다.\n")

    # 분석기 초기화
    analyzer = PpomppuTrendAnalyzer()

    try:
        # 핫딜 게시판 분석
        print("✅ 핫딜 게시판 분석 모드")

        result = analyzer.analyze_hotdeal(max_pages=10)

        if result:
            results = {'hotdeal': result}

            # 결과 저장
            analyzer.save_results(results, 'ppomppu_trends_2025.json')
            analyzer.save_results_to_csv(results, 'ppomppu_trends_2025.csv')

            # Top 20 키워드 출력
            print("\n" + "="*80)
            print("🔥 뽐뿌 핫딜 Top 20 키워드")
            print("="*80)

            keywords = result['keywords'][:20]
            for i, kw in enumerate(keywords, 1):
                print(f"{i:2d}. {kw['keyword']:20s} | "
                      f"출현: {kw['count']:3d}회 | "
                      f"인기도: {kw['total_engagement']:6d}")

            print(f"\n✅ 크롤링 완료!")
            print(f"📅 수집 시간: {result['crawled_at']}")

        if not result:
            print("\n❌ 수집된 데이터가 없습니다.")

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
