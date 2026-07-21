# 세션 D — 차트 분석 및 검증 편입 (평일 18:00 KST)

역할: 회사 분석의 후보들을 기술적 관점에서 점검해, 최종 통과 종목을 2주 모의매매 검증에 편입한다.
**이 세션만이 검증 편입(open-trade) 권한을 갖는다.**

## 절차

1. `prompts/common.md`를 먼저 읽는다.
2. 입력 읽기:
   - 오늘의 `data/company_analysis/YYYY-MM-DD.json`
   - 오늘의 `data/market_analysis/YYYY-MM-DD.json` (국면이 bearish면 신규 편입 기준을 크게 높인다)
   - `python3 scripts/pilot.py status` — 진행 중 종목, 한도 확인
   - 후보 종목의 `data/price_history/{code}.json` (있다면 — 축적된 자체 데이터)
3. 후보별 기술적 점검 (구글 파이낸스 + WebSearch "{종목명} 주가 차트 분석"):
   - 추세: 52주 범위 내 현재 위치. 최고가 대비 -5% 이내면 과열 주의, 최저가 부근이면 하락 추세 여부 확인
   - 당일 캔들: 시가/고가/저가/종가 관계 (장대양봉? 위꼬리? 갭상승?)
   - 거래량: 평균 거래량 대비 당일 거래량 (급증 여부)
   - price_history가 5일 이상 쌓인 종목은 단기 추세(5일 이동 방향)도 계산
   - 판단: enter(편입) / watch(관망, 내일 재검토) / reject(탈락) + 근거
4. 편입 — enter 판정 종목만, 하루 최대 2개 (config.json):
   ```
   echo '{"code":"005930","name":"삼성전자","sector":"반도체","entry_price":259000,
          "thesis":"회사분석 thesis + 차트 근거 요약",
          "analyses":{"market":"YYYY-MM-DD","company":"YYYY-MM-DD","chart":"YYYY-MM-DD"}}' \
     | python3 scripts/pilot.py open-trade
   ```
   entry_price는 당일 종가. 편입과 동시에 오늘 종가를 price_history에도 기록한다 (record-prices).
5. 결과 저장 — `data/chart_analysis/YYYY-MM-DD.json`:
   ```json
   {
     "date": "YYYY-MM-DD",
     "decisions": [
       {"code": "...", "name": "...", "action": "enter|watch|reject",
        "entry_price": 0, "technical_notes": "...", "reason": "..."}
     ],
     "summary": "..."
   }
   ```
   같은 내용을 `.md` 보고서로도 저장.
6. 대시보드 갱신: `python3 scripts/pilot.py dashboard`
7. 커밋·푸시 후 요약: 신규 편입 종목(있으면 맨 앞에, 편입가 포함), watch/reject 사유 한 줄씩.

## 주의

- 편입은 "지금 이 가격에 샀다고 가정"하는 행위다. 확신 없으면 watch가 정답이다.
  좋은 후보는 내일도 좋다. 무리한 편입이 검증 통계를 오염시킨다.
- 시장 국면이 bearish인 날은 원칙적으로 신규 편입하지 않는다 (예외라면 근거를 명확히).
- 급등 마감(+15% 이상)한 종목은 다음 날 되돌림이 흔하므로 watch로 미룬다.
