# 한국 트렌드 크롤러 (Korean Trend Crawler)

한국 주요 온라인 커뮤니티 및 검색 엔진에서 실시간 트렌드 키워드를 수집하는 크롤러 모음입니다.

## 📊 지원 사이트

### 1. 네이버 데이터랩 (Naver DataLab)
- **파일**: `naver_datalab_crawling.py`
- **데이터**: 네이버 공식 검색 트렌드 (월별)
- **특징**: 전국민 검색량 기반, 가장 객관적인 데이터
- **필요사항**: Naver API 키 (무료)

### 2. 디시인사이드 (DCInside)
- **파일**: `dcinside_crawling.py`
- **데이터**: 도서, 만화, 영화, 드라마, 음악, 게임 갤러리
- **특징**: 마니아층의 심층 트렌드

### 3. 클리앙 (Clien)
- **파일**: `clien_crawling.py`
- **데이터**: 모두의공원 월간 베스트
- **특징**: IT/시사/경제 중심, 30~40대 남성

### 4. 뽐뿌 (Ppomppu)
- **파일**: `ppomppu_crawling.py`
- **데이터**: 핫딜 게시판
- **특징**: 쇼핑/핫딜 트렌드, 가격 정보

### 5. 인스티즈 (Instiz)
- **파일**: `instiz_crawling.py`
- **데이터**: 실시간 인기글
- **특징**: 10~20대 여성, 연예/아이돌

## 🚀 설치 및 실행

### 1. 필요한 패키지 설치

```bash
pip install requests beautifulsoup4
```

### 2. 네이버 API 키 발급 (네이버 데이터랩 사용 시)

1. https://developers.naver.com/apps/#/register 방문
2. 애플리케이션 이름 입력 후 등록
3. Client ID와 Client Secret 복사
4. `naver_datalab_crawling.py` 파일에 붙여넣기

### 3. 크롤러 실행

```bash
# 네이버 데이터랩
python naver_datalab_crawling.py

# 디시인사이드
python dcinside_crawling.py

# 클리앙
python clien_crawling.py

# 뽐뿌
python ppomppu_crawling.py

# 인스티즈
python instiz_crawling.py
```

## 📁 출력 파일

각 크롤러는 다음 형식으로 결과를 저장합니다:

- `*_trends_2025.json` - JSON 형식
- `*_trends_2025.csv` - CSV 형식 (엑셀에서 바로 열기 가능)

## 📊 데이터 구조

### CSV 파일 구조
```
게시판/출처, 순위, 키워드, 출현횟수, 총_인기도, 평균_인기도
```

### 인기도 계산 방식
- **네이버**: 검색량 기반
- **커뮤니티**: 조회수 + 댓글수 + 추천수

## ⚠️ 주의사항 및 면책 조항 (Disclaimer)

본 프로젝트는 **Python 데이터 분석 학습 및 연구 목적**으로 개발되었습니다. 이 코드를 사용할 때는 아래 원칙을 반드시 준수해야 하며, 이를 어겨 발생하는 모든 문제에 대한 책임은 사용자 본인에게 있습니다.

1.  **서버 부하 방지 (Crawl-delay)**: `time.sleep(1~2)` 등을 사용하여 각 요청 간 충분한 대기 시간을 두어 대상 서버에 부하를 주지 않도록 합니다.
2.  **공개 데이터만 수집**: 로그인이 필요하거나 접근 권한이 없는 비공개 데이터는 수집하지 않습니다.
3.  **Robots.txt 및 정책 준수**: 대상 사이트의 `robots.txt` 규칙과 이용 약관(Terms of Service)을 확인하고 준수합니다.
4.  **개인정보 수집 금지**: 사용자 개인정보(이름, 전화번호 등)가 포함된 데이터는 수집하거나 저장하지 않습니다.
5.  **저작권 존중**: 수집한 데이터를 무단으로 재배포하거나 상업적으로 이용하지 않습니다.

## 📈 활용 사례

- 시장 조사 및 트렌드 분석
- 콘텐츠 기획
- 키워드 마케팅
- 소비 트렌드 파악
- 세대별 관심사 비교

## 🛠️ 기술 스택

- Python 3.7+
- BeautifulSoup4 (HTML 파싱)
- Requests (HTTP 요청)
- Naver DataLab API

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 제공됩니다.
상업적 사용 시 각 사이트의 이용약관을 확인하세요.

## 🤝 기여

버그 리포트 및 개선 제안은 Issues를 통해 제출해주세요.

## 📧 문의

프로젝트 관련 문의사항이 있으시면 Issues를 통해 연락주세요.
