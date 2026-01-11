"""
네이버 데이터랩 및 한국 SNS 트렌드 크롤링
- 네이버 쇼핑 인사이트
- 네이버 검색어 트렌드
"""

import requests
import json
import csv
import time
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class NaverDataLabCrawler:
    """네이버 데이터랩 크롤러"""

    def __init__(self, client_id: str = None, client_secret: str = None):
        """
        네이버 API 초기화

        API 발급 방법:
        1. https://developers.naver.com/apps/#/register 방문
        2. 애플리케이션 등록 (이름만 입력하면 됨)
        3. 'Client ID'와 'Client Secret' 복사
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.headers = {
            'X-Naver-Client-Id': client_id,
            'X-Naver-Client-Secret': client_secret,
            'Content-Type': 'application/json'
        }

    def search_trend(self, keywords: List[str], start_date: str, end_date: str,
                     timeunit: str = 'month', device: str = '', ages: List[str] = None,
                     gender: str = '') -> Dict:
        """
        네이버 검색어 트렌드 조회

        Args:
            keywords: 검색어 리스트 (최대 5개)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            timeunit: 'date', 'week', 'month' 중 선택
            device: 'pc', 'mo', '' (전체)
            ages: ['1', '2', ...] (1:0-12세, 2:13-18세, 3:19-24세, 4:25-29세, 5:30-34세,
                   6:35-39세, 7:40-44세, 8:45-49세, 9:50-54세, 10:55-59세, 11:60세 이상)
            gender: 'm', 'f', '' (전체)
        """
        url = 'https://openapi.naver.com/v1/datalab/search'

        # 키워드 그룹 생성
        keyword_groups = []
        for i, keyword in enumerate(keywords):
            keyword_groups.append({
                'groupName': keyword,
                'keywords': [keyword]
            })

        body = {
            'startDate': start_date,  # YYYY-MM-DD 형식 그대로 사용
            'endDate': end_date,      # YYYY-MM-DD 형식 그대로 사용
            'timeUnit': timeunit,
            'keywordGroups': keyword_groups
        }

        if device:
            body['device'] = device
        if ages:
            body['ages'] = ages
        if gender:
            body['gender'] = gender

        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(body))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   응답 코드: {e.response.status_code}")
                print(f"   응답 내용: {e.response.text}")
            return None

    def get_popular_keywords_by_category(self, year: int, month: int,
                                         categories: List[str] = None) -> Dict:
        """
        카테고리별 인기 키워드 추출 (시뮬레이션)

        실제로는 여러 seed 키워드를 사용해 관련 검색어를 찾아야 합니다.
        """
        if categories is None:
            categories = [
                '영화', '드라마', '음악', '게임', '스포츠',
                '정치', '경제', '사회', '연예', '패션'
            ]

        start_date = f"{year}-{month:02d}-01"
        # 해당 월의 마지막 날 계산
        if month == 12:
            end_date = f"{year}-{month:02d}-31"
        else:
            from calendar import monthrange
            last_day = monthrange(year, month)[1]
            end_date = f"{year}-{month:02d}-{last_day:02d}"

        print(f"🔍 {year}년 {month}월 네이버 트렌드 수집 중...")
        print(f"   기간: {start_date} ~ {end_date}")

        results = {}

        # 카테고리별로 검색어 트렌드 조회
        for i in range(0, len(categories), 5):  # 한 번에 최대 5개씩
            batch = categories[i:i+5]
            print(f"   카테고리 분석 중: {', '.join(batch)}")

            trend_data = self.search_trend(
                keywords=batch,
                start_date=start_date,
                end_date=end_date,
                timeunit='month'
            )

            if trend_data and 'results' in trend_data:
                for result in trend_data['results']:
                    keyword = result['title']
                    # 평균 검색 비율 계산
                    total_ratio = sum([point['ratio'] for point in result['data']])
                    avg_ratio = total_ratio / len(result['data']) if result['data'] else 0

                    results[keyword] = {
                        'keyword': keyword,
                        'avg_search_ratio': avg_ratio,
                        'data_points': result['data']
                    }

            # API Rate Limit 방지
            time.sleep(1)

        return results


class NaverShoppingInsightCrawler:
    """네이버 쇼핑 인사이트 크롤러"""

    def __init__(self, client_id: str = None, client_secret: str = None):
        """네이버 쇼핑 인사이트 API 초기화"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.headers = {
            'X-Naver-Client-Id': client_id,
            'X-Naver-Client-Secret': client_secret,
            'Content-Type': 'application/json'
        }

    def get_category_keywords(self, category: str, start_date: str, end_date: str,
                              timeunit: str = 'month', device: str = '',
                              ages: List[str] = None, gender: str = '') -> Dict:
        """
        카테고리별 쇼핑 인사이트 조회

        Args:
            category: 카테고리 ID (50000000: 패션의류, 50000001: 패션잡화, 등)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
        """
        url = 'https://openapi.naver.com/v1/datalab/shopping/categories'

        body = {
            'startDate': start_date,  # YYYY-MM-DD 형식 그대로 사용
            'endDate': end_date,      # YYYY-MM-DD 형식 그대로 사용
            'timeUnit': timeunit,
            'category': [{'name': category, 'param': [category]}]
        }

        if device:
            body['device'] = device
        if ages:
            body['ages'] = ages
        if gender:
            body['gender'] = gender

        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(body))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   응답 코드: {e.response.status_code}")
                print(f"   응답 내용: {e.response.text}")
            return None


class KoreanTrendAnalyzer:
    """통합 한국 트렌드 분석기"""

    def __init__(self, naver_client_id: str, naver_client_secret: str):
        """초기화"""
        self.naver_datalab = NaverDataLabCrawler(naver_client_id, naver_client_secret)
        self.naver_shopping = NaverShoppingInsightCrawler(naver_client_id, naver_client_secret)

    def analyze_monthly_trends(self, year: int, month: int,
                               seed_keywords: List[str] = None) -> Dict:
        """
        월별 트렌드 분석

        Args:
            year: 연도
            month: 월
            seed_keywords: 분석할 키워드 리스트
        """
        if seed_keywords is None:
            # 기본 시드 키워드 (다양한 카테고리)
            seed_keywords = [
                # 엔터테인먼트
                '영화', '드라마', '예능', '음악', '게임',
                # 스포츠
                '축구', '야구', '배구', 'E스포츠',
                # 이슈
                '정치', '경제', '사회', '국제',
                # 라이프스타일
                '패션', '뷰티', '건강', '맛집', '여행',
                # 테크
                '스마트폰', 'AI', '전기차'
            ]

        from datetime import datetime, timedelta

        # 네이버 데이터랩은 최소 7일 이상의 기간이 필요함
        # 해당 월의 1일부터 다음 달 1일 전날까지로 설정
        start_date = f"{year}-{month:02d}-01"

        # 다음 달 계산
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1

        # 다음 달 1일에서 1일 빼기 = 현재 월의 마지막 날
        next_month_first = datetime(next_year, next_month, 1)
        end_date_obj = next_month_first - timedelta(days=1)
        end_date = end_date_obj.strftime("%Y-%m-%d")

        print(f"\n{'='*60}")
        print(f"📅 {year}년 {month}월 네이버 트렌드 분석")
        print(f"{'='*60}")
        print(f"기간: {start_date} ~ {end_date}")

        all_results = []

        # 5개씩 나눠서 API 호출
        for i in range(0, len(seed_keywords), 5):
            batch = seed_keywords[i:i+5]
            print(f"\n🔍 키워드 분석 중 ({i+1}-{min(i+5, len(seed_keywords))}/{len(seed_keywords)}): {', '.join(batch)}")

            # 네이버 API는 월 단위 조회 시 최소 1개월 이상 기간 필요
            # date 단위로 변경하여 조회
            trend_data = self.naver_datalab.search_trend(
                keywords=batch,
                start_date=start_date,
                end_date=end_date,
                timeunit='date'  # month -> date로 변경
            )

            if trend_data and 'results' in trend_data:
                for result in trend_data['results']:
                    keyword = result['title']
                    data_points = result['data']

                    # 평균 검색 비율 계산
                    total_ratio = sum([point['ratio'] for point in data_points])
                    avg_ratio = total_ratio / len(data_points) if data_points else 0

                    all_results.append({
                        'keyword': keyword,
                        'avg_search_ratio': round(avg_ratio, 2),
                        'max_ratio': max([point['ratio'] for point in data_points]) if data_points else 0,
                        'total_engagement': int(total_ratio),
                        'data_points': len(data_points)
                    })

                print(f"   ✅ {len(batch)}개 키워드 수집 완료")
            else:
                print(f"   ⚠️ 데이터 수집 실패")

            # Rate Limit 방지
            time.sleep(0.5)

        # 검색 비율 기준 정렬
        all_results.sort(key=lambda x: x['avg_search_ratio'], reverse=True)

        print(f"\n✅ 총 {len(all_results)}개 키워드 분석 완료")
        return all_results

    def analyze_year_by_month(self, year: int = 2025, analyze_full_year: bool = False,
                             seed_keywords: List[str] = None) -> Dict:
        """연도별 월별 분석"""
        results = {}

        # 분석할 월 결정
        if analyze_full_year or datetime.now().year > year:
            current_month = 12
        else:
            current_month = datetime.now().month if datetime.now().year == year else 12

        for month in range(1, current_month + 1):
            print(f"\n{'='*70}")
            print(f"📊 {year}년 {month}월 분석 시작")
            print(f"{'='*70}")

            keywords = self.analyze_monthly_trends(year, month, seed_keywords)

            if keywords:
                results[f"{year}-{month:02d}"] = keywords

                # 결과 출력
                print(f"\n🏆 {year}년 {month}월 Top 10 트렌드 키워드:")
                print("-" * 70)
                for i, kw in enumerate(keywords[:10], 1):
                    print(f"{i:2d}. {kw['keyword']:20s} | "
                          f"평균 검색비율: {kw['avg_search_ratio']:6.2f} | "
                          f"최대: {kw['max_ratio']:6.2f}")
            else:
                print(f"⚠️ {year}년 {month}월: 트렌드를 수집하지 못했습니다.")

            # 월별 대기
            if month < current_month:
                print(f"\n⏳ 다음 월 수집을 위해 잠시 대기 중...")
                time.sleep(2)

        return results

    def save_results(self, results: Dict, filename: str = "naver_trends_2025.json"):
        """결과 저장 (JSON)"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과가 {filename}에 저장되었습니다.")

    def save_results_to_csv(self, results: Dict, filename: str = "naver_trends_2025.csv"):
        """결과 저장 (CSV)"""
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['연월', '순위', '키워드', '평균_검색비율', '최대_검색비율', '총_Engagement'])

            for month, keywords in results.items():
                for i, kw in enumerate(keywords, 1):
                    writer.writerow([
                        month,
                        i,
                        kw['keyword'],
                        kw['avg_search_ratio'],
                        kw['max_ratio'],
                        kw['total_engagement']
                    ])

        print(f"💾 CSV 결과가 {filename}에 저장되었습니다.")


# 실행
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 네이버 데이터랩 트렌드 분석")
    print("="*80)
    print("\n📝 네이버 API 발급 방법:")
    print("   1. https://developers.naver.com/apps/#/register 방문")
    print("   2. 애플리케이션 이름만 입력하고 등록 (1분 소요)")
    print("   3. 생성된 앱에서 'Client ID'와 'Client Secret' 복사")
    print("   4. 아래 코드에 붙여넣기\n")

    # API 키 설정 (사용자가 입력해야 함)
    NAVER_CLIENT_ID = '####'
    NAVER_CLIENT_SECRET = '####'

    # API 키가 설정되지 않은 경우
    if NAVER_CLIENT_ID == 'YOUR_CLIENT_ID':
        print("❌ 네이버 API 키가 설정되지 않았습니다.")
        print("   코드 하단의 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 입력하세요.")
        print("\n💡 API 발급은 1분이면 완료됩니다!")
        sys.exit(1)

    try:
        # 분석기 초기화
        analyzer = KoreanTrendAnalyzer(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)

        # 분석할 키워드 설정 (원하는 키워드로 변경 가능)
        custom_keywords = [
            # 엔터테인먼트
            '영화', '드라마', '예능', '음악', '아이돌',
            # 스포츠
            '축구', '야구', '배구', '골프', 'UFC',
            # 이슈/뉴스
            '정치', '경제', '부동산', '주식', '코인',
            # 라이프스타일
            '맛집', '카페', '여행', '호텔', '캠핑',
            # 패션/뷰티
            '패션', '뷰티', '화장품', '다이어트', '운동',
            # 테크/IT
            '스마트폰', '노트북', '게임', 'AI', '전기차'
        ]

        # 2025년 월별 분석 실행
        results = analyzer.analyze_year_by_month(
            year=2025,
            analyze_full_year=True,
            seed_keywords=custom_keywords
        )

        if results:
            # 결과 저장
            analyzer.save_results(results)
            analyzer.save_results_to_csv(results)

            # 전체 요약 출력
            print("\n" + "="*80)
            print("📊 2025년 전체 요약")
            print("="*80)

            for month, keywords in results.items():
                print(f"\n{month}:")
                top_5 = keywords[:5]
                for i, kw in enumerate(top_5, 1):
                    print(f"  {i}. {kw['keyword']} (검색비율: {kw['avg_search_ratio']:.2f})")

            print(f"\n✅ 분석 완료! 총 {len(results)}개월 데이터 수집")
        else:
            print("\n❌ 수집된 데이터가 없습니다.")

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
