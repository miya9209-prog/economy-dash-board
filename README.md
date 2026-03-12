# 경제 대시보드(Economy Dash board)

## 포함 기능
- 한국 시간 / 미국 동부 시간 표시
- 코스피 / 코스닥 실시간 지수 카드
- 한국 금시세 1돈 기준 살때/팔때
- 한국 기준금리
- 소비심리지수(CCSI)
- 국제유가(브렌트유)
- 한국 기준 유가(휘발유/경유)
- 코스피 10종목 / 코스닥 10종목 / ETF 10종목
- 주요 경제뉴스 리스트
- 주요 경제정보 사이트 바로가기
- 하단 카피라이트 표시

## 배포 순서
1. GitHub 새 레포 생성
2. `economy_dashboard_app.py`를 `app.py`로 이름 변경 후 업로드
3. `economy_dashboard_requirements.txt`를 `requirements.txt`로 이름 변경 후 업로드
4. Streamlit Cloud에서 레포 연결
5. 메인 파일을 `app.py`로 지정
6. Secrets에 필요 시 아래 입력

```toml
OPINET_API_KEY = "YOUR_OPINET_KEY"
```

## 참고
- 한국 유가(휘발유/경유)는 오피넷 API 키가 있어야 안정적으로 표시됩니다.
- 주가/ETF/브렌트유는 yfinance를 사용합니다.
- 기준금리와 소비심리지수는 공개 페이지를 우선 활용하도록 구성했습니다.
