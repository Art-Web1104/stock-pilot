# stock-pilot 공통 규칙 (모든 세션 필독)

이 저장소는 한국 주식(코스피/코스닥) 분석·모의검증·매매추천 자동화 시스템의 상태 저장소다.
각 세션은 예약 작업으로 실행되는 독립된 Claude 세션이며, 이 저장소를 통해서만 상태를 주고받는다.

## 작업 순서

1. 예약 작업 프롬프트에 포함된 토큰으로 저장소를 clone 한다 (이미 했을 것).
2. 최신 상태 확인: `git pull` 후 `python3 scripts/pilot.py status`
3. 자기 역할의 프롬프트 파일(prompts/*.md)을 따라 작업한다.
4. 작업 끝나면 반드시 커밋·푸시한다:
   ```
   git config user.name "stock-pilot-bot" && git config user.email "bot@stock-pilot.local"
   git add -A && git commit -m "<세션이름>: YYYY-MM-DD" && git push
   ```
   푸시가 충돌하면 `git pull --rebase` 후 다시 푸시.
5. 마지막 응답(요약)은 한국어로, 핵심 결론만 간결하게 쓴다. 사용자에게 푸시 알림으로 전달될 수 있다.

## 시세 가져오는 방법 (검증된 방법)

이 환경에서는 pykrx, yfinance, 네이버/다음 금융이 전부 차단되어 있다.
**구글 파이낸스를 WebFetch로 읽는 것만 작동한다:**

- 개별 종목: `https://www.google.com/finance/quote/{종목코드6자리}:KRX`
  → 현재가(=장 마감 후엔 종가), 당일 시가/고가/저가, 시총, PER, EPS, 배당수익률, 52주 최고/최저
- 코스피 지수: `https://www.google.com/finance/quote/KOSPI:KRX`
- 코스닥 지수: `https://www.google.com/finance/quote/KOSDAQ:KRX`

WebFetch prompt에 "시가/고가/저가/현재가를 숫자 그대로 보고해줘"라고 요청할 것.
뉴스·재무 심층 정보는 WebSearch를 사용한다 (예: "삼성전자 실적 2026").

가격은 원 단위 정수로 기록한다. 쉼표 제거. 데이터를 가져오지 못한 종목은 건너뛰고
요약에 명시한다 (추측으로 가격을 만들어내지 말 것 — 잘못된 가격은 검증 전체를 오염시킨다).

## 데이터 파일

- `config.json` — 검증 규칙(2주=10거래일, 목표 +7%, 손절 -5%, 통과 기준 +3%), 한도, 제외 종목
- `data/paper_trades.json` — 모의매매(2주 검증) 기록. 직접 수정하지 말고 scripts/pilot.py 사용
- `data/signals.json` — 검증 통과 후 매매 추천 신호
- `data/control.json` — 사용자가 대시보드에서 내린 명령 (exclude/approve/dismiss)
- `data/price_history/{code}.json` — 자체 축적 일별 OHLC
- `data/market_analysis/`, `data/company_analysis/`, `data/chart_analysis/` — 날짜별 분석 결과 (YYYY-MM-DD.json + 같은 이름 .md 보고서)

## 원칙

- 절대 실제 주문을 넣지 않는다. 이 시스템은 분석과 추천까지만 한다.
- 휴장일(주말/공휴일)에 실행됐고 지수가 전 거래일과 동일하면, 데이터 기록 없이 "휴장"으로 요약하고 종료해도 된다.
- 모든 판단 근거를 분석 파일에 남긴다. 나중 세션이 그 근거를 읽고 이어간다.
- 사용자 제외 종목(config.json의 exclude_codes)은 어떤 경우에도 편입하지 않는다.
