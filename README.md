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

## ⚠️ 주의사항

1. **크롤링 속도**: 각 사이트의 서버에 부담을 주지 않도록 요청 간 1~2초 대기
2. **공개 데이터만**: 로그인이 필요한 콘텐츠는 수집하지 않음
3. **robots.txt 준수**: 각 사이트의 크롤링 정책을 준수
4. **개인정보 보호**: 사용자 개인정보는 수집하지 않음

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
