"""
디시인사이드 (DC Inside) 트렌드 크롤링
- 인기 갤러리의 게시물에서 키워드 추출
- 제목, 내용에서 트렌드 키워드 분석
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


class DCInsideCrawler:
    """디시인사이드 크롤러"""

    def __init__(self):
        """초기화"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.base_url = 'https://gall.dcinside.com'

    def get_gallery_list(self, gallery_id: str, page: int = 1) -> List[Dict]:
        """
        특정 갤러리의 게시물 목록 가져오기

        Args:
            gallery_id: 갤러리 ID (예: 'book' - 도서 갤러리)
            page: 페이지 번호

        Returns:
            게시물 리스트
        """
        url = f'{self.base_url}/board/lists/?id={gallery_id}&page={page}'

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            posts = []

            # 게시물 목록 파싱
            post_list = soup.select('.gall_list tbody tr.ub-content')

            for post in post_list:
                try:
                    # 제목
                    title_elem = post.select_one('.gall_tit a')
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()

                    # 댓글 수
                    reply_elem = post.select_one('.gall_tit .reply_num')
                    reply_count = 0
                    if reply_elem:
                        reply_text = reply_elem.text.strip()
                        reply_match = re.search(r'\[(\d+)\]', reply_text)
                        if reply_match:
                            reply_count = int(reply_match.group(1))

                    # 조회수
                    views_elem = post.select_one('.gall_count')
                    views = 0
                    if views_elem:
                        views_text = views_elem.text.strip()
                        views = int(views_text) if views_text.isdigit() else 0

                    # 추천수
                    recommend_elem = post.select_one('.gall_recommend')
                    recommend = 0
                    if recommend_elem:
                        recommend_text = recommend_elem.text.strip()
                        recommend = int(recommend_text) if recommend_text.isdigit() else 0

                    # 작성일
                    date_elem = post.select_one('.gall_date')
                    date = date_elem.text.strip() if date_elem else ''

                    posts.append({
                        'title': title,
                        'reply_count': reply_count,
                        'views': views,
                        'recommend': recommend,
                        'date': date,
                        'engagement': reply_count + recommend  # 인기도 지표
                    })

                except Exception as e:
                    continue

            return posts

        except requests.exceptions.RequestException as e:
            print(f"❌ 갤러리 조회 실패 ({gallery_id}): {e}")
            return []

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
        keyword_engagement = {}  # 키워드별 인기도 합산

        # 일반적인 단어 필터링
        stopwords = {
            '게시판', '갤러리', '디시인사이드', '디시', '질문', '답변',
            '입니다', '합니다', '있습니다', '없습니다', '가능', '불가능',
            '이거', '저거', '그거', '이게', '저게', '그게',
            '오늘', '어제', '내일', '요즘', '지금', '이제', '그냥',
            '진짜', '정말', '완전', '너무', '엄청', '개', '매우',
            '있다', '없다', '하다', '되다', '이다', '아니다',
            '같다', '듯하다', '보이다', '싶다', '하고', '그리고',
            '또는', '그런데', '하지만', '그러나', '그래서', '때문에'
        }

        for post in posts:
            title = post['title']
            engagement = post['engagement']

            # 한글 키워드 추출 (2글자 이상)
            korean_words = re.findall(r'[가-힣]{2,}', title)

            # 영어 키워드 추출 (3글자 이상)
            english_words = re.findall(r'\b[A-Za-z]{3,}\b', title)

            # 숫자+텍스트 조합 (예: 2024년, 3월)
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

    def crawl_gallery(self, gallery_id: str, gallery_name: str,
                     max_pages: int = 5) -> Dict:
        """
        갤러리 크롤링

        Args:
            gallery_id: 갤러리 ID
            gallery_name: 갤러리 이름
            max_pages: 크롤링할 페이지 수

        Returns:
            크롤링 결과
        """
        print(f"\n{'='*60}")
        print(f"📱 {gallery_name} ({gallery_id}) 크롤링 중...")
        print(f"{'='*60}")

        all_posts = []

        for page in range(1, max_pages + 1):
            print(f"   페이지 {page}/{max_pages} 수집 중...")

            posts = self.get_gallery_list(gallery_id, page)
            all_posts.extend(posts)

            print(f"   ✅ {len(posts)}개 게시물 수집")

            # Rate limit 방지
            time.sleep(random.uniform(1, 2))

        print(f"\n📊 총 {len(all_posts)}개 게시물 수집 완료")

        # 키워드 추출
        print(f"🔍 키워드 추출 중...")
        keywords = self.extract_keywords_from_posts(all_posts)

        print(f"✅ {len(keywords)}개 키워드 추출 완료")

        return {
            'gallery_id': gallery_id,
            'gallery_name': gallery_name,
            'total_posts': len(all_posts),
            'keywords': keywords,
            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


class DCInsideTrendAnalyzer:
    """디시인사이드 트렌드 분석기"""

    def __init__(self):
        """초기화"""
        self.crawler = DCInsideCrawler()

    def analyze_multiple_galleries(self, galleries: List[Dict],
                                   max_pages: int = 5) -> Dict:
        """
        여러 갤러리 분석

        Args:
            galleries: [{'id': 'gallery_id', 'name': 'gallery_name'}, ...]
            max_pages: 갤러리당 크롤링할 페이지 수

        Returns:
            전체 분석 결과
        """
        results = {}

        for gallery in galleries:
            gallery_id = gallery['id']
            gallery_name = gallery['name']

            result = self.crawler.crawl_gallery(gallery_id, gallery_name, max_pages)
            results[gallery_id] = result

            # 각 갤러리별 Top 10 출력
            print(f"\n🏆 {gallery_name} Top 10 키워드:")
            print("-" * 70)
            for i, kw in enumerate(result['keywords'][:10], 1):
                print(f"{i:2d}. {kw['keyword']:20s} | "
                      f"출현: {kw['count']:3d}회 | "
                      f"인기도: {kw['total_engagement']:5d}")

            # 갤러리 사이 대기
            time.sleep(random.uniform(2, 3))

        return results

    def get_overall_trends(self, results: Dict, top_n: int = 30) -> List[Dict]:
        """
        전체 갤러리에서 통합 트렌드 추출

        Args:
            results: 갤러리별 분석 결과
            top_n: 상위 N개 키워드

        Returns:
            통합 트렌드 키워드
        """
        all_keywords = Counter()
        keyword_engagement = {}

        for gallery_id, result in results.items():
            for kw in result['keywords']:
                keyword = kw['keyword']
                count = kw['count']
                engagement = kw['total_engagement']

                all_keywords[keyword] += count

                if keyword not in keyword_engagement:
                    keyword_engagement[keyword] = 0
                keyword_engagement[keyword] += engagement

        # 결과 정리
        overall_trends = []
        for keyword, count in all_keywords.most_common(top_n):
            overall_trends.append({
                'keyword': keyword,
                'count': count,
                'total_engagement': keyword_engagement[keyword],
                'avg_engagement': keyword_engagement[keyword] / count if count > 0 else 0
            })

        return overall_trends

    def save_results(self, results: Dict, filename: str = 'dcinside_trends.json'):
        """결과 저장 (JSON)"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과가 {filename}에 저장되었습니다.")

    def save_results_to_csv(self, results: Dict, filename: str = 'dcinside_trends.csv'):
        """결과 저장 (CSV)"""
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['갤러리', '순위', '키워드', '출현횟수', '총_인기도', '평균_인기도'])

            for gallery_id, result in results.items():
                gallery_name = result['gallery_name']
                for i, kw in enumerate(result['keywords'], 1):
                    writer.writerow([
                        gallery_name,
                        i,
                        kw['keyword'],
                        kw['count'],
                        kw['total_engagement'],
                        round(kw['avg_engagement'], 2)
                    ])

        print(f"💾 CSV 결과가 {filename}에 저장되었습니다.")


# 실행
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 디시인사이드 트렌드 크롤링")
    print("="*80)
    print("\n📱 한국 최대 커뮤니티 디시인사이드에서 실시간 트렌드를 수집합니다.")
    print("⚠️  크롤링 속도 제한을 준수하며, 공개 게시판만 수집합니다.\n")

    # 크롤링할 갤러리 목록 (필요에 따라 수정 가능)
    galleries = [
        {'id': 'book', 'name': '도서 갤러리'},
        {'id': 'comic_new2', 'name': '만화 갤러리'},
        {'id': 'movie', 'name': '영화 갤러리'},
        {'id': 'drama', 'name': '드라마 갤러리'},
        {'id': 'music', 'name': '음악 갤러리'},
        {'id': 'game', 'name': '게임 갤러리'},
    ]

    # 분석기 초기화
    analyzer = DCInsideTrendAnalyzer()

    try:
        # 갤러리별 크롤링 및 분석
        results = analyzer.analyze_multiple_galleries(
            galleries=galleries,
            max_pages=5  # 갤러리당 5페이지 (약 50개 게시물)
        )

        if results:
            # 결과 저장
            analyzer.save_results(results, 'dcinside_trends_2025.json')
            analyzer.save_results_to_csv(results, 'dcinside_trends_2025.csv')

            # 전체 통합 트렌드
            print("\n" + "="*80)
            print("📊 전체 갤러리 통합 트렌드 Top 20")
            print("="*80)

            overall_trends = analyzer.get_overall_trends(results, top_n=20)
            for i, kw in enumerate(overall_trends, 1):
                print(f"{i:2d}. {kw['keyword']:20s} | "
                      f"출현: {kw['count']:3d}회 | "
                      f"인기도: {kw['total_engagement']:6d}")

            # 갤러리별 요약
            print("\n" + "="*80)
            print("📱 갤러리별 요약")
            print("="*80)
            for gallery_id, result in results.items():
                print(f"\n{result['gallery_name']}:")
                top_5 = result['keywords'][:5]
                for i, kw in enumerate(top_5, 1):
                    print(f"  {i}. {kw['keyword']} (출현: {kw['count']}회)")

            print(f"\n✅ 크롤링 완료! 총 {len(results)}개 갤러리 분석")
            print(f"📅 수집 시간: {results[list(results.keys())[0]]['crawled_at']}")

        else:
            print("\n❌ 수집된 데이터가 없습니다.")

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
